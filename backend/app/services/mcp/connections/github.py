from datetime import datetime, timedelta, timezone
import secrets

from urllib.parse import urlencode

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.mcp_connection import MCPConnection
from app.models.mcp_server import MCPServer
from app.services.mcp.connections.base import (
    MCPConnectionProvider,
)

GITHUB_AUTHORIZATION_URL = (
    "https://github.com/login/oauth/authorize"
)

GITHUB_TOKEN_URL = (
    "https://github.com/login/oauth/access_token"
)


class GitHubConnectionProvider(MCPConnectionProvider):


    async def start_connection(
            self,
            user_id: int,
            server: MCPServer,
            db: AsyncSession,
    ) -> str:

        state = secrets.token_urlsafe(32)

        connection = await db.scalar(
            select(MCPConnection).where(
                MCPConnection.user_id == user_id,
                MCPConnection.mcp_server_id == server.id,
            )
        )

        if not connection:
            connection = MCPConnection(
                user_id=user_id,
                mcp_server_id=server.id,
                status="pending",
            )

            db.add(connection)

        connection.oauth_state = state
        connection.status = "pending"

        await db.commit()
        await db.refresh(connection)

        params = {
            "client_id": settings.GITHUB_CLIENT_ID,
            "redirect_uri": settings.GITHUB_REDIRECT_URI,
            "scope": "repo read:user offline_access",
            "state": state,
        }

        authorization_url = (
            f"{GITHUB_AUTHORIZATION_URL}"
            f"?{urlencode(params)}"
        )

        print(
            "GITHUB AUTH URL:",
            authorization_url,
        )

        return authorization_url

    async def complete_connection(
            self,
            connection: MCPConnection,
            server: MCPServer,
            code: str,
            state: str,
            db: AsyncSession,
    ) -> MCPConnection:

        if connection.oauth_state != state:
            raise ValueError(
                "Invalid OAuth state"
            )

        data = {
            "client_id": settings.GITHUB_CLIENT_ID,
            "client_secret": settings.GITHUB_CLIENT_SECRET,
            "redirect_uri": settings.GITHUB_REDIRECT_URI,
            "code": code,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                GITHUB_TOKEN_URL,
                data=data,
                headers={
                    "Accept":
                        "application/json",
                },
            )

        response.raise_for_status()

        token_data = response.json()

        if token_data.get("error"):
            raise ValueError(
                token_data.get(
                    "error_description",
                    token_data["error"],
                )
            )

        access_token = token_data["access_token"]

        if not access_token:
            raise ValueError(
                "GitHub access token is missing"
            )

        connection.access_token = (
            access_token
        )

        connection.refresh_token = (
            token_data.get("refresh_token")
        )

        connection.token_type = (
            token_data.get("token_type")
        )

        connection.scope = (
            token_data.get("scope")
        )

        expires_in = token_data.get("expires_in")

        if expires_in:
            connection.expires_at = (
                    datetime.now(timezone.utc)
                    + timedelta(
                seconds=expires_in
            )
            )

        else:
            connection.expires_at = None

        connection.status = "connected"
        connection.oauth_state = None
        connection.code_verifier = None

        await db.commit()
        await db.refresh(connection)

        return connection

    async def get_valid_access_token(
        self,
        connection: MCPConnection,
        server: MCPServer,
        db: AsyncSession,
    ) -> str | None:

        if not connection.access_token:
            raise ValueError(
                "GitHub access token is missing"
            )

        if not connection.expires_at:
            return connection.access_token


        now = datetime.now(timezone.utc)

        if(
            connection.expires_at > now + timedelta(seconds=60)
        ):
            return connection.access_token

        if not connection.refresh_token:
            connection.status = "expired"

            await db.commit()

            raise ValueError(
                "GitHub connection must be renewed"
            )

        data = {
            "client_id": settings.GITHUB_CLIENT_ID,
            "client_secret": settings.GITHUB_CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": connection.refresh_token,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                GITHUB_TOKEN_URL,
                data=data,
                headers={
                    "Accept":
                        "application/json",
                }
            )

        if response.status_code >= 400:
            connection.status = "expired"

            await db.commit()

            raise ValueError(
                "GitHub token refresh failed: "
                f"{response.text}"
            )

        token_data = response.json()

        if token_data.get("error"):
            connection.status = "expired"

            await db.commit()

            raise ValueError(
                token_data.get(
                    "error_description",
                    token_data["error"],
                )
            )

        access_token = token_data.get("access_token")

        if not access_token:
            connection.status = "expired"

            await db.commit()

            raise ValueError(
                "GitHub access token refresh failed"
            )

        connection.access_token = (access_token)

        if token_data.get("refresh_token"):
            connection.refresh_token = (
                token_data["refresh_token"]
            )

        connection.token_type = (
            token_data.get(
                "token_type",
                connection.token_type,
            )
        )

        connection.scope = (
            token_data.get(
                "scope",
                connection.scope,
            )
        )

        expires_in = token_data.get("expires_in")

        if expires_in:
            connection.expires_at = (
                    datetime.now(timezone.utc)
                    + timedelta(
                seconds=expires_in
            )
            )

        else:
            connection.expires_at = None

        connection.status = "connected"

        await db.commit()
        await db.refresh(connection)

        return connection.access_token










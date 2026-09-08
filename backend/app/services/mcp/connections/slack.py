import base64
import hashlib
import secrets

from datetime import datetime, timedelta, timezone
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

SLACK_AUTHORIZATION_URL = (
    "https://slack.com/oauth/v2_user/authorize"
)

SLACK_TOKEN_URL = (
    "https://slack.com/api/oauth.v2.user.access"
)


SLACK_SCOPES = [
    "search:read.public",
    "search:read.private",
    "search:read.mpim",
    "search:read.im",
    "search:read.files",
    "files:read",
    "files:write",
    "emoji:read",
    "search:read.users",
    "chat:write",
    "channels:history",
    "groups:history",
    "mpim:history",
    "im:history",
    "channels:write",
    "groups:write",
    "im:write",
    "mpim:write",
    "reactions:write",
    "canvases:read",
    "canvases:write",
    "users:read",
    "users:read.email",
    "channels:read",
    "groups:read",
    "im:read",
    "mpim:read",
    "lists:read",
    "lists:write",
]

class SlackConnectionProvider(MCPConnectionProvider):

    async def start_connection(
            self,
            user_id: int,
            server: MCPServer,
            db: AsyncSession,
    ) -> str:

        code_verifier = secrets.token_urlsafe(48)

        challenge_bytes = hashlib.sha256(
            code_verifier.encode("utf-8")
        ).digest()

        code_challenge = (
            base64.urlsafe_b64encode(
                challenge_bytes
            )
            .rstrip(b"=")
            .decode("utf-8")
        )

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
        connection.code_verifier = code_verifier
        connection.status = "pending"

        await db.commit()
        await db.refresh(connection)

        params = {
            "client_id": settings.SLACK_CLIENT_ID,
            "redirect_uri": settings.SLACK_REDIRECT_URI,
            "scope": ",".join(SLACK_SCOPES),
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }

        authorization_url = (
            f"{SLACK_AUTHORIZATION_URL}"
            f"?{urlencode(params)}"
        )

        print(
            "SLACK AUTH URL:",
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

        if not connection.code_verifier:
            raise ValueError(
                "Invalid code verifier"
            )

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.SLACK_REDIRECT_URI,
            "client_id": settings.SLACK_CLIENT_ID,
            "client_secret": settings.SLACK_CLIENT_SECRET,
            "code_verifier": connection.code_verifier,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                SLACK_TOKEN_URL,
                data=data,
            )

        response.raise_for_status()

        token_data = response.json()

        if not token_data.get("ok"):
            raise ValueError(
                "Slack OAuth failed: "
                f"{token_data.get('error')}"
            )

        access_token = token_data.get("access_token")

        if not access_token:
            raise ValueError(
                "Slack access token is missing"
            )

        connection.access_token = (access_token)
        connection.token_type = token_data.get("token_type")
        connection.scope = (
            token_data
            .get("authed_user", {})
            .get("scope")
        )
        connection.refresh_token = (token_data.get("refresh_token"))

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
                "Slack access token is missing"
            )

        if not connection.expires_at:
            return connection.access_token

        now = datetime.now(timezone.utc)

        if (
                connection.expires_at
                > now + timedelta(seconds=60)
        ):
            return connection.access_token

        if not connection.refresh_token:
            connection.status = "expired"

            await db.commit()

            raise ValueError(
                "Slack connection must be renewed"
            )

        data = {
            "grant_type": "refresh_token",
            "refresh_token": connection.refresh_token,
            "client_id": settings.SLACK_CLIENT_ID,
            "client_secret": settings.SLACK_CLIENT_SECRET,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                SLACK_TOKEN_URL,
                data=data,
            )

        if response.status_code >= 400:
            connection.status = "expired"

            await db.commit()

            raise ValueError(
                "Slack token refresh failed: "
                f"{response.text}"
            )

        token_data = response.json()

        if not token_data.get("ok"):
            connection.status = "expired"

            await db.commit()

            raise ValueError(
                "Slack token refresh failed: "
                f"{token_data.get('error')}"
            )

        connection.access_token = (token_data.get("access_token"))

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

        return connection



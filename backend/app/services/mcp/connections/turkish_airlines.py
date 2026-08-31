import base64
import hashlib
import os
import secrets

from urllib.parse import urlencode

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mcp_connection import MCPConnection
from app.models.mcp_server import MCPServer
from app.services.mcp.connections.base import MCPConnectionProvider
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv

load_dotenv()

THY_AUTHORIZATION_URL = "https://mcp.turkishtechlab.com/authorize"

THY_TOKEN_URL = "https://mcp.turkishtechlab.com/token"

THY_REDIRECT_URI = (
    "http://localhost:8000/api/mcp/oauth/callback"
)


class TurkishAirlinesConnectionProvider(
    MCPConnectionProvider
):

    async def start_connection(
        self,
        user_id: int,
        server: MCPServer,
        db: AsyncSession,
    ) -> str:

        client_id = os.getenv("THY_MCP_CLIENT_ID")

        if not client_id:
            raise ValueError(
                "THY_MCP_CLIENT_ID is missing"
            )

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
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": THY_REDIRECT_URI,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "state": state,
        }

        authorization_url = (
            f"{THY_AUTHORIZATION_URL}"
            f"?{urlencode(params)}"
        )

        print("THY AUTH URL:", authorization_url)

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
            raise ValueError("Invalid OAuth state")

        if not connection.code_verifier:
            raise ValueError("Invalid code verifier")

        client_id = os.getenv("THY_MCP_CLIENT_ID")

        if not client_id:
            raise ValueError(
                "THY_MCP_CLIENT_ID is missing"
            )

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": THY_REDIRECT_URI,
            "client_id": client_id,
            "code_verifier": connection.code_verifier,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                THY_TOKEN_URL,
                data=data,
            )

        response.raise_for_status()

        token_data = response.json()

        connection.access_token = token_data["access_token"]
        connection.refresh_token = token_data.get("refresh_token")
        connection.token_type = token_data.get("token_type")
        connection.scope = token_data.get("scope")

        expires_in = token_data.get("expires_in")

        if expires_in:
            connection.expires_at = (
                    datetime.now(timezone.utc)
                    + timedelta(seconds=expires_in)
            )

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
                "Turkish Airlines access token is missing"
            )

        now = datetime.now(timezone.utc)

        if (
                connection.expires_at
                and connection.expires_at
                > now + timedelta(seconds=60)
        ):
            return connection.access_token

        if not connection.refresh_token:
            connection.status = "expired"

            await db.commit()

            raise ValueError(
                "Turkish Airlines connection must be renewed"
            )

        client_id = os.getenv("THY_MCP_CLIENT_ID")

        if not client_id:
            raise ValueError(
                "THY_MCP_CLIENT_ID is missing"
            )

        data = {
            "grant_type": "refresh_token",
            "refresh_token": connection.refresh_token,
            "client_id": client_id,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                THY_TOKEN_URL,
                data=data,
            )

        if response.status_code >= 400:
            connection.status = "expired"

            await db.commit()

            raise ValueError(
                f"Turkish Airlines token refresh failed: "
                f"{response.text}"
            )

        token_data = response.json()

        connection.access_token = token_data["access_token"]

        if token_data.get("refresh_token"):
            connection.refresh_token = token_data["refresh_token"]

        connection.token_type = token_data.get("token_type",connection.token_type)

        connection.scope = token_data.get("scope")

        expires_in = token_data.get("expires_in")

        if expires_in:
            connection.expires_at = (
                    datetime.now(timezone.utc)
                    + timedelta(seconds=expires_in)
            )

        connection.status = "connected"

        await db.commit()
        await db.refresh(connection)

        return connection.access_token


import base64
import hashlib
import secrets

from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode, urlparse

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mcp_connection import MCPConnection
from app.models.mcp_server import MCPServer
from app.services.mcp.connections.base import (
    MCPConnectionProvider,
)

ATLASSIAN_REDIRECT_URI = (
    "http://localhost:8000"
     "/api/mcp/oauth/callback"
)

ATLASSIAN_CLIENT_NAME = "Create Your AI Assistant"

_ATLASSIAN_OAUTH_TRANSACTIONS: dict[str, str] = {}

class AtlassianConnectionProvider(MCPConnectionProvider):

    async def start_connection(
            self,
            user_id: int,
            server: MCPServer,
            db: AsyncSession,
    ) -> str:

        oauth_metadata = await self._discover_oauth(server.url)

        registration_url = (
            oauth_metadata.get("registration_endpoint")
        )

        authorization_url = (
            oauth_metadata.get("authorization_endpoint")
        )

        if not registration_url:
            raise RuntimeError(
                "Atlassian OAuth registration "
                "endpoint was not discovered"
            )

        if not authorization_url:
            raise RuntimeError(
                "Atlassian OAuth authorization "
                "endpoint was not discovered"
            )

        client_id = await self._register_client(
            registration_url
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

        _ATLASSIAN_OAUTH_TRANSACTIONS[state] = (
            client_id
        )

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
            "redirect_uri": ATLASSIAN_REDIRECT_URI,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "resource": server.url,
        }

        authorization_url = (
            f"{authorization_url}"
            f"?{urlencode(params)}"
        )

        print(
            "ATLASSIAN AUTH URL:",
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

        client_id = (
            _ATLASSIAN_OAUTH_TRANSACTIONS.pop(
                state,
                None,
            )
        )

        if not client_id:
            raise ValueError(
                "Atlassian OAuth transaction is missing"
            )

        oauth_metadata = await self._discover_oauth(server.url)

        token_url = oauth_metadata.get(
            "token_endpoint"
        )

        if not token_url:
            raise ValueError(
                "Atlassian token endpoint is missing"
            )

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": ATLASSIAN_REDIRECT_URI,
            "client_id": client_id,
            "code_verifier": connection.code_verifier,
            "resource": server.url,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data=data,
            )

        response.raise_for_status()

        token_data = response.json()

        access_token = token_data.get("access_token")

        if not access_token:
            raise ValueError(
                "Atlassian access token is missing"
            )

        connection.access_token = access_token

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
                "Atlassian access token is missing"
            )

        if not connection.expires_at:
            return connection.access_token

        now = datetime.now(timezone.utc)

        if (
                connection.expires_at
                > now + timedelta(seconds=60)
        ):
            return connection.access_token

        connection.status = "expired"

        await db.commit()

        raise ValueError(
            "Atlassian connection must be renewed"
        )

    async def _discover_oauth(
            self,
            server_url: str,
    ) -> dict:

        parsed_url = urlparse(server_url)

        origin = (
            f"{parsed_url.scheme}://"
            f"{parsed_url.netloc}"
        )

        protected_resource_url = (
            f"{origin}"
            "/.well-known/oauth-protected-resource"
            f"{parsed_url.path}"
        )

        async with httpx.AsyncClient(
            follow_redirects=True
        ) as client:

            response = await client.get(
                protected_resource_url,
            )

            response.raise_for_status()

            resource_metadata = response.json()

            authorization_servers = (
                resource_metadata.get("authorization_servers")
            )

            if not authorization_servers:
                raise ValueError(
                    "Atlassian authorization server is missing"
                )

            authorization_server = (
                authorization_servers[0]
                .rstrip("/")
            )

            metadata_url = (
                f"{authorization_server}"
                "/.well-known/"
                "oauth-authorization-server"
            )

            response = await client.get(
                metadata_url,
            )

            response.raise_for_status()

            return response.json()


    async def _register_client(
            self,
            registration_url: str,
    ) -> str:

        data = {
            "client_name": ATLASSIAN_CLIENT_NAME,
            "redirect_uris": [
                ATLASSIAN_REDIRECT_URI,
            ],
            "grant_types": [
                "authorization_code",
                "refresh_token",
            ],
            "response_types": [
                "code",
            ],
            "token_endpoint_auth_method": "none",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                registration_url,
                json=data,
            )

        response.raise_for_status()

        registration_data = response.json()

        client_id = registration_data.get("client_id")

        if not client_id:
            raise ValueError(
                "Atlassian client ID is missing"
            )

        return client_id















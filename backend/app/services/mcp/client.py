from contextlib import AsyncExitStack

import httpx2

from mcp.client import Client
from mcp.client.streamable_http import streamable_http_client
import mcp.client.session as mcp_session



class MCPClient:

    def __init__(self):
        self.client: Client | None = None
        self.exit_stack = AsyncExitStack()

    async def connect(
            self,
            server_url: str,
            access_token: str | None = None,
    ):
        headers = {}

        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        http_client = httpx2.AsyncClient(
            headers=headers,
            follow_redirects=True,
        )

        await self.exit_stack.enter_async_context(http_client)

        original_handshake_version = mcp_session.LATEST_HANDSHAKE_VERSION
        mcp_session.LATEST_HANDSHAKE_VERSION = "2025-03-26"

        try:
            transport = streamable_http_client(
                server_url,
                http_client=http_client,
            )

            self.client = Client(
                transport,
                mode="legacy",
            )

            await self.exit_stack.enter_async_context(
                self.client
            )

            return await self.client.session.list_tools()

        finally:
            mcp_session.LATEST_HANDSHAKE_VERSION = original_handshake_version

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict,
    ):
        if self.client is None:
            raise RuntimeError(
                "MCP client is not connected"
            )

        return await self.client.session.call_tool(
            tool_name,
            arguments,
        )

    async def close(self):
        try:
            await self.exit_stack.aclose()

        except BaseException as exc:
            print("MCP CLOSE ERROR:", repr(exc))

        finally:
            self.client = None
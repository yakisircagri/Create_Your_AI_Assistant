from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mcp_connection import MCPConnection
from app.models.mcp_server import MCPServer


class MCPConnectionProvider(ABC):

    @abstractmethod
    async def start_connection(
        self,
        user_id: int,
        server: MCPServer,
        db: AsyncSession,
    ) -> str:
        pass

    @abstractmethod
    async def complete_connection(
        self,
        connection: MCPConnection,
        server: MCPServer,
        code: str,
        state: str,
        db: AsyncSession,
    ) -> MCPConnection:
        pass

    @abstractmethod
    async def get_valid_access_token(
        self,
        connection: MCPConnection,
        server: MCPServer,
        db: AsyncSession,
    ) -> str | None:
        pass
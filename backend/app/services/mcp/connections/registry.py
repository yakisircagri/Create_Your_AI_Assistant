from app.services.mcp.connections.base import MCPConnectionProvider


_PROVIDERS: dict[str, MCPConnectionProvider] = {}


def register_provider(
    name: str,
    provider: MCPConnectionProvider,
) -> None:
    _PROVIDERS[name] = provider


def get_connection_provider(
    name: str | None,
) -> MCPConnectionProvider | None:
    if not name:
        return None

    return _PROVIDERS.get(name)
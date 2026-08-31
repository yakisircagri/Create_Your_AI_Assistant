from app.services.mcp.connections.registry import register_provider
from app.services.mcp.connections.turkish_airlines import (
    TurkishAirlinesConnectionProvider,
)


register_provider(
    "turkish_airlines",
    TurkishAirlinesConnectionProvider(),
)
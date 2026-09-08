from app.services.mcp.connections.registry import (
    register_provider,
)

from app.services.mcp.connections.github import (
    GitHubConnectionProvider,
)

from app.services.mcp.connections.turkish_airlines import (
    TurkishAirlinesConnectionProvider,
)

from app.services.mcp.connections.slack import (
    SlackConnectionProvider,
)

from app.services.mcp.connections.linear import (
    LinearConnectionProvider,
)

from app.services.mcp.connections.atlassian import (
    AtlassianConnectionProvider,
)


register_provider(
    "turkish_airlines",
    TurkishAirlinesConnectionProvider(),
)

register_provider(
    "github",
    GitHubConnectionProvider(),
)

register_provider(
    "slack",
    SlackConnectionProvider(),
)

register_provider(
    "linear",
    LinearConnectionProvider(),
)

register_provider(
    "atlassian",
    AtlassianConnectionProvider(),
)
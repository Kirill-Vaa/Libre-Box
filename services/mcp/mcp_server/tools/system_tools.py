from typing import Annotated

from mcp.server.mcpserver import MCPServer
from pydantic import Field

from domain.models import SleepResult, TimeNowResult
from services.container import ServiceContainer


def register_system_tools(mcp: MCPServer, container: ServiceContainer) -> None:
    @mcp.tool(description="Pause for the given number of seconds, useful for waiting between polling steps without holding a shell open.")
    async def sleep(
        seconds: Annotated[float, Field(description="Number of seconds to sleep", ge=0, le=86400)],
    ) -> SleepResult:
        return await container.system_service.sleep(seconds)

    @mcp.tool(description="Return the current time as an ISO 8601 string, epoch seconds, and a human-readable rendering in the requested timezone.")
    async def time_now(
        timezone: Annotated[str, Field(description="IANA timezone name, for example UTC or Europe/Berlin")] = "UTC",
    ) -> TimeNowResult:
        return container.system_service.time_now(timezone)

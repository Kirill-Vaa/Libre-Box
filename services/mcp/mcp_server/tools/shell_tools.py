from typing import Annotated

from mcp.server.mcpserver import MCPServer
from pydantic import Field

from config.settings import settings
from domain.models import ShellResult
from services.container import ServiceContainer


def register_shell_tools(mcp: MCPServer, container: ServiceContainer) -> None:
    @mcp.tool(description="Run a one-shot shell command in the sandbox via bash -lc and return its exit code, stdout, and stderr; the command is terminated when it exceeds the timeout.")
    async def shell_execute(
        command: Annotated[str, Field(description="Shell command to execute via bash -lc")],
        cwd: Annotated[str, Field(description="Working directory for the command")] = "/root/data",
        timeout: Annotated[int, Field(description="Maximum seconds to allow the command to run before it is terminated", ge=1, le=86400)] = settings.default_command_timeout_seconds,
        env: Annotated[dict[str, str] | None, Field(description="Extra environment variables to set for the command")] = None,
    ) -> ShellResult:
        return await container.shell_service.execute(command=command, cwd=cwd, env=env or {}, timeout=timeout)

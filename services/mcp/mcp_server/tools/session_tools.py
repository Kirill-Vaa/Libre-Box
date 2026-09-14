from typing import Annotated

from mcp.server.mcpserver import MCPServer
from pydantic import Field

from config.constants import SESSION_INPUT_WAIT_SECONDS
from config.settings import settings
from domain.models import OkResult, SessionExecutionResult, SessionInfo, SessionInputResult
from services.container import ServiceContainer


def register_session_tools(mcp: MCPServer, container: ServiceContainer) -> None:
    @mcp.tool(description="Create a persistent interactive bash session that keeps its working directory, environment, and shell state across subsequent commands.")
    async def shell_session_create(
        cwd: Annotated[str, Field(description="Initial working directory for the session")] = "/root/data",
        env: Annotated[dict[str, str] | None, Field(description="Extra environment variables to set for the session")] = None,
    ) -> SessionInfo:
        return await container.session_service.create(cwd=cwd, env=env or {})

    @mcp.tool(description="Run a command inside an existing interactive session, capturing output and the resulting working directory; a command still waiting on stdin returns partial output with timed_out set, and can then be answered with shell_session_send_input.")
    async def shell_session_execute(
        session_id: Annotated[str, Field(description="Identifier returned by shell_session_create")],
        command: Annotated[str, Field(description="Command to run in the session")],
        timeout: Annotated[int, Field(description="Maximum seconds to wait for the command to complete", ge=1, le=86400)] = settings.default_command_timeout_seconds,
    ) -> SessionExecutionResult:
        return await container.session_service.execute(session_id=session_id, command=command, timeout=timeout)

    @mcp.tool(description="Write raw text to an interactive session's stdin to answer a prompt of a command that is still running; returns the output that followed and reports whether that command has now finished.")
    async def shell_session_send_input(
        session_id: Annotated[str, Field(description="Identifier returned by shell_session_create")],
        text: Annotated[str, Field(description="Raw text to write to the session stdin")],
        add_newline: Annotated[bool, Field(description="Append a newline after the text to submit it")] = True,
        timeout: Annotated[float, Field(description="Maximum seconds to wait for the command awaiting input to finish before returning the output captured so far", ge=0, le=86400)] = SESSION_INPUT_WAIT_SECONDS,
    ) -> SessionInputResult:
        return await container.session_service.send_input(session_id=session_id, text=text, add_newline=add_newline, timeout=timeout)

    @mcp.tool(description="Terminate an interactive session and release its resources in the sandbox.")
    async def shell_session_close(
        session_id: Annotated[str, Field(description="Identifier returned by shell_session_create")],
    ) -> OkResult:
        await container.session_service.close(session_id)
        return OkResult(ok=True)

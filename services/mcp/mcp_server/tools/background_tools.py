from typing import Annotated

from mcp.server.mcpserver import MCPServer
from pydantic import Field

from config.constants import BACKGROUND_TAIL_DEFAULT_LINES
from config.settings import settings
from domain.models import BackgroundListResult, BackgroundProcessInfo, BackgroundTailResult, BackgroundWaitResult, SignalName
from services.container import ServiceContainer


def register_background_tools(mcp: MCPServer, container: ServiceContainer) -> None:
    @mcp.tool(description="Launch a long-running command as a detached background process whose output is streamed to a log file; returns a process id used to inspect or stop it.")
    async def background_start(
        command: Annotated[str, Field(description="Shell command to launch in the background")],
        cwd: Annotated[str, Field(description="Working directory for the process")] = "/root/data",
        env: Annotated[dict[str, str] | None, Field(description="Extra environment variables to set for the process")] = None,
    ) -> BackgroundProcessInfo:
        return await container.background_service.start(command=command, cwd=cwd, env=env or {})

    @mcp.tool(description="Report whether a background process is still running or has exited, including its exit code once available.")
    async def background_status(
        process_id: Annotated[str, Field(description="Identifier returned by background_start")],
    ) -> BackgroundProcessInfo:
        return await container.background_service.status(process_id)

    @mcp.tool(description="Return recent output from a background process log, either the last lines or a byte range for incremental streaming via the returned next_offset.")
    async def background_tail(
        process_id: Annotated[str, Field(description="Identifier returned by background_start")],
        lines: Annotated[int, Field(description="Number of trailing lines to return when offset_bytes is not given", ge=1, le=100000)] = BACKGROUND_TAIL_DEFAULT_LINES,
        offset_bytes: Annotated[int | None, Field(description="Resume reading from this byte offset instead of tailing lines", ge=0)] = None,
    ) -> BackgroundTailResult:
        return await container.background_service.tail(process_id=process_id, lines=lines, offset_bytes=offset_bytes)

    @mcp.tool(description="Send a signal to a background process group and wait for it to exit, escalating to KILL if it is still running after the timeout.")
    async def background_stop(
        process_id: Annotated[str, Field(description="Identifier returned by background_start")],
        signal: Annotated[SignalName, Field(description="Signal to send to the process group")] = "TERM",
        timeout: Annotated[int, Field(description="Seconds to wait for a graceful exit before sending KILL", ge=0, le=86400)] = 10,
    ) -> BackgroundProcessInfo:
        return await container.background_service.stop(process_id=process_id, signal=signal, timeout=timeout)

    @mcp.tool(description="Block until a background process exits or the timeout elapses, then return its final status and a tail of its output.")
    async def background_wait(
        process_id: Annotated[str, Field(description="Identifier returned by background_start")],
        timeout: Annotated[int, Field(description="Maximum seconds to wait for the process to exit", ge=0, le=86400)] = settings.default_command_timeout_seconds,
    ) -> BackgroundWaitResult:
        return await container.background_service.wait(process_id=process_id, timeout=timeout)

    @mcp.tool(description="List every tracked background process together with its current status and exit code.")
    async def background_list() -> BackgroundListResult:
        return BackgroundListResult(processes=await container.background_service.list_processes())

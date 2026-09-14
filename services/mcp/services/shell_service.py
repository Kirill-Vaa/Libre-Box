from domain.models import ShellResult
from infrastructure.docker.sandbox_client import SandboxClient


class ShellService:
    def __init__(self, sandbox_client: SandboxClient, default_timeout: int) -> None:
        self._sandbox_client = sandbox_client
        self._default_timeout = default_timeout

    async def execute(self, command: str, cwd: str, env: dict[str, str], timeout: int | None) -> ShellResult:
        effective_timeout = timeout if timeout is not None else self._default_timeout
        return await self._sandbox_client.exec_once(command=command, workdir=cwd, env=env, timeout=effective_timeout)

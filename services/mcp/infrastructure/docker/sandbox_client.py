import asyncio
from typing import Any, Final

import aiodocker
from aiodocker.exceptions import DockerError
from aiohttp import ClientError

from config.constants import EXEC_KILL_EXIT_CODE, EXEC_TIMEOUT_BACKSTOP_SECONDS, EXEC_TIMEOUT_EXIT_CODE, EXEC_TIMEOUT_KILL_GRACE_SECONDS, SANDBOX_CONNECT_ATTEMPTS, SANDBOX_RECONNECT_DELAY_SECONDS
from config.settings import settings
from domain.exceptions import SandboxUnavailableError
from domain.models import ShellResult
from utils.logger import logger
from utils.output import truncate_output


_STDOUT_STREAM: Final[int] = 1


class SandboxClient:
    def __init__(self, container_name: str) -> None:
        self._container_name = container_name
        self._docker: aiodocker.Docker | None = None
        self._connect_lock = asyncio.Lock()

    async def start(self) -> None:
        try:
            container = await self._container()
            logger.info(f"SandboxClient connected container={self._container_name} id={container.id[:12]}")
        except SandboxUnavailableError as error:
            logger.warning(f"SandboxClient could not reach the sandbox at startup, will retry on demand: {error}")

    async def close(self) -> None:
        await self._reset_docker()

    async def exec_once(self, command: str, workdir: str, env: dict[str, str], timeout: int) -> ShellResult:
        container = await self._container()
        running_loop = asyncio.get_running_loop()
        started_at = running_loop.time()

        stdout_chunks: list[bytes] = []
        stderr_chunks: list[bytes] = []
        backstop_reached = False

        try:
            exec_instance = await container.exec(
                cmd=["timeout", "-k", str(EXEC_TIMEOUT_KILL_GRACE_SECONDS), str(timeout), "bash", "-lc", command],
                stdout=True,
                stderr=True,
                tty=False,
                workdir=workdir,
                environment=self._format_environment(env),
            )

            try:
                async with asyncio.timeout(timeout + EXEC_TIMEOUT_KILL_GRACE_SECONDS + EXEC_TIMEOUT_BACKSTOP_SECONDS):
                    async with exec_instance.start(detach=False) as stream:
                        while True:
                            message = await stream.read_out()
                            if message is None:
                                break

                            if message.stream == _STDOUT_STREAM:
                                stdout_chunks.append(message.data)
                            else:
                                stderr_chunks.append(message.data)
            except TimeoutError:
                backstop_reached = True
                logger.warning(f"Sandbox exec_once backstop fired timeout={timeout} command={command[:80]!r}")

            exit_code = await self._read_exit_code(exec_instance)
        except (ClientError, DockerError) as connection_error:
            await self._reset_docker()
            raise SandboxUnavailableError(self._container_name, str(connection_error)) from connection_error

        timed_out = backstop_reached or exit_code in (EXEC_TIMEOUT_EXIT_CODE, EXEC_KILL_EXIT_CODE)
        if timed_out and not backstop_reached:
            logger.warning(f"Sandbox exec_once timed out timeout={timeout} exit_code={exit_code} command={command[:80]!r}")

        stdout_text, stdout_truncated = truncate_output(b"".join(stdout_chunks).decode(errors="replace"), settings.output_char_limit)
        stderr_text, stderr_truncated = truncate_output(b"".join(stderr_chunks).decode(errors="replace"), settings.output_char_limit)
        duration_ms = int((running_loop.time() - started_at) * 1000)

        return ShellResult(
            stdout=stdout_text,
            stderr=stderr_text,
            exit_code=exit_code,
            truncated=stdout_truncated or stderr_truncated,
            duration_ms=duration_ms,
            timed_out=timed_out,
        )

    async def open_interactive_stream(self, cwd: str, env: dict[str, str]) -> tuple[Any, Any]:
        container = await self._container()
        try:
            exec_instance = await container.exec(
                cmd=["bash"],
                stdin=True,
                stdout=True,
                stderr=True,
                tty=True,
                workdir=cwd,
                environment=self._format_environment(env),
            )

            stream = exec_instance.start(detach=False)
            await stream.__aenter__()

            return exec_instance, stream
        except (ClientError, DockerError) as connection_error:
            await self._reset_docker()
            raise SandboxUnavailableError(self._container_name, str(connection_error)) from connection_error

    async def _container(self) -> Any:
        last_reason = "unknown error"
        for attempt in range(1, SANDBOX_CONNECT_ATTEMPTS + 1):
            try:
                docker = await self._ensure_docker()
                return await docker.containers.get(self._container_name)
            except (ClientError, OSError) as connection_error:
                last_reason = str(connection_error)
                logger.warning(f"Sandbox connection attempt {attempt}/{SANDBOX_CONNECT_ATTEMPTS} failed container={self._container_name}: {connection_error}")
                await self._reset_docker()
            except DockerError as docker_error:
                last_reason = str(docker_error)
                logger.warning(f"Sandbox lookup attempt {attempt}/{SANDBOX_CONNECT_ATTEMPTS} failed container={self._container_name}: {docker_error}")

            if attempt < SANDBOX_CONNECT_ATTEMPTS:
                await asyncio.sleep(SANDBOX_RECONNECT_DELAY_SECONDS)

        raise SandboxUnavailableError(self._container_name, last_reason)

    async def _ensure_docker(self) -> aiodocker.Docker:
        if self._docker is None:
            async with self._connect_lock:
                if self._docker is None:
                    self._docker = aiodocker.Docker()

        return self._docker

    async def _reset_docker(self) -> None:
        async with self._connect_lock:
            if self._docker is None:
                return

            docker = self._docker
            self._docker = None
            try:
                await docker.close()
            except Exception as error:
                logger.debug(f"Error closing docker client during reset: {error}")

    @staticmethod
    def _format_environment(env: dict[str, str]) -> list[str] | None:
        return [f"{name}={value}" for name, value in env.items()] or None

    @staticmethod
    async def _read_exit_code(exec_instance: Any) -> int | None:
        inspection = await exec_instance.inspect()
        raw_exit_code = inspection.get("ExitCode")
        return int(raw_exit_code) if raw_exit_code is not None else None

import asyncio
import shlex
from typing import get_args
from uuid import uuid4

from config.constants import BACKGROUND_BYTE_COUNT_MARKER, BACKGROUND_LAUNCH_TIMEOUT_SECONDS, BACKGROUND_POLL_INTERVAL_SECONDS, BACKGROUND_TAIL_DEFAULT_LINES
from domain.exceptions import ProcessNotFoundError, SandboxError
from domain.models import BackgroundProcessInfo, BackgroundTailResult, BackgroundWaitResult, SignalName
from infrastructure.docker.sandbox_client import SandboxClient
from utils.logger import logger


_ALLOWED_SIGNALS: frozenset[str] = frozenset(get_args(SignalName))
_SIGNAL_EXIT_CODES: dict[str, int] = {
    "HUP": 129,
    "INT": 130,
    "KILL": 137,
    "QUIT": 131,
    "TERM": 143,
    "USR1": 138,
    "USR2": 140,
}
_UNTRAPPABLE_SIGNALS: frozenset[str] = frozenset({"CONT", "KILL", "STOP"})
_SIGNAL_TRAP_PREFIX: str = " ".join(f"trap 'exit {_SIGNAL_EXIT_CODES[signal_name]}' {signal_name};" for signal_name in sorted(set(_SIGNAL_EXIT_CODES) - _UNTRAPPABLE_SIGNALS))


class BackgroundService:
    def __init__(self, sandbox_client: SandboxClient, log_dir: str) -> None:
        self._sandbox_client = sandbox_client
        self._log_dir = log_dir
        self._processes: dict[str, BackgroundProcessInfo] = {}

    async def start(self, command: str, cwd: str, env: dict[str, str]) -> BackgroundProcessInfo:
        process_id = uuid4().hex[:12]
        log_path = f"{self._log_dir}/{process_id}.log"
        exit_path = f"{self._log_dir}/{process_id}.exit"
        inner_command = f"trap 'echo $? > {exit_path}' EXIT; {_SIGNAL_TRAP_PREFIX} {command}"
        launch_command = f"mkdir -p {self._log_dir} && setsid bash -lc {shlex.quote(inner_command)} > {log_path} 2>&1 < /dev/null & echo $!"

        launch_result = await self._sandbox_client.exec_once(launch_command, workdir=cwd, env=env, timeout=BACKGROUND_LAUNCH_TIMEOUT_SECONDS)
        try:
            pid = int(launch_result.stdout.strip().splitlines()[-1])
        except (IndexError, ValueError) as error:
            raise SandboxError(f"Failed to parse background PID from launch output: {launch_result.stdout.strip()[:200]!r}") from error

        process_info = BackgroundProcessInfo(process_id=process_id, pid=pid, command=command, status="running")
        self._processes[process_id] = process_info

        logger.info(f"Background process started process_id={process_id} pid={pid}")
        return process_info

    async def status(self, process_id: str) -> BackgroundProcessInfo:
        process_info = self._require(process_id)
        exit_path = f"{self._log_dir}/{process_id}.exit"
        probe_command = f"if kill -0 {process_info.pid} 2>/dev/null; then echo running; else cat {exit_path} 2>/dev/null || echo unknown; fi"
        probe_result = await self._sandbox_client.exec_once(probe_command, workdir=self._log_dir, env={}, timeout=15)
        status_marker = probe_result.stdout.strip()

        if status_marker == "running":
            process_info.status = "running"
        elif status_marker.lstrip("-").isdigit():
            process_info.status = "exited"
            process_info.exit_code = int(status_marker)
        else:
            process_info.status = "exited"

        return process_info

    async def tail(self, process_id: str, lines: int, offset_bytes: int | None) -> BackgroundTailResult:
        process_info = self._require(process_id)
        log_path = f"{self._log_dir}/{process_id}.log"
        read_command = f"tail -c +{offset_bytes + 1} {log_path}" if offset_bytes is not None else f"tail -n {lines} {log_path}"
        tail_command = f"{read_command}; printf '\\n{BACKGROUND_BYTE_COUNT_MARKER}%d\\n' \"$(wc -c < {log_path})\""
        tail_result = await self._sandbox_client.exec_once(tail_command, workdir=self._log_dir, env={}, timeout=15)

        content, total_bytes = self._split_byte_marker(tail_result.stdout)
        return BackgroundTailResult(process_id=process_info.process_id, content=content, total_bytes=total_bytes, next_offset=total_bytes)

    async def stop(self, process_id: str, signal: SignalName, timeout: int) -> BackgroundProcessInfo:
        process_info = self._require(process_id)
        await self._signal_process(process_info.pid, signal)

        deadline = asyncio.get_running_loop().time() + timeout
        while asyncio.get_running_loop().time() < deadline:
            refreshed = await self.status(process_id)
            if refreshed.status != "running":
                return self._apply_signal_exit_code(refreshed, signal)

            await asyncio.sleep(BACKGROUND_POLL_INTERVAL_SECONDS)

        await self._signal_process(process_info.pid, "KILL")
        return self._apply_signal_exit_code(await self.status(process_id), "KILL")

    async def wait(self, process_id: str, timeout: int) -> BackgroundWaitResult:
        self._require(process_id)
        deadline = asyncio.get_running_loop().time() + timeout
        while asyncio.get_running_loop().time() < deadline:
            process_info = await self.status(process_id)
            if process_info.status != "running":
                return await self._build_wait_result(process_info)
            await asyncio.sleep(BACKGROUND_POLL_INTERVAL_SECONDS)

        return await self._build_wait_result(await self.status(process_id))

    async def list_processes(self) -> list[BackgroundProcessInfo]:
        process_ids = list(self._processes.keys())
        results: list[BackgroundProcessInfo] = await asyncio.gather(*(self.status(process_id) for process_id in process_ids))
        return results

    async def _signal_process(self, pid: int, signal: SignalName) -> None:
        normalized_signal = signal.upper().removeprefix("SIG")
        if normalized_signal not in _ALLOWED_SIGNALS:
            raise SandboxError(f"Unsupported signal: {signal}")

        signal_command = f"kill -{normalized_signal} -{pid} 2>/dev/null || kill -{normalized_signal} {pid} 2>/dev/null || true"
        await self._sandbox_client.exec_once(signal_command, workdir=self._log_dir, env={}, timeout=15)

    async def _build_wait_result(self, process_info: BackgroundProcessInfo) -> BackgroundWaitResult:
        tail_result = await self.tail(process_info.process_id, lines=BACKGROUND_TAIL_DEFAULT_LINES, offset_bytes=None)
        return BackgroundWaitResult(process_id=process_info.process_id, status=process_info.status, exit_code=process_info.exit_code, tail=tail_result.content)

    @staticmethod
    def _apply_signal_exit_code(process_info: BackgroundProcessInfo, signal: SignalName) -> BackgroundProcessInfo:
        if process_info.status != "running" and process_info.exit_code is None:
            process_info.exit_code = _SIGNAL_EXIT_CODES.get(signal.upper().removeprefix("SIG"))

        return process_info

    @staticmethod
    def _split_byte_marker(output: str) -> tuple[str, int]:
        marker_index = output.rfind(f"\n{BACKGROUND_BYTE_COUNT_MARKER}")
        if marker_index == -1:
            return output, 0

        digits = output[marker_index + 1 + len(BACKGROUND_BYTE_COUNT_MARKER) :].strip()
        try:
            total_bytes = int(digits)
        except ValueError:
            total_bytes = 0

        return output[:marker_index], total_bytes

    def _require(self, process_id: str) -> BackgroundProcessInfo:
        process_info = self._processes.get(process_id)
        if process_info is None:
            raise ProcessNotFoundError(process_id)

        return process_info

import asyncio
import contextlib
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from config.constants import SESSION_BUFFER_MAX_CHARS, SESSION_DRAIN_SECONDS, SESSION_END_MARKER_PREFIX, SESSION_INIT_COMMANDS, SESSION_READ_INTERVAL_SECONDS, SESSION_READY_TIMEOUT_SECONDS
from config.settings import settings
from domain.exceptions import SessionBrokenError
from domain.models import SessionExecutionResult, SessionInputResult
from utils.logger import logger
from utils.output import truncate_output


_ANSI_ESCAPE_PATTERN = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")
_MARKER_FRAGMENT_HEAD = f"\n{SESSION_END_MARKER_PREFIX}"
_MARKER_FRAGMENT_PATTERN = re.compile(rf"\n{re.escape(SESSION_END_MARKER_PREFIX)}[^\n]*\Z")


def _sanitize_output(text: str) -> str:
    return _ANSI_ESCAPE_PATTERN.sub("", text).replace("\r", "")


def _marker_residue_index(text: str) -> int:
    fragment_match = _MARKER_FRAGMENT_PATTERN.search(text)
    if fragment_match is not None:
        return fragment_match.start()

    for overlap_length in range(min(len(_MARKER_FRAGMENT_HEAD), len(text)), 0, -1):
        if text.endswith(_MARKER_FRAGMENT_HEAD[:overlap_length]):
            return len(text) - overlap_length

    return len(text)


class InteractiveShellSession:
    def __init__(self, session_id: str, exec_instance: Any, stream: Any, workspace: Path) -> None:
        self._session_id = session_id
        self._exec_instance = exec_instance
        self._stream = stream
        self._cwd = str(workspace)
        self._buffer = ""
        self._buffer_lock = asyncio.Lock()
        self._command_lock = asyncio.Lock()
        self._pending_marker_pattern: re.Pattern[str] | None = None
        self._reader_task: asyncio.Task[None] | None = None
        self._last_used_at = datetime.now(UTC)
        self._broken_reason: str | None = None

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def cwd(self) -> str:
        return self._cwd

    @property
    def last_used_at(self) -> datetime:
        return self._last_used_at

    @property
    def is_broken(self) -> bool:
        return self._broken_reason is not None

    async def initialize(self) -> None:
        self._reader_task = asyncio.create_task(self._read_loop())
        await self._write(f"{SESSION_INIT_COMMANDS}\n")
        await asyncio.sleep(SESSION_DRAIN_SECONDS)
        await self._reset_buffer()

        health_check = await self.execute(":", SESSION_READY_TIMEOUT_SECONDS)
        if health_check.timed_out:
            self._mark_broken("shell did not respond to the initialization probe")
            raise SessionBrokenError(self._session_id, "shell did not respond to the initialization probe")

    async def execute(self, command: str, timeout: int) -> SessionExecutionResult:
        async with self._command_lock:
            self._raise_if_broken()
            token = uuid4().hex
            marker = f"{SESSION_END_MARKER_PREFIX}{token}__"
            marker_pattern = re.compile(rf"{re.escape(marker)}(-?\d+)__(.*?)__LP_DONE", re.DOTALL)
            framed = f'{{ :\n{command}\n}}; __lp_code=$?; printf \'\\n{marker}%d__%s__LP_DONE\\n\' "$__lp_code" "$(pwd)"\n'

            self._pending_marker_pattern = None
            await self._reset_buffer()
            await self._write(framed)

            match = await self._await_marker(marker_pattern, timeout)
            self._last_used_at = datetime.now(UTC)

            if match is None:
                logger.warning(f"Session execute timed out session={self._session_id} timeout={timeout}")
                self._pending_marker_pattern = marker_pattern
                stdout_text, truncated = truncate_output(await self._drain_buffer(), settings.output_char_limit)
                return SessionExecutionResult(stdout=stdout_text, exit_code=None, cwd=self._cwd, truncated=truncated, timed_out=True)

            self._cwd = _sanitize_output(match.group(2))

            output = await self._consume_through(match)
            stdout_text, truncated = truncate_output(output, settings.output_char_limit)
            return SessionExecutionResult(stdout=stdout_text, exit_code=int(match.group(1)), cwd=self._cwd, truncated=truncated, timed_out=False)

    async def send_input(self, text: str, add_newline: bool, timeout: float) -> SessionInputResult:
        async with self._command_lock:
            self._raise_if_broken()
            pending_marker_pattern = self._pending_marker_pattern
            await self._write(f"{text}\n" if add_newline else text)

            if pending_marker_pattern is None:
                await asyncio.sleep(SESSION_DRAIN_SECONDS)
                match = None
            else:
                match = await self._await_marker(pending_marker_pattern, timeout)

            self._last_used_at = datetime.now(UTC)

            if match is None:
                output_text, truncated = truncate_output(await self._drain_buffer(), settings.output_char_limit)
                return SessionInputResult(output=output_text, exit_code=None, cwd=self._cwd, truncated=truncated, completed=False)

            self._pending_marker_pattern = None
            self._cwd = _sanitize_output(match.group(2))

            output_text, truncated = truncate_output(await self._consume_through(match), settings.output_char_limit)
            return SessionInputResult(output=output_text, exit_code=int(match.group(1)), cwd=self._cwd, truncated=truncated, completed=True)

    async def close(self) -> None:
        if self._reader_task is not None:
            self._reader_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._reader_task

        if not self.is_broken:
            with contextlib.suppress(Exception):
                await self._stream.write_in(b"exit\n")

        try:
            await self._stream.close()
        except Exception as error:
            logger.warning(f"Error closing session {self._session_id}: {error}")

    async def _await_marker(self, marker_pattern: re.Pattern[str], timeout: float) -> re.Match[str] | None:
        try:
            async with asyncio.timeout(timeout):
                while True:
                    async with self._buffer_lock:
                        match = marker_pattern.search(self._buffer)

                    if match is not None:
                        return match

                    await asyncio.sleep(SESSION_READ_INTERVAL_SECONDS)
        except TimeoutError:
            return None

    async def _consume_through(self, match: re.Match[str]) -> str:
        async with self._buffer_lock:
            snapshot = self._buffer
            self._buffer = snapshot[match.end() :]

        return _sanitize_output(snapshot[: match.start()]).strip("\n")

    async def _drain_buffer(self) -> str:
        async with self._buffer_lock:
            snapshot = self._buffer
            residue_index = _marker_residue_index(snapshot)
            self._buffer = snapshot[residue_index:]

        return _sanitize_output(snapshot[:residue_index]).strip("\n")

    async def _reset_buffer(self) -> None:
        async with self._buffer_lock:
            self._buffer = ""

    def _raise_if_broken(self) -> None:
        if self._broken_reason is not None:
            raise SessionBrokenError(self._session_id, self._broken_reason)

    def _mark_broken(self, reason: str) -> None:
        if self._broken_reason is None:
            self._broken_reason = reason
            logger.warning(f"Session marked broken session={self._session_id} reason={reason}")

    async def _write(self, text: str) -> None:
        try:
            await self._stream.write_in(text.encode())
        except (AssertionError, RuntimeError, OSError) as stream_error:
            reason = str(stream_error) or f"{type(stream_error).__name__} while writing to the shell stream"
            self._mark_broken(reason)
            raise SessionBrokenError(self._session_id, reason) from stream_error

    async def _read_loop(self) -> None:
        try:
            while True:
                message = await self._stream.read_out()
                if message is None:
                    self._mark_broken("shell stream closed by the sandbox")
                    return

                async with self._buffer_lock:
                    self._buffer += message.data.decode(errors="replace").replace("\r", "")
                    if len(self._buffer) > SESSION_BUFFER_MAX_CHARS:
                        self._buffer = self._buffer[-SESSION_BUFFER_MAX_CHARS:]
        except asyncio.CancelledError:
            raise
        except Exception as error:
            self._mark_broken(str(error) or f"{type(error).__name__} while reading from the shell stream")
            logger.warning(f"Session reader stopped session={self._session_id}: {error!r}")

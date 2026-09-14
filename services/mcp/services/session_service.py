import asyncio
import contextlib
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from config.constants import SESSION_REAPER_INTERVAL_SECONDS
from domain.exceptions import SessionBrokenError, SessionNotFoundError
from domain.models import SessionExecutionResult, SessionInfo, SessionInputResult
from infrastructure.docker.sandbox_client import SandboxClient
from services.session import InteractiveShellSession
from utils.logger import logger


class SessionService:
    def __init__(self, sandbox_client: SandboxClient, workspace: Path, default_timeout: int, idle_ttl: int) -> None:
        self._sandbox_client = sandbox_client
        self._workspace = workspace
        self._default_timeout = default_timeout
        self._idle_ttl = idle_ttl
        self._sessions: dict[str, InteractiveShellSession] = {}
        self._created_at: dict[str, datetime] = {}
        self._reaper_task: asyncio.Task[None] | None = None

    async def create(self, cwd: str, env: dict[str, str]) -> SessionInfo:
        self._ensure_reaper()

        session_id = uuid4().hex[:12]
        exec_instance, stream = await self._sandbox_client.open_interactive_stream(cwd=cwd, env=env)
        session = InteractiveShellSession(session_id, exec_instance, stream, Path(cwd))

        try:
            await session.initialize()
        except SessionBrokenError:
            await session.close()
            logger.warning(f"Discarded session that failed to initialize session={session_id}")
            raise

        self._sessions[session_id] = session
        self._created_at[session_id] = datetime.now(UTC)
        return self._to_info(session)

    async def execute(self, session_id: str, command: str, timeout: int | None) -> SessionExecutionResult:
        session = self._require(session_id)
        effective_timeout = timeout if timeout is not None else self._default_timeout

        try:
            return await session.execute(command, effective_timeout)
        except SessionBrokenError:
            await self._evict(session_id)
            raise

    async def send_input(self, session_id: str, text: str, add_newline: bool, timeout: float) -> SessionInputResult:
        session = self._require(session_id)

        try:
            return await session.send_input(text, add_newline, timeout)
        except SessionBrokenError:
            await self._evict(session_id)
            raise

    async def close(self, session_id: str) -> None:
        session = self._require(session_id)
        await session.close()
        del self._sessions[session_id]
        del self._created_at[session_id]

    async def shutdown(self) -> None:
        if self._reaper_task is not None:
            self._reaper_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._reaper_task
            self._reaper_task = None

        for session in list(self._sessions.values()):
            await session.close()

        self._sessions.clear()
        self._created_at.clear()

    def _ensure_reaper(self) -> None:
        if self._idle_ttl <= 0:
            return
        if self._reaper_task is None or self._reaper_task.done():
            self._reaper_task = asyncio.create_task(self._reap_idle_sessions())

    async def _reap_idle_sessions(self) -> None:
        cutoff = timedelta(seconds=self._idle_ttl)
        while True:
            await asyncio.sleep(SESSION_REAPER_INTERVAL_SECONDS)

            now = datetime.now(UTC)
            stale_ids = [session_id for session_id, session in list(self._sessions.items()) if session.is_broken or now - session.last_used_at > cutoff]
            for session_id in stale_ids:
                try:
                    await self.close(session_id)
                except SessionNotFoundError:
                    continue

                logger.info(f"Reaped session session={session_id} idle_ttl={self._idle_ttl}")

    async def _evict(self, session_id: str) -> None:
        try:
            await self.close(session_id)
        except SessionNotFoundError:
            return

        logger.warning(f"Evicted broken session session={session_id}")

    def _require(self, session_id: str) -> InteractiveShellSession:
        session = self._sessions.get(session_id)
        if session is None:
            raise SessionNotFoundError(session_id)

        return session

    def _to_info(self, session: InteractiveShellSession) -> SessionInfo:
        return SessionInfo(
            session_id=session.session_id,
            cwd=session.cwd,
            created_at=self._created_at[session.session_id],
            last_used_at=session.last_used_at,
        )

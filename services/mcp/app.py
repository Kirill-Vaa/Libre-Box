import asyncio
import contextlib
import signal
from collections.abc import AsyncIterator

import uvicorn
from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from starlette.types import ASGIApp

from auth_gate.factory import create_auth_app
from config.settings import AppSettings
from config.validation import validate_settings
from infrastructure.docker.sandbox_client import SandboxClient
from infrastructure.http.request_context import RequestContextMiddleware
from mcp_server.factory import create_mcp_server
from services.container import ServiceContainer
from utils.logger import configure_file_sink, logger, set_console_level


async def _healthz(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


class Application:
    def __init__(self, application_settings: AppSettings) -> None:
        self._settings = application_settings
        self._sandbox_client: SandboxClient | None = None
        self._container: ServiceContainer | None = None
        self._servers: list[uvicorn.Server] = []
        self._shutdown_event = asyncio.Event()

    async def setup(self) -> None:
        self._configure_logging()
        logger.info("Application setup started")

        validate_settings(self._settings)

        self._sandbox_client = SandboxClient(self._settings.sandbox_container_name)
        await self._sandbox_client.start()
        self._container = ServiceContainer(self._settings, self._sandbox_client)
        self._build_servers(self._container)

        logger.info("Application setup completed")

    async def run(self) -> None:
        if not self._servers:
            raise RuntimeError("Application is not set up, call setup() first")

        running_loop = asyncio.get_running_loop()
        for shutdown_signal in (signal.SIGINT, signal.SIGTERM):
            with contextlib.suppress(NotImplementedError):
                running_loop.add_signal_handler(shutdown_signal, self._trigger_shutdown)

        server_tasks = [asyncio.create_task(server.serve()) for server in self._servers]
        shutdown_task = asyncio.create_task(self._shutdown_event.wait())

        await asyncio.wait({*server_tasks, shutdown_task}, return_when=asyncio.FIRST_COMPLETED)
        self._request_servers_exit()
        shutdown_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await shutdown_task

        await asyncio.gather(*server_tasks, return_exceptions=True)

    async def shutdown(self) -> None:
        logger.info("Application shutdown started")

        self._request_servers_exit()
        if self._container is not None:
            await self._container.session_service.shutdown()
        if self._sandbox_client is not None:
            await self._sandbox_client.close()

        logger.info("Application shutdown completed")

    def _trigger_shutdown(self) -> None:
        self._shutdown_event.set()

    def _configure_logging(self) -> None:
        set_console_level(self._settings.log_level)
        configure_file_sink(self._settings.log_level, self._settings.log_serialize)

    def _build_servers(self, container: ServiceContainer) -> None:
        mcp = create_mcp_server(container)
        transport_security = TransportSecuritySettings(allowed_hosts=["mcp:*", "localhost:*", "127.0.0.1:*"], allowed_origins=["*"])
        mcp_http_application = mcp.streamable_http_app(transport_security=transport_security)

        @contextlib.asynccontextmanager
        async def _run_session_manager(_: Starlette) -> AsyncIterator[None]:
            async with mcp.session_manager.run():
                yield

        mcp_application = Starlette(routes=[Route("/healthz", _healthz, methods=["GET"]), Mount("/", app=mcp_http_application)], lifespan=_run_session_manager)

        access_secret = self._settings.jwt_secret.get_secret_value() if self._settings.jwt_secret is not None else ""
        refresh_secret = self._settings.jwt_refresh_secret.get_secret_value() if self._settings.jwt_refresh_secret is not None else ""
        if not access_secret and not refresh_secret:
            logger.critical("No JWT secret configured, FileBrowser auth gate will reject every request")

        auth_application = create_auth_app(access_secret, refresh_secret)

        self._servers = [
            self._build_server(mcp_application, self._settings.mcp_port),
            self._build_server(auth_application, self._settings.auth_port),
        ]

    def _request_servers_exit(self) -> None:
        for server in self._servers:
            server.should_exit = True

    @staticmethod
    def _build_server(application: ASGIApp, port: int) -> uvicorn.Server:
        server_config = uvicorn.Config(app=RequestContextMiddleware(application), host="0.0.0.0", port=port, log_config=None, access_log=False, loop="asyncio")
        server = uvicorn.Server(server_config)

        logger.info(f"Configured uvicorn server port={port}")
        return server

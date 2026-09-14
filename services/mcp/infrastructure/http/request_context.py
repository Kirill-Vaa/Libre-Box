from collections.abc import Iterable
from typing import Final
from uuid import uuid4

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from utils.logger import logger


_REQUEST_ID_HEADER: Final[bytes] = b"x-request-id"


class RequestContextMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self._app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self._app(scope, receive, send)
            return

        request_id = self._extract_request_id(scope) or uuid4().hex
        encoded_request_id = request_id.encode()

        async def send_with_request_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                message.setdefault("headers", []).append((_REQUEST_ID_HEADER, encoded_request_id))
            await send(message)

        with logger.contextualize(request_id=request_id):
            await self._app(scope, receive, send_with_request_id)

    @staticmethod
    def _extract_request_id(scope: Scope) -> str | None:
        headers: Iterable[tuple[bytes, bytes]] = scope.get("headers", [])
        for header_name, header_value in headers:
            if header_name == _REQUEST_ID_HEADER:
                return header_value.decode(errors="replace")

        return None

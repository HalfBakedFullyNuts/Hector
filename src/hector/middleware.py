"""Custom ASGI middleware components."""

import contextvars
import uuid
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

_request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("request_id")


def get_request_id() -> str | None:
    """Return the current request id if available."""

    try:
        return _request_id_ctx.get()
    except LookupError:  # pragma: no cover - defensive
        return None


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Ensure every request has an `X-Request-ID` header available."""

    header_name = "X-Request-ID"

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get(self.header_name) or str(uuid.uuid4())
        token = _request_id_ctx.set(request_id)
        try:
            response = await call_next(request)
        finally:
            _request_id_ctx.reset(token)

        response.headers.setdefault(self.header_name, request_id)
        request.state.request_id = request_id
        return response


def middleware_stack() -> list[tuple[Callable[..., BaseHTTPMiddleware], dict]]:
    """Return middleware factory definitions for the application."""

    return [(RequestIDMiddleware, {})]

"""One id per request, carried by a contextvar, echoed in the response.

The log format prints ``[%(request_id)s]`` on every line, which is what lets a
reader -- human or agent -- pull the four lines of one failing request out of an
interleaved file. An incoming ``X-Request-ID`` is honoured so a caller (the e2e
harness, a reverse proxy) can stitch its own trace to ours; otherwise a short
random id is minted. The header is echoed back either way.
"""

import contextvars
import uuid
from typing import Final

from starlette.types import ASGIApp, Message, Receive, Scope, Send

_HEADER: Final = b"x-request-id"

_request_id: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)


def current_request_id() -> str | None:
    return _request_id.get()


class RequestIdMiddleware:
    """Pure ASGI middleware: no BaseHTTPMiddleware, so no response buffering."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        incoming = next((value for key, value in scope.get("headers", []) if key == _HEADER), b"")
        request_id = incoming.decode("latin-1")[:64] or uuid.uuid4().hex[:12]
        token = _request_id.set(request_id)

        async def send_with_header(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.setdefault("headers", []))
                headers.append((_HEADER, request_id.encode("latin-1")))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_with_header)
        except BaseException:
            # Deliberately NOT reset here, and the asymmetry is the whole point.
            # Starlette's `ServerErrorMiddleware` is built OUTSIDE every
            # middleware added with `add_middleware` (`build_middleware_stack`),
            # so it catches this exception only after it has passed through
            # here -- and the catch-all in `app/core/errors.py` logs it after
            # that, with uvicorn logging it once more when the middleware
            # re-raises. A reset taken on the way out blanks `[%(request_id)s]`
            # on exactly the records an operator opens the log for: the failures.
            # Measured by
            # `tests/integration/test_app_integration.py::test_a_failing_real_route_logs_no_value_and_keeps_its_request_id`,
            # which read `[-]` before this branch existed.
            #
            # Nothing leaks by not resetting. The contextvar is set per request
            # and every request sets its own before doing anything else, so the
            # only value this leaves behind is one that the next request
            # overwrites. A `finally` would be the tidier-looking code and the
            # wrong one.
            raise
        else:
            _request_id.reset(token)


__all__ = ["RequestIdMiddleware", "current_request_id"]

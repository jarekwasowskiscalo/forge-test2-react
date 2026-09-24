"""Centralized JSON error handling.

`register_error_handlers(app)` registers three explicit, independent
exception handlers on a FastAPI app, in an order that keeps specific
handling from being swallowed by generic handling:

1. `HTTPException` -- passthrough via Starlette's own default handler, so
   existing behavior (e.g. 404s raised via `HTTPException(status_code=404,
 ...)`) is unchanged.
2. `RequestValidationError` -- returns 422 with a structured JSON body
   containing the Pydantic error details.
3. `Exception` (generic/catch-all) -- logs the full exception server-side
   and returns a FIXED, sanitized JSON body. This handler must never leak
   the exception's message or a traceback to the client.

FastAPI/Starlette dispatch exception handlers by exact type match, not by
registration order. Because `HTTPException` and `RequestValidationError`
are themselves subclasses of `Exception`, they must each be registered
explicitly -- otherwise a catch-all `Exception` handler would intercept
them before they ever reach a more specific handler.

**`CatchAllMiddleware` is here too, and it is not a fourth handler.** The
`Exception` key above is the one FastAPI lifts out of the handler dict and
hands to `ServerErrorMiddleware`, which Starlette builds OUTSIDE every
`add_middleware` middleware. That layer answers through the raw `send`, so for
as long as it was the only thing catching an unhandled exception, a 500 left
the process without passing through `app/core/request_id.py`'s or
`app/core/robots.py`'s wrappers -- and so without `X-Request-ID` or, on a
preview, `X-Robots-Tag`. Both are promised without exception by
`docs/operations.md` and `docs/security.md`, and 500 was the one response that
kept neither. The middleware below catches the same exception one layer INSIDE
those wrappers, which is the whole repair: same body, same log, stamped.

Both live in this module because they are one subject -- what an unhandled
exception becomes -- and the fixed body is then defined once.
"""

import logging
from typing import cast

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.responses import Response
from starlette.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger(__name__)

#: The body a client gets for any unhandled exception. A constant because two
#: layers now answer with it and a second literal is a second thing to keep in
#: step: `CatchAllMiddleware` sends it on the real application, and
#: `_handle_generic_exception` sends it wherever the middleware is not mounted.
_SANITIZED_500: dict[str, str] = {"detail": "internal server error"}

#: Set on the ASGI scope by `CatchAllMiddleware` once it has written the record
#: for this request. `ServerErrorMiddleware` calls the registered handler even
#: when the response has already started, so without this the same exception
#: would produce two identical application records. The scope is per request and
#: is the same object `ServerErrorMiddleware` wraps in its `Request`, so this
#: needs no global and leaks nothing between requests.
_LOGGED = "app_unhandled_logged"

_UNHANDLED = "Unhandled exception while processing request"

# Every handler below takes `Exception` and returns `Response`, because that is
# the signature Starlette's `add_exception_handler` accepts -- it dispatches by
# exact type and cannot express "this handler only ever sees an HTTPException"
# in the callable's type. The `cast` records the invariant Starlette guarantees
# at the one line where the narrower type is needed, which is more honest than a
# blanket `type: ignore` on the registration and keeps the body type-checked.


async def _handle_http_exception(request: Request, exc: Exception) -> Response:
    """Delegate to FastAPI's default HTTPException handler (passthrough)."""
    return await http_exception_handler(request, cast(HTTPException, exc))


async def _handle_validation_error(request: Request, exc: Exception) -> Response:
    """Return a structured 422 JSON payload with Pydantic error details."""
    return JSONResponse(
        status_code=422,
        content={"detail": jsonable_encoder(cast(RequestValidationError, exc).errors())},
    )


async def _handle_generic_exception(request: Request, exc: Exception) -> Response:
    """Log the exception's type and position server-side; return a fixed 500 body.

    Two promises, and this docstring used to make only the first. **The
    response body** is a hardcoded string and never includes any part of `exc`'s
    message or a traceback. **The log record** is held to the same standard by
    `ExceptionSummaryFilter`, on every sink `app/core/logging_config.py`
    configures: the record carries the exception's type, the frames it passed
    through and the request id, and never `str(exc)`, a bind parameter or a
    driver's `DETAIL:` line.

    The silence about the record was the defect. The rule belongs to the layer
    that EMITS a record, because this is not the only place one is emitted --
    uvicorn logs the same exception again once `ServerErrorMiddleware` re-raises
    it, and no edit here reaches that.

    **This handler no longer runs first on the real application.**
    `CatchAllMiddleware` is mounted inside the header wrappers and catches the
    exception there, so by the time `ServerErrorMiddleware` calls this the
    response has already gone out -- Starlette skips its own send because the
    response has started, and only the re-raise is left. The record was already
    written, which is what the scope flag says, so writing a second identical
    one here would be noise an operator has to page through at three in the
    morning.

    It is not dead, and that is why the logging is conditional rather than
    deleted: an exception raised by a layer OUTSIDE `CatchAllMiddleware` --
    `RequestIdMiddleware`, `NoIndexMiddleware` -- still arrives here unlogged,
    and so does one on any app built without the middleware, which is how
    `tests/unit/test_errors.py` builds its own.
    """
    if not request.scope.get("state", {}).get(_LOGGED):
        logger.exception(_UNHANDLED, exc_info=exc)
    return JSONResponse(status_code=500, content=_SANITIZED_500)


class CatchAllMiddleware:
    """Answers an unhandled exception from INSIDE the header wrappers.

    Mounted in `app/main.py` before `RequestIdMiddleware`, which makes it the
    innermost user middleware: `add_middleware` inserts at the front of the
    list and the front of that list is the outermost layer, so the first one
    added is the last one entered. The resulting chain is

        ServerErrorMiddleware -> NoIndex -> RequestId -> CatchAll -> router

    and the 500 this sends therefore travels out through both `send_with_header`
    wrappers instead of past them.

    **It re-raises, and that is a decision rather than an oversight.** The
    response is already complete, so `ServerErrorMiddleware` skips its own send
    and only re-raises in turn -- which is what keeps
    `TestClient(raise_server_exceptions=True)`, the default the whole test suite
    runs on, surfacing the real traceback when a route fails by accident instead
    of a 500 somebody has to go digging for. It is also what keeps uvicorn's own
    record, which `app/core/request_id.py` and
    `tests/unit/test_log_content_policy.py` both reason about. Swallowing here
    would buy one fewer log line and cost all of that.

    Pure ASGI, like the two middlewares it sits inside: no response buffering,
    and nothing that needs a request object built.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        try:
            await self.app(scope, receive, send)
        except Exception as exc:
            # Marked before the record is written, not after: the flag says
            # "this request's record is this layer's business", and an exception
            # from the logging call itself must not hand the duplicate back.
            scope.setdefault("state", {})[_LOGGED] = True
            logger.exception(_UNHANDLED, exc_info=exc)
            await JSONResponse(status_code=500, content=_SANITIZED_500)(scope, receive, send)
            raise


def register_error_handlers(app: FastAPI) -> None:
    """Register the HTTPException, RequestValidationError, and generic
    Exception handlers on `app`, in that order.
    """
    app.add_exception_handler(HTTPException, _handle_http_exception)
    app.add_exception_handler(RequestValidationError, _handle_validation_error)
    app.add_exception_handler(Exception, _handle_generic_exception)

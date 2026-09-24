"""What a 500 carries out, and what it must not carry between requests.

Three properties, and every one of them was untested before this file existed --
which is why the asymmetry below survived: it is invisible from a happy path.

1. **A 500 carries the same headers every other response carries.** Starlette
   builds `ServerErrorMiddleware` OUTSIDE every `add_middleware` middleware
   (`starlette/applications.py`: the stack is `[ServerErrorMiddleware] +
   user_middleware + [ExceptionMiddleware]`), and it sends its sanitized
   response through the RAW `send` rather than through anything a user
   middleware wrapped. So until `CatchAllMiddleware` existed, a 500 was the one
   response that reached the client with neither `X-Request-ID` nor, on a
   preview, `X-Robots-Tag` -- the two headers `docs/operations.md` and
   `docs/security.md` promise without exception. `tests/unit/test_robots.py`
   covers a 200 and a 404, and a routing 404 is raised INSIDE the wrappers, so
   it never reached this.

2. **The repair does not widen the policy.** The `X-Robots-Tag` decision lives
   in `app/main.py` and nowhere else (`app/core/robots.py` § the environment
   set). A fix that stamped the header from the error path would have put
   `noindex` on stage and production the moment somebody crashed a route there,
   so the `local` variant below is not a symmetry exercise -- it is the actual
   risk of this repair, asserted.

3. **The request id is per request and does not leak between them.** The
   contextvar is set on the way in and, on the failure path, deliberately NOT
   reset (`app/core/request_id.py` says why: the catch-all logs afterwards). An
   asymmetric set/reset is exactly the shape that leaks in a warm container --
   `app/lambda_handler.py` runs the application through `Mangum(app,
   lifespan="off")` on a shared loop -- so the concurrency test drives two
   overlapping requests and reads both answers.

No database: the route that fails is synthetic, so this belongs in `tests/unit/`.
`APP_ENV` is read at import time (`app/main.py` decides the middleware there and
not per request), so these tests reload `app.main`, which is the pattern
`tests/unit/test_spa_fallback.py` already established for the same reason.

The one async test in the repository is here, and it is written as a SYNC test
around `asyncio.run`: `pytest-asyncio` is not a dependency, `anyio` is installed
only transitively, and this needs neither.
"""

import asyncio
import contextlib
import importlib
import io
import logging
from collections.abc import Iterator

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

import app.main
from app.core.logging_config import build_config, configure_logging
from app.core.request_id import current_request_id

#: The header value `app/core/robots.py` declares, repeated here on purpose: a
#: test that imported the constant would pass if somebody emptied it.
NOINDEX = "noindex, nofollow"

#: Never appears in a response body or a log record. `tests/unit/test_errors.py`
#: and `tests/unit/test_log_content_policy.py` hold that rule in general; this
#: file only has to not become the hole in it.
LEAK_MARKER = "SYNTHETIC-PRIVATE-ENVELOPE"

_RECORD = "Unhandled exception while processing request"


def _reload_main() -> FastAPI:
    reloaded: FastAPI = importlib.reload(app.main).app
    return reloaded


def _with_crashing_route(built: FastAPI) -> FastAPI:
    """Add a route that raises, ahead of the SPA catch-all that would shadow it.

    `app/main.py` registers `/{full_path:path}` last and Starlette matches in
    registration order, so a route appended here would answer 404 rather than
    raise. Inserted at position 0 instead -- and on a freshly reloaded module,
    so nothing is left behind for the next test.
    """

    async def crash(request: Request) -> None:
        raise RuntimeError(LEAK_MARKER)

    built.router.routes.insert(0, Route("/api/crash-for-test", crash, methods=["GET"]))
    return built


@contextlib.contextmanager
def _application_sink() -> Iterator[io.StringIO]:
    """A sink assembled from the application's OWN declaration, ahead of the rest.

    The same helper `tests/integration/test_app_integration.py` uses, and for
    the same reason: read the filters and the format string out of
    `build_config()` rather than repeating them, so a sink added to the
    declaration is covered here without an edit. Inserted at position 0 --
    appended, it would measure a record another handler's filter had already
    sanitised.
    """
    configure_logging()
    config = build_config("INFO", "")
    formatters = config["formatters"]
    filters = config["filters"]
    handlers = config["handlers"]
    assert isinstance(formatters, dict) and isinstance(filters, dict)
    assert isinstance(handlers, dict)

    buffer = io.StringIO()
    sink = logging.StreamHandler(buffer)
    sink.setFormatter(logging.Formatter(formatters["standard"]["format"]))
    for name in handlers["console"]["filters"]:
        sink.addFilter(filters[name]["()"]())

    root = logging.getLogger()
    root.handlers.insert(0, sink)
    previous = root.level
    root.setLevel(logging.INFO)
    try:
        yield buffer
    finally:
        root.setLevel(previous)
        root.handlers.remove(sink)


@pytest.fixture
def preview_app(monkeypatch: pytest.MonkeyPatch) -> Iterator[FastAPI]:
    """The real application as a preview builds it, with one failing route."""
    monkeypatch.setenv("APP_ENV", "preview")
    yield _with_crashing_route(_reload_main())
    monkeypatch.undo()
    _reload_main()


@pytest.fixture
def local_app(monkeypatch: pytest.MonkeyPatch) -> Iterator[FastAPI]:
    """The same application where `X-Robots-Tag` must NOT apply."""
    monkeypatch.setenv("APP_ENV", "local")
    yield _with_crashing_route(_reload_main())
    monkeypatch.undo()
    _reload_main()


def test_a_500_on_a_preview_carries_both_headers_and_one_record(
    preview_app: FastAPI,
) -> None:
    """The response an operator actually gets, and the record they search by."""
    # `raise_server_exceptions=False` because `ServerErrorMiddleware` re-raises
    # after the response has gone out, and the test transport would surface that
    # instead of the answer. Deliberately kept: the default client is what gives
    # every OTHER test a real traceback when a route fails by accident.
    client = TestClient(preview_app, raise_server_exceptions=False)

    with _application_sink() as buffer:
        response = client.get("/api/crash-for-test", headers={"X-Request-ID": "audit-123"})
        written = buffer.getvalue()

    assert response.status_code == 500
    assert response.json() == {"detail": "internal server error"}
    assert LEAK_MARKER not in response.text, "the exception's text reached the response"

    assert response.headers.get("x-request-id") == "audit-123", (
        "the 500 answered without the id the client sent, so nothing ties the "
        "response in somebody's hand to the line in the log"
    )
    assert response.headers.get("x-robots-tag") == NOINDEX, (
        "a preview's 500 is indexable, which docs/security.md promises it is not"
    )

    assert _RECORD in written, "the catch-all wrote nothing at all"
    assert "audit-123" in written, "the record lost the request id"
    assert LEAK_MARKER not in written, "the exception's text reached the record"
    assert written.count(_RECORD) == 1, (
        "one unhandled exception produced more than one application record:\n" + written
    )


def test_a_500_outside_a_preview_is_not_hidden_from_search(local_app: FastAPI) -> None:
    """The repair must not widen the `noindex` policy to stage and production.

    The environment decision lives in `app/main.py` and is taken once, at
    import. If the header were stamped from the error path instead, this is the
    test that would catch it -- and `tests/unit/test_robots.py` would not,
    because it never reaches a 500.
    """
    client = TestClient(local_app, raise_server_exceptions=False)
    response = client.get("/api/crash-for-test", headers={"X-Request-ID": "audit-local"})

    assert response.status_code == 500
    assert response.headers.get("x-request-id") == "audit-local"
    assert "x-robots-tag" not in response.headers, (
        "a local run answered `noindex`, so the repair moved the decision out of "
        "app/main.py and stage and production would be hidden next"
    )


def test_two_overlapping_requests_keep_their_own_request_ids(preview_app: FastAPI) -> None:
    """Forced interleave, one healthy request and one that fails.

    `asyncio.gather` is not enough on its own -- two fast requests can run to
    completion one after the other and prove nothing. The `await` inside the
    route below is what guarantees the second request sets the contextvar while
    the first is still in flight.
    """

    async def slow(request: Request) -> JSONResponse:
        await asyncio.sleep(0.05)
        seen = current_request_id()
        return JSONResponse({"seen": seen})

    preview_app.router.routes.insert(0, Route("/api/slow-for-test", slow, methods=["GET"]))

    async def drive() -> tuple[httpx.Response, httpx.Response]:
        # `raise_app_exceptions=False` is the ASGI-transport equivalent of
        # TestClient's `raise_server_exceptions=False`, and needed for the same
        # reason: `ServerErrorMiddleware` re-raises after the response has gone
        # out, and this test is about the response.
        transport = httpx.ASGITransport(app=preview_app, raise_app_exceptions=False)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            first, second = await asyncio.gather(
                client.get("/api/slow-for-test", headers={"X-Request-ID": "first-id"}),
                client.get("/api/crash-for-test", headers={"X-Request-ID": "second-id"}),
            )
            return first, second

    with _application_sink() as buffer:
        healthy, failing = asyncio.run(drive())
        written = buffer.getvalue()

    assert healthy.status_code == 200
    assert healthy.json() == {"seen": "first-id"}, (
        "the healthy request read another request's id out of the contextvar"
    )
    assert healthy.headers.get("x-request-id") == "first-id"

    assert failing.status_code == 500
    assert failing.headers.get("x-request-id") == "second-id", (
        "the failing request answered with the other request's id"
    )

    error_lines = [line for line in written.splitlines() if _RECORD in line]
    assert len(error_lines) == 1, f"expected exactly one error record:\n{written}"
    assert "second-id" in error_lines[0], (
        f"the error record carries the wrong request's id:\n{error_lines[0]}"
    )
    assert "first-id" not in error_lines[0]

    assert current_request_id() is None, (
        "a request id outlived the request, so the next invocation on a warm "
        "container would inherit it (app/lambda_handler.py runs on a shared loop)"
    )

"""End-to-end smoke tests for the assembled application.

Exercises the REAL `app.main:app` instance (via the shared `client` fixture)
rather than a throwaway app, to prove health, the guestbook resource and the
centralised error handlers are all wired together correctly on the actual
entrypoint -- not merely verified in isolation as in the per-resource suites.

This is a lightweight smoke suite. Exhaustive endpoint-level assertions -- every
refusal, every boundary -- belong to `test_guestbook_entries_router.py` and
`tests/unit/`, not here.

What this file proves:
- the application accepts HTTP requests once started, and stays reachable
  across several of them
- the documented default listening address and port apply -- not exercised
  directly by TestClient, but satisfied by `app/main.py` adding no host or
  port override
- an undefined `/api` route answers a JSON not-found rather than the SPA shell
- adding a resource router does not break the health endpoint
- invalid input against a real endpoint returns a structured 4xx JSON error
- an unhandled exception inside a real route returns a sanitized 5xx body
  with no leaked exception details

A note on that last one: `tests/unit/test_errors.py` already proves the
500-sanitisation *mechanism* in isolation, but only via a throwaway app with
routes that deliberately raise -- it never exercises a real route. The test
below closes that gap by monkeypatching the real service call used by
`GET /api/guestbook-entries` to raise, without adding any permanent debug or
crash route to the app.
"""

import io
import logging
from collections.abc import Iterator
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient

from app.core.logging_config import build_config, configure_logging
from app.main import app as real_app

ENTRIES = "/api/guestbook-entries"


@pytest.fixture(autouse=True)
def isolated_database(fresh_database):
    """Delegates to the shared fixture, which *discovers* every module holding a
    `SessionLocal` instead of naming three. Without this, every POST below wrote
    into the session database and the rows outlived the test -- the leak
    `tests/fitness/test_test_layout.py` now refuses."""


def test_health_endpoint_responds_on_real_app(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    #: Present on the real aggregate too, not only on the isolated router: the
    #: response model is what puts them there, and a router mounted alone is where
    #: a lost one would go unnoticed.
    assert response.json().keys() == {"status", "environment", "version"}


def test_the_resource_list_responds_on_real_app(client: TestClient) -> None:
    response = client.get(ENTRIES)

    assert response.status_code == 200
    assert isinstance(response.json()["items"], list)


def test_creating_through_the_real_app_answers_201(client: TestClient) -> None:
    response = client.post(ENTRIES, json={"author": "Anna", "message": "Good morning!"})

    assert response.status_code == 201
    assert response.json()["author"] == "Anna"


def test_adding_a_resource_router_did_not_shadow_health(client: TestClient) -> None:
    """Both routers are mounted on one aggregate, in a fixed order.

    The pairing is the point: a router registered after the SPA catch-all would
    be swallowed and answer `index.html` with status 200, so asserting each in
    isolation would miss exactly the failure this ordering exists to prevent.
    """
    assert client.get("/api/health").status_code == 200
    assert client.get(ENTRIES).status_code == 200


def test_undefined_api_route_returns_json_404_on_real_app(client: TestClient) -> None:
    """An undefined `/api/*` path returns a JSON 404, never the SPA shell.

    The catch-all added in app/main.py matches `/api/...` too, so it guards
    on the prefix and re-raises. Without that guard this would answer 200
    with `index.html` and the frontend would fail parsing HTML as JSON.
    See tests/unit/test_spa_fallback.py for the non-API side of the same route.
    """
    response = client.get("/api/this-does-not-exist")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/json")
    assert "detail" in response.json()


def test_an_invalid_body_returns_422_via_the_real_error_handlers(client: TestClient) -> None:
    """Proves `register_error_handlers` is active on the real app, not just on the
    isolated throwaway app used by `tests/unit/test_errors.py`."""
    response = client.post(ENTRIES, json={})

    assert response.status_code == 422
    body = response.json()
    assert isinstance(body["detail"], list)


def test_multiple_sequential_requests_remain_reachable(client: TestClient) -> None:
    """A second request after a prior one still succeeds."""
    assert client.get("/api/health").status_code == 200
    assert client.get(ENTRIES).status_code == 200


# A distinctive marker string, unique to this test, used to prove that if
# the sanitization in app.core.errors._handle_generic_exception ever broke,
# this test would catch it.
_LEAK_CHECK_MARKER = "distinctive-leak-check-marker-4471"


def test_unhandled_exception_on_real_route_returns_sanitized_500(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Simulate an unhandled failure on a REAL route.

    `app.contexts.guestbook.routers.guestbook_entries.list_guestbook_entries` calls the module-level
    name `list_entries` that it imported directly from the service, so the real
    seam to patch is `app.contexts.guestbook.routers.guestbook_entries.list_entries` -- patching the
    service module would not affect the router, which already holds its own bound
    reference to the original function.

    No permanent debug or crash route is added anywhere; the patch is scoped to
    this test by the `monkeypatch` fixture, which reverts at teardown.

    This test builds its own `TestClient(real_app, raise_server_exceptions=False)`
    instead of using the shared `client` fixture. Starlette's
    `ServerErrorMiddleware` always re-raises the original exception after invoking
    the registered handler and sending its response, so that servers can log it or
    a test client can surface it. `raise_server_exceptions=False` is what tells the
    test client to swallow that re-raise and hand back the already-sent sanitized
    response -- the same pattern `tests/unit/test_errors.py` uses.
    """

    def _boom(**_read_parameters: object) -> list:
        #: Takes the read parameters and ignores them. A no-argument stand-in
        #: would raise `TypeError` on the call itself rather than `RuntimeError`
        #: inside it -- still a 500, still sanitized, and no longer the failure
        #: this test says it is simulating.
        raise RuntimeError(_LEAK_CHECK_MARKER)

    monkeypatch.setattr("app.contexts.guestbook.routers.guestbook_entries.list_entries", _boom)

    with TestClient(real_app, raise_server_exceptions=False) as local_client:
        response = local_client.get(ENTRIES)

    assert response.status_code == 500
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {"detail": "internal server error"}

    response_text = response.text
    assert _LEAK_CHECK_MARKER not in response_text
    assert "RuntimeError" not in response_text
    assert "Traceback" not in response_text


# --- what the REAL application writes to its log when a real route fails ------
#
# `tests/unit/test_log_content_policy.py` proves the filter over records built
# by hand; this proves the application actually has that filter in front of the
# one `logger.exception` in `app/core/errors.py`, on a real route, through the
# real handler chain. The two are not the same claim: the first could pass with
# the filter wired to nothing.

_LOG_LEAK_MARKER = "SYNTHETIC-PRIVATE-NAME-INTEGRATION"


@contextmanager
def _application_sink() -> Iterator[io.StringIO]:
    """A sink built from the application's OWN declaration, ahead of the rest.

    Not `logging.getLogger().handlers[0]`, and the reason is worth writing down:
    `tests/_database.py` runs the migrations IN THIS PROCESS, and
    `alembic/env.py` calls `fileConfig(...)`, which closes and replaces every
    root handler there is. So by the time this suite runs, the sink
    `configure_logging()` installed is gone and alembic's is in its place. That
    is a property of migrating inside the test process -- the application
    migrates from `scripts/db.sh`, in a process of its own -- and re-applying
    the configuration here would close pytest's capture handlers for the rest of
    the session.

    So the sink is assembled from `build_config()`: the same filter classes and
    the same format string the application declares, read out of the declaration
    rather than repeated here. What that leaves to the unit suite is the claim
    that `dictConfig` attaches them, which
    `tests/unit/test_log_content_policy.py` holds; what it proves here is
    everything downstream of that -- a real route, the real catch-all handler,
    and the record it actually emits.

    Inserted at position 0: appended, it would see a record another handler's
    filter had already sanitised and would pass without measuring anything.
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


def test_a_failing_real_route_logs_no_value_and_keeps_its_request_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The record the catch-all emits: sanitised, and still correlated.

    Both halves matter and the second is the one that could be broken by the
    first. A summary that dropped the request id would satisfy article XI and
    leave an operator with a failure they cannot tie to the request that caused
    it -- which is what `docs/runbooks/incident-first-response.md` tells them to
    do first.
    """

    def _boom(**_read_parameters: object) -> list:
        raise RuntimeError(f"the row said {_LOG_LEAK_MARKER}")

    monkeypatch.setattr("app.contexts.guestbook.routers.guestbook_entries.list_entries", _boom)

    with _application_sink() as buffer:
        with TestClient(real_app, raise_server_exceptions=False) as local_client:
            response = local_client.get(ENTRIES, headers={"X-Request-ID": "e2e-log-check"})
        written = buffer.getvalue()

    assert response.status_code == 500
    assert written, "the catch-all handler wrote nothing at all"
    assert _LOG_LEAK_MARKER not in written, f"the exception's text reached the log:\n{written}"
    assert "RuntimeError" in written, f"the log does not say what broke:\n{written}"
    assert "app/core/errors.py" not in written.split("exception (", 1)[0], (
        "the summary should describe the route's failure, not the handler that logged it"
    )
    assert "[e2e-log-check]" in written, (
        f"the record lost the request id, so nothing ties it to the request:\n{written}"
    )

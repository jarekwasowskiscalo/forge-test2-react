"""The logging framework: TRACE exists, config is idempotent, the id rides along.

Until `app/core/logging_config.py`, every record fell through to `lastResort`
and anything below WARNING vanished -- so the properties pinned here are the
ones the debugging story depends on: the custom TRACE level is registered and
gated, `configure_logging()` can be called from every entrypoint without
stacking handlers, a `LOG_FILE` run actually leaves a file, and every HTTP
response carries the request id the log lines print.

No database (`no_db`): the TestClient app import is the same one the no-db
suite already performs.

What this module deliberately does NOT hold: the property that a login attempt
leaves neither the password nor the session token in the log. That claim drives
`POST /api/session`, which reads the identities table, so under a no-db run it
fails on the missing table rather than on the leak it forbids -- and a version
weakened until it no longer needs the table would no longer be asking the
question. A claim that needs the database belongs to the integration suite,
and that is where it would live -- this template has no authentication at all
(`spec/invariants.md`), so nothing asserts it today.
"""

import logging
import pathlib

import pytest

from app.core import logging_config
from app.core.request_id import current_request_id


def test_trace_is_registered_below_debug() -> None:
    assert logging_config.TRACE < logging.DEBUG
    logging_config.configure_logging()
    assert logging.getLevelName(logging_config.TRACE) == "TRACE"


def test_trace_helper_respects_the_level() -> None:
    logger = logging.getLogger("test.trace.gate")
    logger.setLevel(logging.INFO)
    records: list[logging.LogRecord] = []

    class Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    handler = Capture(level=logging_config.TRACE)
    logger.addHandler(handler)
    try:
        logging_config.trace(logger, "row=%d outcome=%s", 7, "new")
        assert records == [], "TRACE emitted while the logger sat at INFO"
        logger.setLevel(logging_config.TRACE)
        logging_config.trace(logger, "row=%d outcome=%s", 7, "new")
        assert len(records) == 1
        assert records[0].getMessage() == "row=7 outcome=new"
        assert records[0].levelname == "TRACE"
    finally:
        logger.removeHandler(handler)


def test_configure_logging_is_idempotent() -> None:
    logging_config.configure_logging()
    before = list(logging.getLogger().handlers)
    logging_config.configure_logging()
    assert logging.getLogger().handlers == before, "a second call stacked handlers"


def test_log_file_env_produces_a_file(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "deep" / "app.log"
    monkeypatch.setenv("LOG_FILE", str(target))
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    # dictConfig(disable_existing_loggers=False) replaces the root handlers, so
    # re-running against a configured process is exactly the production path.
    monkeypatch.setattr(logging_config, "_configured", False)
    logging_config.configure_logging()
    logging.getLogger("test.file.sink").debug("code=TEST_SINK count=%d", 1)
    for handler in logging.getLogger().handlers:
        handler.flush()
    assert target.is_file(), "LOG_FILE was set and no file appeared"
    text = target.read_text(encoding="utf-8")
    assert "code=TEST_SINK count=1" in text
    assert "[-]" in text, "a record outside a request carries '-' as its id"
    # Leave the process configured the default way for the tests that follow.
    monkeypatch.delenv("LOG_FILE")
    monkeypatch.setattr(logging_config, "_configured", False)
    logging_config.configure_logging()


def test_every_response_carries_a_request_id() -> None:
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as client:
        first = client.get("/api/health")
        second = client.get("/api/health")
    assert first.status_code == 200
    assert first.headers.get("x-request-id"), "no X-Request-ID on the response"
    assert first.headers["x-request-id"] != second.headers["x-request-id"]


def test_an_incoming_request_id_is_honoured_and_echoed() -> None:
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as client:
        response = client.get("/api/health", headers={"X-Request-ID": "e2e-abc123"})
    assert response.headers["x-request-id"] == "e2e-abc123"


def test_outside_a_request_the_id_is_none() -> None:
    assert current_request_id() is None

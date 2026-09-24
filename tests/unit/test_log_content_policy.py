"""The EMITTED record obeys article XI, exception and traceback included.

`app/core/logging_config.py` states the rule -- "identifiers and counts, never
values" -- and until this module the rule was held on the *constant message
text* alone. A log record is message + args + `exc_info`, and
`logging.Formatter` renders `exc_info` into `record.exc_text` as `str(exc)` plus
the traceback plus the whole `__cause__`/`__context__` chain. So
`app/core/errors.py`'s one `logger.exception(...)` put a SQLAlchemy bind
parameter, psycopg's `DETAIL: Key (author)=(...)`, Pydantic's `input_value='...'`
and every message in the cause chain onto stderr, into `LOG_FILE` and into
CloudWatch -- while the response body it returned beside them was correctly
fixed and sanitised.

**Every case proves the leak before it proves the repair.** Each one first
asserts that its synthetic value really is in `traceback.format_exception(exc)`
-- what the stdlib would have written -- and only then that it is absent from
the rendered record. Without that first half a test that built the wrong
exception would pass by rendering nothing, which is the failure mode
`tests/fitness/test_test_layout.py` names: a detector that has stopped matching
passes everything.

**The application's own declaration, not a replica of it.** `_sink` assembles a
handler out of `build_config()` -- the filter classes it names and the format
string it declares, read rather than repeated here -- and the tests render
through that. It does not read `logging.getLogger().handlers[0]`, and the reason
is measured: under `./scripts/test.sh backend` this module shares a process with
the integration suite, `tests/_database.py` migrates in that process, and
`alembic/env.py` calls `fileConfig(...)`, which closes and replaces every root
handler. Reading the live root would therefore fail in the full run and pass
under `./scripts/test.sh unit`. Re-applying the configuration instead is worse
again: `logging.config` closes the handlers it replaces, pytest's capture
handlers included, and breaks the rest of the session.

So the claim is split in three, and each piece is held where it can be.
`test_every_sink_in_the_configuration_sanitises_and_correlates` holds that the
declaration names both filters on every sink, the `file` one included -- which a
live check never sees, because `LOG_FILE` is unset in a default run.
`test_the_live_console_sink_carries_both_filters` holds that `dictConfig`
attaches them, and **skips with its reason named** in the one run that cannot
answer it. Everything else holds what the filters then do.

The second emission path has a test of its own. Starlette's
`ServerErrorMiddleware` re-raises after the handler has answered, so under
uvicorn `uvicorn.error` logs the same exception again -- and
`app/core/logging_config.py` routes `uvicorn*` into the SAME root handlers on
purpose. `test_the_uvicorn_logger_reaches_a_sanitising_sink` is what proves the
filter sits where that record passes; it is the reason the filter is on the
HANDLERS and not on a logger, since a logger's filters do not run for records
propagated from a child. The same placement covers `asyncio`'s unhandled-task
records and SQLAlchemy's own `exc_info=True` sites in `engine/base.py` and
`pool/base.py`, none of which pass through `app/core/errors.py` either.

No database (`no_db` by placement -- `tests/unit/conftest.py`).
"""

import io
import logging
import traceback
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Final

import pytest

from app.core import logging_config

#: One base, four distinct values. Distinct so that a test which renders the
#: WRONG exception fails on the missing type name rather than passing because
#: some other case's value happened to be absent too.
_SYNTHETIC: Final = "SYNTHETIC-PRIVATE-NAME"
_SYNTHETIC_STATEMENT: Final = f"{_SYNTHETIC}-STATEMENT"
_SYNTHETIC_DRIVER: Final = f"{_SYNTHETIC}-DRIVER"
_SYNTHETIC_VALIDATION: Final = f"{_SYNTHETIC}-VALIDATION"
_SYNTHETIC_CAUSE: Final = f"{_SYNTHETIC}-CAUSE"


# --- the four exceptions the acceptance criteria name -------------------------
#
# Each is RAISED rather than constructed, so it carries a real traceback: the
# summary is meant to keep the frames and drop the messages, and an exception
# with `__traceback__ is None` would not exercise that at all.


def _statement_error() -> BaseException:
    """SQLAlchemy's `StatementError`, whose `str()` appends `[parameters: ...]`."""
    from sqlalchemy.exc import StatementError

    try:
        raise StatementError(
            message="could not execute",
            statement="INSERT INTO guestbook_entries (author) VALUES (%(author)s)",
            params={"author": _SYNTHETIC_STATEMENT},
            orig=Exception("the driver said no"),
        )
    except StatementError as exc:
        return exc


def _driver_error() -> BaseException:
    """The psycopg error that rides under `DBAPIError.orig`.

    `hide_parameters=True` does not touch this one -- it is Postgres's own
    message rather than a bind parameter, which is exactly why the flag is
    surface reduction and this filter is the rule.
    """
    from psycopg.errors import UniqueViolation

    try:
        raise UniqueViolation(
            'duplicate key value violates unique constraint "uq_guestbook_author"\n'
            f"DETAIL: Key (author)=({_SYNTHETIC_DRIVER}) already exists."
        )
    except UniqueViolation as exc:
        return exc


def _validation_error() -> BaseException:
    """Pydantic's `ValidationError`, whose `str()` quotes `input_value='...'`."""
    from pydantic import BaseModel, ValidationError

    class _Counted(BaseModel):
        count: int

    try:
        _Counted(count=_SYNTHETIC_VALIDATION)  # type: ignore[arg-type]
    except ValidationError as exc:
        return exc
    raise AssertionError("the model accepted a string where an int was declared")


def _chained_error() -> BaseException:
    """A cause chain -- `logger.exception` prints every link, message included."""
    try:
        try:
            raise ValueError(f"the row said {_SYNTHETIC_CAUSE}")
        except ValueError as cause:
            raise RuntimeError("while processing the request") from cause
    except RuntimeError as exc:
        return exc


_CASES: Final[tuple[tuple[str, object, str], ...]] = (
    ("statement", _statement_error, _SYNTHETIC_STATEMENT),
    ("driver", _driver_error, _SYNTHETIC_DRIVER),
    ("validation", _validation_error, _SYNTHETIC_VALIDATION),
    ("cause-chain", _chained_error, _SYNTHETIC_CAUSE),
)


# --- the real pipeline --------------------------------------------------------


def _declared_format() -> str:
    """The format string the application declares -- read, never repeated here."""
    formatters = logging_config.build_config("INFO", "")["formatters"]
    assert isinstance(formatters, dict)
    fmt = formatters["standard"]["format"]
    assert isinstance(fmt, str)
    return fmt


def _sink(buffer: io.StringIO) -> logging.StreamHandler[io.StringIO]:
    """A sink assembled from `build_config()`: its filter classes, its format.

    Not `logging.getLogger().handlers[0]`, and the reason is measured rather
    than cautious. `./scripts/test.sh backend` runs this module in the same
    process as the integration suite, `tests/_database.py` migrates in that
    process, and `alembic/env.py` calls `fileConfig(...)` -- which closes and
    replaces EVERY root handler. So under the full run the sink
    `configure_logging()` installed is gone and alembic's is in its place, and a
    test reading the live root would fail there while passing under
    `./scripts/test.sh unit`. Re-applying the configuration instead is worse:
    `logging.config` closes pytest's capture handlers on the way, which breaks
    the rest of the session.

    What this leaves to `test_every_sink_in_the_configuration_sanitises_and_correlates`
    is the claim that the declaration names both filters, and to
    `test_the_live_console_sink_carries_both_filters` the claim that
    `dictConfig` attaches them where nothing has since replaced them.
    """
    config = logging_config.build_config("INFO", "")
    filters = config["filters"]
    handlers = config["handlers"]
    assert isinstance(filters, dict)
    assert isinstance(handlers, dict)

    sink: logging.StreamHandler[io.StringIO] = logging.StreamHandler(buffer)
    sink.setFormatter(logging.Formatter(_declared_format()))
    for name in handlers["console"]["filters"]:
        sink.addFilter(filters[name]["()"]())
    return sink


def _record(exc: BaseException) -> logging.LogRecord:
    """The record `app/core/errors.py` makes, without going through a request."""
    logger = logging.getLogger("tests.log_content_policy")
    return logger.makeRecord(
        logger.name,
        logging.ERROR,
        __file__,
        0,
        "Unhandled exception while processing request",
        (),
        (type(exc), exc, exc.__traceback__),
    )


def _render(record: logging.LogRecord) -> str:
    """What a sink receives: its filters, then its formatter."""
    sink = _sink(io.StringIO())
    sink.filter(record)
    return sink.format(record)


@contextmanager
def _attached_sink() -> Iterator[io.StringIO]:
    """The sink in front of every other, for the length of the block.

    Position 0: appended, it would see a record another handler's filter had
    already sanitised, and would pass whether or not the record arrives clean.
    """
    buffer = io.StringIO()
    sink = _sink(buffer)
    root = logging.getLogger()
    root.handlers.insert(0, sink)
    previous = root.level
    root.setLevel(logging.INFO)
    try:
        yield buffer
    finally:
        root.setLevel(previous)
        root.handlers.remove(sink)


# --- criterion 1: the rendered record carries no value ------------------------


@pytest.mark.parametrize(("name", "build", "synthetic"), _CASES, ids=[c[0] for c in _CASES])
def test_no_value_survives_into_the_rendered_record(
    name: str, build: object, synthetic: str
) -> None:
    exc = build()  # type: ignore[operator]

    stdlib = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    assert synthetic in stdlib, (
        f"the {name} fixture does not carry {synthetic} even in the stdlib's own "
        "rendering -- this case would pass without measuring anything"
    )

    rendered = _render(_record(exc))
    assert synthetic not in rendered, (
        f"{synthetic} reached the emitted record for the {name} case:\n{rendered}"
    )


@pytest.mark.parametrize(("name", "build", "synthetic"), _CASES, ids=[c[0] for c in _CASES])
def test_the_rendered_record_still_says_what_broke_and_where(
    name: str, build: object, synthetic: str
) -> None:
    """Criterion 3 -- sanitising is not deleting. Type and position survive."""
    exc = build()  # type: ignore[operator]
    rendered = _render(_record(exc))

    assert type(exc).__name__ in rendered, (
        f"the {name} record names no exception type; the reader cannot tell what broke:\n{rendered}"
    )
    assert "tests/unit/test_log_content_policy.py" in rendered, (
        f"the {name} record carries no frame from the module that raised it; "
        f"the reader cannot tell where it broke:\n{rendered}"
    )


def test_the_cause_chain_is_summarised_rather_than_dropped() -> None:
    """Both links, by type. A chain rendered as its outermost link loses the cause."""
    rendered = _render(_record(_chained_error()))
    assert "RuntimeError" in rendered
    assert "ValueError" in rendered, f"the cause was dropped rather than summarised:\n{rendered}"


def test_the_record_carries_the_request_id_placeholder_outside_a_request() -> None:
    """The correlation handle survives -- `-` here, a real id under a request."""
    rendered = _render(_record(_chained_error()))
    assert "[-]" in rendered, f"the record lost its request-id field:\n{rendered}"


# --- the other ways an exception reaches a record -----------------------------


def test_an_exception_passed_as_a_message_argument_is_summarised() -> None:
    """`logger.error("boom: %s", exc)` renders `str(exc)` and bypasses `exc_info`."""
    exc = _chained_error()
    logger = logging.getLogger("tests.log_content_policy")
    record = logger.makeRecord(logger.name, logging.ERROR, __file__, 0, "boom: %s", (exc,), None)

    rendered = _render(record)
    assert _SYNTHETIC_CAUSE not in rendered, (
        f"an exception interpolated into the message leaked its text:\n{rendered}"
    )
    assert "RuntimeError" in rendered


def test_an_exception_used_as_the_message_itself_is_summarised() -> None:
    """`logger.error(exc)` -- `getMessage()` calls `str(self.msg)`.

    The statement error rather than the chained one: this path renders
    `str(exc)` and nothing under it, so only an exception whose OWN text carries
    the value measures anything here.
    """
    exc = _statement_error()
    assert _SYNTHETIC_STATEMENT in str(exc), "the fixture's own text carries no value to leak"

    logger = logging.getLogger("tests.log_content_policy")
    record = logger.makeRecord(logger.name, logging.ERROR, __file__, 0, exc, (), None)

    rendered = _render(record)
    assert _SYNTHETIC_STATEMENT not in rendered, (
        f"an exception logged as the message itself leaked its text:\n{rendered}"
    )


def test_the_uvicorn_logger_reaches_a_sanitising_sink() -> None:
    """The second emission path: `ServerErrorMiddleware` re-raises, uvicorn logs it.

    Not a TestClient test, and deliberately: `raise_server_exceptions=False`
    makes the test transport swallow that re-raise
    (`starlette/testclient.py`), so no `uvicorn.error` record is ever produced
    under a TestClient. What can be proved here is the thing that actually
    matters -- that a record on `uvicorn.error` lands on a sink whose filters
    sanitise it, which is what `handlers: []` + `propagate: True` buys.
    """
    exc = _chained_error()
    with _attached_sink() as buffer:
        logging.getLogger("uvicorn.error").error("Exception in ASGI application", exc_info=exc)
        written = buffer.getvalue()

    assert written, "the uvicorn logger's record never reached the root handler"
    assert _SYNTHETIC_CAUSE not in written, (
        f"the uvicorn record reached the sink unsanitised:\n{written}"
    )
    assert "RuntimeError" in written


def test_the_bytes_that_reach_the_sink_are_the_sanitised_ones() -> None:
    """Not just the return of `format()` -- what is actually written out."""
    exc = _statement_error()
    with _attached_sink() as buffer:
        logging.getLogger("tests.log_content_policy").error(
            "Unhandled exception while processing request", exc_info=exc
        )
        written = buffer.getvalue()

    assert written, "nothing was written to the diverted sink"
    assert _SYNTHETIC_STATEMENT not in written, f"the sink received a bind parameter:\n{written}"


# --- the structural claim: no sink is left out --------------------------------


def test_every_sink_in_the_configuration_sanitises_and_correlates() -> None:
    """A sink added later cannot quietly bypass the rule.

    Asserted over the configuration rather than over the live root logger, for
    two reasons. The `file` sink exists only when `LOG_FILE` is set, so a live
    check never sees it and the hole would be in exactly the sink a developer's
    run leaves on disk. And the live root also carries whatever the test runner
    attached -- pytest's capture handlers are there too -- which are not this
    application's sinks and are not this rule's business.
    """
    from app.core.logging_config import ExceptionSummaryFilter, RequestIdFilter, build_config

    config = build_config("INFO", "/tmp/never-opened.log")
    declared = config["filters"]
    assert isinstance(declared, dict)
    assert declared["request_id"] == {"()": RequestIdFilter}
    assert declared["exception_summary"] == {"()": ExceptionSummaryFilter}

    handlers = config["handlers"]
    assert isinstance(handlers, dict)
    assert set(handlers) == {"console", "file"}, (
        f"a sink was added or removed; this test names the ones it knows: {set(handlers)}"
    )
    for name, sink in handlers.items():
        assert set(sink["filters"]) == set(declared), (
            f"the {name} sink does not carry every filter: {sink['filters']}"
        )

    root = config["root"]
    assert isinstance(root, dict)
    assert set(root["handlers"]) == set(handlers), "a configured sink is not attached to root"


def test_the_live_console_sink_carries_both_filters() -> None:
    """The other half: `dictConfig` really attaches what the declaration names.

    A NAMED GAP rather than a silent pass. Under `./scripts/test.sh backend`
    this module shares a process with the integration suite, whose
    `tests/_database.py` migrates in process -- and `alembic/env.py` calls
    `fileConfig(...)`, which closes and replaces every root handler there is. So
    the application's own sink is gone by the time this runs there, and the
    honest answer is to say which run can answer this and skip in the one that
    cannot. It is asserted on every `--no-db` leg, macOS CI included, where
    nothing migrates.
    """
    from app.core.logging_config import ExceptionSummaryFilter, RequestIdFilter

    logging_config.configure_logging()
    declared = _declared_format()
    live = [
        handler
        for handler in logging.getLogger().handlers
        if getattr(handler.formatter, "_fmt", None) == declared
    ]
    if not live:
        pytest.skip(
            "the root logger no longer carries the application's own sink: something in "
            "this process has re-run logging configuration since import -- under the full "
            "backend run that is alembic's fileConfig, via tests/_database.py. Answered by "
            "./scripts/test.sh unit, which migrates nothing."
        )
    for handler in live:
        kinds = {type(one) for one in handler.filters}
        assert ExceptionSummaryFilter in kinds, f"the live sink does not sanitise: {kinds}"
        assert RequestIdFilter in kinds, f"the live sink does not correlate: {kinds}"


def test_the_uvicorn_loggers_own_no_handler_of_their_own() -> None:
    """The filter covers uvicorn only while uvicorn's records come to OUR sinks."""
    logging_config.configure_logging()
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        assert logger.handlers == [], f"{name} has a handler of its own, which no filter covers"
        assert logger.propagate, f"{name} does not propagate, so it never reaches a filtered sink"


# --- the surface the filter does not have to be right about -------------------


def test_the_engine_hides_bind_parameters_and_that_is_not_the_rule() -> None:
    """`hide_parameters=True` is surface reduction; the filter is the rule.

    Both halves are asserted here because the decision is only honest with the
    second one. The flag shortens `StatementError`, and it reaches nothing else:
    `DBAPIError._message()` returns `str(self.orig)`, so psycopg's own
    `DETAIL: Key (author)=(...)` line -- the one an audit would actually find in
    CloudWatch -- is untouched by it. That is why
    `app/core/logging_config.py` holds the rule and `app/db/session.py` only
    makes the rule's job smaller.
    """
    from sqlalchemy.exc import StatementError

    from app.db.session import engine

    assert engine.hide_parameters is True, (
        "the engine that serves requests binds user values and renders them in "
        "StatementError; the decision recorded in app/db/session.py is not in force"
    )

    hidden = StatementError(
        message="could not execute",
        statement="INSERT INTO guestbook_entries (author) VALUES (%(author)s)",
        params={"author": _SYNTHETIC_STATEMENT},
        orig=Exception("the driver said no"),
        hide_parameters=True,
    )
    assert _SYNTHETIC_STATEMENT not in str(hidden), "the flag did not hide the bind parameter"

    assert _SYNTHETIC_DRIVER in str(_driver_error()), (
        "the driver's own message no longer carries a value, so this test has "
        "stopped measuring the boundary it was written for"
    )

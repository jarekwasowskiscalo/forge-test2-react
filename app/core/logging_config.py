"""Logging for the application: console for humans, one file for agents.

Until this module existed the application had four log call sites and zero
configuration -- every record fell through to Python's `lastResort` handler,
bare on stderr, and anything below WARNING vanished. A failing e2e run left no
trail to read. Now `configure_logging()` runs once at import of `app.main`, and
two environment variables decide everything:

- ``LOG_LEVEL`` -- ``TRACE`` | ``DEBUG`` | ``INFO`` (default) | ``WARNING`` |
  ``ERROR``. One level for both sinks.
- ``LOG_FILE`` -- a path for a rotating file sink (5 MB x 3, UTF-8). Empty or
  unset means console only, which is the container default on purpose: the
  image runs read-only as uid 10001 and `docker logs` is the file there. The
  scripts set `.sdd/logs/app.log` locally, so a developer's or an agent's run
  always leaves a file that can be read after the process is gone.

The convention the call sites follow, and the one rule above all of them:

- **INFO** -- business events, one line each: a run starting and finishing with
  its counts, a refusal with its stable code, a record reaching a terminal
  state. Reading INFO alone should tell the story of a working day.
- **DEBUG** -- one line per decision inside a request: phase boundaries, the
  branch a rule took, what was chosen and why.
- **TRACE** (level 5, below DEBUG) -- per-row flow through a batch operation:
  row number and outcome. The volume is deliberate; it exists so a failing e2e
  run can be debugged from the file without re-running anything.

**Article XI applies to every level.** Identifiers and counts, never values:
somebody's name, e-mail, phone, account number or balance never reaches a log
line. If a message needs to point at a row, it points with the row number and
the record's id.

**And the rule is held here, mechanically, over the WHOLE record.** It used to
be held over the constant message text alone, which is the half a call site can
see. A record is message + args + `exc_info`, and `logging.Formatter` renders
`exc_info` into `record.exc_text` as `str(exc)` plus the traceback plus every
link of the `__cause__`/`__context__` chain -- so one `logger.exception(...)` in
`app/core/errors.py` put SQLAlchemy's `[parameters: ...]`, psycopg's
`DETAIL: Key (author)=(...)` and Pydantic's `input_value='...'` onto stderr and
into CloudWatch, beside a 500 body that was correctly fixed and sanitised.
`ExceptionSummaryFilter` reduces an exception to **category and position** --
its type and its frames -- and never its text.

**On the handlers, not on a logger, and that is the whole design.** A logger's
filters do not run for records propagated from a child logger; a handler's run
for every record that reaches it. Three emitters that never touch
`app/core/errors.py` depend on that: `uvicorn.error`, which logs the same
exception again after `ServerErrorMiddleware` re-raises it (and which is routed
into these very handlers below, on purpose); `asyncio`, which logs an unhandled
task exception through `call_exception_handler`; and SQLAlchemy's own
`exc_info=True` sites in `engine/base.py` and `pool/base.py`, whose exception is
the driver's. A filter on one logger would have covered none of them.

**What this does not reach.** On Lambda the runtime prints an exception that
escapes the handler straight to CloudWatch, outside Python logging entirely --
see `docs/security.md` § Data, and what leaves the machine.
"""

import logging
import logging.config
import os
from pathlib import Path
from typing import Final

#: Below DEBUG (10). Registered once, here; call sites use `trace(logger, ...)`.
TRACE: Final = 5

_FORMAT: Final = "%(asctime)s %(levelname)-7s [%(request_id)s] %(name)s: %(message)s"

_configured = False


class RequestIdFilter(logging.Filter):
    """Stamps every record with the current request id, or ``-`` outside one.

    A filter rather than an adapter so third-party loggers (uvicorn's included)
    get the field too -- the formatter references it unconditionally.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        from app.core.request_id import current_request_id

        record.request_id = current_request_id() or "-"
        return True


#: The repository root, as a prefix to strip from a frame's file. A frame
#: rendered whole says `/Users/<somebody>/...` on a laptop and `/var/task/...` in
#: the function -- the machine it ran on, which is not the position of the fault.
_ROOT: Final = f"{Path(__file__).resolve().parents[2]}{os.sep}"

#: Everything past these is elided with a count. A `RecursionError` carries a
#: thousand identical frames, and a log line nobody can scroll is a log line
#: nobody reads; a cycle through `__context__` would not terminate at all.
_MAX_FRAMES: Final = 40
_MAX_CHAIN: Final = 10
_MAX_MEMBERS: Final = 10

_SUMMARY_HEADER: Final = "exception (article XI: type and position, never the text):"

#: Every handler carries BOTH, and the list is written once so that a sink added
#: later cannot be given one and not the other. A handler without
#: `exception_summary` is a hole in article XI that nothing else would report --
#: `tests/unit/test_log_content_policy.py` is what refuses one.
_FILTERS: Final = ["request_id", "exception_summary"]


def _type_name(exc: BaseException) -> str:
    """`ValueError`, `sqlalchemy.exc.StatementError` -- the class, never `str(exc)`."""
    kind = type(exc)
    module = kind.__module__
    return kind.__qualname__ if module == "builtins" else f"{module}.{kind.__qualname__}"


def _short_path(filename: str) -> str:
    """A frame's file without the machine it ran on.

    A string comparison rather than `Path.resolve()`: this runs while an
    exception is being logged, and touching the filesystem once per frame is a
    round trip the failure path does not need.
    """
    package = f"{os.sep}site-packages{os.sep}"
    if package in filename:
        return filename.rsplit(package, 1)[1]
    if filename.startswith(_ROOT):
        return filename[len(_ROOT) :]
    return Path(filename).name


def _frames(exc: BaseException) -> list[str]:
    """Where it broke: file, line and qualified function. No source text.

    `traceback.format_exception` would render the source line and, since 3.11,
    the `^^^` anchors under it -- and it reads them through `linecache`. Walking
    the traceback here reads nothing and can render nothing that was not asked
    for, which is the difference between a renderer that is safe and one that is
    currently safe.
    """
    lines: list[str] = []
    frame = exc.__traceback__
    while frame is not None and len(lines) < _MAX_FRAMES:
        code = frame.tb_frame.f_code
        lines.append(
            f"    at {_short_path(code.co_filename)}:{frame.tb_lineno} in {code.co_qualname}"
        )
        frame = frame.tb_next
    remaining = 0
    while frame is not None:
        remaining += 1
        frame = frame.tb_next
    if remaining:
        lines.append(f"    ... {remaining} more frame(s)")
    return lines


def _describe(exc: BaseException, lines: list[str], seen: set[int], depth: int, lead: str) -> None:
    if depth > _MAX_CHAIN:
        lines.append(f"  {lead}... chain truncated at {_MAX_CHAIN}")
        return
    if id(exc) in seen:
        lines.append(f"  {lead}{_type_name(exc)} (already reported above)")
        return
    seen.add(id(exc))
    lines.append(f"  {lead}{_type_name(exc)}")
    lines.extend(_frames(exc))

    # A `BaseExceptionGroup` carries its members on `.exceptions` rather than on
    # the cause chain, so a chain-only walk would render the group and drop
    # every failure inside it -- which is the whole content of the report.
    members = getattr(exc, "exceptions", None)
    if isinstance(members, tuple):
        for member in members[:_MAX_MEMBERS]:
            if isinstance(member, BaseException):
                _describe(member, lines, seen, depth + 1, "member: ")
        if len(members) > _MAX_MEMBERS:
            lines.append(f"  ... {len(members) - _MAX_MEMBERS} more member(s)")

    if exc.__cause__ is not None:
        _describe(exc.__cause__, lines, seen, depth + 1, "caused by: ")
    elif exc.__context__ is not None and not exc.__suppress_context__:
        _describe(exc.__context__, lines, seen, depth + 1, "while handling: ")


def summarise_exception(exc: BaseException) -> str:
    """An exception reduced to what a reader needs and a policy allows.

    Types and positions for the whole chain. Never `str(exc)`, never a bind
    parameter, never `__notes__` -- all three are free text a library or a caller
    filled in, and none of them can be told from a value by looking.
    """
    lines = [_SUMMARY_HEADER]
    _describe(exc, lines, set(), 0, "")
    return "\n".join(lines)


class ExceptionSummaryFilter(logging.Filter):
    """Replaces every rendering of an exception in a record with its summary.

    Four places an exception's text reaches a sink, and the record is only
    correct when all four are closed:

    - ``exc_info`` -- the formatter renders it into ``exc_text``. Setting
      ``exc_text`` here is what makes the formatter skip its own
      ``formatException``, and clearing ``exc_info`` makes this idempotent: the
      second handler's copy of this filter finds nothing left to do and leaves
      the summary alone. A handler with no filter at all still gets the summary,
      because ``exc_text`` travels with the record.
    - ``stack_info`` -- a stack already rendered as text, source lines included.
      It is dropped rather than summarised: it is a string by the time it
      arrives, so there is nothing left to walk, and nothing in this application
      asks for one.
    - ``args`` -- ``logger.error("boom: %s", exc)`` renders ``str(exc)`` and
      never touches ``exc_info``.
    - ``msg`` -- ``logger.error(exc)``, where ``getMessage()`` calls
      ``str(self.msg)``.

    It does not, and cannot, judge the message a call site wrote: no filter can
    tell an identifier from a value in a string somebody formatted. That half is
    the convention at the top of this module, and this class is the half a
    convention cannot hold.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        info = record.exc_info
        if info is not None:
            exception = info[1]
            record.exc_text = (
                summarise_exception(exception)
                if exception is not None
                else f"{_SUMMARY_HEADER}\n  (no exception object)"
            )
            record.exc_info = None
        if record.stack_info:
            record.stack_info = None

        message: object = record.msg
        if isinstance(message, BaseException):
            record.msg = summarise_exception(message)

        # Rebuilt only when there is something to rebuild: every record passes
        # here, and most carry no exception among their arguments at all.
        arguments = record.args
        if isinstance(arguments, tuple) and any(
            isinstance(one, BaseException) for one in arguments
        ):
            record.args = tuple(
                _type_name(one) if isinstance(one, BaseException) else one for one in arguments
            )
        elif isinstance(arguments, dict) and any(
            isinstance(one, BaseException) for one in arguments.values()
        ):
            # The mapping form -- `logger.info("%(id)s", {"id": ...})`.
            record.args = {
                key: _type_name(one) if isinstance(one, BaseException) else one
                for key, one in arguments.items()
            }
        return True


def trace(logger: logging.Logger, message: str, *args: object) -> None:
    """A TRACE-level record. A helper, not a Logger subclass -- subclassing
    fights both mypy and uvicorn's own logger management."""
    if logger.isEnabledFor(TRACE):
        logger.log(TRACE, message, *args)


def build_config(level: object, log_file: str) -> dict[str, object]:
    """The `dictConfig` document, built rather than applied.

    Separated from `configure_logging()` so that the one claim nothing else can
    hold -- every sink carries both filters, the `file` one included, which is
    absent from a default run -- is checkable without configuring the process
    the test runs in. `logging.config` REMOVES and CLOSES the handlers it
    replaces, and pytest's capture handlers are among them, so a test that
    reconfigures to inspect the result breaks the rest of the session.
    """
    handlers: dict[str, dict[str, object]] = {
        "console": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
            "formatter": "standard",
            "filters": _FILTERS,
        }
    }
    if log_file:
        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": log_file,
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 3,
            "encoding": "utf-8",
            # Opened lazily: a read-only filesystem fails at first write, not
            # at import, and console logging keeps working either way.
            "delay": True,
            "formatter": "standard",
            "filters": _FILTERS,
        }

    return {
        "version": 1,
        # The application's module loggers are created at import time,
        # before this runs from some entrypoints. Disabling them here would
        # silence exactly the records this module exists to surface.
        "disable_existing_loggers": False,
        "filters": {
            "request_id": {"()": RequestIdFilter},
            "exception_summary": {"()": ExceptionSummaryFilter},
        },
        "formatters": {"standard": {"format": _FORMAT}},
        "handlers": handlers,
        "root": {"level": level, "handlers": list(handlers)},
        "loggers": {
            # Route uvicorn through the same sinks: handlers=[] +
            # propagate=True hands its records to root. Our dictConfig runs
            # at app-module import, which is after uvicorn applies its own
            # config, so this wins for both `uvicorn app.main:app` and
            # scripts/run.py.
            "uvicorn": {"handlers": [], "propagate": True},
            "uvicorn.error": {"handlers": [], "propagate": True},
            "uvicorn.access": {"handlers": [], "propagate": True},
        },
    }


def configure_logging() -> None:
    """Idempotent; safe to call from every entrypoint that imports app.main."""
    global _configured
    if _configured:
        return
    _configured = True

    logging.addLevelName(TRACE, "TRACE")

    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = TRACE if level_name == "TRACE" else level_name
    log_file = os.environ.get("LOG_FILE", "").strip()
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    logging.config.dictConfig(build_config(level, log_file))


__all__ = [
    "TRACE",
    "ExceptionSummaryFilter",
    "RequestIdFilter",
    "build_config",
    "configure_logging",
    "summarise_exception",
    "trace",
]

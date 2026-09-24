---
date: 2026-09-16
branch: fix/log-record-content-policy
pr: 40
kind: fix
---

# Hold article XI over the whole log record, not the message alone

## What changed

- `app/core/logging_config.py` — `summarise_exception()` and
  `ExceptionSummaryFilter`, beside `RequestIdFilter`. `build_config()` is split out of
  `configure_logging()` so the configuration can be read without being applied. `_FILTERS`
  is written once and both sinks take it.
- `app/core/request_id.py` — the contextvar is reset in an `else`, not a `finally`.
- `app/core/errors.py` — the catch-all's docstring now makes both promises, the record's
  and the response's. The `logger.exception` line itself is unchanged.
- `app/db/session.py` — `hide_parameters=True`, with the decision and its limits in the
  comment beside it.
- `tests/unit/test_log_content_policy.py` — new, 18 tests.
- `tests/integration/test_app_integration.py` — one test on a real route.
- `docs/security.md`, `docs/operations.md`, `docs/monitoring.md`,
  `docs/runbooks/incident-first-response.md` — four pages said the catch-all "logs the full
  exception". They now say what it logs, and `security.md` names the one residual.
- `spec/design/architecture.md` — three rows of the Platform table, plus a dated `Rejected`
  block carrying the four alternatives this rejects.
- `spec/changes/EXEMPTIONS.md` — one dated row, `change-directory` over the four `app/`
  files, expiring 2026-09-30.

## Why

[Issue #23](https://github.com/Scalo-Sales-Engineering-Consulting/forge_template_python_react/issues/23),
audit finding **A12**, P1.

Article XI says a log line carries identifiers and counts, never values. The rule was held
on the **constant message text** — the half a call site can see. A record is message plus
args plus `exc_info`, and `logging.Formatter` renders `exc_info` into `record.exc_text` as
`str(exc)` plus the traceback plus every link of the `__cause__`/`__context__` chain.

So `app/core/errors.py`'s one `logger.exception(...)` wrote, to stderr, to the `LOG_FILE`
rotating file and to CloudWatch:

- SQLAlchemy's `[parameters: {'author': …}]` — the values somebody typed;
- psycopg's `DETAIL: Key (author)=(…) already exists.`, carried under `DBAPIError.orig`;
- Pydantic's `input_value='…'`;
- every message in the cause chain.

Beside a 500 body that was correctly fixed and sanitised, and whose docstring promised
sanitisation **on the response side only**. That silence was the defect: the docstring was
accurate and the reader took it for the whole claim.

Nothing measured it. `git grep "caplog\|assertLogs"` found nothing, and the one assertion
on a record anywhere in the repository — `tests/unit/test_logging.py:55` — read
`getMessage()`, which is `record.msg % args` with no `exc_text` and no traceback: exactly
the case the issue names as insufficient.

**And a second emitter, which no edit to `errors.py` could have reached.** Starlette's
`ServerErrorMiddleware` re-raises after the handler has answered, so under uvicorn
`uvicorn.error` logs the same exception again with a full traceback — and
`logging_config.py` routes `uvicorn`, `uvicorn.error` and `uvicorn.access` into the **same**
root handlers, on purpose. `asyncio` logs unhandled task exceptions the same way, and
SQLAlchemy has its own `exc_info=True` sites in `engine/base.py` and `pool/base.py` whose
exception is the driver's.

## From what, to what

**Before.** A 500 left this in the log, values included:

```
Traceback (most recent call last):
  File ".../app/contexts/guestbook/routers/guestbook_entries.py", line 96, in list_guestbook_entries
    return list_entries(query=q, sort=sort, limit=limit, offset=offset)
sqlalchemy.exc.StatementError: could not execute
[SQL: INSERT INTO guestbook_entries (author) VALUES (%(author)s)]
[parameters: {'author': 'Ada Lovelace'}]
```

**After.** The same failure, same sink:

```
2026-09-16 16:35:20,055 ERROR   [e2e-log-check] app.core.errors: Unhandled exception while processing request
exception (article XI: type and position, never the text):
  sqlalchemy.exc.StatementError
    at app/contexts/guestbook/routers/guestbook_entries.py:96 in list_guestbook_entries
    at app/contexts/guestbook/services/guestbook_entries.py:40 in list_entries
  caused by: psycopg.errors.UniqueViolation
    at psycopg/cursor.py:97 in Cursor.execute
```

Type and position for the whole chain; no text anywhere. The bracketed request id is the
second change — see below — and it used to read `[-]` on exactly these records.

## How it works now

**`ExceptionSummaryFilter` sits on every sink `configure_logging()` builds**, and closes the
four ways an exception's text reaches a record: `exc_info` (replaced by the summary, and
`exc_info` cleared so the formatter skips its own `formatException` and a second handler's
copy of the filter finds nothing left to do), `stack_info` (dropped — it is already a string
with source lines in it by the time it arrives), `args` (`logger.error("boom: %s", exc)`)
and `msg` (`logger.error(exc)`).

`summarise_exception()` walks the traceback itself rather than calling
`traceback.format_exception`, which renders the source line and, since 3.11, the `^^^`
anchors under it, and reads them through `linecache`. It renders the exception's qualified
type and, per frame, `file:line in qualified-function`, with the repository root and
everything up to `site-packages/` stripped so a frame says `app/core/errors.py` rather than
somebody's home directory or `/var/task`. It follows `__cause__`, then `__context__` unless
suppressed, and a `BaseExceptionGroup`'s `.exceptions`, with a seen-set against cycles and
counted ceilings on frames, chain depth and group members.

**On the handlers, and that is the design rather than a detail.** A logger's filters do not
run for records propagated from a child logger; a handler's filters run for every record
that reaches it. That single placement is what covers `uvicorn.error`, `asyncio` and
SQLAlchemy's own loggers, none of which pass through `app/core/errors.py`.

**The request id survives a failure.** `RequestIdMiddleware` used to reset its contextvar in
a `finally`. `ServerErrorMiddleware` is built **outside** every middleware added with
`add_middleware`, so it catches the exception only after it has passed through — and the
catch-all logs it after that. The reset therefore blanked `[%(request_id)s]` on exactly the
records an operator opens the log for. It now resets in an `else`. Nothing leaks: every
request sets its own id before doing anything else, so the only value left behind is one the
next request overwrites.

**`hide_parameters=True`** is set on the application's engine and recorded as **surface
reduction, not the rule**. It shortens `StatementError`. It does not touch
`DBAPIError._message()`, which returns `str(self.orig)`, so psycopg's `DETAIL:` line is
untouched by it; it does not touch the cause chain; and Pydantic was never in its reach.
`test_the_engine_hides_bind_parameters_and_that_is_not_the_rule` asserts both halves, because
the decision is only honest with the second.

## What it means for the process

Nothing about running or changing this repository moves. No new environment variable, no new
script, no new flag; `LOG_LEVEL` and `LOG_FILE` behave exactly as before.

One thing changes for whoever reads a log during an incident, and
`docs/runbooks/incident-first-response.md` now says it: **there are no tracebacks any more.**
A failure is a block headed `exception (article XI: …)` with one line per frame. Open the
file at the line; the values that produced the failure are not there and are not meant to be.

**Two things are owed rather than changed.** The `change-directory` gate refuses a diff that
touches `trees.behaviour` — which names `app/` — without a change directory, and this repair
was directed to be made outside `/forge:sdd`. The route taken is the register's: one dated row in
`spec/changes/EXEMPTIONS.md` naming the four files, plus the `spec-exempt` label, which is
what reaches a *missing* directory (a row cannot: that failure carries no paths). **Delete
the row once this has merged.** And the label `spec-exempt` did not exist in this repository
until this pull request; it does now.

## What it does not change

- **The HTTP contract.** The 500 body is still `{"detail": "internal server error"}`, the 422
  still carries Pydantic's errors, and `tests/unit/test_errors.py` passes untouched. No
  endpoint, no status, no refusal code moved, and `contracts/openapi/` is not in this diff.
- **The message a call site writes.** The filter covers `exc_info`, `stack_info`, `args` and
  `msg`. A call site that formats a value into its message string by hand is still a call-site
  question: no filter can tell an identifier from a value inside a string somebody built.
- **A26 and A25** ([issue #25](https://github.com/Scalo-Sales-Engineering-Consulting/forge_template_python_react/issues/25)).
  A26 touches the same *line* — `app/core/errors.py`'s `logger.exception` — and issue #23 asks
  for the two to travel together. They did not, because #25 is a separate `Ready` ticket and
  folding it in would have widened this change without anybody choosing that. The line is
  unchanged here, so #25 still has its edit to make.
- **The missing `X-Request-ID` header on a 500.** `ServerErrorMiddleware` sends its response
  through the raw `send`, not through `RequestIdMiddleware`'s `send_with_header`, so a 500
  carries no correlation header even though its log record now does. That is a defect about
  the **response**, not the record, and it is left for its own change.
- **The Lambda runtime's own output.** An exception that escapes the handler is printed by the
  runtime outside Python logging entirely, and no filter can reach it. `docs/security.md` now
  names that residual instead of implying it away; the catch-all is what keeps one from
  escaping.
- **In-process Alembic.** `alembic/env.py` calls `fileConfig(...)`, which closes and replaces
  every root handler — so `tests/_database.py`, which migrates in this process, leaves the
  suite running on alembic's logging rather than the application's. That is why the
  integration test builds its sink from `build_config()` rather than reading
  `logging.getLogger().handlers[0]`, and it is written down in that test. It is a property of
  migrating in-process; the application migrates from `scripts/db.sh`, in a process of its own.

## How it was verified

- **RED first, and on the leak rather than on an import.**
  `./scripts/test.sh unit tests/unit/test_log_content_policy.py` before the filter existed:
  **8 failed, 116 passed** — all four acceptance cases failing on the synthetic value being
  present in the rendered record, with `[parameters: {'author': 'SYNTHETIC-PRIVATE-NAME-STATEMENT'}]`
  quoted in the assertion. Every case also asserts, first, that its value **is** in
  `traceback.format_exception(exc)` — so a case that built the wrong exception fails instead
  of passing vacuously.
- **The request-id half was red too, and on a real route.**
  `test_a_failing_real_route_logs_no_value_and_keeps_its_request_id` read
  `2026-09-16 16:35:20,055 ERROR   [-] app.core.errors: …` before `request_id.py` changed —
  which is how the `finally` was found rather than guessed at.
- `./scripts/test.sh unit`: **126 passed**.
- `./scripts/test.sh integration`: **99 passed**.
- `./scripts/lint.sh --fix`: **OK** — `ruff`, `ruff format`, `mypy --strict` over 101 source
  files, `eslint`, `tsc`.
- `./scripts/check.sh`: **OK**, the e2e leg included — 44 scenarios plus the UI smoke against
  a live application, and the production image built and asserted.
- `sdd-specs`: **OK** — every content gate.
- `sdd-specs --diff-gates --base main`: `recorded-decision` and `change-directory` both fired
  on the first run. The `Rejected` block in `spec/design/architecture.md` cleared the first.
  The second is exempted, and the exemption was verified rather than assumed: with
  `--exempt 1` the run prints *exempted by the `spec-exempt` label, on the strength of an open
  register row for ['change-directory']*.
- `./scripts/changelog.sh check --base main`: **OK** on this entry.

**Not run here, and why.** The macOS leg needs a macOS runner. A proof that a real uvicorn
process emits a sanitised record needs a live server **and** a route that crashes on demand,
and the issue forbids adding one; the closest faithful proof is
`test_the_uvicorn_logger_reaches_a_sanitising_sink`, which logs through the `uvicorn.error`
logger and asserts the root sink sanitised it — that is the mechanism the second emission path
actually uses. The acceptance criterion asking for the uvicorn record **through**
`TestClient(…, raise_server_exceptions=False)` cannot be met as written and the test says so:
`starlette/testclient.py` swallows the re-raise when `raise_server_exceptions` is false, so no
`uvicorn.error` record is ever produced under a test client.

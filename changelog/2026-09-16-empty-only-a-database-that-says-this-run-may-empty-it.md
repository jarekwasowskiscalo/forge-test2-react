---
date: 2026-09-16
branch: fix/e2e-reset-disposable-database
pr:
kind: fix
---

# Empty only a database that says this run may empty it

Closes [#22](https://github.com/Scalo-Sales-Engineering-Consulting/forge_template_python_react/issues/22).

## What changed

- `e2e/harness/database.py` — `libpq_dsn` becomes `connection_parameters` and returns explicit
  libpq parameters instead of a DSN string. It refuses a `service=` target, a connection string
  that names neither `host` nor `hostaddr`, and any address in either key (both are comma lists)
  that is not this host. `E2E_ALLOW_REMOTE_RESET` is compared by equality and takes `1` or a
  database's name. New: `target_identity`, `assert_disposable`, `mark_disposable`, `marker_for`,
  `open_connection`, and a `connect` seam on `reset_target_database`. `""` left `LOCAL_HOSTS`.
- `scripts/e2e_database.py` — new. Writes the `COMMENT ON DATABASE` that marks a database as one
  run's to empty, and refuses to write it on a database the caller did not provision unless
  `E2E_ALLOW_REMOTE_RESET` names that database.
- `scripts/test.sh` — `run_e2e` mints `E2E_RUN_ID`, calls the script above after
  `resolve_database_url`, and passes `--consent-required` when `APP_DB_EXTERNAL=1`.
- `tests/tooling/test_e2e_harness.py` — eleven negative cases replacing one, each driving the real
  `reset_target_database` through its seam and asserting the connection was handed no statement
  that deletes anything.
- `tests/integration/test_e2e_reset.py` — new. The positive control, on databases of its own.
- `e2e/suite/conftest.py`, `e2e/ui/conftest.py` — docstrings only.
- `docs/configuration.md`, `docs/troubleshooting.md`, `spec/design/architecture.md`,
  `spec/design/testing.md` — the interlock as the code now applies it, with a table of every
  refusal and what to do about each.

## Why

`reset_target_database` deletes every row it can reach, before every scenario. One line stood
between that and somebody's shared database: read `host` out of the connection string, and if it
is not `localhost` demand that an environment variable be non-empty. Four things were wrong with
it, and the audit (`claude-marketplace: audits/2026-09-15-latest/03-aplikacja-python-react.md#A10`)
proved each:

- **`hostaddr` was never read.** libpq ignores `host` when `hostaddr` is present, so
  `…@localhost:5432/app?hostaddr=203.0.113.9` read as local and connected to `203.0.113.9`.
- **A missing `host` counted as local** — `""` was in `LOCAL_HOSTS`, meaning "unix socket" — so a
  connection string with no address passed and libpq took the target from `PGHOST`, `PGHOSTADDR`
  or `pg_service.conf`.
- **The opt-in had no value.** `not os.environ.get(...)` meant `E2E_ALLOW_REMOTE_RESET=0` — or
  `false`, or `no` — switched the protection off, while the refusal message asked for `=1`. A
  variable somebody wrote into a profile as a disabler worked as an enabler.
- **"Local" is not "disposable."** An SSH tunnel or a `kubectl port-forward` to a shared database
  answers on `127.0.0.1` and carries `guestbook_entries`, so it was indistinguishable from the
  compose container. The guard had no concept of ownership at all.

`tests/tooling/test_e2e_harness.py` checked exactly one connection-string shape and exactly one
opt-in value — the only two cases the old implementation got right. `docs/configuration.md` and
`docs/troubleshooting.md` promised an interlock stronger than the one that existed.

No leak is claimed: this is a report about protection from a configuration mistake, not about a
mistake anybody made.

## From what, to what

**Before.** One gate, on text. `host` read out of the connection string, compared against four
names, overridable by any non-empty string in one variable. Everything after it — the connection,
the required-tables check, the `TRUNCATE` — trusted that answer. The required-tables check looked
like a second gate and was not: it proves the schema is this application's, which a shared staging
database satisfies exactly as well as a throwaway container does.

**After.** Two gates, and only the second is consent.

The first still reads the connection string, and now refuses to guess: a string that does not
locate its target, or locates it through a service file, or names any address that is not this
host without an exactly-valued opt-in, is refused before a connection opens. It hands libpq
explicit parameters rather than a string, and empties `PGHOST`, `PGHOSTADDR`, `PGPORT`,
`PGDATABASE`, `PGUSER`, `PGSERVICE` and `PGSERVICEFILE` around the connect, so there is no second,
invisible way to aim it.

The second asks the database. On the connection that will truncate, before any statement that
deletes is composed, one query returns `current_database()`, `current_user`,
`inet_server_addr()`, `inet_server_port()`, `pg_backend_pid()` and the database's own comment. The
comment is the criterion; the address is material for the message, because a tunnel is still a
tunnel and the address at the end of one lies.

## How it works now

A disposable database says so in itself:

```
sdd-e2e-disposable run_id=1789570227-88843 stamped_at=2026-09-16T14:50:27+00:00
```

`./scripts/test.sh e2e` mints `E2E_RUN_ID` (never inherited — an id left in a shell profile would
keep an old mark matching for ever), resolves the database, and writes that comment. The harness
refuses a database whose comment is absent, carries another run's id, carries no readable time, or
is older than twelve hours.

Who may write the mark is the whole decision. A database `test.sh` provisioned through compose is
disposable by construction, so it stamps it. A `DATABASE_URL` somebody else set is not, and the
script has no way to find out — so it stops, and names both ways forward:

```
refusing to mark 'app' disposable: DATABASE_URL was already set in this environment, so this
script did not create that database and cannot tell whether emptying it is safe …

Two ways forward:
  * unset DATABASE_URL, and this script provisions a throwaway Postgres itself, or
  * set E2E_ALLOW_REMOTE_RESET=app to say you have looked at that database and it is yours to
    empty.
```

The second form is scoped on purpose: it names one database, so consent does not carry over to the
next target. `_lib.sh`'s rule that a supplied `DATABASE_URL` is never silently overridden is
untouched — the URL is honoured, or the run stops. It is never swapped for another.

The marker is a `COMMENT ON DATABASE` and not a marker table, and that is a decision with a
reason: `alembic/` is the schema's only owner (`spec/design/data-model.md` § Owner of the schema),
so a table would either be created behind Alembic's back or ship in a revision — and a revision
would put an `e2e_disposable` table in production, which is an invitation rather than a guard. A
comment is still content of the database, held in a catalogue no client configuration can forge,
and it costs no schema change and no `NEVER_TRUNCATED` entry.

## What it means for the process

For a person or an agent running the suite the normal way — `./scripts/test.sh e2e`,
`./scripts/test.sh ui`, `./scripts/check.sh` — **nothing moves**. The script does the marking.

Two things change for a hand-run:

- `uv run pytest e2e/suite` with `DATABASE_URL` exported now refuses, naming the script it
  skipped. It used to empty whatever that variable pointed at.
- `./scripts/test.sh e2e` with `DATABASE_URL` already in the environment refuses until
  `E2E_ALLOW_REMOTE_RESET` names that database. That is the one deliberate behaviour change a
  person can be surprised by, and it is the point of the change.

## What it does not change

- **`.github/workflows/ci.yml` is untouched, and the issue expected otherwise.** It reads
  `ci.yml:881` as the E2E leg's `DATABASE_URL` and asks for the workflow and the harness to land
  together. Line 881 belongs to the macOS `db.sh migrate` step; the E2E job runs a bare
  `./scripts/test.sh e2e` with no `DATABASE_URL`, takes the compose branch of
  `resolve_database_url`, and is therefore marked by the script like any other run.
- **No schema change, no migration, no new table.** `NEVER_TRUNCATED` is unchanged.
- **The application is untouched.** No route, no model, no service, no screen.
- **`APP_TEST_DATABASE_URL` is untouched** — the backend suite's bring-your-own-Postgres route
  still works exactly as it did, and creates its own database per test as before.
- **The application-coherence check stays after the reset.** The issue asks for a mirror of it
  before the reset as well; there is nothing to mirror, because no route discloses which database
  the application is reading and adding one would publish the DSN. The pre-reset check is the mark,
  read on the truncating connection.
- **The address is still not proof**, and this change does not pretend it is. It is read from the
  server so a refusal can name the database that was actually reached, and it decides nothing.

## How it was verified

- `./scripts/test.sh tooling` — 254 passed. `test_run_script.py::test_run_script_starts_backend_and_serves_health`
  failed once under load against its five-second readiness timeout and passes in isolation; it
  touches nothing in this change.
- `./scripts/test.sh integration -k e2e_reset` — 5 passed. This is the half no fake can stand in
  for: the comment written by `mark_disposable` is the one `shobj_description` gives back, a marked
  database is emptied and reports a count above zero, `alembic_version` survives, and an unmarked
  database — migrated, carrying `guestbook_entries`, answering on this host — keeps its rows.
- `./scripts/test.sh e2e` — 44 passed, 30 of 30 scenario items collected, with
  `app: sdd-e2e-disposable run_id=… stamped_at=…` printed before the run. The compose port had to
  be moved (`POSTGRES_HOST_PORT=5462 APP_PORT=8090`) because other worktrees on this machine hold
  5432, 5442 and 5452; nothing in the run depends on the number.
- By hand, both halves of the decision above:
  `DATABASE_URL=postgresql+psycopg://app:app@localhost:5462/app ./scripts/test.sh e2e` refuses and
  exits 1, having started no application and emptied nothing; the same command with
  `E2E_ALLOW_REMOTE_RESET=app` runs green.
- `./scripts/lint.sh` — ruff, ruff format, mypy --strict over 102 files, eslint and tsc all clean.
- `./scripts/check.sh` — the local definition of "will CI pass".

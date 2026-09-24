"""The end-to-end reset's guard, against a real Postgres.

`tests/tooling/test_e2e_harness.py` proves the refusals, and it proves them on a
fake connection because its own rule -- **nothing there may hand
`reset_target_database` a real connection string** -- exists so that a "harmless"
reset cannot empty the database the rest of that suite is using. That rule leaves
one claim it cannot make: that the thing being refused would otherwise have
worked, and that the marker the guard reads is one Postgres actually stores and
gives back.

So this file is the positive control, and it is here rather than there for the
one reason that matters: every test below creates **its own** migrated database
through `tests/_database.py` and touches nothing else. The session-wide database
the rest of the suite runs on is never the target.

Two facts are proved here and nowhere else:

* `COMMENT ON DATABASE` survives the round trip -- written by `mark_disposable`,
  read back by `shobj_description(oid, 'pg_database')` in `target_identity`. A
  marker the server does not return is a guard that refuses every run, including
  the legitimate ones, and a fake cursor cannot tell you which it is.
* a marked database is emptied, and `reset_target_database` reports a count
  greater than zero -- "the reset succeeded" and "the reset found something to
  do" being different claims.
"""

import uuid
from collections.abc import Iterator

import pytest
import sqlalchemy as sa
from sqlalchemy.engine import make_url

from e2e.harness.database import (
    RUN_ID_VAR,
    mark_disposable,
    open_connection,
    reset_target_database,
    target_identity,
)
from tests._database import create_migrated_database

#: The one table in this application's schema that holds a scenario's state.
#: Named rather than discovered, because this file is asserting that discovery
#: found it.
REQUIRED: frozenset[str] = frozenset({"guestbook_entries"})


def _run(url: str, statement: str, **parameters: object) -> sa.Result[sa.Row[tuple[object, ...]]]:
    """One statement against `url`, on a connection that is closed again at once.

    A connection per call and not a fixture: `reset_target_database` takes an
    ACCESS EXCLUSIVE lock, and a session this file was holding open would turn a
    refusal into a wait and then into a `statement_timeout`, which reads as an
    entirely different fault.
    """
    engine = sa.create_engine(url, isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as connection:
            return connection.execute(sa.text(statement), parameters)
    finally:
        engine.dispose()


def _entry_count(url: str) -> int:
    return int(_run(url, "SELECT count(*) FROM guestbook_entries").scalar_one())


def _write_an_entry(url: str) -> None:
    _run(
        url,
        "INSERT INTO guestbook_entries (id, author, message, created_at, updated_at) "
        "VALUES (:id, :author, :message, now(), now())",
        id=uuid.uuid4(),
        author="Anna",
        message="hello",
    )


@pytest.fixture
def unmarked_database() -> str:
    """A migrated database of this test's own, carrying no disposability mark.

    This is what a shared environment behind a port-forward looks like from the
    harness: migrated, holding `guestbook_entries`, answering on this very host.
    """
    return create_migrated_database()


@pytest.fixture
def disposable_database(
    unmarked_database: str, monkeypatch: pytest.MonkeyPatch
) -> Iterator[tuple[str, str]]:
    """The same database, marked as THIS test's to empty. Yields `(url, run_id)`.

    The run id is unique per test, so the mark written here cannot be the one a
    neighbouring test is reading -- which is the same property the guard relies
    on between one `./scripts/test.sh e2e` and the next.
    """
    run_id = f"integration-{uuid.uuid4().hex}"
    monkeypatch.setenv(RUN_ID_VAR, run_id)

    database = make_url(unmarked_database).database
    assert database is not None, "create_migrated_database names the database it made"
    with open_connection(unmarked_database) as connection:
        mark_disposable(connection, run_id=run_id, database=database)
    yield unmarked_database, run_id


def test_the_mark_a_run_writes_is_the_mark_the_server_gives_back(
    disposable_database: tuple[str, str],
) -> None:
    """The round trip nothing else can check.

    `mark_disposable` writes a `COMMENT ON DATABASE`; `target_identity` reads it
    through `shobj_description`. Those are two different catalogues' worth of
    assumption, and a fake cursor answers whatever it was handed.
    """
    url, run_id = disposable_database

    with open_connection(url) as connection:
        identity = target_identity(connection)

    assert identity.marker is not None
    assert f"run_id={run_id}" in identity.marker
    assert identity.database == make_url(url).database
    assert identity.backend_pid > 0


def test_a_marked_database_is_emptied_and_says_how_many_tables_it_found(
    disposable_database: tuple[str, str],
) -> None:
    """The positive control the acceptance criterion asks for.

    The count matters as much as the emptiness: a reset that reported success
    while finding nothing to do would be the silent-green this whole harness is
    built to refuse, which is why `truncate_statement` raises rather than allow
    it.
    """
    url, _ = disposable_database
    _write_an_entry(url)
    assert _entry_count(url) == 1

    truncated = reset_target_database(url, required=REQUIRED)

    assert truncated > 0, "the reset found tables to empty"
    assert _entry_count(url) == 0


def test_alembics_bookkeeping_survives_a_reset(disposable_database: tuple[str, str]) -> None:
    """Truncating it would make the next upgrade replay every migration.

    Asserted against a database Alembic actually migrated rather than against a
    list of table names, because the claim is about what `NEVER_TRUNCATED` does
    to a real schema.
    """
    url, _ = disposable_database

    reset_target_database(url, required=REQUIRED)

    assert _entry_count(url) == 0
    assert int(_run(url, "SELECT count(*) FROM alembic_version").scalar_one()) == 1


def test_an_unmarked_database_keeps_its_rows(
    unmarked_database: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The refusal, proved where it counts: the rows are still there afterwards.

    `tests/tooling/` proves that no deleting statement is composed. This proves
    the consequence, against a database that is migrated, carries
    `guestbook_entries` and answers on this host -- every signal the guard used
    to accept as permission.
    """
    monkeypatch.setenv(RUN_ID_VAR, "a-run-that-stamped-nothing")
    _write_an_entry(unmarked_database)

    with pytest.raises(RuntimeError, match="does not carry the mark of a disposable database"):
        reset_target_database(unmarked_database, required=REQUIRED)

    assert _entry_count(unmarked_database) == 1


def test_a_mark_from_another_run_keeps_the_rows_too(
    disposable_database: tuple[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A stamp is consent for one run, and expires with it.

    The database below is genuinely disposable -- this file stamped it -- and it
    is still refused, because the run asking is not the run that stamped it. That
    is what stops a marker left behind on a developer's machine authorising every
    reset that follows it.
    """
    url, _ = disposable_database
    _write_an_entry(url)
    monkeypatch.setenv(RUN_ID_VAR, "some-later-run")

    with pytest.raises(RuntimeError, match="marked disposable by a different run"):
        reset_target_database(url, required=REQUIRED)

    assert _entry_count(url) == 1

"""A preview's database is created and migrated by the release step itself.

Terraform cannot do this. It runs on a GitHub runner, the cluster has no address
reachable from outside its VPC, and there is therefore no route by which the
`postgresql` provider could reach it. So the migration function creates the
branch's database on first invocation and then migrates it -- which puts DDL on a
code path production also runs, and makes this the riskiest piece of the whole
preview arrangement.

**Every failure it can have is silent on a developer's machine**, which is why
this file exists rather than a comment:

- `CREATE DATABASE` cannot run inside a transaction block, and `engine.begin()`
  opens one. The obvious spelling fails only when it is actually run.
- `str(url)` masks a password as `***`, so a target URL built the obvious way
  connects nowhere, slowly.
- Alembic stores its options in a `ConfigParser`, which reads `%` as an
  interpolation and **raises when the value is set**. A deployed URL carries a
  percent-encoded password; a local one does not. The last test here builds a URL
  with a real percent-encoded password for exactly that reason.

`DB_IAM_USER` is deliberately never set below. `_ensure_iam_login` would then
`GRANT rds_iam`, which exists on RDS and on no ordinary Postgres -- the one part
of this path that cannot be exercised anywhere but AWS, and saying so is better
than a test that pretends otherwise.
"""

import pytest
import sqlalchemy as sa
from sqlalchemy.engine import make_url

import tests._database as database
from app.db import session as db_session
from app.lambda_handler import migrate, preview_maintenance

#: Named so a leak is obvious in a `\\l` listing, and so it passes the guard in
#: `app/lambda_handler.py` -- which refuses anything without the prefix.
PREVIEW = "preview_branch_a1b2c3"


@pytest.fixture
def maintenance(monkeypatch: pytest.MonkeyPatch):
    """A database standing in for the shared cluster's own, with the app pointed at it.

    The module attributes are patched rather than the environment variable, because
    `app/db/session.py` builds its engine at import and the handler reads
    `DATABASE_URL` and `engine` from that module at call time. Patching what it
    reads is the honest way to redirect it; setting an environment variable would
    change nothing and pass for the wrong reason.
    """
    url = database.create_database()
    engine = sa.create_engine(url)
    monkeypatch.setattr(db_session, "DATABASE_URL", url)
    monkeypatch.setattr(db_session, "engine", engine)
    try:
        yield url
    finally:
        engine.dispose()
        _drop(url, PREVIEW)


def _drop(maintenance_url: str, name: str) -> None:
    """Tidy up whatever the test left, without going through the code under test."""
    admin = sa.create_engine(maintenance_url, isolation_level="AUTOCOMMIT")
    try:
        with admin.connect() as connection:
            connection.execute(sa.text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
    finally:
        admin.dispose()


def _databases(maintenance_url: str) -> set[str]:
    engine = sa.create_engine(maintenance_url)
    try:
        with engine.connect() as connection:
            rows = connection.execute(sa.text("SELECT datname FROM pg_database")).scalars()
            return set(rows)
    finally:
        engine.dispose()


def _tables(maintenance_url: str, database_name: str) -> set[str]:
    url = make_url(maintenance_url).set(database=database_name)
    engine = sa.create_engine(url)
    try:
        return set(sa.inspect(engine).get_table_names())
    finally:
        engine.dispose()


def test_the_branch_database_is_created_and_migrated(
    maintenance: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The whole path, end to end, against a real Postgres."""
    monkeypatch.setenv("PREVIEW_DATABASE", PREVIEW)

    result = migrate()

    assert result["status"] == "ok"
    assert result["database"] == PREVIEW
    assert result["created"] is True
    assert PREVIEW in _databases(maintenance)

    tables = _tables(maintenance, PREVIEW)
    assert "alembic_version" in tables, "the branch's database was created but never migrated"
    assert "guestbook_entries" in tables


def test_the_migration_lands_in_the_branch_database_and_not_the_other_one(
    maintenance: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The assertion that catches `set_main_option` not taking.

    Without it, a migration that silently ran against the connection the function
    already had would look identical: `alembic_version` exists, the tables exist,
    every other assertion above passes -- and every branch would share one schema
    on the cluster's own database.
    """
    monkeypatch.setenv("PREVIEW_DATABASE", PREVIEW)

    migrate()

    maintenance_tables = _tables(maintenance, make_url(maintenance).database or "")
    assert maintenance_tables == set(), (
        f"the migration ran against the cluster's own database, which now holds "
        f"{sorted(maintenance_tables)}"
    )


def test_running_it_again_migrates_without_creating(
    maintenance: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every push to a branch redeploys its preview; only the first finds nothing there."""
    monkeypatch.setenv("PREVIEW_DATABASE", PREVIEW)

    assert migrate()["created"] is True
    second = migrate()

    assert second["created"] is False
    assert second["status"] == "ok"


def test_the_maintenance_handler_drops_it(
    maintenance: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Teardown, and its two runs.

    A merge with auto-delete fires both `pull_request: closed` and `delete`, so the
    drop happens twice and the second must be quiet rather than an error somebody
    has to go and read.
    """
    monkeypatch.setenv("PREVIEW_DATABASE", PREVIEW)
    migrate()
    assert PREVIEW in _databases(maintenance)

    assert preview_maintenance({"action": "drop", "database": PREVIEW})["status"] == "ok"
    assert PREVIEW not in _databases(maintenance)

    assert preview_maintenance({"action": "drop", "database": PREVIEW})["status"] == "ok"


def test_the_maintenance_handler_refuses_anything_that_is_not_a_preview(
    maintenance: str,
) -> None:
    """It holds the master password and connects to the cluster's own database.

    The name it is given comes from a branch, and the statement it reaches is
    `DROP DATABASE "<name>"` -- interpolated, because identifiers cannot be bound.
    """
    for name in (make_url(maintenance).database, "postgres", 'x"; DROP DATABASE postgres; --'):
        with pytest.raises(ValueError):
            preview_maintenance({"action": "drop", "database": name})

    with pytest.raises(ValueError):
        preview_maintenance({"action": "truncate", "database": PREVIEW})


def test_a_password_that_has_to_be_percent_encoded_still_migrates(
    maintenance: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The defect that stopped every deployed migration, proved against a real database.

    A role is created whose password contains `=`, `[` and `]` -- three of the
    characters `random_password.master` is generated from in
    `infra/terraform/modules/database/main.tf`. SQLAlchemy then percent-encodes
    them when it renders the URL, exactly as Terraform's `urlencode()` does, and
    Alembic's `ConfigParser` reads every `%` as an interpolation and **raises when
    the value is set**.

    The percent signs have to come from a password that genuinely needs them.
    Writing `%65` into the input URL instead does nothing: `make_url` decodes it and
    `render_as_string` re-renders only what must be encoded, so the artificial
    version survived the escape being deleted -- a test that could not fail, which
    is worse than no test. This one fails with `ValueError: invalid interpolation
    syntax` the moment `app/db/alembic_url.py` stops escaping.
    """
    role = "preview_pw_role"
    password = "p=ss[w]rd"

    admin = sa.create_engine(maintenance, isolation_level="AUTOCOMMIT")
    try:
        with admin.connect() as connection:
            connection.execute(sa.text(f'DROP ROLE IF EXISTS "{role}"'))
            connection.execute(
                sa.text(f"CREATE ROLE \"{role}\" WITH LOGIN CREATEDB PASSWORD '{password}'")
            )
    finally:
        admin.dispose()

    url = make_url(maintenance).set(username=role, password=password)
    rendered = url.render_as_string(hide_password=False)
    assert "%" in rendered, (
        f"{rendered!r} carries no percent sign, so this test proves nothing about "
        "the defect it exists for"
    )

    engine = sa.create_engine(rendered)
    monkeypatch.setattr(db_session, "DATABASE_URL", rendered)
    monkeypatch.setattr(db_session, "engine", engine)
    monkeypatch.setenv("PREVIEW_DATABASE", PREVIEW)

    try:
        assert migrate()["status"] == "ok"
        assert "alembic_version" in _tables(rendered, PREVIEW)
    finally:
        engine.dispose()
        _drop(maintenance, PREVIEW)
        admin = sa.create_engine(maintenance, isolation_level="AUTOCOMMIT")
        try:
            with admin.connect() as connection:
                connection.execute(sa.text(f'DROP ROLE IF EXISTS "{role}"'))
        finally:
            admin.dispose()

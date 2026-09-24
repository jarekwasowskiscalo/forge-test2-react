"""Where an isolated, migrated database comes from.

**Postgres, and nothing else** (`spec/design/architecture.md` § One engine). There is no second engine to choose
between any more, which is the point: every test in this suite runs on the
engine production runs on, so a test that passes says something about
production rather than about a stand-in.

Two ways to reach one: a Postgres somebody already has, named by
`APP_TEST_DATABASE_URL`, or an ephemeral container this module starts. Either
way a caller asks for a migrated database and gets one, uniquely named, that no
other test can see.

The supplied-server route is what makes this suite runnable on a machine with no
Linux-container Docker -- a macOS laptop, the macOS CI leg -- and it is why the
escape hatch could be removed rather than merely deprecated.
"""

import atexit
import os
from uuid import uuid4

import sqlalchemy as sa
from alembic.config import Config
from sqlalchemy.engine import make_url

from alembic import command
from app.db.alembic_url import for_alembic_config
from tests._repo import REPO_ROOT

_container: object | None = None


def get_container() -> object:
    """The shared session-wide Postgres container, started on first use."""
    global _container
    if _container is None:
        from testcontainers.community.postgres import PostgresContainer

        container = PostgresContainer("postgres:16-alpine", driver="psycopg")
        container.start()
        atexit.register(container.stop)
        _container = container
    return _container


#: Env var that hands the suite a Postgres somebody else provisioned -- a natively
#: installed server, or a shared one, on a machine with no Linux-container Docker.
#: It names a SERVER, not a database: every route below still creates its own uniquely
#: named, migrated logical database inside it, exactly as the container path does.
#:
#: It lives here rather than in `tests/conftest.py`, where it was declared, because
#: here is where it has to be READ. `conftest` consulted it for the session-wide URL
#: and nothing else did, so `fresh_database` and every other caller went on starting
#: a container through `_base_url` -- and a run on a Postgres host
#: with no Docker announced "no Docker needed" and then failed partway through with a
#: buried container error.
EXTERNAL_DATABASE_URL_VAR = "APP_TEST_DATABASE_URL"


def external_database_url() -> str | None:
    """The Postgres somebody else provisioned, or `None`.

    Empty is `None`: `APP_TEST_DATABASE_URL=` left in a shell profile means "unset",
    and connecting to the empty string fails a long way from here.
    """
    return os.environ.get(EXTERNAL_DATABASE_URL_VAR) or None


def _base_url() -> str:
    """The server to create test databases in: the supplied one, else a container.

    The one place the two provisioning routes meet, so they cannot disagree about
    which server a run means.
    """
    supplied = external_database_url()
    if supplied is not None:
        return supplied
    url: str = get_container().get_connection_url()  # type: ignore[attr-defined]
    return url


#: `(server, database)` for everything created on a server this suite does not own.
#: Empty on the container path, which needs no bookkeeping.
_created_on_a_supplied_server: list[tuple[str, str]] = []


def _drop_when_the_session_ends(base_url: str, db_name: str) -> None:
    """Register one `atexit` hook for the whole list, not one per database."""
    if not _created_on_a_supplied_server:
        atexit.register(_drop_the_databases_this_session_created)
    _created_on_a_supplied_server.append((base_url, db_name))


def _drop_the_databases_this_session_created() -> None:
    """Best effort, and deliberately so: this runs while the interpreter is shutting
    down, and a failure to tidy up must never be the thing that fails a green run.

    `WITH (FORCE)` because a session that ended badly can leave a connection open,
    and a DROP that blocks on it would hang the exit instead of cleaning up.
    """
    if not _created_on_a_supplied_server:
        return
    server = _created_on_a_supplied_server[0][0]
    try:
        admin_engine = sa.create_engine(server, isolation_level="AUTOCOMMIT")
        with admin_engine.connect() as conn:
            for _, db_name in _created_on_a_supplied_server:
                conn.execute(sa.text(f'DROP DATABASE IF EXISTS "{db_name}" WITH (FORCE)'))
        admin_engine.dispose()
    except sa.exc.SQLAlchemyError:
        names = ", ".join(name for _, name in _created_on_a_supplied_server)
        print(f"could not drop the test databases this run created: {names}")
    finally:
        _created_on_a_supplied_server.clear()


def create_database() -> str:
    """A fresh, empty, uniquely named database, unmigrated. Returns its URL."""
    base_url = _base_url()
    db_name = f"test_{uuid4().hex}"
    admin_engine = sa.create_engine(base_url, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        conn.execute(sa.text(f'CREATE DATABASE "{db_name}"'))
    admin_engine.dispose()
    # A container takes its databases with it when it stops, so nothing ever had to
    # clean up. A server somebody else provisioned does not, and a full run creates
    # one database per `fresh_database` test -- so the supported path would quietly
    # fill a developer's Postgres a few dozen entries at a time.
    if external_database_url() is not None:
        _drop_when_the_session_ends(base_url, db_name)
    return make_url(base_url).set(database=db_name).render_as_string(hide_password=False)


def migrate(url: str) -> None:
    """Run `alembic upgrade head` against the given database URL."""
    cfg = Config(str(REPO_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", for_alembic_config(url))
    command.upgrade(cfg, "head")


def create_migrated_database() -> str:
    """A fresh, uniquely named database, migrated to head."""
    url = create_database()
    migrate(url)
    return url

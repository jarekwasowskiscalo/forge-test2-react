"""Shared pytest fixtures for the test suite.

Provides a reusable FastAPI TestClient fixture (`client`) wrapping the
application instance from `app.main`. Future test modules depend on this
fixture rather than constructing their own TestClient.

The app's default backend is Postgres (see app/db/session.py), so most of the
suite needs a real Postgres instance too. Rather than requiring one to already
be running, `pytest_configure` starts an ephemeral, migrated database via
testcontainers - before any `app.*` module is imported, because
`app/db/session.py` builds its Engine at import time and the URL has to exist
by then. Running the full suite therefore needs a Docker daemon capable of
running **Linux** containers.

Three ways out of that requirement, in order of preference:

- `--no-db` runs only the tests marked `no_db` - the ones that touch no
  database at all - and provisions nothing. That is most of the suite, and it
  is the part where a platform regression actually shows (text decoding, path
  handling, line endings), so the macOS CI leg runs
  it rather than nothing.
- `APP_TEST_DATABASE_URL` points the suite at a Postgres somebody else
  provisioned - a natively installed server, for instance, on a machine with no
  Linux-container Docker. It names a SERVER, not a database:
  the suite still creates its own uniquely named, migrated logical database
  inside it, exactly as it does inside a container. `tests/_database.py` reads
  it, so every provisioning route honours it and not merely this one.
- otherwise, testcontainers.

The provisioned database is bound for the whole session, so a test that needs
to start from an empty schema - or to ingest a day the rest of the suite has
already ingested - asks for the `fresh_database` fixture instead.
"""

import importlib
import os
import pkgutil
import sys
from types import ModuleType

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import tests._database as database

#: Declared in `tests/_database.py`, because that is where it is READ -- by every
#: provisioning route, not just this one. Re-exported here so the name still resolves
#: where it was first written down.
EXTERNAL_DATABASE_URL_VAR = database.EXTERNAL_DATABASE_URL_VAR


def pytest_configure(config: pytest.Config) -> None:
    """Resolve `DATABASE_URL` before any `app.*` module is imported.

    `app/db/session.py` builds its `Engine` at import time, so the URL has to
    exist first. This used to run at module scope, which meant *collecting* a
    test that touches no database still started a container -- and that single
    fact is why `pytest` has only ever run on Linux in CI.
    """
    if config.getoption("--no-db"):
        # Never opened: every test that would touch it is deselected below, and
        # SQLAlchemy does not connect when the engine is built. It exists only so
        # importing `app.db.session` succeeds -- and it names a host nothing can
        # reach on purpose, so a test that slipped through the deselection fails
        # on a refused connection rather than quietly finding a real database.
        os.environ.setdefault(
            "DATABASE_URL", "postgresql+psycopg://nobody@no-database.invalid:5432/none"
        )
        return
    # One route, whichever server it lands on: `_base_url` resolves the supplied
    # Postgres or starts a container, and either way this run gets its own uniquely
    # named, MIGRATED database. Reading the variable here instead -- as this line used
    # to -- handed the run an unmigrated database nobody had prepared, and left every
    # other provisioning route reaching for a container regardless.
    os.environ["DATABASE_URL"] = database.create_migrated_database()


@pytest.fixture
def client():
    """Yield a TestClient bound to the application under test.

    `app.main` is imported here, not at module scope: under `--no-db` nothing
    should import the application at all, and an import-time side effect is
    what this module spent its first version working around.

    The host carries no meaning, and an earlier version of this docstring said
    it did. `base_url` names `localhost` because that is a real hostname rather
    than a sentinel, and for no stronger reason: this application sets no cookie
    and opens no session -- authentication is a named non-goal
    (`spec/invariants.md` § Deliberate non-goals) -- and it installs no
    host-sensitive middleware, so the whole backend suite passes on
    `TestClient`'s default `http://testserver` just as well.
    """
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app, base_url="http://localhost") as test_client:
        yield test_client


def _reraise(name: str) -> None:
    raise ImportError(f"could not import {name} while scanning for SessionLocal holders")


def session_local_holders() -> list[ModuleType]:
    """Return every `app.*` module that holds its own `SessionLocal` name.

    Each service module does `from app.db.session import SessionLocal`, which
    copies the factory into that module's globals; rebinding only
    `app.db.session.SessionLocal` therefore reaches none of them. The holders
    are discovered rather than listed because a service added later would
    otherwise keep writing to the session-wide database while a test believed
    it had an isolated one - and that failure surfaces as some other test's
    data appearing, arbitrarily far from its cause.
    """
    package = importlib.import_module("app")
    for module_info in pkgutil.walk_packages(package.__path__, prefix="app.", onerror=_reraise):
        importlib.import_module(module_info.name)

    return [
        module
        for name, module in sorted(sys.modules.items())
        if name.startswith("app.") and module is not None and hasattr(module, "SessionLocal")
    ]


@pytest.fixture
def fresh_database(monkeypatch) -> sessionmaker:
    """Bind every `SessionLocal` holder to a new migrated database for one test.

    The database is another logical database inside the same session-wide
    testcontainers Postgres instance (see `tests/_database.py`), so this costs
    a CREATE DATABASE plus a migration run, not a container start.

    Yields the session factory, for asserting against that database directly.
    `monkeypatch` restores every rebound module attribute afterwards, failure
    or not, so a test that does not ask for this fixture still sees the
    suite-wide binding established at import time.
    """
    url = database.create_migrated_database()
    engine = create_engine(url)
    session_factory = sessionmaker(bind=engine)

    for module in session_local_holders():
        monkeypatch.setattr(module, "SessionLocal", session_factory)

    try:
        yield session_factory
    finally:
        engine.dispose()

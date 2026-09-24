"""A Postgres somebody else provisioned is used, and no container is started.

`tests/conftest.py` has advertised `APP_TEST_DATABASE_URL` since it was written --
"a natively installed server, for instance, on a machine with no Linux-container
Docker" -- and `spec/design/testing.md` names it as one
of the two escape hatches. It was wired for exactly one caller: the session-wide
`DATABASE_URL`.

Every other provisioning route went through `tests/_database.py::_base_url`, which
asked `get_container()` unconditionally. So `fresh_database` -- eleven modules use
it -- and `tests/_parity.py` still started testcontainers, and a run on a machine
with a real Postgres and no Docker would announce "no Docker needed" and then fail
partway through with a buried container error. That is the failure the prerequisite
checks in `scripts/test.sh` exist to prevent, arriving from inside the harness.

The variable therefore names a SERVER, not a database: every route creates its own
uniquely named, migrated logical database inside it. That is what makes the two
provisioning paths one path, and it is strictly better than the old reading --
per-run isolation, migrations actually applied, and nothing for the operator to set
up by hand beyond the server itself.
"""

import os
from typing import Any

import pytest

import tests._database as database

SUPPLIED = "postgresql+psycopg://someone:else@example.invalid:5432/theirs"


@pytest.fixture
def container_is_a_mistake(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Starting a container is the defect, so asking for one is recorded, not served."""
    asked: list[str] = []

    def refuse() -> object:
        asked.append("get_container")
        raise AssertionError("a container was started although a Postgres was supplied")

    monkeypatch.setattr(database, "get_container", refuse)
    return asked


def test_a_supplied_postgres_is_the_base_url(
    monkeypatch: pytest.MonkeyPatch, container_is_a_mistake: list[str]
) -> None:
    monkeypatch.setenv(database.EXTERNAL_DATABASE_URL_VAR, SUPPLIED)
    assert database._base_url() == SUPPLIED
    assert container_is_a_mistake == []


def test_creating_a_database_does_not_start_a_container_when_one_was_supplied(
    monkeypatch: pytest.MonkeyPatch, container_is_a_mistake: list[str]
) -> None:
    """The defect, at the call every `fresh_database` test reaches.

    `create_database` is stopped at the CREATE DATABASE it would issue against a
    server that does not exist -- the point is which URL it built, not that the
    statement lands.
    """
    monkeypatch.setenv(database.EXTERNAL_DATABASE_URL_VAR, SUPPLIED)
    created: list[str] = []

    def record(url: str, **kwargs: Any) -> object:
        created.append(url)
        raise RuntimeError("stop here: the URL is what this test is about")

    monkeypatch.setattr(database.sa, "create_engine", record)

    with pytest.raises(RuntimeError):
        database.create_database()

    assert created == [SUPPLIED], (
        "the admin connection went somewhere other than the supplied server"
    )
    assert container_is_a_mistake == []


def test_the_container_is_still_the_answer_when_nothing_was_supplied(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Prove the detector before trusting it.

    If `_base_url` had stopped calling `get_container` altogether, the two tests
    above would pass for the wrong reason and forever. So the unset case must still
    reach it.
    """
    monkeypatch.delenv(database.EXTERNAL_DATABASE_URL_VAR, raising=False)
    asked: list[str] = []

    class Fake:
        def get_connection_url(self) -> str:
            asked.append("asked")
            return "postgresql+psycopg://container/x"

    monkeypatch.setattr(database, "get_container", Fake)
    assert database._base_url() == "postgresql+psycopg://container/x"
    assert asked == ["asked"], "the container path is no longer reachable at all"


def test_an_empty_variable_is_not_a_supplied_database(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`APP_TEST_DATABASE_URL=` in a shell profile means "unset", not "connect to
    the empty string" -- and an empty URL fails far from here."""
    monkeypatch.setenv(database.EXTERNAL_DATABASE_URL_VAR, "")
    asked: list[str] = []

    class Fake:
        def get_connection_url(self) -> str:
            asked.append("asked")
            return "postgresql+psycopg://container/x"

    monkeypatch.setattr(database, "get_container", Fake)
    assert database._base_url() == "postgresql+psycopg://container/x"
    assert asked == ["asked"]


# --------------------------------------------------------------------------- #
# The two requests that contradict each other
# --------------------------------------------------------------------------- #


class _Config:
    """Just enough `pytest.Config` for `pytest_configure` to read its two flags."""

    def __init__(self, **flags: bool) -> None:
        self._flags = flags

    def getoption(self, name: str) -> bool:
        return self._flags.get(name, False)


def test_no_database_provisions_nothing_and_still_lets_the_app_import(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`--no-db` returns before any provisioning, and leaves behind a URL.

    The URL matters as much as the early return: `app/db/session.py` builds its
    engine at import time, so a run with no `DATABASE_URL` at all would fail on
    the import rather than on the deselection. It names a host nothing can reach,
    so a test that slipped past the deselection fails on a refused connection
    instead of quietly finding somebody's real database.
    """
    import tests.conftest as suite_conftest

    monkeypatch.delenv(database.EXTERNAL_DATABASE_URL_VAR, raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    created: list[str] = []
    monkeypatch.setattr(database, "create_migrated_database", lambda: created.append("x") or "")

    suite_conftest.pytest_configure(_Config(**{"--no-db": True}))

    assert created == [], "--no-db provisioned a database it promised not to"
    assert "no-database.invalid" in os.environ["DATABASE_URL"]

"""What the integration suite needs beyond the shared fixtures, and no more.

There is deliberately very little here. `tests/conftest.py` provides the two
that matter -- `client` (a `TestClient` on the real aggregate) and
`fresh_database` (the only place `SessionLocal` is rebound, a line
`tests/fitness/test_test_layout.py` holds) -- and this file adds one helper for
reading rows back.

**Why raw SQL and not the services.** `entries_in_database` is how a test checks
what actually landed on disk. Reading it back through `app.services` would make
the assertion and its subject the same code, so a service that never wrote
anything would pass by returning what it was given.

**Every UUID bind is a string.** These helpers take an id from a test that got
it as a `uuid.UUID` or as the string a JSON body carried, and normalising at the
boundary means a caller never has to know which -- `str()` on a `UUID` is exactly
the text form Postgres casts back into `uuid`.
"""

import uuid
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker


class Entries:
    """Read guestbook rows straight from the database this test is bound to."""

    def __init__(self, session_factory: sessionmaker) -> None:
        self._sessions = session_factory

    def _rows(self, statement: str, **params: Any) -> list[sa.Row[Any]]:
        with self._sessions() as session:
            return list(session.execute(sa.text(statement), params).all())

    def count(self) -> int:
        rows = self._rows("SELECT COUNT(*) FROM guestbook_entries")
        return int(rows[0][0])

    def exists(self, entry_id: uuid.UUID | str) -> bool:
        rows = self._rows(
            "SELECT COUNT(*) FROM guestbook_entries WHERE id = :id",
            # `str`, whatever the caller had: a test holding a `UUID` and a test
            # holding the string off a JSON body ask the same question, and the
            # helper should not make them ask it differently.
            id=str(entry_id),
        )
        return int(rows[0][0]) == 1

    def authors_newest_first(self) -> list[str]:
        rows = self._rows("SELECT author FROM guestbook_entries ORDER BY created_at DESC, id DESC")
        return [str(row[0]) for row in rows]

    def timestamps_of(self, entry_id: uuid.UUID | str) -> tuple[Any, Any]:
        rows = self._rows(
            "SELECT created_at, updated_at FROM guestbook_entries WHERE id = :id",
            id=str(entry_id),
        )
        return rows[0][0], rows[0][1]


@pytest.fixture
def entries(fresh_database: sessionmaker) -> Entries:
    """Database-side reads, against the isolated database this test was given."""
    return Entries(fresh_database)

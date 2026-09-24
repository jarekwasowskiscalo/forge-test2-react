"""The storage-backend-swap path.

Points a service at a second, independent database -- a separate logical
database inside the shared testcontainers Postgres instance -- re-runs the
migrations against it, and proves the service works unmodified.

The claim is `spec/design/conventions.md` § Layers made concrete: a service
that imported `fastapi` or reached for a request could not be rebound like this
at all, so this test is the observable consequence of the layering rule rather
than a restatement of it.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

import app.contexts.guestbook.services.guestbook_entries as entries_module
import tests._database as database
from app.contexts.guestbook.schemas.guestbook_entries import GuestbookEntryCreate


def test_same_service_and_migrations_work_against_a_different_database(monkeypatch) -> None:
    url = database.create_migrated_database()

    engine = create_engine(url, poolclass=NullPool)
    monkeypatch.setattr(entries_module, "SessionLocal", sessionmaker(bind=engine))

    created = entries_module.create_entry(
        GuestbookEntryCreate(author="Anna", message="the database was moved")
    )
    fetched = entries_module.get_entry(created.id)

    assert fetched.id == created.id
    assert fetched.message == "the database was moved"

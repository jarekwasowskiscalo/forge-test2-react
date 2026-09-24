"""Guestbook entry persistence and the rules that govern it.

Framework-agnostic seam for the guestbook: owns the SQLAlchemy session and the
transaction boundary, raises domain exceptions, and never names an HTTP status
code -- the router translates. Must not import anything from
`fastapi`/`starlette`, so every rule here stays callable from a migration, a
script or a future scheduled job (spec/design/conventions.md § Layers).

Three rules live here rather than in the schema, because all three are about an
entry's life rather than about one request's shape:

- **`BR-02`** -- an edit moves `updated_at` and never `created_at`. Enforced by
  simply not assigning `created_at` anywhere except at creation.
- **`BR-04`** -- the list has a total order in **both** directions, and the
  ordering is part of the contract rather than a coincidence of insertion order.
  Ties break on `id`, so two entries written in the same clock tick still come
  back in a stable order; without it a paged read shows one entry twice and
  misses another.
- **`BR-05`** -- a read may be narrowed by a phrase and cut into pages, and the
  two counts it answers with are counted rather than inferred from the page.
"""

import datetime
import uuid

from sqlalchemy import ColumnElement, Select, func, or_, select
from sqlalchemy.orm import Session

from app.contexts.guestbook.models.guestbook_entry import GuestbookEntry
from app.contexts.guestbook.schemas.guestbook_entries import (
    PAGE_SIZE_DEFAULT,
    GuestbookEntryCreate,
    GuestbookEntryPage,
    GuestbookEntryRead,
    GuestbookEntrySort,
    GuestbookEntryUpdate,
)
from app.db.session import SessionLocal
from app.platform.schemas.text import normalize


class GuestbookEntryNotFoundError(Exception):
    """Raised when a requested entry id does not exist."""


def _now() -> datetime.datetime:
    """The one clock this module reads.

    A single function rather than scattered `datetime.now(UTC)` calls so a test
    that needs to control time has one seam to take, and so `created_at` and
    `updated_at` of a freshly created entry are provably the same instant rather
    than two instants that happen to round the same way.
    """
    return datetime.datetime.now(datetime.UTC)


def _read(row: GuestbookEntry) -> GuestbookEntryRead:
    return GuestbookEntryRead(
        id=row.id,
        author=row.author,
        message=row.message,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _match(phrase: str) -> ColumnElement[bool]:
    """Rows whose signature **or** whose text contains `phrase`, ignoring case.

    Both columns, because a guest looking for "Anna" cannot be expected to know
    whether Anna signed the entry or is named inside somebody else's. One field
    would make half the hits invisible with no way to tell.

    `autoescape=True` is doing real work: `%` and `_` are `LIKE` wildcards, so a
    guest searching for `100%` would otherwise match every entry in the book --
    silently, and looking exactly like a search that found a lot.

    **`icontains` and not a `lower()` in Python.** `icontains` folds both sides
    with the *same* `lower()`, the database's own, and the symmetry is the point:
    lowering the phrase here and the column in SQL would compare a folded needle
    against a haystack folded by different rules, and an exact phrase would stop
    matching itself.

    Postgres folds by Unicode, so `É` finds `é` -- which is a property of the
    engine this application runs on and of no other (`spec/design/architecture.md` § One engine).

    **The same symmetry argument applies to normalization, and it is met on one
    side only.** Since `app/platform/schemas/text.py` landed, every value written
    here is NFC, and so is every phrase -- so needle and haystack are folded alike
    for anything stored from that point on. Rows written BEFORE it were stored as
    they arrived, so a decomposed `é` sitting in an old row is not found by a
    phrase the caller typed precomposed. That was left rather than migrated: the
    guestbook is this template's worked example, no deployment holds data anybody
    depends on, and a backfill is an irreversible rewrite of a column against a
    complaint nobody has made. A deployment that does hold such data runs one
    `UPDATE ... SET author = normalize(author)` before trusting search over its
    history.
    """
    return or_(
        GuestbookEntry.author.icontains(phrase, autoescape=True),
        GuestbookEntry.message.icontains(phrase, autoescape=True),
    )


def _ordered(
    statement: Select[tuple[GuestbookEntry]], sort: GuestbookEntrySort
) -> Select[tuple[GuestbookEntry]]:
    """Apply `BR-04`'s order, whichever end the caller asked to read from.

    The tiebreaker turns with the sort rather than staying `id DESC` in both
    branches. Reversing only the date would leave the two entries written in the
    same tick in the *same* relative order under both sorts, so a book read
    oldest-first would not be the reverse of the same book read newest-first --
    and a page boundary landing between those two entries would drop one of them.
    """
    if sort is GuestbookEntrySort.OLDEST:
        return statement.order_by(GuestbookEntry.created_at.asc(), GuestbookEntry.id.asc())
    return statement.order_by(GuestbookEntry.created_at.desc(), GuestbookEntry.id.desc())


def _count(session: Session, condition: ColumnElement[bool] | None) -> int:
    """How many rows satisfy `condition`, or how many there are when it is `None`.

    `COUNT(*)` over the table rather than `len()` over the rows, so the number
    means the population and not the page -- and so the whole-book count stays
    one cheap query even when the page is four entries out of four thousand.
    """
    statement = select(func.count()).select_from(GuestbookEntry)
    if condition is not None:
        statement = statement.where(condition)
    return int(session.scalar(statement) or 0)


def list_entries(
    *,
    query: str | None = None,
    sort: GuestbookEntrySort = GuestbookEntrySort.NEWEST,
    limit: int = PAGE_SIZE_DEFAULT,
    offset: int = 0,
) -> GuestbookEntryPage:
    """One page of entries, plus how many match and how many exist (`BR-05`).

    `query` is normalized before it is measured, for the same reason `BR-01`
    normalizes what it stores: a phrase of spaces is no phrase, and treating it as
    one would hand back an empty book to somebody who typed nothing.

    Normalized here as well as at the router, and the repetition is deliberate:
    this module is the framework-agnostic seam, so a script or a scheduled job
    calling `list_entries` directly must get the same phrase the HTTP caller gets.
    `normalize` is idempotent, so the second application costs a comparison.

    Both counts are counted in the database rather than derived from `items`. A
    page cannot imply the size of the population it came from, which is the whole
    reason the envelope exists -- and `len(items)` is a plausible-looking number,
    so the mistake would not announce itself.
    """
    phrase = normalize(query or "")
    with SessionLocal() as session:
        total_all = _count(session, None)
        if phrase:
            condition = _match(phrase)
            total = _count(session, condition)
            rows_statement = select(GuestbookEntry).where(condition)
        else:
            # No phrase means the question is the whole book, so the two counts
            # are the same fact and counting twice would only be slower.
            total = total_all
            rows_statement = select(GuestbookEntry)
        rows = session.scalars(_ordered(rows_statement, sort).limit(limit).offset(offset)).all()
        return GuestbookEntryPage(
            items=[_read(row) for row in rows],
            total=total,
            total_all=total_all,
        )


def get_entry(entry_id: uuid.UUID) -> GuestbookEntryRead:
    """Return one entry.

    Raises:
        GuestbookEntryNotFoundError: if no entry with `entry_id` exists.
    """
    with SessionLocal() as session:
        row = session.get(GuestbookEntry, entry_id)
        if row is None:
            raise GuestbookEntryNotFoundError(str(entry_id))
        return _read(row)


def create_entry(data: GuestbookEntryCreate) -> GuestbookEntryRead:
    """Store a new entry with a freshly generated id."""
    written_at = _now()
    with SessionLocal() as session:
        row = GuestbookEntry(
            author=data.author,
            message=data.message,
            created_at=written_at,
            updated_at=written_at,
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return _read(row)


def update_entry(entry_id: uuid.UUID, data: GuestbookEntryUpdate) -> GuestbookEntryRead:
    """Apply the fields the caller gave and stamp `updated_at` (`BR-02`).

    A field left unset is left alone -- this is a PATCH, so "absent" means "do
    not touch" and never "clear".

    Raises:
        GuestbookEntryNotFoundError: if no entry with `entry_id` exists.
    """
    with SessionLocal() as session:
        row = session.get(GuestbookEntry, entry_id)
        if row is None:
            raise GuestbookEntryNotFoundError(str(entry_id))
        if data.author is not None:
            row.author = data.author
        if data.message is not None:
            row.message = data.message
        row.updated_at = _now()
        session.commit()
        session.refresh(row)
        return _read(row)


def delete_entry(entry_id: uuid.UUID) -> None:
    """Remove an entry permanently (`BR-03`).

    Raises:
        GuestbookEntryNotFoundError: if no entry with `entry_id` exists, so a
            second delete of the same id refuses rather than reporting success
            for something it did not do.
    """
    with SessionLocal() as session:
        row = session.get(GuestbookEntry, entry_id)
        if row is None:
            raise GuestbookEntryNotFoundError(str(entry_id))
        session.delete(row)
        session.commit()

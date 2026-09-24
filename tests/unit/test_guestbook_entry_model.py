"""The model's declaration, asserted without a database.

`tests/integration/test_migrations.py` proves the schema Alembic *creates*.
This proves what the **model says it should be** -- and the pair is the point:
they are two independent statements of one schema, and a migration that drifts
from the model shows up as exactly one of them failing.

Nothing here opens a connection. `Base.metadata` is populated at import, so the
table, its columns and their types are readable as data.
"""

import datetime
import uuid
from typing import Final

import sqlalchemy as sa
from sqlalchemy.sql.schema import CallableColumnDefault

from app.contexts.guestbook.models.guestbook_entry import (
    AUTHOR_MAX_LENGTH,
    MESSAGE_MAX_LENGTH,
    GuestbookEntry,
)
from app.db.base import Base

#: Every column the entity has. Compared on **equality**, so a column added to
#: the model without a line in `spec/design/data-model.md` fails here as well as
#: in the migration test -- containment would wave it through.
COLUMNS: Final[frozenset[str]] = frozenset({"id", "author", "message", "created_at", "updated_at"})


def _table() -> sa.Table:
    # `__table__` is typed as `FromClause` on the declarative base; for a mapped
    # class it is always a `Table`, and this is the one place that fact is needed.
    table = GuestbookEntry.__table__
    assert isinstance(table, sa.Table)
    return table


def _id_default() -> CallableColumnDefault:
    """The `id` column's default, narrowed to the callable kind.

    SQLAlchemy types `Column.default` as `DefaultGenerator | None`, which has no
    `arg`. The narrowing is an assertion rather than a cast because "the id has a
    callable default" is exactly what the tests below are about: a scalar default
    would hand every row the same id, and this line is where that is refused.
    """
    default = _table().c.id.default
    assert isinstance(default, CallableColumnDefault), (
        f"the id's default is {type(default).__name__}, not a callable one -- a scalar "
        "default would give every row the same id"
    )
    return default


def test_the_table_is_named_as_the_data_model_names_it() -> None:
    assert GuestbookEntry.__tablename__ == "guestbook_entries"


def test_the_entity_has_exactly_these_columns() -> None:
    assert {column.name for column in _table().columns} == COLUMNS


def test_this_schema_holds_exactly_one_table() -> None:
    """The template's whole schema. A second table appearing without a document is
    the drift this file exists to notice at the cheapest possible level."""
    assert set(Base.metadata.tables) == {"guestbook_entries"}


def test_the_primary_key_is_a_uuid_the_application_generates() -> None:
    """`D-03`. Generated application-side, so the id exists BEFORE the insert --
    which is the property a database-side default would take away.

    Asserted as **behaviour** rather than as an identity check against
    `uuid.uuid4`: SQLAlchemy wraps the callable to hand it an execution context,
    so comparing the function object means reaching under a wrapper this test has
    no business knowing about. Behaviour is also the stronger claim -- it rules
    out a callable that returns the same value every time, which an identity
    check would wave through.
    """
    id_column = _table().c.id

    assert id_column.primary_key
    assert isinstance(id_column.type, sa.Uuid)

    # `None` is the execution context; this default ignores it, which is exactly
    # what makes the id knowable without a connection. SQLAlchemy types the
    # parameter as required, so the call is narrowed here rather than at every
    # future use.
    generate = _id_default().arg
    first = generate(None)  # type: ignore[arg-type]
    second = generate(None)  # type: ignore[arg-type]

    assert isinstance(first, uuid.UUID)
    assert first != second, "the id default returns a constant -- every row would collide"


def test_no_column_is_nullable() -> None:
    """Every fact an entry carries is required. A nullable column here would be a
    fourth state -- "written, but we do not know by whom" -- that no rule describes."""
    nullable = [column.name for column in _table().columns if column.nullable]

    assert nullable == [], f"these columns became nullable with no rule saying so: {nullable}"


def test_the_signature_is_length_bounded_at_the_column() -> None:
    """The bound is in the database, not only in Pydantic.

    A value reaching the table by any other route -- a migration backfill, a
    fixture, a script -- is held to the same number, and there is only one number
    because the schema reads it from the same constant the request schema does.
    """
    author = _table().c.author.type

    assert isinstance(author, sa.String)
    assert author.length == AUTHOR_MAX_LENGTH


def test_the_message_is_text_so_its_ceiling_can_move_without_a_rewrite() -> None:
    """`Text`, deliberately, and `spec/design/data-model.md` says why: the ceiling
    is a product rule that will move, and moving it should be an edit to one
    Pydantic schema rather than a migration that rewrites a column type."""
    assert isinstance(_table().c.message.type, sa.Text)
    assert MESSAGE_MAX_LENGTH > AUTHOR_MAX_LENGTH, "the two limits have been swapped"


def test_both_timestamps_declare_a_time_zone() -> None:
    """ "Which entry is newer" must settle across an offset change. A naive column
    makes the answer depend on the server's local time, and the failure is silent
    until the clocks go back."""
    for name in ("created_at", "updated_at"):
        column = _table().c[name]
        assert isinstance(column.type, sa.DateTime)
        assert column.type.timezone is True, f"{name} lost its time zone"


def test_no_other_temporal_column_slipped_in() -> None:
    """Compared as a set: a new temporal column is a decision this test has to be
    told about, rather than one discovered later on a machine in another zone."""
    temporal = {
        column.name for column in _table().columns if isinstance(column.type, sa.DateTime | sa.Date)
    }

    assert temporal == {"created_at", "updated_at"}


def test_the_entity_carries_no_relationship() -> None:
    """The template's schema is one table and no edges. A relationship appearing
    here means a second context arrived, and `spec/contexts/` has to say so."""
    assert list(sa.inspect(GuestbookEntry).relationships) == []


def test_the_model_imports_no_web_framework() -> None:
    """`conventions.md` § Layers, at the one level a fitness function reads as
    text and this one reads as an object: the module is importable with no
    request in flight, which is what makes it usable from a migration.

    `tests/fitness/test_layering.py` proves the same rule across every module by
    reading source; this proves it about the one that matters most, by having
    already done it.
    """
    import sys

    module = sys.modules[GuestbookEntry.__module__]
    imported = {name.split(".")[0] for name in dir(module)}

    assert "fastapi" not in imported and "starlette" not in imported


def test_the_bounds_are_positive_and_ordered() -> None:
    """A guard against the constants being edited to something that cannot hold:
    a zero maximum makes every entry refused and every test about refusals pass."""
    assert AUTHOR_MAX_LENGTH > 0
    assert MESSAGE_MAX_LENGTH > 0


def test_a_row_can_be_built_without_touching_a_database() -> None:
    """The instance is a plain object until a session claims it -- which is what
    lets a service build a graph before deciding to write it."""
    written = datetime.datetime(2026, 8, 31, 9, 0, tzinfo=datetime.UTC)

    entry = GuestbookEntry(
        author="Anna", message="anything", created_at=written, updated_at=written
    )

    assert entry.author == "Anna"
    assert entry.created_at == entry.updated_at

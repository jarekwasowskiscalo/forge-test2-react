"""The data invariants, swept over the schema rather than asserted about one table.

`contracts/invariants/guestbook.md` states `D-01`..`D-03`. Until this module
existed the document admitted, in its own words, that they were held "by the data
model and by a decision about identifiers, rather than by a test that names them"
-- and a document that concedes a gap is still a document with a gap.

**Why a sweep and not a property-based test.** `D-01` and `D-02` are statements
about the SHAPE of the schema, not about values, so a generator has nothing to
draw from: it would pass on every run, say nothing, and look like the strongest
test in the suite -- worse than no test, because it stops anyone from checking.
`D-03` has a value half as well, and that half lives in
`tests/unit/test_data_invariant_properties.py` with a generator behind it. The
rule is written down in `spec/design/testing.md`.

**Two of these were vacuously true while the guest book was the only table, and
that was said out loud**, the way `spec/design/testing.md` says it about the rule
an index holds: the guest book was one table, so nothing could mirror it and
nothing could copy from it; `todo_tasks` made them real. The value of a sweep is
the NEXT table, not this one -- which is exactly why each test here
carries a known positive built out of a synthetic `MetaData`. A detector that has
stopped detecting passes everything, and it does so most quietly on the day the
rule starts being broken.
"""

import re
from typing import Final

import sqlalchemy as sa

from app.db.base import Base
from tests._repo import REPO_ROOT

#: Names that say "this table is a second home for rows that live somewhere else".
#: The antipattern `D-01` names is the "archive sheet": a record moved to another
#: set once it closes, after which "what happened to it" needs two sources stitched
#: together and every read has to remember both.
_ARCHIVE_SHAPED: Final = re.compile(
    r"(?:^|_)(archive|history|old|backup|copy)(?:$|_)", re.IGNORECASE
)

#: Columns every table is expected to carry independently. Two tables both having
#: `created_at` is not one copying the other.
_UNIVERSAL: Final[frozenset[str]] = frozenset({"id", "created_at", "updated_at"})


def _archive_shaped(metadata: sa.MetaData) -> list[str]:
    return sorted(name for name in metadata.tables if _ARCHIVE_SHAPED.search(name))


def _unreferenced_duplicates(metadata: sa.MetaData) -> list[str]:
    """Columns of the same name and type on two tables with no key between them."""
    linked: set[frozenset[str]] = {
        frozenset({table.name, key.column.table.name})
        for table in metadata.tables.values()
        for column in table.columns
        for key in column.foreign_keys
    }
    findings: list[str] = []
    tables = sorted(metadata.tables.values(), key=lambda table: table.name)
    for index, table in enumerate(tables):
        for other in tables[index + 1 :]:
            if frozenset({table.name, other.name}) in linked:
                continue
            for column in table.columns:
                if column.name in _UNIVERSAL or column.name not in other.columns:
                    continue
                if repr(column.type) == repr(other.columns[column.name].type):
                    findings.append(f"{table.name}.{column.name} == {other.name}.{column.name}")
    return findings


def _non_uuid_primary_keys(metadata: sa.MetaData) -> list[str]:
    findings: list[str] = []
    for table in metadata.tables.values():
        for column in table.primary_key.columns:
            if not isinstance(column.type, sa.Uuid):
                findings.append(f"{table.name}.{column.name} is {column.type!r}, not Uuid")
            elif column.default is None:
                findings.append(
                    f"{table.name}.{column.name} has no application-side default, so the "
                    "identifier does not exist until the database says so"
                )
    return findings


# --- D-01 ------------------------------------------------------------------- #


def test_no_table_is_shaped_like_an_archive() -> None:
    """`D-01` -- an entity has one row from creation to end, never a copy elsewhere.

    Vacuously true while the guest book was the only table: this sweep is written
    for the table somebody adds next, not for the one that is here.
    """
    assert _archive_shaped(Base.metadata) == []


def test_the_archive_sweep_detects_one() -> None:
    metadata = sa.MetaData()
    sa.Table("entries", metadata, sa.Column("id", sa.Uuid, primary_key=True))
    sa.Table("entries_archive", metadata, sa.Column("id", sa.Uuid, primary_key=True))
    assert _archive_shaped(metadata) == ["entries_archive"]


# --- D-02 ------------------------------------------------------------------- #


def test_no_column_is_a_copy_of_another_tables_column() -> None:
    """`D-02` -- a fact owned by another entity is pointed at, never rewritten.

    A deliberate historical snapshot is the named exception, and it has to say so
    in `spec/design/data-model.md`. Nothing claims one today, so the sweep is
    absolute; the day something does, this test grows the lookup rather than the
    exception growing silently.
    """
    assert "snapshot" not in (REPO_ROOT / "spec/design/data-model.md").read_text(
        encoding="utf-8"
    ), "a snapshot is now declared -- teach this sweep to read the declaration"
    assert _unreferenced_duplicates(Base.metadata) == []


def test_the_copied_column_sweep_detects_one() -> None:
    metadata = sa.MetaData()
    sa.Table(
        "entries",
        metadata,
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("signature", sa.String(80)),
    )
    sa.Table(
        "reports",
        metadata,
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("signature", sa.String(80)),
    )
    assert _unreferenced_duplicates(metadata) == ["entries.signature == reports.signature"]


def test_a_key_between_the_tables_makes_the_shared_column_a_relation() -> None:
    """The whole point of `D-02`: pointing at the fact is the sanctioned form."""
    metadata = sa.MetaData()
    sa.Table(
        "entries",
        metadata,
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("signature", sa.String(80)),
    )
    sa.Table(
        "reports",
        metadata,
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("entry_id", sa.Uuid, sa.ForeignKey("entries.id")),
        sa.Column("signature", sa.String(80)),
    )
    assert _unreferenced_duplicates(metadata) == []


# --- D-03 ------------------------------------------------------------------- #


def test_every_primary_key_is_an_application_generated_uuid() -> None:
    """`D-03` -- and this is the half that speaks about EVERY future table.

    `tests/unit/test_guestbook_entry_model.py` proves it of the one entity that
    exists; this proves it of the schema, so a table added with a sequence fails
    here without anybody remembering to write a test for it.
    """
    assert _non_uuid_primary_keys(Base.metadata) == []


def test_the_primary_key_sweep_detects_a_sequence() -> None:
    metadata = sa.MetaData()
    sa.Table("entries", metadata, sa.Column("id", sa.Integer, primary_key=True))
    assert _non_uuid_primary_keys(metadata) == ["entries.id is Integer(), not Uuid"]


def test_the_primary_key_sweep_detects_a_database_side_identifier() -> None:
    """A UUID the database generates still fails: the id has to exist before the insert."""
    metadata = sa.MetaData()
    sa.Table("entries", metadata, sa.Column("id", sa.Uuid, primary_key=True))
    assert _non_uuid_primary_keys(metadata) == [
        "entries.id has no application-side default, so the identifier does not exist "
        "until the database says so"
    ]

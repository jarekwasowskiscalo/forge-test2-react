"""Integration tests for the Alembic migration mechanism itself.

Each test runs against its own fresh, isolated database -- a new logical
database inside the shared testcontainers Postgres instance -- so a test that
upgrades, downgrades and upgrades again cannot leave the next one standing
somewhere unexpected.

The schema this file asserts is compared on **equality**, never containment: a
column added to `guestbook_entries` without a line in
`spec/design/data-model.md` is exactly the drift this file exists to catch, and
containment would wave it through.
"""

import datetime

import sqlalchemy as sa
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy.pool import NullPool

import tests._database as database
from alembic import command
from app.db.alembic_url import for_alembic_config
from app.db.base import Base

#: The one table this schema has, and the columns `spec/design/data-model.md`
#: gives it.
GUESTBOOK_COLUMNS = {"id", "author", "message", "created_at", "updated_at"}

#: The index behind the ordering the list contract publishes (`BR-04`). Named
#: here so a migration that drops it fails with a sentence about the rule rather
#: than as a slow query nobody measures.
ORDERING_INDEX = "ix_guestbook_entries_created_at_id"


def _config_for(url: str) -> Config:
    cfg = Config(str(database.REPO_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(database.REPO_ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", for_alembic_config(url))
    return cfg


def _upgraded() -> tuple[Config, sa.Engine]:
    url = database.create_database()
    cfg = _config_for(url)
    command.upgrade(cfg, "head")
    return cfg, sa.create_engine(url, poolclass=NullPool)


def test_the_models_and_the_migrations_describe_the_same_schema() -> None:
    """`alembic/versions/` IS the schema's contract, so nothing may outrank it.

    `contracts/README.md` states plainly that there is no `contracts/` directory
    for the database and that this is a decision rather than a gap: the set of
    revisions is the contract. A contract nothing compares against the code is a
    contract in name only -- and until this test, nothing did. The constants at
    the top of this file are a HAND-MAINTAINED mirror of
    `spec/design/data-model.md`; they catch a column the specification never
    named, and they cannot catch a model and a migration disagreeing, because
    both would have to be wrong in the same way for the mirror to notice.

    This asks the question directly. Upgrade an empty database to head, then ask
    Alembic what it would autogenerate against `Base.metadata`. The answer has to
    be **nothing**: any operation in that list is a change somebody made to a
    model and never wrote a revision for -- new code meeting an old schema, which
    fails on every request rather than at deploy time.

    Deterministic and with no false positive by construction, which is why it
    blocks rather than warns: it compares two artefacts in this repository and
    asks no opinion. The comparison is deliberately narrow -- names, columns,
    types and constraints -- because that is what Alembic can answer without
    guessing, and a drift detector that guesses is one people learn to override.
    """
    _, engine = _upgraded()
    try:
        with engine.connect() as connection:
            context = MigrationContext.configure(
                connection,
                opts={
                    # Alembic reports its own bookkeeping table as an extra table
                    # it would drop, because `Base.metadata` rightly knows nothing
                    # about it. Excluding it here keeps the verdict about the
                    # application's schema.
                    "include_name": lambda name, type_, parent: (
                        not (type_ == "table" and name == "alembic_version")
                    ),
                    "compare_type": True,
                    "compare_server_default": True,
                },
            )
            difference = compare_metadata(context, Base.metadata)
    finally:
        engine.dispose()

    assert not difference, (
        "the models and the applied migrations describe different schemas. Alembic "
        f"would autogenerate {len(difference)} operation(s) to reconcile them: "
        f'{difference}. Write the revision (`./scripts/db.sh revision "..."` produces a '
        "FIRST DRAFT, not an answer) rather than adjusting this test -- new code "
        "against an old schema fails on every request."
    )


def test_upgrade_head_creates_the_guestbook_table_with_exactly_these_columns() -> None:
    _, engine = _upgraded()

    inspector = sa.inspect(engine)
    columns = {col["name"]: col for col in inspector.get_columns("guestbook_entries")}

    assert set(columns) == GUESTBOOK_COLUMNS
    assert set(inspector.get_pk_constraint("guestbook_entries")["constrained_columns"]) == {"id"}
    for name in ("author", "message", "created_at", "updated_at"):
        assert columns[name]["nullable"] is False, f"{name} became nullable"


def test_the_ordering_the_contract_publishes_has_an_index_behind_it() -> None:
    """`BR-04` is read on every load of the only screen. An ordering with no index
    is a full sort of the table, which is invisible until the table is large."""
    _, engine = _upgraded()

    indexes = {
        index["name"]: list(index["column_names"])
        for index in sa.inspect(engine).get_indexes("guestbook_entries")
    }

    assert ORDERING_INDEX in indexes
    # `id` is in the index for the same reason it is in the ORDER BY: it is what
    # makes the order total.
    assert indexes[ORDERING_INDEX] == ["created_at", "id"]


def test_both_timestamps_are_stored_with_a_time_zone() -> None:
    """ "Which entry is newer" has to settle across an offset change.

    A naive column would make the answer depend on the server's local time, and
    the failure mode is silent: the ordering is right until the clocks go back.
    """
    _, engine = _upgraded()

    columns = {col["name"]: col for col in sa.inspect(engine).get_columns("guestbook_entries")}

    for name in ("created_at", "updated_at"):
        assert isinstance(columns[name]["type"], sa.DateTime)
        assert columns[name]["type"].timezone is True, f"{name} lost its time zone"


def test_no_other_temporal_column_slipped_in_naive() -> None:
    """The set is compared, not scanned: a new aware or naive column is a decision
    this test has to be told about rather than a failure discovered later."""
    _, engine = _upgraded()

    temporal = {
        col["name"]
        for col in sa.inspect(engine).get_columns("guestbook_entries")
        if isinstance(col["type"], sa.DateTime | sa.Date)
    }

    assert temporal == {"created_at", "updated_at"}


def test_current_reports_applied_revision() -> None:
    _, engine = _upgraded()

    with engine.connect() as conn:
        applied = conn.execute(sa.text("SELECT version_num FROM alembic_version")).scalar()

    assert applied is not None


def test_upgrade_head_twice_is_idempotent() -> None:
    cfg, engine = _upgraded()

    with engine.connect() as conn:
        first = conn.execute(sa.text("SELECT version_num FROM alembic_version")).scalar()
    command.upgrade(cfg, "head")
    with engine.connect() as conn:
        second = conn.execute(sa.text("SELECT version_num FROM alembic_version")).scalar()

    assert first == second


def test_downgrade_removes_the_table_and_its_index() -> None:
    """A downgrade that leaves the index behind makes the next upgrade fail on a
    name that already exists -- and it fails on the operator's machine, mid-release,
    not here."""
    cfg, engine = _upgraded()

    command.downgrade(cfg, "base")

    inspector = sa.inspect(engine)
    assert "guestbook_entries" not in inspector.get_table_names()


def test_the_schema_survives_a_full_down_and_up_cycle() -> None:
    """Not the same claim as the two above: this is the one that catches a
    `downgrade` whose drops are in the wrong order, which only shows on the way
    back up."""
    cfg, engine = _upgraded()

    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")

    inspector = sa.inspect(engine)
    columns = {col["name"] for col in inspector.get_columns("guestbook_entries")}
    assert columns == GUESTBOOK_COLUMNS


def test_a_row_written_through_the_schema_keeps_its_offset() -> None:
    """The column type is one claim; that a value survives a round trip with its
    offset intact is another, and only the second one is what the ordering rests on."""
    _, engine = _upgraded()
    written = datetime.datetime(2026, 8, 30, 20, 0, tzinfo=datetime.UTC)

    with engine.begin() as conn:
        conn.execute(
            sa.text(
                "INSERT INTO guestbook_entries (id, author, message, created_at, updated_at) "
                "VALUES (:id, :author, :message, :at, :at)"
            ),
            {
                "id": "0d0d5c3a-6d9c-4a1e-9a4a-2f7f6f0e5b11",
                "author": "Anna",
                "message": "anything",
                "at": written,
            },
        )
    with engine.connect() as conn:
        read = conn.execute(sa.text("SELECT created_at FROM guestbook_entries")).scalar_one()

    assert read.tzinfo is not None
    assert read == written

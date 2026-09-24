"""create todo tasks table

The to-do list's one table (`CR-2609-823a/R-1`, `R-3`, `R-4`): a text, a state, a
moment of adding and the identifier, and nothing else -- the ordered operations of
`spec/design/data-model.md` § The revision that creates `todo_tasks`, exactly.

The text column is `String(200)` written as the literal, never as
`TODO_TASK_TEXT_MAX_LENGTH`: a released revision must not change when the constant
later moves. Moving the bound is a new revision that widens the column, and the
model-against-revision comparison in `tests/integration/test_migrations.py` turns
red on the day the constant moves without one.

No column carries a server default. The model declares none -- `done` is written
`false` by the application on every insert (`BR-08`) and `created_at` by the
service's clock -- and the comparison above compares server defaults too, so a
default here would be drift the next autogeneration drafts away.

The index is a plain build, not `CONCURRENTLY`: the table is created one step
earlier in this same revision and holds no row, so there is no write for the build
to block (`tests/fitness/test_migration_safety.py` draws the line on the table's
age). For the same reason there is no `lock_timeout` and no backfill -- this
revision alters no table it did not create, and no column becomes NOT NULL over
rows that already exist. No data arrives with the schema: example tasks reach a
new environment through the API (`scripts/seed.sh`).

Compatibility mode: backward compatible. Code released before this revision never
names `todo_tasks`, so it runs unchanged over the new schema, in either deploy
order (`spec/design/data-model.md` § Compatibility mode).

Revision ID: 5c58af1f8e8a
Revises: a1b2c3d4e5f6
Create Date: 2026-09-24 21:02:31.996517

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5c58af1f8e8a"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "todo_tasks",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("text", sa.String(length=200), nullable=False),
        sa.Column("done", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    # The list is read whole, newest first, on every opening of the to-do screen
    # (`BR-11`): `ORDER BY created_at DESC, id DESC`. Both keys run one direction,
    # so one backward scan of this index answers it; `id` makes the order total
    # for two tasks stored in the same instant.
    op.create_index(
        "ix_todo_tasks_created_at_id",
        "todo_tasks",
        ["created_at", "id"],
    )


def downgrade() -> None:
    """Downgrade schema.

    The index before the table -- the exact reverse of `upgrade()`. Dropping the
    table destroys every task: the inverse of creating it, and a step no release
    runs, because a rollback moves the alias and leaves the schema where it is
    (`./scripts/deploy.sh --help`).
    """
    op.drop_index("ix_todo_tasks_created_at_id", table_name="todo_tasks")
    op.drop_table("todo_tasks")

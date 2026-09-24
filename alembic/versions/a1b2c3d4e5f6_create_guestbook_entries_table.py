"""create guestbook entries table

The template's only revision, and the head every later one builds on.

`Uuid` rather than a native `UUID` column type: SQLAlchemy renders it as
Postgres' `uuid`, and the generic spelling keeps the revision readable next to
the model, which declares the same type. `DateTime(timezone=True)` is a real
`timestamptz` -- the ordering this table exists to serve has to settle across an
offset change, so the zone is part of the value and not of the formatting.

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-08-30 22:40:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "guestbook_entries",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("author", sa.String(length=80), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    # The list is read newest-first on every load of the only screen, so the
    # ordering it uses gets an index rather than a sort of the whole table.
    # `id` is in the index for the same reason it is in the ORDER BY: it is what
    # makes the order total.
    op.create_index(
        "ix_guestbook_entries_created_at_id",
        "guestbook_entries",
        ["created_at", "id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_guestbook_entries_created_at_id", table_name="guestbook_entries")
    op.drop_table("guestbook_entries")

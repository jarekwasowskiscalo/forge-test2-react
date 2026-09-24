"""SQLAlchemy declarative model for the `GuestbookEntry` domain concept.

Framework-agnostic mapping (no fastapi/starlette imports) so this module stays
usable by both the application runtime and Alembic migrations. See
spec/design/data-model.md (`guestbook_entries`) for the specification this
mirrors.

`created_at` and `updated_at` are the only columns in this schema carrying a
time zone, and they carry one because "which entry is newer" has to settle
across an offset change -- the list is ordered by `created_at` and the ordering
must not depend on the server's local time. `BR-02` makes them two columns
rather than one: an edit moves `updated_at` and must never move `created_at`,
so "when was this written" survives every later correction.
"""

import datetime
import uuid

from sqlalchemy import DateTime, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

#: The longest an author's name may be. Stated here rather than only in the
#: Pydantic schema because the column enforces it too: a value that reaches the
#: database by any other route -- a migration backfill, a fixture, a script --
#: is bound by the same number, and the two cannot drift because there is one.
AUTHOR_MAX_LENGTH = 80

#: The longest a message may be. `Text` rather than `String(1000)` on purpose:
#: the ceiling is a product rule that will move, and moving it should be a
#: schema edit in one file, not a migration that rewrites a column type.
MESSAGE_MAX_LENGTH = 1000


class GuestbookEntry(Base):
    __tablename__ = "guestbook_entries"
    #: The ordering index is declared here AS WELL AS in the revision that
    #: creates it, and the duplication is the point: `./scripts/db.sh revision`
    #: autogenerates against `Base.metadata`, so an index the model does not
    #: know about is, to Alembic, an index to drop in the next revision anybody
    #: writes. `spec/design/data-model.md` § Indexes and uniqueness names the same rule.
    __table_args__ = (Index("ix_guestbook_entries_created_at_id", "created_at", "id"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    author: Mapped[str] = mapped_column(String(AUTHOR_MAX_LENGTH), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    #: Set on every edit, and equal to `created_at` on a freshly created entry.
    #: Nullable would make "never edited" and "edited at an unknown time" the
    #: same value, and the list has to be able to say "amended" without
    #: guessing.
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)

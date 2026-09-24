"""SQLAlchemy declarative model for the to-do list's `TodoTask`.

Framework-agnostic mapping (no fastapi/starlette imports), so this module stays
usable by the application, by a script and by Alembic's autogeneration alike. See
`spec/design/data-model.md` § `todo_tasks` for the table this mirrors and
`spec/contexts/todo_list.md` for the rules behind it.

A task is a text, a state and a moment of adding, and the table holds those three
and the identifier -- no `updated_at`, no position, no author. Each absence is a
decision the data model records rather than a gap:

- **`done` is a boolean with the model's default and no server's.** One state with
  two values and no third (`BR-08`, `BR-09`); a nullable column would be a third,
  "we do not know", that no rule describes. The default lives here and not in the
  database because the revision declares no server default, and the
  model-against-revision comparison compares the two.
- **`created_at` carries its zone and has no `onupdate`.** The list is ordered by
  it (`BR-11`), so "which task is newer" has to settle across an offset change; and
  it is set once, by the service's clock on insert, so an `onupdate` would move a
  task every time somebody ticked or corrected it (`BR-08`, `BR-10`).
- **`text` is `String(TODO_TASK_TEXT_MAX_LENGTH)`, not `Text`**, although the
  guestbook's message is `Text`: the column is the last layer's refusal of a value
  that arrived by a route that skipped the rule -- a fixture, a script, a service
  that measured before it normalized, where two hundred decomposed letters are four
  hundred code points. A Postgres `varchar` counts code points, which is the unit
  the rule counts in, so the column and the service measure the same thing.

The rest of the text rule -- empty, one line -- is deliberately NOT a `CHECK`
constraint. It would be a second hand-written copy of the thirty-code-point trim set
and the seven line breaks, in SQL, beside the one in `app/platform/schemas/text.py`,
and two copies of a set agree only until one of them moves. The length is different
in kind: one number, read from one constant, and watched by the model-against-revision
comparison (`spec/design/data-model.md` § `todo_tasks`, "Why `String(200)`").
"""

import datetime
import uuid
from typing import Final

from sqlalchemy import Boolean, DateTime, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

#: The longest a task's text may be, in code points after NFC and the trim (`BR-06`).
#: Its one home: the column is declared from it, the service's judgement of a text
#: imports it, and the request shapes do not -- a bound in a shape would answer with
#: FastAPI's list and no code (`spec/design/api.md` § Shapes, `TodoTaskCreate`). The
#: browser's copy is `frontend/src/contexts/todo_list/lib/todoTask.ts`, legal only
#: while `tests/fitness/test_length_constants.py` holds the two literals equal, so it
#: stays a bare integer literal. Qualified by the context's name because the
#: guestbook's search phrase is also bounded at 200 (`QUERY_MAX_LENGTH`): two rules
#: sharing a number, and moving one moves nothing on the other side.
TODO_TASK_TEXT_MAX_LENGTH = 200

#: The code points a task may not hold inside its text (`BR-07`, the seven of
#: `CR-2609-823a/R-2` clause 6, confirmed as `A-1`). Written as NUMBERS, the way the
#: shared kernel writes its trim set, because each language's own idea of a line
#: break differs from the other's -- Python's `str.splitlines` also breaks on the four
#: C0 separators, and JavaScript's line terminators leave out U+000B, U+000C and
#: U+0085 -- and a written set is the one thing two runtimes can both read. Every
#: one of the seven is also in the trim set, so one at either end is
#: removed before the rule looks, and only a line break left inside is refused. The
#: browser's copy is held to this one by `tests/fitness/test_length_constants.py`.
LINE_BREAKS: Final[tuple[int, ...]] = (
    0x000A,  # line feed
    0x000B,  # line tabulation
    0x000C,  # form feed
    0x000D,  # carriage return
    0x0085,  # next line
    0x2028,  # line separator
    0x2029,  # paragraph separator
)


class TodoTask(Base):
    __tablename__ = "todo_tasks"
    #: The ordering index, declared here AS WELL AS in the revision that creates it:
    #: `./scripts/db.sh revision` autogenerates against `Base.metadata`, so an index the
    #: model does not know about is, to Alembic, an index to drop in the next revision.
    #: `created_at` then `id`, both read backwards by `ORDER BY created_at DESC, id
    #: DESC` -- `id` is what makes the order total for two tasks stored in the same
    #: instant (`BR-11`). Not unique: the same text twice is two tasks (`BR-12`).
    __table_args__ = (Index("ix_todo_tasks_created_at_id", "created_at", "id"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    text: Mapped[str] = mapped_column(String(TODO_TASK_TEXT_MAX_LENGTH), nullable=False)
    done: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)

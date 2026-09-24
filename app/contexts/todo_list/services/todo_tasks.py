"""The to-do list's rules, its session and its transaction boundary.

Framework-agnostic seam for the to-do list: owns the SQLAlchemy session, raises
domain exceptions, and never names an HTTP status code -- the router translates.
Must not import anything from `fastapi`/`starlette`, so every rule here stays
callable from a script or a future scheduled job (`spec/design/conventions.md`
§ Layers). The rules are `spec/contexts/todo_list.md`'s; which layer holds each is
`spec/design/architecture.md` § The to-do list -- where each rule lives.

**A task's text is judged here, once, for the addition and the correction alike**
(`BR-06`, `BR-07`, `BR-10`): normalize, then empty, then one line, then measure, in
that order and before any write. One judgement serving both writes is what makes "a
correction is held to `BR-06` and `BR-07` exactly as an addition is" true by
construction rather than by care, and the order is what makes a text that is both too
long and on two lines refused for the line break -- the reason a person cannot see
for themselves. Each verdict is its own exception class, because each is its own code
on the wire and the router matches on the class.

**Every write is one statement, and no row is read before it** (`spec/design/data-model.md`
§ Two writers on one task). A correction names `text` alone, a marking names `done`
alone with the state the person chose, a deletion names the id. That is what holds
`BR-10` and `BR-13` under two writers, and nothing a check made in Python could:

- a statement that waits on another writer's row lock re-reads the row at `READ
  COMMITTED` before it applies its own `SET`, so the column it does not name keeps
  what the other writer put there -- a correction never undoes a marking, and of two
  changes to the same column the one applied later wins;
- a marking writes the chosen value, never `NOT done` and never a value computed from
  a state read earlier, so two people who both chose done end with done;
- a statement that meets no row changes nothing, and no path here writes an upsert or
  calls the ORM's `merge()`, so a change behind a deletion creates nothing and is
  refused as not found.

What defeats that, and nothing in the schema can refuse, is named so nobody
"simplifies" into it: loading the task, assigning, and flushing (a deletion between
the load and the flush surfaces as a stale-data error rather than "no longer
exists"); writing back both columns with the values read; a flip; or raising the
isolation to `REPEATABLE READ`, where the waiting statement fails with a
serialization error instead of re-reading. `tests/integration/test_todo_tasks_concurrency.py`
interleaves two writers on one row to tell these apart, which no sequential test can.

The exception messages carry identifiers and never the text somebody typed: an
exception's message reaches logs and assertion output, and a task's text is content
(constitution, article XI).
"""

import datetime
import uuid
from typing import Final

from sqlalchemy import delete, insert, select, update

from app.contexts.todo_list.models.todo_task import (
    LINE_BREAKS,
    TODO_TASK_TEXT_MAX_LENGTH,
    TodoTask,
)
from app.contexts.todo_list.schemas.todo_tasks import TodoTaskList, TodoTaskRead
from app.db.session import SessionLocal
from app.platform.schemas.text import length, normalize

#: `LINE_BREAKS` as characters, built once. The model keeps the code points as numbers,
#: the shape its browser copy is compared in; this is only their other spelling.
_LINE_BREAK_CHARACTERS: Final[frozenset[str]] = frozenset(chr(code) for code in LINE_BREAKS)

#: What an UPDATE or DELETE does to objects already in the session: nothing. Each
#: operation here opens a session of its own and loads no task into it, so there is
#: nothing to synchronize -- and the other strategies are exactly what this module
#: exists not to do: `"evaluate"` would apply the change to loaded objects in Python,
#: and `"fetch"` may SELECT the matched rows before the write where RETURNING is not
#: available. `False` keeps each write the single statement the data model describes.
_NO_SESSION_SYNC: Final = {"synchronize_session": False}


class TodoTaskNotFoundError(Exception):
    """No task has this identifier: it never existed, or it was deleted (`BR-13`).

    Raised when a correction, a marking or a deletion meets no row -- including a
    second deletion of the same task, which is never reported as a deletion that
    happened. Carries the identifier, which the refusal names.
    """

    def __init__(self, todo_task_id: uuid.UUID) -> None:
        super().__init__(str(todo_task_id))
        self.todo_task_id = todo_task_id


class TodoTaskTextEmptyError(Exception):
    """A task's text is empty once normalized and trimmed (`BR-06`)."""


class TodoTaskTextMultilineError(Exception):
    """A task's text, once trimmed, still holds one of the seven line breaks (`BR-07`).

    Also raised for a text that is too long as well: the one-line reason is the one a
    person is given, because a pasted line break is often invisible in a one-line field
    and a text's length is not.
    """


class TodoTaskTextTooLongError(Exception):
    """A one-line text longer than `TODO_TASK_TEXT_MAX_LENGTH` code points once
    normalized and trimmed (`BR-06`)."""


def _now() -> datetime.datetime:
    """The one clock this module reads, and it is read on insert only.

    One function rather than a `datetime.now` at the call site, so a test that needs
    to control time has one seam to take -- and so it is plain from a search that
    nothing but the addition ever stamps `created_at` (`BR-08`).
    """
    return datetime.datetime.now(datetime.UTC)


def _read(row: TodoTask) -> TodoTaskRead:
    return TodoTaskRead(id=row.id, text=row.text, done=row.done, created_at=row.created_at)


def judge_todo_task_text(text: str) -> str:
    """The text as it will be stored, or the one reason it is refused.

    `BR-06` and `BR-07`, in the order `spec/design/architecture.md` § The layer per
    rule gives: normalized and trimmed by the shared kernel first
    (`app/platform/schemas/text.py`), then empty, then a line break left inside, then
    longer than the bound in code points. An empty text cannot hold a line break --
    all seven are in the trim set, so none survives at an end -- and a text with a
    line break inside is never measured, so exactly one of the three is ever raised.

    Whitespace inside the text is the person's own and is kept as typed: two spaces,
    a tab between two words. Only the ends are trimmed.

    Raises:
        TodoTaskTextEmptyError: nothing is left once the text is trimmed.
        TodoTaskTextMultilineError: a line break is left inside it.
        TodoTaskTextTooLongError: it is one line and over the bound.
    """
    kept = normalize(text)
    if not kept:
        raise TodoTaskTextEmptyError
    if _LINE_BREAK_CHARACTERS.intersection(kept):
        raise TodoTaskTextMultilineError
    if length(kept) > TODO_TASK_TEXT_MAX_LENGTH:
        raise TodoTaskTextTooLongError
    return kept


def list_todo_tasks() -> TodoTaskList:
    """Every task, done and not done alike, newest first, in one read (`BR-11`).

    `created_at` then `id`, both descending, so the order is total: two tasks stored in
    the same instant still come back in one order for every reader. Both keys run in
    one direction, which is what lets `ix_todo_tasks_created_at_id` answer the query
    with one backward scan. No pieces and no ceiling -- the list is read whole.

    **`total` is `len(items)`, and here that is the population rather than a guess
    about it.** The guestbook counts in the database because its read is a page, and a
    page cannot imply its population. This read is the whole table in one statement,
    so its length IS the count; a second `COUNT(*)` statement would see its own
    snapshot at `READ COMMITTED` and could disagree with the rows beside it when
    somebody adds a task between the two.
    """
    statement = select(TodoTask).order_by(TodoTask.created_at.desc(), TodoTask.id.desc())
    with SessionLocal() as session:
        items = [_read(row) for row in session.scalars(statement)]
    return TodoTaskList(items=items, total=len(items))


def add_todo_task(*, text: str) -> TodoTaskRead:
    """Store a new task, not done, stamped with this moment (`BR-06`...`BR-08`, `BR-12`).

    `done` is written `False` and `created_at` from this module's clock on every
    insert, whatever a caller might have wanted: nothing a request carries reaches
    either column, which is `BR-08` held by the one place that writes. The same text
    as another task is simply another task -- there is no uniqueness check to make
    (`BR-12`), and none in the schema either.

    One `INSERT ... RETURNING`, so what comes back is the row as stored.

    Raises:
        TodoTaskTextEmptyError, TodoTaskTextMultilineError, TodoTaskTextTooLongError:
            the text is refused, and nothing is written.
    """
    kept = judge_todo_task_text(text)
    statement = (
        insert(TodoTask).values(text=kept, done=False, created_at=_now()).returning(TodoTask)
    )
    with SessionLocal() as session:
        task = _read(session.scalars(statement).one())
        session.commit()
    return task


def change_todo_task(
    todo_task_id: uuid.UUID, *, text: str | None = None, done: bool | None = None
) -> TodoTaskRead:
    """Correct a task's text, mark it, or both, in one statement naming only those columns.

    What `PATCH` does, whichever of the two fields it carried (`BR-09`, `BR-10`). The
    text, when there is one, is judged first, so a refused text writes nothing -- the
    `done` beside it included -- and is refused for what it is before anybody asks
    whether the task exists (`spec/design/api.md` § The to-do list's refusals, the
    lookup last). Then one `UPDATE ... WHERE id = :id RETURNING`, whose `SET` names the
    columns that were given and no other; `RETURNING` hands back the row as the
    statement left it, the other writer's change included.

    A call naming neither is a caller's mistake rather than a refusal a person meets:
    "no change given" is decided beside the endpoint, before this is called (`Q-21`,
    item 3), so here it is a `ValueError`.

    Raises:
        TodoTaskTextEmptyError, TodoTaskTextMultilineError, TodoTaskTextTooLongError:
            the text is refused, and nothing is written.
        TodoTaskNotFoundError: no task has `todo_task_id`; nothing is written and
            nothing is created.
    """
    values: dict[str, str | bool] = {}
    if text is not None:
        values["text"] = judge_todo_task_text(text)
    if done is not None:
        values["done"] = done
    if not values:
        raise ValueError("a change to a task names its text, its state, or both")
    statement = (
        update(TodoTask)
        .where(TodoTask.id == todo_task_id)
        .values(**values)
        .returning(TodoTask)
        .execution_options(**_NO_SESSION_SYNC)
    )
    with SessionLocal() as session:
        row = session.scalars(statement).one_or_none()
        if row is None:
            raise TodoTaskNotFoundError(todo_task_id)
        task = _read(row)
        session.commit()
    return task


def correct_todo_task(todo_task_id: uuid.UUID, *, text: str) -> TodoTaskRead:
    """Replace a task's text and nothing else: not its state, not its moment of adding.

    `BR-10`: a correction is held to `BR-06` and `BR-07` exactly as an addition is --
    it is the same judgement -- and names `text` alone, so a done task stays done.

    Raises:
        TodoTaskTextEmptyError, TodoTaskTextMultilineError, TodoTaskTextTooLongError:
            the text is refused, and the task keeps the text it had.
        TodoTaskNotFoundError: no task has `todo_task_id`.
    """
    return change_todo_task(todo_task_id, text=text)


def mark_todo_task(todo_task_id: uuid.UUID, *, done: bool) -> TodoTaskRead:
    """Record the state the person chose, whatever is stored (`BR-09`).

    Done over done stays done and not done over not done stays not done: the value
    written is the one chosen, never the opposite of the one stored. The text and the
    moment of adding are not named, so they are what they were.

    Raises:
        TodoTaskNotFoundError: no task has `todo_task_id`.
    """
    return change_todo_task(todo_task_id, done=done)


def delete_todo_task(todo_task_id: uuid.UUID) -> None:
    """Remove a task for good: the row stops existing, with no bin and no undo (`BR-13`).

    One `DELETE ... RETURNING id`; no row returned is the "no longer exists" answer, so
    a second deletion of the same task is refused rather than reported as done.

    Raises:
        TodoTaskNotFoundError: no task has `todo_task_id`.
    """
    statement = (
        delete(TodoTask)
        .where(TodoTask.id == todo_task_id)
        .returning(TodoTask.id)
        .execution_options(**_NO_SESSION_SYNC)
    )
    with SessionLocal() as session:
        if session.scalars(statement).one_or_none() is None:
            raise TodoTaskNotFoundError(todo_task_id)
        session.commit()

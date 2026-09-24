"""The to-do list service's rules, against a real database.

The claims that need storage to be true at all: a row that is written not done
whatever was asked, a moment of adding that no later change moves, an order the
database performs and settles totally, a text that reaches the column normalized,
and a row that stops existing and stays gone. What is provable without a database
-- the verdict on a text, the model's declarations -- is `tests/unit/`'s.

**What this module fixes for the implementation.** The service does not exist yet
(`CR-2609-823a`, T-15 writes it), so the names below are the ones it is to have,
in `app.contexts.todo_list.services.todo_tasks`:

- `add_todo_task(text=...)`, `list_todo_tasks()`, `correct_todo_task(id, text=...)`,
  `mark_todo_task(id, done=...)`, `delete_todo_task(id)` -- the add, read,
  correct, mark and delete of `spec/design/architecture.md` § The files; the first
  four return the task as stored (`id`, `text`, `done`, `created_at`), the read an
  envelope of `items` and `total`;
- `TodoTaskNotFoundError`, when a statement meets no row (`BR-13`);
- `TodoTaskTextEmptyError`, `TodoTaskTextMultilineError`, `TodoTaskTextTooLongError`
  -- one domain exception per verdict of the text's judgement, named after the
  three `todo_task_text_*` codes the router turns them into.

Each is imported inside the test that calls it, never at the top of the module: a
failed import there would un-collect every case in the file, and a declared red the
runner does not collect fails the gate (`spec/design/testing.md` § CR-2609-823a,
"Red first").

**The bound is read from the constant**, `TODO_TASK_TEXT_MAX_LENGTH` beside
`TodoTask`, never written here as a number: a test that writes the number keeps
proving it after the rule moves.

**What reached the column is read with SQL**, not through the service, so the
assertion and its subject are never the same code -- a service that returned what
it was given and stored something else would otherwise pass. Every test asks for
`fresh_database`, so the rows it counts are its own.
"""

import datetime as dt
import uuid
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker


def _column(session_factory: sessionmaker) -> list[tuple[Any, ...]]:
    """Every row of `todo_tasks` as `(id, text, done, created_at)`, in the list's order."""
    with session_factory() as session:
        rows = session.execute(
            sa.text(
                "SELECT id, text, done, created_at FROM todo_tasks "
                "ORDER BY created_at DESC, id DESC"
            )
        ).all()
    return [tuple(row) for row in rows]


def _row(session_factory: sessionmaker, todo_task_id: uuid.UUID) -> tuple[Any, ...] | None:
    """One row as `(text, done, created_at)`, or `None` when no row has that id."""
    with session_factory() as session:
        row = session.execute(
            sa.text("SELECT text, done, created_at FROM todo_tasks WHERE id = :id"),
            {"id": todo_task_id},
        ).first()
    return None if row is None else tuple(row)


# --------------------------------------------------------------------------- #
# Adding (`BR-08`, `BR-12`)
# --------------------------------------------------------------------------- #


@pytest.mark.req("CR-2609-823a/R-1")
def test_an_added_task_is_stored_not_done_with_its_moment_of_adding(
    fresh_database: sessionmaker,
) -> None:
    """Not done, and stamped by the service's own clock when it is stored.

    The moment is bracketed by two readings of the clock taken around the call, so
    it is the moment of THIS write -- not a default the column supplied, not a
    value the caller sent -- and it carries its zone, because "which task is newer"
    has to settle across an offset change.
    """
    from app.contexts.todo_list.services.todo_tasks import add_todo_task

    before = dt.datetime.now(dt.UTC)
    task = add_todo_task(text="Water the plants")
    after = dt.datetime.now(dt.UTC)

    assert isinstance(task.id, uuid.UUID), "the application issues the identifier"
    assert task.text == "Water the plants"
    assert task.done is False, "a new task is not done (BR-08)"
    assert task.created_at.tzinfo is not None, "the moment of adding lost its zone"
    assert before <= task.created_at <= after, (
        "the moment of adding is not the moment the service stored the task"
    )
    assert _row(fresh_database, task.id) == ("Water the plants", False, task.created_at)


@pytest.mark.req("CR-2609-823a/R-1")
def test_the_same_text_added_twice_is_two_tasks_marked_apart(
    fresh_database: sessionmaker,
) -> None:
    """`BR-12`: no uniqueness rule, so a repeated text is a second task -- with an
    identity of its own, which is what lets one of the two be marked alone."""
    from app.contexts.todo_list.services.todo_tasks import (
        add_todo_task,
        list_todo_tasks,
        mark_todo_task,
    )

    older = add_todo_task(text="Buy bread")
    newer = add_todo_task(text="Buy bread")
    assert older.id != newer.id, "the repeated text was merged into the task it repeats"

    mark_todo_task(newer.id, done=True)

    assert [(task.id, task.text, task.done) for task in list_todo_tasks().items] == [
        (newer.id, "Buy bread", True),
        (older.id, "Buy bread", False),
    ]
    assert _row(fresh_database, older.id) == ("Buy bread", False, older.created_at), (
        "marking one of two tasks with the same text marked the other"
    )


# --------------------------------------------------------------------------- #
# What reaches the column (`BR-06`, `BR-07`)
# --------------------------------------------------------------------------- #


@pytest.mark.req("CR-2609-823a/R-2")
def test_a_stored_text_is_normalized_one_line_and_within_the_bound_in_code_points(
    fresh_database: sessionmaker,
) -> None:
    """The task text's invariant, asserted where it has to be true: the row.

    One of the three witnesses `spec/design/testing.md` names for it -- the round
    trip only a real database can answer. The unit tests prove the judgement; this
    proves the value that reaches `varchar(200)`, which counts code points, is the
    judged one: a service that measured the normalized text and wrote the raw one
    would store four hundred code points of decomposed letters, or the spaces
    around a padded text, and pass every length assertion in the suite.

    A line break at the end is trimmed like a space (`BR-07` reads the text after
    the trim), so it reaches the column as a text on one line.
    """
    from app.contexts.todo_list.models.todo_task import TODO_TASK_TEXT_MAX_LENGTH
    from app.contexts.todo_list.services.todo_tasks import add_todo_task

    bound = TODO_TASK_TEXT_MAX_LENGTH
    sent_and_stored: tuple[tuple[str, str], ...] = (
        (("e" + chr(0x0301)) * bound, chr(0x00E9) * bound),
        ("  " + "a" * bound + "  ", "a" * bound),
        (chr(0x1F600) * bound, chr(0x1F600) * bound),
        ("Buy bread" + chr(0x000A), "Buy bread"),
    )

    for sent, stored in sent_and_stored:
        task = add_todo_task(text=sent)
        row = _row(fresh_database, task.id)

        assert row is not None, "the task was answered and never stored"
        assert row[0] == stored, "the column holds the text as sent rather than as judged"
        assert task.text == stored, "the answer and the column disagree"
        assert len(row[0]) <= bound, "the column holds more code points than the bound"
        assert chr(0x000A) not in row[0], "the column holds a text on two lines"

    emoji = chr(0x1F600) * bound
    assert len(emoji.encode("utf-16-le")) // 2 == 2 * bound, (
        "the emoji case no longer tells a code point from a UTF-16 unit"
    )


@pytest.mark.req("CR-2609-823a/R-2")
def test_inner_whitespace_is_stored_as_typed(fresh_database: sessionmaker) -> None:
    """The trim takes the ends. Two spaces and three inside a text, or a tab
    between two words, are the person's own, and a service that squeezed them
    would be rewriting what was typed (`R-2` clause 4)."""
    from app.contexts.todo_list.services.todo_tasks import add_todo_task

    for typed in ("Buy  two   lamps", "Buy" + chr(0x0009) + "bread"):
        task = add_todo_task(text=typed)

        row = _row(fresh_database, task.id)
        assert row is not None and row[0] == typed, (
            "whitespace inside the text did not survive to the column"
        )


# --------------------------------------------------------------------------- #
# One list, one order (`BR-11`)
# --------------------------------------------------------------------------- #


@pytest.mark.req("CR-2609-823a/R-3")
def test_the_list_comes_back_newest_first(fresh_database: sessionmaker) -> None:
    """The order is the database's, asserted through the service and again against
    the rows, so a service that sorted in Python would still be caught."""
    from app.contexts.todo_list.services.todo_tasks import add_todo_task, list_todo_tasks

    for text in ("First", "Second", "Third"):
        add_todo_task(text=text)

    listed = list_todo_tasks()

    assert [task.text for task in listed.items] == ["Third", "Second", "First"]
    assert [text for _, text, _, _ in _column(fresh_database)] == ["Third", "Second", "First"]
    assert listed.total == 3


@pytest.mark.req("CR-2609-823a/R-3")
def test_tasks_sharing_a_moment_of_adding_still_have_a_total_order(
    fresh_database: sessionmaker,
) -> None:
    """The tie-break on `id`, descending like the moment, is what makes the order total.

    The equal moment is WRITTEN rather than raced for: two quick adds share a
    microsecond only by luck, and a test that waits for luck fails on somebody
    else's machine. Without the tie-break, two readers of the same stored tasks
    could read two different lists.
    """
    from app.contexts.todo_list.services.todo_tasks import list_todo_tasks

    instant = dt.datetime(2026, 9, 24, 12, 0, tzinfo=dt.UTC)
    ids = sorted(uuid.uuid4() for _ in range(2))
    with fresh_database() as session:
        for todo_task_id, text in zip(ids, ("Left", "Right"), strict=True):
            session.execute(
                sa.text(
                    "INSERT INTO todo_tasks (id, text, done, created_at) "
                    "VALUES (:id, :text, false, :at)"
                ),
                {"id": todo_task_id, "text": text, "at": instant},
            )
        session.commit()

    first_read = [task.id for task in list_todo_tasks().items]
    second_read = [task.id for task in list_todo_tasks().items]

    # Descending on `id`, because the order is `created_at DESC, id DESC`.
    assert first_read == list(reversed(ids))
    assert second_read == first_read, "two reads of the same tasks disagree about their order"


@pytest.mark.req("CR-2609-823a/R-3")
def test_every_task_is_read_at_once_done_and_not_done(fresh_database: sessionmaker) -> None:
    """No pages, no filter: every stored task in one read.

    A hundred and one, "Task 001" to "Task 101", because a hundred is the largest
    piece the guestbook's read hands out -- a list read in pieces loses its oldest
    task here, silently. Every second task is marked done, so a read that dropped
    the done ones, or moved them, fails on the same list.
    """
    from app.contexts.todo_list.services.todo_tasks import (
        add_todo_task,
        list_todo_tasks,
        mark_todo_task,
    )

    texts = [f"Task {number:03d}" for number in range(1, 102)]
    added = [add_todo_task(text=text) for text in texts]
    for number, task in enumerate(added, start=1):
        if number % 2 == 0:
            mark_todo_task(task.id, done=True)

    listed = list_todo_tasks()

    assert len(listed.items) == len(texts), "the list came back in pieces"
    assert listed.total == len(texts)
    assert [task.text for task in listed.items] == list(reversed(texts))
    assert [task.done for task in listed.items] == [
        number % 2 == 0 for number in range(len(texts), 0, -1)
    ]


@pytest.mark.req("CR-2609-823a/R-3")
def test_marking_and_correcting_leave_a_task_in_its_place(fresh_database: sessionmaker) -> None:
    """Newest means the moment of adding, never the moment of the last change: a
    list reordered by its last change makes a task jump every time somebody ticks
    it (`BR-11`)."""
    from app.contexts.todo_list.services.todo_tasks import (
        add_todo_task,
        correct_todo_task,
        list_todo_tasks,
        mark_todo_task,
    )

    added = [add_todo_task(text=text) for text in ("First", "Second", "Third")]
    second = added[1]

    mark_todo_task(second.id, done=True)
    assert [task.text for task in list_todo_tasks().items] == ["Third", "Second", "First"], (
        "marking moved the task"
    )

    correct_todo_task(second.id, text="Second, corrected")
    listed = list_todo_tasks().items
    assert [task.text for task in listed] == ["Third", "Second, corrected", "First"], (
        "correcting moved the task"
    )
    assert listed[1].created_at == second.created_at, "a change re-stamped the moment of adding"
    assert [task.created_at for task in reversed(listed)] == [task.created_at for task in added]


# --------------------------------------------------------------------------- #
# Marking (`BR-09`)
# --------------------------------------------------------------------------- #


@pytest.mark.req("CR-2609-823a/R-4")
def test_marking_records_the_state_chosen_whatever_is_stored(fresh_database: sessionmaker) -> None:
    """All four pairs of stored and chosen state.

    Done over done and not done over not done are the pairs that matter: a marking
    that flips whatever is stored passes the other two exactly as the right one does,
    and on these two it undoes a choice two people both made.
    """
    from app.contexts.todo_list.services.todo_tasks import add_todo_task, mark_todo_task

    for stored in (False, True):
        for chosen in (False, True):
            task = add_todo_task(text="Buy bread")
            if stored:
                mark_todo_task(task.id, done=True)

            marked = mark_todo_task(task.id, done=chosen)

            row = _row(fresh_database, task.id)
            assert marked.done is chosen, (
                f"stored {stored}, chosen {chosen}: answered {marked.done}"
            )
            assert row is not None and row[1] is chosen, (
                f"stored {stored}, chosen {chosen}: the column holds {row}"
            )


@pytest.mark.req("CR-2609-823a/R-4")
def test_marking_leaves_the_text_and_the_moment_of_adding_alone(
    fresh_database: sessionmaker,
) -> None:
    """A marking names `done` and nothing else, so the text and the moment of adding
    are what they were -- both ways (`BR-09`, `BR-08`)."""
    from app.contexts.todo_list.services.todo_tasks import add_todo_task, mark_todo_task

    task = add_todo_task(text="Buy bread")

    done = mark_todo_task(task.id, done=True)
    assert (done.id, done.text, done.created_at) == (task.id, task.text, task.created_at)
    assert _row(fresh_database, task.id) == ("Buy bread", True, task.created_at)

    undone = mark_todo_task(task.id, done=False)
    assert (undone.id, undone.text, undone.created_at) == (task.id, task.text, task.created_at)
    assert _row(fresh_database, task.id) == ("Buy bread", False, task.created_at)


# --------------------------------------------------------------------------- #
# Correcting (`BR-10`)
# --------------------------------------------------------------------------- #


@pytest.mark.req("CR-2609-823a/R-6")
def test_a_correction_changes_the_text_and_nothing_else(fresh_database: sessionmaker) -> None:
    """The same task, the new text, and nothing else moved: not its state, not its
    moment of adding, and no second task beside it."""
    from app.contexts.todo_list.services.todo_tasks import add_todo_task, correct_todo_task

    task = add_todo_task(text="Buy bred")

    corrected = correct_todo_task(task.id, text="Buy bread")

    assert corrected.id == task.id
    assert corrected.text == "Buy bread"
    assert corrected.done is False, "a correction touched the state"
    assert corrected.created_at == task.created_at, "a correction re-stamped the moment of adding"
    assert _column(fresh_database) == [(task.id, "Buy bread", False, task.created_at)]


@pytest.mark.req("CR-2609-823a/R-6")
def test_a_done_task_is_corrected_as_a_not_done_one_is(fresh_database: sessionmaker) -> None:
    """Editing a done task keeps it done: a correction names `text` alone, so the
    state it did not name stays what is stored."""
    from app.contexts.todo_list.services.todo_tasks import (
        add_todo_task,
        correct_todo_task,
        mark_todo_task,
    )

    task = add_todo_task(text="Call the plumber")
    mark_todo_task(task.id, done=True)

    corrected = correct_todo_task(task.id, text="Call the plumber again")

    assert corrected.text == "Call the plumber again"
    assert corrected.done is True, "correcting a done task reset it to not done"
    assert corrected.created_at == task.created_at
    assert _row(fresh_database, task.id) == ("Call the plumber again", True, task.created_at)


@pytest.mark.req("CR-2609-823a/R-6")
def test_a_refused_correction_keeps_the_text_it_had(fresh_database: sessionmaker) -> None:
    """A correction is held to `BR-06` and `BR-07` exactly as an addition is, and a
    refused one writes nothing: the task keeps its text, and the refusal is the one
    domain exception of its verdict -- the router's only way to tell the person
    which of three things is wrong."""
    from app.contexts.todo_list.models.todo_task import TODO_TASK_TEXT_MAX_LENGTH
    from app.contexts.todo_list.services.todo_tasks import (
        TodoTaskTextEmptyError,
        TodoTaskTextMultilineError,
        TodoTaskTextTooLongError,
        add_todo_task,
        correct_todo_task,
    )

    task = add_todo_task(text="Buy bread")
    refused: tuple[tuple[str, type[Exception]], ...] = (
        ("   ", TodoTaskTextEmptyError),
        ("a" * (TODO_TASK_TEXT_MAX_LENGTH + 1), TodoTaskTextTooLongError),
        ("Buy bread" + chr(0x000A) + "and milk", TodoTaskTextMultilineError),
    )

    for text, verdict in refused:
        with pytest.raises(verdict):
            correct_todo_task(task.id, text=text)

        assert _row(fresh_database, task.id) == ("Buy bread", False, task.created_at), (
            f"a correction refused with {verdict.__name__} changed the task"
        )


# --------------------------------------------------------------------------- #
# Deleting, and what is gone (`BR-13`)
# --------------------------------------------------------------------------- #


@pytest.mark.req("CR-2609-823a/R-7")
def test_deleting_removes_the_row_and_leaves_every_other_task(
    fresh_database: sessionmaker,
) -> None:
    """The row stops existing -- no flag, no bin -- and its neighbours, a done one
    among them, are exactly as they were."""
    from app.contexts.todo_list.services.todo_tasks import (
        add_todo_task,
        delete_todo_task,
        mark_todo_task,
    )

    alpha, beta, gamma = (add_todo_task(text=text) for text in ("Alpha", "Beta", "Gamma"))
    mark_todo_task(gamma.id, done=True)
    before = {row[0]: row for row in _column(fresh_database)}

    delete_todo_task(beta.id)

    after = {row[0]: row for row in _column(fresh_database)}
    assert beta.id not in after, "the deleted task is still in the table"
    assert after == {alpha.id: before[alpha.id], gamma.id: before[gamma.id]}, (
        "deleting one task changed another"
    )


@pytest.mark.req("CR-2609-823a/R-8")
def test_a_change_to_a_deleted_task_changes_nothing_and_creates_nothing(
    fresh_database: sessionmaker,
) -> None:
    """A marking, a correction and a second deletion aimed at a task that is gone
    are each refused as not found, and none of them brings the task back -- not
    under its old text and not under the new one. A write that inserted on absence
    would resurrect what somebody deleted; a deletion that reported success twice
    would make a person believe they deleted twice."""
    from app.contexts.todo_list.services.todo_tasks import (
        TodoTaskNotFoundError,
        add_todo_task,
        correct_todo_task,
        delete_todo_task,
        mark_todo_task,
    )

    task = add_todo_task(text="Buy bread")
    delete_todo_task(task.id)

    with pytest.raises(TodoTaskNotFoundError):
        mark_todo_task(task.id, done=True)
    with pytest.raises(TodoTaskNotFoundError):
        correct_todo_task(task.id, text="Buy rye bread")
    with pytest.raises(TodoTaskNotFoundError):
        delete_todo_task(task.id)
    with pytest.raises(TodoTaskNotFoundError):
        mark_todo_task(uuid.uuid4(), done=True)

    assert _column(fresh_database) == [], "a change to a task that is gone created a row"

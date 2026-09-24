"""Two writers on one task, the second queued behind the first on the row's lock.

`BR-10` asks that a correction and a marking of one task sent at the same moment
both stick, and that of two changes to the same thing the one applied later wins;
`BR-13` asks that a change aimed at a task that is gone creates nothing. A test
that sends one change after the other passes a whole-row write-back, a flip and an
upsert exactly as it passes the statement shape that holds these rules
(`spec/design/data-model.md` § Two writers on one task). Only two writers
interleaved on one row, the second waiting on the first's lock, tell them apart --
so that is what every case here arranges, the way `spec/design/testing.md`
§ CR-2609-823a, "How two writers are interleaved", prescribes:

1. A third connection opens a transaction and takes the row's lock
   (`SELECT ... FOR UPDATE`).
2. Change A starts on a thread of its own, through the service with its own
   session, and the test waits until `pg_stat_activity` shows one backend of this
   database waiting on a lock. Change B starts, and the test waits for two.
3. The holder commits, both changes finish, and the row is read.

Postgres hands the row to its waiters in the order they queued, so A is applied
first and B later: "applied later" is a fact the test ARRANGED rather than one it
hoped for. Every wait is bounded at a few seconds and fails with a message of its
own rather than hanging, and a case that needs a re-run to pass goes to
quarantine, never to a retry (§ A test that flickers is not a gate).

What each defect looks like here, so a red line can be read:

- a correction that writes back the whole task it read restores the state it read
  and undoes the marking queued ahead of it;
- a marking that flips the stored state turns two people's "done" into not done;
- an upsert, or the ORM's `merge()`, brings a deleted task back; a load, modify and
  flush ends in a stale-data error instead of the not-found refusal.

The service's names are the ones `test_todo_tasks_service.py` fixes, imported
inside each test for the reason given there.
"""

import functools
import time
import uuid
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Final

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

#: How long any one wait may last before the case fails with its own message. A
#: queued statement shows in `pg_stat_activity` within milliseconds; five seconds
#: is room for a loaded runner, not a guess at how long a lock is held.
DEADLINE_SECONDS: Final[float] = 5.0

#: How often the waits look again.
POLL_SECONDS: Final[float] = 0.02


@dataclass(frozen=True)
class Outcome:
    """What one change came back with: the task as stored, or the error it raised."""

    value: Any = None
    error: BaseException | None = None

    def stored(self, what: str) -> Any:
        """The value, or a failure naming the change that raised instead."""
        if self.error is not None:
            pytest.fail(f"{what} raised {type(self.error).__name__}: {self.error}")
        return self.value


def _waiting_on_a_lock(session_factory: sessionmaker, database: str) -> int:
    """How many backends of `database` are waiting on a lock right now.

    A session of its own per look: `pg_stat_activity` is a snapshot taken once per
    transaction, so a single long-lived session would keep reading the first answer.
    """
    with session_factory() as session:
        count = session.execute(
            sa.text(
                "SELECT count(*) FROM pg_stat_activity "
                "WHERE datname = :database AND wait_event_type = 'Lock'"
            ),
            {"database": database},
        ).scalar_one()
    return int(count)


def _wait_until_queued(
    session_factory: sessionmaker,
    database: str,
    expected: int,
    change: Future[Any],
    what: str,
) -> None:
    deadline = time.monotonic() + DEADLINE_SECONDS
    while time.monotonic() < deadline:
        if change.done():
            pytest.fail(
                f"{what} finished while the row was still locked, so it never queued "
                f"behind the lock: {change.exception() or change.result()!r}"
            )
        if _waiting_on_a_lock(session_factory, database) >= expected:
            return
        time.sleep(POLL_SECONDS)
    pytest.fail(
        f"{what} was not seen waiting on the row's lock within {DEADLINE_SECONDS} s "
        f"(pg_stat_activity shows fewer than {expected} backends of {database} waiting)"
    )


def _outcome(change: Future[Any], what: str) -> Outcome:
    try:
        return Outcome(value=change.result(timeout=DEADLINE_SECONDS))
    except TimeoutError:
        pytest.fail(f"{what} did not finish within {DEADLINE_SECONDS} s of the lock being released")
    except Exception as error:
        return Outcome(error=error)


def _interleave(
    session_factory: sessionmaker,
    todo_task_id: uuid.UUID,
    first: Callable[[], Any],
    later: Callable[[], Any],
) -> tuple[Outcome, Outcome]:
    """Run `first` and then `later` against one row, `later` queued behind `first`.

    Returns what each came back with. The holder is released in every path, so a
    case that fails half-way leaves no thread waiting on a lock nobody will free.
    """
    holder = session_factory()
    workers = ThreadPoolExecutor(max_workers=2, thread_name_prefix="todo-task-writer")
    changes: list[Future[Any]] = []
    released = False
    try:
        locked = holder.execute(
            sa.text("SELECT id FROM todo_tasks WHERE id = :id FOR UPDATE"),
            {"id": todo_task_id},
        ).first()
        assert locked is not None, "the task to interleave on is not in the table"
        database = str(holder.execute(sa.text("SELECT current_database()")).scalar_one())

        changes.append(workers.submit(first))
        _wait_until_queued(session_factory, database, 1, changes[0], "the first change")
        changes.append(workers.submit(later))
        _wait_until_queued(session_factory, database, 2, changes[1], "the later change")

        holder.commit()
        released = True
        return _outcome(changes[0], "the first change"), _outcome(changes[1], "the later change")
    finally:
        if not released:
            holder.rollback()
        holder.close()
        workers.shutdown(wait=all(change.done() for change in changes), cancel_futures=True)


def _row(session_factory: sessionmaker, todo_task_id: uuid.UUID) -> tuple[Any, ...] | None:
    """One row as `(text, done)`, or `None` when no row has that id."""
    with session_factory() as session:
        row = session.execute(
            sa.text("SELECT text, done FROM todo_tasks WHERE id = :id"), {"id": todo_task_id}
        ).first()
    return None if row is None else tuple(row)


def _texts(session_factory: sessionmaker) -> list[str]:
    with session_factory() as session:
        return [str(text) for text in session.execute(sa.text("SELECT text FROM todo_tasks"))]


# --------------------------------------------------------------------------- #
# A correction and a marking (`BR-10`: a change to one thing never undoes the other)
# --------------------------------------------------------------------------- #


@pytest.mark.req("CR-2609-823a/R-9")
def test_a_correction_and_a_marking_queued_on_one_task_are_both_kept(
    fresh_database: sessionmaker,
) -> None:
    """Both orders, because each order catches a different write-back.

    A correction applied after a marking would restore the state it read; a marking
    applied after a correction would restore the text it read. Both changes are
    kept, whichever was applied first, and the statement applied later hands back
    the row as it left it -- the other writer's change included.
    """
    from app.contexts.todo_list.services.todo_tasks import (
        add_todo_task,
        correct_todo_task,
        mark_todo_task,
    )

    orders = ("the marking applied first", "the correction applied first")
    for order in orders:
        task = add_todo_task(text="Buy bread")
        marking = functools.partial(mark_todo_task, task.id, done=True)
        correction = functools.partial(correct_todo_task, task.id, text="Buy rye bread")
        first, later = (marking, correction) if order == orders[0] else (correction, marking)

        applied_first, applied_later = _interleave(fresh_database, task.id, first, later)

        applied_first.stored(f"{order}: the first change")
        returned = applied_later.stored(f"{order}: the later change")
        assert _row(fresh_database, task.id) == ("Buy rye bread", True), (
            f"{order}: one change undid the other"
        )
        assert (returned.text, returned.done) == ("Buy rye bread", True), (
            f"{order}: the later statement did not hand back the row as it left it"
        )


# --------------------------------------------------------------------------- #
# Two changes to the same thing (`BR-10`: the one applied later wins)
# --------------------------------------------------------------------------- #


@pytest.mark.req("CR-2609-823a/R-9")
def test_of_two_queued_corrections_the_one_applied_later_wins(
    fresh_database: sessionmaker,
) -> None:
    """The text of the correction applied later stays, and the state neither of
    them named is untouched."""
    from app.contexts.todo_list.services.todo_tasks import add_todo_task, correct_todo_task

    task = add_todo_task(text="Buy bread")

    applied_first, applied_later = _interleave(
        fresh_database,
        task.id,
        functools.partial(correct_todo_task, task.id, text="Buy rye bread"),
        functools.partial(correct_todo_task, task.id, text="Buy white bread"),
    )

    applied_first.stored("the first correction")
    applied_later.stored("the later correction")
    assert _row(fresh_database, task.id) == ("Buy white bread", False), (
        "the correction applied first survived, or the state moved"
    )


@pytest.mark.req("CR-2609-823a/R-9")
def test_of_two_queued_markings_the_one_applied_later_wins(fresh_database: sessionmaker) -> None:
    """Done after done, not done after done, done after not done.

    The first is the one a flip gets wrong: two people who both chose done, from a
    task that was not done, end with not done. The other two show the later
    choice is the one kept in both directions.
    """
    from app.contexts.todo_list.services.todo_tasks import add_todo_task, mark_todo_task

    # (stored before either, the first choice, the later choice)
    variants = ((False, True, True), (False, True, False), (True, False, True))
    for stored, first_choice, later_choice in variants:
        task = add_todo_task(text="Buy bread")
        if stored:
            mark_todo_task(task.id, done=True)

        applied_first, applied_later = _interleave(
            fresh_database,
            task.id,
            functools.partial(mark_todo_task, task.id, done=first_choice),
            functools.partial(mark_todo_task, task.id, done=later_choice),
        )

        variant = f"stored {stored}, then {first_choice}, then {later_choice}"
        applied_first.stored(f"{variant}: the first marking")
        applied_later.stored(f"{variant}: the later marking")
        assert _row(fresh_database, task.id) == ("Buy bread", later_choice), (
            f"{variant}: the task did not end in the state chosen by the marking applied later"
        )


# --------------------------------------------------------------------------- #
# A change behind a deletion (`BR-13`: what is gone stays gone)
# --------------------------------------------------------------------------- #


@pytest.mark.req("CR-2609-823a/R-8")
@pytest.mark.req("CR-2609-823a/R-9")
def test_a_change_queued_behind_a_deletion_creates_nothing(fresh_database: sessionmaker) -> None:
    """A correction and a marking, each queued behind a deletion of the same task.

    The statement that waited re-reads the row once the deletion commits, finds
    none, changes nothing and is refused as not found. An upsert would bring the
    task back -- under the new text, for the correction -- and a load, modify and
    flush would end in a stale-data error rather than the refusal.
    """
    from app.contexts.todo_list.services.todo_tasks import (
        TodoTaskNotFoundError,
        add_todo_task,
        correct_todo_task,
        delete_todo_task,
        mark_todo_task,
    )

    for change in ("correction", "marking"):
        task = add_todo_task(text="Buy bread")
        queued: Callable[[], Any] = (
            functools.partial(correct_todo_task, task.id, text="Buy rye bread")
            if change == "correction"
            else functools.partial(mark_todo_task, task.id, done=True)
        )

        deletion, behind = _interleave(
            fresh_database, task.id, functools.partial(delete_todo_task, task.id), queued
        )

        deletion.stored("the deletion")
        answered = "reported success" if behind.error is None else f"raised {behind.error!r}"
        assert isinstance(behind.error, TodoTaskNotFoundError), (
            f"the {change} queued behind a deletion {answered} instead of being refused as "
            "not found"
        )
        assert _row(fresh_database, task.id) is None, f"the {change} brought the deleted task back"
        assert _texts(fresh_database) == [], f"the {change} left a row behind"

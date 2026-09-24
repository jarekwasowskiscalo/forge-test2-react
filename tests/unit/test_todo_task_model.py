"""The to-do list model's declaration, asserted without a database.

`tests/integration/test_migrations.py` proves the table the revision *creates*; this
proves what the **model says it should be** (`spec/design/data-model.md` § `todo_tasks`).
They are two independent statements of one schema, so a revision that drifts from the
model shows up as exactly one of them failing -- the pair
`spec/design/testing.md` § Evidence map keeps for the guestbook, kept for the second
table.

Nothing here opens a connection: `Base.metadata` is populated at import, so the table,
its columns, their types and their defaults are readable as data.

**Red first.** `TodoTask` does not exist until the implementation wave writes
`app/contexts/todo_list/models/todo_task.py`, so it is imported inside `_table()`,
which each test calls -- never at the top of the module, where a failed import would
un-collect every case in the file (`spec/design/testing.md` § CR-2609-823a, "Red first").

**The bound is read from `TODO_TASK_TEXT_MAX_LENGTH`**, never written here as a
number: a test that writes `200` keeps proving it after the rule moves.
"""

import pytest
import sqlalchemy as sa
from sqlalchemy.sql.schema import ScalarElementColumnDefault


def _table() -> sa.Table:
    """`todo_tasks` as the model declares it, reached from inside the test that asks.

    `__table__` is typed as `FromClause` on the declarative base; for a mapped class it
    is always a `Table`, and this is the one place that fact is needed.
    """
    from app.contexts.todo_list.models.todo_task import TodoTask

    table = TodoTask.__table__
    assert isinstance(table, sa.Table)
    return table


@pytest.mark.req("CR-2609-823a/R-2")
def test_the_text_column_is_as_long_as_the_bound() -> None:
    """`String(TODO_TASK_TEXT_MAX_LENGTH)`, not null -- the last layer's refusal.

    A value that reaches the table by a route that skipped the rule -- a fixture, a
    script, a service that measured before it normalized, where two hundred decomposed
    letters are four hundred code points -- is held to the same number, and there is
    one number because the column reads it from the constant the service's judgement
    reads (`spec/design/data-model.md` § `todo_tasks`, "Why `String(200)`").
    """
    from app.contexts.todo_list.models.todo_task import TODO_TASK_TEXT_MAX_LENGTH

    text = _table().c.text

    assert isinstance(text.type, sa.String) and not isinstance(text.type, sa.Text), (
        f"the text column is {text.type!r}; the data model declares a bounded String"
    )
    assert text.type.length == TODO_TASK_TEXT_MAX_LENGTH
    assert text.nullable is False, "a task with no text is a row with nothing in it"


@pytest.mark.req("CR-2609-823a/R-1")
@pytest.mark.req("CR-2609-823a/R-4")
def test_a_new_task_is_not_done_by_the_models_default() -> None:
    """`done` is a boolean, not null, `False` by the model's default and by no server's.

    The one state a task has, with two values and no third (`BR-08`, `BR-09`): a
    nullable column would be a third -- "we do not know" -- that no rule describes. The
    default is the model's and not the database's, because the revision declares no
    server default and the model-against-revision comparison compares them
    (`spec/design/data-model.md` § The revision that creates `todo_tasks`).
    """
    done = _table().c.done

    assert isinstance(done.type, sa.Boolean), f"done is {done.type!r}, not a Boolean"
    assert done.nullable is False, "a nullable done is a third state no rule describes"
    assert isinstance(done.default, ScalarElementColumnDefault), (
        f"done's default is {done.default!r}; the data model declares default=False"
    )
    assert done.default.arg is False, f"a new task's default state is {done.default.arg!r}"
    assert done.server_default is None, "the database declares a default the model owns"


@pytest.mark.req("CR-2609-823a/R-1")
@pytest.mark.req("CR-2609-823a/R-3")
def test_the_moment_of_adding_is_stored_with_its_zone() -> None:
    """`created_at` keeps its zone, is set once, and nothing moves it afterwards.

    "Which task is newer" must settle across an offset change: a naive column makes
    the list's order depend on the server's local time (`BR-11`). And the moment of
    adding never changes -- not by a marking, not by a correction (`BR-08`) -- so the
    model declares no `onupdate` that would move it on every write, and no server
    default: the service stamps it from its own clock on insert.
    """
    created_at = _table().c.created_at

    assert isinstance(created_at.type, sa.DateTime), f"created_at is {created_at.type!r}"
    assert created_at.type.timezone is True, "created_at lost its time zone"
    assert created_at.nullable is False, "a task with no moment of adding has no place"
    assert created_at.onupdate is None and created_at.server_onupdate is None, (
        "created_at is rewritten on update, so a marking or a correction would move the task"
    )
    assert created_at.server_default is None, "the database stamps a moment the service owns"


@pytest.mark.req("CR-2609-823a/R-3")
def test_the_order_has_an_index_the_model_declares() -> None:
    """`ix_todo_tasks_created_at_id` over `created_at` then `id`, not unique.

    Declared in the model as well as in the revision, deliberately: autogeneration
    compares the database against `Base.metadata`, and an index the model does not
    know about is, to it, an index to drop in the next revision. `id` is in it because
    it is in the `ORDER BY` -- it is what makes the order total for two tasks stored in
    the same instant (`BR-11`). Not unique: the same text twice is two tasks (`BR-12`),
    and no rule in this table says "at most one".
    """
    indexes = {str(index.name): index for index in _table().indexes}

    assert "ix_todo_tasks_created_at_id" in indexes, (
        f"the model declares the indexes {sorted(indexes)}"
    )
    order = indexes["ix_todo_tasks_created_at_id"]
    assert [column.name for column in order.columns] == ["created_at", "id"]
    assert not order.unique, "the ordering index refuses two tasks sharing a moment"

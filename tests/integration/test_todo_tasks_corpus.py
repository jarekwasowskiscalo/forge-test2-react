"""The to-do list's rules, driven by the committed corpus rather than by invented values.

The counterpart of `test_guestbook_entries_corpus.py` for the second context, and
apart from `test_todo_tasks_service.py` for the same reason that one is apart from
the guestbook's service test: the service test states each rule once with the
smallest value that shows it; this one runs **every** case the corpus ships
through the whole stack -- the route, the service, the column -- and lets the files
decide the coverage (`spec/design/testing.md` § CR-2609-823a, the to-do list).

What each file claims, and what is asserted about it:

- `todo-tasks-boundary.json` -- every text on the bound is accepted and stored as
  its `stored` says: the bound counted in code points, after NFC and the trim;
- `todo-tasks-refused.json` -- every text is refused with the code the contract
  gives it, and nothing is stored; sent again as a correction, the task keeps the
  text it had (`BR-10`: a correction is held to `BR-06` and `BR-07` exactly as an
  addition is);
- `todo-tasks-ordinary.json` -- added in file order, the done ones marked only
  after every task is added (a task is never born done, `BR-08`), the list reads
  back as the reversal of the file with its marks (`BR-11`), a repeated text as
  two tasks (`BR-12`).

The file is the input and the rule is the claim: an expectation is derived from
the corpus -- its reversal, its `stored`, its `refusal` -- and never written out a
second time here. The corpus itself is held to its own rules by
`tests/fitness/test_golden_set.py`, so a red line here is the application
disagreeing with the corpus, never the corpus disagreeing with itself.

What reached the column is read with SQL rather than through the service, so the
assertion and its subject are never the same code.
"""

from typing import Any

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from tests._golden_set import TODO_TASKS_BOUNDARY, TODO_TASKS_ORDINARY, TODO_TASKS_REFUSED, tasks_of

TASKS = "/api/todo-tasks"

#: The task every refused text is sent to as a correction -- the value the
#: scenario for a refused edit uses (`scenarios.md`, "An edit breaking a rule is
#: refused and the task keeps its text").
EXISTING = "Buy bread"


def _ids(path: Any) -> list[str]:
    return [str(task["case"]) for task in tasks_of(path)]


def _column(session_factory: sessionmaker) -> list[tuple[Any, ...]]:
    """Every row of `todo_tasks` as `(id, text, done)`, in the list's order."""
    with session_factory() as session:
        rows = session.execute(
            sa.text("SELECT id, text, done FROM todo_tasks ORDER BY created_at DESC, id DESC")
        ).all()
    return [tuple(row) for row in rows]


def _said(response: Any) -> str:
    """The start of an answer, for a failure message -- enough to tell a JSON 404
    from a refusal, and never a whole two-hundred-emoji body."""
    return f"{response.status_code} {response.text[:160]}"


# --------------------------------------------------------------------------- #
# On the bound: accepted, and stored as the file says
# --------------------------------------------------------------------------- #


@pytest.mark.req("CR-2609-823a/R-2")
@pytest.mark.parametrize("task", tasks_of(TODO_TASKS_BOUNDARY), ids=_ids(TODO_TASKS_BOUNDARY))
def test_every_boundary_task_is_accepted_and_stored_as_the_file_states(
    client: TestClient, fresh_database: sessionmaker, task: dict[str, Any]
) -> None:
    """The half of a bound that is usually missing, in the unit the bound is in.

    Two hundred emoji are four hundred UTF-16 units, two hundred decomposed letters
    four hundred code points before NFC, and a padded text two hundred and four as
    sent: every one is accepted, because the rule normalizes, trims and only then
    counts code points. A bound proved only where it refuses passes identically
    whether it sits at 200 or at 2000.
    """
    response = client.post(TASKS, json={"text": task["text"]})

    assert response.status_code == 201, f"{task['case']} was not accepted: {_said(response)}"
    body = response.json()
    assert body["text"] == task["stored"], f"{task['case']} came back as something else"
    assert body["done"] is False, f"{task['case']} was born done"

    listed = client.get(TASKS).json()
    assert [item["text"] for item in listed["items"]] == [task["stored"]]
    assert [text for _, text, _ in _column(fresh_database)] == [task["stored"]], (
        f"{task['case']}: what reached the column is not what the file says it is stored as"
    )


# --------------------------------------------------------------------------- #
# Refused: with the code the contract gives, and nothing written
# --------------------------------------------------------------------------- #


@pytest.mark.req("CR-2609-823a/R-2")
@pytest.mark.parametrize("task", tasks_of(TODO_TASKS_REFUSED), ids=_ids(TODO_TASKS_REFUSED))
def test_every_refused_task_is_refused_with_its_code_and_stores_nothing(
    client: TestClient, fresh_database: sessionmaker, task: dict[str, Any]
) -> None:
    """Refused, with a reason of its own, and nothing stored.

    The code is the contract the screen branches on to say which of three things is
    wrong, so a text refused with FastAPI's list -- the guestbook's shape, which
    names no reason -- fails here as surely as one that was stored. Two hundred and
    five spaces are the case that proves the order: refused as empty, never as too
    long, because the text is trimmed before it is measured.
    """
    response = client.post(TASKS, json={"text": task["text"]})

    assert response.status_code == 422, f"{task['case']} was not refused: {_said(response)}"
    detail = response.json()["detail"]
    assert isinstance(detail, dict), (
        f"{task['case']} was refused with FastAPI's list instead of a coded refusal: "
        f"{_said(response)}"
    )
    assert detail["code"] == task["refusal"], (
        f"{task['case']} was refused as {detail['code']!r}, and the file says {task['refusal']!r}"
    )
    assert "id" not in detail, "a refusal about a text is about no identified task"
    assert _column(fresh_database) == [], f"{task['case']} was refused and stored anyway"


@pytest.mark.req("CR-2609-823a/R-6")
@pytest.mark.req("CR-2609-823a/R-2")
@pytest.mark.parametrize("task", tasks_of(TODO_TASKS_REFUSED), ids=_ids(TODO_TASKS_REFUSED))
def test_every_refused_text_is_refused_as_a_correction_and_the_task_keeps_its_text(
    client: TestClient, fresh_database: sessionmaker, task: dict[str, Any]
) -> None:
    """The rule belongs to the task's text, not to the route that writes it.

    An addition and a correction share one judgement in the service
    (`spec/design/architecture.md` § The layer per rule, `BR-10`), and this is what
    shows it from outside: a text weaker rules let through on the way in by editing
    would be a hole no addition test can see. A refused correction writes nothing,
    so the task reads exactly as it did.
    """
    created = client.post(TASKS, json={"text": EXISTING})
    assert created.status_code == 201, f"there is no task to correct: {_said(created)}"
    existing = created.json()

    response = client.patch(f"{TASKS}/{existing['id']}", json={"text": task["text"]})

    assert response.status_code == 422, (
        f"{task['case']} was not refused as a correction: {_said(response)}"
    )
    detail = response.json()["detail"]
    assert isinstance(detail, dict), f"{task['case']} was refused without a code: {_said(response)}"
    assert detail["code"] == task["refusal"], (
        f"{task['case']} was refused as {detail['code']!r} on a correction, and the file says "
        f"{task['refusal']!r} -- the reason an addition of that text would get"
    )
    assert [(text, done) for _, text, done in _column(fresh_database)] == [(EXISTING, False)], (
        f"{task['case']}: a refused correction changed the task"
    )
    assert client.get(TASKS).json()["items"] == [existing]


# --------------------------------------------------------------------------- #
# Ordinary: the whole list, in one order, with its marks
# --------------------------------------------------------------------------- #


@pytest.mark.req("CR-2609-823a/R-3")
@pytest.mark.req("CR-2609-823a/R-1")
def test_the_ordinary_tasks_read_back_as_the_reversal_of_the_file_with_their_marks(
    client: TestClient, fresh_database: sessionmaker
) -> None:
    """`BR-11` over the corpus, and the one assertion the file's ORDER exists for.

    The file is in ADDING order and the list answers newest first, so the
    expectation is the file reversed -- a claim about the rule, where a hand-written
    list would be a second copy of the data. Every task is added before any is
    marked, because the contract has no way to add a task done and the file's marks
    are where the tasks END. Done tasks stay where they were added (`BR-11`), the
    repeated text is two tasks each with its own mark (`BR-12`), and the text
    outside ASCII comes back byte for byte.
    """
    written = tasks_of(TODO_TASKS_ORDINARY)
    ids: list[str] = []
    for task in written:
        response = client.post(TASKS, json={"text": task["text"]})
        assert response.status_code == 201, f"{task['text']!r} was not added: {_said(response)}"
        assert response.json()["done"] is False, f"{task['text']!r} was born done"
        ids.append(response.json()["id"])
    assert len(set(ids)) == len(written), "a repeated text was merged into the task it repeats"

    for task_id, task in zip(ids, written, strict=True):
        if task["done"]:
            marked = client.patch(f"{TASKS}/{task_id}", json={"done": True})
            assert marked.status_code == 200, f"{task['text']!r} was not marked: {_said(marked)}"

    listed = client.get(TASKS)

    assert listed.status_code == 200, _said(listed)
    body = listed.json()
    expected = [(task["text"], task["done"]) for task in reversed(written)]
    assert [(item["text"], item["done"]) for item in body["items"]] == expected
    assert [item["id"] for item in body["items"]] == list(reversed(ids))
    assert body["total"] == len(written)
    assert [(text, done) for _, text, done in _column(fresh_database)] == expected

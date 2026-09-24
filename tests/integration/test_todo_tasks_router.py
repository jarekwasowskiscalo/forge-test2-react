"""The to-do list's HTTP contract, over real storage.

The seam the service tests cannot reach: the status each outcome carries, the
body each answer has, which refusal one request earns and in which order, and the
router's translation of every domain exception into the coded refusal
`spec/design/api.md` § The to-do list's refusals publishes. The rules themselves
are proved a layer down, in `test_todo_tasks_service.py`.

**Refusals are asserted by their code AND their sentence here**, unlike the
guestbook's router test, which pins codes alone. The to-do list's contract gives
every refusal a sentence written out in the register, the three about a text
included, and says the router holds them "exactly as written here" -- a sentence
reworded in the router and not in the register is the divergence the register
exists to prevent, and this is where it would show.

Values come from `scenarios.md` § Inline values, and every text the rules refuse
from the corpus, looked up by its case name -- never a number written here.

What reached the column is read with SQL, not through the application, so the
assertion and its subject are never the same code.
"""

import datetime as dt
import uuid
from typing import Any, Final

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from tests._golden_set import TODO_TASK_TEXT, TODO_TASKS_REFUSED, cases_of, tasks_of

TASKS: Final[str] = "/api/todo-tasks"

#: A well-formed UUID no task has. Distinct from a malformed one: the first is a
#: `404` about a task that is not there, the second a `422` about an identifier
#: that cannot be read, and the two answer with different shapes.
ABSENT: Final[str] = "00000000-0000-4000-8000-000000000000"

#: The five sentences of `spec/design/api.md` § The to-do list's refusals, copied
#: verbatim -- the contract's words, which the router is to hold exactly.
SENTENCES: Final[dict[str, str]] = {
    "todo_task_not_found": (
        "This task no longer exists. Somebody may have deleted it, and nothing was changed."
    ),
    "todo_task_empty_patch": "No change was given. The task is unchanged.",
    "todo_task_text_empty": "A task needs text. Type what there is to do.",
    "todo_task_text_multiline": (
        "A task is one line, and this text has a line break inside it, which may not be "
        "visible. Remove the line break and try again."
    ),
    "todo_task_text_too_long": "A task can be at most 200 characters. Shorten it and try again.",
}


def _refused(name: str) -> dict[str, Any]:
    """One case of `todo-tasks-refused.json`, by name and never by position."""
    for task in tasks_of(TODO_TASKS_REFUSED):
        if task["case"] == name:
            return task
    raise AssertionError(f"no case {name!r} in {TODO_TASKS_REFUSED.name}")


#: One text per refusal code, each the corpus's own.
EMPTY: Final[dict[str, Any]] = _refused("text_three_spaces")
MULTILINE: Final[dict[str, Any]] = _refused("text_line_break_inside")
TOO_LONG: Final[dict[str, Any]] = _refused("text_one_past_maximum")


def _said(response: Any) -> str:
    return f"{response.status_code} {response.text[:300]}"


def _add(client: TestClient, text: str) -> dict[str, Any]:
    response = client.post(TASKS, json={"text": text})
    assert response.status_code == 201, f"adding {text!r} was answered {_said(response)}"
    body: dict[str, Any] = response.json()
    return body


def _refusal(response: Any, code: str, *, status: int = 422) -> dict[str, Any]:
    """The coded refusal `code`, with its status and the contract's sentence."""
    assert response.status_code == status, f"expected {status} {code}, got {_said(response)}"
    detail = response.json()["detail"]
    assert isinstance(detail, dict), (
        f"expected the coded refusal {code}, got FastAPI's list with no code: {_said(response)}"
    )
    assert detail.get("code") == code, f"expected {code}, got {_said(response)}"
    assert detail.get("message") == SENTENCES[code], (
        f"{code} carries a sentence other than the one spec/design/api.md publishes"
    )
    return detail


def _validation(response: Any, what: str) -> None:
    """The standing validation `422`: FastAPI's list of `{loc, msg, type}`, no code."""
    assert response.status_code == 422, f"{what} was answered {_said(response)}"
    detail = response.json()["detail"]
    assert isinstance(detail, list) and detail, (
        f"{what} was not given the standard validation refusal: {_said(response)}"
    )
    assert all("code" not in item for item in detail), f"{what} carries a coded refusal"


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


def _stored(session_factory: sessionmaker, todo_task_id: str) -> tuple[Any, ...] | None:
    """One row as `(text, done)`, or `None` when no row has that id."""
    with session_factory() as session:
        row = session.execute(
            sa.text("SELECT text, done FROM todo_tasks WHERE id = :id"),
            {"id": uuid.UUID(todo_task_id)},
        ).first()
    return None if row is None else tuple(row)


# --------------------------------------------------------------------------- #
# The four routes, answering
# --------------------------------------------------------------------------- #


@pytest.mark.req("CR-2609-823a/R-1")
def test_adding_answers_201_with_the_task_as_stored(
    client: TestClient, fresh_database: sessionmaker
) -> None:
    """`201` with the task exactly as it now stands in the column: the four fields
    `TodoTaskRead` has and no other, not done, and a moment of adding that carries
    its offset on the wire."""
    response = client.post(TASKS, json={"text": "Water the plants"})

    assert response.status_code == 201, _said(response)
    body = response.json()
    assert set(body) == {"id", "text", "done", "created_at"}, (
        "a task has an id, a text, a state and a moment of adding, and nothing else"
    )
    assert body["text"] == "Water the plants"
    assert body["done"] is False
    created_at = dt.datetime.fromisoformat(body["created_at"])
    assert created_at.utcoffset() is not None, "the moment of adding lost its offset on the wire"
    assert _column(fresh_database) == [
        (uuid.UUID(body["id"]), "Water the plants", False, created_at)
    ]


@pytest.mark.req("CR-2609-823a/R-1")
def test_a_done_sent_with_a_new_task_is_ignored(
    client: TestClient, fresh_database: sessionmaker
) -> None:
    """The create shape has no `done`, and a key it does not have is ignored rather
    than refused: the request asked for a task and gets one, not done (`BR-08`)."""
    response = client.post(TASKS, json={"text": "Already finished", "done": True})

    assert response.status_code == 201, _said(response)
    assert response.json()["done"] is False, "a task sent as done was born done"
    assert _stored(fresh_database, response.json()["id"]) == ("Already finished", False)


@pytest.mark.req("CR-2609-823a/R-3")
def test_the_list_is_one_envelope_with_every_task_and_its_count(
    client: TestClient, fresh_database: sessionmaker
) -> None:
    """One envelope, `items` and `total`, with every task in it newest first.

    An empty list is a `200` with nothing in it, never a `404`. The read takes no
    parameters, so one it does not take changes nothing -- in particular `limit`
    and `offset`, which a read borrowed from the guestbook would obey and so hand
    out the list in pieces (`BR-11`).
    """
    empty = client.get(TASKS)
    assert empty.status_code == 200, _said(empty)
    assert empty.json() == {"items": [], "total": 0}

    for text in ("First", "Second", "Third"):
        _add(client, text)

    response = client.get(TASKS)

    assert response.status_code == 200, _said(response)
    body = response.json()
    assert set(body) == {"items", "total"}
    assert [item["text"] for item in body["items"]] == ["Third", "Second", "First"]
    assert body["total"] == len(body["items"]) == 3
    for params in ({"limit": 1}, {"offset": 2}, {"limit": 1, "offset": 1}, {"sort": "oldest"}):
        again = client.get(TASKS, params=params)
        assert again.status_code == 200, f"{params} was answered {_said(again)}"
        assert again.json() == body, f"{params} changed the answer; the read takes no parameters"


@pytest.mark.req("CR-2609-823a/R-4")
def test_a_patch_carrying_done_alone_writes_done_alone(
    client: TestClient, fresh_database: sessionmaker
) -> None:
    """A marking, both ways: the state chosen, and the text and the moment of adding
    as they were."""
    task = _add(client, "Buy bread")

    done = client.patch(f"{TASKS}/{task['id']}", json={"done": True})
    assert done.status_code == 200, _said(done)
    assert done.json() == {**task, "done": True}
    assert _stored(fresh_database, task["id"]) == ("Buy bread", True)

    undone = client.patch(f"{TASKS}/{task['id']}", json={"done": False})
    assert undone.status_code == 200, _said(undone)
    assert undone.json() == task
    assert _stored(fresh_database, task["id"]) == ("Buy bread", False)


@pytest.mark.req("CR-2609-823a/R-6")
def test_a_patch_carrying_text_alone_writes_text_alone(
    client: TestClient, fresh_database: sessionmaker
) -> None:
    """A correction of a done task leaves it done, and a field sent as `null` reads
    as absent -- "do not touch", never "clear"."""
    task = _add(client, "Call the plumber")
    marked = client.patch(f"{TASKS}/{task['id']}", json={"done": True})
    assert marked.status_code == 200, _said(marked)

    corrected = client.patch(f"{TASKS}/{task['id']}", json={"text": "Call the plumber again"})

    assert corrected.status_code == 200, _said(corrected)
    assert corrected.json() == {**task, "text": "Call the plumber again", "done": True}
    assert _stored(fresh_database, task["id"]) == ("Call the plumber again", True)

    with_a_null = client.patch(
        f"{TASKS}/{task['id']}", json={"text": "Call the plumber", "done": None}
    )
    assert with_a_null.status_code == 200, _said(with_a_null)
    assert with_a_null.json() == {**task, "done": True}
    assert _stored(fresh_database, task["id"]) == ("Call the plumber", True)


@pytest.mark.req("CR-2609-823a/R-6")
def test_a_refused_text_in_a_patch_that_also_carries_done_writes_neither(
    client: TestClient, fresh_database: sessionmaker
) -> None:
    """A body carrying both fields is one change: when its text is refused, its
    `done` is not written either, and the task is exactly as it was."""
    task = _add(client, "Buy bread")

    for refused in (EMPTY, MULTILINE, TOO_LONG):
        response = client.patch(
            f"{TASKS}/{task['id']}", json={"text": refused["text"], "done": True}
        )

        _refusal(response, refused["refusal"])
        assert _stored(fresh_database, task["id"]) == ("Buy bread", False), (
            f"{refused['case']} was refused and the marking beside it was written anyway"
        )


@pytest.mark.req("CR-2609-823a/R-7")
def test_deleting_answers_204_with_no_body(
    client: TestClient, fresh_database: sessionmaker
) -> None:
    """`204`, no body, the row gone -- and the two tasks beside it exactly as they were."""
    alpha, beta, gamma = (_add(client, text) for text in ("Alpha", "Beta", "Gamma"))

    response = client.delete(f"{TASKS}/{beta['id']}")

    assert response.status_code == 204, _said(response)
    assert response.content == b""
    assert _stored(fresh_database, beta["id"]) is None, "the deleted task is still in the table"
    assert client.get(TASKS).json() == {"items": [gamma, alpha], "total": 2}


# --------------------------------------------------------------------------- #
# The refusals, each made to happen
# --------------------------------------------------------------------------- #


@pytest.mark.req("CR-2609-823a/R-8")
def test_a_change_to_a_missing_task_answers_404_with_its_code(
    client: TestClient, fresh_database: sessionmaker
) -> None:
    """A marking, a correction and a second deletion of a task that is gone: each a
    `404` naming the identifier it was about, and none of them creating a task --
    not under the old text, not under the new one."""
    task = _add(client, "Buy bread")
    url = f"{TASKS}/{task['id']}"
    first_deletion = client.delete(url)
    assert first_deletion.status_code == 204, _said(first_deletion)

    for response in (
        client.patch(url, json={"done": True}),
        client.patch(url, json={"text": "Buy rye bread"}),
        client.delete(url),
    ):
        detail = _refusal(response, "todo_task_not_found", status=404)
        assert detail.get("id") == task["id"], "the refusal does not name the task it is about"

    never_existed = _refusal(
        client.patch(f"{TASKS}/{ABSENT}", json={"done": True}), "todo_task_not_found", status=404
    )
    assert never_existed.get("id") == ABSENT
    assert _column(fresh_database) == [], "a change to a task that is gone created a row"


@pytest.mark.req("CR-2609-823a/R-4")
@pytest.mark.req("CR-2609-823a/R-6")
def test_a_patch_setting_neither_field_is_refused(
    client: TestClient, fresh_database: sessionmaker
) -> None:
    """A body that sets neither field asks for nothing, and saying so is better than
    a `200` for a change nobody made. A field sent as `null` sets nothing, so a body
    of two nulls is the same request as `{}`."""
    task = _add(client, "Buy bread")

    for body in ({}, {"text": None, "done": None}, {"text": None}, {"done": None}):
        detail = _refusal(client.patch(f"{TASKS}/{task['id']}", json=body), "todo_task_empty_patch")
        assert "id" not in detail, f"{body}: the refusal is about the request, not about a task"

    assert _stored(fresh_database, task["id"]) == ("Buy bread", False)


@pytest.mark.req("CR-2609-823a/R-2")
@pytest.mark.req("CR-2609-823a/R-6")
def test_each_text_refusal_answers_with_its_own_code(
    client: TestClient, fresh_database: sessionmaker
) -> None:
    """Three reasons, three codes, on an addition and on a correction alike.

    A text refused with FastAPI's list instead would leave the screen unable to say
    which of three things to change -- which is why the contract carries no length
    bound in the schema at all.
    """
    for refused in (EMPTY, MULTILINE, TOO_LONG):
        detail = _refusal(client.post(TASKS, json={"text": refused["text"]}), refused["refusal"])
        assert "id" not in detail, f"{refused['case']}: a refusal about a text names no task"
    assert _column(fresh_database) == [], "a refused addition stored a task"

    task = _add(client, "Buy bread")
    for refused in (EMPTY, MULTILINE, TOO_LONG):
        response = client.patch(f"{TASKS}/{task['id']}", json={"text": refused["text"]})
        _refusal(response, refused["refusal"])
    assert _stored(fresh_database, task["id"]) == ("Buy bread", False)


@pytest.mark.req("CR-2609-823a/R-2")
@pytest.mark.req("CR-2609-823a/R-6")
def test_a_text_too_long_and_on_two_lines_is_refused_as_multiline(
    client: TestClient, fresh_database: sessionmaker
) -> None:
    """A text that breaks both rules earns one reason, and it is the one a person
    cannot see for themselves: a pasted line break is often invisible in a
    one-line field, a text's length is not (`BR-07`)."""
    both = next(
        case
        for case in cases_of(TODO_TASK_TEXT)
        if case["case"] == "too_long_and_on_two_lines_is_multiline"
    )

    _refusal(client.post(TASKS, json={"text": both["input"]}), "todo_task_text_multiline")
    assert _column(fresh_database) == []

    task = _add(client, "Buy bread")
    _refusal(
        client.patch(f"{TASKS}/{task['id']}", json={"text": both["input"]}),
        "todo_task_text_multiline",
    )
    assert _stored(fresh_database, task["id"]) == ("Buy bread", False)


@pytest.mark.req("CR-2609-823a/R-2")
@pytest.mark.req("CR-2609-823a/R-4")
@pytest.mark.req("CR-2609-823a/R-8")
def test_a_body_of_the_wrong_shape_gets_the_standard_validation_refusal(
    client: TestClient, fresh_database: sessionmaker
) -> None:
    """A malformed request is not a text anybody typed, and it gets FastAPI's list.

    No `text` on a `POST`, a `text` that is `null` or a number, a `done` that only
    reads as a boolean -- `"true"` or `1` is not a choice anybody made -- and an
    identifier that is not a UUID, which is "this is not an identifier" and never
    "there is no such task".
    """
    for body, what in (
        ({}, "a POST with no text"),
        ({"text": None}, "a POST whose text is null"),
        ({"text": 42}, "a POST whose text is a number"),
    ):
        _validation(client.post(TASKS, json=body), what)
    assert _column(fresh_database) == [], "a malformed addition stored a task"

    task = _add(client, "Buy bread")
    url = f"{TASKS}/{task['id']}"
    for body, what in (
        ({"done": "true"}, "a PATCH whose done is the string true"),
        ({"done": 1}, "a PATCH whose done is the number one"),
        ({"text": 42}, "a PATCH whose text is a number"),
    ):
        _validation(client.patch(url, json=body), what)
    assert _stored(fresh_database, task["id"]) == ("Buy bread", False)

    _validation(
        client.patch(f"{TASKS}/not-a-uuid", json={"done": True}),
        "a PATCH to an identifier that is not a UUID",
    )
    _validation(
        client.delete(f"{TASKS}/not-a-uuid"), "a DELETE of an identifier that is not a UUID"
    )


@pytest.mark.req("CR-2609-823a/R-8")
def test_a_request_is_refused_for_what_it_is_whatever_its_identifier_names(
    client: TestClient, fresh_database: sessionmaker
) -> None:
    """One refusal per request, in the contract's order, and the lookup last.

    A request that could never succeed -- a body of the wrong shape, one that sets
    nothing, a text the rules refuse -- is refused for what it is, even when it is
    sent to an identifier no task has. Only a request that could succeed learns
    that the task is not there.
    """
    url = f"{TASKS}/{ABSENT}"

    _validation(client.patch(url, json={"done": "yes"}), "a malformed PATCH to a missing task")
    _refusal(client.patch(url, json={}), "todo_task_empty_patch")
    for refused in (EMPTY, MULTILINE, TOO_LONG):
        _refusal(client.patch(url, json={"text": refused["text"]}), refused["refusal"])
    _refusal(client.patch(url, json={"done": True}), "todo_task_not_found", status=404)

    assert _column(fresh_database) == [], "a refused request created a task"

"""Every real answer of the to-do routes validates against the schema published for it.

The to-do list's counterpart of `test_guestbook_entries_contract.py`, and for the
same reason: `scripts/openapi_contract.py` compares two documents and never sends
a request, so a response whose declared schema is simply wrong -- or a status
raised with no `responses=` behind it -- passes that gate. This module sends the
request, reads the status that actually came back, pulls the schema the published
document declares for THAT operation and THAT status, and validates the body
against it with every `$ref` resolved.

It matters more here than it did for the guestbook. `POST` and `PATCH` answer
`422` with two shapes -- a coded `Refusal` for a text the rules refuse or a patch
that sets nothing, FastAPI's `HTTPValidationError` for a body of the wrong shape --
and `spec/design/api.md` § The to-do list's refusals publishes both as an `anyOf`.
A declaration of one alone would describe half the answers and suppress the type
of the other half in `frontend/src/api/schema.d.ts`; the two cases of each shape
below are what would say so.

`app.openapi()` is the published document: the one `scripts/dump_openapi.py`
writes and the frontend's types are generated from. OpenAPI 3.1 schemas are JSON
Schema 2020-12, which is why the validator is pinned to that draft.

The thirteen cases are exactly the ones `CR-2609-823a`'s plan names, by id.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Final

import jsonschema
import pytest
from fastapi.testclient import TestClient

from app.main import app

TASKS: Final[str] = "/api/todo-tasks"
ONE_TASK: Final[str] = "/api/todo-tasks/{todo_task_id}"

#: A well-formed UUID no task has: a `404` about a missing task, never the `422`
#: about an unreadable identifier.
ABSENT: Final[str] = "00000000-0000-4000-8000-000000000000"


@pytest.fixture(autouse=True)
def isolated_database(fresh_database):
    """Delegates to the shared fixture, which discovers every module holding a
    `SessionLocal`. Most cases add a task to have something to address, and those
    rows must not outlive the case."""


@dataclass(frozen=True)
class Case:
    """One request, the template the document keys it under, and the status it must answer."""

    name: str
    method: str
    template: str
    url: Callable[[TestClient], str]
    status: int
    body: Any = None


def _added(client: TestClient, text: str = "Buy bread") -> str:
    """Add one task and return its id, so a case has something to address."""
    response = client.post(TASKS, json={"text": text})
    assert response.status_code == 201, (
        f"no task to address: {response.status_code} {response.text}"
    )
    identifier: str = response.json()["id"]
    return identifier


CASES: Final[tuple[Case, ...]] = (
    Case("list_answers", "get", TASKS, lambda c: TASKS, 200),
    Case("create_succeeds", "post", TASKS, lambda c: TASKS, 201, {"text": "Water the plants"}),
    # The coded half of the POST's two `422` shapes.
    Case("create_refuses_an_empty_text", "post", TASKS, lambda c: TASKS, 422, {"text": "   "}),
    # And FastAPI's half: a text that is not a string is a malformed request.
    Case(
        "create_refuses_a_text_that_is_not_a_string",
        "post",
        TASKS,
        lambda c: TASKS,
        422,
        {"text": 42},
    ),
    Case(
        "patch_marks",
        "patch",
        ONE_TASK,
        lambda c: f"{TASKS}/{_added(c)}",
        200,
        {"done": True},
    ),
    Case(
        "patch_corrects",
        "patch",
        ONE_TASK,
        lambda c: f"{TASKS}/{_added(c, 'Buy bred')}",
        200,
        {"text": "Buy bread"},
    ),
    Case(
        "patch_refuses_an_empty_patch",
        "patch",
        ONE_TASK,
        lambda c: f"{TASKS}/{_added(c)}",
        422,
        {},
    ),
    Case(
        "patch_refuses_a_text_on_two_lines",
        "patch",
        ONE_TASK,
        lambda c: f"{TASKS}/{_added(c)}",
        422,
        {"text": "Buy bread" + chr(0x000A) + "and milk"},
    ),
    Case(
        "patch_refuses_a_done_that_is_not_a_boolean",
        "patch",
        ONE_TASK,
        lambda c: f"{TASKS}/{_added(c)}",
        422,
        {"done": "true"},
    ),
    Case(
        "patch_task_is_absent",
        "patch",
        ONE_TASK,
        lambda c: f"{TASKS}/{ABSENT}",
        404,
        {"done": True},
    ),
    Case(
        "patch_id_is_not_a_uuid",
        "patch",
        ONE_TASK,
        lambda c: f"{TASKS}/not-a-uuid",
        422,
        {"done": True},
    ),
    Case("delete_succeeds", "delete", ONE_TASK, lambda c: f"{TASKS}/{_added(c)}", 204),
    Case("delete_is_absent", "delete", ONE_TASK, lambda c: f"{TASKS}/{ABSENT}", 404),
)


def _declared_schema(document: dict[str, Any], case: Case, status: int) -> Any:
    """The JSON body schema the document declares for this operation and status.

    `None` means no JSON body is declared -- right for a `204`, a finding for
    anything else, which is why the caller decides what it means.
    """
    operations = document["paths"].get(case.template)
    assert operations is not None and case.method in operations, (
        f"the published document has no {case.method.upper()} {case.template}"
    )
    responses = operations[case.method]["responses"]
    assert str(status) in responses, (
        f"{case.method.upper()} {case.template} answered {status}, and the published document "
        f"declares no such response. A status raised without `responses={{{status}: ...}}` on "
        "the decorator reaches neither openapi.json nor frontend/src/api/schema.d.ts."
    )
    content = responses[str(status)].get("content")
    if not content or "application/json" not in content:
        return None
    return content["application/json"].get("schema")


@pytest.mark.req("CR-2609-823a/R-1")
@pytest.mark.req("CR-2609-823a/R-2")
@pytest.mark.req("CR-2609-823a/R-3")
@pytest.mark.req("CR-2609-823a/R-4")
@pytest.mark.req("CR-2609-823a/R-6")
@pytest.mark.req("CR-2609-823a/R-7")
@pytest.mark.req("CR-2609-823a/R-8")
@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
def test_the_body_matches_the_schema_published_for_the_status_it_returned(
    client: TestClient, case: Case
) -> None:
    url = case.url(client)

    response = client.request(case.method.upper(), url, json=case.body)

    assert response.status_code == case.status, (
        f"expected {case.status} from {case.method.upper()} {url}, got "
        f"{response.status_code}: {response.text[:300]}"
    )

    schema = _declared_schema(app.openapi(), case, response.status_code)

    if response.status_code == 204:
        assert schema is None, "a 204 declares a body, which no client can receive"
        assert not response.content
        return

    assert schema is not None, (
        f"{case.method.upper()} {case.template} answers {response.status_code} with a JSON body "
        "the document does not describe"
    )

    # Wrapped in `allOf` so a bare `{"$ref": ...}` stays a lone keyword while the
    # resolver still gets a root with `#/components/schemas/...` under it.
    root = {"allOf": [schema], "components": app.openapi()["components"]}
    validator = jsonschema.Draft202012Validator(root)
    errors = sorted(validator.iter_errors(response.json()), key=lambda error: error.json_path)
    assert not errors, (
        f"{case.method.upper()} {case.template} answered {response.status_code} with a body the "
        "published schema refuses:\n"
        + "\n".join(f"  {error.json_path}: {error.message}" for error in errors)
        + f"\nbody: {response.text[:300]}"
    )

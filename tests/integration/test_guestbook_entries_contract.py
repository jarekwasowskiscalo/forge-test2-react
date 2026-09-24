"""Every real response validates against the schema the document declares for it.

**What this proves that nothing else did.** `scripts/openapi_contract.py`
compares two documents; it never sends a request and never looks at a body. Its
subset design is deliberate and stays (`contracts/openapi/README.md` § The
contract is a SUBSET), but it leaves one class open: a response whose declared
schema is simply wrong. `contracts/openapi/guestbook.yaml` declared the PATCH
`422` with a `description` and no `content`, and a response with no `content`
hits `if wanted is None: continue` -- so it counted towards "10 responses
checked" while nothing about it was checked at all.

Underneath that, PATCH declared `422: {"model": Refusal}`, which REPLACES the
`HTTPValidationError` FastAPI would have generated. One of the six ways a PATCH
can be refused with 422 is a `Refusal`; the other five are Pydantic's list of
`{loc, msg, type}` coming through `app/core/errors.py`. A consumer reading the
generated types had no way to describe the shape it would see most often.

**So the assertion here is the one the other gate cannot make.** For each case:
send it, read the status code that actually came back, pull the schema the
published document declares for THAT operation and THAT code, and validate the
body against it with `$ref`s resolved. A test that asserted only
`response.status_code` -- as `test_guestbook_entries_router.py` reasonably does,
since it is asserting behaviour rather than shape -- cannot see any of this.

`app.openapi()` is the published document: the same object `scripts/dump_openapi.py`
writes to `openapi.json` and `frontend/src/api/schema.d.ts` is generated from. So
a divergence between the code and the generated types fails here, in one place,
for every operation at once.

FastAPI emits OpenAPI 3.1, whose schemas are JSON Schema 2020-12 -- which is why
`jsonschema` can read them directly and why the validator below is pinned to that
draft rather than left to be inferred.
"""

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import jsonschema
import pytest
from fastapi.testclient import TestClient

from app.contexts.guestbook.models.guestbook_entry import (
    AUTHOR_MAX_LENGTH,
    MESSAGE_MAX_LENGTH,
)
from app.main import app

ENTRIES = "/api/guestbook-entries"
ONE_ENTRY = "/api/guestbook-entries/{entry_id}"

#: A well-formed UUID that is deliberately not in the database. Distinct from a
#: malformed one: the first is a 404 about a missing entry, the second a 422
#: about an unreadable path parameter, and the two answer with different shapes.
ABSENT = "00000000-0000-4000-8000-000000000000"


@pytest.fixture(autouse=True)
def isolated_database(fresh_database):
    """Delegates to the shared fixture, which *discovers* every module holding a
    `SessionLocal` instead of naming three. Most cases below POST an entry to
    have something to address, and without this those rows would outlive the
    test -- the leak `tests/fitness/test_test_layout.py` refuses."""


@dataclass(frozen=True)
class Case:
    """One request, the template it was sent to, and the code it must answer."""

    #: Reads as a sentence in the parametrised test id, so a failure names the
    #: case rather than an index.
    name: str
    method: str
    #: The path as the DOCUMENT spells it, which is not the path that was sent:
    #: `openapi()` keys operations by template.
    template: str
    #: Given a live client, produce the concrete URL. A callable because a case
    #: that needs a stored entry has to create one first.
    url: Callable[[TestClient], str]
    status: int
    body: Any = None


def _created(client: TestClient) -> str:
    """POST one entry and return its id, so a 200/204 case has something to hit."""
    response = client.post(ENTRIES, json={"author": "Ada", "message": "Hello"})
    assert response.status_code == 201, response.text
    identifier: str = response.json()["id"]
    return identifier


CASES: tuple[Case, ...] = (
    # --- the six PATCH refusals: the finding this file was written for --------
    # Only the first is a Refusal. The rest are Pydantic's list, and the document
    # used to say every one of them was a Refusal.
    Case("patch_sets_no_field", "patch", ONE_ENTRY, lambda c: f"{ENTRIES}/{_created(c)}", 422, {}),
    Case(
        "patch_author_is_empty",
        "patch",
        ONE_ENTRY,
        lambda c: f"{ENTRIES}/{_created(c)}",
        422,
        {"author": ""},
    ),
    Case(
        "patch_author_is_too_long",
        "patch",
        ONE_ENTRY,
        lambda c: f"{ENTRIES}/{_created(c)}",
        422,
        {"author": "x" * (AUTHOR_MAX_LENGTH + 1)},
    ),
    Case(
        "patch_message_is_too_long",
        "patch",
        ONE_ENTRY,
        lambda c: f"{ENTRIES}/{_created(c)}",
        422,
        {"message": "y" * (MESSAGE_MAX_LENGTH + 1)},
    ),
    Case(
        "patch_author_is_the_wrong_type",
        "patch",
        ONE_ENTRY,
        lambda c: f"{ENTRIES}/{_created(c)}",
        422,
        {"author": 123},
    ),
    Case(
        "patch_id_is_not_a_uuid",
        "patch",
        ONE_ENTRY,
        lambda c: f"{ENTRIES}/not-a-uuid",
        422,
        {"author": "Ada"},
    ),
    Case(
        "patch_entry_is_absent",
        "patch",
        ONE_ENTRY,
        lambda c: f"{ENTRIES}/{ABSENT}",
        404,
        {"author": "Ada"},
    ),
    Case(
        "patch_succeeds",
        "patch",
        ONE_ENTRY,
        lambda c: f"{ENTRIES}/{_created(c)}",
        200,
        {"author": "Grace"},
    ),
    # --- the rest of the surface: green today, which is the point ------------
    # They cost one line each and they close the class rather than the instance,
    # so the next operation that declares a shape it does not return fails here.
    Case("health_answers", "get", "/api/health", lambda c: "/api/health", 200),
    Case("list_answers", "get", ENTRIES, lambda c: ENTRIES, 200),
    # `limit`, spelled as the route spells it. An unknown parameter is ignored
    # rather than refused, so a misspelt one here would assert nothing at all.
    Case("list_rejects_a_limit_below_one", "get", ENTRIES, lambda c: f"{ENTRIES}?limit=0", 422),
    Case(
        "list_rejects_a_limit_above_the_max", "get", ENTRIES, lambda c: f"{ENTRIES}?limit=101", 422
    ),
    Case("list_rejects_a_negative_offset", "get", ENTRIES, lambda c: f"{ENTRIES}?offset=-1", 422),
    Case("list_rejects_an_unknown_sort", "get", ENTRIES, lambda c: f"{ENTRIES}?sort=sideways", 422),
    Case(
        "create_succeeds", "post", ENTRIES, lambda c: ENTRIES, 201, {"author": "A", "message": "B"}
    ),
    Case(
        "create_rejects_an_empty_author",
        "post",
        ENTRIES,
        lambda c: ENTRIES,
        422,
        {"author": "", "message": "B"},
    ),
    Case("read_one_succeeds", "get", ONE_ENTRY, lambda c: f"{ENTRIES}/{_created(c)}", 200),
    Case("read_one_is_absent", "get", ONE_ENTRY, lambda c: f"{ENTRIES}/{ABSENT}", 404),
    Case("read_one_id_is_not_a_uuid", "get", ONE_ENTRY, lambda c: f"{ENTRIES}/not-a-uuid", 422),
    Case("delete_succeeds", "delete", ONE_ENTRY, lambda c: f"{ENTRIES}/{_created(c)}", 204),
    Case("delete_is_absent", "delete", ONE_ENTRY, lambda c: f"{ENTRIES}/{ABSENT}", 404),
    Case("delete_id_is_not_a_uuid", "delete", ONE_ENTRY, lambda c: f"{ENTRIES}/not-a-uuid", 422),
)


def _declared_schema(document: dict[str, Any], case: Case, status: int) -> Any:
    """The JSON body schema the document declares for this operation and code.

    `None` means the document declares no JSON body -- correct for a 204, and a
    finding for anything else, which is why the caller and not this function
    decides what it means.
    """
    responses = document["paths"][case.template][case.method]["responses"]
    assert str(status) in responses, (
        f"{case.method.upper()} {case.template} answered {status}, and the published "
        f"document declares no such response. A status raised without "
        f"`responses={{{status}: ...}}` on the decorator reaches neither openapi.json "
        f"nor frontend/src/api/schema.d.ts."
    )
    content = responses[str(status)].get("content")
    if not content or "application/json" not in content:
        return None
    return content["application/json"].get("schema")


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
def test_the_body_matches_the_schema_published_for_the_status_it_returned(
    client: TestClient, case: Case
) -> None:
    document = app.openapi()
    url = case.url(client)

    response = client.request(case.method.upper(), url, json=case.body)

    assert response.status_code == case.status, (
        f"expected {case.status} from {case.method.upper()} {url}, got "
        f"{response.status_code}: {response.text}"
    )

    schema = _declared_schema(document, case, response.status_code)

    if response.status_code == 204:
        assert schema is None, "a 204 declares a body, which no client can receive"
        assert not response.content
        return

    assert schema is not None, (
        f"{case.method.upper()} {case.template} answers {response.status_code} with a "
        "JSON body the document does not describe"
    )

    # `allOf` rather than merging the declared schema with `components` directly:
    # the declared schema is often a bare `{"$ref": ...}`, and wrapping keeps the
    # `$ref` a lone keyword while still giving the resolver a document root that
    # has `#/components/schemas/...` under it.
    root = {"allOf": [schema], "components": document["components"]}
    validator = jsonschema.Draft202012Validator(root)
    errors = sorted(validator.iter_errors(response.json()), key=lambda error: error.json_path)
    assert not errors, (
        f"{case.method.upper()} {case.template} answered {response.status_code} with a "
        f"body the published schema refuses:\n"
        + "\n".join(f"  {error.json_path}: {error.message}" for error in errors)
        + f"\nbody: {response.text}"
    )


def test_the_empty_patch_still_refuses_with_its_stable_code(client: TestClient) -> None:
    """The refusal code is the contract; widening the schema must not blur it.

    `contracts/openapi/guestbook.yaml` § `x-refusals` freezes
    `guestbook_entry_empty_patch`, and `frontend/src/api/problem.ts` mints it
    into `Problem.type` so a screen branches on the code and never on the
    sentence. A union that also admits Pydantic's list makes it possible for
    this to regress into the other shape without any schema noticing.
    """
    entry_id = _created(client)

    response = client.patch(f"{ENTRIES}/{entry_id}", json={})

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "guestbook_entry_empty_patch"


def test_a_malformed_id_and_a_missing_entry_answer_differently(client: TestClient) -> None:
    """The two cases a single `Refusal` declaration used to flatten together.

    Both are "the entry you named is not here" from a caller's seat, and they
    are different answers: an unreadable path parameter never reaches the
    router, so it carries no refusal code, while a well-formed id that is absent
    does. Asserted here because the parametrised test above validates each shape
    against its own schema and would pass if the two were swapped.
    """
    malformed = client.get(f"{ENTRIES}/not-a-uuid")
    absent = client.get(f"{ENTRIES}/{uuid.UUID(ABSENT)}")

    assert malformed.status_code == 422
    assert isinstance(malformed.json()["detail"], list)

    assert absent.status_code == 404
    assert absent.json()["detail"]["code"] == "guestbook_entry_not_found"

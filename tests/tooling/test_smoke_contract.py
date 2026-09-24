"""What a deploy's smoke asks, and the three ways an answer can be wrong.

The defect this module was written for is not that `scripts/deploy.sh` asked the wrong
path -- it is that **nothing could notice**. The question lived in one place and the
contract in another, the two disagreed from the day the first was typed, and the only
test near it asserted that a marker file existed. So the assertion that carries here is
the known positive at the bottom: over the repository's REAL `contracts/openapi/`, the
list endpoint is `/api/guestbook-entries` and its envelope is `items, total, total_all`.
That one would have been red the day the drift appeared.

The rest is the shape of the derivation and of the verdict, over hand-built documents --
no HTTP, no application, no account.
"""

import json
from typing import Any

import pytest
from openapi_contract import Contract, read_contracts
from smoke_contract import REPO_ROOT, Question, questions, verdict


def _contract(paths: dict[str, Any], schemas: dict[str, Any] | None = None) -> Contract:
    document: dict[str, Any] = {"paths": paths}
    if schemas is not None:
        document["components"] = {"schemas": schemas}
    return Contract(path="contracts/openapi/fixture.yaml", document=document, lines={})


PAGE = {"Page": {"type": "object", "required": ["items", "total", "total_all"]}}
LIST = {
    "get": {
        "parameters": [{"name": "limit", "in": "query"}, {"name": "q", "in": "query"}],
        "responses": {
            "200": {
                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Page"}}}
            }
        },
    }
}


def test_a_collection_read_is_asked_with_the_keys_its_contract_freezes() -> None:
    found = questions([_contract({"/api/things": LIST}, PAGE)])
    assert found == [Question("/api/things", "?limit=1", ("items", "total", "total_all"))]


def test_limit_is_appended_only_where_the_contract_declares_it() -> None:
    """The query string is derived too. A smoke that appends `?limit=1` to an endpoint
    that never declared the parameter is inventing a contract of its own."""
    bare = {"get": {"responses": {"200": {"content": {"application/json": {"schema": {}}}}}}}
    assert questions([_contract({"/api/health": bare})])[0].query == ""


def test_an_operation_with_a_path_parameter_is_not_asked() -> None:
    """`GET /api/things/{id}` cannot be asked of a deployment whose contents are
    unknown, and a smoke that invented an id would be asserting about a 404."""
    one = {
        "get": {
            "parameters": [{"name": "thing_id", "in": "path", "required": True}],
            "responses": {"200": {"content": {"application/json": {"schema": {}}}}},
        }
    }
    assert [
        question.path
        for question in questions(
            [_contract({"/api/things": LIST, "/api/things/{thing_id}": one}, PAGE)]
        )
    ] == ["/api/things"]


def test_a_write_is_not_asked() -> None:
    """Read-only is what makes a smoke safe against production, so the rule is
    structural rather than a list of paths somebody keeps up to date."""
    write = {"post": {"responses": {"201": {"content": {"application/json": {"schema": {}}}}}}}
    assert questions([_contract({"/api/things": write})]) == []


def test_an_unfrozen_body_is_still_asked_and_promises_nothing() -> None:
    """A contract may freeze the 200 and no field of it. That is a real answer -- the
    endpoint has to answer 200 -- and it must not be read as "no such endpoint"."""
    loose = {"get": {"responses": {"200": {"description": "something"}}}}
    assert questions([_contract({"/api/health": loose})]) == [Question("/api/health", "", ())]


def test_an_answer_that_honours_the_envelope_has_no_verdict() -> None:
    body = json.dumps({"items": [], "total": 0, "total_all": 0})
    assert verdict(body, ("items", "total", "total_all")) is None


def test_an_answer_that_is_not_json_is_told_apart_from_one_that_is() -> None:
    """**The verdict A03 never had**, which is why a wrong URL was reported as a wrong
    envelope. It states what arrived and does not say what caused it: the old message
    named a cause it had not observed, and an operator who believed it went looking in
    the application for a fault in the smoke."""
    failure = verdict('<!doctype html><div id="root"></div>', ("items",))
    assert failure is not None
    assert "not JSON" in failure
    assert '<!doctype html><div id="root"></div>' in failure
    assert "items" not in failure


def test_the_media_type_is_reported_when_one_was_observed() -> None:
    """Evidence rather than narration. `text/html` is what says an answer came from
    something other than the API, and it is read off the response rather than assumed
    from the shape of the path."""
    failure = verdict("<html>", ("items",), "text/html")
    assert failure is not None
    assert "text/html" in failure
    assert verdict("<html>", ("items",)) != failure


def test_an_answer_missing_a_key_names_every_key_it_is_missing() -> None:
    failure = verdict(json.dumps({"items": []}), ("items", "total", "total_all"))
    assert failure is not None
    assert "total, total_all" in failure
    assert "not JSON" not in failure


def test_the_three_failures_are_three_different_sentences() -> None:
    """Told apart because they are repaired in three different places. The shell sees
    the first one -- no answer at all -- and these are the two this module owns."""
    not_json = verdict("<html>", ("items",))
    missing = verdict(json.dumps({}), ("items",))
    assert not_json != missing
    assert verdict(json.dumps([]), ("items",)) not in (not_json, missing)


@pytest.fixture
def declared() -> list[Question]:
    contracts, findings = read_contracts(REPO_ROOT / "contracts" / "openapi", REPO_ROOT)
    assert findings == [], findings
    return questions(contracts)


def test_the_real_contracts_name_the_collection_the_application_serves(
    declared: list[Question],
) -> None:
    """The known positive, and the assertion that was missing for as long as the drift
    lasted: `deploy.sh` asked `/api/entries` for a field `matching`, and the contract
    had said `/api/guestbook-entries` with `total_all` since before either was typed."""
    assert (
        Question("/api/guestbook-entries", "?limit=1", ("items", "total", "total_all")) in declared
    )


def test_the_real_contracts_name_the_health_probe(declared: list[Question]) -> None:
    """`environment` and `version` are frozen in that body so somebody can ask which
    release answered. Nothing was checking they arrive."""
    assert Question("/api/health", "", ("status", "environment", "version")) in declared


def test_no_endpoint_the_smoke_would_ask_takes_a_path_parameter(
    declared: list[Question],
) -> None:
    assert [question for question in declared if "{" in question.path] == []


def test_the_smoke_has_something_to_ask(declared: list[Question]) -> None:
    """A smoke with an empty plan passes everything, which is the shape of the defect
    being repaired. `deploy.sh` refuses on an empty plan; this is the other half."""
    assert declared

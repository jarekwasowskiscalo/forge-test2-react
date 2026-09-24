"""The two comparisons the contract checker could not make, and now can.

`scripts/openapi_contract.py` had no test of any kind, though its own docstring said
a suite drove it "over hand-built pairs without starting anything". Nothing imported
it. That absence is not incidental to the two holes below -- it is how they survived:

- **A parameter's `schema` was parsed and then never read.** `_compare_operation`
  matched a parameter by name and compared exactly `in` and `required`, so a `$ref`
  written under one froze nothing. The `$ref` is the half that carries: it gives a
  closed set a NAME, and the name is what `frontend/src/api/schema.d.ts` renders as a
  union the browser compiles against.
- **A schema with no `properties` was compared against nothing at all.**
  `_compare_schema` walked `properties` and returned clean when there were none, so
  `GuestbookEntrySort` -- a bare `type` plus an `enum`, the one schema in the tree
  shaped that way -- declared a closed set that no check had ever read.

Both are asserted here in both directions. A checker tested only for what it accepts
is half a checker: the failure that matters is the one where it stops objecting.

Hand-built pairs, no application, no database -- which is what makes this cheap enough
to run in the leg that has neither.
"""

from typing import Any

import openapi_contract

_PATH = "/api/things"


def _contract(document: dict[str, Any]) -> openapi_contract.Contract:
    """A contract with no line index. Every line reports as 0, and nothing here reads it."""
    return openapi_contract.Contract(
        path="contracts/openapi/fixture.yaml", document=document, lines={}
    )


def _pair(
    parameter: dict[str, Any],
    dump_parameter: dict[str, Any],
    schemas: dict[str, Any] | None = None,
    dump_schemas: dict[str, Any] | None = None,
) -> list[openapi_contract.Finding]:
    contract = _contract(
        {
            "paths": {_PATH: {"get": {"parameters": [parameter], "responses": {}}}},
            "components": {"schemas": schemas or {}},
        }
    )
    dump = {
        "paths": {_PATH: {"get": {"parameters": [dump_parameter], "responses": {}}}},
        "components": {"schemas": dump_schemas or {}},
    }
    return openapi_contract.compare([contract], dump, router_source="")


_SORT = {"name": "sort", "in": "query", "required": False}
_REF = {"$ref": "#/components/schemas/ThingSort"}


def test_a_parameter_pointed_at_the_schema_the_dump_uses_is_no_finding() -> None:
    assert _pair({**_SORT, "schema": _REF}, {**_SORT, "schema": _REF}) == []


def test_a_parameter_pointed_at_another_schema_is_caught() -> None:
    """The drift this exists for: the contract names one type, the application another."""
    findings = _pair(
        {**_SORT, "schema": _REF},
        {**_SORT, "schema": {"$ref": "#/components/schemas/SomethingElse"}},
    )
    assert len(findings) == 1, findings
    assert "points sort at the schema ThingSort" in findings[0].message
    assert "SomethingElse" in findings[0].message


def test_a_parameter_schema_the_dump_inlines_instead_of_naming_is_caught() -> None:
    """An inlined enum is not the same promise -- it reaches the browser as a bare union."""
    findings = _pair(
        {**_SORT, "schema": _REF},
        {**_SORT, "schema": {"type": "string", "enum": ["newest", "oldest"]}},
    )
    assert len(findings) == 1, findings
    assert "None" in findings[0].message


def test_a_parameter_with_no_schema_in_the_contract_freezes_none() -> None:
    """The contract gets exactly what it wrote. Silence is not a claim about the type."""
    assert _pair(_SORT, {**_SORT, "schema": {"type": "integer"}}) == []


def test_a_constraint_written_on_a_parameter_is_compared() -> None:
    findings = _pair(
        {**_SORT, "schema": {"maxLength": 200}},
        {**_SORT, "schema": {"maxLength": 500}},
    )
    assert len(findings) == 1, findings
    assert "maxLength" in findings[0].message


def _schema_pair(declared: dict[str, Any], found: dict[str, Any]) -> list[openapi_contract.Finding]:
    contract = _contract({"paths": {}, "components": {"schemas": {"ThingSort": declared}}})
    return openapi_contract.compare(
        [contract],
        {"paths": {}, "components": {"schemas": {"ThingSort": found}}},
        router_source="",
    )


_CLOSED = {"type": "string", "enum": ["newest", "oldest"]}


def test_a_closed_set_that_agrees_is_no_finding() -> None:
    assert _schema_pair(_CLOSED, dict(_CLOSED)) == []


def test_a_closed_set_the_application_has_widened_is_caught() -> None:
    """The direction that matters. A third word accepted by the code and not by the
    contract is exactly the drift a hand-written contract exists to notice, and for as
    long as this schema had no `properties` the checker returned clean on it."""
    findings = _schema_pair(_CLOSED, {"type": "string", "enum": ["newest", "oldest", "random"]})
    assert len(findings) == 1, findings
    assert "freezes enum" in findings[0].message
    assert "ThingSort" in findings[0].message


def test_a_scalar_alias_whose_type_changed_underneath_is_caught() -> None:
    findings = _schema_pair({"type": "string"}, {"type": "integer"})
    assert len(findings) == 1, findings
    assert "freezes type 'string'" in findings[0].message


def test_a_schema_root_says_nothing_when_the_contract_writes_nothing() -> None:
    assert _schema_pair({"properties": {}}, {"type": "object", "enum": ["anything"]}) == []


def test_the_scale_counts_the_parameters_it_now_reads() -> None:
    """The scale line is the reader's only measure of how much a contract froze, so a
    sentence that started being checked has to start being counted."""
    contract = _contract(
        {"paths": {_PATH: {"get": {"parameters": [_SORT, _SORT], "responses": {}}}}}
    )
    assert openapi_contract.scale([contract])["parameters"] == 2

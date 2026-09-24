"""A repair round dispatches the authors the repair's own scope needs, and no others.

`.specconf/process.json` § `fix_conditional` is the only table that narrows a repair tail,
and until 2026-09-23 it carried nothing from the requirements family. A member absent from
the union of `conditional` and `fix_conditional` always runs, so a `review_fix` return to
`requirements` sent `cr-impact`, `cr-requirements` and `cr-scenarios` unconditionally -- on
the other stack that round cost $40.94, as much as the original change
(Scalo-Sales-Engineering-Consulting/claude-marketplace#196).

The arithmetic these tests run is the engine's, in one line: a member runs when it is absent
from `conditional | fix_conditional`, or when the scope lights one of its signals. It is
re-implemented here rather than asked of the engine because this suite reads files and never
the process -- the dependency runs one way (`CLAUDE.md`).

What each case holds is a property of THIS profile's values, so the day somebody adds a
signal, a worker or a member, one of them says which sentence stopped being true.
"""

import json
import pathlib
from typing import Final

from tests._repo import REPO_ROOT

PROCESS: Final[pathlib.Path] = REPO_ROOT / ".specconf" / "process.json"
STACK: Final[pathlib.Path] = REPO_ROOT / ".specconf" / "stack.json"

#: Who writes each artefact a worker may declare in `requires`.
PRODUCERS: Final[dict[str, str]] = {
    "impact.md": "cr-impact",
    "requirements.md": "cr-requirements",
    "scenarios.md": "cr-scenarios",
}

#: The one fact copied from the process. This stack's own workers declare `requires` in
#: `.specconf/stack.json`; `build-tests-uat` is the engine's and declares its own in the
#: plugin's catalogue. It is copied because this repository may not read the process.
ENGINE_REQUIRES: Final[dict[str, list[str]]] = {
    "build-tests-uat": ["requirements.md", "scenarios.md"],
}

REQUIREMENTS_FAMILY: Final = ("cr-impact", "cr-requirements", "cr-scenarios")


def _load(path: pathlib.Path) -> dict[str, object]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _section(document: dict[str, object], name: str) -> dict[str, object]:
    """A named object with its `$comment` prose removed."""
    body = document[name]
    assert isinstance(body, dict)
    return {key: value for key, value in body.items() if key != "$comment"}


def _signals_of(value: object) -> frozenset[str]:
    """The profile writes one signal as a string and several as a list; both are `any_of`."""
    if isinstance(value, str):
        return frozenset({value})
    assert isinstance(value, list)
    return frozenset(str(item) for item in value)


def _every_signal() -> frozenset[str]:
    """The engine's six, described under `detection.signals`, and this stack's own."""
    process, stack = _load(PROCESS), _load(STACK)
    detection = process["detection"]
    assert isinstance(detection, dict)
    return frozenset(_section(detection, "signals")) | frozenset(_section(stack, "signals"))


def _tail_table(fix_conditional: dict[str, object] | None = None) -> dict[str, frozenset[str]]:
    """The two tables the tail reads, merged as the engine merges them: an entry in
    `fix_conditional` wins over the same name in `conditional`."""
    process = _load(PROCESS)
    merged = {name: _signals_of(v) for name, v in _section(process, "conditional").items()}
    fixes = _section(process, "fix_conditional") if fix_conditional is None else fix_conditional
    merged.update({name: _signals_of(v) for name, v in fixes.items()})
    return merged


def _repair_members(tier: str, stage: str, lit: set[str]) -> list[str]:
    """The members of `stage` on `tier` that a repair scoped to `lit` dispatches."""
    table = _tail_table()
    tiers = _section(_load(PROCESS), "tiers")
    body = tiers[tier]
    assert isinstance(body, dict)
    declared = _section(body, "steps")[stage]
    assert isinstance(declared, list)
    return [name for name in declared if name not in table or table[name] & lit]


def _orphans(table: dict[str, frozenset[str]]) -> list[str]:
    """Every consumer that a scope can dispatch while leaving the author of its input home."""
    requires = dict(ENGINE_REQUIRES)
    for name, body in _section(_load(STACK), "skills").items():
        assert isinstance(body, dict)
        if body.get("kind") == "worker":
            requires[name] = [str(item) for item in body.get("requires") or []]

    # A member in neither table runs on every scope, so its author must too.
    every = _every_signal()
    orphans = []
    for consumer, artefacts in sorted(requires.items()):
        for artefact in artefacts:
            producer = PRODUCERS.get(artefact)
            if producer is None:
                continue
            uncovered = table.get(consumer, every) - table.get(producer, every)
            if uncovered:
                orphans.append(
                    f"{consumer} requires {artefact} and outruns {producer} on "
                    f"{', '.join(sorted(uncovered))}"
                )
    return orphans


def test_a_repair_that_moves_no_backend_and_no_surface_sends_one_author_not_three() -> None:
    for scope in ({"frontend_touched"}, {"tooling_touched"}, {"infra_touched"}, {"ci_touched"}):
        assert _repair_members("p2", "requirements", scope) == ["cr-requirements"], (
            f"a repair scoped to {sorted(scope)} re-describes no area and moves no scenario, "
            "and the requirements family is the fan-out a repair must not re-enter whole"
        )


def test_a_backend_repair_keeps_the_author_of_its_fixture_values() -> None:
    """Not a missed narrowing. `build-tests-integration` requires `scenarios.md` and its
    skill refuses to invent a fixture value -- they come from `scenarios.md § Test data`.
    A backend repair dispatches it, so it dispatches the author of that section too."""
    assert _repair_members("p2", "requirements", {"backend_touched"}) == [
        "cr-requirements",
        "cr-scenarios",
    ]


def test_a_repair_that_moves_behaviour_keeps_the_author_of_what_it_moves() -> None:
    assert "cr-scenarios" in _repair_members("p2", "requirements", {"screen_touched"}), (
        "a screen is behaviour somebody outside the code can see"
    )
    assert "cr-impact" in _repair_members("p2", "requirements", {"new_context"}), (
        "a concept in no context and in no glossary is an area no impact.md in the record "
        "can already describe"
    )
    assert "cr-impact" not in _repair_members("p2", "requirements", {"rule_touched"}), (
        "impact.md records how the area worked BEFORE the change; a repair inside the same "
        "context does not move the past"
    )


def test_no_consumer_goes_out_without_the_author_of_what_it_requires() -> None:
    orphans = _orphans(_tail_table())
    assert not orphans, (
        "a repair scoped to one of these signals dispatches the consumer and leaves the author "
        f"of its input at home, so it writes against last round's document: {orphans}"
    )


def test_the_orphan_detector_finds_the_orphan_it_exists_to_find() -> None:
    """The known positive: the entry exactly as flutter writes it, which lacks the
    `backend_touched` this stack's integration author needs."""
    fixes = _section(_load(PROCESS), "fix_conditional")
    fixes["cr-scenarios"] = ["contract_touched", "screen_touched", "schema_touched", "rule_touched"]
    assert any(
        orphan.startswith("build-tests-integration requires scenarios.md")
        and "backend_touched" in orphan
        for orphan in _orphans(_tail_table(fixes))
    ), "the detector missed a narrowing that leaves build-tests-integration with no fixtures"


def test_cr_requirements_carries_every_signal_this_stack_declares() -> None:
    """`design-spec` requires requirements.md and runs unconditionally, so every scope that
    reaches the design stage needs the requirement. Written out rather than left absent:
    absence and completeness read the same to the engine and differently to a person."""
    fixes = _section(_load(PROCESS), "fix_conditional")
    assert "cr-requirements" in fixes, "absent reads as 'nobody measured'"
    assert _signals_of(fixes["cr-requirements"]) == _every_signal(), (
        "a signal was added to the profile and this line was not decided again: either it "
        "belongs here, or say in the $comment why a repair that lights it needs no requirement"
    )


def test_the_first_pass_through_requirements_is_untouched_by_the_tail() -> None:
    """`fix_conditional` is consulted only when the composition comes from a fix's scope. A
    `cr-*` name in `conditional` would narrow the ORIGINAL change too -- a decision nobody took."""
    ordinary = set(_section(_load(PROCESS), "conditional"))
    assert not ordinary & set(REQUIREMENTS_FAMILY), (
        "a change with no requirements author has no requirement for any test to cite"
    )

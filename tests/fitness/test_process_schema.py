"""The process profile declares the schema under which its own keys mean what they say.

`tiers.*.max_lines` was a per-artefact line budget. The audit of 2026-09-20 measured all six
on one change: every one was exceeded, `delta.md` by 24x, and every stage closed anyway. The
engine printed a multiplier and refused nothing, so the numbers were advice wearing the shape
of a rule. This stack's numbers were also byte-identical to the Flutter template's, so they
had been copied, not measured. `claude-marketplace#204` withdrew the key instead of raising
the numbers. `delta.md` is now bounded by what it IS: the brief, one entry per path, with
everything an earlier pass said assembled beside it into `delta-history.md`.

The withdrawal has a window. At schema 5 the key loads, nothing reads it, and the engine names
it as withdrawn; at 6 it is refused. So the engine already refuses a profile that declares 6
and still carries the key. What it cannot see is a profile that quietly walks back to 5 to keep
one. These two tests guard exactly that, and they read the file rather than asking the process,
because the dependency runs one way (`CLAUDE.md`).
"""

import json
import pathlib
from typing import Final

REPO_ROOT: Final[pathlib.Path] = pathlib.Path(__file__).resolve().parents[2]
PROCESS: Final[pathlib.Path] = REPO_ROOT / ".specconf" / "process.json"

#: The first schema that refuses `max_lines` -- the engine's
#: `process_config.MAX_LINES_WITHDRAWN_AT`. Written out, because a value read from the engine
#: would be an import of the process, which nothing under `tests/` makes.
WITHDRAWN_AT: Final = 6


def _process() -> dict[str, object]:
    loaded: dict[str, object] = json.loads(PROCESS.read_text(encoding="utf-8"))
    return loaded


def test_the_profile_declares_the_schema_that_refuses_the_withdrawn_budget() -> None:
    version = _process()["schema_version"]
    assert isinstance(version, int) and version >= WITHDRAWN_AT, (
        f"process.json declares schema {version!r}. Schema {WITHDRAWN_AT} is where the engine "
        "refuses tiers.*.max_lines; below it the key loads and is only named, so a budget could "
        "return without a refusal."
    )


def test_no_tier_carries_a_line_budget_for_an_artefact() -> None:
    tiers = _process()["tiers"]
    assert isinstance(tiers, dict)
    compositions = {name: body for name, body in tiers.items() if name != "$comment"}
    assert compositions, "the profile composes no tier"
    carrying = sorted(
        name
        for name, body in compositions.items()
        if isinstance(body, dict) and "max_lines" in body
    )
    assert carrying == [], (
        f"tiers {carrying} carry max_lines, withdrawn by claude-marketplace#204: a budget that "
        "printed a multiplier and refused nothing was exceeded six times out of six, and an "
        "artefact nobody can shorten is a finding about the skill that writes it, not a line "
        "to trim"
    )

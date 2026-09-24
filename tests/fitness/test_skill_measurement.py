"""Every skill of this template is inside the discipline measurement, and each one names the rule.

The engine counts improvisation and article XII breaches from a transcript, hours after the
session that committed them. Until `claude-marketplace#211` it counted only the **parent
conversation's** calls: 30 of 286 in one measured session, while 3 622 of 5 201 requests ran
inside dispatched subagents, that is, inside skills like the ones declared here. The number it
reported was a lower bound, not a measurement.

The engine's half of the fix widened the scope, and it now reads every dispatch. This
repository's half is the tests below. The stack says which of its skills are in the
measurement, and each one cites the rule rather than relying on the session it happens to be
loaded in, because someone charged with breaking a rule must have had somewhere to read it. The
`build-*` skills reach it through the worker contract that every dispatch hands them. The
`run-*` skills are loaded in the main conversation and get nothing from a dispatch, so they cite
it themselves.

The declaration is the tree: every directory under `.claude/skills/` is in the measurement, and
no skill can opt out. A `measured` key in `.specconf/stack.json` would be refused by the engine,
which allows an `operational` skill nothing but `kind`, so the declaration lives in the document
the model reads.
"""

import pathlib
import re
from typing import Final

REPO_ROOT: Final[pathlib.Path] = pathlib.Path(__file__).resolve().parents[2]
SKILLS: Final[pathlib.Path] = REPO_ROOT / ".claude" / "skills"

#: The marker every skill document opens its declaration with. One string, so that the
#: declaration can be found rather than recognised.
MARKER: Final = "**Measured.**"

#: The rule a measured skill is charged against, cited by file name.
RULE: Final = "process-failure.md"

#: A skill cites the process's documents at the plugin root, never at a path that is right
#: only where the plugin happens to be unpacked.
PLUGIN_ROOT: Final = "${CLAUDE_PLUGIN_ROOT}/skills/_shared/"

#: An instruction to open a skill document by path: a skill is loaded, not read.
_READ_BY_PATH: Final = re.compile(
    r"\b(Read|cat|grep|sed|head|tail|open)\b[^\n]{0,60}?\.claude/skills/\S*\.md"
)


def _documents() -> dict[str, str]:
    return {
        skill.name: (skill / "SKILL.md").read_text(encoding="utf-8")
        for skill in sorted(SKILLS.iterdir())
        if skill.is_dir() and not skill.name.startswith("_")
    }


def test_there_are_skills_to_measure_at_all() -> None:
    assert _documents(), (
        "no skill under .claude/skills/ -- every assertion below would be vacuously true"
    )


def test_every_skill_declares_that_it_is_inside_the_measurement() -> None:
    silent = [name for name, text in _documents().items() if MARKER not in text]
    assert silent == [], (
        f"{silent} never say they are measured. The engine reads the calls of the parent "
        "conversation and of every dispatch; a skill whose document never says so leaves "
        "whoever loads it to discover the rule from the count."
    )


def test_every_skill_names_the_rule_it_is_charged_against() -> None:
    unread = [name for name, text in _documents().items() if RULE not in text]
    assert unread == [], (
        f"{unread} do not cite {RULE}. Accountability without a readable rule is what the "
        "audit found: 66 of 69 charges in one session fell on a reader that was never "
        "pointed at it."
    )


def test_the_rule_is_cited_at_the_plugin_root_never_opened_by_path() -> None:
    offenders: list[str] = []
    for name, text in _documents().items():
        if PLUGIN_ROOT not in text:
            offenders.append(f"{name}: cites the rule without the ${{CLAUDE_PLUGIN_ROOT}} form")
        if _READ_BY_PATH.search(text):
            offenders.append(f"{name}: instructs a read of a skill document by path")
    assert offenders == [], "\n".join(offenders)

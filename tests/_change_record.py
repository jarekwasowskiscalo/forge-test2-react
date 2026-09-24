"""What a change record declares, and what is still the form the scaffold copied into place.

The change process opens a change by copying every file of its record from the forms under
`.specconf/templates/change/`, and each form opens by declaring itself absent:
`<!-- TEMPLATE: ... the file counts as non-existent until this marker is gone -->`. A reader
that judges a form judges the scaffold, and the scaffold's placeholders are nobody's
declaration -- `requirements.md` ships with `### R-1: <area>` and `### R-2: <area>` in it, so a
reader without this rule reports two requirements the moment a change is opened, before anybody
has written one. `spec/changes/CR-2609-8ef9-*` is such a record today.

**This is the template's own readiness contract, not a copy of the process.** Nothing under
`tests/` may call the engine, so the rule is read off the marker the form itself carries. The
same rule already has a reader here -- `scripts/changelog.sh` refuses an entry that still carries
the marker "so it counts as unwritten" -- and this module is where it is written down for the
suites. `tests/fitness/test_requirement_citations.py` proves the seed is recognised.

Deliberately narrow: only a recognised scaffold declares nothing. A document whose marker has
been removed is read in full at every stage.

Imports nothing but `pathlib`, `re` and `typing`.
"""

import pathlib
import re
from typing import Final

#: The opening of every form the scaffold copies, and the whole of the contract: a change
#: document carrying this counts as non-existent. Matched at the start of a line, as
#: `scripts/changelog.sh` matches it.
SCAFFOLD_MARKER: Final = "<!-- TEMPLATE:"

#: The change half of a qualified requirement id -- and the prefix a record's directory is
#: addressed by, because the slug after it is a convenience for a reader and no part of the id.
CHANGE_ID: Final = r"CR-\d{4}-[0-9a-f]{4}"

#: The declaration form, the traceability gate's own (`traceability.py` `_DECLARED`). Copied
#: rather than approximated: a heading this reads and the gate does not would pass here and
#: refuse there, and a copy keeps the drift visible in a diff instead of silent.
_DECLARED: Final = re.compile(r"^(?P<hashes>#{2,4})\s+(?P<rid>R-\d+)\b", re.MULTILINE)

#: Guidance is not content: the forms carry their instructions in HTML comments, and the gate
#: strips them before it reads (`verify_lib.strip_comments`). Replaced with a space rather than
#: deleted, so an inline comment between two words cannot weld them into one.
_HTML_COMMENT: Final = re.compile(r"<!--.*?-->", re.DOTALL)

_RECORD_DIRECTORY: Final = re.compile(rf"^({CHANGE_ID})")


def is_still_a_form(text: str) -> bool:
    """Whether `text` is still the form the scaffold wrote."""
    return any(line.startswith(SCAFFOLD_MARKER) for line in text.splitlines())


def declared_requirements(text: str) -> frozenset[str]:
    """The requirement ids (`R-n`) a `requirements.md` declares -- none while it is a form."""
    if is_still_a_form(text):
        return frozenset()
    stripped = _HTML_COMMENT.sub(" ", text)
    return frozenset(match.group("rid") for match in _DECLARED.finditer(stripped))


def requirements_by_change(changes: pathlib.Path) -> dict[str, frozenset[str]]:
    """`{CR-YYMM-xxxx -> the R-n its record declares}` for every record under `changes`.

    A record with no `requirements.md` is present and declares nothing, which is a different
    answer from a record that is absent: a citation of the first names a missing requirement,
    a citation of the second names a missing change.
    """
    if not changes.is_dir():
        return {}
    by_change: dict[str, frozenset[str]] = {}
    for record in sorted(changes.iterdir()):
        matched = _RECORD_DIRECTORY.match(record.name)
        if not record.is_dir() or matched is None:
            continue
        requirements = record / "requirements.md"
        by_change[matched.group(1)] = (
            declared_requirements(requirements.read_text(encoding="utf-8"))
            if requirements.is_file()
            else frozenset()
        )
    return by_change

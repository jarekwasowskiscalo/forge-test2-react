"""`CLAUDE.md` says *that* a process fault is filed, never *where* or *under which label*.

Neither is a property of this stack. `sdd-ownership` computes both from GitHub's own record
of the lineage -- one label from a template, another from a repository created from it -- and
the `fault-report` skill runs it, fills the form and creates the issue. A label written into a
page is a value that was right once: fourteen issues in the marketplace register carry the
template's label and were raised from an instance, which is what a value typed from memory
looks like a year later.

Who may post outward is settled upstream, in `process-failure.md` § Which document wins, and
this page is the one that loses: it cites the winner rather than ranking itself in words of
its own (claude-marketplace#206).
"""

import pathlib
from typing import Final

REPO_ROOT: Final[pathlib.Path] = pathlib.Path(__file__).resolve().parents[2]
PAGE: Final[pathlib.Path] = REPO_ROOT / "CLAUDE.md"

#: The two labels `sdd-ownership` chooses between. Written out, because the test exists to
#: keep them OUT of the page, and a value read from the page would agree with anything.
COMPUTED_LABELS: Final = ("from-template", "from-instance")


def _page() -> str:
    return PAGE.read_text(encoding="utf-8")


def test_the_page_names_the_skill_that_files_a_process_fault() -> None:
    assert "fault-report" in _page(), (
        "CLAUDE.md does not name the fault-report skill. The skill fills the form and computes "
        "the destination; a page that spells the command out instead is a second copy of it."
    )


def test_the_page_writes_no_ownership_label_down() -> None:
    offenders: list[str] = []
    for number, line in enumerate(_page().splitlines(), start=1):
        offenders += [
            f"CLAUDE.md:{number}: {label} is computed, not written"
            for label in COMPUTED_LABELS
            if label in line
        ]
        if "gh issue create" in line and "--label" in line:
            offenders.append(f"CLAUDE.md:{number}: a label typed onto gh issue create")
    assert offenders == [], "sdd-ownership prints the label; this page does not know it:\n" + (
        "\n".join(offenders)
    )


def test_the_page_cites_the_document_that_outranks_it() -> None:
    assert "process-failure.md" in _page(), (
        "CLAUDE.md does not cite process-failure.md. Who may post outward is a property of the "
        "process, not of this stack; the loser cites the winner instead of ranking itself."
    )

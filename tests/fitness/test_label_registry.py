"""The labels the automation branches on, held against the file that declares them.

A label is a repository setting. `git` has never seen one, a clone carries none, and a
repository made from this template starts with GitHub's defaults -- so a `case` arm or an
`if:` that waits for one is inert until an admin creates it, and inert *silently*: a branch
that is never taken reads exactly like a rule nobody reached for. Three documents promised
the `no-changelog` exemption for two days in a repository where the label did not exist, and
nothing was red, because nothing on either side knew the other existed.

`.github/labels.md` is the side that can be checked. This module refuses a disagreement
between it and the automation in either direction -- a label branched on and not declared, a
row nothing branches on, a row whose cited document has stopped naming its label.

**What it cannot do, stated rather than implied.** It cannot ask GitHub whether the labels
exist. That needs the API, this suite takes no network by construction (`conftest.py`), and a
test that reached for one would be red on an aeroplane and on every fork without a token.
The registry carries a dated claim for that half and this module holds the date's *shape*;
the value of the claim is the reader's to re-check, in the one command the file gives them.

Parsed with anchored regexes and no YAML parser, for the reason `test_ci_parity.py` gives:
PyYAML is not a dependency, and the shapes read here are closed. The cost is named in each
assertion message -- when the automation's shape changes, update the parser in the same
commit.
"""

import datetime as dt
import pathlib
import re
from typing import Final

from tests._repo import REPO_ROOT

_REGISTRY: Final[pathlib.Path] = REPO_ROOT / ".github" / "labels.md"
_WORKFLOW: Final[pathlib.Path] = REPO_ROOT / ".github" / "workflows" / "ci.yml"
_CHANGELOG: Final[pathlib.Path] = REPO_ROOT / "scripts" / "changelog.sh"
_DEPENDABOT: Final[pathlib.Path] = REPO_ROOT / ".github" / "dependabot.yml"

#: A row of the registry's table: the label in the first cell, the document that owns its
#: meaning in the last. The two middle cells are prose and are not read -- what a label does
#: is a sentence, and a test that graded sentences is one nobody could satisfy.
_ROW: Final = re.compile(
    r"^\| `(?P<label>[a-z0-9][a-z0-9-]*)` \|[^|]*\|[^|]*\| `(?P<document>[^`]+)` \|$",
    re.MULTILINE,
)

#: The dated claim about the half no offline test can reach.
_VERIFIED: Final = re.compile(
    r"^\*\*Last verified against the live repository: (\d{4}-\d{2}-\d{2})\*\*", re.MULTILINE
)

#: A workflow condition that reads one label off the event payload.
_WORKFLOW_CONDITION: Final = re.compile(
    r"contains\(\s*github\.event\.pull_request\.labels\.\*\.name\s*,\s*'([^']+)'\s*\)"
)

#: The head of the `case` in `changelog.sh` that matches the names CI hands it. Sliced to
#: first, because the same file has two other `case` statements and one of them matches a
#: variable in the same shape.
_LABEL_CASE: Final = re.compile(r'^\s*case\s+"[^"]*\$\{labels[^"]*"\s+in\s*$', re.MULTILINE)

#: One arm of that `case`: a literal label between the glob's two spaces.
_CASE_ARM: Final = re.compile(r'^\s*\*"\s*([a-z0-9][a-z0-9-]*)\s*"\*\)', re.MULTILINE)

#: A `labels:` key in `dependabot.yml`, inline or block. Nothing sets one today -- the file
#: says at length why the `spec-exempt` it used to carry was removed -- so this scanner is
#: proved on a fabricated positive below. A scanner with no positive at all is how the next
#: standing label slips in unread.
_DEPENDABOT_INLINE: Final = re.compile(r"^\s*labels:\s*\[(?P<items>[^\]]*)\]\s*$", re.MULTILINE)
_DEPENDABOT_BLOCK: Final = re.compile(r"^(?P<indent>\s*)labels:\s*$", re.MULTILINE)
_LIST_ITEM: Final = re.compile(r'^\s*-\s*["\']?(?P<name>[a-z0-9][a-z0-9 -]*?)["\']?\s*$')


def _declared() -> dict[str, str]:
    """`{label: the document that owns its meaning}`, from the registry's table."""
    return {
        match.group("label"): match.group("document")
        for match in _ROW.finditer(_REGISTRY.read_text(encoding="utf-8"))
    }


def _workflow_labels(text: str) -> set[str]:
    """Every label a job's `if:` or a step's input reads off the pull request."""
    return set(_WORKFLOW_CONDITION.findall(text))


def _changelog_labels(text: str) -> set[str]:
    """Every label the changelog gate waives itself on."""
    head = _LABEL_CASE.search(text)
    assert head is not None, (
        f"{_CHANGELOG} no longer matches its labels with a `case` over ${{labels}} -- the "
        "exemption may have moved, and this parser has to move with it"
    )
    block, _, _ = text[head.end() :].partition("esac")
    return set(_CASE_ARM.findall(block))


def _dependabot_labels(text: str) -> set[str]:
    """Every label the bot would put on the pull requests it opens."""
    found: set[str] = set()
    for match in _DEPENDABOT_INLINE.finditer(text):
        found.update(
            item.strip().strip("\"'") for item in match.group("items").split(",") if item.strip()
        )
    lines = text.splitlines()
    for match in _DEPENDABOT_BLOCK.finditer(text):
        start = text[: match.start()].count("\n") + 1
        indent = len(match.group("indent"))
        for line in lines[start:]:
            if not line.strip() or line.strip().startswith("#"):
                continue
            if len(line) - len(line.lstrip()) <= indent and not line.lstrip().startswith("-"):
                break
            item = _LIST_ITEM.match(line)
            if item is None:
                break
            found.add(item.group("name"))
    return found


def _branched_on() -> dict[str, set[str]]:
    """`{label: the files whose behaviour turns on it}` -- the whole automation."""
    sources: dict[pathlib.Path, set[str]] = {
        _WORKFLOW: _workflow_labels(_WORKFLOW.read_text(encoding="utf-8")),
        _CHANGELOG: _changelog_labels(_CHANGELOG.read_text(encoding="utf-8")),
        _DEPENDABOT: _dependabot_labels(_DEPENDABOT.read_text(encoding="utf-8")),
    }
    found: dict[str, set[str]] = {}
    for path, labels in sources.items():
        for label in labels:
            found.setdefault(label, set()).add(str(path.relative_to(REPO_ROOT)))
    return found


def test_every_row_of_the_registry_parses() -> None:
    """Proved first, because every rule below is vacuous over a table nobody can parse.

    A registry renamed, or rewritten into a shape `_ROW` does not match, would otherwise
    turn this whole module green -- the failure it exists to prevent.

    What is checked is that no row is *skipped*, never how many rows there are. A count
    would make retiring a label -- taking its branch out of the automation and its row out
    of here, which is a correct thing to do -- fail as though it were the defect.
    """
    assert _REGISTRY.is_file(), f"{_REGISTRY} is gone, and with it the only declared list"
    lines = [
        line
        for line in _REGISTRY.read_text(encoding="utf-8").splitlines()
        if line.startswith("|") and not line.startswith(("| ---", "| Label"))
    ]
    assert lines, f"{_REGISTRY} has no table rows at all -- is the table still a table?"
    unparsed = [line for line in lines if not _ROW.match(line)]
    assert not unparsed, (
        f"a row of the table in {_REGISTRY} does not parse, so it is invisible to every rule "
        f"below -- `_ROW` wants `| `label` | … | … | `document` |`: {unparsed}"
    )


def test_the_workflow_scanner_sees_the_conditions_that_are_really_there() -> None:
    """A live positive: `ci.yml` reads two labels off the payload, and they are these."""
    found = _workflow_labels(_WORKFLOW.read_text(encoding="utf-8"))
    assert {"cross-platform", "spec-exempt"} <= found, (
        f"the scanner no longer finds the conditions ci.yml really carries: {sorted(found)}"
    )


def test_the_changelog_scanner_sees_the_arm_that_is_really_there() -> None:
    """A live positive: the gate waives itself on exactly one label today."""
    found = _changelog_labels(_CHANGELOG.read_text(encoding="utf-8"))
    assert found == {"no-changelog"}, (
        f"the scanner reads {sorted(found)} out of changelog.sh's label case -- the arm it "
        "must see is the `no-changelog` one, and the variable arm beside it is not a label"
    )


def test_the_dependabot_scanner_convicts_a_label_somebody_adds() -> None:
    """The fabricated positive, because the real file sets none.

    Both shapes: the block list a person writes and the inline list a formatter leaves.
    """
    block = _DEPENDABOT.read_text(encoding="utf-8") + (
        '\n  - package-ecosystem: cargo\n    directory: /\n    labels:\n      - "standing-waiver"\n'
    )
    assert "standing-waiver" in _dependabot_labels(block)
    inline = _DEPENDABOT.read_text(encoding="utf-8") + '\n    labels: ["inline-waiver"]\n'
    assert "inline-waiver" in _dependabot_labels(inline)
    assert _dependabot_labels(_DEPENDABOT.read_text(encoding="utf-8")) == set(), (
        "dependabot.yml has acquired a `labels:` key. That is the standing, never-expiring "
        "exemption the file's own comment argues against -- read it before declaring the label"
    )


def test_every_label_the_automation_branches_on_is_declared_and_the_table_no_ghost() -> None:
    """Both directions, because each failure is a different kind of lie.

    A label branched on and undeclared is the defect this module was written for: the
    mechanism cannot be used and nothing says so. A row nothing branches on is the opposite
    -- a documented lever wired to nothing, which is worse, because somebody will pull it.
    """
    branched = _branched_on()
    declared = _declared()
    assert set(branched) == set(declared), (
        "the automation and .github/labels.md disagree about which labels matter. Undeclared "
        f"-- create the label and add its row: "
        f"{ {label: sorted(branched[label]) for label in sorted(set(branched) - set(declared))} }. "
        f"Declared but unread -- delete the row, or wire the branch it promises: "
        f"{sorted(set(declared) - set(branched))}"
    )


def test_a_new_condition_lands_undeclared_until_somebody_declares_it() -> None:
    """The known positive for the rule above: the detector convicts a fresh condition."""
    fabricated = _WORKFLOW.read_text(encoding="utf-8") + (
        "\n  invented:\n    if: contains(github.event.pull_request.labels.*.name, 'ship-it')\n"
    )
    assert _workflow_labels(fabricated) - set(_declared()) == {"ship-it"}


def test_each_row_cites_a_document_that_still_names_its_label() -> None:
    """The half a reader actually follows: the row points somewhere, and the somewhere
    has not quietly dropped the subject. Names only -- whether the explanation is any
    good is not checkable and is not attempted."""
    silent: list[str] = []
    for label, document in sorted(_declared().items()):
        path = REPO_ROOT / document
        assert path.is_file(), f"{_REGISTRY} sends `{label}` to `{document}`, which is not a file"
        if label not in path.read_text(encoding="utf-8"):
            silent.append(f"{label} -> {document}")
    assert not silent, (
        "a row cites a document that no longer names its label, so the meaning has moved "
        f"and the pointer has not: {silent}"
    )


def test_the_registry_says_when_it_was_last_checked_against_the_repository() -> None:
    """The dated claim stands in for the check this suite cannot run.

    Its shape is held, not its freshness: a test that expired would turn an unrelated pull
    request red on a day nobody chose, and the rule people switch off is the one that cries
    wolf. What is refused is the date going missing, or landing in the future -- which is
    how a claim gets copied forward instead of re-checked.
    """
    text = _REGISTRY.read_text(encoding="utf-8")
    match = _VERIFIED.search(text)
    assert match is not None, (
        f"{_REGISTRY} no longer carries its `**Last verified against the live repository: "
        "YYYY-MM-DD**` line. No offline test can ask GitHub whether these labels exist, so "
        "that dated line is the whole of the claim -- do not remove it, re-check it"
    )
    verified = dt.date.fromisoformat(match.group(1))
    assert verified <= dt.date.today(), (
        f"the registry claims it was verified on {verified}, which has not happened yet"
    )

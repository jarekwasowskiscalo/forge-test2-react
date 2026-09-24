"""A requirement citation names a requirement that exists, in the one form the gate reads.

Until this module nothing in the repository opened `spec/changes/*/requirements.md`: 123
citations across three runners -- `@pytest.mark.req(...)`, the Gherkin `@req:` tag and
the `[req:...]` inside a vitest name -- were checked against nothing. The traceability gate of
the change process cannot close that gap from its side. It accounts **per change**, from the
record to the citation, so a citation belonging to no change is invisible to it, and over a tree
with no record it returns green on an empty set. The Flutter template nearly demonstrated
exactly that (`test/fitness/citation_resolves_test.dart` tells the story); this is the same
check for this stack, reading the other way round -- from the citation to the record, which is
the direction the failure has.

Three questions, three sweeps:

- **resolves** -- every citation on a traceability surface names a record under
  `spec/changes/` and a requirement that record declares;
- **form** -- every shape that looks like a citation on a surface is one the surface's own form
  reads in full (`CR-YYMM-xxxx/R-n`): a bare `R-3`, a loose `req:R-3` or a marker the gate's
  pattern does not match counts as coverage and proves none;
- **only on surfaces** -- `tests/fitness/`, `tests/tooling/` and `e2e/ui/` cite nothing,
  because they prove tools, structure and the smoke rather than product requirements
  (`.specconf/stack.json` § `traceability`, `spec/design/testing.md` § The UI smoke is not a
  traceability surface).

Where the surfaces are is read from `.specconf/stack.json`, which this template writes. How
each form is spelt is **copied** from the engine's `traceability.py` (`_MARKER`, `_TAG`,
`_IN_NAME`), never imported -- nothing under `tests/` may reach the process -- and a copy keeps a
drift between the two visible in a diff.

Deliberately NOT here: the reverse direction, a declared requirement with no citation. That one
is phased -- between the requirements stage and the first implement wave real identifiers exist
and no test cites them yet -- and the phase is the change process's to know
(claude-marketplace#192). A fresh record must not turn this suite red, and a record still
carrying the scaffold's marker declares nothing (`tests/_change_record.py`).

Every detector is proved on a known positive first, because a detector that has stopped
matching passes everything, silently.
"""

import json
import pathlib
import re
from typing import Final, NamedTuple

import pytest

from tests._change_record import CHANGE_ID, declared_requirements, requirements_by_change
from tests._repo import REPO_ROOT

PROFILE: Final = REPO_ROOT / ".specconf" / "stack.json"
CHANGES: Final = REPO_ROOT / "spec" / "changes"
SCAFFOLD_FORM: Final = REPO_ROOT / ".specconf" / "templates" / "change" / "requirements.md"

#: A fully qualified requirement id, captured in its two halves.
_ID: Final = rf"(?P<change>{CHANGE_ID})/(?P<rid>R-\d+)"

#: How each surface cites, by the name the profile uses -- the engine's three patterns
#: (`traceability.py` `_MARKER`, `_TAG`, `_IN_NAME`), with the id split into named groups.
_FORMS: Final[dict[str, re.Pattern[str]]] = {
    "pytest_marker": re.compile(rf"""@pytest\.mark\.req\(\s*["']{_ID}["']\s*\)"""),
    "tag": re.compile(rf"@req:{_ID}"),
    "in_name": re.compile(rf"\[req:{_ID}\]"),
}

#: Anything that looks like an attempt at a citation, in any of the three forms. Each hit on
#: a surface must be the start of a match of that surface's own form; one that is not is a
#: citation the gate cannot read. Split so this module's own source is not a hit.
_ATTEMPT: Final = re.compile(r"(?:@?pytest\.)?mark\.req\(|@" + r"req:|\[" + r"req:")

#: Where no citation may live, and why: see the module docstring.
_NOT_A_SURFACE: Final[tuple[str, ...]] = ("tests/fitness", "tests/tooling", "e2e/ui")


class Surface(NamedTuple):
    glob: str
    form: str


class Citation(NamedTuple):
    where: str
    change: str
    rid: str


def _surfaces() -> list[Surface]:
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    return [
        Surface(glob=entry["glob"], form=entry["citation"])
        for entry in profile["traceability"]["surfaces"]
    ]


def _files(root: pathlib.Path, glob: str) -> list[pathlib.Path]:
    return sorted(path for path in root.glob(glob) if path.is_file())


def _line(text: str, offset: int) -> int:
    return text[:offset].count("\n") + 1


def _citations(root: pathlib.Path, surfaces: list[Surface]) -> list[Citation]:
    found = []
    for surface in surfaces:
        pattern = _FORMS[surface.form]
        for path in _files(root, surface.glob):
            text = path.read_text(encoding="utf-8")
            for match in pattern.finditer(text):
                where = f"{path.relative_to(root)}:{_line(text, match.start())}"
                found.append(Citation(where, match.group("change"), match.group("rid")))
    return found


def _dangling(citations: list[Citation], by_change: dict[str, frozenset[str]]) -> list[str]:
    offenders = []
    for citation in citations:
        declared = by_change.get(citation.change)
        if declared is None:
            offenders.append(f"{citation.where}: no spec/changes/{citation.change}* record")
        elif citation.rid not in declared:
            offenders.append(f"{citation.where}: {citation.change} declares no {citation.rid}")
    return offenders


def _unreadable(text: str, form: str, where: str) -> list[str]:
    """Every citation attempt in `text` that `form` does not read from where it starts."""
    pattern = _FORMS[form]
    offenders = []
    for attempt in _ATTEMPT.finditer(text):
        if not pattern.match(text, attempt.start()):
            snippet = text[attempt.start() : attempt.start() + 48].splitlines()[0]
            offenders.append(f"{where}:{_line(text, attempt.start())}: {snippet!r}")
    return offenders


# --------------------------------------------------------------------------- #
# The detectors, proved on fabricated positives before the tree is trusted.
# --------------------------------------------------------------------------- #

#: Assembled, so the sweeps below never read this module's samples as citations.
_M: Final = "@pytest.mark." + "req"


def test_the_resolver_still_finds_a_citation_that_names_nothing(tmp_path: pathlib.Path) -> None:
    record = tmp_path / "spec" / "changes" / "CR-2609-aaaa-some-change"
    record.mkdir(parents=True)
    (record / "requirements.md").write_text("# Requirements\n\n### R-1: one\n", encoding="utf-8")
    (tmp_path / "t").mkdir()
    (tmp_path / "t" / "test_x.py").write_text(
        f'{_M}("CR-2609-aaaa/R-1")\ndef test_ok(): ...\n'
        f'{_M}("CR-2609-aaaa/R-2")\ndef test_no_requirement(): ...\n'
        f'{_M}("CR-2609-bbbb/R-1")\ndef test_no_record(): ...\n',
        encoding="utf-8",
    )
    citations = _citations(tmp_path, [Surface("t/*.py", "pytest_marker")])
    assert len(citations) == 3, citations
    offenders = _dangling(citations, requirements_by_change(tmp_path / "spec" / "changes"))
    assert offenders == [
        "t/test_x.py:3: CR-2609-aaaa declares no R-2",
        "t/test_x.py:5: no spec/changes/CR-2609-bbbb* record",
    ]


@pytest.mark.parametrize(
    ("form", "sample"),
    [
        ("pytest_marker", f'{_M}("R-3")'),
        ("pytest_marker", f'{_M}("CR-2609-XYZW/R-3")'),
        ("pytest_marker", 'pytestmark = pytest.mark.req("CR-2609-aaaa/R-3")'),
        ("tag", "@" + "req:R-3"),
        ("tag", "@" + "req:CR-2609-aaaa/3"),
        ("in_name", "it('does a thing [" + "req:R-3]')"),
        ("in_name", "it('does a thing [" + "req:CR-2609-aaaa/R-3')"),
        ("tag", f'{_M}("CR-2609-aaaa/R-3")'),
    ],
)
def test_the_form_detector_still_refuses_what_the_gate_cannot_read(form: str, sample: str) -> None:
    assert _unreadable(sample, form, "sample"), f"{sample!r} was read as a {form} citation"


@pytest.mark.parametrize(
    ("form", "sample"),
    [
        ("pytest_marker", f'{_M}("CR-2609-aaaa/R-3")'),
        ("pytest_marker", f"{_M}(\n    'CR-2609-aaaa/R-12'\n)"),
        ("tag", "  @" + "req:CR-2609-aaaa/R-3"),
        ("in_name", "it('does a thing [" + "req:CR-2609-aaaa/R-3]')"),
    ],
)
def test_the_form_detector_still_reads_a_well_formed_citation(form: str, sample: str) -> None:
    assert not _unreadable(sample, form, "sample")


def test_the_scaffold_form_declares_nothing() -> None:
    """A record opened a minute ago is not a set of requirements.

    The seed ships `### R-1: <area>` and `### R-2: <area>`; read as content, every fresh change
    would declare two requirements nobody wrote. It carries the marker, and the marker is what
    makes it declare nothing -- proved on the seed itself, and on the same text with the marker
    gone, so the test fails if the reader stops seeing either half.
    """
    seed = SCAFFOLD_FORM.read_text(encoding="utf-8")
    assert declared_requirements(seed) == frozenset()
    written = "\n".join(line for line in seed.splitlines() if not line.startswith("<!-- TEMPLATE:"))
    assert {"R-1", "R-2"} <= declared_requirements(written)


def test_a_commented_heading_is_guidance_not_a_declaration() -> None:
    text = "# Requirements\n\n### R-1: real\n\n<!--\n### R-9: an example\n-->\n"
    assert declared_requirements(text) == frozenset({"R-1"})


# --------------------------------------------------------------------------- #
# The sweeps over this tree.
# --------------------------------------------------------------------------- #


def test_every_surface_names_a_form_this_suite_knows() -> None:
    """A surface whose form this suite does not know would be swept by no pattern at all."""
    unknown = [s for s in _surfaces() if s.form not in _FORMS]
    assert not unknown, (
        f"{unknown}: .specconf/stack.json § traceability names a citation form this suite has "
        f"no pattern for; the known ones are {sorted(_FORMS)}"
    )


def test_every_cited_requirement_is_declared_by_a_change_record() -> None:
    offenders = _dangling(_citations(REPO_ROOT, _surfaces()), requirements_by_change(CHANGES))
    assert not offenders, (
        f"{len(offenders)} citations name nothing, and a citation naming nothing counts as "
        "coverage and proves none; declare the requirement in spec/changes/<CR>/requirements.md "
        "or correct the id:\n" + "\n".join(offenders)
    )


def test_every_citation_on_a_surface_is_in_the_form_the_gate_reads() -> None:
    offenders = []
    for surface in _surfaces():
        for path in _files(REPO_ROOT, surface.glob):
            text = path.read_text(encoding="utf-8")
            offenders += _unreadable(text, surface.form, str(path.relative_to(REPO_ROOT)))
    assert not offenders, (
        "a citation the gate cannot read looks like coverage and counts as none; cite as "
        '@pytest.mark.req("CR-YYMM-xxxx/R-n"), @req:CR-YYMM-xxxx/R-n or [req:CR-YYMM-xxxx/R-n] '
        "by what the surface carries (.specconf/stack.json § traceability):\n"
        + "\n".join(offenders)
    )


def test_nothing_outside_a_surface_cites_a_requirement() -> None:
    offenders = []
    for directory in _NOT_A_SURFACE:
        for path in _files(REPO_ROOT, f"{directory}/**/*.py"):
            text = path.read_text(encoding="utf-8")
            for pattern in _FORMS.values():
                for match in pattern.finditer(text):
                    rel = path.relative_to(REPO_ROOT)
                    offenders.append(f"{rel}:{_line(text, match.start())}: {match.group(0)}")
    assert not offenders, (
        "these directories prove tools, structure and the smoke, not product requirements, and "
        "own no citation (spec/design/testing.md § The UI smoke is not a traceability surface):\n"
        + "\n".join(offenders)
    )

"""Every invariant names a test that exists, and says what kind of proof it is.

`contracts/invariants/` replaced a document that admitted, in its own words, that
`D-01`..`D-03` were held "by the data model and by a decision about identifiers,
rather than by a test that names them". Replacing the address would have changed
nothing; what changes something is that the new home refuses an invariant without
a witness, and that this module is what refuses it.

**A fitness test rather than a gate**, and the choice is not laziness. "This
string points at a test that exists" is a statement about the test tree, which is
exactly what `tests/fitness/` is for -- `test_evidence_map.py` is the precedent one
file over. A gate would cost an entry in `CHECKS`, a row in `_EXEMPTABLE`, a row in
`CLAUDE.md`, a literal in `test_sdd_spec_summary.py` and a line in the CI parity
map, to ask a question none of those registers make sharper.

**`none` is a legal answer and that is the point.** An invariant nobody has proved
yet says so, in at least forty characters of why. A gap counted and printed is a
different object from a gap unmentioned -- the same argument `**Verified-by:** manual`
and `**ADR:** none` already make, one document over.
"""

import pathlib
import re
from typing import Final

from tests._repo import REPO_ROOT

#: A heading that declares an invariant, as `## |D-01| -- <sentence>` with backticks
#: around the identifier.
#:
#: Two or three hashes, because the outline depth is not what this module is about and
#: pinning it is how the reader stops reading. The first draft demanded three, the
#: document writes two, and it was the scale test below -- not the assertion about
#: problems -- that said so: a parser matching nothing reports no problems and passes
#: triumphantly. That is the whole reason a detector is made to detect something.
_HEADING: Final = re.compile(r"^#{2,3}\s+`(?P<id>[A-Z]+-\d{2})`", re.MULTILINE)

#: The two lines every entry owes. Captured to the end of the line: a witness may
#: name two tests joined by prose, and the reason of a `none` is a sentence.
_WITNESS: Final = re.compile(r"^\*\*Witness:\*\*\s*(?P<body>\S.*)$", re.MULTILINE)
_KIND: Final = re.compile(r"^\*\*Kind of evidence:\*\*\s*(?P<body>\S.*)$", re.MULTILINE)

#: What an entry says when nothing proves it yet.
_NONE: Final[tuple[str, ...]] = ("none",)

#: `path::name`, in backticks, as `spec/design/testing.md` spells a witness.
_REFERENCE: Final = re.compile(r"`(?P<path>[\w./_-]+\.py)::(?P<name>[\w_]+)`")

#: Shorter than this and "none" says when, not why.
_MIN_REASON: Final = 40

_HOME: Final = REPO_ROOT / "contracts" / "invariants"


def _documents() -> list[pathlib.Path]:
    return sorted(path for path in _HOME.glob("*.md") if path.name != "README.md")


def _entries(text: str) -> list[tuple[str, str]]:
    """Each invariant id with the body that follows it, up to the next heading."""
    marks = list(_HEADING.finditer(text))
    return [
        (
            mark.group("id"),
            text[mark.end() : marks[index + 1].start() if index + 1 < len(marks) else len(text)],
        )
        for index, mark in enumerate(marks)
    ]


def _problems(text: str, root: pathlib.Path) -> list[str]:
    problems: list[str] = []
    for identifier, body in _entries(text):
        witness = _WITNESS.search(body)
        kind = _KIND.search(body)
        if witness is None:
            problems.append(f"{identifier}: no **Witness:** line")
            continue
        if kind is None:
            problems.append(f"{identifier}: no **Kind of evidence:** line")
        stated = witness.group("body")
        if stated.lstrip().lower().startswith(_NONE):
            reason = stated.split("—", 1)[-1] if "—" in stated else ""
            if len(reason.strip()) < _MIN_REASON:
                problems.append(
                    f"{identifier}: 'none' with no reason worth the name -- say why nothing "
                    f"proves this yet, in at least {_MIN_REASON} characters"
                )
            continue
        references = _REFERENCE.findall(stated)
        if not references:
            problems.append(f"{identifier}: the witness names no `file.py::test` reference")
        for path, name in references:
            module = root / path
            if not module.is_file():
                problems.append(f"{identifier}: {path} does not exist")
            elif f"def {name}(" not in module.read_text(encoding="utf-8"):
                problems.append(f"{identifier}: {path} defines no {name}")
    return problems


def test_every_invariant_names_a_witness_that_exists() -> None:
    documents = _documents()
    assert documents, "no invariant document at all -- has the home moved again?"
    for document in documents:
        assert _problems(document.read_text(encoding="utf-8"), REPO_ROOT) == [], document.name


def test_the_reader_finds_the_invariants_that_are_there() -> None:
    """Scale, not just silence: a parser that matches nothing passes everything."""
    found = {
        identifier
        for document in _documents()
        for identifier, _ in _entries(document.read_text(encoding="utf-8"))
    }
    assert {"D-01", "D-02", "D-03"} <= found


# --- Known positives: the detector, on documents built to trip it ----------- #

_GOOD = (
    "### `D-09` — something always true\n\nThe body.\n\n"
    "**Witness:** `tests/fitness/test_invariant_witnesses.py::test_the_witness_reader_detects_a_missing_line`\n"
    "**Kind of evidence:** sweeper\n"
)


def test_the_witness_reader_accepts_a_complete_entry() -> None:
    assert _problems(_GOOD, REPO_ROOT) == []


def test_the_witness_reader_detects_a_missing_line() -> None:
    without_kind = _GOOD.replace("**Kind of evidence:** sweeper\n", "")
    assert _problems(without_kind, REPO_ROOT) == ["D-09: no **Kind of evidence:** line"]
    without_witness = re.sub(r"\*\*Witness:\*\*.*\n", "", _GOOD)
    assert _problems(without_witness, REPO_ROOT) == ["D-09: no **Witness:** line"]


def test_the_witness_reader_detects_a_dangling_test() -> None:
    dangling = _GOOD.replace("test_the_witness_reader_detects_a_missing_line", "test_nothing_here")
    assert _problems(dangling, REPO_ROOT) == [
        "D-09: tests/fitness/test_invariant_witnesses.py defines no test_nothing_here"
    ]


def test_a_declared_gap_is_legal_and_a_bare_one_is_not() -> None:
    """The whole reason `none` exists -- and the reason it costs a sentence."""
    reasoned = _GOOD.replace(
        "**Witness:** `tests/fitness/test_invariant_witnesses.py::test_the_witness_reader_detects_a_missing_line`",
        "**Witness:** none — there is no second table, so a rule of this class has nothing to break it today",
    )
    assert _problems(reasoned, REPO_ROOT) == []
    bare = _GOOD.replace(
        "**Witness:** `tests/fitness/test_invariant_witnesses.py::test_the_witness_reader_detects_a_missing_line`",
        "**Witness:** none — for now",
    )
    assert len(_problems(bare, REPO_ROOT)) == 1

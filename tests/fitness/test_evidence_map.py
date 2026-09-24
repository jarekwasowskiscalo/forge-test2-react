"""A file handed to a test author must have a row in § Evidence map.

`spec/design/testing.md` wrote the rule down and gave it no enforcer:

    Assigning a file to an author is not assigning a claim. The file set says who
    may write; § Evidence map says what is to be proved and by which suite. A
    clause with no row in § Evidence map has no suite -- and an author who got a
    file and did not get a row has nothing to write from: they will pick the claim
    themselves and land in a suite that cannot carry it.

`traceability` will not catch that failure: it reads identifiers at the requirement level
(`R-n`), and a sentence with no witness is a clause or screen copy, so `traceability` counts
the requirement as covered and stays silent. Six of the eleven findings in
`CR-2608-6fb2`'s final review are exactly this shape, and three of them -- `FR-3`,
`FR-5`, `FR-7` -- aim at the same document.

The detector takes the **mechanically checkable half** of that rule, the one finding
`FR-5` named: a file that § Four file sets hands to an author **as a new product of
this change** must be named in a row of the § Evidence map table. Nobody can
enumerate prose clauses; file assignments, however, can be -- and that is the half
`FR-5` measured: "§ Four file sets **gave** an author a file
(`frontend/src/pages/IdentitiesPage.test.tsx`), and § Evidence map **gave them not
one clause**".

Deliberately NOT covered:

- **edited files** (a cell segment beginning with "edits") -- an edit carries existing
  evidence over to a new world and does not order a new claim;
- **infrastructure** (the segment after the word "infrastructure") -- a shared
  conftest, the harness and the parity module are no author's product, and the same
  document says so;
- **the UI smoke** -- § The UI smoke is not a traceability surface says outright that
  the smoke is always supplementary and never an owner, so it cannot have a row in
  the map.

The detector is proved on a known positive, because the house pattern is that a
detector which has stopped detecting should report that rather than report a clean
tree.
"""

import itertools
import re
from typing import Final

from tests._repo import REPO_ROOT

TESTING_DOC: Final = REPO_ROOT / "spec" / "design" / "testing.md"


#: Anchors in `testing.md`, each in both wordings while the normative tree is being
#: translated to English (`spec/design/conventions.md` § Language). An anchor that
#: knows one wording stops matching on the day of the translation and does not say so
#: -- it finds zero sections and passes.
def _anchor(text: str, *wordings: str) -> str:
    """The wording this document actually uses, or the first one for the message."""
    return next((w for w in wordings if w in text), wordings[0])


#: The map's section names itself with this string, so the anchor is not its title --
#: that is written after the subject of a change and moves with every one.
_MAP_SELF_NAMES: Final[tuple[str, ...]] = ("**§ Evidence map**", "**§ Evidence map**")

#: The subsection holding the file-assignment table.
_FILE_SETS_HEADINGS: Final[tuple[str, ...]] = ("Four file sets",)

#: The subsection the UI smoke's exemption comes from. When it goes, the exemption
#: dies with it rather than outliving the rule it cites.
_SMOKE_HEADINGS: Final[tuple[str, ...]] = ("The UI smoke is not a traceability surface",)

#: A surface that by definition never owns a citation, so it cannot have a row in the
#: map (§ The UI smoke is not a traceability surface).
_NOT_A_TRACEABILITY_SURFACE: Final[tuple[str, ...]] = ("e2e/ui/",)

#: A cell segment speaking about an existing file or about a shared layer. "no change"
#: is the same sentence as "edits", only with a zero on the other side: the
#: `build-tests-unit` cell cites an existing detector in it as the reason it writes
#: nothing there -- and a citation is not an assignment.
_NOT_A_PRODUCT: Final[tuple[str, ...]] = (
    "edits",
    "infrastructure",
    "no change",
    "unchanged",
)

_PATH: Final = re.compile(r"[A-Za-z0-9_./-]+\.(?:tsx|ts|py|feature)")

_SEGMENT_SEPARATOR: Final = "·"


def _is_test_file(path: str) -> bool:
    name = path.rsplit("/", 1)[-1]
    return (
        (name.startswith("test_") and name.endswith(".py"))
        or name.endswith((".test.ts", ".test.tsx"))
        or name.endswith(".feature")
    )


def _section_bounds(lines: list[str], marker: str, level: str) -> tuple[int, int]:
    """The bounds of the `level` section (e.g. `"## "`) whose body contains `marker`."""
    heads = [i for i, line in enumerate(lines) if line.startswith(level)] + [len(lines)]
    for start, stop in itertools.pairwise(heads):
        if marker in "\n".join(lines[start:stop]):
            return start, stop
    raise AssertionError(f"found no {level!r} section containing {marker!r}")


def _split_map_and_file_sets(text: str) -> tuple[str, list[str]]:
    """`(the map tables' rows, the file-assignment table's rows)`."""
    lines = text.splitlines()
    start, stop = _section_bounds(lines, _anchor("\n".join(lines), *_MAP_SELF_NAMES), "## ")
    section = lines[start:stop]
    sets_start, sets_stop = _section_bounds(
        section, _anchor("\n".join(section), *_FILE_SETS_HEADINGS), "### "
    )

    file_sets = [line for line in section[sets_start:sets_stop] if line.lstrip().startswith("|")]
    map_rows = [
        line
        for index, line in enumerate(section)
        if not sets_start <= index < sets_stop and line.lstrip().startswith("|")
    ]
    return "\n".join(map_rows), file_sets


def _paths_in(cell: str) -> list[str]:
    """A cell's paths, with bare names expanded by the last directory seen.

    The table writes `**tests/integration/test_authentication.py**, `test_access_refusals.py``
    -- the second name lives in the first one's directory, and without that expansion it
    cannot be compared against a map that writes full paths.
    """
    directory = ""
    found: list[str] = []
    for match in _PATH.finditer(cell):
        raw = match.group(0)
        if "/" in raw:
            directory = raw.rsplit("/", 1)[0] + "/"
            found.append(raw)
        else:
            found.append(directory + raw)
    return found


def _products_of(file_set_rows: list[str]) -> dict[str, str]:
    """`{path: author}` for the files the table hands over as a **new product**."""
    products: dict[str, str] = {}
    for row in file_set_rows:
        columns = [part.strip() for part in row.strip().strip("|").split("|")]
        if len(columns) != 2 or set(columns[1]) <= {"-", ":"}:
            continue
        author, cell = columns
        for segment in cell.split(_SEGMENT_SEPARATOR):
            if any(word in segment for word in _NOT_A_PRODUCT):
                continue
            for path in _paths_in(segment):
                # A bare name with no directory before it anywhere in this cell is not
                # an assignment a map of full paths can be compared against.
                if "/" not in path or not _is_test_file(path):
                    continue
                if path.startswith(_NOT_A_TRACEABILITY_SURFACE):
                    continue
                products.setdefault(path, author.strip("`*"))
    return products


def files_without_a_row(text: str) -> dict[str, str]:
    """Files handed to an author as a new product that the map never names."""
    map_rows, file_sets = _split_map_and_file_sets(text)
    return {
        path: author for path, author in _products_of(file_sets).items() if path not in map_rows
    }


def test_the_detector_sees_a_file_without_a_row() -> None:
    """A known positive: a map with no row for a new file must light up, while an
    edited, an infrastructure and a smoke file in the same document must not."""
    document = "\n".join(
        [
            "# Testing",
            "",
            "## The map",
            "",
            "The rest of this document names this section **§ Evidence map**.",
            "",
            "| Requirement | Owner of the proof |",
            "|---|---|",
            "| `R-1` | `tests/unit/test_seen.py` |",
            "",
            "### Four file sets, disjoint",
            "",
            "| Author | Writes |",
            "|---|---|",
            "| `build-tests-unit` | **tests/unit/test_seen.py**, `test_without_a_row.py`"
            " (new) · edits `tests/unit/test_edited.py` · **infrastructure**:"
            " `tests/conftest.py` |",
            "| `build-tests-e2e` | `e2e/ui/test_smoke.py` |",
            "",
            "### The UI smoke is not a traceability surface",
            "",
            "The smoke is supplementary, never an owner.",
        ]
    )
    assert files_without_a_row(document) == {"tests/unit/test_without_a_row.py": "build-tests-unit"}


def test_the_document_still_carries_both_anchors_this_detector_reads() -> None:
    """There are two anchors and both are the document's sentences about itself. When
    one goes, the detector is to fail here rather than quietly start searching the
    wrong section."""
    text = TESTING_DOC.read_text(encoding="utf-8")
    assert any(name in text for name in _MAP_SELF_NAMES), "§ Evidence map has stopped naming itself"
    assert any(heading in text for heading in _SMOKE_HEADINGS), (
        f"the § {_SMOKE_HEADINGS[0]} section is gone, and the exemption "
        f"{_NOT_A_TRACEABILITY_SURFACE} cites it -- the exemption is to die with it"
    )


def test_the_scan_reads_both_tables_and_not_an_empty_one() -> None:
    """If the parser stopped matching the tables, finding nothing would read as clean.

    The thresholds are here so that ZERO does not look like order -- not to measure the
    size of a change. An earlier version demanded fourteen map rows, because that is how
    many the change this detector was written for had; in a repository with no open
    change such a threshold demands rows about requirements that do not exist, and
    goes red on a correct tree. Three rows are a header, a separator and at least one
    row of content -- exactly enough to prove the parser matched the table.
    """
    map_rows, file_sets = _split_map_and_file_sets(TESTING_DOC.read_text(encoding="utf-8"))
    assert len(file_sets) >= 4, "the § Four file sets table has four author rows"
    assert len(map_rows.splitlines()) >= 3, "§ Evidence map was not found at all"
    products = _products_of(file_sets)
    assert len(products) >= 5, f"too few assignments, the cell parser is broken: {products}"


def test_every_file_given_to_an_author_as_a_product_has_a_row_in_the_evidence_map() -> None:
    orphans = files_without_a_row(TESTING_DOC.read_text(encoding="utf-8"))
    assert not orphans, (
        "§ Four file sets hands these files to an author as a new product, and "
        f"§ Evidence map never names them: {sorted(orphans)}. An author who got a file "
        "and did not get a row picks the claim themselves -- or picks none at all. The "
        "direction of the fix runs to the map: a missing clause is added as a row in "
        "§ Evidence map, never as a file in the file-set table."
    )

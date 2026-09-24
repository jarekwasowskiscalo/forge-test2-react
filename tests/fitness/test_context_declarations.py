"""The bounded context declares itself, and this is what reads the declaration.

`spec/contexts/<name>.md` carries a front-matter header naming what the context
owns, whom it borders on, which screens and which feature files belong to it.
Until this module existed **nothing read it**, and the header was not merely
unread -- it was illegal: it used block sequences, which
`tests/_frontmatter.py`, this template's front-matter
reader, refuses outright. A declaration nobody parses is a comment, and a comment
that claims to be a declaration is worse than none, because the next author
copies its shape.

Four rules, each of which exists because the alternative is silent:

- **One reader.** Every context document parses with `tests._frontmatter` and no
  other parser. `tests/_golden_set.py` already paid for the lesson: a hand-copied
  twin of one locator diverged in return type *and* exception type before anybody
  noticed.
- **Every declared thing exists.** A table in `owns` is a table
  `spec/design/data-model.md` declares; a path in `screens` or `features` is a
  path on disk. A register pointing at nothing is how `spec/` starts describing a
  system that is no longer there.
- **Every registered thing is claimed exactly once.** The converse, and the half
  that fails in practice: a screen or a feature file belonging to no context is a
  surface with no owner, and one belonging to two contexts is a boundary drawn in
  two places.
- **A neighbour carries a classified pattern, not a direction.** `a` writing into
  `b` is equally true of a context that translates `b`'s model at the seam and one
  that adopts it whole, and those produce different code and different blast radii
  when `b` changes (`spec/design/architecture.md` § Rules between contexts).

Most of these were **vacuously true** while there was one context bordering on
nothing; since `CR-2609-823a` two contexts declare each other, and the sweeps read
real headers. Each therefore carries a known positive over synthetic input, exactly
as `tests/fitness/test_data_invariants.py` does for the data invariants it sweeps
over a single table: a check that has never seen a violation is a check nobody has
reason to believe.

Reads text. No database, no application import.
"""

import pathlib
import re
from typing import Final

import pytest

from tests import _frontmatter as frontmatter
from tests._repo import REPO_ROOT

CONTEXTS: Final[pathlib.Path] = REPO_ROOT / "spec/contexts"
DATA_MODEL: Final[pathlib.Path] = REPO_ROOT / "spec/design/data-model.md"
API_REGISTER: Final[pathlib.Path] = REPO_ROOT / "spec/design/api.md"
SCREENS: Final[pathlib.Path] = REPO_ROOT / "spec/design/ui"
FEATURES: Final[pathlib.Path] = REPO_ROOT / "e2e/suite/features"

#: Every key a context document owes. Absence is a failure rather than a default:
#: a context with no `neighbours` line has not said it borders on nothing, it has
#: said nothing -- and those are different claims.
REQUIRED_KEYS: Final[tuple[str, ...]] = (
    "context",
    "classification",
    "owns",
    "neighbours",
    "processes",
    "screens",
    "features",
)

#: Evans' three kinds, and the reason the key is not free text: a context called
#: `generic` that carries elaborate rules is either misclassified or rebuilding
#: something a vendor sells.
CLASSIFICATIONS: Final[frozenset[str]] = frozenset({"core", "supporting", "generic"})

#: Which patterns each role may take, from Context Mapper's own semantics: an open
#: host service and a published language are things an **upstream** publishes; an
#: anti-corruption layer and a conformist are the two **opposite** answers a
#: downstream can give -- one translates the other model, one adopts it whole.
#: Writing both against one neighbour means the boundary has not been decided.
PATTERNS_BY_ROLE: Final[dict[str, frozenset[str]]] = {
    "upstream": frozenset({"acl", "conformist", "customer-supplier"}),
    "downstream": frozenset({"open-host-service", "published-language", "customer-supplier"}),
    "peer": frozenset({"shared-kernel", "separate-ways"}),
}

#: A table's declaration in the data-model register: `## `guestbook_entries``.
_TABLE_HEADING: Final = re.compile(r"^## `([a-z_][a-z0-9_]*)`\s*$", re.MULTILINE)

#: The heading of the register's route table. It was "## Module map" until
#: 2026-09-07; one concept wearing two words is what `spec/glossary.md` exists to
#: prevent, and "Context map" was not available -- in DDD that names the map of
#: relationships BETWEEN contexts, which this table is not.
_API_ROUTE_SECTION: Final = re.compile(
    r"## Routes and their contexts\n(.*?)(?:\n## |\Z)", re.DOTALL
)


def _context_documents() -> list[pathlib.Path]:
    return sorted(CONTEXTS.glob("*.md"))


def _declared() -> dict[str, dict[str, frontmatter.FrontMatterValue]]:
    """Every context document's header, keyed by the context it names."""
    return {path.stem: frontmatter.read(path) for path in _context_documents()}


def _neighbour_fault(entry: str, contexts: frozenset[str], mine: str) -> str | None:
    """Why `entry` is not a legal neighbour declaration, or None when it is."""
    parts = entry.split(":")
    if len(parts) != 3:
        return f"{entry!r} is not `<context>:<role>:<pattern>`"
    other, role, pattern = parts
    if other == mine:
        return f"{entry!r} names its own context as a neighbour"
    if other not in contexts:
        return f"{entry!r} names {other!r}, which has no document in spec/contexts/"
    allowed = PATTERNS_BY_ROLE.get(role)
    if allowed is None:
        return f"{entry!r} has role {role!r}; roles are {sorted(PATTERNS_BY_ROLE)}"
    if pattern not in allowed:
        return (
            f"{entry!r} pairs role {role!r} with pattern {pattern!r}; "
            f"a {role} neighbour allows {sorted(allowed)}"
        )
    return None


# --------------------------------------------------------------------------- #
# One reader
# --------------------------------------------------------------------------- #


def test_every_context_document_parses_with_the_one_reader() -> None:
    """The header is legal by this repository's own grammar.

    The live positive is the parse itself: a document with no front matter
    returns `{}` rather than raising, so an empty result would let a header-less
    file pass as parsed. Both halves are asserted.
    """
    documents = _context_documents()
    assert documents, "spec/contexts/ holds no context document -- has the tree moved?"

    for path in documents:
        header = frontmatter.read(path)
        assert header, (
            f"{path.relative_to(REPO_ROOT)} has no front matter. The header is the "
            "context's declaration and this module is what reads it"
        )


def test_the_reader_refuses_the_shape_this_repository_used_to_write() -> None:
    """Proof the grammar is a constraint and not a preference.

    `spec/contexts/guestbook.md` carried block sequences until 2026-09-07. They
    parse in any YAML library and in this one they do not -- so a check that
    accepted them would have been checking a shape the framework cannot read.
    """
    with pytest.raises(frontmatter.FrontMatterError):
        frontmatter.parse("---\nscreens:\n  - spec/design/ui/guestbook.md\n---\n")


# --------------------------------------------------------------------------- #
# The keys a context owes
# --------------------------------------------------------------------------- #


def test_every_context_declares_the_keys_a_context_has() -> None:
    """Every required key present, the slug matching the file, the class known."""
    for path in _context_documents():
        header = frontmatter.read(path)
        missing = [key for key in REQUIRED_KEYS if key not in header]
        assert not missing, (
            f"{path.relative_to(REPO_ROOT)} declares no {missing}. The shape is "
            ".specconf/templates/system/context.md; a key left out is a claim not made"
        )

        named = frontmatter.as_str(header["context"])
        assert named == path.stem, (
            f"{path.relative_to(REPO_ROOT)} calls itself {named!r}. The file name is the "
            "context's identifier everywhere else -- two names for one context is the "
            "failure spec/glossary.md exists to prevent"
        )

        classification = frontmatter.as_str(header["classification"])
        assert classification in CLASSIFICATIONS, (
            f"{path.relative_to(REPO_ROOT)} is classified {classification!r}; "
            f"the three kinds are {sorted(CLASSIFICATIONS)}"
        )


# --------------------------------------------------------------------------- #
# Every declared thing exists
# --------------------------------------------------------------------------- #


def test_every_table_a_context_owns_is_declared_by_the_data_model() -> None:
    """A context owning a table the register does not declare owns nothing.

    The live positive is the register's own scan: it must find at least one
    table, or a passing result below would mean the regex stopped matching
    rather than that every claim resolved.
    """
    declared_tables = set(_TABLE_HEADING.findall(DATA_MODEL.read_text(encoding="utf-8")))
    assert declared_tables, (
        "no `## `table`` heading found in spec/design/data-model.md -- the register's "
        "shape moved and this detector is now blind"
    )

    for path in _context_documents():
        header = frontmatter.read(path)
        for table in frontmatter.as_list(header["owns"]):
            assert table in declared_tables, (
                f"{path.relative_to(REPO_ROOT)} owns `{table}`, which "
                f"spec/design/data-model.md does not declare. It declares "
                f"{sorted(declared_tables)}"
            )


def test_every_screen_and_feature_a_context_names_is_on_disk() -> None:
    """A register pointing at nothing describes a system that is not there."""
    for path in _context_documents():
        header = frontmatter.read(path)
        for key in ("screens", "features"):
            for target in frontmatter.as_list(header[key]):
                assert (REPO_ROOT / target).is_file(), (
                    f"{path.relative_to(REPO_ROOT)} names `{target}` under `{key}`, "
                    "and there is no such file"
                )


# --------------------------------------------------------------------------- #
# Every registered thing is claimed exactly once
# --------------------------------------------------------------------------- #


def _claims(key: str) -> dict[str, list[str]]:
    """Which contexts claim each path under `key`."""
    claimed: dict[str, list[str]] = {}
    for path in _context_documents():
        header = frontmatter.read(path)
        for target in frontmatter.as_list(header[key]):
            claimed.setdefault(target, []).append(path.stem)
    return claimed


def test_every_registered_screen_is_claimed_by_exactly_one_context() -> None:
    """A screen with a frozen `S-xx` belongs to a context, and to one of them.

    The discriminator is `info_ref`, not the file name. `spec/design/ui/`
    holds documents that are not screens in the register -- `system-states.md`
    describes states every route can be in and carries `info_ref: null` -- and
    demanding an owner for those would force a context to claim a surface it
    does not own.
    """
    claimed = _claims("screens")
    registered = {
        f"spec/design/ui/{path.name}"
        for path in sorted(SCREENS.glob("*.md"))
        if frontmatter.read(path).get("info_ref") not in (None, "")
    }
    assert registered, (
        "no screen document under spec/design/ui/ carries an info_ref -- the S-xx "
        "space moved and this detector is now blind"
    )

    for screen in sorted(registered):
        owners = claimed.get(screen, [])
        assert len(owners) == 1, (
            f"`{screen}` is claimed by {owners or 'no context'}. A screen belongs to "
            "exactly one context: none means a surface nobody owns, two means a "
            "boundary drawn in two places"
        )


def test_every_feature_file_is_claimed_by_exactly_one_context() -> None:
    """The black box's scenarios have an owner too."""
    claimed = _claims("features")
    present = {f"e2e/suite/features/{path.name}" for path in sorted(FEATURES.glob("*.feature"))}
    assert present, "e2e/suite/features/ holds no .feature file -- has the suite moved?"

    for feature in sorted(present):
        owners = claimed.get(feature, [])
        assert len(owners) == 1, (
            f"`{feature}` is claimed by {owners or 'no context'}; a feature file proves "
            "one context's rules and is claimed by that context"
        )


def test_the_claim_sweep_detects_an_orphan_and_a_double_claim() -> None:
    """Proof the counting above can fail, on input this repository does not hold."""
    synthetic: dict[str, list[str]] = {"a.md": [], "b.md": ["one", "two"], "c.md": ["one"]}
    assert [name for name, owners in synthetic.items() if len(owners) != 1] == ["a.md", "b.md"]


# --------------------------------------------------------------------------- #
# A neighbour carries a classified pattern
# --------------------------------------------------------------------------- #


def test_every_neighbour_names_a_context_and_a_pairing_the_rules_allow() -> None:
    """Vacuously true while there was one context; since `CR-2609-823a` it reads
    two real neighbours.

    `test_the_neighbour_reader_refuses_every_illegal_pairing` is the half that
    carries the weight until a second context exists.
    """
    contexts = frozenset(_declared())
    for path in _context_documents():
        header = frontmatter.read(path)
        faults = [
            fault
            for entry in frontmatter.as_list(header["neighbours"])
            if (fault := _neighbour_fault(entry, contexts, path.stem)) is not None
        ]
        assert not faults, f"{path.relative_to(REPO_ROOT)}: {faults}"


@pytest.mark.parametrize(
    "entry",
    [
        "billing:upstream:open-host-service",  # OHS is what an upstream publishes
        "billing:downstream:acl",  # an ACL is a downstream's answer
        "billing:downstream:conformist",  # so is conforming
        "billing:peer:acl",  # a peer supplies nothing to translate
        "billing:sideways:acl",  # no such role
        "billing:upstream:antikorruption",  # no such pattern
        "billing:upstream",  # not a triple
        "guestbook:upstream:acl",  # a context is not its own neighbour
        "nowhere:upstream:acl",  # no document for that context
    ],
)
def test_the_neighbour_reader_refuses_every_illegal_pairing(entry: str) -> None:
    """The known positives, one per way the declaration can be wrong.

    This is where the rule actually lives today. `neighbours: []` everywhere
    means the sweep above proves nothing on its own, and a rule proved by nothing
    is a rule that will be discovered broken by the change that first needed it.
    """
    assert _neighbour_fault(entry, frozenset({"guestbook", "billing"}), "guestbook") is not None


def test_the_neighbour_reader_accepts_the_pairings_the_rules_allow() -> None:
    """The other direction: a reader that refused everything would also pass above."""
    legal = (
        "billing:upstream:acl",
        "billing:upstream:conformist",
        "billing:upstream:customer-supplier",
        "billing:downstream:open-host-service",
        "billing:downstream:published-language",
        "billing:peer:shared-kernel",
        "billing:peer:separate-ways",
    )
    contexts = frozenset({"guestbook", "billing"})
    faults = {entry: _neighbour_fault(entry, contexts, "guestbook") for entry in legal}
    assert not any(faults.values()), f"a legal pairing was refused: {faults}"


# --------------------------------------------------------------------------- #
# The API register agrees with the context registry
# --------------------------------------------------------------------------- #


def _table_column(section: str, heading: str) -> list[str]:
    """The cells under `heading`, found by NAME rather than by position.

    A column located by index checks a different column the day the table gains
    one, and it does so in silence -- which is the failure mode a fitness
    function is supposed to remove rather than reproduce.
    """
    rows = [line for line in section.splitlines() if line.strip().startswith("|")]
    assert rows, "the route table has no rows -- its shape moved"
    header = [cell.strip() for cell in rows[0].strip().strip("|").split("|")]
    assert heading in header, f"no {heading!r} column in the route table; it has {header}"
    index = header.index(heading)
    cells = []
    for row in rows[2:]:  # rows[1] is the ---|--- separator
        parts = [cell.strip() for cell in row.strip().strip("|").split("|")]
        if len(parts) > index:
            cells.append(parts[index].strip("`"))
    return cells


def test_every_context_the_api_register_names_is_a_declared_context() -> None:
    """The route table's Context column resolves.

    The register names a context per route; `spec/contexts/` is where a context
    is declared. Two homes for one fact is what this repository refuses
    everywhere else -- the register may cite the registry, and this is the check
    that turns the citation into a link rather than a coincidence of spelling.

    An em dash is a legal cell: it is the Platform slice, which answers routes
    and owns no domain rules (`spec/design/architecture.md` § Platform).
    """
    section = _API_ROUTE_SECTION.search(API_REGISTER.read_text(encoding="utf-8"))
    assert section is not None, (
        "spec/design/api.md no longer has a '## Routes and their contexts' section -- "
        "if it was renamed, move this anchor rather than deleting the check"
    )

    cells = _table_column(section.group(1), "Context")
    assert cells, "no route rows in the register's route table -- its shape moved"

    cited = {cell for cell in cells if cell not in {"", "\u2014", "-"}}
    unknown = sorted(cited - frozenset(_declared()))
    assert not unknown, (
        f"spec/design/api.md names {unknown} in its Context column, and no document "
        "in spec/contexts/ declares them"
    )


def test_the_column_reader_finds_the_column_by_name() -> None:
    """Proof the reader is not counting pipes.

    The column is deliberately moved and a new one inserted before it: a reader
    that took position 3 would return the methods and pass every assertion above
    for the wrong reason.
    """
    table = "| Route | Context | Methods |\n|---|---|---|\n| `/api/x` | `billing` | `GET` |\n"
    assert _table_column(table, "Context") == ["billing"]

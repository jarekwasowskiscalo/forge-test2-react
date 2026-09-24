"""The directory a test lives in is its declaration, and this is what makes that true.

`tests/unit/`, `tests/fitness/` and `tests/tooling/` each carry a `conftest.py` that
marks everything below it `no_db`. That half is mechanical and cannot be forgotten.

The half that *can* rot is the converse: a test under `tests/integration/` carrying the
marker anyway would be collected on the macOS leg, where no Postgres is
provisioned, and fail there for a reason that has nothing to do with the platform. And a
test placed in `tests/unit/` that quietly opens a database would pass here and fail only
on a machine without Docker.

So both directions are checked, and the detector is proved against a known positive
first -- the house rule from `spec/design/testing.md`.
"""

import ast
import pathlib
import re
from typing import Final

from tests._repo import REPO_ROOT

TESTS: Final[pathlib.Path] = REPO_ROOT / "tests"

#: The directories whose `conftest.py` applies `no_db` to everything below.
WITHOUT_DATABASE: Final[tuple[str, ...]] = ("unit", "fitness", "tooling")

#: What a module has to name to be reaching for a database.
_DATABASE_NAMES: Final[frozenset[str]] = frozenset(
    {"SessionLocal", "fresh_database", "create_migrated_database", "isolated_database"}
)


def _names_used(path: pathlib.Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {
        node.id if isinstance(node, ast.Name) else node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Name | ast.Attribute)
    }


def test_every_group_that_claims_to_need_no_database_has_the_conftest_that_says_so() -> None:
    for group in WITHOUT_DATABASE:
        conftest = TESTS / group / "conftest.py"
        assert conftest.is_file(), f"tests/{group}/ marks nothing, so its tests are unmarked"
        assert "no_db" in conftest.read_text(encoding="utf-8")


def test_no_module_outside_integration_reaches_for_a_database() -> None:
    """The known positive is `tests/integration/` itself: run the same check there and it
    must find plenty, or this check is matching nothing and would pass on anything."""
    offenders = {
        f"tests/{group}/{path.name}"
        for group in WITHOUT_DATABASE
        for path in (TESTS / group).glob("test_*.py")
        if _names_used(path) & _DATABASE_NAMES
    }
    assert not offenders, (
        f"these name a database from a directory that declares it needs none: {sorted(offenders)}"
    )

    proof = {
        path.name
        for path in (TESTS / "integration").glob("test_*.py")
        if _names_used(path) & _DATABASE_NAMES
    }
    assert proof, "the detector matched nothing in tests/integration/, so it detects nothing"


def test_no_integration_module_marks_itself_no_db() -> None:
    """A `no_db` under `tests/integration/` is collected on a leg that provisions no
    Postgres, so it fails there for a reason unrelated to the platform it is testing."""
    offenders = [
        path.name
        for path in (TESTS / "integration").glob("test_*.py")
        if "no_db" in path.read_text(encoding="utf-8")
    ]
    assert not offenders, f"marked no_db but live under tests/integration/: {offenders}"


# --------------------------------------------------------------------------- #
# One place binds the database, and two named exceptions
# --------------------------------------------------------------------------- #

#: Modules allowed to rebind `SessionLocal` themselves. It binds exactly one
#: module on purpose -- it is about what happens to *that* module's storage, a
#: swap to a second database -- so discovery would bind more than the test is
#: talking about.
PERMITTED_BINDERS: Final[frozenset[str]] = frozenset({"test_storage_swap.py"})

#: The rebinding itself, not the word. A module that *mentions* `SessionLocal` in
#: a docstring is explaining the fixture; one that calls this is replacing it.
_REBIND: Final = re.compile(r'setattr\(\s*[\w.]+\s*,\s*["\']SessionLocal["\']')


def test_only_the_shared_fixture_discovers_which_modules_hold_a_session() -> None:
    """Five test modules used to rebind `SessionLocal` by naming two or three
    service modules each. `tests/conftest.py` *discovers* the holders instead, and
    the difference is not style: a service added later is bound by discovery and
    missed by a hand-written list -- missed silently, surfacing as another test's
    data appearing arbitrarily far from its cause. That is the failure
    `session_local_holders()` was written to prevent, and a copy of the list
    beside it puts the failure straight back.
    """
    offenders = {
        path.name
        for path in (TESTS / "integration").glob("test_*.py")
        if _REBIND.search(path.read_text(encoding="utf-8")) and path.name not in PERMITTED_BINDERS
    }
    assert not offenders, (
        f"these rebind SessionLocal themselves instead of asking for `fresh_database`: "
        f"{sorted(offenders)}"
    )

    proof = {path.name for path in (TESTS / "integration").glob("test_*.py")} & PERMITTED_BINDERS
    assert proof == PERMITTED_BINDERS, (
        f"the exception list names modules that are gone: {sorted(PERMITTED_BINDERS - proof)}"
    )


# --------------------------------------------------------------------------- #
# One engine, and it stays one
# --------------------------------------------------------------------------- #

#: Assembled rather than written, so this module can search for the word without
#: being the file that reintroduces it. The scan below skips its own path anyway;
#: the split is belt and braces, and it costs one line.
_SECOND_ENGINE: Final = "sql" + "ite"

#: Where first-party source lives. `.venv`, caches and vendored trees are not this
#: rule's business, and neither is `.claude`: that is the change process, independent
#: of this application, with a suite of its own -- and the one place the rule was
#: actually broken there (thirty-four mentions after the engine left the code on
#: 2026-08-31, two of them in the hook's Article XII table) is data now, the `runners`
#: table of `.specconf/stack.json`, which this template writes and this test reads.
_FIRST_PARTY: Final[tuple[str, ...]] = ("app", "tests", "scripts", "alembic", "e2e", ".specconf")

#: Prose counts, and that is the point. `architecture.md` § One engine says the escape
#: hatch was removed "in full ... and the documentation", and the documentation is what
#: outlived it: a SKILL.md telling an agent to prove a migration on an engine that is
#: gone is a wrong instruction, not a stale comment.
_SOURCE_SUFFIXES: Final[frozenset[str]] = frozenset({".py", ".md", ".sh"})

#: The one place allowed to say the word, because it exists to refuse it: `check.sh`
#: rejects the flag by name and points at the decision.
_MAY_NAME_IT: Final[frozenset[str]] = frozenset({"scripts/check.sh"})


def test_the_second_engine_does_not_come_back() -> None:
    """`spec/design/architecture.md` § One engine leaves one engine, and this is what keeps it at one.

    The removed one was not a dependency but a *branch*: a `connect_args` here, a
    provisioning route there, a marker naming the tests that could not hold on it.
    Every one of those came back cheap and individually defensible, and together
    they were a second supported backend nobody had decided to support.

    So the rule is the word, not the package. A module that names it is a module
    that has an opinion about a second engine, and this repository has exactly one
    place for that opinion: the ADR that says there is not one.
    """
    offenders = []
    for root in _FIRST_PARTY:
        for path in (REPO_ROOT / root).rglob("*"):
            if path.suffix not in _SOURCE_SUFFIXES or not path.is_file():
                continue
            if "__pycache__" in path.parts or path.resolve() == pathlib.Path(__file__).resolve():
                continue
            if path.relative_to(REPO_ROOT).as_posix() in _MAY_NAME_IT:
                continue
            text = path.read_text(encoding="utf-8")
            if _SECOND_ENGINE in text.lower():
                line = text.lower().index(_SECOND_ENGINE)
                offenders.append(
                    f"{path.relative_to(REPO_ROOT).as_posix()}:{text[:line].count(chr(10)) + 1}"
                )
    assert not offenders, (
        f"{_SECOND_ENGINE} is named in first-party source again: {offenders}. "
        "One engine is a decision (`spec/design/architecture.md` § One engine); a second one arrives as a branch nobody "
        "reviewed as a backend."
    )


def test_no_test_claims_it_cannot_hold_on_this_engine() -> None:
    """The marker that let a test opt out of the second engine is gone with it.

    A marker left registered but unused is a marker somebody reaches for, and the
    thing it used to mean -- "true on Postgres, false on the other one" -- has no
    referent now. `pyproject.toml` runs `--strict-markers`, so this also proves the
    registration went with it.
    """
    marker = "postgres" + "_only"
    users = sorted(
        path.relative_to(REPO_ROOT).as_posix()
        for root in (*_FIRST_PARTY, ".")
        for path in (REPO_ROOT / root).glob("*.py" if root == "." else "**/*.py")
        if "__pycache__" not in path.parts
        and path.resolve() != pathlib.Path(__file__).resolve()
        and marker in path.read_text(encoding="utf-8")
    )
    assert users == [], f"{marker} is used again in: {users}"


# --------------------------------------------------------------------------- #
# The fitness table in spec/design/testing.md names what actually exists
# --------------------------------------------------------------------------- #

#: A table row whose first cell is a backticked module name.
_FITNESS_TABLE_ROW: Final = re.compile(r"^\| `([^`]+)` \|", re.MULTILINE)


def test_the_fitness_table_in_the_testing_spec_matches_the_directory() -> None:
    """Every fitness module has a row, and every plain row names a fitness module.

    The table went stale in both directions at once: it never learned about
    `test_test_layout.py` and `test_script_twins.py` (470 lines of enforced
    rules invisible to a reader of the spec), and it listed `test_migrations.py`
    as a fitness function though that file lives in `tests/integration/` and
    needs a database. A normative document that missells what is enforced is
    how a rule gets deleted by someone who never learned it existed.
    """
    spec = (REPO_ROOT / "spec/design/testing.md").read_text(encoding="utf-8")
    section = re.search(r"## Fitness functions\n(.*?)(?:\n## |\Z)", spec, flags=re.DOTALL)
    assert section is not None, (
        "spec/design/testing.md no longer has a '## Fitness functions' section -- "
        "if it was renamed, update this test's anchor rather than deleting it"
    )
    named = set(_FITNESS_TABLE_ROW.findall(section.group(1)))
    # The change process's suite is not in this table: it lives beside the engine and
    # is the process's own (§ Where the change process lives), not a fitness function
    # of this application.
    plain = {name for name in named if "/" not in name}
    actual = {path.name for path in (TESTS / "fitness").glob("test_*.py")}

    missing = actual - plain
    assert not missing, f"fitness modules with no row in spec/design/testing.md: {sorted(missing)}"
    strangers = plain - actual
    assert not strangers, (
        f"rows naming modules that are not in tests/fitness/: {sorted(strangers)} -- "
        "a rule proved elsewhere belongs in that suite's own description, not here"
    )


# --------------------------------------------------------------------------- #
# No test cites the numbering of a specification that no longer exists
# --------------------------------------------------------------------------- #

#: The dead idioms, assembled by concatenation so this module never matches
#: itself. The bare "(6.7)" form -- 231 occurrences once -- was removed after
#: the 2026-08-14 audit; the word forms below survived that sweep. `\s+`
#: instead of a space and the optional plural are both from measurement: the
#: first draft of this pattern scanned line by line and missed
#: "Requirements 2.1 / 2.2" (the plural) and "(task\n2.1)" (wrapped across a
#: line break) in the very sweep it was written for.
_DEAD_NUMBERING: Final = re.compile(
    "|".join(
        (
            "Requirements" + r"\s+covered",
            "[Rr]equirements?" + r"\s+\d+\.\d+",
            "[Tt]asks?" + r"\s+\d+\.\d+",
        )
    )
)


def test_the_dead_numbering_detector_still_detects() -> None:
    """Proved on fabricated positives before the sweep below is trusted: a
    detector that has stopped matching passes everything, silently."""
    for sample in (
        "Requirements covered: 2.1, 2.3.",
        "Requirement 3.4: docker is reachable.",
        "Requirements 2.1 / 2.2: the app starts.",
        "Task 6.1. This is the load-bearing test.",
        "the narrow try/except (task\n    2.1) is meant to catch",
    ):
        assert _DEAD_NUMBERING.search(sample), f"the detector no longer matches: {sample!r}"


def test_no_test_module_cites_the_dead_numbering_scheme() -> None:
    """A reference that resolves to nothing reads as coverage and points at nothing.

    The 2026-08 audit measured 314 references to the numbering of a deleted
    `.kiro/specs/` tree; the live scheme is `@pytest.mark.req("CR-…/R-n")` and
    it is the only one a gate reads (`traceability`). The bare parenthesised form was
    removed then; the word forms kept accumulating in docstrings, where they
    look like traceability and trace nothing. New prose either cites a real
    requirement id or states the rule in its own words.
    """
    offenders = []
    for path in TESTS.rglob("test_*.py"):
        if path == pathlib.Path(__file__):
            continue
        text = path.read_text(encoding="utf-8")
        for match in _DEAD_NUMBERING.finditer(text):
            line = text[: match.start()].count("\n") + 1
            offenders.append(f"tests/{path.relative_to(TESTS)}:{line}")
    assert not offenders, f"{len(offenders)} citations of the dead numbering scheme: {offenders}"


# --------------------------------------------------------------------------- #
# A module that reaches the application from tests/integration/ isolates itself
# --------------------------------------------------------------------------- #

#: Imports that mean "this module drives the application" -- and so its writes
#: land in whatever database the session provisioned, unless it isolates.
_APP_REACHING_IMPORTS: Final[tuple[str, ...]] = (
    "app.main",
    "app.services",
    "app.routers",
    "fastapi.testclient",
    "starlette.testclient",
)

#: Modules excused from the isolation rule, each with the reason on record.
#: Empty today, deliberately: the three violators this rule was written for
#: were repaired (two) or deleted (one) in the same change that added it.
ISOLATION_EXCEPTIONS: Final[dict[str, str]] = {}


def _module_imports(tree: ast.Module) -> set[str]:
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def _fixture_args(tree: ast.Module) -> set[str]:
    return {
        arg.arg
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        for arg in node.args.args
    }


def test_every_integration_module_that_reaches_the_app_isolates_its_database() -> None:
    """Writes without isolation leak into every test that runs later.

    The incident on record: `test_services_items.py` seeded rows into the
    session database and its own docstring *explained the leak as a property*
    ("this test's own items persist for tests after it") -- a relic of an
    in-memory era that had ended. Its weakest assertion, `isinstance(items,
    list)`, passed on any database state whatsoever. Two more modules drove
    the app through `TestClient` POSTs with no isolation either.

    The rule: a module under `tests/integration/` that imports the
    application (or uses the `client` fixture) either asks for
    `fresh_database` (directly or through a delegating fixture), rebinds
    `SessionLocal` as one of the `PERMITTED_BINDERS`, or stands in
    `ISOLATION_EXCEPTIONS` with a reason.

    A fourth arm used to admit importing `tests._parity`, whose
    `_bind_fresh_database` isolated on the importer's behalf. That module was
    deleted with the second engine and the arm outlived it -- along with the
    follow-up assertion that read it off disk, and a failure message naming a
    regression test that has not existed for as long.
    """
    offenders = []
    for path in sorted((TESTS / "integration").glob("test_*.py")):
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=str(path))
        imports = _module_imports(tree)
        arguments = _fixture_args(tree)
        reaches = (
            any(imported.startswith(_APP_REACHING_IMPORTS) for imported in imports)
            or "client" in arguments
        )
        if not reaches:
            continue
        isolated = (
            "fresh_database" in arguments
            or "fresh_database" in _names_used(path)
            or bool(_REBIND.search(text))
            or path.name in ISOLATION_EXCEPTIONS
        )
        if not isolated:
            offenders.append(path.name)

    assert not offenders, (
        f"these reach the application without isolating a database: {offenders} -- "
        "take `fresh_database` as an argument (the pattern every test in "
        "test_guestbook_entries_router.py uses) or add a reasoned "
        "ISOLATION_EXCEPTIONS entry"
    )


def test_no_module_in_an_auto_marked_directory_carries_the_manual_mark() -> None:
    """The directory is the declaration; a manual mark beside it is a second one.

    21 of 30 files carried the module-level no_db pytestmark on top of the
    conftest that already applies it, 9 did not, and a reader could not tell
    whether the mark in any given file meant something extra. Two conventions
    for one fact drift independently; this keeps exactly one. The needle is
    assembled by concatenation so this module's own prose never trips it.
    """
    module_mark = "pytestmark = pytest.mark." + "no_db"
    # The per-function spelling, which the module-level check above missed entirely:
    # 45 decorators across four files survived a rule whose docstring says it keeps
    # exactly one convention. Two spellings of one fact drift exactly as two
    # conventions do -- and a decorator is the likelier of the two to be copied into
    # the next test, because it sits where the next test is written.
    function_mark = "@pytest.mark." + "no_db"
    offenders = []
    for group in WITHOUT_DATABASE:
        for path in (TESTS / group).glob("test_*.py"):
            text = path.read_text(encoding="utf-8")
            for spelling in (module_mark, function_mark):
                if spelling in text:
                    offenders.append(f"tests/{group}/{path.name} ({spelling})")
    assert not offenders, (
        f"the conftest already marks these directories; drop the manual mark: {offenders}"
    )

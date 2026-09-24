"""The three structural rules `e2e/` used to get from a separate virtualenv.

**The suite must not be able to import the application.** That is the whole
reason for having two test suites: `tests/` can reach into a service and check
an invariant, and `e2e/` cannot, so between them they cover both what the code
believes and what it actually serves. A scenario that imported `app` could
assert against the same object the application does and pass while the wire was
broken.

It used to be impossible rather than forbidden: the suite ran in a virtualenv of
its own that had no application in it. That also put it outside mypy, outside
pytest and outside `uv.lock`, and a bumped pin silently never reinstalled --
`ensure_e2e_venv` only checked that the venv existed. This file is what replaces
it, and the trade is deliberate: a rule that is checked, against three costs
that were not.

Two more rules ride along, both about the harness staying the only route to the
outside world. One module owns every HTTP request, so a timeout cannot be
forgotten at a new call site; one module owns every database connection, so the
guards on a function that deletes every row it can reach cannot be walked around.

**Every `.py` file under `e2e/` is checked, package initialisers included.** They
used to be skipped, on the unexamined assumption that an `__init__.py` holds
nothing but a docstring. All four of them do -- but `e2e/suite/steps/__init__.py`
is the natural home for a shared helper, and a rule that replaces a physical
guarantee cannot afford a file it never looks at: an `import app.services.cases`
or an `httpx.Client(...)` there would have passed all three checks in silence.

Each check reads the source with `ast` rather than importing it, so a violation
is reported as the file and line it is on. And each one is pointed at a known
positive **first**: a detector that has stopped detecting passes every file, and
it does so silently, exactly when the rule has started being broken.
"""

import ast
import pathlib
from typing import Final

import pytest

from tests._repo import REPO_ROOT

E2E: Final[pathlib.Path] = REPO_ROOT / "e2e"

#: The packages `e2e/` may not reach. `e2e` itself is absent -- the suite
#: importing its own harness is the design. `tests` is present, with exactly one
#: named exception below rather than a prefix match: `tests/conftest.py` imports
#: the application, so a blanket `tests.*` allowance would be a hole straight
#: through the rule this file exists for.
FIRST_PARTY: Final[frozenset[str]] = frozenset({"app", "alembic", "scripts", "tests"})

#: The one crossing, and the only one. `tests/_golden_set.py` is where
#: `golden-set/` is located; it imports nothing but `json`, `pathlib` and
#: `typing`, and the alternative is a hand-copied twin, which is what this
#: repository had until the two quietly diverged in return type and exception
#: type.
#:
#: A second entry here is a scenario that can reach the same objects the
#: application does -- and such a scenario passes while the wire is broken.
PERMITTED_CROSSING: Final[tuple[str, str]] = ("e2e/suite/golden_set.py", "tests._golden_set")

#: Dynamic imports are refused outright rather than inspected. `import_module`,
#: `__import__` and `spec_from_file_location` all take a name or a path that is
#: usually computed, so there is nothing for a static check to read -- and none
#: of them has a legitimate use in a suite whose imports are all known at
#: authoring time.
DYNAMIC_IMPORTS: Final[frozenset[str]] = frozenset(
    {"import_module", "__import__", "spec_from_file_location", "load_module", "exec_module"}
)

#: Rule 2 and rule 3: the outside world, and the one module allowed to reach it.
GATEWAYS: Final[tuple[tuple[str, str, str], ...]] = (
    ("httpx", "e2e/harness/client.py", "every HTTP request"),
    ("psycopg", "e2e/harness/database.py", "every database connection"),
)

#: The package initialiser that made the old `__init__.py` exclusion a real hole
#: rather than a theoretical one: it is the obvious place to put a helper shared
#: by the three step modules, and it was exempt from all three rules.
STEPS_INITIALISER: Final[str] = "e2e/suite/steps/__init__.py"

#: A module that breaks all three rules at once, used to prove each detector can
#: see a violation at all. It is a string rather than a file because two of the
#: three rules have no legitimate in-tree positive to point at.
KNOWN_POSITIVE: Final[str] = """
import httpx
import psycopg
import app.services.cases
from tests.conftest import client
from importlib import import_module

module = import_module("app.main")
"""


def _modules() -> list[pathlib.Path]:
    """Every Python file under `e2e/`, package initialisers included.

    The `if path.name != "__init__.py"` that used to be here was a hole in all
    three rules at once, and a silent one: nothing fails when a check stops
    looking at a file, it just stops covering it.
    """
    return sorted(E2E.rglob("*.py"))


def _label(path: pathlib.Path) -> str:
    """A repository-relative path with forward slashes, on every platform.

    `str(relative_to(...))` renders `e2e\\suite\\golden_set.py` on Windows, which
    matches neither `PERMITTED_CROSSING` nor a `GATEWAYS` entry -- so the exemption
    and the gateway skip both silently stopped applying and this file failed on the
    cross-platform leg while passing on macOS. Paths
    that are compared against a literal are normalised; paths that are only
    printed would not need it, and the distinction is not worth remembering.
    """
    return path.relative_to(REPO_ROOT).as_posix()


def _first_party_imports(source: str, label: str, allowed: str | None = None) -> list[str]:
    """Every reach into another package from `source`, as `label:line what`."""
    found = []
    for node in ast.walk(ast.parse(source, filename=label)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in FIRST_PARTY and alias.name != allowed:
                    found.append(f"{label}:{node.lineno} import {alias.name}")
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            if node.module.split(".")[0] in FIRST_PARTY and node.module != allowed:
                found.append(f"{label}:{node.lineno} from {node.module} import ...")
        elif isinstance(node, ast.Call):
            name = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
            if name in DYNAMIC_IMPORTS:
                found.append(f"{label}:{node.lineno} {name}(...) -- imports dynamically")
    return found


def _references(source: str, label: str, package: str) -> list[str]:
    """Every mention of `package` in `source`, however it was reached.

    An import, a `from` import and an attribute access on the module object are
    the same violation reached three ways, and checking only the first would
    leave the other two open.
    """
    found = []
    for node in ast.walk(ast.parse(source, filename=label)):
        if isinstance(node, ast.Import):
            found += [
                f"{label}:{node.lineno} import {alias.name}"
                for alias in node.names
                if alias.name.split(".")[0] == package
            ]
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            if node.module.split(".")[0] == package:
                found.append(f"{label}:{node.lineno} from {node.module} import ...")
        elif isinstance(node, ast.Attribute) and getattr(node.value, "id", None) == package:
            found.append(f"{label}:{node.lineno} reaches {package}.{node.attr}")
    return found


def test_the_rules_below_are_applied_to_every_file_including_package_initialisers() -> None:
    """The scope of the two tests below, asserted rather than assumed.

    `_modules()` excluded `__init__.py` for as long as this file existed, so
    `e2e/suite/steps/__init__.py` was exempt from the rule that the suite may not
    import the application. Narrowing the scope again would fail no assertion
    below -- it would quietly stop covering something -- so the scope is itself
    the assertion.
    """
    labels = {_label(path) for path in _modules()}

    initialisers = sorted(label for label in labels if label.endswith("__init__.py"))
    assert initialisers, (
        "no package initialiser is in scope, so the three rules below are not being "
        f"applied to one. Files found: {sorted(labels)}"
    )
    assert STEPS_INITIALISER in initialisers, (
        f"{STEPS_INITIALISER} is not being checked. It is the obvious home for a helper "
        f"shared between step modules, which is exactly why it must not be exempt: "
        f"initialisers in scope are {initialisers}"
    )


def test_no_e2e_module_imports_first_party_code() -> None:
    """The rule the deleted virtualenv used to enforce by construction."""
    assert _first_party_imports(KNOWN_POSITIVE, "<known positive>"), (
        "the first-party-import detector found nothing in a module that imports `app`, "
        "`tests` and `importlib`, so a passing result below would mean nothing"
    )

    modules = _modules()
    assert modules, "e2e/ has no modules to check -- has the layout moved?"

    permitted_file, permitted_module = PERMITTED_CROSSING
    #: Checked against the labels rather than the filesystem. `is_file()` would
    #: have been satisfied on Windows while the exemption still failed to apply,
    #: because the label was rendered with backslashes and never equalled this
    #: constant -- which is exactly how this file failed on the cross-platform
    #: leg and passed everywhere else.
    assert permitted_file in {_label(path) for path in modules}, (
        f"{permitted_file} is the one exemption to this rule and no module in the tree "
        "carries that label. An exemption that matches nothing does not fail -- it just "
        "stops applying, and the file it was written for is reported as a violation"
    )

    offenders: dict[str, list[str]] = {}
    for path in modules:
        label = _label(path)
        allowed = permitted_module if label == permitted_file else None
        reaches = _first_party_imports(path.read_text(encoding="utf-8"), label, allowed)
        if reaches:
            offenders[label] = reaches

    assert offenders == {}, (
        "the end-to-end suite asserts only what an HTTP client can see, so it may not "
        "import the application or the other suite -- a scenario that could reach the "
        f"same objects the application does would pass while the wire was broken: {offenders}"
    )


@pytest.mark.parametrize(("package", "gateway", "what"), GATEWAYS)
def test_one_module_owns_the_outside_world(package: str, gateway: str, what: str) -> None:
    """`httpx` and `psycopg` each have exactly one door into this tree.

    The gateway is the known positive: it must reach its package, that is its
    whole job, so a detector that cannot see it there would pass over every
    other module for the wrong reason.
    """
    assert _references(KNOWN_POSITIVE, "<known positive>", package), (
        f"the {package} detector found nothing in a module that imports it, so a passing "
        "result below would mean nothing"
    )

    modules = _modules()
    assert gateway in {_label(path) for path in modules}, (
        f"{gateway} is named as the one module allowed to reach {package}, and no module "
        "in the tree carries that label -- so the skip below never fires and the gateway "
        "reports itself as a violation"
    )

    owner = REPO_ROOT / gateway
    assert _references(owner.read_text(encoding="utf-8"), gateway, package), (
        f"{gateway} is supposed to be the one module that reaches {package}, and the "
        "detector cannot see it doing so"
    )

    offenders: dict[str, list[str]] = {}
    for path in modules:
        label = _label(path)
        if label == gateway:
            continue
        reaches = _references(path.read_text(encoding="utf-8"), label, package)
        if reaches:
            offenders[label] = reaches

    assert offenders == {}, (
        f"{gateway} owns {what} in this suite, so the guards it carries -- the timeout, "
        f"the refusal to empty a database it does not recognise -- cannot be walked "
        f"around by a new call site: {offenders}"
    )

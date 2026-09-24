"""The UI smoke suite's two boundaries, held as code (`spec/design/testing.md` § The UI smoke in a browser).

Playwright is allowed in exactly one directory, and the Gherkin machinery is
allowed everywhere *but* that directory. Both boundaries are the decision's
enforcement arm: the browser leaking into `tests/` or `e2e/suite/` would let an
"integration" test quietly become a UI test outside the artefact policy, and a
`.feature` under `e2e/ui/` would be the costume `spec/design/testing.md` § The UI smoke in a browser explicitly refuses --
smoke is an engineering tool, the business-readable artefact lives in
`e2e/suite/features/`.

The import rule is proved on a known positive: `e2e/ui/conftest.py` must import
playwright, so a rule whose scan broke reports the missing positive instead of
a clean tree.
"""

import ast
import pathlib
from typing import Final

REPO_ROOT: Final = pathlib.Path(__file__).resolve().parents[2]

#: Where first-party Python lives. `.venv`, caches and vendored trees are not
#: this rule's business.
_SCANNED_ROOTS: Final[tuple[str, ...]] = ("app", "tests", "e2e", "scripts", "alembic")

_UI_PREFIX: Final = "e2e/ui/"


def _imports_of(path: pathlib.Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            found.add(node.module.split(".")[0])
    return found


def _python_files() -> list[pathlib.Path]:
    return sorted(
        path
        for root in _SCANNED_ROOTS
        for path in (REPO_ROOT / root).rglob("*.py")
        if "__pycache__" not in path.parts
    )


def test_playwright_is_imported_under_e2e_ui_and_nowhere_else() -> None:
    inside: list[str] = []
    outside: list[str] = []
    for path in _python_files():
        if "playwright" not in _imports_of(path):
            continue
        relative = path.relative_to(REPO_ROOT).as_posix()
        (inside if relative.startswith(_UI_PREFIX) else outside).append(relative)

    assert not outside, (
        f"playwright imported outside {_UI_PREFIX}: {outside}. The browser belongs to "
        "the smoke suite alone -- anywhere else it is a UI test running outside the "
        "artefact policy of e2e/ui/conftest.py (`spec/design/testing.md` § The UI smoke in a browser)."
    )
    # The known positive: the conftest must hold the browser, or this scan is
    # reporting a clean tree because it stopped seeing imports at all.
    assert "e2e/ui/conftest.py" in inside


def test_the_smoke_suite_has_no_gherkin() -> None:
    """No `.feature` files and no pytest_bdd import under `e2e/ui/` -- the smoke
    is plain pytest by decision, not by omission."""
    ui = REPO_ROOT / "e2e" / "ui"
    features = sorted(str(p.relative_to(REPO_ROOT)) for p in ui.rglob("*.feature"))
    assert features == [], f"Gherkin artefacts under {_UI_PREFIX}: {features}"

    bdd_importers = sorted(
        path.relative_to(REPO_ROOT).as_posix()
        for path in ui.rglob("*.py")
        if "__pycache__" not in path.parts and "pytest_bdd" in _imports_of(path)
    )
    assert bdd_importers == [], (
        f"pytest_bdd imported under {_UI_PREFIX}: {bdd_importers}. The smoke suite is "
        "plain pytest (`spec/design/testing.md` § The UI smoke in a browser); scenarios for a non-programmer live in e2e/suite/."
    )


def test_the_plugin_the_decision_refused_is_not_installed() -> None:
    """`pytest-playwright` stays out of the lockfile.

    The plugin's CLI (`--screenshot`, `--video`, `--tracing`) is the Article XI
    risk surface `spec/design/testing.md` § The UI smoke in a browser names; one `uv add` would hand every future run a
    recording switch this suite must not have.
    """
    lock = (REPO_ROOT / "uv.lock").read_text(encoding="utf-8")
    assert 'name = "pytest-playwright"' not in lock
    # And the bare package really is here -- the other half, so this test cannot
    # pass by scanning the wrong lockfile.
    assert 'name = "playwright"' in lock

"""A bounded context has a public API, and reaching past it fails the build.

`app/contexts/<name>/` and `frontend/src/contexts/<name>/` are the whole of a
context. What another context may know about it is what its package exports --
`app/contexts/<name>/__init__.py` -- and nothing else. sdd31 puts the rule as
"declare a package's public API and catch every boundary violation in a pull
request"; sdd107 says why it stopped being optional the moment agents write the
code: an agent feels no cultural friction. It can wire itself into the deepest
undocumented method of a neighbouring package in seconds, pass every local test,
and leave the architecture broken in a way no diff shows.

Four rules:

- **No context reaches into another's internals.** `app.contexts.b` is legal from
  `app/contexts/a/`; `app.contexts.b.services.x` is not. The first is a contract,
  the second is a coupling to a decision `b` is entitled to change.
- **Only the composition root reaches a context's wiring.** `app/api.py` imports
  router modules because that is what a composition root does. Nothing else
  outside `app/contexts/` may.
- **Registration is checked in both directions.** A directory under
  `app/contexts/` that no aggregate names is a context whose tables never reach
  `Base.metadata` and whose routes are never mounted -- and it fails no test,
  because there is nothing to run. A name in an aggregate with no directory
  behind it is the same failure from the other end.
- **The frontend mirrors it**, with `frontend/src/router.tsx` as its composition
  root.

**Every rule here is vacuously true today**: there is one context, so no import
can cross a boundary that does not exist. That is exactly why each carries a
known positive over synthetic input -- a check that cannot be shown to fail is a
check nobody has reason to believe, and this one has to still work on the day a
second context arrives, which is the day nobody will re-read it.

Reads source with `ast` for Python and with a regular expression for TypeScript,
so a violation is reported as a file and a line rather than as an import-time
crash. No database, no application import.

**Relative imports are resolved, not ignored.** The first version of this file read
`from app.contexts.b.services import x` and nothing else, so
`from ...b.services import x` -- the same crossing, spelled relatively -- walked
straight through, and so did `'../../billing/lib/invoice'` on the frontend. A
boundary that holds only against one spelling of the import is a boundary with a
door in it (2026-09-08 audit).
"""

import ast
import pathlib
import re
from typing import Final

import pytest

from tests._repo import REPO_ROOT

CONTEXTS: Final[pathlib.Path] = REPO_ROOT / "app" / "contexts"
WEB_CONTEXTS: Final[pathlib.Path] = REPO_ROOT / "frontend" / "src" / "contexts"

#: The one module outside `app/contexts/` allowed to import a context's
#: submodules, and the reason it is allowed: it is where the routers are mounted.
COMPOSITION_ROOT: Final[str] = "app/api.py"

#: Its frontend counterpart.
WEB_COMPOSITION_ROOT: Final[str] = "frontend/src/router.tsx"

#: `from '@/contexts/<name>/<rest>'` in TypeScript, single or double quoted.
_WEB_IMPORT: Final = re.compile(r"""from\s+['"]@/contexts/([A-Za-z0-9_-]+)(/[^'"]*)?['"]""")

#: `from './x'` and `from '../../billing/lib/invoice'` -- the relative spelling.
_WEB_RELATIVE: Final = re.compile(r"""from\s+['"](\.\.?/[^'"]*)['"]""")


def _context_names() -> list[str]:
    return sorted(
        path.name for path in CONTEXTS.iterdir() if path.is_dir() and path.name != "__pycache__"
    )


def _python_modules(root: pathlib.Path) -> list[pathlib.Path]:
    return sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)


def _package_of(path: pathlib.Path) -> list[str]:
    """The dotted package a module's relative imports are resolved against."""
    parts = list(path.relative_to(REPO_ROOT).with_suffix("").parts)
    parts.pop()  # the module's own name, or `__init__` -- either way, its package
    return parts


def _resolve_relative(package: list[str], level: int, module: str | None) -> str:
    """`from ..b.services import x` inside `app/contexts/a/services/y.py` is
    `app.contexts.b.services` -- what `ast` gives as `level=2, module='b.services'`."""
    base = package[: len(package) - (level - 1)] if level > 1 else list(package)
    return ".".join(base + (module.split(".") if module else []))


def _imported_modules(path: pathlib.Path) -> list[tuple[int, str]]:
    """Every `app.*` module `path` imports, as (line, dotted name), relative
    imports resolved to their absolute name first."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found += [
                (node.lineno, alias.name)
                for alias in node.names
                if alias.name == "app" or alias.name.startswith("app.")
            ]
        elif isinstance(node, ast.ImportFrom):
            module = (
                _resolve_relative(_package_of(path), node.level, node.module)
                if node.level
                else node.module
            )
            if module is None or not (module == "app" or module.startswith("app.")):
                continue
            # `from app.contexts import guestbook` names the context in the
            # alias, not in the module -- a reader that missed that would bless
            # the aggregate and every file shaped like it.
            found.append((node.lineno, module))
            found += [(node.lineno, f"{module}.{alias.name}") for alias in node.names]
    return found


def _reaches_past_the_api(module: str, *, mine: str | None) -> str | None:
    """The context whose internals `module` reaches, or None when it reaches none.

    `app.contexts.b` is the public API and always legal. `app.contexts.b.x` is
    the violation, and it is a violation from anywhere except the composition
    root -- including from context `b` itself, where it is simply normal and is
    filtered out by `mine`.
    """
    parts = module.split(".")
    if len(parts) < 4 or parts[:2] != ["app", "contexts"]:
        return None
    other = parts[2]
    return None if other == mine else other


# --------------------------------------------------------------------------- #
# No context reaches into another's internals
# --------------------------------------------------------------------------- #


def test_no_context_imports_another_contexts_internals() -> None:
    """The rule. Vacuously true with one context; the detector is proved below."""
    offenders: dict[str, list[str]] = {}
    for name in _context_names():
        for path in _python_modules(CONTEXTS / name):
            crossings = [
                f"line {line}: {module} (reaches into `{other}`)"
                for line, module in _imported_modules(path)
                if (other := _reaches_past_the_api(module, mine=name)) is not None
            ]
            if crossings:
                offenders[str(path.relative_to(REPO_ROOT))] = crossings

    assert offenders == {}, (
        "a context may import another context's package (`app.contexts.<name>`) and "
        f"nothing below it -- see app/contexts/<name>/__init__.py. These reach past it: {offenders}"
    )


def test_only_the_composition_root_reaches_a_contexts_wiring() -> None:
    """`app/api.py` mounts routers; nothing else outside a context may."""
    offenders: dict[str, list[str]] = {}
    for path in _python_modules(REPO_ROOT / "app"):
        relative = path.relative_to(REPO_ROOT).as_posix()
        if relative.startswith("app/contexts/") or relative == COMPOSITION_ROOT:
            continue
        crossings = [
            f"line {line}: {module}"
            for line, module in _imported_modules(path)
            if _reaches_past_the_api(module, mine=None) is not None
        ]
        if crossings:
            offenders[relative] = crossings

    assert offenders == {}, (
        f"only {COMPOSITION_ROOT} may reach a context's submodules -- everything else "
        f"imports `app.contexts.<name>` and takes what that package exports: {offenders}"
    )


def test_the_composition_root_really_does_reach_one() -> None:
    """The live positive. Without it the two checks above pass on a blind reader."""
    reached = [
        module
        for _, module in _imported_modules(REPO_ROOT / COMPOSITION_ROOT)
        if _reaches_past_the_api(module, mine=None) is not None
    ]
    assert reached, (
        f"{COMPOSITION_ROOT} imports no context submodule, so the detector above found "
        "nothing to find and a passing result means nothing"
    )


@pytest.mark.parametrize(
    ("module", "mine", "expected"),
    [
        ("app.contexts.billing.services.invoices", "guestbook", "billing"),
        ("app.contexts.billing.models", "guestbook", "billing"),
        ("app.contexts.billing", "guestbook", None),  # the public API, always legal
        ("app.contexts.guestbook.services.x", "guestbook", None),  # its own internals
        ("app.db.session", "guestbook", None),  # infrastructure, shared by all
        ("app.platform.schemas.refusals", "guestbook", None),  # the shared envelope
    ],
)
def test_the_boundary_reader_tells_a_crossing_from_a_contract(
    module: str, mine: str, expected: str | None
) -> None:
    """The known positives, one per way the reader could be wrong.

    This is where the rule lives today. With one context nothing can cross, so
    the sweeps above would pass over a reader that always answered None.
    """
    assert _reaches_past_the_api(module, mine=mine) == expected


@pytest.mark.parametrize(
    ("package", "level", "module", "expected"),
    [
        # from ...billing.services import x   (in app/contexts/guestbook/services/y.py)
        (
            ["app", "contexts", "guestbook", "services"],
            3,
            "billing.services",
            "app.contexts.billing.services",
        ),
        # from ..models import guestbook_entry (in app/contexts/guestbook/services/y.py)
        (
            ["app", "contexts", "guestbook", "services"],
            2,
            "models",
            "app.contexts.guestbook.models",
        ),
        # from . import x                      (in app/contexts/guestbook/__init__.py)
        (["app", "contexts", "guestbook"], 1, None, "app.contexts.guestbook"),
        # from .routers import x               (in app/contexts/guestbook/__init__.py)
        (["app", "contexts", "guestbook"], 1, "routers", "app.contexts.guestbook.routers"),
    ],
)
def test_a_relative_import_resolves_to_the_module_it_names(
    package: list[str], level: int, module: str | None, expected: str
) -> None:
    """The relative spelling of a crossing lands on the same name as the absolute one,
    so `_reaches_past_the_api` judges both alike."""
    resolved = _resolve_relative(package, level, module)
    assert resolved == expected
    assert _reaches_past_the_api(resolved, mine="guestbook") == (
        "billing" if "billing" in expected and len(expected.split(".")) >= 4 else None
    )


def test_the_relative_reader_sees_the_crossing_in_real_source(tmp_path: pathlib.Path) -> None:
    """End to end over a synthetic file placed where a context module would be."""
    target = tmp_path / "app" / "contexts" / "guestbook" / "services" / "probe.py"
    target.parent.mkdir(parents=True)
    target.write_text("from ...billing.services.invoices import total\n", encoding="utf-8")
    package = list(target.relative_to(tmp_path).with_suffix("").parts)[:-1]
    resolved = _resolve_relative(package, 3, "billing.services.invoices")
    assert _reaches_past_the_api(resolved, mine="guestbook") == "billing"


# --------------------------------------------------------------------------- #
# Registration, both ways
# --------------------------------------------------------------------------- #


def _registered_in(path: pathlib.Path) -> set[str]:
    """The contexts an aggregate names, read from its imports rather than its prose."""
    return {
        other
        for _, module in _imported_modules(path)
        if (parts := module.split("."))[:2] == ["app", "contexts"] and len(parts) >= 3
        for other in (parts[2],)
    }


def test_every_context_directory_is_registered_and_every_registration_exists() -> None:
    """A context nothing imports has no tables in the metadata and no mounted routes.

    Nothing fails when that happens: there is no code to run and no test to go
    red. The aggregate is an explicit list precisely so this can be asked, and
    asked in both directions.
    """
    on_disk = set(_context_names())
    assert on_disk, "app/contexts/ holds no context -- has the tree moved?"

    for aggregate in (CONTEXTS / "__init__.py", REPO_ROOT / COMPOSITION_ROOT):
        registered = _registered_in(aggregate)
        relative = aggregate.relative_to(REPO_ROOT).as_posix()
        assert not (missing := on_disk - registered), (
            f"{relative} names no context for {sorted(missing)}, so its tables never "
            "reach Base.metadata and its routes are never mounted -- silently"
        )
        assert not (dangling := registered - on_disk), (
            f"{relative} registers {sorted(dangling)}, and there is no such directory "
            "under app/contexts/"
        )


def test_the_registration_sweep_detects_both_directions() -> None:
    """Proof the set arithmetic above can fail, on input this repository does not hold."""
    on_disk, registered = {"guestbook", "billing"}, {"guestbook", "shipping"}
    assert on_disk - registered == {"billing"}
    assert registered - on_disk == {"shipping"}


# --------------------------------------------------------------------------- #
# The specification and the code agree on which contexts exist
# --------------------------------------------------------------------------- #


def test_every_context_document_has_code_and_every_context_directory_has_a_document() -> None:
    """The spec-to-code link is the NAME, so there is nothing to keep in sync.

    `spec/contexts/<name>.md`, `app/contexts/<name>/` and (where the context has
    a screen) `frontend/src/contexts/<name>/`. A declared key mapping one to the
    other would be a second home for a fact the file system already holds, and
    the second home is the one that goes stale.

    The frontend half is conditional on the context declaring a screen, because
    a context with no screen is a real thing and demanding an empty directory for
    it would teach people to create empty directories.
    """
    from tests import _frontmatter as frontmatter

    documented = {path.stem for path in sorted((REPO_ROOT / "spec/contexts").glob("*.md"))}
    in_code = set(_context_names())
    assert documented, "spec/contexts/ holds no context document"

    assert not (undocumented := in_code - documented), (
        f"app/contexts/{sorted(undocumented)} has no document under spec/contexts/. "
        "Code with no specification is behaviour nobody described (the constitution, "
        "article I)"
    )
    assert not (unbuilt := documented - in_code), (
        f"spec/contexts/{sorted(unbuilt)}.md describes a context with no directory under "
        "app/contexts/. A context is a directory here, and that is what makes it ownable"
    )

    for name in sorted(documented):
        header = frontmatter.read(REPO_ROOT / "spec/contexts" / f"{name}.md")
        if frontmatter.as_list(header["screens"]):
            assert (WEB_CONTEXTS / name).is_dir(), (
                f"spec/contexts/{name}.md declares a screen, and there is no "
                f"frontend/src/contexts/{name}/ for it to live in"
            )


# --------------------------------------------------------------------------- #
# The frontend mirrors it
# --------------------------------------------------------------------------- #


def _web_modules(root: pathlib.Path) -> list[pathlib.Path]:
    return sorted(
        path
        for pattern in ("*.ts", "*.tsx")
        for path in root.rglob(pattern)
        if "node_modules" not in path.parts
    )


def test_no_screen_reaches_into_another_contexts_folder() -> None:
    """The same rule on the other side of the wire, and the same exception.

    `frontend/src/router.tsx` is the composition root: it binds a path to a
    screen, which is exactly the frontend's version of mounting a router.
    """
    offenders: dict[str, list[str]] = {}
    web_root = REPO_ROOT / "frontend" / "src"
    for path in _web_modules(web_root):
        relative = path.relative_to(REPO_ROOT).as_posix()
        if relative == WEB_COMPOSITION_ROOT:
            continue
        mine: str | None = None
        if WEB_CONTEXTS in path.parents:
            mine = path.relative_to(WEB_CONTEXTS).parts[0]
        source = path.read_text(encoding="utf-8")
        crossings = [
            f"@/contexts/{other}{rest or ''}"
            for other, rest in _WEB_IMPORT.findall(source)
            if other != mine
        ]
        crossings += [
            f"{target} (reaches into `{other}`)"
            for target in _WEB_RELATIVE.findall(source)
            if (other := _web_context_of(path, target)) is not None and other != mine
        ]
        if crossings:
            offenders[relative] = crossings

    assert offenders == {}, (
        f"a screen belongs to its context; only {WEB_COMPOSITION_ROOT} binds one to a "
        f"route. These reach across: {offenders}"
    )


def _web_context_of(importer: pathlib.Path, target: str) -> str | None:
    """The context a relative import lands in, or None when it lands outside every
    context. Resolved against the importing file, the way the bundler resolves it."""
    landed = (importer.parent / target).resolve()
    try:
        return landed.relative_to(WEB_CONTEXTS.resolve()).parts[0]
    except ValueError:
        return None


def test_the_web_import_reader_sees_a_crossing() -> None:
    """The known positive: proof the expression matches what it claims to match."""
    source = "import { X } from '@/contexts/billing/lib/invoice'\nimport { Y } from '@/lib/cn'\n"
    assert _WEB_IMPORT.findall(source) == [("billing", "/lib/invoice")]
    assert _WEB_IMPORT.findall("import { Z } from '@/contexts/billing'") == [("billing", "")]


def test_the_web_relative_reader_sees_a_crossing() -> None:
    """The relative spelling lands in the same context as the aliased one."""
    importer = WEB_CONTEXTS / "guestbook" / "pages" / "GuestbookPage.tsx"
    assert _WEB_RELATIVE.findall("import { X } from '../../billing/lib/invoice'") == [
        "../../billing/lib/invoice"
    ]
    assert _web_context_of(importer, "../../billing/lib/invoice") == "billing"
    assert _web_context_of(importer, "../components/EntryCard") == "guestbook"
    assert _web_context_of(importer, "../../../lib/cn") is None

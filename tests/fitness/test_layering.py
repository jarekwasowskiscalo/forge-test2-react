"""The structural rules nothing else enforces.

Stated in `spec/design/conventions.md` and repeated in every module docstring
they govern, and broken -- historically -- by code that read as perfectly
reasonable:

- **No framework below the router.** A service, model or schema module that
  imports `fastapi` cannot be called from anything but a request, which is how a
  business rule becomes untestable without a client and unusable from a future
  scheduled job.
- **Dependencies point one way.** `routers` -> `services` -> `models`/`schemas`.
  A service importing a router, or a model importing a service, is a cycle that
  works until the day something imports the other half first.

Each check reads the source with `ast` rather than importing it, so a violation
is reported as the file and line it is on rather than as an import-time crash.
"""

import ast
import pathlib
from typing import Final

from tests._repo import REPO_ROOT

APP: Final[pathlib.Path] = REPO_ROOT / "app"

#: Where a layer directory can sit. The outermost cut is the bounded context
#: (`app/contexts/<name>/`) plus the one supporting technical slice
#: (`app/platform/`); the layer is a directory INSIDE one of those, not above
#: them. Layering did not change when the tree was recut -- only the depth at
#: which the layer directories are found -- so this is a glob rather than a list,
#: and a context added tomorrow is covered without editing this file.
LAYER_ROOTS: Final[tuple[str, ...]] = ("contexts/*", "platform")

#: The layers that must stay callable without a request in flight.
FRAMEWORK_FREE_PACKAGES: Final[tuple[str, ...]] = ("services", "models", "schemas")

#: Importing either of these is what makes a module framework-bound; the check
#: is on the top-level package name, so `from starlette.requests import Request`
#: is caught as readily as `import fastapi`.
FRAMEWORK_ROOTS: Final[frozenset[str]] = frozenset({"fastapi", "starlette"})


def _modules(package: str) -> list[pathlib.Path]:
    """Every module of one layer, wherever that layer sits.

    `app/services/x.py` became `app/contexts/<context>/services/x.py`, so a
    helper that took one fixed directory would now find nothing and the assert
    below it would be the only thing standing between a silent pass and a rule
    nobody checks.
    """
    found: list[pathlib.Path] = []
    for root in LAYER_ROOTS:
        for layer in APP.glob(f"{root}/{package}"):
            found += (path for path in layer.rglob("*.py") if path.name != "__init__.py")
    return sorted(found)


def _all_modules() -> list[pathlib.Path]:
    return sorted(path for path in APP.rglob("*.py") if path.name != "__init__.py")


def _framework_imports(path: pathlib.Path) -> list[str]:
    """Every framework import in `path`, as `line: statement` for the failure text."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in FRAMEWORK_ROOTS:
                    found.append(f"{path.name}:{node.lineno} import {alias.name}")
        elif (
            isinstance(node, ast.ImportFrom)
            and node.module is not None
            and node.module.split(".")[0] in FRAMEWORK_ROOTS
        ):
            found.append(f"{path.name}:{node.lineno} from {node.module} import ...")
    return found


def test_no_service_model_or_schema_module_imports_the_web_framework() -> None:
    """The rule, and proof the check can see a violation at all.

    The detector is pointed at the import router first. That module *does*
    import `fastapi`, legitimately, and a check that cannot see it there would
    pass over every package below it for the wrong reason -- silently, and
    exactly when the rule started being broken.
    """
    router = APP / "contexts" / "guestbook" / "routers" / "guestbook_entries.py"
    assert _framework_imports(router), (
        "the framework-import detector found nothing in a router that imports FastAPI, "
        "so a passing result below would mean nothing"
    )

    offenders: dict[str, list[str]] = {}
    scanned = 0
    for package in FRAMEWORK_FREE_PACKAGES:
        modules = _modules(package)
        assert modules, (
            f"no module found in any app/*/{package}/ -- the layer directories moved "
            "and this check would otherwise pass by finding nothing"
        )
        scanned += len(modules)
        for path in modules:
            imports = _framework_imports(path)
            if imports:
                offenders[f"{package}/{path.name}"] = imports

    assert offenders == {}, (
        "these modules must stay callable without a request in flight, but import the "
        f"web framework: {offenders}"
    )
    assert scanned >= 3


# --------------------------------------------------------------------------- #
# Dependencies point one way: routers -> services -> models/schemas
# --------------------------------------------------------------------------- #

#: Who may not import whom, exactly as `spec/design/conventions.md` puts it:
#: "A service importing a router, or a model importing a service, is a defect."
#: Sibling traffic (models <-> schemas) is deliberately not legislated here,
#: because the convention does not legislate it either.
_UPWARD_FORBIDDEN: Final[dict[str, tuple[str, ...]]] = {
    "models": ("services", "routers"),
    "schemas": ("services", "routers"),
    "services": ("routers",),
}


def _app_imports(path: pathlib.Path) -> list[tuple[int, str]]:
    """Every `app.*` import in `path`, as (line, module). Absolute only --
    `app/` has no relative imports, and this helper is proved on a live
    positive before anything trusts it."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found += [
                (node.lineno, alias.name)
                for alias in node.names
                if alias.name == "app" or alias.name.startswith("app.")
            ]
        elif (
            isinstance(node, ast.ImportFrom)
            and node.module is not None
            and (node.module == "app" or node.module.startswith("app."))
        ):
            found.append((node.lineno, node.module))
    return found


def test_no_lower_layer_imports_an_upper_one() -> None:
    """The one-way street, and proof the collector can see an `app.*` import.

    The live positive is `app/contexts/guestbook/routers/guestbook_entries.py`, which imports
    `app.contexts.guestbook.services.guestbook_entries` legitimately -- a collector that cannot see that
    one would bless every package below for the wrong reason. The rule this
    enforces has been in `spec/design/conventions.md` since the layering was
    drawn; until now nothing checked it, so a model importing a service
    would have parsed, imported and passed every suite.
    """
    proof = _app_imports(APP / "contexts" / "guestbook" / "routers" / "guestbook_entries.py")
    assert any("services" in module.split(".") for _, module in proof), (
        "the app-import collector found nothing in a router that imports a service, "
        "so a passing result below would mean nothing"
    )

    offenders: dict[str, list[str]] = {}
    for package, forbidden in _UPWARD_FORBIDDEN.items():
        for path in _modules(package):
            # The layer is a SEGMENT of the dotted name now, not its prefix:
            # `app.contexts.guestbook.services.x`. A `startswith` check against
            # `app.services` was correct while the layer was the first component
            # and would silently match nothing after the tree was recut -- which
            # is the shape of failure this whole module exists to prevent.
            upward = [
                f"line {line}: {module}"
                for line, module in _app_imports(path)
                if set(module.split(".")) & set(forbidden)
            ]
            if upward:
                offenders[f"{package}/{path.name}"] = upward

    assert offenders == {}, (
        "dependencies point one way (routers -> services -> models/schemas, "
        f"spec/design/conventions.md); these import upward: {offenders}"
    )


# --------------------------------------------------------------------------- #
# The session belongs to the service; a router never opens one itself
# --------------------------------------------------------------------------- #


def test_no_router_reaches_for_the_session() -> None:
    """A router that opens `SessionLocal` has bypassed the layer that owns
    transactions -- `spec/design/conventions.md`: "`app/contexts/<name>/services/` --
    business rules. Owns the session and the transaction boundary." Routers bind HTTP and
    delegate; a router reaching around its service would pass every behavioural
    test while changing where a transaction begins and ends.

    The live positive is `app/contexts/guestbook/services/guestbook_entries.py`, which imports
    `app.db.session` legitimately -- a detector blind to that one would
    bless every router for the wrong reason.
    """
    service = APP / "contexts" / "guestbook" / "services" / "guestbook_entries.py"
    service_source = service.read_text(encoding="utf-8")
    assert "app.db.session" in service_source or "SessionLocal" in service_source, (
        "the detector's live positive is gone: app/contexts/guestbook/services/guestbook_entries.py no "
        "longer names the session -- point this proof at a service that does"
    )

    offenders: dict[str, list[str]] = {}
    for path in _modules("routers"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        reaches = [
            f"line {line}: {module}"
            for line, module in _app_imports(path)
            if module.startswith("app.db")
        ]
        reaches += [
            f"line {node.lineno}: SessionLocal"
            for node in ast.walk(tree)
            if (isinstance(node, ast.Name) and node.id == "SessionLocal")
            or (isinstance(node, ast.Attribute) and node.attr == "SessionLocal")
        ]
        if reaches:
            offenders[path.name] = reaches

    assert offenders == {}, (
        "routers bind HTTP and delegate; the session and the transaction "
        f"boundary belong to the service. These reach for the session: {offenders}"
    )

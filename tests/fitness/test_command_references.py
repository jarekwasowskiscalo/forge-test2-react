"""Commands named in prose exist on the machine that reads them.

A sentence like "run `npm run gen:contract`" is an interface: somebody will
type it, and a user-facing error message once told them to -- for a script
that `frontend/package.json` had never defined. The path-existence gates
(`backtick-paths`, `source-paths`) cover file paths; nothing covered *command* references until this
module. Each rule scans text, resolves the reference against the registry
that owns it, and is proved on a known positive before the sweep is trusted.
"""

import json
import re
from typing import Final

from tests._repo import REPO_ROOT

#: Where an `npm run <name>` instruction may appear and be believed.
_NPM_RUN_SCOPES: Final[tuple[str, ...]] = (
    "scripts/*.py",
    "scripts/*.sh",
    "frontend/src/**/*.ts",
    "frontend/src/**/*.tsx",
    ".github/workflows/*.yml",
)

_NPM_RUN: Final = re.compile(r"npm run ([A-Za-z][A-Za-z0-9:_-]*)")


def _npm_run_references() -> dict[str, list[str]]:
    """Every `npm run <name>` token in scope, mapped to where it was said."""
    references: dict[str, list[str]] = {}
    for pattern in _NPM_RUN_SCOPES:
        for path in REPO_ROOT.glob(pattern):
            text = path.read_text(encoding="utf-8")
            for match in _NPM_RUN.finditer(text):
                line = text[: match.start()].count("\n") + 1
                # `as_posix()`: `relative_to` renders the host separator, and
                # the known-positive assertion (and any reader of these places)
                # compares against the POSIX spelling. Caught the hard way --
                # pathlib's flavour follows the host, not `sys.platform`.
                references.setdefault(match.group(1), []).append(
                    f"{path.relative_to(REPO_ROOT).as_posix()}:{line}"
                )
    return references


def test_the_npm_run_scanner_sees_the_reference_everyone_relies_on() -> None:
    """Proved on a live positive: `scripts/test.sh` runs the frontend suite
    through `npm run test`. A scanner that cannot see that one is a broken
    glob or regex, and the sweep below would pass over anything."""
    references = _npm_run_references()
    assert "test" in references, "the scanner no longer sees `npm run test` in scripts/"
    assert any(place.startswith("scripts/test.sh") for place in references["test"])


def test_every_npm_run_named_in_prose_exists_in_package_json() -> None:
    """The registry is `frontend/package.json` `scripts`, and only it.

    The known incident: three docstrings and one user-facing error message
    instructed `npm run gen:contract`, which no package.json ever defined --
    the person following the error got a second error about the first.
    """
    declared = set(
        json.loads((REPO_ROOT / "frontend/package.json").read_text(encoding="utf-8"))["scripts"]
    )
    unresolved = {
        name: places for name, places in _npm_run_references().items() if name not in declared
    }
    assert not unresolved, (
        f"instructions naming npm scripts that do not exist: {unresolved} -- "
        "either add the script to frontend/package.json or point the prose at "
        "the entry point that is real (./scripts/generate.sh, ./scripts/test.sh …)"
    )


# --------------------------------------------------------------------------- #
# A disabled pytest plugin is a plugin the lockfile actually holds
# --------------------------------------------------------------------------- #

_DISABLED_PLUGIN: Final = re.compile(r"-p no:([A-Za-z0-9_-]+)")


def test_the_disabled_plugin_scanner_still_detects() -> None:
    """Proved on a fabricated positive: the sweep below currently finds
    nothing, and a regex that finds nothing is indistinguishable from a
    broken one until it is handed a line built to trip it."""
    assert _DISABLED_PLUGIN.search("uv run pytest x -p no:randomly -q")


def test_every_disabled_plugin_is_one_the_lockfile_holds() -> None:
    """`-p no:X` for an absent plugin is dead text pytest swallows silently.

    The process's test runner (then `scripts/sdd-tests.sh`) shipped `-p no:randomly` while `pytest-randomly`
    was never in `uv.lock` -- the flag looked like it pinned determinism and
    pinned nothing. Either the plugin is a real, locked dependency being
    deliberately switched off, or the flag goes.
    """
    lock = (REPO_ROOT / "uv.lock").read_text(encoding="utf-8")
    unresolved: dict[str, list[str]] = {}
    for pattern in ("scripts/*.sh", "scripts/*.py"):
        for path in REPO_ROOT.glob(pattern):
            for match in _DISABLED_PLUGIN.finditer(path.read_text(encoding="utf-8")):
                plugin = match.group(1)
                if f'name = "pytest-{plugin}"' not in lock:
                    unresolved.setdefault(plugin, []).append(str(path.relative_to(REPO_ROOT)))
    assert not unresolved, (
        f"scripts disable pytest plugins the lockfile does not hold: {unresolved}"
    )

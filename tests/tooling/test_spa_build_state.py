"""The staleness detector fires: touch a source, and the check asks for a rebuild.

`scripts/test.sh` used to prepare the UI smoke with a PRESENCE check -- is there an
`app/static/index.html` -- so a bundle built from the previous sources was reused
silently. On 2026-09-16 that reported three UI failures against components that had
already been fixed; the mirror image is the dangerous one, a bundle still holding the
old, passing behaviour reporting green for a screen nobody built. CI never meets either,
because a clean checkout has no `app/static/` at all, so this hazard lives entirely in
the local loop -- and a suite whose verdict is about the wrong code erodes trust in
every other verdict it gives.

What is proved here: the comparison actually notices a newer source (the positive the
old check could not have passed), every declared input is a path this repository really
has, and the module and the report `status.sh` prints share one implementation rather
than two that agree today.

No database, no Docker, no network: mtimes on a temporary tree, and one subprocess run
of the module's own command line.
"""

import os
import pathlib
import subprocess
import sys
from typing import Final

import pytest

from tests._repo import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "scripts"))

import app_status
import spa_build_state

#: Comfortably past any filesystem's mtime granularity, so "newer" is never a tie.
_A_CLEAR_SECOND: Final = 10.0


def _a_built_checkout(root: pathlib.Path) -> pathlib.Path:
    """A tree with every declared build input and a bundle newer than all of them."""
    for relative in spa_build_state.BUILD_INPUTS:
        # A suffix means a file input (`package.json`, `vite.config.ts`); without one
        # it is a tree (`frontend/src`), and a tree needs a file in it to have an mtime
        # worth comparing.
        path = root / relative
        if path.suffix:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("source", encoding="utf-8")
        else:
            path.mkdir(parents=True, exist_ok=True)
            (path / "main.tsx").write_text("source", encoding="utf-8")
    static = root / spa_build_state.STATIC_DIR
    static.mkdir(parents=True, exist_ok=True)
    built = static / "index.html"
    built.write_text("<!doctype html>", encoding="utf-8")
    _stamp(built, _newest_source(root) + _A_CLEAR_SECOND)
    return root


def _newest_source(root: pathlib.Path) -> float:
    return max(
        spa_build_state.newest_mtime(root / relative) for relative in spa_build_state.BUILD_INPUTS
    )


def _stamp(path: pathlib.Path, when: float) -> None:
    """Set a file's mtime, which is what a save does and what `touch` does."""
    os.utime(path, (when, when))


# --------------------------------------------------------------------------- #
# The detector fires -- the positive the presence check could never have passed
# --------------------------------------------------------------------------- #


def test_a_built_checkout_is_current(tmp_path: pathlib.Path) -> None:
    """The baseline, without which the staleness test below proves nothing: a bundle
    newer than every source is not reported as needing a rebuild."""
    found = spa_build_state.report(_a_built_checkout(tmp_path))
    assert found.state == "current"
    assert found.absent == (), f"the fixture is missing declared inputs: {found.absent}"


@pytest.mark.parametrize("relative", spa_build_state.BUILD_INPUTS)
def test_touching_any_declared_input_asks_for_a_rebuild(
    tmp_path: pathlib.Path, relative: str
) -> None:
    """Every input, not just `frontend/src`: a dependency bump, a change to the build
    script in `package.json` or a compiler option in `tsconfig.json` stales a bundle
    exactly as an edit to a component does, and `npm run build` type-checks before it
    compiles, so `tsconfig.json` decides whether there is a bundle at all."""
    root = _a_built_checkout(tmp_path)
    built = spa_build_state.report(root).built_mtime

    target = root / relative
    edited = target if target.is_file() else target / "main.tsx"
    _stamp(edited, built + _A_CLEAR_SECOND)

    found = spa_build_state.report(root)
    assert found.state == "stale", f"editing {relative} left the bundle looking current"
    assert found.newest_input == (relative if target.is_file() else f"{relative}/main.tsx"), (
        "the report names the wrong file as the one that staled the bundle"
    )
    assert "older than its sources" in spa_build_state.explain(found)


def test_a_file_the_build_never_reads_does_not_ask_for_one(tmp_path: pathlib.Path) -> None:
    """The other half of a detector worth having: `vite build` never reads the test
    config or the README, so touching one must not cost a rebuild on every loop.
    A check that fires at everything is a check people switch off."""
    root = _a_built_checkout(tmp_path)
    built = spa_build_state.report(root).built_mtime
    for noise in ("frontend/vitest.config.ts", "frontend/eslint.config.js", "README.md"):
        path = root / noise
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("not a build input", encoding="utf-8")
        _stamp(path, built + _A_CLEAR_SECOND)
    assert spa_build_state.report(root).state == "current"


def test_no_bundle_at_all_is_missing_rather_than_stale(tmp_path: pathlib.Path) -> None:
    """A fresh clone and CI. The caller builds either way, but the sentence a person
    reads must not accuse a bundle that does not exist of being out of date."""
    root = _a_built_checkout(tmp_path)
    (root / spa_build_state.STATIC_DIR / "index.html").unlink()
    found = spa_build_state.report(root)
    assert found.state == "missing"
    assert "nothing has been built" in spa_build_state.explain(found)


def test_an_asset_written_after_index_html_still_counts_as_the_build(
    tmp_path: pathlib.Path,
) -> None:
    """Judged against the newest file under `app/static`, not `index.html` alone: vite
    writes hashed assets and the entry point in one pass, and the last of them is the
    build's true stamp. Against `index.html` alone this tree would read as stale for
    ever, and `--if-stale` would rebuild on every single run."""
    root = _a_built_checkout(tmp_path)
    index = root / spa_build_state.STATIC_DIR / "index.html"
    source = root / "frontend/src/main.tsx"
    _stamp(source, index.stat().st_mtime + _A_CLEAR_SECOND)
    assert spa_build_state.report(root).state == "stale"

    asset = root / spa_build_state.STATIC_DIR / "assets" / "index-abc123.js"
    asset.parent.mkdir(parents=True, exist_ok=True)
    asset.write_text("bundled", encoding="utf-8")
    _stamp(asset, source.stat().st_mtime + _A_CLEAR_SECOND)
    assert spa_build_state.report(root).state == "current"


# --------------------------------------------------------------------------- #
# The declaration is about this repository, and there is one of it
# --------------------------------------------------------------------------- #


def test_every_declared_build_input_is_a_path_this_repository_has() -> None:
    """An input that has been renamed away contributes nothing and weakens the check
    silently, for ever -- the failure mode of a glob that has stopped matching. It is
    cheaper to fail here than to wonder why a rebuild stopped happening."""
    absent = spa_build_state.report().absent
    assert not absent, (
        f"declared build inputs that no longer exist: {absent} -- either the path moved "
        "and BUILD_INPUTS in scripts/spa_build_state.py must follow it, or it is no "
        "longer an input and the entry goes"
    )


def test_the_status_report_and_the_build_scripts_share_one_implementation() -> None:
    """`status.sh --json`, `build.sh --if-stale` and `test.sh ui` must not be able to
    disagree about what stale means. They cannot, because there is one function and one
    tuple, and this is what holds them to it: an `app_status.py` that grew its own copy
    back would still pass every other test in the suite."""
    assert app_status.build_state is spa_build_state.build_state
    assert app_status.BUILD_INPUTS is spa_build_state.BUILD_INPUTS
    assert app_status.newest_mtime is spa_build_state.newest_mtime


# --------------------------------------------------------------------------- #
# The command line the scripts actually call
# --------------------------------------------------------------------------- #


def test_the_command_line_prints_the_verdict_first_and_the_reason_second() -> None:
    """`build.sh --if-stale` reads the verdict off line 1 and the reason off line 2, with
    `sed -n '1p'` and `sed -n '2p'`. Either would read an empty string if the order or
    the line count changed, and `--if-stale` would then rebuild every time without
    anybody noticing it had stopped deciding."""
    finished = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "spa_build_state.py"), "--explain"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert finished.returncode == 0, finished.stderr
    lines = finished.stdout.splitlines()
    assert len(lines) == 2, f"expected a verdict and a reason, got {lines}"
    assert lines[0] in {"missing", "stale", "current"}
    assert lines[1]

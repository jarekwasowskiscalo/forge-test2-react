"""Whether the SPA under `app/static/` still answers for the sources it was built from.

Three callers ask this question and each used to answer it differently. `scripts/test.sh`
asked only whether a build EXISTED; `scripts/build.sh` announced "app/static is current"
having compared nothing at all; `scripts/app_status.py` was the only one that looked at
mtimes. The first of those is what made `./scripts/test.sh ui` report three failures
against code that had already been fixed (2026-09-16): it reused the bundle built from
the previous sources. The mirror image is the dangerous one -- a stale bundle still
holding the old, PASSING behaviour reports green for a screen nobody built. CI never
meets either, because a clean checkout has no `app/static/` and always builds; this is a
hazard of the local loop alone, which is the loop whose verdict people act on fastest.

So the fact lives here, once, and the scripts read it:

- `BUILD_INPUTS` is what the bundle is judged against. The lockfile, `package.json`,
  `tsconfig.json` and the Vite config count: a dependency bump, a script change or a
  compiler-option change stales a build exactly as a source edit does, and
  `npm run build` type-checks before it compiles, so `tsconfig.json` can decide whether
  there is a bundle at all.
- The comparison is mtimes, and nothing else. A content hash would be exact and would
  also mean reading every source on every `test.sh ui`; mtimes are what `make` has
  judged on for fifty years, and the failure mode they have -- a clock moved backwards
  -- makes a build look stale, which costs a rebuild rather than a false green.

Read-only, exit code 0 always: this is a report, not a gate. The caller decides what to
do about the verdict.

Standard library only, and held to the older syntax floor by
`tests/fitness/test_scripts_syntax_floor.py`, for the same reason `app_status.py` is:
that module imports this one, and it runs under whatever `python3` a bare machine has
before `uv` has synced anything.

Usage:
    python3 scripts/spa_build_state.py            # one word: missing | stale | current
    python3 scripts/spa_build_state.py --explain  # ...then a sentence saying what was compared
"""

import argparse
import pathlib
import sys
import time
from typing import Final, NamedTuple

REPO_ROOT: Final[pathlib.Path] = pathlib.Path(__file__).resolve().parent.parent

#: What the freshness of the served build is judged against, relative to the repo root.
#:
#: A path that stops existing contributes nothing and would silently weaken the check
#: for ever, which is why `report()` reports the absent ones and
#: `tests/tooling/test_spa_build_state.py` holds every entry to a path this repository has.
BUILD_INPUTS: Final[tuple[str, ...]] = (
    "frontend/src",
    "frontend/index.html",
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/tsconfig.json",
    "frontend/vite.config.ts",
)

#: Where `vite build` puts the bundle the application serves (`frontend/vite.config.ts`).
STATIC_DIR: Final = "app/static"


def newest_file(path: pathlib.Path) -> tuple[pathlib.Path | None, float]:
    """The newest file at or under a path, and its mtime. `(None, 0.0)` when absent.

    The path itself when it is a file, so an input may be a directory or a single file
    and the caller need not know which.
    """
    if path.is_file():
        return path, path.stat().st_mtime
    winner: pathlib.Path | None = None
    newest = 0.0
    if path.is_dir():
        for child in path.rglob("*"):
            if child.is_file():
                stamp = child.stat().st_mtime
                if stamp > newest:
                    winner, newest = child, stamp
    return winner, newest


def newest_mtime(path: pathlib.Path) -> float:
    """The newest mtime under a path. 0.0 when it does not exist."""
    return newest_file(path)[1]


def build_state(static_dir: pathlib.Path, source_mtimes: list[float]) -> str:
    """`missing` / `current` / `stale`, from mtimes alone.

    Judged against the newest file anywhere under `static_dir`, not against
    `index.html` alone: every artefact `vite build` writes is written by that build, so
    the newest of them is the build's own stamp, and a bundle whose assets were
    rewritten without its entry point being touched is still a bundle from that moment.

    Ties count as current. A source and a bundle written in the same tick is the build
    that has just finished writing them, and the alternative -- rebuilding on equality --
    would make `--if-stale` rebuild for ever on a filesystem with a coarse clock.
    """
    if not (static_dir / "index.html").is_file():
        return "missing"
    built = newest_mtime(static_dir)
    return "stale" if max(source_mtimes, default=0.0) > built else "current"


class Report(NamedTuple):
    """The verdict and everything the sentence explaining it needs."""

    state: str
    newest_input: str | None
    """The build input that decided it, repo-relative and POSIX-spelled. None when the
    `frontend/` tree holds no file at all -- a broken checkout, not a fresh one."""
    newest_input_mtime: float
    built_mtime: float
    compared: tuple[str, ...]
    """The inputs that exist and were therefore actually compared."""
    absent: tuple[str, ...]
    """The declared inputs that do not exist, so nothing was compared for them."""


def report(root: pathlib.Path = REPO_ROOT) -> Report:
    """Compare the bundle under `root` against every build input it has."""
    compared: list[str] = []
    absent: list[str] = []
    winner: pathlib.Path | None = None
    newest = 0.0
    for relative in BUILD_INPUTS:
        path = root / relative
        (compared if path.exists() else absent).append(relative)
        candidate, stamp = newest_file(path)
        if stamp > newest:
            winner, newest = candidate, stamp
    static_dir = root / STATIC_DIR
    return Report(
        state=build_state(static_dir, [newest]),
        newest_input=winner.relative_to(root).as_posix() if winner is not None else None,
        newest_input_mtime=newest,
        built_mtime=newest_mtime(static_dir),
        compared=tuple(compared),
        absent=tuple(absent),
    )


def _clock(stamp: float) -> str:
    """A wall-clock time somebody can compare against their own last save."""
    return time.strftime("%H:%M:%S", time.localtime(stamp))


def explain(found: Report) -> str:
    """One sentence naming what was compared against what, and when.

    The point of the sentence: `build.sh` used to print "app/static is current" with no
    comparison behind it, which reads as a freshness claim. A claim that names its
    evidence can be disbelieved by whoever reads it, which is the whole difference.
    """
    missing_note = (
        ""
        if not found.absent
        else f" ({len(found.absent)} declared input(s) absent: {', '.join(found.absent)})"
    )
    if found.state == "missing":
        return f"{STATIC_DIR}/index.html does not exist -- nothing has been built"
    if found.state == "stale":
        return (
            f"{found.newest_input} changed at {_clock(found.newest_input_mtime)}, after "
            f"{STATIC_DIR} was written at {_clock(found.built_mtime)} -- the bundle is "
            f"older than its sources{missing_note}"
        )
    return (
        f"{STATIC_DIR} was written at {_clock(found.built_mtime)}, after all "
        f"{len(found.compared)} build inputs ({', '.join(found.compared)}) -- newest of "
        f"them {found.newest_input} at {_clock(found.newest_input_mtime)}{missing_note}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Report whether app/static is missing, stale or current.",
        epilog="Exit code is 0 whatever the verdict: this is a report, not a gate. "
        "The verdict is the first line of stdout.",
    )
    parser.add_argument(
        "--explain",
        action="store_true",
        help="print a second line saying what was compared against what, and when",
    )
    arguments = parser.parse_args(argv)
    found = report()
    print(found.state)
    if arguments.explain:
        print(explain(found))
    return 0


if __name__ == "__main__":
    sys.exit(main())

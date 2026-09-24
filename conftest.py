"""The `--no-db` switch, registered where pytest will accept it.

One testpath holds tests: `tests/`. The change process's suite
(the engine) is its own, run from its own root with its own
conftest (`sdd-tests`), and this file is not loaded for it. The option
lives here, at the repository root above `tests/`, where pytest accepts
`pytest_addoption` for every collection.

**The switch, and one whole-run invariant.** Everything that provisions a database
stays in `tests/conftest.py`: this conftest is loaded for every collection, and
`--no-db` exists precisely so a run on a host with no Docker never touches Postgres. The deselection lives here too, because it is the other half of one flag
and splitting a flag from its meaning is how the two drift.

`no_db` is opt-in rather than opt-out on purpose. A new test that forgets the marker
is then simply not run on the macOS leg, which is a gap. The opposite
default would make it *fail* on a runner with no Docker, and its author would learn
that from a red build on a machine they cannot reproduce.

**The suite leaves the working tree as it found it**, and that is checked here for
the same reason the switch is: it has to hold across the whole tree, and this is the
conftest above it. `session_log.path_for()` resolved its directory
against the real repository and created it, so every run of `test.sh backend`
and `gate.py run --profile fast` dropped
`spec/changes/spec/changes/<CR>/sessions/sess-{forced,mirror}/trace.md` into
whoever's checkout. Nobody noticed for as long as they did because it needs an open
change to have a `<CR>` to write under, and the branch that has one is the branch
nobody runs `git status` on twice.

Scoped to the whole tree rather than to `spec/`, because `--porcelain` already
draws the line this wants: anything `.gitignore` covers -- `.sdd/`, the caches, the
venvs -- is scratch and never reported, and everything it does report is the
committed tree. A narrower rule would have to be widened by the next leak that
lands one directory over.

It reports and fails; it does not delete. A guard that tidies up after the defect
is a guard that hides it -- the second run would be green and the cause would still
be there.
"""

import pathlib
import subprocess
import sys

import pytest

#: Untracked paths as they stood before collection, or `None` when git could not be
#: asked. `None` rather than an empty set because "we could not look" and "there was
#: nothing" must not be the same value: conflating them turns a git that fails at
#: startup and answers at the end into a report blaming this run for every stray
#: file already on the disk.
_UNTRACKED_BEFORE: set[str] | None = None


def _untracked() -> set[str] | None:
    """Every untracked path git can see, or `None` if it could not be asked."""
    try:
        completed = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=pathlib.Path(__file__).resolve().parent,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    return {
        line[3:].strip().strip('"') for line in completed.stdout.splitlines() if line[:3] == "?? "
    }


def pytest_sessionstart(session: pytest.Session) -> None:
    global _UNTRACKED_BEFORE
    _UNTRACKED_BEFORE = _untracked()


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Fail a run that grew the working tree, and name what it grew it by."""
    after = _untracked()
    if _UNTRACKED_BEFORE is None or after is None:
        return
    leaked = sorted(after - _UNTRACKED_BEFORE)
    if not leaked:
        return

    shown = leaked[:20]
    lines = [
        "",
        f"ERROR: the suite left {len(leaked)} untracked file(s) in the working tree.",
        "A test is writing to the real repository instead of to tmp_path -- isolate it,",
        "do not add the path to .gitignore.",
        *(f"  {path}" for path in shown),
        *([f"  … and {len(leaked) - len(shown)} more"] if len(leaked) > len(shown) else []),
        "",
    ]
    print("\n".join(lines), file=sys.stderr)

    # Do not overwrite a red that is already there: a run with a failing test is to
    # return that failure's code, not this one's.
    if exitstatus == 0:
        session.exitstatus = 1


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--no-db",
        action="store_true",
        help=(
            "Skip every test that needs Postgres and provision none. For a host with "
            "neither a Linux-container Docker nor a Postgres of its own, where the pure "
            "tests -- decoding, paths, line endings -- are exactly where a platform "
            "regression shows. A host that HAS a Postgres should point "
            "APP_TEST_DATABASE_URL at it instead and run the whole suite."
        ),
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Under `--no-db`, keep only the tests marked `no_db`.

    There is no second engine to deselect for any more (`spec/design/architecture.md` § One engine): a test either
    needs a database or it does not, and `no_db` is the whole of that question.
    """
    if not config.getoption("--no-db"):
        return
    skip = pytest.mark.skip(reason="needs Postgres; deselected by --no-db")
    for item in items:
        if "no_db" not in item.keywords:
            item.add_marker(skip)

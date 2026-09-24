"""Unit and integration tests for the preflight prerequisite check
(Boundary: PreflightScript).

Covers `scripts/preflight.py`: each individual `check_*` function's
pass/fail/informational behavior under simulated (mocked) tool
availability, `run_preflight()`'s pass/fail aggregation rule (a required
check's failure fails the run; the informational Docker check's failure
never does), the extensibility property (a new check can be added to the
list passed to `run_preflight` without touching any existing `check_*`
function), and one real-subprocess integration test proving the script
still runs to completion and correctly reports a missing `uv` even when
invoked standalone, with no project environment set up from its own
perspective.
"""

from __future__ import annotations

import contextlib
import os
import shutil
import subprocess
import sys
from collections import namedtuple
from pathlib import Path
from typing import Final
from unittest import mock

import pytest

from scripts.preflight import (
    CheckResult,
    check_docker,
    check_python_version,
    check_uv,
    run_preflight,
)
from tests._repo import REPO_ROOT

PROJECT_ROOT = REPO_ROOT
PREFLIGHT_SCRIPT = PROJECT_ROOT / "scripts" / "preflight.py"

# `sys.version_info` is a named-tuple-like struct sequence exposing both
# positional indexing/slicing (used by `check_python_version()`'s
# `sys.version_info[:2]`) and named attributes (`.major`/`.minor`/`.micro`,
# used in its message string). A plain tuple supports the former but not
# the latter, so tests mock it with an actual namedtuple that supports
# both, matching the real object's interface closely enough to exercise
# the function's actual code path rather than a simplified stand-in.
_FakeVersionInfo = namedtuple("version_info", ["major", "minor", "micro", "releaselevel", "serial"])


# ---------------------------------------------------------------------------
# check_python_version()
# ---------------------------------------------------------------------------


def test_check_python_version_ok_when_version_meets_minimum() -> None:
    """A mocked interpreter version >= 3.14 reports ok=True, required=True."""
    fake_version = _FakeVersionInfo(3, 14, 4, "final", 0)
    with mock.patch("scripts.preflight.sys.version_info", fake_version):
        result = check_python_version()

    assert result.ok is True
    assert result.required is True
    assert "3.14.4" in result.message


def test_check_python_version_fails_when_version_below_minimum() -> None:
    """A mocked interpreter version < 3.14 reports ok=False with a clear message."""
    fake_version = _FakeVersionInfo(3, 11, 9, "final", 0)
    with mock.patch("scripts.preflight.sys.version_info", fake_version):
        result = check_python_version()

    assert result.ok is False
    assert result.required is True
    assert "3.11.9" in result.message
    assert "3.14" in result.message


# ---------------------------------------------------------------------------
# check_uv()
# ---------------------------------------------------------------------------


def test_check_uv_fails_when_not_on_path() -> None:
    """shutil.which("uv") -> None means uv is reported missing, ok=False."""
    with mock.patch("scripts.preflight.shutil.which", return_value=None):
        result = check_uv()

    assert result.ok is False
    assert result.required is True
    assert "uv" in result.message.lower()
    assert "not found" in result.message.lower()


def test_check_uv_ok_when_present_and_version_satisfies_requirement() -> None:
    """A uv inside the range pyproject.toml accepts is ok=True.

    The version used is the range's floor rather than a comfortable middle: the
    floor is where an inclusive bound written as an exclusive one fails, and
    nothing else in this file would notice.
    """
    fake_result = subprocess.CompletedProcess(
        args=["uv", "--version"], returncode=0, stdout="uv 0.12.0 (abc123 2024-01-01)\n", stderr=""
    )
    with (
        mock.patch("scripts.preflight.shutil.which", return_value="/usr/local/bin/uv"),
        mock.patch("scripts.preflight.subprocess.run", return_value=fake_result) as mock_run,
    ):
        result = check_uv()

    assert result.ok is True
    assert result.required is True
    assert "0.12.0" in result.message
    mock_run.assert_called_once()


def test_check_uv_fails_when_present_but_version_too_low() -> None:
    """A uv below the range's floor is ok=False."""
    fake_result = subprocess.CompletedProcess(
        args=["uv", "--version"], returncode=0, stdout="uv 0.5.0\n", stderr=""
    )
    with (
        mock.patch("scripts.preflight.shutil.which", return_value="/usr/local/bin/uv"),
        mock.patch("scripts.preflight.subprocess.run", return_value=fake_result),
    ):
        result = check_uv()

    assert result.ok is False
    assert result.required is True
    assert "0.5.0" in result.message


def test_check_uv_fails_when_present_but_version_is_past_the_ceiling() -> None:
    """The half a floor-only check cannot state.

    `required-version` in pyproject.toml is a range, so a uv from the next minor
    is refused by every `uv` command in this project. A preflight reporting a
    floor would certify a machine that the very next `uv sync` rejects -- which
    is the exact failure this check was written after.
    """
    fake_result = subprocess.CompletedProcess(
        args=["uv", "--version"], returncode=0, stdout="uv 0.13.0\n", stderr=""
    )
    with (
        mock.patch("scripts.preflight.shutil.which", return_value="/usr/local/bin/uv"),
        mock.patch("scripts.preflight.subprocess.run", return_value=fake_result),
    ):
        result = check_uv()

    assert result.ok is False
    assert "0.13.0" in result.message


# ---------------------------------------------------------------------------
# check_docker()
# ---------------------------------------------------------------------------


def _docker_info(returncode: int = 0) -> subprocess.CompletedProcess[str]:
    """What `docker info --format {{.ServerVersion}}` returns, as a fake."""
    return subprocess.CompletedProcess(
        args=["docker", "info", "--format", "{{.ServerVersion}}"],
        returncode=returncode,
        stdout="27.3.1\n",
        stderr="",
    )


#: What `check_docker` is handed, and what it must conclude.
#:
#: One table rather than five near-identical functions: they differed only in what
#: `subprocess.run` did, and written out separately the difference was buried in
#: forty lines of identical `mock.patch` scaffolding. Each row keeps its own name
#: in the report, which is what a failure needs to say.
#:
#: `which` is mocked alongside `run` in every row, and that is the point. This
#: family once mocked only `which` and let `docker info` really run -- so it
#: asserted a property of the *machine*. It passed on a laptop with Docker Desktop
#: up and failed on the CI runners, where there is no Docker at all.
_DOCKER_CASES: Final[tuple[tuple[str, str | None, object, bool, str], ...]] = (
    ("present-and-daemon-answering", "/usr/bin/docker", _docker_info(), True, ""),
    (
        "daemon-not-answering",
        "/usr/bin/docker",
        _docker_info(returncode=1),
        False,
        "daemon",
    ),
    # `which` finding a path does not mean the file can be run: a broken symlink or
    # a stale shim raises, and preflight must survive it rather than abort.
    ("binary-that-cannot-be-executed", "/usr/bin/docker", OSError("not found"), False, ""),
    ("absent-entirely", None, None, False, ""),
)


@pytest.mark.parametrize(
    ("which", "run_behaviour", "ok", "message_fragment"),
    [pytest.param(w, r, ok, msg, id=name) for name, w, r, ok, msg in _DOCKER_CASES],
)
def test_check_docker_reads_the_machine_and_never_fails_preflight(
    which: str | None, run_behaviour: object, ok: bool, message_fragment: str
) -> None:
    """Docker is `required=False` in every one of these, including the good one:
    a machine without it can still run the no-database subset, and preflight
    saying otherwise would turn an optional tool into a blocker."""
    patches = [mock.patch("scripts.preflight.shutil.which", return_value=which)]
    if isinstance(run_behaviour, BaseException):
        patches.append(mock.patch("scripts.preflight.subprocess.run", side_effect=run_behaviour))
    elif run_behaviour is not None:
        patches.append(mock.patch("scripts.preflight.subprocess.run", return_value=run_behaviour))

    with contextlib.ExitStack() as stack:
        for patch in patches:
            stack.enter_context(patch)
        result = check_docker()

    assert result.required is False
    assert result.ok is ok
    if message_fragment:
        assert message_fragment in result.message


def test_missing_docker_alone_never_fails_run_preflight() -> None:
    """Even via the real check_docker (mocked absent) run_preflight must still
    exit 0 when it is the only failing check, since it is required=False."""
    with (
        mock.patch("scripts.preflight.shutil.which", return_value=None),
        mock.patch(
            "scripts.preflight.subprocess.run",
            return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr=""),
        ),
    ):
        passing_required = CheckResult(name="fake required", required=True, ok=True, message="fine")
        exit_code = run_preflight(checks=[lambda: passing_required, check_docker])

    assert exit_code == 0


# ---------------------------------------------------------------------------
# run_preflight() aggregation rule
# ---------------------------------------------------------------------------


def _result(*, required: bool, ok: bool, name: str = "fake") -> CheckResult:
    return CheckResult(name=name, required=required, ok=ok, message=f"{name} message")


def test_run_preflight_exits_zero_when_required_passes_and_informational_fails() -> None:
    required_pass = _result(required=True, ok=True, name="required-pass")
    informational_fail = _result(required=False, ok=False, name="docker-like")

    exit_code = run_preflight(checks=[lambda: required_pass, lambda: informational_fail])

    assert exit_code == 0


def test_run_preflight_exits_one_when_a_required_check_fails() -> None:
    required_fail = _result(required=True, ok=False, name="required-fail")
    informational_fail = _result(required=False, ok=False, name="docker-like")

    exit_code = run_preflight(checks=[lambda: required_fail, lambda: informational_fail])

    assert exit_code == 1


def test_run_preflight_prints_each_missing_required_prerequisite(
    capsys: pytest.CaptureFixture[str],
) -> None:
    required_fail = _result(required=True, ok=False, name="widget-tool")

    run_preflight(checks=[lambda: required_fail])
    captured = capsys.readouterr()

    assert "widget-tool" in captured.out
    assert "widget-tool" in captured.out.split("missing or unmet required prerequisites:")[1]


def test_run_preflight_reports_ready_when_everything_passes(
    capsys: pytest.CaptureFixture[str],
) -> None:
    required_pass = _result(required=True, ok=True, name="widget-tool")

    exit_code = run_preflight(checks=[lambda: required_pass])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "environment ready" in captured.out.lower()


# ---------------------------------------------------------------------------
# Extensibility
# ---------------------------------------------------------------------------


def test_a_new_check_can_be_added_without_modifying_existing_checks() -> None:
    """Demonstrates that adding a 4th prerequisite only requires extending the
    list passed to run_preflight -- check_python_version/check_uv/check_docker
    are used completely unmodified and untouched, and their own pass/fail
    behavior is unaffected by the extra check's presence."""
    with (
        mock.patch("scripts.preflight.sys.version_info", _FakeVersionInfo(3, 12, 4, "final", 0)),
        mock.patch("scripts.preflight.shutil.which", return_value="/usr/local/bin/uv"),
        mock.patch(
            "scripts.preflight.subprocess.run",
            return_value=subprocess.CompletedProcess(
                args=["uv", "--version"], returncode=0, stdout="uv 0.12.0\n", stderr=""
            ),
        ),
    ):
        baseline_checks = [check_python_version, check_uv, check_docker]
        baseline_results = [check() for check in baseline_checks]

        def check_new_widget() -> CheckResult:
            return CheckResult(name="widget", required=True, ok=True, message="widget present")

        extended_checks = [*baseline_checks, check_new_widget]
        extended_results = [check() for check in extended_checks]

    # The original three checks behave identically whether or not the new
    # check is appended -- nothing about check_python_version/check_uv/
    # check_docker had to change to accommodate the 4th check.
    assert extended_results[:3] == baseline_results
    assert extended_results[3].name == "widget"

    exit_code = run_preflight(checks=extended_checks)
    assert exit_code == 0


# ---------------------------------------------------------------------------
# Integration: standalone subprocess invocation with uv hidden from PATH
#
# ---------------------------------------------------------------------------


def test_preflight_runs_to_completion_and_reports_missing_uv_as_standalone_subprocess() -> None:
    """The preflight check must be runnable independently of
    having performed environment setup, and must still run to completion
    (not crash) and correctly report a missing `uv` when invoked as a bare
    subprocess on a system where no project environment has been set up.

    `scripts/preflight.py` detects `uv` via `shutil.which("uv")`, i.e. a
    PATH lookup -- not via a Python import -- so simulating "uv missing"
    requires hiding uv's directory from PATH itself -- a modified PATH
    environment variable is the only faithful simulation of that scenario. This differs from the run script's
    `-S`-flag trick, which only suppresses automatic `import site` and
    therefore only affects package *imports* (e.g. `uvicorn`); it does not
    touch PATH-based executable lookups, so it would not hide `uv` here.

    Cross-platform safety: `sys.executable` (an absolute path) is used
    instead of a hardcoded `python3`/`python` command name, and
    `os.pathsep` is used to split/join PATH -- both of which behave
    correctly on Linux and macOS without any `skipif` or platform-specific
    assumption.
    """
    uv_path = shutil.which("uv")
    assert uv_path is not None, (
        "This test needs uv discoverable on PATH in the *current* process "
        "so it can prove that hiding its directory removes it for the "
        "subprocess under test."
    )
    # The directory uv is *found through*, not the one it resolves to.
    # `Path(uv_path).resolve().parent` follows the symlink first, so on a
    # Homebrew, pipx, mise, asdf or Nix install it yields the real store
    # directory -- which was never on PATH. Nothing got stripped, uv stayed
    # discoverable, preflight passed, and this test failed on `assert 0 == 1`
    # while blaming the script. Reproduced against a Homebrew-shaped layout.
    uv_dir = Path(uv_path).parent

    original_path = os.environ.get("PATH", "")
    remaining_dirs = [
        entry
        for entry in original_path.split(os.pathsep)
        # Both forms, because either the raw entry or its resolved form may be
        # the one that matches, depending on how uv was installed.
        if entry and Path(entry) != uv_dir and Path(entry).resolve() != uv_dir.resolve()
    ]
    modified_env = dict(os.environ)
    modified_env["PATH"] = os.pathsep.join(remaining_dirs)

    # Assert the *setup* worked before asserting anything about the script.
    # Without this the failure below reads as "preflight did not fail when uv
    # was missing" when the truth is "uv was never missing".
    assert shutil.which("uv", path=modified_env["PATH"]) is None, (
        "uv is still discoverable after removing its directory from PATH, so "
        "this test would be measuring nothing"
    )

    result = subprocess.run(
        [sys.executable, str(PREFLIGHT_SCRIPT)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=10,
        env=modified_env,
    )

    # Runs to completion (no traceback / crash) and reports failure via exit
    # code, per run_preflight()'s documented contract.
    assert result.returncode == 1, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert result.stderr == ""
    assert "Preflight check results:" in result.stdout
    assert "uv" in result.stdout
    assert "not found" in result.stdout.lower()
    assert "Environment not ready" in result.stdout

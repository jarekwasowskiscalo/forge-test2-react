"""check.sh's three-state exit, proven on a stubbed tree in seconds.

`check.sh` is Article XII's definition of "will CI pass", and its exit contract
carries three sentences that must not blur: 0 -- every gate ran and passed;
1 -- a gate ran and failed; 4 (INCOMPLETE) -- everything that ran passed, but a
gate did not run. The third state exists so a green that skipped two gates can
never read like a green that passed them, and until now nothing executed it: the
only caller of the real script is a person, against the real gates, at real cost.

The stub: `check.sh` and `_lib.sh` are copied into a tmp tree verbatim --
`_lib.sh` derives `REPO_ROOT` from its own file location, never from `$PWD`, so
the copy re-roots itself for free -- and each gate script is a two-line stub
exiting a chosen code. What is under test is check.sh's own aggregation
(`gate()`, the failed/incomplete arrays, the exit), not any gate's substance.
"""

import pathlib
import shutil
import stat
import subprocess

_REPO = pathlib.Path(__file__).resolve().parents[2]

#: Every script check.sh invokes as a gate. A new gate that adds a script shows
#: up as a loud "No such file" failure here, not as a silently green stub.
_GATE_SCRIPTS = (
    "hygiene.sh",
    "lint.sh",
    "infra-check.sh",
    "generate.sh",
    "contracts.sh",
    "test.sh",
    "build.sh",
    "audit.sh",
)


def _plant(tmp_path: pathlib.Path, codes: dict[str, int]) -> pathlib.Path:
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    for name in ("check.sh", "_lib.sh"):
        shutil.copy2(_REPO / "scripts" / name, scripts / name)
    for name in _GATE_SCRIPTS:
        stub = scripts / name
        stub.write_text(f"#!/usr/bin/env bash\nexit {codes.get(name, 0)}\n", encoding="utf-8")
        stub.chmod(stub.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return scripts / "check.sh"


def _run(check: pathlib.Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(check)], capture_output=True, text=True, timeout=120, check=False
    )


def test_every_gate_green_is_exit_zero(tmp_path: pathlib.Path) -> None:
    completed = _run(_plant(tmp_path, {}))
    assert completed.returncode == 0, completed.stderr
    assert "Check: OK" in completed.stderr


def test_a_gate_that_did_not_run_is_incomplete_never_ok(tmp_path: pathlib.Path) -> None:
    """A gate reporting 4 propagates as 4, with the gap named on stderr."""
    completed = _run(_plant(tmp_path, {"audit.sh": 4}))
    assert completed.returncode == 4, completed.stderr
    assert "Check: INCOMPLETE" in completed.stderr
    assert "Not run:" in completed.stderr
    assert "inside Dependency audit" in completed.stderr


def test_a_red_gate_beats_incomplete(tmp_path: pathlib.Path) -> None:
    """1 wins over 4: a run with a failure is a failure, whatever else was skipped."""
    completed = _run(_plant(tmp_path, {"lint.sh": 1, "audit.sh": 4}))
    assert completed.returncode == 1, completed.stderr
    assert "Check: FAILED" in completed.stderr
    assert "Failed gates:" in completed.stderr
    assert "Static checks" in completed.stderr

"""The verdict a script returns is the same verdict whoever reads it, and however.

Issue #61 (audit ticket E3-03) asks for three things, and each one is proved here by
running the shell rather than by reading it. `tests/fitness/test_pipeline_verdicts.py`
reads the source for the rule.

1. **`lists_line` / `lists_match` answer three things, not two**: 0 yes, 1 no, 2 the
   producer could not be asked. The third is the one a bare `producer | grep -q` folds
   into "no". A producer that `grep -q` cut off with SIGPIPE after a match is a yes.
2. **bash and zsh keep `0/1/2/4/124` identical.** Every script has a bash shebang, so
   the calling shell cannot change the code. The pipe can: `$?` after `| tail -1` is
   `tail`'s in both shells. `set -o pipefail` is the remedy both shells honour. zsh's
   `${pipestatus[1]}` is not bash's `${PIPESTATUS[0]}`, so no printed command may rely
   on either.
3. **A log above 100 KB does not push the reason out of the first screenful.** `summary`
   writes its banner to stderr, beside `fail`, so stderr alone carries the reason and
   the verdict whatever stdout held.

Sources the real `scripts/_lib.sh` in a bare shell and plants tiny scripts in a tmp
directory. No database, no Docker.
"""

import pathlib
import shutil
import stat
import subprocess
from typing import Final

import pytest

from tests._repo import REPO_ROOT

_LIB: Final = REPO_ROOT / "scripts" / "_lib.sh"
_ENV: Final = {"PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "HOME": str(REPO_ROOT), "NO_COLOR": "1"}
_CONTRACT_CODES: Final = (0, 1, 2, 4, 124)


def _ask(helper_call: str) -> int:
    """The status of one helper call, in a bash that sourced the real library."""
    completed = subprocess.run(
        ["bash", "-c", f'source "$1"; {helper_call}; echo "status=$?"', "bash", str(_LIB)],
        capture_output=True,
        text=True,
        env=_ENV,
        timeout=30,
        check=False,
    )
    lines = [line for line in completed.stdout.splitlines() if line.startswith("status=")]
    assert lines, completed.stderr
    return int(lines[-1].removeprefix("status="))


@pytest.mark.parametrize(
    ("call", "expected"),
    [
        (r"lists_line db printf 'app\ndb\n'", 0),
        (r"lists_line db printf 'app\ndbx\n'", 1),
        ("lists_line db false", 2),
        (r"lists_line db sh -c 'echo db; exit 3'", 2),
        (r"lists_match '\(head\)' printf 'abc (head)\n'", 0),
        (r"lists_match '\(head\)' printf 'abc\n'", 1),
        (r"lists_match '\(head\)' sh -c 'echo \"(head)\" >/dev/null; exit 1'", 2),
    ],
)
def test_the_helpers_answer_yes_no_and_could_not_ask(call: str, expected: int) -> None:
    assert _ask(call) == expected


def test_a_producer_cut_off_by_the_match_it_produced_is_a_yes() -> None:
    """`grep -q` quits at the first match. The producer, still writing, gets SIGPIPE,
    and under `pipefail` that 141 used to read as "no" -- for an answer that was found.
    Several megabytes, so the write outlasts the pipe buffer on every kernel."""
    assert _ask("lists_match '^1$' seq 1 2000000") == 0


def _plant_exit(tmp_path: pathlib.Path, code: int) -> pathlib.Path:
    script = tmp_path / f"exits_{code}.sh"
    script.write_text(
        "#!/usr/bin/env bash\nset -euo pipefail\n"
        f'source "{_LIB}"\n'
        "printf 'a line of payload\\n'\n"
        f'summary "Planted" {code}\n',
        encoding="utf-8",
    )
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    return script


def _status_in(shell: str, command: str) -> int:
    completed = subprocess.run(
        [shell, "-c", command], capture_output=True, text=True, env=_ENV, timeout=60, check=False
    )
    return completed.returncode


_SHELLS: Final = [
    "bash",
    pytest.param(
        "zsh",
        marks=pytest.mark.skipif(
            shutil.which("zsh") is None, reason="zsh is not installed on this machine"
        ),
    ),
]


@pytest.mark.parametrize("shell", _SHELLS)
@pytest.mark.parametrize("code", _CONTRACT_CODES)
def test_every_contract_code_reaches_the_caller_bare_and_through_a_pipe(
    tmp_path: pathlib.Path, shell: str, code: int
) -> None:
    script = _plant_exit(tmp_path, code)
    assert _status_in(shell, f"'{script}'") == code
    assert _status_in(shell, f"set -o pipefail; '{script}' | tail -1") == code


@pytest.mark.parametrize("shell", _SHELLS)
def test_without_pipefail_the_pipe_answers_for_tail_in_both_shells(
    tmp_path: pathlib.Path, shell: str
) -> None:
    """The known positive for the remedy above. A test that only ever saw the remedy
    work could not tell it apart from a pipe that never lost anything."""
    script = _plant_exit(tmp_path, 1)
    assert _status_in(shell, f"'{script}' | tail -1") == 0


@pytest.mark.parametrize("shell", _SHELLS)
def test_a_real_script_answers_the_same_under_either_shell(shell: str) -> None:
    test_sh = REPO_ROOT / "scripts" / "test.sh"
    assert _status_in(shell, f"'{test_sh}' --help >/dev/null") == 0
    assert _status_in(shell, f"'{test_sh}' no-such-suite >/dev/null 2>&1") == 1
    assert _status_in(shell, f"set -o pipefail; '{test_sh}' no-such-suite 2>&1 | tail -1") == 1


def test_the_reason_and_the_verdict_survive_a_log_of_150_kb(tmp_path: pathlib.Path) -> None:
    script = tmp_path / "loud_then_red.sh"
    script.write_text(
        "#!/usr/bin/env bash\nset -euo pipefail\n"
        f'source "{_LIB}"\n'
        "for _ in $(seq 1 3000); do printf '%s\\n' "
        '"a line of a suite that talks a great deal before it fails, fifty bytes"; done\n'
        'fail "the reason, which must be read first"\n'
        'summary "Loud gate" 1\n',
        encoding="utf-8",
    )
    script.chmod(script.stat().st_mode | stat.S_IXUSR)

    completed = subprocess.run(
        [str(script)], capture_output=True, text=True, env=_ENV, timeout=60, check=False
    )

    assert completed.returncode == 1
    assert len(completed.stdout) > 150_000
    assert "the reason, which must be read first" in completed.stderr
    assert "Loud gate: FAILED" in completed.stderr
    assert len(completed.stderr) < 1024, completed.stderr
    assert "FAILED" not in completed.stdout

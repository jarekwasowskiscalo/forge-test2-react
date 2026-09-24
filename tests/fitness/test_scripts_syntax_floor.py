"""The bare-machine scripts parse on the oldest `python3` a machine may have.

`scripts/preflight.py` reports what a machine is missing -- including the Python this
project needs -- so it has to parse on the interpreter that machine already has.
`scripts/ci_summary.py` runs in CI's aggregate job with no toolchain installed, and
`scripts/app_status.py` answers `status.sh --json` before `uv` has synced anything.
`scripts/spa_build_state.py` is here for two reasons at once: `app_status.py` imports it,
so it parses on whatever interpreter starts that one, and `_lib.sh` runs it under a bare
`python3` before every `./scripts/test.sh ui` -- an import a bare machine cannot parse
would take the status report down with it.
The runtime floor is 3.14 (`requires-python`); the SYNTAX floor is older on purpose, and
`ruff`'s `target-version` has to agree with it, or the formatter writes syntax the older
interpreter refuses (PEP 758, `except A, B:`). `ast.parse(..., feature_version=...)` is
the check, and it is precise: CPython rejects syntax newer than the version it is given.
"""

import ast
import pathlib
import re
from typing import Final

from tests._repo import REPO_ROOT

#: The scripts a person or CI runs with a bare `python3`.
BARE_MACHINE_SCRIPTS: Final[tuple[str, ...]] = (
    "preflight.py",
    "ci_summary.py",
    "app_status.py",
    "scenario_census.py",
    "spa_build_state.py",
)

#: The oldest interpreter such a script may be started by.
OLDEST_BARE_PYTHON: Final[tuple[int, int]] = (3, 12)


def _rejections(paths: list[pathlib.Path], version: tuple[int, int]) -> dict[str, str]:
    rejected: dict[str, str] = {}
    for path in paths:
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path), feature_version=version)
        except SyntaxError as error:
            rejected[path.name] = f"line {error.lineno}: {error.msg}"
    return rejected


def test_ruffs_syntax_floor_is_the_bare_machine_floor() -> None:
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^target-version = "py(\d)(\d+)"', text, flags=re.MULTILINE)
    assert match, "pyproject.toml no longer pins ruff's target-version where this test looks"
    assert (int(match.group(1)), int(match.group(2))) == OLDEST_BARE_PYTHON


def test_every_bare_machine_script_parses_on_the_oldest_python() -> None:
    scripts = [REPO_ROOT / "scripts" / name for name in BARE_MACHINE_SCRIPTS]
    assert all(path.is_file() for path in scripts), [p.name for p in scripts if not p.is_file()]
    rejected = _rejections(scripts, OLDEST_BARE_PYTHON)
    assert not rejected, (
        f"these scripts use syntax Python {'.'.join(map(str, OLDEST_BARE_PYTHON))} rejects, and a "
        f"script that starts on that interpreter dies before it can say why: {rejected}"
    )


def test_the_check_rejects_the_syntax_it_is_here_for(tmp_path: pathlib.Path) -> None:
    probe = tmp_path / "probe.py"
    probe.write_text("try:\n    pass\nexcept ValueError, OSError:\n    pass\n", encoding="utf-8")
    assert "probe.py" in _rejections([probe], OLDEST_BARE_PYTHON)
    probe.write_text("try:\n    pass\nexcept (ValueError, OSError):\n    pass\n", encoding="utf-8")
    assert _rejections([probe], OLDEST_BARE_PYTHON) == {}

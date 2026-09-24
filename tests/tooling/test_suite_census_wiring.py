"""The e2e runner calls the scenario census, after the junit, without replacing it.

The census (`scripts/scenario_census.py`) subtracts what the feature files declare
from what the runner collected, and it can only read a report that exists -- so
the call has to come *after* the `--junitxml` run, and must not carry a
`--junitxml` of its own, or it overwrites the very file it is about to count.
Wired into `test.sh e2e` rather than as a bare CI step, because Article XII makes
`check.sh` the definition of "will CI pass" and a census only CI runs would make
that sentence quietly false.

This became safe to wire the day `gate.py decide()` learned to charge a non-zero
runner with a green report to the gate itself; before that, a red census beside a
green suite read as GREEN to the SDD gate while `check.sh` was red.

Read as text rather than by running the suite: the wiring is ORDERING inside a
shell function, and a green e2e run proves the two calls happened, never that the
census read the report this run wrote.
"""

import pathlib
import re
from typing import Final

_SCRIPTS: Final = pathlib.Path(__file__).resolve().parents[2] / "scripts"

_CENSUS: Final = "scripts/scenario_census.py"


def _census_wiring(name: str) -> tuple[str, str]:
    """The junit-writing line and the census line, in file order."""
    text = (_SCRIPTS / name).read_text(encoding="utf-8")
    junit = re.search(r"^.*--junitxml=e2e/reports/junit\.xml.*$", text, re.MULTILINE)
    census = re.search(rf"^.*{re.escape(_CENSUS)}.*$", text, re.MULTILINE)
    assert junit is not None, f"{name} no longer writes the e2e junit -- update this test"
    assert census is not None, f"{name} does not call the census at all"
    assert junit.start() < census.start(), (
        f"{name} calls the census before the junit is written -- it would count a stale "
        "report, or none"
    )
    return junit.group(0), census.group(0)


def test_the_runner_calls_the_census_after_the_junit() -> None:
    _junit_line, census_line = _census_wiring("test.sh")
    assert "--junitxml" not in census_line, (
        "test.sh's census call carries --junitxml and would overwrite the report it exists to count"
    )

"""The junit `test.sh` leaves behind has the shape the script contract promises.

The change process reads test-level evidence off the reports this template's
`scripts/test.sh` writes (the process's `script-contract.md`): `junit_family` decides
the element shape, `junit_logging` decides whether a `<failure>` body exists at all --
and the second is also Article XI, because a captured stdout is where a real name or
an e-mail address lands in an artifact CI keeps. A future "let us capture the logs for
debugging" has to argue with this assertion, not only with a comment.
"""

import tomllib

from tests._repo import REPO_ROOT


def test_the_junit_the_process_reads_is_xunit2_with_attributes_only() -> None:
    config = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    pytest_config = config["tool"]["pytest"]["ini_options"]
    assert pytest_config["junit_family"] == "xunit2"
    assert pytest_config["junit_logging"] == "no"

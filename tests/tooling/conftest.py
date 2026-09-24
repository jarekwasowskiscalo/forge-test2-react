"""Everything below this directory runs without a database, and says so by being here.

The marker is applied rather than written. `no_db` used to be opt-in, and the root
`conftest.py` argued for that: a forgotten marker is a gap, while the opposite default
would make a new test *fail* on a runner with no Docker whose author cannot reproduce it.

The directory settles the argument by removing the choice. Placing a file here *is* the
declaration, so there is no marker to forget -- and a test that does touch a database,
put here by mistake, now fails on the author's own machine instead of quietly vanishing
from the macOS leg, which is the failure that was actually expensive.

`tests/fitness/test_test_layout.py` proves the other half: nothing under
`tests/integration/` carries the marker.

Three identical copies of this file -- `tests/unit/`, `tests/fitness/`, `tests/tooling/` --
and deliberately no shared module behind them: the directory IS the declaration, and a
declaration that pointed elsewhere for its meaning would be a reference, not a declaration.
"""

import pathlib

import pytest

_HERE = pathlib.Path(__file__).parent


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Mark every test collected from this directory, and touch no other."""
    for item in items:
        if _HERE in pathlib.Path(str(item.path)).parents:
            item.add_marker(pytest.mark.no_db)

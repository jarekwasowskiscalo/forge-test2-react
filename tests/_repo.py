"""Where the repository root is, decided once.

Eleven modules used to count directories themselves -- `parents[1]`, sometimes
`parent.parent` -- and every one of them was correct only while it sat exactly
two levels down. Splitting the suite into `unit/`, `integration/`, `fitness/` and
`tooling/` moved all eleven one level deeper and broke all eleven at once, which
is the clearest possible argument that the count was never theirs to hold.

Imports nothing but `pathlib`, so it stays cheap to import from anywhere.

Deliberately imported by nothing under `e2e/`: `tests/fitness/test_e2e_isolation.py`
allows the end-to-end suite **no** first-party import at all, and a helper that
looked harmless is exactly how such a boundary acquires its first hole.
"""

import pathlib
from typing import Final

#: The repository root. `tests/_repo.py` sits directly under it, and this file
#: does not move -- the helpers stayed flat when the test modules were grouped.
REPO_ROOT: Final[pathlib.Path] = pathlib.Path(__file__).resolve().parents[1]

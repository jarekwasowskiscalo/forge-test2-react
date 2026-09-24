"""The one test module: bind every `.feature` to the step definitions.

`scenarios()` takes the **directory**, so a new `.feature` file is picked up
without an edit here and a run over zero scenarios is not something a typo can
produce.

**The wildcard imports are deliberate, and `architecture.md` records the
exception.** A pytest-bdd step definition is not the decorated function -- the
decorator writes a *fixture* into its defining module's globals under a
generated `pytestbdd_stepdef_*` name, and pytest only sees fixtures in the
module it is collecting. So importing the modules by name registers nothing at
all, and the scenarios fail at run time with "step definition is not found".
The two alternatives are worse: `pytest_plugins` outside the rootdir conftest is
a hard error in pytest 9, and `-p` in `addopts` would load the step modules into
every `tests/` run.

Two hazards come with that, and both are mechanised in
`tests/fitness/test_e2e_scenarios.py` rather than left to review: a step module that
defines `__all__` would have every step silently dropped by `import *`, and a
step module nobody imports here would leave its scenarios unbound.
"""

from pytest_bdd import scenarios

from e2e.suite.steps.guestbook_steps import *  # noqa: F403

scenarios("features")

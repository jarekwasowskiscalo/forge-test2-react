"""End-to-end scenarios, and the harness that runs them.

This tree drives a **running** application over HTTP and asserts only what an
HTTP client can see. `tests/` can reach into a service and check an invariant
that never crosses the wire; this one cannot, and between them they cover both
what the code believes and what it actually serves.

**Nothing here may import `app`.** The suite used to make that impossible by
living in a virtualenv of its own, which also put it outside mypy, outside
pytest and outside `uv.lock` -- so the rule held and nothing else did. The rule
is now asserted instead, by `tests/fitness/test_e2e_isolation.py`, and the tree is
ordinary Python in this project.

Two halves, and the dependency runs one way:

- `harness/` -- how a request is made, how a list answer is read, how a failure
  is phrased, how the target database is emptied. No domain word appears in it.
- `suite/` -- what a fully paid case is. Owns the `.feature` files, the step
  definitions, and every endpoint, JSON field and status code the scenarios rely
  on.

A harness module that imports `e2e.suite` is a defect, and the isolation test
says so with a line number.
"""

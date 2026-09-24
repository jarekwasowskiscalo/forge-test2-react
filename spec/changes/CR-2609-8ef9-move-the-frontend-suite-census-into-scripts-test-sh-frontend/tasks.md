<!-- TEMPLATE: filled in by the plan stage; the file counts as non-existent until this marker is gone -->
# Tasks — <change title>

## Wave 1 — tests

### T-1 · build-tests-integration · R-1
**Files:** `tests/integration/test_<subject>.py`
**Scope:** `tests/integration/test_<subject>.py` — *nothing beyond it; checked after the wave against `git diff`*
**Does:** <one sentence>
**Depends on:** —
**Must be red:** `tests/integration/test_<subject>.py::test_<name>`
**Verification:** `./scripts/test.sh backend` — the named test fails, nothing else changes

### T-2 · build-tests-e2e · R-1
**Files:** `e2e/suite/features/<file>.feature`, `e2e/suite/steps/<file>.py`
**Does:** <one sentence>
**Depends on:** —
**Must be red:** <scenario>
**Verification:** <the command and the expected result>

## Wave 2 — implementation

### T-4 · build-backend · R-1
**Files:** `app/contexts/<context>/services/<x>.py`, `alembic/versions/<new>.py`
**Scope:** `app/contexts/<context>/services/<x>.py`, `alembic/versions/` — *a subset of "This change owns" from the design*
**Does:** <one sentence>
**Depends on:** T-1
**Verification:** `./scripts/test.sh backend` — T-1's test passes

## Scope against the design
*The union of every task's **Scope** field has to fit inside "This change owns" from `design/delta/architecture.md`.
A task that steps outside that list is either a mistake in the plan or a design that kept
quiet about what it would touch — and both are settled now, not after the implementation.*

| Path from the design | Tasks that touch it |
|---|---|
| `<path>` | T-n |

## Disjointness
Wave 1: <sets>. Intersection: empty.
Wave 2: <sets>. Intersection: empty.

## Requirement coverage
| R-n | Tasks |
|---|---|
| R-1 | T-1, T-2, T-4 |

## What can go in parallel
<outright, so that nobody serialises out of caution>

## Lessons from the implementation

*Appended by the implementers during a wave, one line per lesson. The orchestrator pastes
this section into the next wave's prompts, so the second wave does not discover what the
first already knows — and `reconcile-docs` reads it at the end instead of guessing why
something has the shape it has.*

*Not "I did X". A lesson is something that surprised you: an assumption that turned out
false, a test that does not catch what it was meant to, or a place where the code does not
work the way it looks.*

- **T-n:** <what turned out to be the case — and what that did not catch>

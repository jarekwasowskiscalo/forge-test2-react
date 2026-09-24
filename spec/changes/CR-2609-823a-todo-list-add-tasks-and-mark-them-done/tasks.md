<!-- TEMPLATE: filled in by the plan stage; the file counts as non-existent until this marker is gone -->
# Tasks — <change title>

## Wave 1 — tests

### T-1 · <test author> · R-1
**Files:** `<test file>`
**Scope:** `<test file>` — *nothing beyond it; checked after the wave against `git diff`*
**Does:** <one sentence>
**Depends on:** —
**Must be red:** `<test file>::<the case's name, as the suite's junit spells it>`
**Verification:** `./scripts/test.sh <suite>` — the named test fails, nothing else changes

### T-2 · <black-box test author> · R-1
**Files:** `<scenario or journey file>`
**Does:** <one sentence>
**Depends on:** —
**Must be red:** `<scenario or journey file>::<the scenario's name>`
**Verification:** <the command and the expected result>

*Every field above is read by the `tasks` gate while this record is open: the owner is a
skill something can dispatch, `Files:`/`Scope:` name paths, `Depends on:` is `T-n` ids or
`—`, `Verification:` carries the command, and a test author's `**Must be red:**` names a
case a runner can collect — `<file>::<case>`, the one spelling `declare-red` accepts and the
junit carries. A case that is already green, and correctly so, is written
`green-by-design: <why the rule it asserts is already kept>` instead.*

## Wave 2 — implementation

### T-4 · <implementer> · R-1
**Files:** `<source file>`, `<second source file>`
**Scope:** `<source file>`, `<directory/>` — *a subset of the boundary this change recorded*
**Does:** <one sentence>
**Depends on:** T-1
**Verification:** `./scripts/test.sh <suite>` — T-1's test passes

## Scope against the design
*The union of every task's **Scope** field has to fit inside the boundary the design recorded
— the `boundary` your preflight envelope carries, which `set-boundary --from-design` read out
of the "This change owns" table in the delta fragments. Read it from there, not out of a named
fragment: `design/delta/architecture.md` exists only when the composition ran
`design-architecture`, and a change that touches only a screen never does.
A task that steps outside that list is either a mistake in the plan or a design that kept
quiet about what it would touch — and both are settled now, not after the implementation.*

| Path from the boundary | Tasks that touch it |
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

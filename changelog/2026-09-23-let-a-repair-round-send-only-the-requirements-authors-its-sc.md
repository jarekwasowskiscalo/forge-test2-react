---
date: 2026-09-23
branch: process/fix-conditional-requirements-family
pr: 79
kind: process
---

# Let a repair round send only the requirements authors its scope needs

## What changed

- `.specconf/process.json` § `fix_conditional`: three new entries, one for each member of the
  requirements family, plus a `$comment` paragraph explaining how each was derived:
  - `cr-impact` on `new_context` and `contexts_touched_gt_1`;
  - `cr-requirements` on all eleven signals this stack declares (the engine's six and the five
    path signals from `.specconf/stack.json` § `signals`), written out in full;
  - `cr-scenarios` on `contract_touched`, `screen_touched`, `schema_touched`, `rule_touched`
    and `backend_touched`.
- `tests/fitness/test_repair_composition.py` (new): re-runs the engine's composition arithmetic
  from the two profile files. It holds the compositions this entry promises, and it holds the rule
  the values were derived from.
- `spec/design/testing.md` § the fitness table: one row for the new module.

## Why

Issue #60 (B-2 of epic #58, E2-06). Until now `fix_conditional` named no member of the
requirements family. The engine dispatches a member absent from `conditional ∪ fix_conditional`
on every scope. So a `review_fix` return to `requirements` sent `cr-impact`, `cr-requirements` and
`cr-scenarios` unconditionally, however small the repair. On the other stack that round cost
$40.94, as much as the change it repaired.

The engine half landed first, as the epic's ordering rule requires:
Scalo-Sales-Engineering-Consulting/claude-marketplace#196 (forge 0.1.100) made a fix's scope
narrow `requirements` and `design` too. Scalo-Sales-Engineering-Consulting/claude-marketplace#274
(forge 0.1.120) withdrew the guard test that asserted no template had adopted yet. That guard runs
against this profile in `sdd-tests@main`, so without #274 this change would have turned CI red.
The flutter half is Scalo-Sales-Engineering-Consulting/forge-template-flutter#94.

## From what, to what

A repair returning to `requirements` on p2, by scope:

| the repair's scope | before | after |
|---|---|---|
| `frontend_touched`, `tooling_touched`, `infra_touched` or `ci_touched` alone | all 3 | `cr-requirements` |
| `backend_touched` | all 3 | `cr-requirements`, `cr-scenarios` |
| `screen_touched`, `contract_touched` or `rule_touched` | all 3 | `cr-requirements`, `cr-scenarios` |
| `new_context` | all 3 | `cr-impact`, `cr-requirements` |

## How it works now

The values follow one rule: **a consumer never goes out without the author of what it
requires**. This mirrors the existing rule that a builder never goes out without a test author.

- `impact.md` records how the area worked *before* the change, and a repair does not move the
  past. So `cr-impact` returns only when the repair's area is larger than the one already
  recorded: a new concept, or a second context.
- `cr-scenarios` carries the union of the conditions of the three members that require
  `scenarios.md`:
  - `build-tests-e2e`;
  - `build-tests-uat`;
  - `build-tests-integration`. This one is specific to this stack. Its skill refuses to invent a
    fixture value and takes every value from `scenarios.md § Test data`. So a backend repair,
    which dispatches it, needs the author of that section too. This is why the backend row keeps
    two authors where flutter's app-code row keeps one.
- `cr-requirements` carries every signal. `design-spec` requires `requirements.md` and is
  unconditional, so every scope that reaches the design stage needs a requirement.

The fitness module turns red on any of these:
- a profile signal is added without `cr-requirements` being decided again;
- a worker in `stack.json` gains a `requires` that its producer's conditions do not cover;
- a `cr-*` name appears in `conditional`, which would narrow the first pass too.

Its orphan detector is proved against a known positive: flutter's `cr-scenarios` entry, which
would leave `build-tests-integration` without fixtures here.

## What it means for the process

A repair round re-entering `requirements` now costs what its scope needs rather than a full
fan-out. Nobody has to do anything differently. Adding a signal or a worker now means deciding
this table again, and the new test says so by name.

## What it does not change

- The first pass through `requirements`: `conditional` still names no `cr-*` member, so an
  ordinary change sends all three authors.
- No tier, no step list, no other `fix_conditional` entry.
- The `set-fix-scope` precondition that still refuses a scope before the first turn-back is not
  addressed here. It is the engine's, tracked in claude-marketplace#164.

## How it was verified

- `./scripts/test.sh fitness -k repair_composition` against the old profile: 4 of 7 red. They
  failed on the missing entries, as expected. The consumer rule held trivially while every author
  was unconditional, and the known positive held.
- The same suite after the values: 316 passed.
- `./scripts/check.sh` and `./scripts/changelog.sh check --base main`: see the pull request.

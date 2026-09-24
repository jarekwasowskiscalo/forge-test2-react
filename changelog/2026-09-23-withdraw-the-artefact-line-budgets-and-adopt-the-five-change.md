---
date: 2026-09-23
branch: chore/withdraw-line-budgets-and-adopt-seeds
pr: 82
kind: process
---

# Withdraw the artefact line budgets, and adopt the five change forms the seed moved to

## What changed

- `.specconf/process.json`: `tiers.p0`–`p3.max_lines` are removed and `schema_version` goes from
  5 to 6. The `$comment` no longer lists line budgets among what this file composes, and it says
  why the key is gone. It also says outright that the numbers were byte-identical to the Flutter
  template's, and were withdrawn rather than re-derived.
- `.specconf/templates/change/`: five forms become byte-identical to the plugin's seed (forge
  0.1.124):
  - `delta.md`: the brief, with earlier passes in `delta-history.md` (#64);
  - `delta-fragment.md`: `set-boundary` records the table plus the trees the reconciliation
    writes, and the author must not declare them; each part of a fragment lands in the brief or
    in `delta-history.md` (#72, #64);
  - `coherence.md`: a repository path inside a quotation is a backticked path, never a Markdown
    link (#71);
  - `session-audit.md`: the briefing is an HTML comment, so `audit.md` opens with a verdict (#70);
  - `tasks.md`: both reds are spelled `<file>::<case>`, and the form closes with what the `tasks`
    gate reads (#74).
- `tests/fitness/test_process_schema.py` (new): the profile declares schema 6 or later, and no
  tier carries `max_lines`.
- `spec/design/testing.md`: the new module's row.

## Why

forge_template_python_react#58: #64 (audit E5-01, engine half claude-marketplace#204), plus the
seed adoptions #70, #71, #72 and #74. The audit measured all six budgets on one change. All six
were exceeded, `delta.md` by 24x, and every stage closed anyway: a number the engine printed a
multiplier for and refused nothing on. The numbers here were also Flutter's, byte for byte, so
they described no measurement of this stack.

The seed is what moves first, and the engine's `ALLOWED_DRIFT` names these five forms as ones this
stack had yet to adopt. Each entry dies on the marketplace pin that adopts this tree. The
`delta-fragment.md` entry needs both #64 and #72, which is why they travel together.

## From what, to what

Before: schema 5, with four tiers carrying budgets nobody enforced, and five forms that differed
from the seed under named, transitional exceptions.

After: schema 6, where the engine refuses the key outright, and every form in
`.specconf/templates/change/` except `README.md` is the seed's own copy.

## How it works now

An artefact has no line budget. `delta.md` is bounded by its shape: one entry per path, with
history kept beside it. A change record is filled from the same forms the plugin ships. A new
divergence from the seed fails the engine's suite on this stack as unexplained.

## What it means for the process

A plan now spells a red as `<file>::<case>`, a delta fragment no longer declares the
reconciliation's trees in its boundary, and a coherence finding quotes a path in backticks. The
forms say all three themselves.

## What it does not change

Records already committed under `spec/changes/` are not rewritten. They are dated evidence, and
the gates read them green as they are. `.specconf/templates/change/README.md` keeps its own text:
the seed's copy explains seeds, and this one is the authority. No tier's steps, ladder or gates
move.

## How it was verified

- `./scripts/test.sh fitness`: 311 passed. Seen failing first: `main`'s `process.json` is schema
  5 with `max_lines` in p0–p3, which both assertions refuse.
- `SDD_PROJECT_DIR=<this tree> plugins/forge/bin/sdd-tests` (forge 0.1.124): 3753 passed, 7
  skipped. This includes the byte-for-byte form comparison and loading `process.json` at
  schema 6.
- `sdd-specs`: OK. `sdd-engine stack --check`: OK.
- `./scripts/check.sh --fast --no-docker`: see the pull request. Its gaps are the database,
  Docker and e2e.

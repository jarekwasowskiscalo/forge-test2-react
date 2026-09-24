---
date: 2026-09-15
branch: engine/say-twenty-three-gates-and-take-the-window-class-axis
pr:
kind: docs
---

# Say twenty-three gates, and take the screen form's window-class axis

## What changed

- `CLAUDE.md` § The gates — "Twenty-two checks, in three families" becomes "Twenty-three".
- `.specconf/templates/system/ui-screen.md` — takes the plugin's seed verbatim, which gains a
  `## Layout by window class` section.

Nothing else. No code, no specification, no script, no workflow, no dependency.

## Why

Two engine changes landed upstream and each left this repository a sentence behind.

`claude-marketplace#54` added a twenty-third gate to the register, and
`test_sdd_spec_lint.py` holds this repository's `CLAUDE.md` to the count the register
actually has — it reads `len(spec_gates.GATES)` and looks for the spelled word. So the suite
went red here the moment that merged, on a number in prose.

`claude-marketplace#58` gave the screen form a window-class axis, and
`test_sdd_document_templates.py` holds `.specconf/templates/` byte-identical to the plugin's
seed. A form that does not follow is a form that has drifted, and the suite says so.

Neither was reachable from here before it merged: every template resolves the marketplace's
composite actions at `@main`, so an engine change is live the moment it lands and the
follow-up can only come after.

## From what, to what

Before: `CLAUDE.md` said twenty-two, the register held twenty-three, and the screen form was a
version behind the seed. The engine's suite failed here for two reasons that had nothing to do
with this repository's own code.

After: the number matches the register, the form matches the seed, and the suite is green
again, which is what lets this repository's commit be adopted as a pin again.

## How it works now

Exactly as before for anyone running or changing this repository. A screen document may now
carry a `## Layout by window class` section; a stack that declares no `window_classes` omits
it, which is this repository's case today, so nothing an author writes changes yet.

## What it means for the process

Nothing moves: the same scripts, the same suites, the same gates. The twenty-third gate was
already in force here — it arrived with the engine — and this only makes the prose say so.

## What it does not change

No behaviour, no specification, no invariant, no test, no CI job. `.specconf/stack.json` is
untouched, and this repository declares no `window_classes`, so the new section of the screen
form stays unused until it does.

## How it was verified

- `SDD_PROJECT_DIR=<this repo> sdd-tests` — green, run from a marketplace worktree carrying the
  engine commit that demands both changes. Both failures reproduced first and then went away:
  the gate count, and `system/ui-screen.md` under the byte-identity check.
- `SDD_PROJECT_DIR=<this repo> sdd-specs` — green.
- `./scripts/changelog.sh check` — passes on this entry.
- Not run here, and named: this repository's own CI, which runs on the pull request.

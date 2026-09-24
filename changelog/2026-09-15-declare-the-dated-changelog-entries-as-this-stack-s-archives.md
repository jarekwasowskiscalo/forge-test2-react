---
date: 2026-09-15
branch: gates/declare-stack-archives
pr: 18
kind: process
---

# Declare the dated changelog entries as this stack's archives

## What changed

`.specconf/stack.json` § `trees` gains one key:

```json
"archives": ["changelog/20"]
```

It sits after `lint_skip` and before `test_files`, where `forge-template-flutter` put its own.
The `$comment` block above it gains nine lines saying what the key answers, why `changelog/` was
never the engine's, and why the pattern names the record rather than the directory holding it.

Nothing else. No script, no workflow, no gate, no suite and no application file.

## Why

`claude-marketplace` 0.1.45 (PR #86, closing #79) took `/changelog/20` out of the hardcoded
`_ARCHIVE` tuple in `check_specs.py` and handed that declaration to the stack. The engine now
exempts only the archives it writes itself — `spec/ADR/`, `spec/changes/CR-`,
`spec/rationale/AUDIT-`, `retro/rounds/`. `changelog/` was never one of them: no constant in
`paths.py`, nothing written to it, nothing read from it.

Undeclared, the dated entries are linted by `backtick-paths` like any other document, and **a
dated record lints falsely by construction**: its paths were right on the day of the change and
go stale every time the tree moves, for ever. The correct answer when one rots is not to edit the
entry — a corrected record agrees with today at the cost of no longer being a record.

This is tidiness rather than a repair, and the distinction is worth stating plainly: no entry
here has a stale path yet. `forge-template-flutter` had exactly one and took the same line as an
urgent fix. The first directory move produces ours, and the declaration has to be in place before
that, not after — because afterwards the cheap-looking answer is the wrong one.

## From what, to what

Before: `trees` had no `archives` key, so `stack.current().trees.archives` was the empty tuple and
every dated entry was read by `backtick-paths` — 69 documents, 847 paths.

After: the seven dated entries are skipped and `changelog/README.md` and `changelog/TEMPLATE.md`
are not — 62 documents, 802 paths. The 45 tokens that stop being checked are the ones inside the
records.

## How it works now

`check_specs._is_archive` asks *is this document a dated record* in two halves: the engine's four
literals, and the stack's patterns through `stack.matches`. A document matching either is skipped
by `backtick-paths`.

`changelog/20` is a **plain prefix**, and that spelling is the whole of the decision. It covers
`changelog/2026-09-15-*.md` and stops there. `changelog/` would end in a slash, `stack.matches`
tests the trailing slash first, and it would read as a directory prefix — silencing `README.md`
and `TEMPLATE.md` along with the entries, with nothing reporting the loss. Those two describe
**today** and are edited when today changes, so they must stay linted.

## What it means for the process

Nothing about running or changing this repository moves: no stage, no gate, no skill, no script
and no suite. An author writes an entry exactly as before.

What changes is where the exemption is *recorded*. It is this stack's statement about its own
documents now, in the profile the engine reads, rather than a directory name compiled into an
engine that knows no directory names.

## What it does not change

* No other `trees` key is touched, and none is reused. `archives` answers *which of this stack's
  documents are dated records*; it is not `lint_skip`, which is about generated files, and this
  repository declares no `decision_register` to confuse it with.
* `changelog/README.md` and `changelog/TEMPLATE.md` stay linted, by construction and by the
  mutation check below.
* `SCHEMA_VERSION` does not move: the key is additive and optional, and bumping it would refuse
  the sibling template at import.
* CI was green before this change and is green after it. Nothing here was red.
* The application is untouched, so `scripts/check.sh` judges nothing that moved — see below.

## How it was verified

Against the engine at `claude-marketplace` 0.1.46 (`188181b`), which is what this repository's CI
resolves at `@main`:

* `sdd-specs` — **OK**. `backtick-paths` 0 problems, **62 documents, 802 paths** (undeclared, on
  the same tree: 0 problems, **69 documents, 847 paths**). The drop is exactly the seven dated
  entries and the 45 tokens inside them, which is the evidence the declaration is *read* rather
  than merely accepted.
* `sdd-tests` — **2650 passed**, 7 skipped, 0 failed.
* The cut is proved by mutation rather than asserted, in both directions. A dead path appended
  to `changelog/README.md` is reported:

  ```
  changelog/README.md:79: [backtick-paths] `app/no/such/file.py` does not exist.
  ```

  The same dead path appended to a dated entry is not reported at all. That is the
  `changelog/20`-versus-`changelog/` distinction demonstrated rather than argued: a `changelog/`
  declaration would have silenced the README case too, and silenced it with nothing to tell you.
* Both mutations were reverted; the diff is `.specconf/stack.json` and this entry.

**Not run:** `scripts/check.sh`. It is the application's gate set by its own statement — the
specification gates are deliberately not in it — and this change touches no application file,
no script and no workflow. The gates that judge a `.specconf/stack.json` edit are the two run
above, and they run in this repository's CI through the marketplace's composite actions.

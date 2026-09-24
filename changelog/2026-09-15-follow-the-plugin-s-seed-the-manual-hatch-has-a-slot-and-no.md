---
date: 2026-09-15
branch: forms/follow-the-plugins-seed-for-the-hatch-and-the-corpus
pr:
kind: chore
---

# Follow the plugin's seed: the manual hatch has a slot, and no form names a corpus

## What changed

Four forms under `.specconf/templates/change/`, taken from the plugin's seed verbatim:

- `requirements.md` — the `R-1` block gains a `**Verified-by:** manual` slot, inside an HTML
  comment that states the rules for using it.
- `uat.md`, `scenarios.md`, `input-README.md` — the literal `golden-set/` is replaced by what
  the stack profile declares (`trees.fixtures`, `trees.seed`), which the worker's brief names
  in a new `REFERENCE DATA` section.

Nothing else moves. No code, no specification, no script, no workflow.

## Why

Both defects were found by an audit of the test area in THIS repository and reported to the
plugin as issue #42, deliberately unfixed here: these forms mirror the plugin's seed byte for
byte, and `test_sdd_document_templates.py` holds them to it, so patching a fork of the form
would have split it from the process that reads it.

The plugin has now fixed both at the source. This is the other half: the copies follow, and the
byte-identity check goes green again.

`traceability` parses `**Verified-by:** manual — <reason>` out of a change's `requirements.md`
and accepts no row in `spec/changes/EXEMPTIONS.md`, because the exit is meant to be in the
artefact. The form did not offer the field, so the only exit the gate has was reachable by
nobody following the process.

And `uat.md` told an author to take identifiers from `golden-set/fixtures/` by name. That
directory does exist here — but it exists because THIS profile declares it, and a form shipped
to every project cannot know that. The other pinned template has no such directory, and was
being handed the same instruction.

## From what, to what

Before: the form offered no `**Verified-by:**` field, and three forms named `golden-set/`
outright. `trees.fixtures` and `trees.seed` already said `golden-set/fixtures/` and
`golden-set/seed/`, so the same fact was written twice — once where it could be wrong.

After: the hatch has a slot, and the forms ask the profile. On this stack the brief's
`REFERENCE DATA` section names exactly the two paths the profile declares, so nothing an author
sees changes in substance — only where it comes from.

## How it works now

A requirement no automated suite can prove is marked by deleting the two comment markers in the
form's `R-1` block and writing at least twenty characters of reason. The gate counts it and
prints it, and `uat.md` then owes that `R-n` a numbered step. A marker spelt wrongly is reported
as a marker spelt wrongly.

Where test data comes from is a question the stack profile answers. Every worker's brief carries
a `REFERENCE DATA` section built from `trees.fixtures` and `trees.seed`.

## What it means for the process

Nothing about running this repository moves: the same scripts, the same suites, the same gates.
For an author of a change record, one field exists that did not, and the forms no longer point
at a directory the profile has not declared.

## What it does not change

No behaviour, no specification, no invariant, no script, no workflow, no dependency. The
`.specconf/stack.json` profile is untouched — it already declared both corpus keys, and both
values stand exactly as they were. `spec/changes/EXEMPTIONS.md` still takes no `traceability`
row: the exit is in the artefact, which is the whole point of the slot.

## How it was verified

- The four forms were diffed against the plugin's seed and are byte-identical; `README.md`
  remains the one named divergence, as `ALLOWED_DRIFT` records.
- The engine's suite was run against this repository from the marketplace worktree that carries
  the matching plugin commit, and `test_sdd_document_templates.py` passes in both directions.
- The specification gates were run against this repository and pass.
- Not run here, and named: this repository's own CI, which runs on the pull request.

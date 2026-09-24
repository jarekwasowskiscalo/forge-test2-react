---
date: 2026-09-14
branch: main
pr:
kind: process
---

# Record every change made outside the process, in a file per pull request

## What changed

A new tree, `changelog/`, holding `README.md` (the convention), `TEMPLATE.md` (the form,
carrying the scaffold marker so no linter reads it as a document) and one dated entry per
pull request — this file being the first.

`scripts/changelog.sh` is the interface, with two verbs: `new "<title>"` writes today's entry
from the form, and `check` is the gate. It is registered in `scripts/help.sh`, committed
executable and shellcheck-clean, which is what `scripts/hygiene.sh` asks of every script here.

`.github/workflows/ci.yml` gains a `changelog` job that runs that script on the pull request,
named in the workflow's header comment and read by the `ci` aggregate. Three registers that
hold this workflow to itself were updated with it: `scripts/ci_summary.py` says what the job
answers, `tests/fitness/test_ci_parity.py` declares it CI-only and declares `changelog/`
unrouted, and `spec/design/testing.md` § What only CI can answer names it as a blind spot.

`.github/pull_request_template.md` gains a section with the same two-checkbox shape the
specification section already uses. `CLAUDE.md` gains the rule and a row in its structure
tree; `docs/README.md` gains a row in *What is not here*.

## Why

`spec/constitution.md` makes framework changes on the trunk and gives them no `delta.md`, and
only a behaviour change gets a change record. That is the right rule — five stages of ceremony
around a forty-line repair is a ratio nobody should pay — but it left a hole. The reasoning
behind every change to the scripts, to CI, to the infrastructure and to the documentation
survived only in a squash-commit body and a pull-request description: not browsable, not
greppable as a set, and invisible to anyone reading the tree six months later.

`spec/changes/INDEX.md` answers *what went through the process*. Nothing answered *what was
done to the framework, and why*.

## From what, to what

Before: a change outside the process left a commit subject, a body if its author wrote one,
and nothing in the tree. Recovering the reasoning meant `git log` and knowing what to look
for.

After: it leaves a file, in a directory that sorts by date, answering seven fixed questions.
The commit body is still written and still says the same thing; the entry is the copy that
stays where a reader will find it without being told it exists.

## How it works now

A change that does not go through `/forge:sdd` runs `./scripts/changelog.sh new "<title>"`,
which writes `changelog/<today>-<slug>.md` with the front matter filled and the seven headings
in place. The author fills them in. On the pull request the `changelog` job runs
`./scripts/changelog.sh check`, which demands that the diff adds at least one entry and that
each added entry is well formed: front matter with a `date` and a known `kind`, exactly one
title, every section present, and no section still holding nothing but the form's own prompt.

It passes, printing which exemption it used, in four cases: there is no base to diff against,
the diff carries a change directory under `spec/changes/CR-*`, the author is a bot, or the
pull request has the `no-changelog` label.

## What it means for the process

Nothing inside `/forge:sdd` moves. The process's stages, gates and documents are untouched,
and a change that has a directory under `spec/changes/` writes no entry — the two registers
cut the same history by the road a change took, and never overlap.

What changes is the trunk. Work the constitution permits without a record now leaves one, and
the record is cheap: one script invocation and seven short answers.

## What it does not change

The release path is untouched: `scripts/release.sh` still writes the annotated tag's commit
list and `.github/workflows/release.yml` still generates the GitHub release page, and neither
reads this tree. Those are two audiences with two sources, as `release.yml` says; this is a
third with a different subject, and it duplicates neither.

There is no generated index of entries: that would mean a new input to the non-exemptable
`generated-indexes` gate, and a directory named by date already sorts itself.

## How it was verified

`./scripts/changelog.sh --help` answers, and `shellcheck -x scripts/changelog.sh` is clean.
The gate's six behaviours — refusing a diff with no entry, and passing for a bot author, for
the `no-changelog` label, for a diff carrying a change directory, for a well-formed added
entry, and refusing one with a section deleted — were each proved against a throwaway
repository before the script was copied here.

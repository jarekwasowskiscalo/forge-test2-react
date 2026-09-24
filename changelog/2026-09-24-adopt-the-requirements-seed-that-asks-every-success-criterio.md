---
date: 2026-09-24
branch: chore/adopt-requirements-seed
pr:
kind: process
---

# Adopt the requirements seed that asks every success criterion for a baseline and a measurement after delivery

## What changed

`.specconf/templates/change/requirements.md` is now byte-for-byte identical to the plugin's seed
`document-templates/change/requirements.md` (forge 0.1.126). It differs from the previous copy in
two places:

- **`## Success criteria`:**
  - A paragraph and a comment now come before the table.
  - The table changes from `| Id | Criterion | How measured |` to
    `| Id | Criterion | Baseline | How measured after delivery |`.
  - Either new cell may say "not measured, because …".
- **`### Attacks`:** the category placeholder is now separated by commas, and its last category is
  `slow-network / offline`.

## Why

Upstream, claude-marketplace issue 243 (U-6 of epic 250) was delivered in pull request 285, plugin
0.1.126. The success criteria asked "how will we know this worked". They did not ask for the state
before the change, or for who would measure the effect once it had shipped. So a criterion stated an
intent, and after delivery nobody owned the question "did it help". The attack list also had no
category for the case where a person loses what they typed into a form because the network is slow
or gone.

The plugin's copy is only the seed. The engine reads this project's copy, and the
`cr-requirements` content check asks exactly what this copy asks. Until this merge the check asked
nothing here and printed a warning instead. Tracked here as issue 86.

## From what, to what

**Before.**
- A success criterion had one column for how it was measured. In practice that column held the
  test that proves it at delivery.
- A blank cell passed.
- The attack list had seven categories.

**After.**
- Every success criterion names where it starts and who measures it after delivery, with what and
  when. Where neither can be said, the cell says why.
- The content check refuses a blank cell, a lone dash, a placeholder left standing, a dropped or
  merged column, a repeated `SC-n`, or a section with no criterion.
- The attack list has eight categories.

## How it works now

- `cr-requirements` scaffolds `requirements.md` from this copy.
- Its content check (`resources/cr_requirements_verify.py`) reads every row of
  `## Success criteria`. The check accepts any text as an answer, including "not measured,
  because …", and refuses only a blank.
- The requirements skill asks the slow-network / offline question beside empty and concurrency. A
  line saying why a category cannot happen is its answer.

## What it means for the process

- An author writing requirements here fills two cells per success criterion.
- `CR-2609-8ef9` (draft, deferred) still carries an unfilled form from before this change. Whoever
  fills it in will be asked for the two columns and will have to add them.

## What it does not change

- The records already committed. `CR-2609-9b1e-guestbook` is merged and closed, and the content
  check tolerates a settled record.
- The CI `requirements` gate, which judges no committed record again.
- `.specconf/stack.json` and every other form.
- The transitional `ALLOWED_DRIFT` entry for this stack in the marketplace's
  `test_sdd_document_templates.py`. That entry describes the gitlink, so it goes on the marketplace
  pin bump that picks up this commit, not on this merge.

## How it was verified

- `cmp` of the plugin seed (forge 0.1.126) against `.specconf/templates/change/requirements.md`:
  identical.
- `./scripts/changelog.sh check --base origin/main`, locally, before the push.
- The marketplace engine's suite against this tree with the transitional entry removed (the state
  after the pin bump): see the pull request.
- CI on the pull request.

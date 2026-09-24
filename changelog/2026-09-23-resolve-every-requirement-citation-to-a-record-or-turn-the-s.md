---
date: 2026-09-23
branch: process/resolve-every-requirement-citation
pr: 75
kind: process
---

# Resolve every requirement citation to a record, or turn the suite red

## What changed

- `tests/fitness/test_requirement_citations.py` (new) — three sweeps over the traceability
  surfaces `.specconf/stack.json` § `traceability` declares, each preceded by a known positive:
  every citation resolves to a record under `spec/changes/` and to an `R-n` that record
  declares; every citation-shaped string on a surface (`mark.req(`, `@req:`, `[req:`) is one the
  surface's own form reads in full; and `tests/fitness/`, `tests/tooling/` and `e2e/ui/` carry
  no citation. The three citation patterns and the declaration heading are copied from the
  engine's `traceability.py` (`_MARKER`, `_TAG`, `_IN_NAME`, `_DECLARED`), never imported.
- `tests/_change_record.py` (new) — the template's own readiness contract for a change record:
  a document that still carries the scaffold's `TEMPLATE:` marker comment declares nothing, HTML
  comments are guidance rather than declarations, and a record is addressed by its
  `CR-YYMM-xxxx` prefix.
- `spec/design/testing.md` § fitness table — one row for the new module, which
  `test_test_layout.py` requires, and a dated `Rejected` block naming the three alternatives
  turned down (trusting `traceability` alone, importing the engine, checking the reverse
  direction).
- `spec/changes/EXEMPTIONS.md` — the two rows for the 2026-09-08 audit (`change-directory` over
  `alembic/env.py` and the rest, `e2e-scenario` over `frontend/src/components/ui/**`) expired on
  2026-09-22 and turned the `exemptions` content gate red on every pull request. The repairs
  they covered merged long before, so the exemption is over and the rows are deleted rather
  than renewed.

## Why

[#59](https://github.com/Scalo-Sales-Engineering-Consulting/forge_template_python_react/issues/59)
(audit 2026-09-20, E1-04, epic #58): nothing in this repository opened
`spec/changes/*/requirements.md`, so 123 citations — 52 `@pytest.mark.req` markers, 21 Gherkin
`@req:` tags and 50 `[req:…]` vitest names — were checked against nothing. The process's
`traceability` accounts per change, from the record to the citation, so a citation belonging
to no change is invisible to it and a tree with no record is green on an empty set. The
Flutter template already had this gate (`test/fitness/citation_resolves_test.dart`,
`citation_form_test.dart`); this stack had none.

## From what, to what

Before: a typo in a citation id (`R-99`, a wrong change prefix, a bare `R-1`) counted as
coverage in a reader's eyes and was refused by nothing in this repository. After: the backend
suite's fitness group is red, naming `path:line` and what is missing — the record, the
requirement, or a readable form.

## How it works now

`./scripts/test.sh fitness` runs the module with no database. The surfaces come from the
profile, so a new surface is swept the day it is declared; a surface naming a form this module
has no pattern for is itself a failure. A fresh change record copied from
`.specconf/templates/change/` declares nothing until its marker is removed —
`CR-2609-8ef9` is such a record today — and the seed is proved to be recognised.

## What it means for the process

None for running it. For writing tests: a citation must name a requirement declared in a
record that is on the trunk or on the same branch — which is already what the process asks.

## What it does not change

The reverse direction — a declared requirement no test cites — is deliberately not checked
here: between the requirements stage and the first implement wave real identifiers exist and
no test cites them yet, and knowing the phase is the process's (claude-marketplace#192).
`test_evidence_map.py`, `test_withdrawn_claims.py` and `test_test_layout.py` are untouched;
`.specconf/stack.json` is untouched; nothing imports the engine.

## How it was verified

- `./scripts/test.sh fitness -k requirement_citations` — 19 passed.
- Red on the real tree, then reverted: changing one marker in
  `tests/unit/test_entry_text_rules.py` to `CR-2609-9b1e/R-99` failed the resolve sweep with
  `tests/unit/test_entry_text_rules.py:77: CR-2609-9b1e declares no R-99`; changing one tag in
  `e2e/suite/features/guestbook.feature` to `@req:R-1` failed the form sweep with
  `e2e/suite/features/guestbook.feature:12: '@req:R-1'`.
- `./scripts/test.sh fitness` — 298 passed; `./scripts/test.sh backend --no-db` green;
  `./scripts/lint.sh` and `./scripts/changelog.sh check --base main` OK.
- `./scripts/check.sh` could not run its database, image and e2e gates on the authoring machine
  (the Docker daemon was not answering); CI runs them on the pull request.

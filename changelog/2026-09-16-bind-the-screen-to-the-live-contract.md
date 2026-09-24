---
date: 2026-09-16
branch: forms/bind-the-screen-to-the-live-contract
pr: 34
kind: docs
---

# Bind a screen's fields to the live contract, and stop the Source column assuming HTTP

## What changed

`.specconf/templates/system/ui-screen.md` § Data, and nothing else in this repository.

- The binding target is the live `spec/design/api.md`, with a sentence saying a change's own
  `design/delta/api.md` is **not** a binding source.
- `| Element | Endpoint | Fields |` becomes `| Element | Source | Fields |`, and the paragraph
  above the table says the Source column names whatever this stack's `binding_target`
  declares.

The file is byte-identical to the engine's seed,
`plugins/forge/document-templates/system/ui-screen.md` in `claude-marketplace`, which is what
`test_sdd_document_templates.py` requires of it.

## Why

§ Data told an author to bind a screen's fields to *"this change's `design/api.md`"*, while
the same form four lines above correctly named `spec/design/api.md`. Two instructions about
one fact, in one document.

That is worse than a dangling path. The change directory really does produce
`design/delta/api.md`, so an author following the wrong instruction lands one level off, binds
the screen to a document describing only what this change alters, and the binding looks
successful — it passes further than a STOP would.

The `Endpoint` header assumed the contract is served over HTTP. It is served over HTTP
here, which is exactly why the word could sit in a shared form unnoticed: the same bytes go
to a stack that serves no route, where the column asks for a value that does not exist.

## From what, to what

Before: the form pointed into the change directory, and its table header named a transport.
The filled documents in this repository had been corrected by hand; the form they are written
from had not, so every new screen reproduced the divergence.

After: the form points at the live contract, says the delta fragment is not a binding source,
and names its Source column after whatever the stack declares. The three copies of the form —
the engine's seed and both templates' — agree byte for byte again.

## How it works now

Somebody writing a screen document copies this form, reads *Bound to the live contract in
`spec/design/api.md`*, and fills a Source column whose meaning their own preflight names under
`MECHANISMS`.

## What it means for the process

Nothing about running or changing this repository moves. No script, no gate and no workflow
reads the changed lines; the form is the shape a document is written in.

## What it does not change

`.specconf/stack.json` and `.specconf/process.json` are untouched — this repository declares
none of the engine's four new mechanism keys yet, and does not have to: they are optional and
the profile loads exactly as before. Declaring them, and the rest of the scope named in the
issue below, is not in this change.

No document under `spec/design/ui/` is edited, and none needs to be: this repository's
screen documents carry no data-binding table, so nothing here was written against the old
header.

## How it was verified

The engine's suite, run against this checkout from the `claude-marketplace` working tree
before the change was pushed:

- `SDD_PROJECT_DIR=templates/python-react plugins/forge/bin/sdd-tests` — green with this copy in place,
  and failing on exactly one test without it,
  `test_every_form_is_byte_identical_unless_the_divergence_is_named`, which is the test this
  change exists to satisfy.
- `SDD_PROJECT_DIR=templates/python-react plugins/forge/bin/sdd-specs` — OK.

The byte-identity is the claim, so it was checked as one: `diff` against the engine's seed is
empty.

This branch could not go green until
Scalo-Sales-Engineering-Consulting/claude-marketplace#115 merged, because the test compares
this copy against that seed resolved at `@main`. That merged first; this follows it.

---
date: 2026-09-15
branch: gates/name-the-twenty-third-check
pr: 11
kind: process
---

# Let a row exempt the screen-states gate

## What changed

- `spec/changes/EXEMPTIONS.md` — `screen-states` joins the content gates a row of this
  register may name, alphabetically between `requirements` and `session-archives`.

That is the whole change. One line, wrapped onto two.

## Why

The process grew a twenty-third gate, `screen-states`, which reads a screen document's
state table: it refuses a state row with an empty cell, a `States omitted:` line that names
a state without saying why, and a document whose components account for `empty` nowhere at
all. It arrived in the marketplace with
Scalo-Sales-Engineering-Consulting/claude-marketplace#54.

This register enumerates the gates a row may name, and the list is read by a person rather
than derived from the engine. A gate missing from it is one nobody can write an exemption
for — and the omission is invisible until somebody needs one, which is the worst moment to
discover it.

The other half of following that gate — the `CLAUDE.md` sentence that counts the process's
gates, held by `test_the_counts_claude_md_spells_out_are_the_counts_the_tree_has` — arrived
here already, with the window-class work. Only the register was left.

## From what, to what

Before: eleven content gates listed as reachable by a row.

After: twelve.

## How it works now

Unchanged in every respect a person acts on. If `screen-states` ever refuses something that
has to ship anyway, a dated row naming it now parses and is honoured, like any other content
gate. Nothing in this repository needs one today: the gate reports zero problems over both
screen documents.

## What it means for the process

Nothing about running or changing this repository moves.

## What it does not change

- No screen document, and no `.specconf/templates/` form. The gate is the rule
  `.specconf/templates/system/ui-screen.md` has always stated — list the states that exist,
  declare the omitted ones with a reason — now read by something other than a person, and
  this repository's screen documents already satisfied it untouched.
- Not `CLAUDE.md`, which already counts twenty-three.

## How it was verified

- `sdd-specs` — `Specs: OK`, with `screen-states` reporting 0 problems over 2 documents
  (8 components / 23 states) and `exemptions` clean over the edited register (2 rows).
- `sdd-tests` — 2607 passed, 7 skipped.

Both are re-run by CI on this pull request, against the engine on the marketplace's `main`,
which now carries the gate.

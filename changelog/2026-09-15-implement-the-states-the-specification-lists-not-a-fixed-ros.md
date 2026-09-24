---
date: 2026-09-15
branch: skills/implement-the-states-the-specification-lists
pr: 15
kind: fix
---

# Implement the states the specification lists, not a fixed roster of eight

## What changed

- `.claude/skills/build-frontend/SKILL.md` — two sites. The Stage 2 rule no longer calls what
  the screen document holds "the eight states", and IRON RULE 4 asks for every state **the
  specification lists**, names the component's table as the roster, and says where the eight
  went: considering them is the specification author's job, not the implementer's.
- `changelog/2026-09-15-let-a-row-exempt-the-screen-states-gate.md` — `pr:` still read "<the
  number, once the pull request is open>", where the number has been known since #11 merged.
  Corrected in passing: a register whose own form is left unfilled reads as one nobody checks.

Nothing under `spec/`, `app/`, `frontend/` or `scripts/` moves.

## Why

The rule could not be obeyed against this repository's own screen document. `spec/design/ui/`
`guestbook.md` has no `hover` row and no `active` row anywhere: the composer card lists
`default`, `focus`, `error`, `disabled` and `loading`, the entry card `default`, `edited`,
`editing`, `saving` and `deleting`. An implementer reading "Default, hover, focus, active,
disabled, error, loading, empty" literally was told to build states nothing had specified —
and IRON RULE 5 forbids inventing the copy they would need, so the rule sent them into a
`NEEDS_DECISION` the specification had already answered by leaving the state out.

It was also the last copy of a rule withdrawn twice. `spec/design/ui/README.md` § "Why states
are enumerated" has said **only the states that exist on the built screen** since finding F-49
in `spec/rationale/AUDIT-2026-09-02.md:84` — *"the README demanded eight states, the template
only the existing ones"* — where the README and the document form were fixed and this skill
kept its copy. `Scalo-Sales-Engineering-Consulting/claude-marketplace#45` settled the same
contradiction on the process side, in `design-ui`, and added the `screen-states` gate. That
gate reads state tables under `spec/design/ui/**` and reads no skill, so nothing here was ever
going to find this one; it was found by hand while doing #45 and filed as issue #10.

## From what, to what

Before, rule 0: *"The screen document holds **the eight states** and the interface copy"*. Rule
4: *"Every state in the specification is implemented, including the empty one. Default, hover,
focus, active, disabled, error, loading, empty."*

After, rule 0: *"the states and the interface copy"*. Rule 4: *"Every state **the specification
lists** is implemented, including the empty one"* — the component's table is the roster, under
the names it uses, with the entry card's `editing`, `saving` and `deleting` as the proof that
no fixed list of eight carries them.

## How it works now

The implementer walks the component's table in `spec/design/ui/<screen>.md` and builds the rows
that are in it, empty first. A state that is not in the table is not theirs to invent. A state
that is in it and says nothing is still `NEEDS_DECISION`, by the ERROR HANDLING row that has
always said so. Where a table carries a `States omitted:` line, that line is the record of what
the author considered and ruled out — `guestbook.md` carries none, because nothing was.

## What it means for the process

Nothing to relearn beyond the rule itself. The six other sites in this skill that speak about
states — CONSTRAINTS 4, QUALITY GATE 4, the Phase 3 checklist, the defect list, the input table
and the BOTTOM LINE — already said *specified* and were already right; that is why the fix is
two sites rather than eight.

## What it does not change

- No screen document, no specification, no code. `guestbook.md` was right and stays byte for
  byte as it was; it was the skill that was wrong about it.
- `build-tests-frontend`, which already asks for "every specified state that is observable",
  and the flutter template, which carries no copy of this rule at all.
- The gate. `screen-states` reads `spec/design/ui/**`, not `.claude/skills/**`, so this rule is
  held by a reader and not by a check — which is precisely how F-49 left half of itself behind
  for two weeks, and is worth knowing rather than assuming.

## How it was verified

`git` on the machine this ran on is blocked by an unaccepted Xcode licence; every command was
run with `DEVELOPER_DIR=/Library/Developer/CommandLineTools`.

- Read side by side with `spec/design/ui/README.md` § "Why states are enumerated" and
  `.specconf/templates/system/ui-screen.md`: one rule between the three, no second version.
- `grep -rn eight .claude/skills/` — one hit, the sentence that says the roster is not the
  implementer's obligation. Before this change there were two, both obligations.
- `grep -n state .claude/skills/build-frontend/SKILL.md` — every remaining site reads
  *specified* or names `spec/design/ui/<screen>.md`.
- The engine's suite and gates against this working tree, from the marketplace checkout that
  pins it: `sdd-tests` and `sdd-specs` — the verdicts are in the pull request body.
- `./scripts/changelog.sh check --file changelog/2026-09-15-implement-the-states-the-specification-lists-not-a-fixed-ros.md`.

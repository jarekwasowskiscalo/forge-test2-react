# `spec/rationale/` — lasting reasoning

Notes the code still rests on that fit in no normative document. Today: `mockup-guestbook/` (the
Claude Design mock-up the guestbook screen was built from) and the dated audits
`AUDIT-<date>.md` (a measurement of the tree on a given day, not edited afterwards).

The directory stays because its role in the process stays: `reconcile-docs` has it in its write
set, and it is where reasoning worth outliving one change is put down.

## What belongs here, and what does not

**Belongs:** a dated audit, a measurement, a planning note a decision in the code still stands on
— knowledge somebody would reconstruct from nothing if it were absent.

**Does not belong:**

| Thing | Home |
|---|---|
| A rejected alternative | the ADR that rejected it, or the decision paragraph in a normative document — never here |
| A rule that holds now | `spec/design/` or `spec/contexts/` |
| A fact always true of the data | `contracts/invariants/` |
| A deliberate non-goal | `spec/invariants.md` |
| What a particular change changed | `spec/changes/<CR>/` |

**Nothing in this directory binds by itself.** A document here describes why something is the way
it is; if it is also to *hold*, that sentence must stand in a normative document rather than
here. A descriptive document read as normative is a second home for one rule — exactly the
failure `spec/README.md` defends against.

## A document here is dated

A document here is dated and is not edited after the fact. An audit rewritten a year later
stops saying what was measured then.

<!-- TEMPLATE: filled in by the requirements stage; the file counts as non-existent until this marker is gone -->
# Requirements — <change title>

**Change:** <cr_id>
**Source:** request.md, impact.md, brainstorm.md

## Goal
<one sentence: the observable change in the world>

## Success criteria

Measurable effects, **deliberately non-technical** — this is the answer to "how will we know
this worked", not to "what did we build". A functional rule says what the system does; a
success criterion says what changes for a human. Without that layer a change can be
implemented in full and be useless in full, and nothing will show it.

- ❌ "the `/api/entries` response time below 200 ms" — that is a measure of the implementation
- ✅ "the operator sees the list of cases at once, without waiting on a spinner"

Every criterion answers two more questions, because one that nobody checks after delivery is
a sentence about intent: **where it starts** — the state today, observed rather than
remembered — and **who looks again once it has shipped**, with what, and when. "Not measured,
because …" is a full answer to either, and often the right one: an internal change may have
nothing a person could observe.

<!-- Both columns are read, row by row, by the cr-requirements content check. A cell left
     empty, a lone dash, or a placeholder still standing is silence, and the check refuses it.
     "Not measured, because the change is internal" passes, and it is what the column is for:
     the reason written down instead of the question skipped. The Baseline here is the
     criterion's, not the verification baseline cr-request records -- that one is about gates,
     this one is about the world. -->

| Id | Criterion | Baseline | How measured after delivery |
|---|---|---|---|
| **SC-1** | <an observable effect for a human or for the data> | <the state before this change, as observed today — or "not measured, because …"> | <who measures it, with what, and when — or "not measured, because …"> |

## Requirements

Stories ordered by **priority**, each **independently testable**. Priority is not a label of
importance — it is the answer to "if we ship only one, does it still make sense". Without
that order the scope cannot be trimmed under pressure, because nothing says what is the core
and what is an addition, and trimming ends with removing something that held the rest up.

### R-1: <area> — **P1**
**Objective:** As a <role>, I want <capability>, so that <benefit>.
**Why this priority:** <what happens if it is absent; P1 = without it the change makes no sense>
**Independent test:** <how to check this alone, without R-2 and the rest>
<!-- Only when NO automated suite can prove this requirement. Delete the two comment
     markers to use it; leave them and this line says nothing to anybody.
     It is the ONLY exit from the `traceability` gate: that gate takes no row in
     `spec/changes/EXEMPTIONS.md`, because the exit is here, in the requirement itself.
     At least 20 characters of reason -- the gate counts them and prints what you wrote --
     and `uat.md` MUST then carry a numbered step for this R-n. It does not replace the
     **Acceptance** block below: a requirement a person checks still says what they see.
**Verified-by:** manual — <why no automated suite can prove this>
-->

1. WHEN <event>, the system SHALL <reaction>.
2. IF <condition>, THEN the system SHALL <safeguard>.

**Acceptance**
- **R-1.1** GIVEN <context>, WHEN <action>, THEN <observable result>.

### R-2: <area> — **P2**
**Objective:** As a <role>, I want <capability>, so that <benefit>.
**Why this priority:** <…>
**Independent test:** <…>

1. WHEN <event>, the system SHALL <reaction>.

**Acceptance**
- **R-2.1** GIVEN <context>, WHEN <action>, THEN <observable result>.

## Edge cases

### Defects that have already happened once
| Source | What it was | Can this change bring it back? | Evidence |
|---|---|---|---|
| <invariant / incident in the spec> | <description> | <yes/no> | <path or quotation> |

### Attacks
- **E-1 — <category: empty, boundary, concurrent, permissions, malformed, partial, repeated, slow-network / offline>:**
  <what exactly happens> — it costs: <business effect> — the requirements say: <R-n / they do not>

### Races
- **W-1 — <who collides with whom>:** read-then-write: <which sequence>; what the database
  holds at that moment: <state>

### With no defined behaviour
- <the gap, as a question — not an answer>

## Impact analysis

- **Collisions with invariants:** <D-xx — what would have to bend — `critical`; or "none">
- **Decisions that already settle this:** <ADR-nnnn (alias) — what it settled — consistent /
  departs from it: requires an ADR with `supersedes`>
- **Dependencies:** <what this change needs — exists / does not exist; a dependency on
  something unbuilt blocks (the `§ Unbuilt` sections in `spec/contexts/`)>
- **Frozen rules:** <`BR-xx` / `P-xx` (in the context document) — consistent / departs from it: "requires an ADR with `supersedes`">
- **Tests that would fail:** <`<test file>::<test name>` / `<black-box file>` — what it nails down today>
- **Other changes in flight:** <CR-... touching the same documents, or "none">

## Non-Goals
- <what this change does not do> — <why and who decided so>

## Bounds
| Quantity | Value | Where it comes from |
|---|---|---|
| <quantity> | <number> | <source> |

## Open questions
- <question> — blocks <what>

## Self-check
<an attack on your own document along five dimensions (completeness, contradiction,
observability, bounds, collisions) — every item is one sentence with a question mark and what
changes the answer; ≤25 items. The section is mandatory and checked by verify.py:
a heading with no content is not an attack.>

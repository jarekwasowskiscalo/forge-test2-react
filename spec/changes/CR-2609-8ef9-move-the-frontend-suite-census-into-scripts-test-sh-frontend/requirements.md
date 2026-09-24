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

| Id | Criterion | How measured |
|---|---|---|
| **SC-1** | <an observable effect for a human or for the data> | <who/what checks it> |

## Requirements

Stories ordered by **priority**, each **independently testable**. Priority is not a label of
importance — it is the answer to "if we ship only one, does it still make sense". Without
that order the scope cannot be trimmed under pressure, because nothing says what is the core
and what is an addition, and trimming ends with removing something that held the rest up.

### R-1: <area> — **P1**
**Objective:** As a <role>, I want <capability>, so that <benefit>.
**Why this priority:** <what happens if it is absent; P1 = without it the change makes no sense>
**Independent test:** <how to check this alone, without R-2 and the rest>

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
- **E-1 — <category: empty / boundary / concurrent / permissions / malformed / partial / repeated>:**
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
- **Tests that would fail:** <`tests/...::test_...` / `e2e/...feature` — what it nails down today>
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

---
id: ADR-NNNN
title: <one line, present tense, stating the decision — not the topic>
status: Proposed          # Proposed | Accepted | Superseded
date: YYYY-MM-DD          # the day it was taken, never the day it was written down
cr: CR-YYMM-xxxx          # the change that took it; `historical` for a recovered decision
supersedes: []            # the identifiers it overrides, frozen rules such as BR-14 included
superseded_by: null       # set by a LATER ADR, never by this one
aliases: []               # earlier names of this decision, still cited from the code
---

# ADR-NNNN — <title>

## Context

What was true when this came up, and what forced the choice. Give the constraint, not the
solution. If there was an incident, name it: what broke, where and what it cost. A reader two
years from now has to know whether the constraint still holds, and cannot judge that from the
decision alone.

## Decision

One paragraph, present tense, imperative where it binds. This is the sentence that also
appears — normatively and without justification — in the appropriate document under
`spec/design/` or `spec/contexts/`.

## Rejected alternatives

Each together with the reason it lost.

A rejected alternative is necessary and **not sufficient**. An ADR is also cross-cutting —
reversing it touches more than one module, layer or suite — and expensive to reverse: undoing
it requires a data migration, a rewritten contract or a change in CI, not an edit to one
file. A decision that fails either of those two conditions has an address and this is not it:
a fact always true about the data goes to `contracts/invariants/`, a deliberate non-goal to
`spec/invariants.md`, a placement rule to `spec/design/conventions.md`, a choice of suite or
fixture to `spec/design/testing.md`, a column to `spec/design/data-model.md`, a contract
field to `spec/design/api.md`. The justification:
`spec/design/conventions.md` § When a decision is an ADR.

- **<alternative>** — <why not>.

## Consequences

What it costs, what it closes off and what now has to be true elsewhere for it to hold. Name
the check that enforces it — a test, a gate, a constraint — because a consequence nothing
enforces is a hope.

## Enforced by

`<path to the test, gate or constraint>` — <what it would catch>.

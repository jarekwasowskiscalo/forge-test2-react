---
context: <context-slug>
classification: <core|supporting|generic>
owns: [<table_name>]
neighbours: []
processes: [P-NN]
screens: [spec/design/ui/<screen>.md]
features: [<the black-box files this context owns, by the path this stack uses>]
---

# <Context name>

One paragraph: what this context is responsible for, in the words the business uses. Not
what it stores and not which endpoints it has — those have their own homes
(`spec/design/data-model.md`, `spec/design/api.md`). This document is the rules.

**The front matter is read, not decorative.** This stack's context-declaration fitness test
resolves every key in it: `owns` against what `spec/design/data-model.md` declares,
`screens` and `features` against files on disk, `neighbours` against the contexts that
exist. It takes flat scalars and inline lists only — the grammar in
the engine's `frontmatter.py`, which is the one reader.

## Strategic classification

`core`, `supporting` or `generic`, and one sentence saying which and why. It decides how
much this context is worth: **core** is what the product competes on and where the modelling
effort goes, **supporting** is specific to this business but not a differentiator, and
**generic** is something you would buy if a vendor sold it. A context classified `generic`
that nevertheless carries elaborate rules is either misclassified or building something
somebody else already sells.

## Language

The words that mean something **here**, with the source form that is the identifier in the
code. A word whose meaning is the same across the whole system belongs in
[`spec/glossary.md`](../../spec/glossary.md) instead; a word that means one thing here and
another thing next door belongs in this table, and that difference is the entire reason the
boundary exists.

| Term | What it means here |
|---|---|
| **<Term>** | |

## Neighbours

One row per context this one borders on, and every row carries a **classified pattern**
rather than a direction. A boundary described only by an arrow says who calls whom; it does
not say what happens when the other side changes, and that is the only question a boundary
has to answer.

The front-matter grammar is `<context>:<role>:<pattern>`, where `role` says what the
neighbour is **relative to this context**:

| Role | Meaning | Patterns this context may take |
|---|---|---|
| `upstream` | they supply, we consume | `acl`, `conformist`, `customer-supplier` |
| `downstream` | we supply, they consume | `open-host-service`, `published-language`, `customer-supplier` |
| `peer` | neither supplies the other | `shared-kernel`, `separate-ways` |

The role/pattern pairing is not a convention. `open-host-service` and `published-language`
are things an **upstream** publishes; `acl` and `conformist` are the two answers a
**downstream** can give, and they are the opposite answers — an anti-corruption layer
translates the other model into this one, a conformist adopts it whole. Writing both against
one neighbour means the boundary has not been decided. The fitness function refuses every
pairing this table does not list.

| Neighbour | Role | Pattern | What crosses, and what happens when they change it |
|---|---|---|---|

A context with no neighbours writes `neighbours: []` and says so below the table, so that
the emptiness reads as a boundary nobody has needed yet rather than a section somebody forgot.

## `P-NN` — <the flow>

The flows this context owns, in business language, numbered in the `P-xx` space this
document is the home of ([`spec/glossary.md`](../../spec/glossary.md) § Identifiers and
their spaces). Each step is something a person or another system does, and something this
context does in reply.

## Business rules

Each rule with its own `BR-nn`, stated so it can be failed. A rule the database can hold is
a constraint before it is a sentence (the constitution, article VI) — say which constraint
holds it, or say that none does and why.

## Deliberate non-goals

What this context does **not** do, so that the absence reads as a decision rather than a gap
somebody will close by accident. A non-goal that binds the whole system belongs in
[`spec/invariants.md`](../../spec/invariants.md) instead; this section is for what is
deliberately out of scope **here**.

## Open questions

What is genuinely undecided, each with who has to decide it. An open question written down
is a question somebody can answer; the same question left in a head is the thing the next
change improvises about (the constitution, article VII).

Delete this section when it empties — an empty heading reads as "nothing is open", which is a
claim, and this document should not make claims nobody checked.

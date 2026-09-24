# `spec/` — what the system is, and why

This directory is the system's description of itself. It is normative: when `spec/` and the
code contradict each other, one of the two is a defect, and which one is answered by the
change process. It is never a divergence anybody may leave standing.

Two kinds of document live here, and mixing them is the failure this arrangement exists to
prevent:

- **`spec/design/**` and `spec/contexts/**` say what holds *now*.** Present tense, no dates,
  no history. Edited whenever a rule changes.
- **`spec/ADR/**` says *why*, once, with a date.** An ADR is never edited after acceptance; a
  later ADR supersedes it — because rewriting a decision in place destroys the reasoning
  behind it, and then nobody can tell a settled decision from an accident. The directory is
  empty today: the template's decisions, taken without a change record, stand as "decision of
  <date>" paragraphs in the normative documents, and the first ADR will come out of the first
  change through `/forge:sdd` ([`design/conventions.md`](design/conventions.md) § When a decision
  is an ADR).

## Where each question is answered

| Question | File |
|---|---|
| What the product is, who uses it, what it is made of | [`design/architecture.md`](design/architecture.md) |
| What the guestbook does — `P-01`, every `BR-xx` | [`contexts/guestbook.md`](contexts/guestbook.md) |
| What we knowingly do not do | [`invariants.md`](invariants.md) |
| What must always be true of the data | [`contracts/invariants/`](../contracts/invariants/README.md) — `D-01`… |
| What holds at the system boundary | [`contracts/`](../contracts/README.md) |
| What a domain word means | [`glossary.md`](glossary.md) |
| How the process works — for people and for agents | [`constitution.md`](constitution.md) |
| Where a file goes, what it is called, what it may import | [`design/conventions.md`](design/conventions.md) |
| Which tables and columns exist | [`design/data-model.md`](design/data-model.md) |
| Which fields an endpoint takes and returns | [`design/api.md`](design/api.md) |
| What each screen is | [`design/ui/`](design/ui/) |
| What proves the system works | [`design/testing.md`](design/testing.md) |
| How it is run, built and released | [`CLAUDE.md`](../CLAUDE.md) |
| Why a decision was taken and what it rejected | [`ADR/index.md`](ADR/index.md) |
| What is changing right now | [`changes/INDEX.md`](changes/INDEX.md) |

`spec/` is cut **by domain**: a business rule or a flow lives in its context's document, a
contract field in `api.md`, a column in `data-model.md`. One fact, one home — a context
document never lists columns, and a register never argues a rule.

**`spec/contexts/` is the registry, and it is read rather than admired.** Each document's
front matter declares what its context owns, whom it borders on and with which pattern,
which screens and which feature files belong to it —
[`../.specconf/templates/system/context.md`](../.specconf/templates/system/context.md) is
the shape. `tests/fitness/test_context_declarations.py` resolves every one of those claims
against the tree and refuses two failures in particular: a screen or a feature file claimed
by **no** context, which is a surface nobody owns, and one claimed by **two**, which is a
boundary drawn in two places. That is what makes a context something a person or a team can
be given, rather than a heading in a document.

Document templates live in `.specconf/templates/{change,system}/`, editable per project.

## This directory describes a template

The only domain context is the **guestbook**, and it is deliberately trivial: four operations,
one table, one screen. It exists so that every document here has content that shows its shape
— and so that it can be deleted when the first real feature replaces it.

Deleting the example deletes with it: `contexts/guestbook.md`, `design/ui/guestbook.md`, the
entries in `design/api.md` and `design/data-model.md`, the contracts
`contracts/openapi/guestbook.yaml` and `contracts/invariants/guestbook.md`, both halves
of the corpus `golden-set/`, the mock-up `rationale/mockup-guestbook/`, the black box
`e2e/suite/features/guestbook.feature` with the steps that bind it, the user guide
`docs/user-guide.md` and the request file `http/guestbook-entries.http`. The rest of this
tree describes the process and stays.

## Identifier spaces

`P-xx` and `BR-xx` resolve in the context document that owns them, under
[`contexts/`](contexts/), beside the rule they name. `S-xx` in the front matter of
[`design/ui/`](design/ui/). `D-xx` in
[`../contracts/invariants/`](../contracts/invariants/README.md). `ADR-xxxx` in [`ADR/`](ADR/).
The full table: [`glossary.md`](glossary.md) § Identifiers.

A departure from a rule that carries an identifier is an ADR with `supersedes:
[<identifier>]` in its front matter — so "which rules have been overridden" stays one grep
over the index.

## How this tree changes

Never on its own and never after the fact. Every edit under `spec/` arrives on a change
branch, in the same pull request as the code it describes, declared line by line in that
change's `delta.md`. The rule is mechanical rather than customary — see
[`constitution.md`](constitution.md) article IV and the `specs` job in
[`.github/workflows/ci.yml`](../.github/workflows/ci.yml).

**One exception, and it is the commit that created the template.** Resetting the repository to
its starting state is not a change of product behaviour and has no change record. The first
real change after it already goes through `/forge:sdd` — and that one is the test of whether this
template works.

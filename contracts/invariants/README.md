# Data invariants

**Contracts:** `guestbook.md` — `D-01`…`D-03`, each with a witness and a kind of evidence.

An invariant is a sentence true of **all** the data the system will ever see — not of the
cases somebody thought of. That is what separates it from the reference corpus in
`golden-set/fixtures/`, which proves the known cases, and it is the reason neither replaces
the other. It is further still from `golden-set/seed/`, which proves nothing at all and is
not meant to: that half is what a new environment opens with.

Invariants are a boundary in the same way the HTTP contract is: they are what may be relied
on without looking inside. That is why they live here rather than in `spec/`.

## Format

One file per domain. Each invariant is a section with an identifier in the heading, a body —
and **two lines without which the entry is incomplete**:

```markdown
## `D-xx` — <a sentence true for every input>

<body: what it forbids, which pattern it guards against, what it looks like here and now>

**Witness:** `tests/<group>/test_<subject>.py::<test name>`
**Kind of evidence:** generator | sweeper | database constraint | invocation
```

**`Witness`** names the test that proves this invariant, or — when there is no proof —
`none — <reason>` with a reason of at least forty characters. The form with a reason is
deliberate and has two siblings in this repository: `**Verified-by:** manual — <reason>` in
requirement traceability and `**ADR:** none — <reason>` in a change delta. A gap counted and
written down is a different thing from a gap passed over in silence, and a document claiming
coverage it does not have is worse than a document admitting a gap: the first one stops
anybody from checking.

**`Kind of evidence`** exists because without it a witness with the right name and an empty
body looks exactly like a real one. The distinction that cost the most:

- a **generator** proves a rule about a **value** — "every primary key is a UUID" is
  sensible to randomise, because the space of values is what the rule is about;
- a **sweeper** proves a rule about **shape** — "an entity has one row for its whole
  lifecycle" is a sentence about the schema rather than about data, so a generator has
  nothing to draw for it. A property-based test put behind a rule about shape **always
  passes, says nothing, and looks like the strongest test in the suite while doing it**.

A sweeper walks the metadata and sees the **next** table, not the one table the author
remembered. A sweeper that is vacuously true — because the domain has one entity today — is
fine, and has to say so about itself in the body of the test.

## Identifiers

`D-xx` are **load-bearing**: never renamed, never reused. A superseded invariant keeps its
heading and gains a "Superseded by" line together with one sentence about what it guarded —
a hole in the numbering is information only when what was in it can still be read.

Rules common to every boundary: [`contracts/README.md`](../README.md).

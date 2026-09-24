---
contract: invariants
domain: guestbook
version: 2
---

# Data invariants — guestbook

Things that must always be true of this domain's data. An invariant has no date and no
rejected alternative — if it had one it would be a decision and would belong in
[`spec/ADR/`](../../spec/ADR/index.md).

**This contract's version rises when the body of any invariant changes.** The identifiers are
load-bearing: never renamed, never reused. A superseded invariant keeps its heading and gains
a "Superseded by" line together with one sentence about what it guarded — a hole in the
numbering is information only when what was in it can still be read.

**Every entry carries a witness and a kind of evidence, and is not complete without both.**
Until recently this document lived in `spec/invariants.md`, where it admitted outright that
`D-01`…`D-03` were held "by the data model and by a decision about identifiers, rather than
by a test that names them". That is no longer true, which is why the paragraph left along
with the move — but it did not leave without a replacement: two lines under every entry, whose
empty value is visible.

Rules common to every boundary, and the format of those two lines:
[`contracts/README.md`](../README.md) and [`contracts/invariants/README.md`](README.md).

---

## `D-01` — a record is one record for its whole lifecycle

A domain entity has **one** row from creation to end. A change of state is an edit of that row
or a separate event pointing at it — never a copy into a second table.

The pattern this guards against is called the "archive sheet": a record moved into a second
set once it closes, after which the question "what happened to it" requires stitching two
sources together and every read has to remember both. History is destroyed then not by
deletion but by separation.

In the guestbook this invariant is trivially satisfied, and that is how it should be:
`guestbook_entries` has no archive table, and deleting is deleting (`BR-03`), not moving.

**Witness:** `tests/fitness/test_data_invariants.py::test_no_table_is_shaped_like_an_archive`
**Kind of evidence:** sweeper — a rule about the shape of the schema, not about a value.
Vacuously true today (one table) and the test says so; it is worth having for the NEXT table,
which is why it carries a known positive over synthetic metadata.

## `D-02` — a relation replaces a copied column

A fact belonging to another entity is **pointed at**, not transcribed. A column copied from a
neighbouring table is a copy that will diverge on the first change to the original — and will
diverge silently, because nothing compares a copy against its source.

The exception is a **deliberate historical snapshot**: a value stored in order to show what
was true at the time. A snapshot has to be named as one in
[`spec/design/data-model.md`](../../spec/design/data-model.md), because a snapshot
indistinguishable from a copy is a copy.

**Witness:** `tests/fitness/test_data_invariants.py::test_no_column_is_a_copy_of_another_tables_column`
**Kind of evidence:** sweeper — a pair of tables sharing a column name and type with no key
between them. The test also holds the named exception: as long as no snapshot is declared the
sweeper is absolute, and the first declaration forces somebody to teach it to read that
declaration, rather than letting the exception grow quietly.

## `D-03` — a technical identifier is a UUID

Every primary key is a UUID generated on the application side. Never a number from a sequence:
a sequence counts (the address gives away how many records there are), can be walked in a
loop, and needs the database before an identifier can exist at all.

A natural key, if the feature has one, is a **separate column with its own uniqueness
constraint** and never replaces the primary key: a natural key gets corrected, a primary key
never does.

The decision and its rejected alternatives are carried by
[`spec/design/data-model.md`](../../spec/design/data-model.md) § Identifiers.

**Witness:** `tests/fitness/test_data_invariants.py::test_every_primary_key_is_an_application_generated_uuid` and `tests/unit/test_data_invariant_properties.py::test_any_identifier_survives_the_round_trip_to_storage`
**Kind of evidence:** two, because this invariant has two halves. The sweeper answers "is every
primary key DECLARED that way" — a question about shape, about every future table. The
generator answers "does an identifier from the whole space survive the trip to storage and
back" — a question about a value, and the only place in this document where a property-based
test really buys something.

## `D-04` — a stored text value is normalized, and its bound is in code points

Every `author` and `message` in the table is in **Unicode NFC**, carries no member of the
written trim set at either end, and is between 1 and its bound **code points** long. The bound
counts code points and not characters-as-a-person-sees-them and not UTF-16 code units, and the
unit is part of the invariant rather than an implementation detail of whoever measured last.

It has to be stated because the number alone could not carry it. `AUTHOR_MAX_LENGTH` is 80 in
the column, 80 in the Pydantic schema, 80 in the published contract and 80 in the browser, and
a fitness test held all four equal — while the browser measured UTF-16 code units and the other
three measured code points. Four literals agreed and two of them meant different strings, so a
signature of 41 emoji was refused by the screen and stored by the API with a 201. A unit cannot
be checked against a number; it can only be checked against data, which is what the witness
below does from both sides at once.

Normalization is the half that makes the bound honest to a person: without it the same eighty
letters are accepted or refused depending on nothing but whether the keyboard emitted `e` +
U+0301 or a single U+00E9.

**Rows written before 2026-09-17 are not covered**, and that is a stated limit rather than an
oversight: nothing normalized on write until then, and no backfill was run, so a decomposed
value may still sit in the table and a phrase typed precomposed will not find it. The invariant
is true of every write from that date. A deployment holding data it depends on closes the gap
with one `UPDATE`; this template holds none.

**Witness:** `tests/integration/test_guestbook_entries_service.py::test_a_stored_value_is_normalized_and_within_the_bound_in_code_points` and `tests/unit/test_entry_text_rules.py::test_every_case_gets_the_verdict_the_corpus_states`
**Kind of evidence:** two, because the invariant has two halves and one suite cannot see both.
The round trip answers "is what reached the column the normalized value" — a question about a
value, and only a real database can answer it. The corpus answers "does the rule say the same
thing here as it says in the browser" — a question about agreement, which is why the same file
is read by `frontend/src/contexts/guestbook/lib/entryText.test.ts` and why neither half is
sufficient alone.

# Data model

Tables, columns and constraints. The rules behind them are in
[`spec/contexts/guestbook.md`](../contexts/guestbook.md); the shapes on the wire are in
[`api.md`](api.md). This document never argues a rule — it states a column and a type. Two
cross-cutting decisions that bind it are recorded below together with their rejected
alternatives, because they have no other home.

## Owner of the schema

**The `alembic/versions/` directory is the sole owner of the schema.** Every schema change is
a revision with a working `upgrade` and a working `downgrade`. `create_all()` is called
nowhere: not in the application, not in a fixture, not in a script. The database is created
and migrated by `./scripts/db.sh migrate`; tests that need a fresh database get one through a
migration — so the suite proves the same path production takes. Every change to this document
is a revision, and the other way round.

The reason: `create_all()` creates what is missing and **does not touch what is there**. A
column added to a model does not appear in an existing table, a `NOT NULL` from the model does
not reach the database — the application starts, the tests pass on a fresh database and break
on somebody else's. Without revisions there is also no answer to "which schema version is this
database on", and no way back.

Rejected (decision of 2026-08-30):

- **`create_all()` at application start** — works only on an empty database and is silent on a
  non-empty one; a column change surfaces at random, on somebody else's machine, later.
- **`create_all()` in tests, migrations in production** — the suite stops proving the
  migration, so the migration is the one untested part of a release.
- **Autogeneration without review** — `./scripts/db.sh revision` is a first draft, not an
  answer: it does not see data changes, it confuses a type change with a drop/add pair, and it
  can generate a `downgrade` that loses a column. A revision is read before it is committed.

Consequences: every model change costs a revision; `downgrade` has to work rather than merely
exist; the production image does **not** migrate at start — the migration is an explicit step
of a release ([`architecture.md`](architecture.md) § Deployment). This is enforced by
`tests/integration/test_migrations.py`: it compares columns **for equality** against the
specification, walks a full cycle down and up, and checks idempotence.

### What Alembic sees, after the tree was cut by context

`Base` lives in [`../../app/db/base.py`](../../app/db/base.py), and every model registers on it
by being imported. **Importing `app.contexts` imports every context**, which is what fills
`Base.metadata` before autogeneration reads it — `alembic/env.py` does exactly that and nothing
more.

Rejected (decision of 2026-09-07, `cr: historical` — the models moved under
`app/contexts/<name>/models/` when the tree was recut, and who owns the metadata Alembic reads
is a fact about the schema, so it is recorded here; the recut was done on the trunk and carries
no `delta.md` in which to declare the edit. The recut itself, and its alternatives:
[`architecture.md`](architecture.md) § What a new feature adds):

- **Leave `Base` with the models.** It sat in the models package, which was true while there
  was one such package. With one per context it would have to live in somebody's context and be
  imported by every other — a shared thing filed under one owner's name, which is the same
  mistake as putting `app/core/` under `app/platform/`.
- **Let `alembic/env.py` walk the context directories itself.** It would need no aggregate. It
  would also be a second implementation of "which contexts exist", and the one that runs least
  often — a migration is generated on the days somebody changes the schema, so a walk that
  quietly found nothing would be discovered by an empty autogeneration diff that reads exactly
  like "no schema change".
- **Import each context's models directly in `alembic/env.py`.** Explicit, and it puts a list
  of contexts in a second file that nothing checks. `app/contexts/__init__.py` is the one list,
  and `tests/fitness/test_context_boundaries.py` holds it against the directories on disk.

## Identifiers

**Every primary key is a UUID generated on the application side** (`default=uuid.uuid4` on a
`Uuid` column, natively `uuid` in Postgres). A natural key — where a feature has one — is a
separate column with its own uniqueness constraint and never replaces the primary key,
because a natural key gets corrected and a primary key never does. As a data invariant the
rule carries the identifier `D-03` in
[`contracts/invariants/guestbook.md`](../../contracts/invariants/guestbook.md).

The reason: a number from a sequence **counts** (`/api/things/842` says how many there are),
**can be guessed** (every future authorisation bug becomes enumerable in a loop) and
**needs the database in order to exist** (an identifier known only after `INSERT` forces a
round trip where none was needed).

Rejected (decision of 2026-08-30):

- **`Integer` with autoincrement** — the three properties above; reversing it later is a
  migration of every table and every foreign key at once.
- **A UUID generated by the database (`gen_random_uuid()`)** — ties the schema to an extension
  and takes away the most valuable thing a UUID gives: an identifier known **before** the write.
- **ULID / time-sortable identifiers** — they need a dependency and a column type of their own,
  while ordering in this project is settled by a time column with a tie-break on `id`, which
  gives a total order without a new format.

Consequences: addresses are longer and unreadable to a human — a feature that needs a
reference a person can say over the phone adds a separate column for it.

## `guestbook_entries`

The only table. No relations, no foreign keys, no lookup tables.

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | `Uuid` | no | primary key, `default=uuid.uuid4` — issued by the application, known **before** the write (§ Identifiers) |
| `author` | `String(80)` | no | the guest's signature; the length is the same number the contract states |
| `message` | `Text` | no | the body of the entry; **`Text`, not `String(1000)`** — see below |
| `created_at` | `DateTime(timezone=True)` | no | when it was written; set once (`BR-02`) |
| `updated_at` | `DateTime(timezone=True)` | no | when it was last amended; equal to `created_at` on an entry never amended |

**Why `Text` rather than `String(1000)`.** The ceiling on message length is a product rule and
it will move. As `Text`, moving it is an edit to one Pydantic schema; as `String(1000)` it is a
migration rewriting a column type. The signature stays `String(80)`, because its length is a
display constraint rather than an editorial one, and it does not move.

**`String(80)` is a Postgres `varchar(80)`, and Postgres counts CODE POINTS in it.** That one
fact settles an argument that would otherwise keep reopening. "Eighty characters" invites the
reading a person actually has — eighty things you can see, which Unicode calls grapheme
clusters — and that reading is unreachable from here: eighty graphemes of family emoji is up
to four hundred code points, so the application would accept a signature the column then
refused. The bound is in code points because the column already is, the published
`maxLength` already is (JSON Schema defines it that way), and Pydantic already is. Only the
browser was not, and the repair moved the browser.

Values are normalized to Unicode NFC before they are measured or stored, which is what keeps
the column's count and the application's count the same number for a decomposed letter.

Rejected (decision of 2026-09-17, `cr: historical` — normalization on write was introduced on
GitHub issue #28, outside `/forge:sdd`):

- **Backfill the existing rows with a data migration.** It would make the invariant true of the
  whole table rather than of writes from today, and it is an irreversible rewrite of a column
  with no downgrade, run against a complaint nobody has made. The guestbook is this template's
  worked example and no deployment holds data anybody depends on; a deployment that does closes
  the gap with one `UPDATE` and knows its own data well enough to decide.
- **Widen `author` to `String(160)` so a decomposed value fits without normalizing.** It treats
  the symptom, doubles a display constraint for a reason no reader could infer from the number,
  and still leaves the same eighty letters accepted or refused by which key the guest pressed.
[`../contexts/guestbook.md`](../contexts/guestbook.md) § `BR-01` carries the rule;
`contracts/invariants/guestbook.md` § `D-04` carries it as an invariant and names what proves
it. Rows written before 2026-09-17 were not rewritten — no migration backfilled them, and that
is recorded rather than assumed.

**Why two time columns rather than one.** `BR-02`: "when this was written" has to survive every
later amendment. One column cannot answer both questions at once.

**Why both with a timezone.** "Which entry is newer" has to settle correctly across an offset
change. A naive column makes the answer depend on the server's local time, and the failure is
silent: sorting is correct right up to the day the clocks go back.

The constants `AUTHOR_MAX_LENGTH` and `MESSAGE_MAX_LENGTH` live beside the model
(`app/contexts/guestbook/models/guestbook_entry.py`) and are imported by the schemas. One number, one place: a
value reaching the database by another route — a backfill in a migration, a fixture, a script —
is bound by the same limit. **The routes are three and all three are named**: a migration under
`alembic/versions/`, the fixture half of the corpus (`golden-set/fixtures/`), and the
environment seeder over the seed half (`golden-set/seed/`, through the HTTP API —
[`architecture.md`](architecture.md) § What a new environment starts with). The last of those
is bound twice over, because it posts rather than inserts: it cannot plant a value the
application itself would refuse.

**One named exception:** the browser does not import Python, so
`frontend/src/contexts/guestbook/lib/guestbookEntry.ts` carries the same numbers as copies —
the two lengths, the largest page the list may ask for, and the longest search phrase. The
copies are legal only because `tests/fitness/test_length_constants.py` holds them: each
TypeScript literal must equal the literal beside the model, or the screen rejects an entry the
database would have accepted, or the other way round.

**Equal literals were not enough, and the gap is worth keeping written down.** That fitness
test compares `80` with `80` and cannot compare what the two sides count with it. For the whole
life of this repository the browser measured UTF-16 code units and every other layer measured
code points, so all four literals agreed and two of them meant different strings — a signature
of 41 emoji was refused by the screen and stored by the API with a `201`, with a green suite on
both sides. The second binding is `golden-set/fixtures/text-measurement.json`: one corpus, read
by `tests/unit/test_entry_text_rules.py` and by the browser's own suite, asserting the same
verdicts and the same lengths. A number can only be checked against a number; a unit has to be
checked against data.

Rejected (decision of 2026-09-05, `cr: historical` — taken on the trunk with the golden-set
split, so it is recorded here; [`conventions.md`](conventions.md) § When a decision is an ADR):

- **Leaving the third route unnamed.** The sentence above already admitted "a fixture, a
  script" and named neither, so the one route that reaches a DEPLOYED database was the one no
  document pointed at.
- **Seeding from an Alembic revision.** `alembic/versions/` owns the schema and only the
  schema (§ Owner of the schema); data in a revision rides into every environment that runs
  it, production included, and cannot be declined there.

## Indexes and uniqueness

| Index | Columns | Unique | What for |
|---|---|---|---|
| `ix_guestbook_entries_created_at_id` | `created_at`, `id` | no | the order the contract publishes (`BR-04`) |

There is no uniqueness constraint at all: two guests with the same signature and the same
message are two entries, not an error.

`id` is in the index for the same reason it is in the `ORDER BY` — it is what makes the order
**total**. Without it two entries sharing an instant come back in whatever order the planner
chooses: stable in a test and unstable under paged reads, where it shows one entry twice and
loses another.

An order promised by the contract with no index behind it means a full sort of the table every
time the only screen is opened — invisible while the table is small.

The index is declared **twice, deliberately**: in the revision that creates it, and in the
model (`__table_args__`), because autogeneration compares the database against `Base.metadata`
— an index the model does not know about is, to it, an index to drop in the next revision.

**Phrase search (`BR-05`) has no index, and that is a decision rather than a gap.** Narrowing by
`q` is `ILIKE '%phrase%'` over `author` and `message` joined by `OR`, and no B-tree index
serves a query with a leading wildcard; it would take `pg_trgm` and a GIN index on both
columns. The guestbook is small — one screen, a few hundred entries — so a sequential scan of
two columns costs less than maintaining an extension and two indexes that grow with every
entry. The decision returns to the table when the table passes **10,000 entries**, or when `q`
becomes a query called more often than the screen is opened; the change is then a revision with
`CREATE EXTENSION pg_trgm` and GIN indexes, declared here as `backward compatible`.

## Migrations

| Revision | Parent | What it does |
|---|---|---|
| `a1b2c3d4e5f6` | — | creates `guestbook_entries` and the ordering index |

One revision, and it is the head. Every next one declares as its parent the head **at the time
of implementation**, never the one the author remembered.

`downgrade` drops the index before the table. The order is not cosmetic: some engines refuse
`DROP COLUMN` on an indexed column, and a revision with the order reversed passes on the way up
and breaks only on the way back — at an operator's machine, in the middle of a release.

**A released revision is not edited** — not its `upgrade`, not its `downgrade`, not its
identifier. The prose in it (docstring, comment) may be corrected, because Alembic does not
execute it and the database never sees it; the DDL never, because a database that has already
applied that revision will not learn about the correction.

### Compatibility mode

**The set of revisions in `alembic/versions/` IS the schema contract** — versioned by revision
id, ordered, released once and never edited after release (§ Owner of the schema; the rule
about boundaries: [`contracts/README.md`](../../contracts/README.md)). That is why there is no
directory for SQL under `contracts/`: a second home would carry either a copy that diverges on
the first change, or a pointer, which is not a contract.

A contract with no declared mode does not say whether it may be deployed before the code or
after — and that is a question answered at three in the morning. **Every schema change declares
one of three values here**, and for the last two also its deployment order relative to the
code:

| Mode | What it means |
|---|---|
| `backward compatible` | old code works against the new schema. A new nullable column, a new table, a new index. Deploy in any order |
| `expand-contract` | two revisions with code between them: expand first, then the code, then contract. The only safe route for a rename and for narrowing a type |
| `breaking` | old code does not work against the new schema. Requires a window, an order written down explicitly, and an entry in `delta.md` |

**History:** `a1b2c3d4e5f6` — the initial one, creating the schema from nothing. The mode does
not apply here: there is nothing to break, because there is no previous state.

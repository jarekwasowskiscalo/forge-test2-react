# Data model

Tables, columns and constraints. The rules behind them are in the document of the context that
owns each table — [`spec/contexts/guestbook.md`](../contexts/guestbook.md) and
[`spec/contexts/todo_list.md`](../contexts/todo_list.md); the shapes on the wire are in
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

One of two tables, and unrelated to the other (§ `todo_tasks`). No relations, no foreign keys,
no lookup tables.

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

## `todo_tasks`

One row per task on the to-do list, the one list every visitor shares
([`spec/contexts/todo_list.md`](../contexts/todo_list.md)). A task is a text, a state and a
moment of adding; the table holds those three and the identifier, and nothing else. The model is
`TodoTask`, in `app.contexts.todo_list.models.todo_task`.

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | `Uuid` | no | primary key, `default=uuid.uuid4` — issued by the application, known **before** the write (§ Identifiers) |
| `text` | `String(200)` | no | the task's one line, stored as the shared text rule leaves it — NFC, trimmed at both ends, 1 to 200 code points, no line break inside (`BR-06`, `BR-07`); the length is `TODO_TASK_TEXT_MAX_LENGTH`, below |
| `done` | `Boolean` | no | the one state: `true` is done, `false` is not done. Written `false` on every insert whatever the request claims (`BR-08`), and afterwards only by a marking, which writes the state the person chose (`BR-09`). `default=False` on the model; no server default |
| `created_at` | `DateTime(timezone=True)` | no | the moment of adding: set once, by the service from its clock, when the task is stored, and never assigned again — not by a marking, not by a correction (`BR-08`, `BR-10`). The list is ordered by it (`BR-11`) |

Every `text` in this table is NFC, trimmed at both ends, 1 to 200 code points and one line: a
data invariant of the to-do list's own under `contracts/invariants/`, the counterpart of `D-04`,
whose witnesses [`testing.md`](testing.md) § CR-2609-823a, the to-do list names.

**Relations: none.** The to-do list is not a row. There is exactly one list, so every row of
`todo_tasks` is on it: a `todo_lists` table would hold one row for ever, and a `list_id` column
would carry the same value in every row. No foreign key leaves this table and none arrives at it.
It points at nothing in `guestbook_entries` and copies no value from it (`D-02`) — the two
contexts share a rule about text, never a record
([`spec/contexts/todo_list.md`](../contexts/todo_list.md) § Neighbours).

**What is deliberately not a column:**

- **No `updated_at`.** A task has no moment of amendment and no "edited" fact; those are an
  entry's (`BR-02`). Nothing reads when a task last changed, and the list is never ordered by it:
  "newest" is the moment of adding (`BR-11`).
- **No `deleted_at`.** Deletion is a `DELETE` of the row, with no bin and no undo (`BR-13`), and a
  done task stays the same row in the same place (`D-01`).
- **No position.** The moment of adding is the only thing that orders the list; nothing reorders
  it by hand or by state.
- **Nobody.** No author, owner or "done by": the system records nobody
  ([`spec/invariants.md`](../invariants.md) § Deliberate non-goals).

**Why `String(200)`, when the message is `Text`.** The task's bound is a product rule like the
message's, and it could move. The column holds it anyway, for two reasons the message does not
have. A task is one line on a list, so its bound is nearer the signature's display constraint than
a message's editorial one. And the column is the last layer's refusal of a value that arrives by
a route that skipped the rule — a fixture, a script, a service that measured before it
normalized, where two hundred decomposed letters are four hundred code points. Moving the bound
is then a revision that widens the column as well as an edit to the constant; because the model
declares the column from the constant, `tests/integration/test_migrations.py` turns red on the
day the constant moves without that revision, rather than a write failing in production. A
Postgres `varchar` counts code points (§ `guestbook_entries`), so the column and the rule measure
the same thing.

Rejected:

- **`Text`, with the bound in the schemas alone, as the message has it.** Moving the bound would
  be an edit to one file; the price is a column that stores whatever length a route that skipped
  the rule sends it, and a table whose longest value nobody can read off the schema.
- **`CHECK` constraints for the rest of the rule — an empty text, a line break inside.** That is
  a second copy of the text rule, in SQL, beside the one in `app/platform/schemas/text.py`: the
  trim set is thirty code points and the line breaks seven, and two hand-written copies of a set
  agree only until one of them moves. The length is different in kind — one number, which the
  model already reads from one constant and the model-against-revision comparison already
  watches.

**Why a boolean rather than a status.** `P-02` gives a task one state with two values, switched
freely both ways, and no other; `done` says so in its type.

Rejected:

- **A `status` column over a set of values.** It is the shape that invites a third state the
  rules do not have, and whatever then guarded the values — a `CHECK` or an enum type — would make
  each new one a migration.
- **A nullable `done_at` standing for both the state and when it changed.** Nothing asks when a
  task was ticked, and "not done" would become an absence rather than a value.

**The bound, beside the model.** `TODO_TASK_TEXT_MAX_LENGTH = 200` lives beside `TodoTask`; the
column is declared from it and the service's judgement of a text imports it; the schemas do not
([`conventions.md`](conventions.md) § Layers) — one number, one place, bound on the same
three routes as the guestbook's (§ `guestbook_entries`). The name is qualified because the number
is the to-do list's own (`BR-06`): the guestbook's search phrase is also bounded at 200, by
`QUERY_MAX_LENGTH`, and neither constant is ever read to prove the other. The to-do screen's copy
is legal on the guestbook's terms exactly: `tests/fitness/test_length_constants.py` holds the two
literals equal, and a corpus read by both sides checks the unit, because equal literals were not
enough. The revision declares the literal `200` and never imports the constant: a released
revision must not change when the constant later moves.

**No row arrives with the schema.** Example tasks reach a new environment through the API, as the
guestbook's entries do (§ `guestbook_entries`, the rejected seeding from a revision; the filling
itself is [`architecture.md`](architecture.md) § What a new environment starts with).

### Two writers on one task

`BR-10` asks that a correction and a marking of one task, sent at the same moment, both stick,
and that two changes to the same thing end with the one applied later. No check made before the
write can hold that, and no column is added to hold it. **The store holds it, through the shape
of every write:**

- a **correction** is one statement, `UPDATE todo_tasks SET text = :text WHERE id = :id
  RETURNING …`, naming `text` alone;
- a **marking** is one statement, `UPDATE todo_tasks SET done = :chosen WHERE id = :id
  RETURNING …`, naming `done` alone and carrying the state the person chose — never
  `SET done = NOT done`, and never a value computed from a state read earlier (`BR-09`);
- a **deletion** is one statement, `DELETE FROM todo_tasks WHERE id = :id RETURNING id`.

Whatever shape the contract gives the requests, a write names only the columns the person
changed, each with the value the person sent: a request that carried the whole task back would
be the write-back below, arriving from the browser instead of from the service. No row is read
before any of these statements in the same request. Postgres takes the row's lock for each
`UPDATE` and `DELETE`, and at `READ COMMITTED` — the isolation the session factory leaves in
force — a statement that waited for the lock re-reads the row as the first writer committed it
before it applies its own `SET`. So the column a statement does not name keeps what the other
writer put there, and a column both name ends with the value of the one applied later.
`RETURNING` hands back the row as the statement left it, both columns current.

The read-then-writes it protects:

- **A correction against a marking** — the write-back. Read the task, replace the text, write
  back text *and* state; a marking that stored done between the read and the write is undone by
  the not done the correction read. A correction that names `text` alone carries no state to
  restore.
- **Two markings from screens that are out of date** — the flip. Read the state, store its
  opposite; two people who both chose done end with not done. A marking that writes the chosen
  state has nothing read to go stale.
- **A change against a deletion** — the return of the deleted. Read the task (it is there), the
  deletion removes it, then write. A statement that matches no row changes nothing and creates
  nothing, and no row returned is the "no longer exists" answer for a correction, a marking and a
  second deletion alike (`BR-13`). The write that would bring the task back is an upsert —
  `INSERT … ON CONFLICT`, or the ORM's `merge()`, which inserts on absence — and no path writes
  one.

**What defeats it, and nothing in the schema can refuse:** a write that names both columns with
a value it read, a flip computed in SQL or in Python, or an isolation raised to
`REPEATABLE READ`, where the waiting statement fails with a serialization error instead of
re-reading. A sequential test passes all three exactly as it passes the shape above; only two
writers interleaved on one row, the second waiting on the first's lock, tell them apart.

Rejected:

- **A version column checked on every write** (`… WHERE id = :id AND version = :read`). It
  refuses the second writer instead of keeping both changes — the opposite of `BR-10` — and
  telling a person their change lost is a named non-goal of the context. It would cost a column,
  a refusal in the contract and a screen state, to undo what the rule chose.
- **A locking read** (`SELECT … FOR UPDATE`, then the write). Correct, and one round trip and one
  held lock longer than a statement that needs no read; it holds only while every path remembers
  to take the lock, and the single statement has nothing to remember.
- **The ORM's load, modify and flush.** It writes only the attributes that changed, so it too
  names one column — but it reads the row first, and a deletion landing between that read and the
  flush surfaces as a stale-data error ("0 rows matched") rather than as "no longer exists".

**Filling an empty list is the one rule here the store does not hold.** Example tasks are added
only while the list holds no task ([`architecture.md`](architecture.md) § What a new environment
starts with says when; once added, the context's rules bind them like any task). That is a read
and then posts, over HTTP, and "only while the table is empty" is a statement about the absence
of every row — nothing a key or a unique index can state. The guarantee is the seeder's
own check, and it is weaker by choice: a person adding a task in the seconds between that read
and those posts, or two fillings of one environment at once, leaves the examples beside the task
or twice over. The guestbook's filling has carried the same exposure since it was written.

## Indexes and uniqueness

| Index | Columns | Unique | What for |
|---|---|---|---|
| `ix_guestbook_entries_created_at_id` | `created_at`, `id` | no | the order the contract publishes (`BR-04`) |
| `ix_todo_tasks_created_at_id` | `created_at`, `id` | no | the to-do list's one order, newest first (`BR-11`) |

There is no uniqueness constraint at all: two guests with the same signature and the same
message are two entries, not an error.

`todo_tasks` has none either, and on purpose: the same text twice is two tasks (`BR-12`), so a
unique index on `text` would turn a deliberate duplicate into a refusal. No rule in this schema
says "at most one", so there is no unique constraint and no partial unique index to declare; the
first such rule arrives with its constraint, in its revision and in its model, and a concurrent
insert to prove it ([`testing.md`](testing.md)).

`id` is in the index for the same reason it is in the `ORDER BY` — it is what makes the order
**total**. Without it two entries sharing an instant come back in whatever order the planner
chooses: stable in a test and unstable under paged reads, where it shows one entry twice and
loses another.

An order promised by the contract with no index behind it means a full sort of the table every
time the screen that reads it is opened — invisible while the table is small.

`ix_todo_tasks_created_at_id` serves `ORDER BY created_at DESC, id DESC`: newest first, with
`id` making the order total for two tasks stored in the same instant (`BR-11`). Both keys run in
one direction, so one backward scan of the index answers the query; a tie-break on `id` in the
other direction would be a sort again. The list has no pages, so every read is of the whole
table — while it is small the planner may sort it and pass the index by, and the index is what
lets the read stay a scan rather than a sort as the table grows.

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
| `5c58af1f8e8a` | `a1b2c3d4e5f6` | creates `todo_tasks` and its ordering index |

Two revisions, and the second is the head. Every next one declares as its parent the head **at
the time of implementation**, never the one the author remembered.

`downgrade` drops the index before the table. The order is not cosmetic: some engines refuse
`DROP COLUMN` on an indexed column, and a revision with the order reversed passes on the way up
and breaks only on the way back — at an operator's machine, in the middle of a release.

**A released revision is not edited** — not its `upgrade`, not its `downgrade`, not its
identifier. The prose in it (docstring, comment) may be corrected, because Alembic does not
execute it and the database never sees it; the DDL never, because a database that has already
applied that revision will not learn about the correction.

### The revision that creates `todo_tasks`

`5c58af1f8e8a`, whose parent is `a1b2c3d4e5f6`, the head at the time of implementation.
`upgrade()`, in this order:

1. `op.create_table("todo_tasks", …)` with the four columns of § `todo_tasks` exactly — `id`
   `sa.Uuid()` as the primary key, `text` `sa.String(length=200)`, `done` `sa.Boolean()`,
   `created_at` `sa.DateTime(timezone=True)` — every one `nullable=False`, and none with a server
   default, because the model declares none and the model-against-revision comparison compares
   server defaults too.
2. `op.create_index("ix_todo_tasks_created_at_id", "todo_tasks", ["created_at", "id"])` — a plain
   build: the table was created one step earlier and holds no row, and `CONCURRENTLY` is owed only
   to a table the revision did not create (`tests/fitness/test_migration_safety.py`).

`downgrade()`, in this order — the index before the table, for the reason above:

1. `op.drop_index("ix_todo_tasks_created_at_id", table_name="todo_tasks")`
2. `op.drop_table("todo_tasks")`

What it leaves out, each on purpose: no `lock_timeout` and no `batch_alter_table`, because it
alters no table it did not create and Postgres is the one engine; no backfill, because the table
is new and no column becomes `NOT NULL` over rows that already exist; no data, because example
tasks arrive through the API (§ `todo_tasks`). Its `downgrade` destroys every task — the inverse
of creating the table, and a step no release runs: a rollback moves the alias and leaves the
schema where it is (`./scripts/deploy.sh --help`).

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

`5c58af1f8e8a`, the revision that creates `todo_tasks` — **`backward compatible`**. A new table and an index on
it: the code released before it never names `todo_tasks`, so it runs unchanged over the new
schema, and a rollback that moves the code back while the table stays is safe for the same
reason. The release migrates before it moves the alias ([`architecture.md`](architecture.md)
§ Deployment — two artefacts from one source), which is also the order the to-do routes need;
nothing in it asks for a window or a second revision.

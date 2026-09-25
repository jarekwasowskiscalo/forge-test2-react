# Delta fragment — `design-data`

*The schema half of the to-do list: one new table, `todo_tasks`, owned by the `todo_list`
context that `design-domain` opened (`design/delta/domain.md`), one index, no uniqueness
constraint, and one revision in `backward compatible` mode. The mechanism `BR-10` delegates to
the data model ("the data model names the mechanism that does") is written into
§ `todo_tasks` › Two writers on one task. One file is edited, so there is one entry.*

- MODIFIED `spec/design/data-model.md` — the opening paragraph; § `guestbook_entries` (its first line); § `todo_tasks` (new, with its subsection Two writers on one task); § Indexes and uniqueness (one row, two paragraphs, one phrase); § Migrations (one row, the sentence naming the head, and the new subsection The revision that creates `todo_tasks`); § Compatibility mode (one paragraph after the history)
  **Was:** One table, `guestbook_entries`, called "The only table", with the context rules cited from `spec/contexts/guestbook.md` alone; one index; "One revision, and it is the head"; an unindexed order described as a full sort "every time the only screen is opened"; the compatibility history naming only the initial revision.
  **Now:** A second table, `todo_tasks` — `id` `Uuid` primary key issued by the application, `text` `String(200)`, `done` `Boolean`, `created_at` `DateTime(timezone=True)`, all `NOT NULL`, no server default, no relation to anything — with what is deliberately not a column, why the text is `String(200)` and the state a boolean (each with its rejected alternatives), the constant `TODO_TASK_TEXT_MAX_LENGTH = 200` beside the model, the statement shape through which the store holds `BR-10` (column-scoped single-statement writes under the row lock at `READ COMMITTED`, each naming only the columns the person changed, no read before them, no upsert) with the three read-then-writes it protects, and the one rule the store does not hold (filling an empty list); the index `ix_todo_tasks_created_at_id` on (`created_at`, `id`) serving `ORDER BY created_at DESC, id DESC`; no uniqueness constraint, on purpose (`BR-12`); the revision as ordered `upgrade()` and `downgrade()` operations with its parent the head at the time of implementation; its mode declared `backward compatible`. The guestbook's first line and the intro name two tables and two context documents; "the only screen" became "the screen that reads it".
  **Why:** The to-do list stores something no table holds — a task with a text, a state switched both ways and a moment of adding (`R-1`, `R-3`, `R-4`, `R-6`) — and `spec/contexts/todo_list.md` declares `owns: [todo_tasks]`, which `tests/fitness/test_context_declarations.py::test_every_table_a_context_owns_is_declared_by_the_data_model` refuses until this register carries a `## todo_tasks` heading. The concurrency half is the part that matters most: `R-9` clause 2 and race `W-1` say an edit and a mark on one task must both stick, `BR-10` says "No check made before the write can hold it; the data model names the mechanism that does", and the only update path in the codebase today reads the row first (`app/contexts/guestbook/services/guestbook_entries.py`, `update_entry`). Without a named statement shape two implementers would each pick one, and a whole-row write-back passes every sequential test. No "at most one" rule exists — `BR-12` makes the same text twice two tasks — so the preflight's mechanism (a unique constraint or a partial unique index) has nothing to hold, and the document now says so rather than staying silent. Four existing sentences became false the moment a second table exists ("The only table", the context citation, "One revision, and it is the head", "the only screen"), and each is corrected in the fewest words that make it true again.
  **ADR:** none — five decisions are taken here and none is both cross-cutting and expensive to reverse, so each is recorded with its rejected alternatives in `spec/design/data-model.md`, the home `spec/design/conventions.md` § When a decision is an ADR gives a column, a type and a constraint. (1) `text` is `String(200)`, rejecting `Text` with the bound in the schemas alone and rejecting `CHECK` constraints for the empty text and the line break; reversing it is one revision widening one column. (2) `done` is a boolean, rejecting a `status` column over a set of values and a nullable `done_at`; it follows from `P-02`'s one state with two values. (3) `BR-10` is held by column-scoped single-statement writes, rejecting a version column (it refuses the second writer, which `R-9` and the context's non-goal "Telling a person that somebody else's change replaced theirs" rule out — so the one alternative that would cost a migration and a contract is excluded by the requirements, not by this choice), a locking read and the ORM's load-modify-flush; reversing it is an edit to one service. (4) No uniqueness constraint, which is `BR-12` restated as a schema fact. (5) The filling race is left to the seeder's check, which requirements races `W-5` and `W-6` already accept and the guestbook already carries. The one cross-cutting decision underneath all of this — the to-do list is a context of its own — is the ADR `design/delta/domain.md` marks as required.
  **Requirements:** CR-2609-823a/R-1, CR-2609-823a/R-2, CR-2609-823a/R-3, CR-2609-823a/R-4, CR-2609-823a/R-6, CR-2609-823a/R-7, CR-2609-823a/R-8, CR-2609-823a/R-9, CR-2609-823a/R-11

## Traceability — every table, column, index and operation to its requirement

| What | Where in `spec/design/data-model.md` | Requirements |
|---|---|---|
| table `todo_tasks`, one row per task, no list row | § `todo_tasks` | R-1 (clause 3), R-3 (clause 1) |
| `id` — `Uuid`, primary key, `default=uuid.uuid4` | § `todo_tasks`, the table | R-4, R-6, R-7, R-8 (a task is addressed by it); `D-03` |
| `text` — `String(200)`, `NOT NULL` | § `todo_tasks`, the table and "Why `String(200)`" | R-1 (clause 3), R-2 (clauses 1-3 and 6), R-6 (clauses 1 and 4) |
| `done` — `Boolean`, `NOT NULL`, `false` on every insert | § `todo_tasks`, the table and "Why a boolean" | R-1 (clause 3, R-1.4), R-4 (clauses 1-3), R-6 (clause 2) |
| `created_at` — `DateTime(timezone=True)`, `NOT NULL`, set once | § `todo_tasks`, the table | R-1 (clause 3), R-3 (clauses 2-4), R-6 (clause 2) |
| no `updated_at`, no `deleted_at`, no position, nobody | § `todo_tasks`, "What is deliberately not a column" | R-3 (clauses 2 and 4), R-7 (clause 2); the non-goals of `requirements.md` |
| `TODO_TASK_TEXT_MAX_LENGTH = 200` beside the model | § `todo_tasks`, "The bound, beside the model" | R-2 (clauses 3 and 5) |
| column-scoped correction, chosen-state marking, single-statement deletion, no upsert | § `todo_tasks` › Two writers on one task | R-4 (clause 3), R-6 (clause 2), R-8 (clauses 1-2), R-9 (clauses 1-3); races `W-1`, `W-2`, `W-3` |
| no row in the revision; the filling race left to the seeder | § `todo_tasks`, the last two paragraphs | R-11 (clauses 1 and 4); races `W-5`, `W-6` |
| `ix_todo_tasks_created_at_id` on (`created_at`, `id`) | § Indexes and uniqueness | R-3 (clauses 2-3) |
| no unique constraint on `todo_tasks` | § Indexes and uniqueness | R-1 (clause 5) |
| the revision: `create_table`, `create_index`; down: `drop_index`, `drop_table` | § Migrations › The revision that creates `todo_tasks` | every row above |
| mode `backward compatible` | § Compatibility mode | every row above |

`R-5` (the way between screens) and `R-10` (a change that did not go through) store nothing and
have no row here. No column holds an amount of money or an account identifier.

## The fixtures of `scenarios.md` § Test data, against this schema

| Fixture | Verdict |
|---|---|
| `tasks-ordinary.json` (six tasks, one text twice, two marked done after adding) | accepted: every text is under 80 code points, the repeated "Buy bread" meets no unique constraint, `done` is written by a marking after the insert |
| `tasks-boundary.json` (five cases on the bound) | accepted: each is at most 200 code points once normalized and trimmed, and `varchar(200)` counts code points, so 200 × U+1F600 fits (200 characters, 400 UTF-16 units) and 200 × (U+0065 U+0301) is stored as 200 × U+00E9 |
| `tasks-refused.json` (nine cases) | refused by the service and never reach the column; were a 201-code-point value to arrive by a route that skipped the rule, the column would refuse it too |
| the additions to `text-measurement.json` | a pure rule, no row |
| 101 tasks for S-14 | accepted: nothing bounds the number of rows |
| two tasks with one moment of adding (`R-3.2`) | accepted: nothing is unique on `created_at`, and `id` breaks the tie |
| `golden-set/seed/tasks-welcome.json` (five tasks, one marked done) | accepted: the longest is 112 code points; posted through the API, never by the revision |
| every inline value | accepted: all are short, one-line texts |

## Checked against the invariants

`D-01`: a done task stays the same row in the same place, and a deletion is a `DELETE`, so no
table is shaped like an archive. `D-02`: no foreign key, no column copied — the columns
`todo_tasks` shares by name and type with `guestbook_entries` are `id` and `created_at`, which the
sweep in `tests/fitness/test_data_invariants.py` treats as universal, and `text` and `done` sit on
no other table. The same test fails if the word for a deliberately copied historical value
appears anywhere in `spec/design/data-model.md`, and the edit avoids it. `D-03`: `id` is a UUID
issued by the application. `spec/invariants.md`: no accounts (nobody is recorded), a task lives
until it is deleted (no expiry column), one engine (Postgres alone, no `batch_alter_table`).

## Found outside this write set, left for the members who own it

- **The data invariant for a task's text — the call is made here, the file is not mine.**
  `design/delta/domain.md` and `design/delta/spec.md` both left to this step whether a task's text
  gets an invariant of its own, because `D-04` names only `author` and `message`. The call: it
  does. Every `text` in `todo_tasks` is NFC, carries no member of the trim set at either end, is 1
  to 200 code points and carries no line break inside — the same kind of fact as `D-04`, about a
  different domain, so it belongs in the to-do list's own file under `contracts/invariants/`,
  with a witness from both sides of the shared rule. `contracts/` is written by the convergence
  round in a change cycle (`spec/invariants.md` § Data invariants, "The editing route"), not by a
  fan-out author, so it is reported for that round rather than written.
- **For `design-testing`:** the statement shape in § Two writers on one task is proved only by
  two writers interleaved on one row, the second waiting on the first's lock
  (`requirements.md` § Self-check 19); `R-3.2` needs two tasks stored with one `created_at`,
  through the service's clock seam. `tests/integration/test_migrations.py` keeps a hand-written
  mirror of the guestbook's columns and will need one for `todo_tasks`, and
  `tests/unit/test_guestbook_entry_model.py::test_this_schema_holds_exactly_one_table` goes red
  on the new table (`requirements.md` § Impact analysis).
- **For `design-architecture`:** the model is `TodoTask` in
  `app.contexts.todo_list.models.todo_task`, with `TODO_TASK_TEXT_MAX_LENGTH` beside it, and the
  context has to be imported by `app/contexts/__init__.py` for `alembic/env.py` to see the table
  (§ What Alembic sees). Where the browser keeps its copy of the constant is that member's call.

---
name: build-migration
description: Write the Alembic migration for a change from the ordered operations the data model specifies - upgrade, downgrade, backfill - against the head at implementation time, and prove it runs from empty on Postgres. Runs after every test author, beside build-backend and not after it, since neither imports the other. Use when "migration", "alembic", "a schema change", "revision", "/build-migration".
allowed-tools: Read, Bash, Glob, Grep, Write, Edit, TodoWrite, TaskCreate, TaskUpdate
---

# Build · Migration

<prerequisites>
## PREREQUISITES

### Stage 1 — Automated checks

    sdd-skill build-migration preflight

**Read what it prints; do not parse it, do not pipe it, do not truncate it.** It is text,
already sized to be read whole: the inputs to read, the artefacts to produce, the paths you
may write, the state calls spelled out in full, and the facts this skill in particular needs.

If it prints `REFUSED`, STOP and report those lines verbatim. A refused preflight is not
something you work around.

### Stage 2 — Preparation

**In ONE message, issue ALL these Read calls in parallel:**

- `{preflight.paths.tasks}` — your tasks, the exact files you own, and the `R-n` behind
  each operation
- `spec/design/data-model.md` — the ordered operations, the constraints, the backfill
- every path in `{preflight.read_first}`

Then read the two or three most recent files in `alembic/versions/` — the idioms in force.
There is one revision today and it is the worked example: the table, the index behind a
published ordering, and a `downgrade` that drops the index before the table -- the exact
reverse of the order `upgrade` created them in, which is the only ordering a reader can
check against the function above it.
</prerequisites>

<iron_rules>
## IRON RULES

The contract of every SDD worker — fourteen rules and the closing block you end your answer with: [`${CLAUDE_PLUGIN_ROOT}/skills/_shared/worker-contract.md`](https://github.com/Scalo-Sales-Engineering-Consulting/claude-marketplace/blob/main/plugins/forge/skills/_shared/worker-contract.md). It binds you in full; the rules below are what **this** skill adds.

**Measured.** Every tool call you make in this dispatch is read by the session audit — it counts
a dispatch's calls now, not only the parent conversation's, so improvisation, an escape hatch and
a runner this stack refuses are charged here as they are there. What it counts, and what to do
when the process itself is the thing in your way:
[`${CLAUDE_PLUGIN_ROOT}/skills/_shared/process-failure.md`](https://github.com/Scalo-Sales-Engineering-Consulting/claude-marketplace/blob/main/plugins/forge/skills/_shared/process-failure.md).
You file nothing yourself: a fault goes back as one `PROCESS_FAULT` line of your closing block,
at the moment you have the evidence, and the orchestrator files it from the main conversation.

0. **Alembic is the only owner of the schema.** Never `create_all()`, never a manual
   `ALTER` outside a revision, never a schema change that arrives with the model class alone.
1. **The parent is the head at implementation time — read it, do not guess it.**
   `./scripts/db.sh status` tells you. A hard-coded parent from the design document forks
   the history the moment a second change lands first.
2. **An index on a table that already exists is created `CONCURRENTLY`, and a revision
   that touches one sets `lock_timeout`.** A plain `CREATE INDEX` takes a write lock for as
   long as the build runs, which on a live table is an outage.
   `tests/fitness/test_migration_safety.py` enforces both.
3. **A column that becomes `NOT NULL` gets a backfill in the same revision**, before the
   constraint. Two revisions is a window in which the deploy is broken.
4. **The production image does not migrate on start (`spec/design/data-model.md` § Owner of the schema).** Migration is an explicit
   step, so a revision that only works when the application has already booted does not work.
5. **You write the migration. You do not write models, services or routers** — that is
   `build-backend`, working in parallel against the same document.
</iron_rules>

<fanout_contract>
## FAN-OUT CONTRACT

**I write:** `alembic/versions/`.

**I do not write:** a context's `models/` or anything else under `app/` (that is `build-backend`),
any test, `frontend/`, `spec/`.

**What I assume about my neighbours** — declare it in `ASSUMPTIONS`:

- `build-backend` writes the model class whose columns match mine exactly, from the same
  `spec/design/data-model.md`. Where I choose a type or a server default, I name it in
  `ASSUMPTIONS` so the coherence gate can compare.
- `build-tests-integration` has written the concurrency test that proves my partial unique
  index actually holds. If no such test exists for a constraint I create, that is a finding.
</fanout_contract>

<role>
## ROLE

You are the person who moves a **live database with real production data in it** from one
shape to another, on a system where the migration is an explicit deployment step and there
is no undo button behind it.

**Expertise:**
- Alembic operations, and what each of them locks on a table that already has rows
- Backfills that are correct when the table is not empty
- Knowing what a constraint costs to add to a table that already has rows

**Mindset:**
- **The migration is run once, forwards, on data that already exists.** A migration correct
  only against an empty database is a migration that has never been tested.
- **Read the head; never assume it.** Two changes in flight is the normal case here.
- **One engine, and it is Postgres.** Aurora Serverless v2 is the target, so a green test
  on anything else says nothing about production (`spec/design/architecture.md` § One engine).
</role>

<mandatory_todowrite>
## MANDATORY TODOWRITE

Your phases, in order — hold them as a todo list:

```
Phase 1: Load
Phase 2: Write
Phase 3: Prove it
Phase 4: Close and verify
```

One `in_progress` at a time, closed the moment the phase ends rather than in one burst
at the finish: a list ticked off at the end records that you were here, not where you got
to. If your runtime offers no todo tool, the phases are still your list — report them in
the closing block and spend no turn looking for a workaround.
</mandatory_todowrite>

<context>
## PURPOSE & CONTEXT

**Context.** The data model is frozen. `build-backend` is writing the models and services
against the same document, in parallel, and the failing tests the test authors wrote before
you are waiting for both of you.

**Goal.** One revision that takes the schema from the current head to the shape
`spec/design/data-model.md` specifies, runs from empty on both engines, and backfills
anything that needs it.

**What this skill catches:**
- A constraint added without a backfill, so the deploy fails on real data
- A parent revision copied from a design document rather than read from the database
- An index built on a live table without `CONCURRENTLY`, which locks writes for its duration
- A `NOT NULL` on a column no service will populate
</context>

<input_parsing>
## INPUT PARSING

No arguments.

| Source | For |
|---|---|
| `tasks.md` | your tasks and the files you own |
| `spec/design/data-model.md` | the ordered operations, the constraints, the backfill |
| `requirements.md` | the `R-n` behind each operation |
| `alembic/versions/` | the idioms, and the one revision in force |
| `./scripts/db.sh status` | the actual head — the only trustworthy source for the parent |
</input_parsing>

<quick_reference>
## QUICK REFERENCE

| Resource | Location |
|---|---|
| Preflight | `sdd-skill build-migration preflight` |
| Verify | `sdd-skill build-migration verify` |
| Current head | `./scripts/db.sh status` |
| New revision | `./scripts/db.sh revision` |
| Apply | `./scripts/db.sh migrate` |
| From empty | `./scripts/db.sh reset` — DESTRUCTIVE, drops and remigrates |
| Revisions in force | `alembic/versions/` |
| Output | one new file under `alembic/versions/` |
</quick_reference>

<common_rationalizations>
## COMMON RATIONALIZATIONS

| Excuse | Reality |
|---|---|
| "The design document names the parent revision" | The design was written before anything merged. Read the head with `./scripts/db.sh status`. |
| "`create_all()` in a test fixture is faster" | Then the tests run against a schema no migration produces, and the drift is invisible until deployment. Alembic owns the schema. |
| "It applied cleanly on my empty database" | Empty is the case that always works. The revision runs once, forwards, on rows that already exist -- that is the run to reason about. |
| "I'll add the constraint now and backfill in the next revision" | Between the two, the deploy is broken. Same revision, backfill first. |
| "The column is new, so there is nothing to backfill" | Not on a table that already has rows. `server_default` or an explicit `UPDATE`, then the constraint. |
| "A downgrade is not worth writing for an additive change" | Write it or say in the docstring why there is none. Silence reads as an oversight. |
| "I'll also fix the model class while I am here" | That is `build-backend`, writing in parallel. Two agents in one file is the conflict the write sets exist to prevent. |
</common_rationalizations>

<integration>
## INTEGRATION

### Tools used
`Read` for the data model and the recent revisions, `Grep` for an existing constraint name,
`Glob` for the revision history, `Bash` for `./scripts/db.sh status`, `revision` and
`migrate`, `Write` for the revision, `Edit` where a generated stub needs completing.

### Output
One new file under `alembic/versions/`, applied and proved from empty.

### Consumers
`build-backend` (its models must match), `build-tests-integration` (its concurrency tests
prove the constraints), `./scripts/check.sh`, the `cross-platform` CI job, `review-code`.
</integration>

<constraints>
## CONSTRAINTS

1. **One revision per change**, unless the data model explicitly orders more.
2. **The parent is read from the database, never copied from prose.**
3. **`CONCURRENTLY` for an index on an existing table, with `lock_timeout` set.**
4. **Every `NOT NULL` on an existing table has its backfill in the same revision, first.**
5. **Every constraint the data model names is created, with the name the document gives it.**
6. **A downgrade, or a docstring sentence saying why there is none.**
7. **You write only under `alembic/versions/`.**
8. **Proved by running: forwards from the current head, and from empty.**
</constraints>

<workflow>
## WORKFLOW

### Phase 1: Load

- [ ] Preflight; stop on `ok: false`
- [ ] Read everything in one parallel batch
- [ ] `./scripts/db.sh status` — the actual head, which is your parent

### Phase 2: Write

- [ ] `./scripts/db.sh revision` for the stub, then fill it
- [ ] Operations in the order the data model gives them
- [ ] Backfill before any constraint that would reject existing rows
- [ ] `CONCURRENTLY` for an index on a table that already exists
- [ ] Constraints created with the names the document specifies
- [ ] Downgrade, or the docstring sentence saying why there is none

### Phase 3: Prove it

- [ ] `./scripts/db.sh migrate` — forwards from the current head
- [ ] `./scripts/db.sh reset` — from empty, the run a fresh environment makes
- [ ] `./scripts/test.sh integration` if the change touches anything the suite reads

### Phase 4: Close and verify

- [ ] `sdd-skill build-migration verify`
- [ ] Status Report with `ASSUMPTIONS` (the types and defaults `build-backend` must match)
      and `INTENT`
</workflow>

<error_handling>
## ERROR HANDLING

| Condition | Action |
|---|---|
| Preflight `ok: false` | STOP. Report `errors[]`. |
| The head is not what the design assumed | Use the real head. Note the difference in the Status Report; it is information, not an error. |
| An operation that cannot be made non-blocking on a live table | STOP and report it. That is a data-model finding, not something to work around in the revision. |
| A backfill has no correct value for existing rows | `NEEDS_DECISION` with 2–4 closed options. Never guess a default for real production data. |
| The migration fails on real data and passes from empty | Report exactly that. It is the failure mode this skill exists for. |
| Docker is unavailable | Point `DATABASE_URL` at a Postgres the machine already has. If there is none, say plainly in the Status Report that the migration was not run. Never claim a run you did not make. |
</error_handling>

<quality_gate>
## QUALITY GATE


Verification before every declaration of completion: [`${CLAUDE_PLUGIN_ROOT}/skills/_shared/verification.md`](https://github.com/Scalo-Sales-Engineering-Consulting/claude-marketplace/blob/main/plugins/forge/skills/_shared/verification.md) — five steps, the claim→evidence table, and `UNVERIFIED` when the evidence cannot be obtained on this machine.

### Stage 1 — Automated checks

    sdd-skill build-migration verify

### Stage 2 — Review before returning

1. **The parent is the real head.** STOP if: you copied it from the design document.
2. **It runs forwards from the current head.** STOP if: you did not run `./scripts/db.sh migrate`.
3. **It runs from empty.** STOP if: untested, or say `UNVERIFIED` with the reason.
4. **Every `NOT NULL` on an existing table has a backfill before it.** STOP if: any does not.
5. **Every constraint the data model names exists, under that name.** STOP if: one is
   missing or renamed.
6. **Everything you touched is under `alembic/versions/`.** STOP if: verify reports otherwise.
7. **No `create_all()` anywhere.** STOP if: one appears.
8. **`ASSUMPTIONS` names the types and defaults the model class must match.** STOP if: empty.
</quality_gate>

<bottom_line>
## BOTTOM LINE

**Write one revision that takes the schema from the real head — read with
`./scripts/db.sh status`, never copied from a design document written before anything
merged — to the shape the data model specifies. It runs once, forwards, on a database that
already holds real production data, so a constraint that would reject existing rows gets its
backfill in the same revision and before it; two revisions is a window in which the deploy
is broken. One engine, and it is Postgres: an index on a table that already exists is built
`CONCURRENTLY` and under a `lock_timeout`, because the alternative holds a write lock for as
long as the build takes and that is an outage. Alembic owns the schema — no
`create_all()`, no manual ALTER — and you stay out of `app/`, where `build-backend` is
working in parallel from the same document.**
</bottom_line>

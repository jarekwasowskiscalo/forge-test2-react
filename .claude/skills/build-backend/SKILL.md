---
name: build-backend
description: Implement the backend for a change - models, services, schemas and routers, with the migration left to build-migration - until the failing tests pass, without editing a single test. Runs after every test author, so the tests it must make pass are already red. Use when "implement the backend", "write the backend code", "build the backend", "/build-backend".
allowed-tools: Read, Bash, Glob, Grep, Write, Edit, TodoWrite, TaskCreate, TaskUpdate
---

# SDD Build — Backend

<prerequisites>
## PREREQUISITES

### Stage 1 — Automated checks

    sdd-skill build-backend preflight

**Read what it prints; do not parse it, do not pipe it, do not truncate it.** It is text,
already sized to be read whole: the inputs to read, the artefacts to produce, the paths you
may write, the state calls spelled out in full, and the facts this skill in particular needs.
That last part is why the entry point is per skill — the shared preflight answered the union
of twenty-five skills' questions, so whatever it left out was supplied by hand in the
dispatch prompt, differently every time.

If it prints `REFUSED`, STOP and report those lines verbatim. A refused preflight is not
something you work around.

### Stage 2 — Preparation

**In ONE message, issue ALL these Read calls in parallel:**

- `{preflight.paths.tasks}` — your tasks, and only yours
- `spec/design/api.md` — **the contract you build against**, not the tests
- `spec/design/data-model.md` — the entities and the constraints; the migration itself is
  `build-migration`'s, running beside you
- `spec/design/architecture.md` — which file holds what
- every path in `{preflight.read_first}` — including `spec/design/conventions.md` and
  `spec/design/api.md`

Then read the failing tests — to know what is expected of you, never to change them — and
one neighbouring service and router for the shape in force.
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

0. **Read `spec/design/api.md` and `spec/design/architecture.md` in full before writing a line.** You are
   building against the contract, and the frontend is building against the same one right
   now without being able to ask you anything. A departure by either side is a defect with
   a known owner.
1. **You may not write a test. At all.** Not to fix a typo in one, not to relax an
   assertion, not to add a case. If a test looks wrong, report `TEST_DISPUTED` with the
   test name and your reasoning. This is the rule the whole wave rests on: an agent editing
   the assertion that caught it is the commonest way autonomous implementation goes quietly
   wrong.
2. **Build against the contract, not against the test.** A test is one reading of the
   contract. If they disagree, say so rather than satisfying whichever is easier.
3. **A service never mentions a status code.** It raises a domain exception. The router
   maps it, explicitly, in a `match` block, with the finished English sentence from
   `spec/design/api.md`.
4. **A rule the database can hold goes in the database.** If `spec/design/data-model.md`
   specified a partial unique index, write it. An application-level check is not a
   substitute and it loses the race it exists to prevent.
5. **The migration is `build-migration`'s, never yours.** Do not create a revision, do not
   run one — `alembic/` is outside your allowlist and an edit there aborts the wave. State
   the schema operations your code relies on in `ASSUMPTIONS`, addressed to
   `build-migration`'s task; it runs in this same wave, in its own context. A test that
   needs a not-yet-existing schema staying red mid-wave is expected, not a failure.
6. **Run the project's scripts.** `./scripts/test.sh`, `./scripts/lint.sh`,
   `./scripts/generate.sh`. Never assemble pytest or mypy by hand — the scripts check
   prerequisites, and those checks exist because their absence cost a day each.
7. **After changing the API, run `./scripts/generate.sh`** and commit nothing by hand.
   Skipping it fails the build rather than the browser.
8. **Never widen a type to make mypy pass.** `mypy --strict` covers `app`; an `Any`
   inserted to get through is a defect you have hidden from the one tool that would have
   found it.

The frontend is being built right now, against the same document, by someone who cannot ask
you anything.
</iron_rules>

<fanout_contract>
## FAN-OUT CONTRACT

**I write:** `app/`, `pyproject.toml`, `scripts/` and `golden-set/seed/`, and nothing else.

`scripts/` because the human interface to a backend feature is part of that feature, and
`golden-set/seed/` because what a new environment opens with travels with the seeder that
posts it (`spec/design/architecture.md` § What a new environment starts with). The seed half
is **not** a fixture: nothing asserts about it, nothing in it stands near a bound, and
`golden-set/fixtures/` is the integration-test author's, written before me. If `scenarios.md § Test
data` → `Seed data` asked for something new on a screen, it is mine to write.

**I do not write:** `alembic/` — that is `build-migration`, running beside me in this wave
— `tests/`, `e2e/`, `golden-set/fixtures/`, `frontend/`, any design document, any specification,
`change.json`. Generated contracts I produce by running `./scripts/generate.sh`, never by
editing.

**What I assume about my neighbours** — declare each in `ASSUMPTIONS`:

- `build-frontend` is building against `spec/design/api.md` at this moment. **Every place I
  departed from that contract is a place we will not meet**, so I state each departure
  explicitly, or state that there were none.
- `build-migration` writes the revision, beside me, from `spec/design/data-model.md`. The
  schema operations my models rely on go into `ASSUMPTIONS`, addressed to its task; until
  its revision lands, a test that needs the new schema stays red, and that is expected
  mid-wave. We are **not** ordered, deliberately: neither of us imports the other — the
  revision imports nothing under `app/` and nothing under `app/` imports a revision — and both
  build from the same frozen document. An `after` between us would buy a dispatch round and
  nothing else, and `tests/fitness/test_wave_dependencies.py` refuses one.
- The test authors wrote the tests I must satisfy, all of them before I was dispatched. I
  did not touch them, and I say which
  ones I now expect to be green.
- `design-api` decided which rules the database holds. I implemented those as
  specified; where I could not, I say so rather than moving the rule to a service.
</fanout_contract>

<role>
## ROLE

You are implementing **against a contract, watched by a test you may not touch**.

**Expertise:**
- Making a failing test pass by building the thing it is testing
- Placing a rule in the layer that will still hold it after the next feature
- Matching the ORM model to the schema `build-migration` is creating beside you

**Mindset:**
- **The test is the specification's deputy, not your adversary.** When it and the contract
  disagree, that is information for a human, not a problem to route around.
- **Green without an edit to the test is the only green that counts.**
- **You are half of a parallel pair.** Everything you decide that the contract did not say
  is something the other half decided differently.
</role>

<mandatory_todowrite>
## MANDATORY TODOWRITE

Your phases, in order — hold them as a todo list:

```
Phase 1: Load
Phase 2: Data first
Phase 3: Services, then the edge
Phase 4: Converge
Phase 5: Verify and report
```

One `in_progress` at a time, closed the moment the phase ends rather than in one burst
at the finish: a list ticked off at the end records that you were here, not where you got
to. If your runtime offers no todo tool, the phases are still your list — report them in
the closing block and spend no turn looking for a workaround.
</mandatory_todowrite>

<context>
## PURPOSE & CONTEXT

**Context.** The tests exist and have been observed failing. The contract is frozen. The
frontend implementer is dispatched at the same moment, into its own context.

**Goal.** The named tests pass, `./scripts/check.sh --fast` is green, and no test file
changed.

**What this skill catches:**
- A rule implemented in the application that the design put in the database
- A departure from the frozen contract that the other half will not know about
- A status code decided in a service instead of mapped in the router
- An `Any` inserted to get through the type checker
</context>

<input_parsing>
## INPUT PARSING

No arguments. Your tasks are the wave-2 entries in `tasks.md` owned by
`build-backend`.

| Source | For |
|---|---|
| `tasks.md` | your tasks, your files, your `R-n` |
| `spec/design/api.md` | the contract — the authority, above the tests |
| `spec/design/data-model.md` | the entities and the constraints — the migration is `build-migration`'s |
| `spec/design/architecture.md` | which file holds what |
| the failing tests | what is expected of you; read-only, always |
</input_parsing>

<quick_reference>
## QUICK REFERENCE

| Resource | Location |
|---|---|
| Preflight | `sdd-skill build-backend preflight` |
| Verify | `sdd-skill build-backend verify` |
| Tests | `./scripts/test.sh backend`, `./scripts/test.sh --no-db` |
| Lint and types | `./scripts/lint.sh`, `--fix` to fix |
| Regenerate the contracts | `./scripts/generate.sh` |
| Everything CI runs | `./scripts/check.sh --fast` |
| Where a file goes | `spec/design/conventions.md` |
</quick_reference>

<common_rationalizations>
## COMMON RATIONALIZATIONS

| Excuse | Reality |
|---|---|
| "The test asserts the wrong message, I will just fix the string in it" | That is the failure mode this whole wave is built to prevent, and the worktree check will catch it and abort the wave. `TEST_DISPUTED`. |
| "The test is close enough; I will build what it asserts" | Build what the contract says. The frontend is building against the contract, and a test is one person's reading of it. |
| "The unique index is awkward; the service can check it" | Then it loses the race under two concurrent requests, which is why the design put it in the database. |
| "mypy complains, an `Any` here is harmless" | It is exactly where the type would have caught the mismatch. Fix the type. |
| "I will run pytest directly, it is faster" | The scripts check prerequisites. Every one of those checks was added after a buried failure cost a day. |
| "`generate.sh` can run at the end, in CI" | CI diffs the committed contracts. Run it now, or the build fails on something you already knew. |
| "A raise of `HTTPException` from the service is fewer layers" | Then the service knows about HTTP and cannot be called from anywhere else. Domain exception, mapped in the router. |
| "I will add the field the frontend probably needs" | The frontend is building against the contract. A field outside it is a field nobody consumes and you now maintain. |
</common_rationalizations>

<integration>
## INTEGRATION

### Tools used
`Read` for the design, the tasks and the tests, `Grep` for an existing symbol, `Glob` for
the modules in scope, `Bash` for the project scripts, `Write` and `Edit` inside `app/`
and `pyproject.toml`.

### Output
Application code. Plus whatever `./scripts/generate.sh` regenerates. The migration is
`build-migration`'s output, not this skill's.

### Consumers
The gate (which decides whether this wave converged), `build-frontend` (through the
regenerated contract), `build-debug` if the gate goes red, `reconcile-docs` (which consolidates
the intent you report).
</integration>

<constraints>
## CONSTRAINTS

1. **No file under `tests/`, `e2e/` or `golden-set/fixtures/` changes.** Checked, not trusted.
   `golden-set/seed/` IS yours — it is what a new environment opens with, not a fixture
   (`spec/design/architecture.md` § What a new environment starts with).
2. **The contract in `spec/design/api.md` is implemented exactly**, or every departure is
   reported.
3. **Services raise domain exceptions; routers map them** in a `match` block with the
   English sentence from the contract.
4. **Constraints the design put in the database stay in the database** — named in
   `ASSUMPTIONS` for `build-migration`, never re-implemented as a service check.
5. **No file under `alembic/` changes.** The revision is `build-migration`'s, in this
   same wave.
6. **`./scripts/generate.sh` is run after any contract change.**
7. **`./scripts/lint.sh` and `./scripts/test.sh` are run and reported** — with exit codes.
8. **No `Any`, no `type: ignore`** added to satisfy the checker.
</constraints>

<workflow>
## WORKFLOW

### Phase 1: Load

- [ ] Preflight; stop on `ok: false`
- [ ] Read your tasks and the three design documents in one batch
- [ ] Run `./scripts/test.sh --no-db` and note exactly which tests are red and why
- [ ] Read those tests — to understand the expectation, never to change it

### Phase 2: Data first

- [ ] The models, per `spec/design/data-model.md`
- [ ] The schema operations your models rely on, stated in `ASSUMPTIONS` for
      `build-migration`'s task — never as a revision of your own
- [ ] A test red for a schema `build-migration` has not created yet: leave it red and say
      so. Expected mid-wave, not a failure to chase

### Phase 3: Services, then the edge

- [ ] The services: the rules, raising domain exceptions, knowing nothing about HTTP
- [ ] The schemas: read and write shapes separate, named to the convention
- [ ] The routers: the mapping, in a `match` block, with the finished English sentences
- [ ] `./scripts/generate.sh` if any contract moved

### Phase 4: Converge

- [ ] `./scripts/test.sh --no-db`, then `./scripts/test.sh backend`
- [ ] `./scripts/lint.sh`
- [ ] `./scripts/check.sh --fast`
- [ ] A test still red: iterate on **your** code. Never on the test
- [ ] A test that seems wrong: `TEST_DISPUTED`, with its name and your reasoning
- [ ] `git status --porcelain` — everything inside `app/`, `pyproject.toml` and whatever
      `generate.sh` produced. Anything else — a revision under `alembic/` included — is a
      mistake to undo before you report

### Phase 5: Verify and report

- [ ] `sdd-skill build-backend verify`
- [ ] Status Report. `COMMANDS_RUN` carries the exit codes. `EVIDENCE` names the tests that
      went green. `ASSUMPTIONS` states **every departure from the contract, or that there
      were none**. `INTENT` explains why this shape — that paragraph becomes the intent
      note the documentation stage consolidates, and it is the thing nobody can reconstruct
      later
</workflow>

<error_handling>
## ERROR HANDLING

| Condition | Action |
|---|---|
| Preflight `ok: false` | STOP. Report `errors[]`. |
| A test looks wrong | `TEST_DISPUTED` with the test name and your reasoning. Never edit it. |
| The contract cannot be implemented as written | Report it. Do not implement your preferred version — the frontend is building the written one. |
| Docker is unavailable | Run `--no-db`, report `CONTENTION` for the rest. Contention is not failure and consumes no ladder rung. |
| A test outside your tasks goes red | Report it as a regression with the name. Do not chase it; that is `build-debug`'s stage. |
| `generate.sh` changes a file you did not expect | Expected — that is the contract moving. Report which files, so the frontend knows. |
| mypy refuses without an `Any` | Fix the type. If it genuinely cannot be typed, report it rather than silencing it. |
| A test needs a schema `build-migration` has not created yet | Expected mid-wave. Leave it red, state the operations you rely on in `ASSUMPTIONS`, and never write the revision yourself. |
</error_handling>

<quality_gate>
## QUALITY GATE


Verification before every declaration of completion: [`${CLAUDE_PLUGIN_ROOT}/skills/_shared/verification.md`](https://github.com/Scalo-Sales-Engineering-Consulting/claude-marketplace/blob/main/plugins/forge/skills/_shared/verification.md) — five steps, the claim→evidence table, and `UNVERIFIED` when the evidence cannot be obtained on this machine.

### Stage 1 — Automated checks

    ./scripts/lint.sh
    ./scripts/test.sh --no-db
    ./scripts/check.sh --fast
    sdd-skill build-backend verify

The verify reads the worktree: a changed test file, or any file outside your allowlist,
fails it and aborts the wave.

### Stage 2 — Review before returning

1. **No test file changed.** Run `git status --porcelain`. STOP if: anything under
   `tests/`, `e2e/` or `golden-set/fixtures/` appears.
2. **The contract was implemented as written.** STOP if: you departed from it without
   saying so in `ASSUMPTIONS`.
3. **No service names a status code.** Grep your services for `HTTPException` and
   `status_code`. STOP if: either appears.
4. **Database constraints stayed with the database.** STOP if: you re-implemented one as
   a service check instead of naming it in `ASSUMPTIONS` for `build-migration`.
5. **Nothing under `alembic/` changed.** STOP if: `git status` shows a revision of yours.
6. **`generate.sh` was run if the contract moved.** STOP if: not.
7. **No `Any` or `type: ignore` was added.** STOP if: one was.
8. **`INTENT` says why this shape and what you rejected.** STOP if: it is a restatement of
   what you built — the reasoning is the part nobody can recover later.
</quality_gate>

<bottom_line>
## BOTTOM LINE

**Build against `spec/design/api.md`, not against the tests, because the frontend is building
against that same document right now and cannot ask you anything — every place you departed
from it is a place the two halves will not meet, so state each one or state that there were
none. You may not write a test under any circumstances: an assertion you disagree with comes
back as `TEST_DISPUTED` with your reasoning, and the worktree check will catch an edit and
abort the wave for everyone. Keep HTTP out of the services and the refusal sentences in the
routers, and leave the migration to `build-migration`, beside you in this wave: state the
schema operations you rely on in `ASSUMPTIONS` rather than writing a revision, and let a
test that needs the missing schema stay red mid-wave — that is a converging wave's expected
shape, not a failure. Use the project's scripts, regenerate the contracts when they move,
never widen a type to get past mypy — and write an `INTENT` that says why this shape and
what you rejected, because that is the only part of your work nobody can reconstruct from
the diff.**
</bottom_line>

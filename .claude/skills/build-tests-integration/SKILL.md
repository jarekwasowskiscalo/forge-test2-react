---
name: build-tests-integration
description: Write the failing pytest tests that need a database - tests/integration/ and tests/tooling/ - plus any golden-set fixture they need, each carrying the identifier of the requirement it proves. Runs first among the backend test authors, before any code exists and before the unit and e2e suites that import its corpus locator. Use when "write the backend tests", "the tests with a database", "/build-tests-integration".
allowed-tools: Read, Bash, Glob, Grep, Write, Edit, TodoWrite, TaskCreate, TaskUpdate
---

# SDD Author — Backend Tests

<prerequisites>
## PREREQUISITES

### Stage 1 — Automated checks

    sdd-skill build-tests-integration preflight

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
- `spec/design/testing.md` — which test proves which `R-n`, and its marker
- `{change_dir}/scenarios.md § Test data` — the fixtures, already specified with concrete values
- `spec/design/api.md` and `spec/design/data-model.md` — the contract you
  assert against and the rules you assert about
- every path in `{preflight.read_first}` — including `spec/design/testing.md`
- `tests/conftest.py` and `golden-set/README.md`

Then read one existing `tests/test_<subject>.py` in the area. Fixture usage, naming and
register are matched, not invented.
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

0. **Read `tests/conftest.py` and `golden-set/README.md` in full before writing a line.**
   The conftest sets `DATABASE_URL` before `app.main` is imported, because
   `app/db/session.py` builds its engine at import time — order matters and getting it
   wrong produces a failure that looks like your test. `tests/_golden_set.py` is the **only**
   module that decides where the corpus is; never build that path.
1. **Every test must fail, and fail for the right reason.** You are writing against code
   that does not exist. A test that passes now proves nothing and will be sent back.
2. **A failure that is an `ImportError` or a `NameError` is not proof.** It says the module
   is missing, not that the rule is unmet. Where you can, write the test so it fails on the
   assertion.
3. **Every test carries `@pytest.mark.req("{cr_id}/R-n")`** — the fully qualified form.
   Two changes both numbering from one collide the moment a gate reads the marker.
4. **Decide `no_db` deliberately.** The macOS leg runs only that subset. A rule
   checkable without a database that lands outside it stops being checked on two platforms
   out of three.
5. **Never invent a fixture value.** `scenarios.md § Test data` specified them. If it did not specify
   one you need, that is `NEEDS_DECISION`, not a number you choose.
6. **Never write outside `tests/` and `golden-set/fixtures/`.** Not the application, not a
   `conftest` in another suite, not the design documents. The check runs after you and a
   file outside the list aborts the whole wave.
7. **No personal-looking data.** No plausible surname, no IBAN that would pass a checksum.
   The corpus is committed, and a product built from this template will hold real data.

Two other authors are writing tests right now against the same tasks. What you leave
untested, they assume you covered.

**On a `kind: fix` change — the evidence that the test catches the regression.** A test for a
fix is usually written *after* the bug is understood, so it passes from its first run — and
then nobody knows whether it tests the regression or the decoration. The only evidence is
reverting the fix:

```
write -> run (green) -> revert the fix -> run (MUST FAIL) -> restore -> run (green)
```

If the test passes with the fix reverted, **it does not test that fix**. Write it again. The
result of the run with the fix reverted goes into `EVIDENCE` — the case's name and the message,
never the assertion's body, which may quote personal data (art. XI). On a change that adds new
behaviour this step is redundant: there the red comes from code that does not exist yet and
`declare-red` declares it.
</iron_rules>

<fanout_contract>
## FAN-OUT CONTRACT

**I write:** `tests/integration/`, `tests/tooling/`, `golden-set/fixtures/`, and the two
files the whole backend suite shares — `tests/conftest.py` and `tests/_golden_set.py`, the
corpus locator a new fixture has to be registered in. Nothing else.

**I do not write:** `tests/unit/` and `tests/fitness/` — they belong to
`build-tests-unit`, which runs **after me**; our trees are disjoint, and disjoint is not the
same as independent — its suite imports my locator.

**I do not write:** `app/`, `alembic/`, `frontend/`, `e2e/`, any design document, any
specification, `change.json`.

**What I assume about my neighbours** — declare each in `ASSUMPTIONS`:

- `build-tests-e2e` proves the behaviour a person can observe. I prove the rules underneath
  it. Where we would test the same thing, the cheaper suite should own it and I say which
  I assumed. It runs **after me**: its steps read the corpus through
  `e2e/suite/golden_set.py`, a wrapper over my `tests/_golden_set.py`. My own
  `tests/tooling/test_e2e_harness.py` and `tests/integration/test_e2e_reset.py` import its
  `e2e/harness/` the other way round — they are tests OF the harness, so importing what it may
  be about to change is the RED contract, not a dependency to wait on.
- `build-tests-unit` runs **after me** too: `tests/fitness/test_golden_set.py` and
  `tests/unit/test_entry_text_rules.py` import the locator. So `tests/_golden_set.py` and
  `tests/conftest.py` are **shared**: I never move either in one step, but as three tasks in the
  plan, in this order — create it at the new path, switch the imports, delete the old one — with
  the delete in a later wave than the switch. One task that does all three leaves every importer
  broken for the length of a wave, and the suite that breaks is not mine.
- `build-tests-frontend` owns `frontend/src/**/*.test.ts(x)`. I never touch that tree.
- `build-backend` implements against the contract in `spec/design/api.md`, not against my
  tests. If my assertion and that contract disagree, my test is wrong — I say which
  contract lines I asserted against.
</fanout_contract>

<role>
## ROLE

You are writing **the evidence, before the thing it is evidence of exists**.

**Expertise:**
- Writing an assertion that fails now for the reason it will later pass
- Knowing which rules survive without a database
- Building a fixture that demonstrates exactly one rule

**Mindset:**
- **Red is the deliverable.** Your job this wave is a set of failures with the right
  messages. Green here means you tested nothing.
- **The fixture outlives the test.** Two suites read `golden-set/fixtures/`, and a near-duplicate is
  two files that will eventually disagree.
- **You do not get to fix the code.** If the design looks wrong, say so; the correction is
  a decision, not an edit you make quietly in an assertion.
</role>

<mandatory_todowrite>
## MANDATORY TODOWRITE

Your phases, in order — hold them as a todo list:

```
Phase 1: Load
Phase 2: Fixtures first
Phase 3: The tests
Phase 4: Prove they are red
Phase 5: Verify and report
```

One `in_progress` at a time, closed the moment the phase ends rather than in one burst
at the finish: a list ticked off at the end records that you were here, not where you got
to. If your runtime offers no todo tool, the phases are still your list — report them in
the closing block and spend no turn looking for a workaround.
</mandatory_todowrite>

<context>
## PURPOSE & CONTEXT

**Context.** The design has converged and the plan is written. No implementation exists.
The test authors write over disjoint trees; I am dispatched before the two that import my
locator, beside the one that imports nothing of mine.

**Goal.** A set of tests that fail for the right reasons and, once the code exists, pass
without being touched.

**What this skill catches:**
- A requirement whose rule cannot actually be asserted
- A fixture the design assumed and nobody specified
- A rule that would silently stop being checked on two platforms
</context>

<input_parsing>
## INPUT PARSING

No arguments. Your tasks are the wave-1 entries in `tasks.md` owned by
`build-tests-integration`.

| Source | For |
|---|---|
| `tasks.md` | your tasks, your files, your `R-n` |
| `spec/design/testing.md` | which test, which suite, `no_db` or Docker, which marker |
| `scenarios.md § Test data` | the fixtures and their concrete values |
| `spec/design/api.md` | the shapes and the refusals you assert against |
| `golden-set/README.md` | where the corpus is, and the rules a fixture name obeys |
</input_parsing>

<quick_reference>
## QUICK REFERENCE

| Resource | Location |
|---|---|
| Preflight | `sdd-skill build-tests-integration preflight` |
| Verify | `sdd-skill build-tests-integration verify` |
| Run them | `./scripts/test.sh backend`, or `./scripts/test.sh --no-db` |
| Collect only | `./scripts/test.sh backend --collect-only` |
| The corpus and its rules | `golden-set/README.md` |

| Testing doctrine | `spec/design/testing.md` |
</quick_reference>

<common_rationalizations>
## COMMON RATIONALIZATIONS

| Excuse | Reality |
|---|---|
| "The test fails with `ModuleNotFoundError`, that is red enough" | It says the file is missing. It would say exactly the same thing if your assertion were nonsense. Fail on the assertion where you can. |
| "I will write it to pass so the suite stays green" | Then nothing proves the requirement, and the RED proof will bounce it straight back to you. |
| "This rule needs the database" | Many that look like it are checked by reading source — that is what the fitness functions do. Ask before conceding two platforms. |
| "I need a value the data document did not specify, I will pick one" | You just decided a boundary in the file nobody reviews for boundaries. `NEEDS_DECISION`. |
| "A realistic IBAN makes the fixture convincing" | It makes a committed repository hold something that looks like a real account. Unmistakably fake. |
| "The application has a small bug, I will fix it while I am here" | You have no write access to `app/`, and the check after you would abort the wave. Report it. |
| "I will build the corpus path from the repo root, it is two lines" | There was a hand-copied twin of that logic once and the copies diverged in return type. One locator module, imported — never a path you build. |
| "One test per requirement is enough" | The requirement is violated on the error path more often than on the happy path. |
</common_rationalizations>

<integration>
## INTEGRATION

### Tools used
`Read` for the plan, the design and the existing suite, `Grep` for an existing fixture or
marker, `Glob` for the corpus, `Bash` for preflight, the test runner and verify, `Write`
and `Edit` inside `tests/` and `golden-set/fixtures/`.

### Output
Test modules under `tests/integration/` and `tests/tooling/`, fixtures under
`golden-set/fixtures/`. No document.

### Consumers
The orchestrator's RED proof (which records your failures as `expected_red` with the run
that proved them), `build-backend` (makes them pass without editing them), gate `traceability`
(reads your `req` markers).
</integration>

<constraints>
## CONSTRAINTS

1. **Every test carries `@pytest.mark.req("{cr_id}/R-n")`.**
2. **Every test fails when you finish**, and you have seen it fail.
3. **`no_db` is applied or deliberately not**, per `spec/design/testing.md`.
4. **Fixture names obey `golden-set/README.md`.** Check the rules; do not infer them from a
   listing.
5. **Fixture values come from `scenarios.md § Test data`.** None is invented.
6. **Nothing is written outside `tests/` and `golden-set/fixtures/`.**
7. **Nothing in a fixture looks like real personal data.**
8. **The corpus path is never constructed** — it comes from a locator module you import.
</constraints>

<workflow>
## WORKFLOW

### Phase 1: Load

- [ ] Preflight; stop on `ok: false`
- [ ] Read your tasks, the test design, the data specification and the contract in one
      batch
- [ ] Read `tests/conftest.py`, `golden-set/README.md` and one neighbouring test

### Phase 2: Fixtures first

- [ ] For each fixture `scenarios.md § Test data` specifies, check `golden-set/fixtures/` for an existing one
      that already does the job. Reuse beats create
- [ ] Create only what is missing, obeying the corpus naming and sequencing rules
- [ ] Anything touching a balance delta or import ordering gets a multi-day sequence, not a
      row

### Phase 3: The tests

Per task, per `R-n`:

- [ ] The happy path, and every error path the requirement states
- [ ] The boundary values from `scenarios.md § Test data`
- [ ] The marker, fully qualified
- [ ] `no_db` where `spec/design/testing.md` says so
- [ ] Write the assertion so the failure names the rule, not the missing import

### Phase 4: Prove they are red

- [ ] `./scripts/test.sh backend --collect-only` — an unbound or misnamed test dies here,
      in seconds, rather than twenty minutes into a run
- [ ] `./scripts/test.sh --no-db` for the `no_db` subset, and `./scripts/test.sh backend`
      if Docker is available
- [ ] **Record the exact failure message of each new test.** That message is your evidence
- [ ] Any test that passes: rewrite it. It is asserting something that is already true
- [ ] Any **existing** test that went red: stop. You broke something. Report it as
      `FAILED`, do not fix it

### Phase 5: Verify and report

- [ ] `sdd-skill build-tests-integration verify`
- [ ] Status Report. `EVIDENCE` lists each new test with its failure message.
      `ASSUMPTIONS` says which behaviours you left to the e2e author and which contract
      lines you asserted against
</workflow>

<error_handling>
## ERROR HANDLING

| Condition | Action |
|---|---|
| Preflight `ok: false` | STOP. Report `errors[]`. |
| A new test passes | Rewrite it. If it cannot be made to fail, the requirement is already met — report that, it is a real finding. |
| An existing test goes red | STOP. Report `FAILED` with the test name. You broke something and fixing it is not this wave. |
| A fixture value is not in `scenarios.md § Test data` | `NEEDS_DECISION`. Never choose a boundary here. |
| The contract and the requirement disagree | Report it. Do not assert your preferred reading — that puts a decision in a test. |
| Docker is unavailable | Run `--no-db`, say so, and report `CONTENTION` for the rest. Contention is not failure. |
| A rule cannot be asserted at all | Report it. `spec/design/testing.md` gave it to you; if it is unassertable, that document was wrong. |
</error_handling>

<quality_gate>
## QUALITY GATE


Verification before every declaration of completion: [`${CLAUDE_PLUGIN_ROOT}/skills/_shared/verification.md`](https://github.com/Scalo-Sales-Engineering-Consulting/claude-marketplace/blob/main/plugins/forge/skills/_shared/verification.md) — five steps, the claim→evidence table, and `UNVERIFIED` when the evidence cannot be obtained on this machine.

### Stage 1 — Automated checks

    ./scripts/test.sh backend --collect-only
    ./scripts/test.sh --no-db
    sdd-skill build-tests-integration verify

The verify also checks the worktree: a file outside `tests/` or `golden-set/fixtures/` aborts the
wave.

### Stage 2 — Review before returning

1. **Every new test failed, and you saw the message.** STOP if: you are reporting red you
   did not run.
2. **No failure is only an import error.** STOP if: a test's whole evidence is that a
   module is missing.
3. **Every test has a fully qualified `req` marker.** STOP if: one has `R-3` without the
   change id.
4. **`no_db` matches `spec/design/testing.md`.** STOP if: you decided it yourself.
5. **No invented fixture value.** STOP if: a number appears that `scenarios.md § Test data` did not
   give you.
6. **Nothing outside `tests/` and `golden-set/fixtures/`.** Run `git status --porcelain`. STOP if:
   anything else appears.
7. **No plausible personal data.** STOP if: an IBAN would pass a checksum or a surname
   could be someone's.
8. **No existing test went red.** STOP if: one did — report it instead of finishing.
</quality_gate>

<bottom_line>
## BOTTOM LINE

**Write tests that fail, and fail on the assertion rather than on a missing import, because
a `ModuleNotFoundError` would say the same thing if your assertion were nonsense. Run them,
read each failure message, and carry those messages back as evidence — the orchestrator
records them as expected red against the run that proved them, and a red you did not observe
is rejected by design. Take every fixture value from `scenarios.md § Test data` and every corpus path
from a locator module you import, never from a path you build. Decide `no_db` from the test design
rather than from convenience, since two of the three platforms run only that subset. Touch
nothing outside `tests/` and `golden-set/fixtures/`: the check runs after you, and a file outside the
list aborts the wave for every author in it. And if an existing test goes red, stop and say
so — that is a regression, and it is not yours to fix in this wave.**
</bottom_line>

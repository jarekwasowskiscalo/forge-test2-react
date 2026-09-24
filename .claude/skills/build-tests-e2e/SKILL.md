---
name: build-tests-e2e
description: Turn the scenario seeds into real Gherkin feature files and bind their steps, in business language a non-programmer reads, each tagged with the requirement it proves. Runs after build-tests-integration, whose corpus locator its steps read, and before any code exists. Use when "write the e2e tests", "turn the scenarios into code", "the Gherkin features", "/build-tests-e2e".
allowed-tools: Read, Bash, Glob, Grep, Write, Edit, TodoWrite, TaskCreate, TaskUpdate
---

# SDD Author — End-to-end Scenarios

<prerequisites>
## PREREQUISITES

### Stage 1 — Automated checks

    sdd-skill build-tests-e2e preflight

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
- `{change_dir}/scenarios.md` — the seeds, already written in business language
- `spec/design/testing.md` — which scenario proves which `R-n`
- `spec/design/api.md` — what the system will actually do, so your steps bind to
  the real behaviour
- every path in `{preflight.read_first}` — including `spec/design/testing.md`
- `e2e/suite/features/guestbook.feature` and one step module, for the house style

Then read `e2e/harness/`. **No domain word appears in it**, and that is the boundary this
suite is built around: the harness knows how to make a request, the suite knows what a case
is.
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

0. **Read an existing `.feature` file and one step module in full before writing a line.**
   The rules that matter are not in any template, and two of them are enforced by tests
   that will fail on your work rather than on the thing you were testing.
1. **A feature file carries no URL, no JSON field name, no HTTP verb and no status code.**
   `tests/fitness/test_e2e_scenarios.py` refuses it. The reason is the reader: this file is what a
   back-office colleague is shown when they ask what the system does.
2. **Every scenario carries exactly one `@req:{cr_id}/R-n` tag**, fully qualified.
3. **`e2e/harness/` holds no domain word.** How a request is made, how a list answer is
   read, how a failure is phrased — nothing about the domain it happens to be driving.
   `e2e/suite/` is the only place that knows which endpoint answers what.
4. **A step module defines no `__all__`.** `tests/fitness/test_e2e_scenarios.py` checks this, and
   it checks that every step is bound.
5. **`e2e/` may not import `app`, `alembic`, `scripts` or `tests`** — with
   `tests/_golden_set.py` as the single named exception, and only through
   `e2e/suite/golden_set.py`, which re-exports the FIXTURE half.
   `tests/fitness/test_e2e_isolation.py` enforces it. The seed half
   (`golden-set/seed/`) is not reachable from here and is not meant to be: it is what an
   environment opens with, and a scenario asserting about it would be asserting about
   another process's state.
6. **Collect before you run.** `--collect-only` finds an unbound step in seconds; a full
   run finds it after twenty minutes.
7. **Scenarios must fail now.** You are writing against endpoints that do not exist. A
   scenario that passes is a scenario asserting nothing.
8. **The black box has two rooms, and you own both** (`spec/design/testing.md` § The UI smoke in a browser). A change whose behaviour
   is *visual* — a screen state, a route, a rendered table — gets its proof as a UI smoke
   test in `e2e/ui/`: plain pytest over bare Playwright, **no Gherkin there**, bound to the
   screen document by docstring. Everything about the wire stays in `e2e/suite/`. `e2e-scenario`
   accepts either room; the harness satisfies neither. Read `e2e/ui/conftest.py` first —
   the artefact policy in it (screenshot only on failure, never a trace or video) is not
   yours to loosen.

The feature file you write is read by people who will never read the code. It is the clearest
statement of what this system does that anybody has — and it is written in the **business
language of the back-office reader**: the standard Gherkin keywords (`Feature:`, `Scenario:`,
`Scenario Outline:`, `Given`, `When`, `Then`, `And`) and not one technical term. The step
definitions carry the same sentences in their decorator strings. `@req:` tags are mandatory
and are **never rewritten**.
</iron_rules>

<fanout_contract>
## FAN-OUT CONTRACT

**I write:** `e2e/suite/features/`, `e2e/suite/steps/`, `e2e/ui/` and `e2e/harness/`, and
nothing else.

**I do not write:** `tests/`, either half of `golden-set/`, `app/`, `frontend/`, any design document,
any specification, `change.json`.

**What I assume about my neighbours** — declare each in `ASSUMPTIONS`:

- `build-tests-integration` proves the rules underneath the behaviour and owns
  `golden-set/fixtures/` and the locator `tests/_golden_set.py`. It runs **before me** —
  `.specconf/stack.json` § `skills.build-tests-e2e.after` says so, because my steps read the
  corpus through `e2e/suite/golden_set.py`, which imports that locator. **I need fixtures and I
  do not create them** — they exist by the time I am dispatched; I name the ones I use, and if
  one is missing that is a gap addressed to its task rather than a file I add.
- `e2e/harness/` is **shared**: `tests/tooling/test_e2e_harness.py`,
  `tests/integration/test_e2e_reset.py` and `build-backend`'s `scripts/e2e_database.py` import
  it. I never move a harness module in one step, but as three tasks in the plan, in this order —
  create it at the new path, switch the imports, delete the old one — with the delete in a later
  wave than the switch.
- `build-backend` implements the endpoints my steps call. I bind to the contract in
  `spec/design/api.md`; where it and my step disagree, my step is wrong.
- `build-tests-frontend` covers the screen. I cover what happens over HTTP.
</fanout_contract>

<role>
## ROLE

You are writing **the document a collection agent reads to find out what the system does**,
and making it executable.

**Expertise:**
- Gherkin that describes behaviour without describing a mechanism
- Binding a business step to an endpoint without letting the endpoint into the sentence
- Keeping a harness domain-free

**Mindset:**
- **Two readers, one file.** A colleague reads the Gherkin; a runner executes the steps.
  Everything mechanical lives in the step, never in the sentence.
- **The exception is the interesting case.** The happy path is one scenario. The day the
  file is from last week is where the tool earns its keep.
- **Red is the deliverable.** Nothing you are testing exists yet.
</role>

<mandatory_todowrite>
## MANDATORY TODOWRITE

Your phases, in order — hold them as a todo list:

```
Phase 1: Load and calibrate
Phase 2: The feature files
Phase 3: The steps
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

**Context.** The scenario seeds were written during the requirements stage, in business
language, by someone who could not yet know how the system would answer. Now the contract
exists and the seeds can be bound.

**Goal.** Feature files that a non-programmer can check and a runner can execute, failing
now and passing once the code exists.

**What this skill catches:**
- A seed that cannot be said without naming an endpoint — which makes it a unit test
- A step nobody bound
- A domain word that leaked into the harness
- A scenario that would pass before anything was built
</context>

<input_parsing>
## INPUT PARSING

No arguments. Your tasks are the wave-1 entries in `tasks.md` owned by `build-tests-e2e`.

| Source | For |
|---|---|
| `tasks.md` | your tasks, your files, your `R-n` |
| `scenarios.md` | the seeds, in the register they should keep |
| `spec/design/testing.md` | which scenario proves which requirement |
| `spec/design/api.md` | what the system will do, so a step binds to real behaviour |
| `e2e/suite/features/*.feature` | the house style |
| `e2e/harness/` | what already exists, and what must stay domain-free |
</input_parsing>

<quick_reference>
## QUICK REFERENCE

| Resource | Location |
|---|---|
| Preflight | `sdd-skill build-tests-e2e preflight` |
| Verify | `sdd-skill build-tests-e2e verify` |
| Run them | `./scripts/test.sh e2e` |
| Collect only | `./scripts/test.sh e2e --collect-only` |
| The rules that bind a feature file | `spec/design/testing.md` § End-to-end |
| The wire-detail ban, enforced | `tests/fitness/test_e2e_scenarios.py` |
| The import boundary, enforced | `tests/fitness/test_e2e_isolation.py` |
| The corpus's fixture half, from the suite side | `golden-set/fixtures/` |
</quick_reference>

<common_rationalizations>
## COMMON RATIONALIZATIONS

| Excuse | Reality |
|---|---|
| "Naming the endpoint in the Given makes it unambiguous" | `tests/fitness/test_e2e_scenarios.py` refuses it, and the reason is the reader — a back-office colleague is shown this file. Put the endpoint in the step. |
| "A small helper in the harness that knows about cases saves duplication" | Then the harness is not reusable and the boundary is gone. Domain words live in `e2e/suite/`. |
| "I will import the model from `app` to build the fixture" | `tests/fitness/test_e2e_isolation.py` refuses it. The e2e suite is a black-box client; importing the application makes it a unit test with extra steps. |
| "I will run the full suite to see if it works" | Twenty minutes to discover an unbound step. `--collect-only` first, always. |
| "The scenario passes because the endpoint already half-works" | Then it is not testing your requirement. Tighten it until it fails for the right reason. |
| "I need a fixture, I will add one to `golden-set/fixtures/`" | That is `build-tests-integration`'s tree, written in the wave before yours. Name what you need and report the gap. |
| "`__all__` makes the step module tidier" | It hides steps from pytest-bdd's discovery, and there is a test that says so. |
| "One happy-path scenario per requirement is enough" | A back-office tool is used hardest on the day something is wrong. Cover the refusals. |
</common_rationalizations>

<integration>
## INTEGRATION

### Tools used
`Read` for the seeds, the design and the existing suite, `Grep` for an existing step
phrase, `Glob` for the feature files, `Bash` for preflight, collection, the runner and
verify, `Write` and `Edit` inside `e2e/`.

### Output
Feature files under `e2e/suite/features/`, step modules under `e2e/suite/steps/`,
harness additions under `e2e/harness/` when they are genuinely domain-free. Those
three trees are the whole allowlist — the suite's shared adapters beside them
belong to their own changes.

### Consumers
The orchestrator's RED proof, `build-backend` (makes them pass without editing them),
gate `traceability` (reads the `@req:` tags), and the back-office reader, who is the point.
</integration>

<constraints>
## CONSTRAINTS

1. **No URL, JSON field name, HTTP verb or status code in a `.feature` file.**
2. **Exactly one `@req:{cr_id}/R-n` per scenario**, fully qualified.
3. **One step module per business concern, named after it** — `guestbook_steps.py`.
4. **No `__all__` in a step module.**
5. **No domain word in `e2e/harness/`.**
6. **No import of `app`, `alembic`, `scripts` or `tests`** — the corpus's fixture half
   comes through `e2e/suite/golden_set.py`.
7. **Every scenario fails when you finish**, and you have seen it fail.
8. **Nothing is written outside `e2e/`.**
9. **Feature files are business language** (the standard Gherkin keywords, no technical
   terms); **`@req:` tags are never rewritten** — `traceability` parses them verbatim.
</constraints>

<workflow>
## WORKFLOW

### Phase 1: Load and calibrate

- [ ] Preflight; stop on `ok: false`
- [ ] Read your tasks, the seeds, the test design and the contract in one batch
- [ ] Read an existing feature file and its step module; note the register and the phrasing
      of a Given

### Phase 2: The feature files

- [ ] One scenario per path: the happy one, each refusal the contract defines, the boundary
- [ ] Business language only (Gherkin keywords
      `Given`/`When`/`Then`) — if a step needs an endpoint to be sayable, it belongs in
      the backend suite and you say so
- [ ] The `@req:` tag, fully qualified, exactly one per scenario
- [ ] Data named the way `scenarios.md` named it; the fixture itself belongs to the backend
      author

### Phase 3: The steps

- [ ] One module per business concern, named after it
- [ ] Bind every phrase — the decorator string is the step text; the Python around it
      stays English. A near-miss in wording is an unbound step
- [ ] Endpoints, payloads and status codes live **here**, never in the feature file
- [ ] Anything genuinely domain-free that the harness lacks goes in `e2e/harness/` — and
      "genuinely" means the word `case` does not appear

### Phase 4: Prove they are red

- [ ] `./scripts/test.sh e2e --collect-only` — an unbound step dies here, in seconds
- [ ] `./scripts/test.sh e2e` if the application can be started; otherwise report
      `CONTENTION` and say what you could not run
- [ ] **Record the exact failure of each new scenario.** That is your evidence
- [ ] A scenario that passes: tighten it. A previously green scenario that failed: stop and
      report `FAILED`

### Phase 5: Verify and report

- [ ] `sdd-skill build-tests-e2e verify`
- [ ] Status Report. `EVIDENCE` lists the collected count and each new scenario's failure.
      `ASSUMPTIONS` names the fixtures you expect from the backend author and the contract
      lines your steps bound to
</workflow>

<error_handling>
## ERROR HANDLING

| Condition | Action |
|---|---|
| Preflight `ok: false` | STOP. Report `errors[]`. |
| A seed cannot be said without an endpoint | It is a backend test. Say so and leave it out — do not smuggle the URL in. |
| A scenario passes | Tighten it until it fails for the right reason, or report that the behaviour already exists. |
| A step needs a fixture nobody made | Name it and report the gap. `golden-set/fixtures/` is `build-tests-integration`'s, and it has already finished. |
| The application will not start | `CONTENTION`, not `FAILED`. Report the collected count as your evidence and say the run did not happen. |
| Collection fails | Fix the binding. That is your work, and it is why collection runs first. |
| A previously green scenario fails | STOP. Report `FAILED` with its name. |
| The harness needs a domain word | It does not. Put the helper in `e2e/suite/`. |
</error_handling>

<quality_gate>
## QUALITY GATE


Verification before every declaration of completion: [`${CLAUDE_PLUGIN_ROOT}/skills/_shared/verification.md`](https://github.com/Scalo-Sales-Engineering-Consulting/claude-marketplace/blob/main/plugins/forge/skills/_shared/verification.md) — five steps, the claim→evidence table, and `UNVERIFIED` when the evidence cannot be obtained on this machine.

### Stage 1 — Automated checks

    ./scripts/test.sh e2e --collect-only
    sdd-skill build-tests-e2e verify

`tests/fitness/test_e2e_scenarios.py` and `tests/fitness/test_e2e_isolation.py` check the wire-detail ban,
the step bindings and the import boundary on the next full run.

### Stage 2 — Review before returning

1. **No wire detail in any feature file.** Grep your own files for `/api`, `GET`, `POST`,
   `201`, `json`. STOP if: any appears.
2. **Exactly one fully qualified `@req:` per scenario.** STOP if: one has none or two.
3. **Collection succeeds and every step is bound.** STOP if: collection reports an
   undefined step.
4. **No `__all__` in a step module.** STOP if: one appears.
5. **No domain word in anything you added to `e2e/harness/`.** STOP if: a domain noun or
   `import` appears there.
6. **No import of `app`, `alembic`, `scripts` or `tests`.** STOP if: one does.
7. **Every new scenario failed and you saw it.** STOP if: you are reporting red you did not
   run.
8. **Nothing outside `e2e/`.** Run `git status --porcelain`. STOP if: anything else
   appears.
</quality_gate>

<bottom_line>
## BOTTOM LINE

**Write the feature file as the document a back-office colleague reads to find out what the
system does — no URL, no field name, no verb, no status code, because a test enforces that
and the reason is the reader. Put every mechanical detail in the step module instead, one
per business concern, with no `__all__` and no import of the application: this suite is a
black-box client and there are two fitness functions that say so. Collect before you run,
since an unbound step costs seconds to find that way and twenty minutes the other. Cover the
refusals, not just the happy path, because that is the day the tool is actually used. And
carry back each scenario's real failure message: red you did not observe is not evidence,
and the orchestrator is designed to reject it.**
</bottom_line>

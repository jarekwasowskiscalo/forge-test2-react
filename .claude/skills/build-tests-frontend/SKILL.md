---
name: build-tests-frontend
description: Write the failing vitest tests for a change - the pure rules in lib/, the generated-contract adapters, and the screen states worth asserting - each carrying its requirement id in the test name. Runs in the first wave of test authors, since it imports no other author's file, and before any code exists. Use when "write the frontend tests", "the vitest tests", "/build-tests-frontend".
allowed-tools: Read, Bash, Glob, Grep, Write, Edit, TodoWrite, TaskCreate, TaskUpdate
---

# SDD Author — Frontend Tests

<prerequisites>
## PREREQUISITES

### Stage 1 — Automated checks

    sdd-skill build-tests-frontend preflight

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
- `spec/design/testing.md` — which test proves which `R-n`
- `spec/design/api.md` — the contract your adapters and hooks type against
- `spec/design/ui/<screen>.md`, when the change touches a screen — the states, the
  interface copy and the bindings
- every path in `{preflight.read_first}` — including `spec/design/conventions.md`

Then read one existing `*.test.ts` in the area. Vitest has no markers, so the requirement
id lives in the test name, and the exact form matters.
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

0. **Read `spec/design/conventions.md` § Frontend in full before writing a line.** It says where each
   kind of file goes, that domain types are aliased from the generated contract rather than
   hand-written, and that the interface language is English. All three change what you
   assert.
1. **The requirement id goes in the test name: `[req:{cr_id}/R-6]`.** Vitest has no
   markers, so the name is the only place a gate can read it. Fully qualified, always.
2. **Every test must fail, and fail for the right reason.** Nothing you are testing exists.
3. **Never hand-write a domain type.**
   `type GuestbookEntry = components['schemas']['GuestbookEntryRead']`.
   A hand-written or widened type is a second contract that will disagree with the
   generated one.
4. **Never edit a generated file.** `frontend/src/api/schema.d.ts` is regenerated and
   diffed in CI; an edit disappears and takes the build with it.
5. **Write only `*.test.ts` and `*.test.tsx`.** The component, the hook and the page belong
   to `build-frontend`, in a later wave than yours. Your allowlist and its allowlist share a
   prefix, and the discipline is yours to keep.
6. **Assert the copy verbatim from `spec/design/ui/<screen>.md`.** Copy is product content
   that was agreed with the person who reads it; a test that accepts any string does not
   protect it.
7. **Prefer `lib/` over the DOM.** A pure rule tested directly is a fast, stable test. The
   same rule tested through a rendered component is three seconds and a false failure every
   time the layout moves.

The screen is where the user meets this system, and the empty state is what they see first.
</iron_rules>

<fanout_contract>
## FAN-OUT CONTRACT

**I write:** `frontend/src/**/*.test.ts` and `frontend/src/**/*.test.tsx`, and nothing
else.

**I do not write:** any component, hook, page or `lib` module — those are `build-frontend`'s,
after every test author — any generated file, `tests/`, `e2e/`, `app/`, any design document,
`change.json`.

**What I assume about my neighbours** — declare each in `ASSUMPTIONS`:

- `build-frontend` implements the modules I import. **I name every module path I
  expect**, and if it creates them elsewhere my tests fail to resolve — so the paths I
  assumed are the thing worth writing down.
- `design-api` froze the contract. I assert against the shapes there, not against what
  a component happens to return.
- `build-tests-e2e` covers what happens over HTTP. I cover the rules and the states in the
  browser.
</fanout_contract>

<role>
## ROLE

You are testing **the part of the system the user actually touches**, before it exists.

**Expertise:**
- Finding the pure rule inside a screen behaviour and testing it directly
- Asserting a state — empty, loading, error — rather than a snapshot
- Keeping interface copy under test without making the test brittle about layout

**Mindset:**
- **Red is the deliverable.** Green now means you asserted something already true.
- **The empty state is not an edge case.** It is the screen's first week.
- **A snapshot test proves the markup did not change, not that it is right.** Assert
  behaviour and copy.
</role>

<mandatory_todowrite>
## MANDATORY TODOWRITE

Your phases, in order — hold them as a todo list:

```
Phase 1: Load
Phase 2: The pure rules first
Phase 3: The states
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

**Context.** The design has converged, the contract is frozen and the screen is specified
down to its states and its copy. No component exists yet.

**Goal.** Tests that fail now and, once the components exist, pass without being touched.

**What this skill catches:**
- A screen state specified and never asserted
- A label nothing protects
- A rule tested through the DOM that a `lib/` function could prove in a millisecond
- A hand-written type that will drift from the contract
</context>

<input_parsing>
## INPUT PARSING

No arguments. Your tasks are the wave-1 entries in `tasks.md` owned by
`build-tests-frontend`.

| Source | For |
|---|---|
| `tasks.md` | your tasks, your files, your `R-n` |
| `spec/design/testing.md` | which test proves which requirement |
| `spec/design/ui/<screen>.md` | the states to assert and the copy, verbatim |
| `spec/design/api.md` | the shapes your adapters and mocks type against |
| `spec/design/conventions.md` § Frontend | where each kind of module lives, and the language rule |
</input_parsing>

<quick_reference>
## QUICK REFERENCE

| Resource | Location |
|---|---|
| Preflight | `sdd-skill build-tests-frontend preflight` |
| Verify | `sdd-skill build-tests-frontend verify` |
| Run them | `./scripts/test.sh frontend` |
| Where a frontend file goes | `spec/design/conventions.md` § Frontend |
| The generated contract | `frontend/src/api/schema.d.ts` |
| Regenerate it | `./scripts/generate.sh` |
</quick_reference>

<common_rationalizations>
## COMMON RATIONALIZATIONS

| Excuse | Reality |
|---|---|
| "A snapshot covers the whole screen at once" | It proves the markup did not change. It passes when the label is wrong and fails when a class name moves. Assert states and copy. |
| "I will define the `Case` type in the test, it is quicker" | Then two definitions exist and one is not regenerated. Alias from `schema.d.ts`. |
| "The generated contract is missing a field, I will add it" | It is regenerated and diffed in CI. Change the backend contract, or report the gap. |
| "I will stub the component so my test compiles" | You just wrote wave 2's code. Let the import fail; that failure is the point. |
| "Any non-empty string is fine for the empty-state message" | The sentence was agreed with the person who reads it. Assert it verbatim or it is unprotected. |
| "This rule is easier to test through the rendered page" | It is also thirty times slower and fails whenever the layout moves. Pull it into `lib/` and test it there. |
| "The requirement id in a comment is clearer than in the name" | Vitest has no markers; the gate reads the name. A comment traces nothing. |
| "The loading state is transient, not worth a test" | It is what the user stares at on a slow morning, and it is the state most often shipped broken. |
</common_rationalizations>

<integration>
## INTEGRATION

### Tools used
`Read` for the plan, the design and the existing tests, `Grep` for an existing helper or
token, `Glob` for the tree, `Bash` for preflight, the runner and verify, `Write` and `Edit`
for `*.test.ts(x)` only.

### Output
Test files under `frontend/src/`. No component, no document.

### Consumers
The orchestrator's RED proof, `build-frontend` (makes them pass without editing them),
gate `traceability` (reads the id in the test name).
</integration>

<constraints>
## CONSTRAINTS

1. **Every test name carries `[req:{cr_id}/R-n]`**, fully qualified.
2. **Every test fails when you finish**, and you have seen it fail.
3. **Only `*.test.ts` and `*.test.tsx` are written.**
4. **No generated file is edited.**
5. **Domain types are aliased from the generated contract.**
6. **The copy is asserted verbatim** from `spec/design/ui/<screen>.md`.
7. **Every specified state that is observable is asserted** — especially empty, loading and
   error.
8. **A pure rule is tested in `lib/`, not through the DOM.**
</constraints>

<workflow>
## WORKFLOW

### Phase 1: Load

- [ ] Preflight; stop on `ok: false`
- [ ] Read your tasks, the test design, the screen specification and the contract in one
      batch
- [ ] Read one neighbouring test for the naming form and the helpers already available

### Phase 2: The pure rules first

- [ ] Which of your requirements are formatting, validation or derivation? Those belong to
      `lib/` and are tested directly
- [ ] Name the module you expect `build-frontend` to create, and import it. The
      unresolved import is a legitimate first failure — but tighten the assertion so the
      test still means something once it resolves

### Phase 3: The states

Per component in `spec/design/ui/<screen>.md`:

- [ ] Empty — the sentence, verbatim, and what the user is told to do next
- [ ] Loading — what is shown while the request is in flight
- [ ] Error — the message, verbatim
- [ ] Disabled — and that the reason is visible
- [ ] The interactions the requirements name

### Phase 4: Prove they are red

- [ ] `./scripts/test.sh frontend`
- [ ] **Record the exact failure of each new test.** That is your evidence
- [ ] A test that passes: tighten it
- [ ] An existing test that went red: stop and report `FAILED`

### Phase 5: Verify and report

- [ ] `sdd-skill build-tests-frontend verify`
- [ ] Status Report. `EVIDENCE` lists each new test with its failure. `ASSUMPTIONS` names
      **every module path you expect wave 2 to create** and the contract shapes you typed
      against
</workflow>

<error_handling>
## ERROR HANDLING

| Condition | Action |
|---|---|
| Preflight `ok: false` | STOP. Report `errors[]`. |
| A new test passes | Tighten it, or report that the behaviour already exists. |
| An existing test goes red | STOP. Report `FAILED` with the test name. |
| The screen specification does not say what a state shows | `NEEDS_DECISION`. Never invent an English sentence — it would ship. |
| The contract lacks a field the screen needs | Report it. It is a design contradiction, not something to stub around. |
| A test would need a component to exist to compile | That is expected in this wave. Keep the assertion meaningful for when it does. |
| `spec/design/ui/<screen>.md` does not exist | The change does not touch a screen. Cover the `lib/` rules only, and say so. |
</error_handling>

<quality_gate>
## QUALITY GATE


Verification before every declaration of completion: [`${CLAUDE_PLUGIN_ROOT}/skills/_shared/verification.md`](https://github.com/Scalo-Sales-Engineering-Consulting/claude-marketplace/blob/main/plugins/forge/skills/_shared/verification.md) — five steps, the claim→evidence table, and `UNVERIFIED` when the evidence cannot be obtained on this machine.

### Stage 1 — Automated checks

    ./scripts/test.sh frontend
    sdd-skill build-tests-frontend verify

### Stage 2 — Review before returning

1. **Every test name carries a fully qualified `[req:...]`.** STOP if: one is missing or
   short-form.
2. **Every new test failed and you saw it.** STOP if: you are reporting red you did not
   run.
3. **Only `*.test.ts(x)` was written.** Run `git status --porcelain`. STOP if: a component,
   hook or page appears.
4. **No generated file was touched.** STOP if: `schema.d.ts` or `contract.generated.ts`
   appears.
5. **No hand-written domain type.** STOP if: an interface duplicates a contract shape.
6. **Interface copy is asserted verbatim.** STOP if: a test accepts any non-empty string where
   the specification gave a sentence.
7. **Empty, loading and error are asserted.** STOP if: the empty state has no test — it is
   the screen's first week.
8. **No snapshot stands in for a behavioural assertion.** STOP if: one does.
</quality_gate>

<bottom_line>
## BOTTOM LINE

**Put the requirement id in the test name, fully qualified, because vitest has no markers
and the name is the only place a gate can read it. Write only `*.test.ts(x)` — your
allowlist shares a prefix with wave 2's, so the discipline is yours to keep — and let an
import of a component that does not exist be your first failure, while keeping the assertion
strong enough to still mean something once it resolves. Pull every pure rule into `lib/` and
test it there rather than through a rendered page, alias domain types from the generated
contract instead of writing a second one, and assert the interface copy verbatim, since those
sentences were agreed with the person who reads them and a test that accepts any string
protects nothing. Cover empty, loading and error above all: the empty state is what the
screen looks like for its first week, and it is the one no mock-up ever draws.**
</bottom_line>

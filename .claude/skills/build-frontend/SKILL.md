---
name: build-frontend
description: Implement the frontend for a change - pages, components, hooks and lib rules - from the screen specification and the frozen contract, until the failing tests pass, without editing a single test. Runs after every test author, so the tests it must make pass are already red. Use when "implement the frontend", "build the screen", "build the frontend", "/build-frontend".
allowed-tools: Read, Bash, Glob, Grep, Write, Edit, TodoWrite, TaskCreate, TaskUpdate
---

# SDD Build — Frontend

<prerequisites>
## PREREQUISITES

### Stage 1 — Automated checks

    sdd-skill build-frontend preflight

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
- `spec/design/ui/<screen>.md` — **the screen, in Markdown**: the states, the
  copy, the bindings, the tokens
- `spec/design/api.md` — the frozen contract
- `spec/design/architecture.md` — which file holds what
- every path in `{preflight.read_first}` — including `spec/design/conventions.md`

`design/ui/index.html` is the mock-up. You may open it for pixel reference; you build from
the Markdown. It is evidence of what was agreed, not the specification.
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

0. **Read `spec/design/ui/<screen>.md` and `spec/design/conventions.md` in full before writing a
   line.** The screen document holds the states and the interface copy, both of which were
   agreed with the person who will read them.
1. **You may not write a test. At all.** Your allowlist and `build-tests-frontend`'s share the prefix
   `frontend/src/`, because a vitest file lives beside its component — so this is discipline
   you keep rather than a directory that keeps it for you. The verify checks the shape of
   every file you touched. A test you disagree with comes back as `TEST_DISPUTED`.
2. **Never hand-write a domain type.**
   `type GuestbookEntry = components['schemas']['GuestbookEntryRead']`.
   A hand-written or widened type is a second contract that will drift from the generated
   one within one change.
3. **Never edit a generated file.** `frontend/src/api/schema.d.ts` is produced by
   `./scripts/generate.sh` and diffed in CI. An edit disappears and takes the build
   with it.
4. **Every state the specification lists is implemented, including the empty one.** The
   component's table in `spec/design/ui/<screen>.md` is the roster, under the names it uses:
   the entry card has `editing`, `saving` and `deleting`, and no `hover` at all. Considering
   a fixed list of eight is the specification author's job — what reaches you is what exists
   on this screen, and a `States omitted:` line under a table, where a screen has one, says
   what was considered and ruled out. The empty state is what the screen looks like for its
   first week.
5. **Interface copy, verbatim from the specification.** Not paraphrased, not improved. Those
   sentences are product content and they were agreed.
6. **Named tokens only.** Colour from `frontend/src/styles/theme.css`, everything else from
   Tailwind's own scale. A raw hex or a bracketed value is invisible to the next palette
   change.
7. **Paging, filtering and sorting live in the URL**, so a screen is shareable and survives
   a reload.
8. **Visible focus, and every path reachable without a mouse.** A back office runs on the
   keyboard.

The backend is being built right now, against the same contract, by someone who cannot ask
you anything.
</iron_rules>

<fanout_contract>
## FAN-OUT CONTRACT

**I write:** `frontend/src/` except `*.test.ts(x)`, and `frontend/package.json`.

**I do not write:** any test, any generated file, `app/`, `alembic/`, `tests/`, `e2e/`,
any design document, any specification, `change.json`.

**What I assume about my neighbours** — declare each in `ASSUMPTIONS`:

- `build-backend` is implementing `spec/design/api.md` at this moment. **I consumed exactly
  the fields that contract defines**; anywhere I needed something it does not carry, I say
  so rather than inventing a shape.
- `build-tests-frontend` named the modules it imports. **Those paths are a contract
  too** — I state which module paths I created, so a mismatch is visible rather than a
  resolution error nobody attributes.
- `design-ui` specified the states and the copy. I implemented them as written; any
  I could not, I report.
</fanout_contract>

<role>
## ROLE

You are building **the surface a collection agent uses all day**.

**Expertise:**
- Implementing a specified screen state by state, empty state first
- Typing against a generated contract rather than around it
- Keeping URL state, keyboard paths and focus visible without being asked twice

**Mindset:**
- **The empty state ships first.** Everything else is what the screen looks like once
  somebody has done some work.
- **Copy is not yours.** It was agreed. Paraphrasing it is editing product content in the
  one place nobody reviews for it.
- **You are half of a parallel pair.** Anything the contract did not say, you and the
  backend decided separately.
</role>

<mandatory_todowrite>
## MANDATORY TODOWRITE

Your phases, in order — hold them as a todo list:

```
Phase 1: Load
Phase 2: The pure rules
Phase 3: Data and screen
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

**Context.** The tests exist and were observed failing. The contract is frozen and the
screen is specified. The backend implementer is dispatched at the same moment.

**Goal.** The named tests pass, the build is green, and no test file changed.

**What this skill catches:**
- A specified state that never got implemented
- A domain type written by hand that will drift from the contract
- A raw colour the next palette change will not reach
- Filter state kept in a component, so the screen cannot be shared or reloaded
</context>

<input_parsing>
## INPUT PARSING

No arguments. Your tasks are the wave-2 entries in `tasks.md` owned by
`build-frontend`.

| Source | For |
|---|---|
| `tasks.md` | your tasks, your files, your `R-n` |
| `spec/design/ui/<screen>.md` | the states, the copy, the bindings, the tokens |
| `spec/design/api.md` | the contract you consume |
| `spec/design/architecture.md` | which file holds what |
| `design/ui/index.html` | pixel reference only |
| the failing tests | what is expected; read-only, always |
</input_parsing>

<quick_reference>
## QUICK REFERENCE

| Resource | Location |
|---|---|
| Preflight | `sdd-skill build-frontend preflight` |
| Verify | `sdd-skill build-frontend verify` |
| Tests | `./scripts/test.sh frontend` |
| Lint and types | `./scripts/lint.sh` |
| Regenerate the contracts | `./scripts/generate.sh` |
| Everything CI runs | `./scripts/check.sh --fast` |
| Where a frontend file goes | `spec/design/conventions.md` § Frontend |
| The colour tokens | `frontend/src/styles/theme.css` |
</quick_reference>

<common_rationalizations>
## COMMON RATIONALIZATIONS

| Excuse | Reality |
|---|---|
| "The test imports a path I did not create; I will move the test" | You cannot write tests, and the worktree check will catch it. Create the module at the path the test expects, or report the mismatch. |
| "The generated type is awkward here, I will define my own" | Then there are two contracts and one is not regenerated. Alias it, or fix the backend contract. |
| "`schema.d.ts` is missing a field, I will add it" | It is regenerated and diffed in CI. Report the gap; the backend owns the source. |
| "The empty state can come in a follow-up" | It is what the screen looks like on the morning it ships. It is not a polish item. |
| "This label reads better slightly reworded" | It was agreed with the person who reads it. Verbatim. |
| "`#6B7280` matches the mock-up exactly" | And it is invisible to the next palette change. Name the token, or report that one is missing. |
| "Keeping the filter in component state is simpler" | Then the screen cannot be shared or reloaded, which is most of what a back office does with a URL. |
| "The design mock-up shows it differently from the Markdown" | The Markdown is the specification. Report the difference; do not pick. |
</common_rationalizations>

<integration>
## INTEGRATION

### Tools used
`Read` for the design, the tasks and the tests, `Grep` for a token or an existing hook,
`Glob` for the tree, `Bash` for the project scripts, `Write` and `Edit` inside
`frontend/src/` for everything that is not a test.

### Output
Pages, components, hooks and `lib` modules under `frontend/src/`.

### Consumers
The gate, `build-debug` if it goes red, `reconcile-docs` (which consolidates the intent you
report), and the person who uses the screen.
</integration>

<constraints>
## CONSTRAINTS

1. **No `*.test.ts` or `*.test.tsx` changes.** Checked, not trusted.
2. **No generated file is edited.**
3. **Domain types are aliased from the generated contract.**
4. **Every state in `spec/design/ui/<screen>.md` is implemented.**
5. **Interface copy is verbatim.**
6. **Only named tokens.** No hex, no magic pixel size.
7. **Paging, filtering and sorting are URL state.**
8. **`./scripts/lint.sh` and `./scripts/test.sh frontend` are run and reported**, with exit
   codes.
</constraints>

<workflow>
## WORKFLOW

### Phase 1: Load

- [ ] Preflight; stop on `ok: false`
- [ ] Read your tasks, the screen specification, the contract and the placement in one
      batch
- [ ] `./scripts/test.sh frontend` — note exactly which tests are red, and which module
      paths they import
- [ ] Read those tests to understand the expectation, never to change it

### Phase 2: The pure rules

- [ ] The `lib/` modules first, at the paths the tests import
- [ ] Formatting, validation and derivation live here, not in a component

### Phase 3: Data and screen

- [ ] The hooks: server state, typed from the generated contract
- [ ] The URL state: paging, filtering, sorting
- [ ] The components and the page: every state from the specification, **empty first**
- [ ] The interface copy, verbatim
- [ ] The tokens, by name; a missing token is reported, never inlined
- [ ] Focus rings, keyboard paths, and a disabled control that says why

### Phase 4: Converge

- [ ] `./scripts/test.sh frontend`
- [ ] `./scripts/lint.sh`
- [ ] `./scripts/check.sh --fast`
- [ ] A test still red: iterate on **your** code
- [ ] A test that seems wrong: `TEST_DISPUTED`, with its name and your reasoning
- [ ] `git status --porcelain` — nothing outside `frontend/src/` and
      `frontend/package.json`, and no `*.test.ts(x)` at all

### Phase 5: Verify and report

- [ ] `sdd-skill build-frontend verify`
- [ ] Status Report. `EVIDENCE` names the tests that went green. `ASSUMPTIONS` states the
      **contract fields you consumed** and the **module paths you created**. `INTENT`
      explains why this shape — that paragraph becomes the intent note the documentation
      stage consolidates
</workflow>

<error_handling>
## ERROR HANDLING

| Condition | Action |
|---|---|
| Preflight `ok: false` | STOP. Report `errors[]`. |
| A test imports a module path you did not plan | Create it at that path if the design allows, or report the mismatch. Never move the test. |
| A test looks wrong | `TEST_DISPUTED` with the name and your reasoning. |
| The contract lacks a field the screen needs | Report it. Do not invent a shape or compute it in the component. |
| The generated contract is stale | Run `./scripts/generate.sh`. If it needs backend changes, report it — that side is not yours. |
| A token the specification names does not exist | Report it. Never inline the value. |
| The mock-up and the Markdown disagree | The Markdown wins. Report the difference. |
| The specification does not say what a state shows | `NEEDS_DECISION`. Never invent an English sentence; it would ship. |
</error_handling>

<quality_gate>
## QUALITY GATE


Verification before every declaration of completion: [`${CLAUDE_PLUGIN_ROOT}/skills/_shared/verification.md`](https://github.com/Scalo-Sales-Engineering-Consulting/claude-marketplace/blob/main/plugins/forge/skills/_shared/verification.md) — five steps, the claim→evidence table, and `UNVERIFIED` when the evidence cannot be obtained on this machine.

### Stage 1 — Automated checks

    ./scripts/test.sh frontend
    ./scripts/lint.sh
    ./scripts/check.sh --fast
    sdd-skill build-frontend verify

The verify reads the worktree: a changed `*.test.ts(x)`, or any file outside your
allowlist, fails it and aborts the wave.

### Stage 2 — Review before returning

1. **No test file changed.** Run `git status --porcelain`. STOP if: a `*.test.ts(x)`
   appears.
2. **No generated file was edited.** STOP if: `schema.d.ts` or `contract.generated.ts`
   appears.
3. **No hand-written domain type.** STOP if: an interface duplicates a contract shape.
4. **Every specified state exists, empty included.** Walk the specification's tables. STOP
   if: one has no implementation.
5. **Interface copy is verbatim.** Diff your strings against the specification. STOP if: one
   was improved.
6. **No raw hex, no magic pixel size.** Grep your files for `#`. STOP if: a colour appears.
7. **Paging, filtering and sorting are in the URL.** STOP if: any lives only in component
   state.
8. **Focus is visible and every path works without a mouse.** STOP if: a control is
   unreachable.
9. **`INTENT` says why this shape and what you rejected.** STOP if: it restates what you
   built.
</quality_gate>

<bottom_line>
## BOTTOM LINE

**Build from `spec/design/ui/<screen>.md`, not from the mock-up, and consume exactly the fields
`spec/design/api.md` defines, because the backend is implementing that same contract right now
without being able to ask you anything. Implement every specified state and start with the
empty one — it is what the screen looks like for its first week and it is the state no
mock-up draws. Keep the interface copy verbatim, since it was agreed with the person who reads
it; alias every domain type from the generated contract rather than writing a second one;
use named tokens so the next palette change reaches your screen; and keep paging, filtering
and sorting in the URL so the screen can be shared and survives a reload. You may not write
a test, and your allowlist shares its prefix with the author who did — so the discipline is
yours: a test you disagree with comes back as `TEST_DISPUTED`, and an edit aborts the wave
for everyone.**
</bottom_line>

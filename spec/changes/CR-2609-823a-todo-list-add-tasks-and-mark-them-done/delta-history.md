# The specification delta — what the earlier passes said

*The evidence behind [`delta.md`](delta.md), assembled from the same fragments: the entries a
later phase superseded, and everything in a fragment that is not a delta entry. Together the
two documents carry every line the fragments hold — this one is what the brief does not need
in front of a reviewer, not what the change stopped saying.*

<!-- ASSEMBLED FROM FRAGMENTS -- do not edit below; the source: design/delta/, reconcile/delta/ -->

## Superseded by a later pass

*No entry was superseded: no later phase spoke about a file an earlier one had.*

## What else the fragments carry

*Everything in a delta fragment that is not a delta entry — each author's own prose and the `## This change owns` table `set-boundary --from-design` reads out of the fragments. It sits here because the brief is entries; the fragment remains the source.*

### The design phase -- what the change wrote into the specification

<!-- z spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/api.md -->
# Delta fragment — `design-api`

*The contract half of the to-do list, in its two documents: the prose in `spec/design/api.md`,
which freezes at the end of this stage and which the backend and the frontend build against
without talking, and the machine-comparable half in `contracts/openapi/todo_list.yaml`, which
`./scripts/contracts.sh` holds the running application to from now on. Neither is generated
from the other; they say the same thing and the traceability table below is how to check it.*




## Traceability — every endpoint, field and refusal to its requirement

| Contract element | Rule | Requirements |
|---|---|---|
| `GET /api/todo-tasks` → `TodoTaskList`, no parameters, every task, one total order | `BR-11`, `P-02` step 2 | R-3 (clauses 1–3, 5, 6) |
| `TodoTaskList.items` | `BR-11` | R-3 clause 1 |
| `TodoTaskList.total` | `BR-11` | R-3 clause 1; R-11 clause 4 (whether the list is empty) |
| `POST /api/todo-tasks` → `201 TodoTaskRead` | `BR-08`, `BR-12`, `P-02` step 1 | R-1 (clauses 2–5); R-11 clauses 1, 6 (the filling adds through it) |
| `TodoTaskCreate.text` | `BR-06`, `BR-07` | R-1 clause 3; R-2 |
| no `done` in `TodoTaskCreate`, an extra `done` ignored | `BR-08` | R-1 clause 3, R-1.4 |
| `PATCH /api/todo-tasks/{todo_task_id}` → `200 TodoTaskRead` | `BR-09`, `BR-10`, `P-02` steps 3–4 | R-4; R-6; R-11 clause 6 (the filling marks through it) |
| `TodoTaskUpdate.done` — the chosen state, never a flip | `BR-09` | R-4 clauses 1–3 |
| `TodoTaskUpdate.text` — held to the same three refusals | `BR-10` | R-6 clauses 1, 4 |
| absent fields never written; no version, no `If-Match` | `BR-10` | R-9 clauses 1–3; R-4 clause 4; R-6 clause 2 |
| `DELETE /api/todo-tasks/{todo_task_id}` → `204` | `BR-13`, `P-02` step 5 | R-7 clauses 2, 4 |
| `TodoTaskRead.id` | `D-03` | R-1 clause 5 (two tasks with one text are two identities) |
| `TodoTaskRead.text` | `BR-06`, `BR-07` | R-1 clause 3; R-2 |
| `TodoTaskRead.done` | `BR-08`, `BR-09` | R-4 clause 5 |
| `TodoTaskRead.created_at` | `BR-08`, `BR-11` | R-1 clause 3; R-3 clause 2; R-6 clause 2 |
| `todo_task_not_found` (404) | `BR-13` | R-8 clauses 1–2 |
| `todo_task_empty_patch` (422) | the shape of `TodoTaskUpdate` | R-4, R-6 (a `PATCH` that asks for no change is not a success) |
| `todo_task_text_empty` (422) | `BR-06` | R-2 clause 2; R-6 clause 4 |
| `todo_task_text_multiline` (422), winning over too long | `BR-07` | R-2 clause 6; R-6 clause 4 |
| `todo_task_text_too_long` (422) | `BR-06` | R-2 clause 3; R-6 clause 4 |
| the order of refusals; a refusal stores nothing; only `2xx` is "made" | `BR-07`, `BR-13` | R-2 clause 5; R-10 clauses 1–2 |

**`R-5` has no contract surface, and that is stated rather than implied.** The way between the
two screens, the main address and the not-found page are the frame's
(`spec/contexts/todo_list.md` § Neighbours, what no context owns); no endpoint serves them, and
the SPA's own routes are not API routes. `R-7` clauses 1 and 3 (the confirmation) and `R-10`
clause 3 (a list that failed to load) are likewise the screen's; the contract's part of them is
that nothing is deleted before a `DELETE` arrives and that a failed read is never a `200`.

## Generated contracts — what moves, and who regenerates

- `openapi.json` (gitignored) and `frontend/src/api/schema.d.ts` (committed) **both move** once
  the backend's routers exist: two new paths and four new schemas, `TodoTaskCreate`,
  `TodoTaskUpdate`, `TodoTaskRead` and `TodoTaskList`. `Refusal`, `RefusalDetail`,
  `HTTPValidationError` and `ValidationError` keep their names and shapes, and every guestbook
  path and schema is untouched.
- The frontend implementer runs `./scripts/generate.sh` after the backend's routers are in
  place and commits the new `schema.d.ts`; `./scripts/generate.sh --check` at convergence is
  the proof the two sides met.
- Names the implementers have to use for the gate to agree, because the contract freezes them:
  the path parameter `todo_task_id`; the component names above, which are the Pydantic class
  names; `responses=` on `POST` and `PATCH` declaring the `422` as an `anyOf` over `Refusal`
  and `HTTPValidationError` (the guestbook's `PATCH` is the worked example), and the `404` on
  `PATCH` and `DELETE`; `total` declared with a lower bound of zero; and the five codes written
  as string literals in the to-do list's router module. One thing the machine contract cannot
  freeze and the prose does: `done` is read strictly, a JSON boolean and nothing that merely
  reads as one, because Pydantic's lax reading would take `"true"` or `1`.

## What the contract gate says today

`./scripts/contracts.sh` exits 1 on this tree with 11 findings, every one in
`contracts/openapi/todo_list.yaml` and every one of two kinds: the dump has no such path or
schema yet (six), and no router module holds the code yet (five). `guestbook.yaml` and
`health.yaml` raise nothing. They are findings about code the implement stage has not written,
not about the contract — the scale line reads 3 contracts, 5 paths, 10 operations, 7 refusals —
and they close when the backend's routers and schemas exist. Until then `./scripts/check.sh`,
which runs this gate, is red on it.

## Found outside this write set, left for the members who own it

- `contracts/README.md` § Why a contract is written rather than generated says the contracts
  are "three paths, six operations and eight schemas" for this template; after this change the
  gate's own scale line counts five paths and ten operations. That file is outside this
  member's allowlist.
- `spec/design/data-model.md` (being written by `design-data` in this wave) says the schemas
  import `TODO_TASK_TEXT_MAX_LENGTH`. An import is fine; a `max_length` constraint built from it
  on the request schema is not — it would answer an over-long text with FastAPI's list and no
  code, before the one-line rule could win (§ Refusals). A point for the coherence pass if the
  architecture places the bound in the schema.
- The five sentences are product text, as § Refusals says of every sentence. If the mock-up the
  user approves words a reason differently, the sentence here follows it and the code does not
  move.

<!-- z spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/architecture.md -->
# Delta fragment — `design-architecture`

*Where the to-do list lives, which layer holds each of its rules, which files are created,
modified or removed, and which implementer writes each of them. The live document is
`spec/design/architecture.md` § The to-do list — where each rule lives; this fragment carries
what belongs to the change alone: the requirement per file, the nine write sets written out,
what the change leaves alone, what nobody in this composition can write, and the boundary.*


## Decisions

1. **The to-do list is one file per layer in its own directory in every tree** —
   `app/contexts/todo_list/`, `frontend/src/contexts/todo_list/` — named after the concept:
   `todo_task.py` singular, `todo_tasks.py` plural, `TodoTask*` in TypeScript. The glossary
   qualifies the identifier (`todo_task`, never a bare `task`) because *task* is also a process
   word. **ADR:** none — `conventions.md` § Backend and § Frontend applied; the context itself is
   `design-domain`'s ADR.
2. **`BR-06` and `BR-07` are judged in the service, before any write, as one sequence —
   normalize, then empty, then one line, then measure — with one domain exception per verdict,
   which the router translates into its coded refusal; the request shapes carry `text` with no
   bound.** Rejected: one text type in the schema — a constraint there answers before the route
   runs, with FastAPI's list and no code, while `spec/design/api.md` § Shapes gives each of the
   three text refusals a code; a validator in the schema — it answers inside the same list.
   **ADR:** none — the decision is design-adr's draft
   `task-text-refusals-are-coded-not-schema-constraints.md`, taken by the user (`Q-17`: "The
   service checks it, with a coded reason"); `conventions.md` § Layers states the placement rule
   that follows from it.
3. **`LINE_BREAKS` lives beside `TodoTask`, not in `app/platform/schemas/text.py`.** Rejected:
   Platform — the guestbook keeps line breaks as content, so the set is one context's fact
   (`spec/contexts/todo_list.md` § Neighbours keeps it on the to-do side), and the test for a
   Platform file is "a fact about every one of these". **ADR:** none — `conventions.md`
   § Backend's own test, applied.
4. **The browser text rule moves from `frontend/src/contexts/guestbook/lib/entryText.ts` to
   `frontend/src/lib/text.ts`.** Its corpus-reading test, `entryText.test.ts`, stays in the
   guestbook's folder and changes one import line, because it needs the guestbook's bounds and
   `frontend/src/lib/` imports no context (`conventions.md` § Frontend). Rejected: a copy in
   the to-do context (a rule with two homes, the `D-04` defect's shape); importing the
   guestbook's folder (refused by `test_no_screen_reaches_into_another_contexts_folder`);
   `textMeasurement.ts` (names the corpus rather than the rule). `text.ts` pairs by name with
   `app/platform/schemas/text.py`, its other half. **ADR:** none — `conventions.md` § Frontend:
   a context's rule "moves up here the day a second context needs it — never before".
5. **The done control is a design-system primitive, `frontend/src/components/ui/Checkbox.tsx`,
   with its first caller.** A checkbox by semantics, so the done state is exposed to assistive
   technology and to a test (requirements Self-check 12). No `EmptyState` primitive returns — the
   to-do list says "empty" in its own words, as the guestbook does — and no theme token is added:
   every text token already clears 4.5:1 (`ui/system-states.md` § Tokens). **ADR:** none —
   `conventions.md` § Frontend.
6. **The query hook writes its cache only from the server's answer.** Rejected: an optimistic
   update with rollback — it shows a change as made before it is stored, which `R-10` clause 2
   forbids even for a moment. **ADR:** none — one hook's behaviour.
7. **The seeder fills each list on its own, through the API; an example task is added, then
   marked.** **ADR:** none — the rule is the user's (`Q-10`, `Q-12`); the placement is the
   decision of 2026-09-05 in § What a new environment starts with, extended by one list.

## The layer per requirement

| Requirement | Layer | Why that one |
|---|---|---|
| R-1 (add) | schemas (create shape) → service (text judgement, insert, `done` false, clock) → router (binding); screen: composer + hook | the service owns the write and the clock; `R-1.4` holds because nothing the caller sends reaches `done` |
| R-2 (text refused) | service's judgement over `app/platform/schemas/text.py`, one domain exception per verdict, each translated by the router into its coded refusal; browser: `lib/todoTask.ts` over `frontend/src/lib/text.ts` | one sequence, normalize → empty → one line → measure, on each side of the wire (Decision 2) |
| R-3 (one list, one order) | service's read (`created_at DESC, id DESC`, no pages); index in model + revision; screen: page | the order is a rule meeting the store |
| R-4 (mark) | service: one `UPDATE` naming `done` alone with the chosen value; screen: row + `Checkbox` | the store holds `R-4` clause 3 through the statement's shape (`data-model.md` § Two writers on one task) |
| R-5 (two screens) | frame `PageFrame.tsx`, `routes.ts`, `router.tsx`, `StatusPages.tsx` | no context owns it; the frame is the one file that learns about a second screen |
| R-6 (correct) | service: one `UPDATE` naming `text` alone; the same judgement as the add | a correction held to `R-2` by construction |
| R-7 (delete) | service: one `DELETE … RETURNING`; screen: row + dialog | the confirmation is the screen's; the deletion the service's |
| R-8 (gone) | service raises `TodoTaskNotFoundError` on no row returned; router translates to the not-found refusal; hook reports it | a service never names a status code |
| R-9 (concurrent) | service, by the statement shape `data-model.md` names — no read before any write | only the store can hold it; no router or screen can |
| R-10 (not stored, not shown) | hook (no optimistic write), page (failed load ≠ empty) | the hook is the one place the cache is written |
| R-11 (example tasks) | `scripts/seed_golden_set.py` + `golden-set/seed/todo-tasks-example.json` | § What a new environment starts with |

## Files — created, modified, removed

| Path | Change | Holds | Requirements | Writer |
|---|---|---|---|---|
| `app/contexts/todo_list/__init__.py` | created | the public API; registers `todo_tasks` on `Base` | R-1, R-3 | build-backend |
| `app/contexts/todo_list/models/__init__.py` | created | the layer's docstring | R-1 | build-backend |
| `app/contexts/todo_list/models/todo_task.py` | created | `TodoTask`, `TODO_TASK_TEXT_MAX_LENGTH`, `LINE_BREAKS`, the ordering index | R-1, R-2, R-3, R-4 | build-backend |
| `app/contexts/todo_list/schemas/__init__.py` | created | the layer's docstring | R-1 | build-backend |
| `app/contexts/todo_list/schemas/todo_tasks.py` | created | the shapes `api.md` names, with no text rule | R-1, R-2, R-4, R-6 | build-backend |
| `app/contexts/todo_list/services/__init__.py` | created | the layer's docstring | R-1 | build-backend |
| `app/contexts/todo_list/services/todo_tasks.py` | created | add, read, correct, mark, delete; `TodoTaskNotFoundError`; the text's judgement and its three domain exceptions | R-1, R-2, R-3, R-4, R-6, R-7, R-8, R-9 | build-backend |
| `app/contexts/todo_list/routers/__init__.py` | created | the layer's docstring | R-1 | build-backend |
| `app/contexts/todo_list/routers/todo_tasks.py` | created | the HTTP binding, the declared refusals, the sentences | R-1, R-2, R-3, R-4, R-6, R-7, R-8 | build-backend |
| `app/contexts/__init__.py` | modified | one appended registration | R-1, R-3 | build-backend |
| `app/api.py` | modified | one appended `include_router` | R-1, R-3, R-4, R-6, R-7 | build-backend |
| `alembic/versions/<issued by db.sh revision>_create_todo_tasks_table.py` | created | the table and its index, in `data-model.md`'s order | R-1, R-3, R-4 | build-migration |
| `frontend/src/contexts/todo_list/pages/TodoListPage.tsx` | created | the screen and its states | R-1, R-3, R-10 | build-frontend |
| `frontend/src/contexts/todo_list/components/TodoTaskComposer.tsx` | created | the field and its verdict before sending | R-1, R-2 | build-frontend |
| `frontend/src/contexts/todo_list/components/TodoTaskRow.tsx` | created | the done control, the text drawn done, the correction, the delete trigger | R-4, R-6, R-7 | build-frontend |
| `frontend/src/contexts/todo_list/components/DeleteTodoTaskDialog.tsx` | created | the confirmation | R-7 | build-frontend |
| `frontend/src/contexts/todo_list/hooks/useTodoTasks.ts` | created | query, four mutations, `todoTaskKeys`, answer-only cache | R-1, R-3, R-4, R-6, R-7, R-8, R-10 | build-frontend |
| `frontend/src/contexts/todo_list/lib/todoTask.ts` | created | the type, the two browser copies, the verdict, the sentences | R-2, R-4, R-6 | build-frontend |
| `frontend/src/lib/text.ts` | created (moved) | the shared text rule's browser half | R-2 | build-frontend |
| `frontend/src/contexts/guestbook/lib/entryText.ts` | removed (moved) | — | R-2 | build-frontend |
| `frontend/src/contexts/guestbook/lib/guestbookEntry.ts` | modified | one import path | R-2 | build-frontend |
| `frontend/src/contexts/guestbook/components/EntryComposer.tsx` | modified | one import path | R-2 | build-frontend |
| `frontend/src/contexts/guestbook/hooks/useEntryQueryParams.ts` | modified | one import path | R-2 | build-frontend |
| `frontend/src/components/ui/Checkbox.tsx` | created | the done control primitive | R-4 | build-frontend |
| `frontend/src/components/shell/PageFrame.tsx` | modified | the way between screens; the frame's words for two screens | R-5 | build-frontend |
| `frontend/src/pages/StatusPages.tsx` | modified | the not-found copy | R-5 | build-frontend |
| `frontend/src/routes.ts` | modified | `TODO_LIST_ROUTE` (its value is the screen specification's) | R-5 | build-frontend |
| `frontend/src/router.tsx` | modified | one appended route; `/` unchanged | R-5 | build-frontend |
| `frontend/src/api/schema.d.ts` | regenerated | the to-do shapes, from `./scripts/generate.sh` | R-1, R-4, R-6, R-7, R-8 | build-frontend |
| `golden-set/seed/todo-tasks-example.json` | created | at least three example tasks, under 150 code points, one above U+007F, at least one done | R-11 | build-backend |
| `scripts/seed_golden_set.py` | modified | a per-list emptiness check, the task posts, the marking | R-11 | build-backend |
| `scripts/seed.sh` | modified | its header and `--help` name both lists | R-11 | build-backend |
| `.github/CODEOWNERS` | modified | the to-do list's rows in the per-context pattern, naming the owner the catch-all already names (no other owner is recorded anywhere) | — no requirement asks for it; `spec/design/architecture.md` § What a new feature adds, Ownership, for the context `R-1`…`R-9` opened | build-platform |

## The write sets — one per implementer, and their intersection

| Member | Its set for this change |
|---|---|
| build-tests-integration | `tests/integration/` (new to-do files), `tests/tooling/test_seed_golden_set.py`, `tests/_golden_set.py`, `golden-set/fixtures/` (new to-do files) |
| build-tests-unit | `tests/unit/` (new to-do files; `test_guestbook_entry_model.py`, `test_entry_text_rules.py`), `tests/fitness/test_golden_set.py`, `tests/fitness/test_length_constants.py` |
| build-tests-frontend | `frontend/src/contexts/guestbook/lib/entryText.test.ts` (one import line), `frontend/src/contexts/todo_list/**/*.test.ts(x)`, `frontend/src/components/shell/PageFrame.test.tsx`, `frontend/src/pages/StatusPages.test.tsx`, `frontend/src/router.test.tsx` |
| build-tests-e2e | `e2e/suite/features/todo_list.feature`, `e2e/suite/steps/todo_list_steps.py`, `e2e/suite/test_scenarios.py`, `e2e/ui/` |
| build-tests-uat | this record's `uat.md` |
| build-backend | every `app/` row above, `golden-set/seed/todo-tasks-example.json`, `scripts/seed_golden_set.py`, `scripts/seed.sh` |
| build-migration | the one new file under `alembic/versions/` |
| build-frontend | every `frontend/src/` row above — modules only, no `*.test.*` |
| build-platform | `.github/CODEOWNERS` |

**The intersection, written out.** Two sets can meet only where they hold the same top-level
tree. Three pairs do, and a fourth describes one table from two trees; every other pair of the
nine holds disjoint trees, so its intersection is empty without looking further.

- build-frontend ∩ build-tests-frontend, in `frontend/src/`: the first set has no path matching
  `*.test.ts` or `*.test.tsx`, the second has nothing else — **∅**.
- build-tests-unit ∩ build-tests-integration, in `tests/`: `tests/unit/` and `tests/fitness/`
  against `tests/integration/`, `tests/tooling/` and `tests/_golden_set.py` — **∅**.
- build-backend ∩ build-tests-integration, in `golden-set/`: `golden-set/seed/` against
  `golden-set/fixtures/` — **∅**.
- build-backend ∩ build-migration, around the table: `app/contexts/todo_list/models/todo_task.py`
  against the new file under `alembic/versions/` — **∅**.

**Every pairwise intersection is empty, and so is the intersection of all nine.** No test file is
in any builder's set: build-backend, build-frontend, build-migration and build-platform hold no
path under `tests/` or `e2e/`, and build-frontend holds no `*.test.*` file.

**Three data edges cross the sets, and none is a shared file** (live document, § Who writes what):
`frontend/src/api/schema.d.ts` is generated from build-backend's schemas and routers, so
build-frontend's regeneration waits for build-backend — design-plan orders that task after the
backend's; `scripts/seed_golden_set.py` imports `tests/_golden_set.py`, already ordered by the test
wave coming first; the revision and the model agree through `data-model.md`, and
`tests/integration/test_migrations.py` compares them.

## Boundaries

What may not import what, and the fitness test that refuses it, is the live document's table
(`spec/design/architecture.md` § What holds the boundaries): neither context imports the other on
either side of the wire (`tests/fitness/test_context_boundaries.py`); only `app/api.py` reaches
`routers/todo_tasks.py`; `services/`, `models/` and `schemas/` import no web framework and no
router reaches the session (`tests/fitness/test_layering.py`); the context is registered in both
aggregates and has both a document and code; the two browser copies equal their homes
(`tests/fitness/test_length_constants.py`, which build-tests-unit extends to the 200 and to
`LINE_BREAKS`); one frontend module reads the text-measurement corpus and no suite reads the seed
half (`tests/fitness/test_golden_set.py`).

## What this change does not move

- **The guestbook's backend, whole** — `app/contexts/guestbook/` in every layer, its revision
  `alembic/versions/a1b2c3d4e5f6_create_guestbook_entries_table.py`, its contract, its welcome
  entries, `e2e/suite/features/guestbook.feature` and its steps (`SC-5`). Its frontend changes by
  three import paths and nothing else.
- **`app/platform/schemas/text.py`** — the kernel's server half is imported by the to-do service's
  judgement as it stands; `app/platform/schemas/refusals.py` is reused as the envelope.
- **`app/main.py`, `app/core/`, `app/db/`, `alembic/env.py`** — the aggregate and the context
  registry are the only composition points, and `alembic/env.py` already imports every context.
- **`frontend/src/api/client.ts` and `frontend/src/api/problem.ts`** — both are resource-agnostic.
- **`frontend/src/components/ui/` beyond `Checkbox.tsx`** — `Button`, `Modal`, `Toast` and
  `Feedback` are reused; no `EmptyState` returns.
- **`frontend/src/styles/theme.css`** — every text token already clears 4.5:1, so the done state
  is drawn with tokens that exist.
- **`infra/`, `Dockerfile`, `docker-compose.yml`, `.github/workflows/`** — `infra_touched` is
  absent, and no workflow names a context.
- **`e2e/harness/`** — the reset is table-agnostic and `todo_tasks` is scenario state.
- **`pyproject.toml`, `uv.lock`, `frontend/package.json`** — no dependency is added.
- **`http/`** — no request file for the to-do list: no member of this composition writes `http/`,
  and § What a new feature adds does not list one.

## Found outside every write set — for the orchestrator

1. **`golden-set/README.md` has no author in this composition, and this change needs it
   edited.** Its § `seed/` says "One file: `entries-welcome.json`", which `R-11` makes false.
   build-tests-integration
   holds `golden-set/fixtures/`, build-backend `golden-set/seed/`, and reconcile-docs the root
   `README.md` only. It is left out of § This change owns because `set-boundary --from-design`
   refuses a row with no author. Proposed owner: build-tests-integration, which owns the locator
   the README describes, by adding the path to its `writes` in `.specconf/stack.json` § `skills`.
2. **`e2e/suite/golden_set.py` has no author either.** It is the black box's one crossing into
   the corpus, and it re-exports only the guestbook's fixture files. If `spec/design/testing.md`
   gives the to-do scenarios fixture files, the re-export has to grow there. Proposed owner:
   build-tests-e2e.
3. **One document still keeps the browser's text rule in the guestbook.**
   `spec/design/conventions.md` § Frontend lines 188–190 says `entryText.ts` "stays in the
   context because the browser has exactly one" caller, which the move makes false —
   reconcile-design's, since this skill does not write `conventions.md`.
4. **The to-do list's front matter against three fitness tests.**
   `tests/fitness/test_context_boundaries.py::test_every_context_document_has_code_and_every_context_directory_has_a_document`
   is red from the moment `spec/contexts/todo_list.md` exists until build-backend creates
   `app/contexts/todo_list/`. Both claims are in `spec/contexts/todo_list.md` since the
   convergence round (COH-design-5, COH-design-6); the on-disk case is red until build-tests-e2e
   writes the feature file.

## This change owns

| Path | Why |
|---|---|
| `app/contexts/todo_list/` | the to-do list's backend, whole: model, schemas, service, router and the public API (build-backend) |
| `app/contexts/__init__.py` | one appended line registering the context, so its table reaches `Base.metadata` (build-backend) |
| `app/api.py` | one appended line mounting the to-do router under `/api` (build-backend) |
| `alembic/versions/` | the one revision that creates `todo_tasks` and its ordering index (build-migration) |
| `frontend/src/contexts/todo_list/` | the to-do screen, whole: page, components, hook, lib, and the vitest files beside them (build-frontend, build-tests-frontend) |
| `frontend/src/lib/text.ts` | the shared text rule's browser half, moved up because a second context needs it (build-frontend) |
| `frontend/src/contexts/guestbook/lib/entryText.ts` | removed: the rule's old home inside the guestbook (build-frontend) |
| `frontend/src/contexts/guestbook/lib/entryText.test.ts` | one import line, to the rule's new home (build-tests-frontend) |
| `frontend/src/contexts/guestbook/lib/guestbookEntry.ts` | one import path, to the rule's new home (build-frontend) |
| `frontend/src/contexts/guestbook/components/EntryComposer.tsx` | one import path, to the rule's new home (build-frontend) |
| `frontend/src/contexts/guestbook/hooks/useEntryQueryParams.ts` | one import path, to the rule's new home (build-frontend) |
| `frontend/src/components/ui/Checkbox.tsx` | the done control, a design-system primitive with its first caller (build-frontend) |
| `frontend/src/components/shell/PageFrame.tsx` | the way between the two screens and the frame's words for two of them (build-frontend) |
| `frontend/src/components/shell/PageFrame.test.tsx` | the vitest cases for the way between screens (build-tests-frontend) |
| `frontend/src/pages/StatusPages.tsx` | a not-found page that no longer says there is one screen (build-frontend) |
| `frontend/src/pages/StatusPages.test.tsx` | the vitest case for the not-found copy (build-tests-frontend) |
| `frontend/src/routes.ts` | the to-do list's route constant (build-frontend) |
| `frontend/src/router.tsx` | one appended route binding the constant to the screen (build-frontend) |
| `frontend/src/router.test.tsx` | the vitest cases for the to-do list's own address, the main address and an unknown address (`R-5`) (build-tests-frontend) |
| `frontend/src/api/schema.d.ts` | regenerated from the backend's schemas, never edited (build-frontend) |
| `golden-set/seed/todo-tasks-example.json` | the example tasks a new environment opens with (build-backend) |
| `scripts/seed_golden_set.py` | filling each list on its own, adding then marking an example task (build-backend) |
| `scripts/seed.sh` | its header and `--help`, which name the guest book alone today (build-backend) |
| `.github/CODEOWNERS` | the to-do list's rows in the per-context pattern the file states (build-platform) |
| `tests/unit/` | the text rule and the model's constants, and the one-table assertion a second table turns red (build-tests-unit) |
| `tests/fitness/` | the corpus rules scoped to entries and the two new browser copies (build-tests-unit) |
| `tests/integration/` | the service, router, contract, concurrency and corpus tests of the to-do list (build-tests-integration) |
| `tests/tooling/` | the seeder's per-list filling (build-tests-integration) |
| `tests/_golden_set.py` | registers the example-task file and any to-do fixture file (build-tests-integration) |
| `golden-set/fixtures/` | the to-do list's ordinary, boundary and refused texts (build-tests-integration) |
| `e2e/suite/features/todo_list.feature` | the to-do list's Gherkin scenarios (build-tests-e2e) |
| `e2e/suite/steps/todo_list_steps.py` | the steps that bind them (build-tests-e2e) |
| `e2e/suite/test_scenarios.py` | the import that makes the new step module exist for the runner (build-tests-e2e) |
| `e2e/ui/` | the UI smoke: the to-do screen boots, and locators follow the approved names (`A-4`) (build-tests-e2e) |

<!-- z spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md -->
# Delta fragment — `review-converge`

*Written by the convergence round of coherence pass 1, `requirements` stage. The requirements
stage has no fragment directory of its own, and `close_stage` assembles `delta.md` from
`design/delta/` and `reconcile/delta/` alone, so this entry sits in the first of them. The
edits this round made to `requirements.md` and `impact.md` are inside the change record and
need no entry.*


*Written by the convergence round of coherence pass 4, `design` stage, for the eight findings
`COH-design-1` to `COH-design-8`. Each entry below is an edit to the earliest document a finding
names as its `ambiguity_source` (constitution, Article VIII). The artefact-level patches under
each finding in `review/coherence.md` belong to the authors the convergence round sends again,
and they are not declared here. This round's edits to `requirements.md` (`COH-design-7`) are
inside the change record and need no entry.*


*Written by the convergence round of coherence pass 5, `design` stage, for the ten findings
`COH-design-9` to `COH-design-18`. Every decision was taken before this round, automatically from
the document a finding's `auto_basis` names or by the user at `Q-21`, and this round records it.
Each finding's edit lands in the earliest document it names as its `ambiguity_source`. Where the
dispatch also handed this round the ready patch under a finding, that patch landed too, in the
artefact that carried the contradiction. Both kinds are declared below when they land under
`spec/` or `contracts/`. This round's edits inside the change record need no entry: the
requirements (`COH-design-14`), the scenarios (`COH-design-15`), the ADR draft on coded text
refusals (`COH-design-15`), and the api and architecture fragments (`COH-design-15`,
`COH-design-9`, `COH-design-13`).*

<!-- z spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/data-model.md -->
# Delta fragment — `design-data`

*The schema half of the to-do list: one new table, `todo_tasks`, owned by the `todo_list`
context that `design-domain` opened (`design/delta/domain.md`), one index, no uniqueness
constraint, and one revision in `backward compatible` mode. The mechanism `BR-10` delegates to
the data model ("the data model names the mechanism that does") is written into
§ `todo_tasks` › Two writers on one task. One file is edited, so there is one entry.*


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

<!-- z spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/domain.md -->
# Delta fragment — `design-domain`

*A new bounded context, the to-do list, opened only after placing the requirements in the one
context that exists was tried and failed. The evidence for both is below the entries.*



## The concept is absent — the search

Run from the repository root on 2026-09-24, before any edit:

| Search | Where | Found |
|---|---|---|
| `grep -niE "to-do\|todo\|\btasks?\b\|\bdone\b\|tick" spec/glossary.md` | the glossary | nothing |
| the same, `-r` | `spec/contexts/` (one document, `guestbook.md`) | nothing |
| `grep -rniEl "to-do\|todo" spec --exclude-dir=changes` | the whole specification | `spec/invariants.md` lines 124 and 162 — "any to-do task", "like a to-do task", written by this change's own convergence round (COH-requirements-5, `design/delta/converge.md`); `spec/rationale/AUDIT-2026-09-01.md` — "TODO/FIXME" markers, not the concept |
| `grep -rciE "\btasks?\b"` over `spec/` outside `spec/changes/` | the whole specification | only the process word: "every task is a script" (constitution art. XII, conventions § Scripts), the `tasks` gate (conventions § Naming) |
| `grep -rnwI todo` over `app/ frontend/src e2e golden-set alembic contracts` | the code and the corpus | nothing (0 lines), and no `TODO` marker in first-party source |
| `grep -rhoE "\bBR-[0-9]{2}\b\|\bP-[0-9]{2}\b"` over `spec/ contracts/ CLAUDE.md` | the frozen spaces | `BR-01`…`BR-05`, `P-01` declared; `BR-14` appears only as an illustration in `spec/ADR/index.md`, which the `frozen-ids` gate does not hold. So `P-02` and `BR-06`…`BR-13` are fresh |

`impact.md` § What is missing ran the wider search (`todo|to-do|todos|task|tasks|done|complete|completed|zadani|checkbox|checked`
over twelve trees) and found the same. The term is not in the glossary after all, so the
`new_context` signal stands.

## The alternative that was tried — placing the requirements in the guestbook

| Test | Guestbook | Result |
|---|---|---|
| Does its language cover a task? | Entry, Author, Message, Edited. A task has no signature, no moment of amendment, no "edited"; an entry has no state. | fails |
| Does its flow hold a state? | `P-01`: "There are no intermediate states, no lifecycle … An entry either exists or it does not." Tasks would make that sentence false for its own context (requirements Self-check 24). | fails |
| Is any rule shared? | Only the text rule of `BR-01` (NFC, the trim set, code points). `BR-03` and `BR-04` are the same *shape* of rule about a different thing, and each side can change its own without the other (the list is read one way; the guestbook both ways). | one rule, handled as a kernel |
| Does a flow cross? | No step of either flow reads or writes the other's records; `Q-10` fills each list on its own. | nothing crosses |
| Can one owner hold both? | The guestbook is the template's example, deleted as a unit (`CLAUDE.md` § What is an example; `spec/contexts/guestbook.md`, "it can be deleted when your first real feature replaces it"). The user kept it beside the list (`Q-1`), so the list must survive its deletion. | fails |
| Could Platform hold it? | Platform has no domain rules (`spec/design/architecture.md` § Platform). | fails |

## Traceability — every rule to its requirement

| Rule | Requirements |
|---|---|
| `P-02` step 1, `BR-08` | R-1 (clauses 1-5; R-1.4) |
| `BR-06` | R-2 clauses 1-3, 4, 5; R-6 clause 4 |
| `BR-07` | R-2 clause 6 (assumption `A-1` set, `A-3` reading); R-6 clause 4 |
| `BR-11`, `P-02` step 2 | R-3 clauses 1-5 |
| `BR-09` | R-4 clauses 1-5; R-4 clause 6 by reference to the screen's floor |
| `BR-10` | R-6 clauses 1-3; R-9 clauses 1-3 |
| `BR-12` | R-1 clause 5 |
| `BR-13`, `P-02` step 5 | R-7 clauses 1-4; R-8 clauses 1-2 |

**Handed over, not owned by this context:** R-5 (the way between screens, the main address, the
404 copy) to the frame, `spec/design/ui/system-states.md`; R-3 clause 6 and R-10 (how an empty,
unreadable or failed state looks) to the screen specification; R-11 (example tasks in a new
environment) to `spec/design/architecture.md` § What a new environment starts with — bound by
`BR-06`…`BR-08` like any task.

## Checked against `spec/invariants.md` and `contracts/invariants/`

Authentication: consistent — anybody adds, marks, corrects and deletes any task, and the
non-goal already names tasks. CSRF, moderation, mobile, one engine: consistent. Paging and
search, lifted for the guestbook alone: consistent — the list has neither. Retention: consistent
— a task lives until deleted, and the non-goal names tasks. `D-01`: a done task stays one record
in its place, never moved to an archive. `D-02`, `D-03`: nothing here conflicts. `D-04` names
the guestbook's two fields; whether the task's text gets an invariant of its own is design-data's
call. No rule here contradicts an invariant.

<!-- z spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/spec.md -->
# Delta fragment — `design-spec`

*The to-do list's context document was opened by `design-domain` in the wave before this one
(`design/delta/domain.md`), with `P-02` and `BR-06`…`BR-13`. This pass read it whole against
every requirement, brought the guestbook's document level with the new boundary, and closed two
gaps in the rules. No rule identifier is minted: the highest in use is `BR-13`, and every edit
below amends a section that already has one.*



## Traceability — every requirement to where the live specification carries it

| Requirement | Carried by | This pass |
|---|---|---|
| R-1 | `P-02` step 1, `BR-08`, `BR-12` | read, no edit needed |
| R-2 | `BR-06`, `BR-07`; the shared text rule in the guestbook's `BR-01` | `BR-07` amended (two reasons meeting); `BR-01` names its second holder |
| R-3 | `P-02` step 2, `BR-11` | read, no edit needed |
| R-4 | `BR-09` (clause 6 by reference to the screen's floor) | read, no edit needed |
| R-5 | the frame every screen renders inside — owned by no context (todo_list § Neighbours, what no context owns) | no edit here; the guestbook's "only bounded context and only feature" sentence is corrected |
| R-6 | `P-02` step 4, `BR-10` | `BR-10` amended (a correction held to `BR-06` and `BR-07`) |
| R-7 | `P-02` step 5, `BR-13` | read, no edit needed |
| R-8 | `BR-13` | read, no edit needed |
| R-9 | `BR-10` | read, no edit needed |
| R-10 | how a screen shows a failure — owned by no context (todo_list § Neighbours) | no edit here |
| R-11 | a new environment's starting state — owned by no context; `BR-08` binds example tasks | no edit here |

## Checked against the invariants

Authentication and retention: consistent — the non-goals name tasks, and a correction or a
refusal needs no identity. `D-01`: a refused correction leaves one record as it was. `D-02`,
`D-03`: untouched. `D-04` names the guestbook's two fields; the sentence added to `BR-01` says a
task's text is held to the same rule and leaves to design-data whether the task's own domain
gets a data invariant for it. No edit here contradicts an invariant.

## Found outside this write set, left for the members who own it

Four documents still say there is one context, and none of them is a context document: the
specification's README (the row "What the guestbook does" and "The only domain context is the
guestbook"), architecture § the opening line and § Rules between contexts ("One domain context
has nothing to border on"), and testing's fitness table ("vacuously true with one context", on
the boundaries and declarations rows). The project's CLAUDE.md lists what deleting the guestbook
deletes; since this change it also has to say that the text rule's words move into the to-do
list first.

<!-- z spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/testing.md -->
# Delta fragment — `design-testing`

*How anyone will know the to-do list works: the cheapest suite per requirement, the citation, the
fixtures, which tests must be seen red first and which are green by design. Written into the live
`spec/design/testing.md`. This fragment carries the entry and what belongs to the change alone:
the owner per requirement, where this design departs from `scenarios.md` and from a neighbour's
fragment, and what nobody in the composition can write.*


## Traceability — every requirement to its owner

| Requirement | Owner (the deciding claim) | Supplementary | Citation surfaces |
|---|---|---|---|
| R-1 | `tests/integration/` — service and router | unit model, vitest page and hook, e2e (3 scenarios) | marker, tag, in-name |
| R-2 | `tests/unit/` — the text rule over `todo-task-text.json`, and a generator | integration corpus/service/router, vitest rule and composer, e2e (2); fitness and smoke without citation | marker, tag, in-name |
| R-3 | `tests/integration/` — order, tie on `id`, 101 in one read | router envelope, corpus reversal, vitest page, e2e (5) | marker, tag, in-name |
| R-4 | `tests/integration/` — chosen state for all four pairs | router, vitest row, e2e (4); clause 6 by the smoke, the token fitness and `uat.md` (no citation) | marker, tag, in-name |
| R-5 | `frontend` — router, frame, not-found page | `test_spa_fallback.py` already covers the server half; the smoke | in-name |
| R-6 | `tests/integration/` — service and corpus on `PATCH` | router, vitest row, e2e (2) | marker, tag, in-name |
| R-7 | `tests/integration/` — the row gone, the rest untouched | vitest row (the confirmation, its only proof), e2e (1) | marker, tag, in-name |
| R-8 | `tests/integration/` — service and the deletion race | router `404`, e2e (3) | marker, tag |
| R-9 | `tests/integration/` — two writers interleaved behind a held row lock | e2e (2, overlapping sends, supplementary) | marker, tag |
| R-10 | `frontend` — page and hook with a failing client | — | in-name |
| R-11 | **manual**, as the requirement already states | tooling seeder tests and the corpus fitness, neither citing | — (`uat.md`) |

Refusal codes from `spec/design/api.md` § The to-do list's refusals: `todo_task_not_found`,
`todo_task_empty_patch`, `todo_task_text_empty`, `todo_task_text_multiline`,
`todo_task_text_too_long` — five codes, five router tests, plus the standard validation `422`, the
order of the refusals, and the contract test over every shape.

Characterisation (green by design): `frontend/src/router.test.tsx` "opens the guestbook at the
main address", pinning `spec/design/ui/system-states.md` § Interactions. Also green on the first
run: the new corpus-shape rules in `tests/fitness/test_golden_set.py`, pinning
`golden-set/README.md`, because their subject is test data written earlier in the same wave.

## Where this departs from `scenarios.md`

1. **The task's text cases are a file of their own, `todo-task-text.json`, not additions to
   `text-measurement.json`.** Adding a field its readers do not know turns guestbook cases red on
   both sides in the commit that adds it, while the frontend author runs beside the fixture author
   and must stop on an existing red; the fitness sweeps would import a bound that does not exist
   until implementation; and `text-measurement.json` is deleted with the guestbook. The values are
   the ones S-8's note and the additions table give, plus one case for `BR-07`'s precedence, which
   design-spec added after the scenarios were written.
2. **The fixture files are `todo-tasks-*.json`, not `tasks-*.json`**, for glossary § Task
   (process); the seed file is `todo-tasks-example.json`, design-architecture's name, not
   `tasks-welcome.json`. Every value stands.
3. **The black box does not bind S-5, S-6, S-8, S-13 or S-33.** Each looks a text up in a to-do
   fixture file by its sentence; the deciding claim is a rule over a corpus, which
   `tests/integration/test_todo_tasks_corpus.py` reads directly, and the black box reaches the
   corpus only through `e2e/suite/golden_set.py`, which no author may write. S-18, S-41 and S-43
   (store-ordered) are proved in integration only, as the scenarios already said.
4. **`refusal` in `todo-tasks-refused.json` holds the contract's code**, not the guestbook's
   mechanism word, because every to-do refusal has a stable code.

## Where this departs from `design/delta/architecture.md` — for the coherence gate

**Decision 4's second half does not hold: the corpus-reading test cannot move to
`frontend/src/lib/text.test.ts`.** `frontend/src/contexts/guestbook/lib/entryText.test.ts` asserts
the guestbook's verdicts, and they need `AUTHOR_MAX_LENGTH`, `MESSAGE_MAX_LENGTH` and
`QUERY_MAX_LENGTH` from `./guestbookEntry`. From `frontend/src/lib/` that import is refused by
`tests/fitness/test_context_boundaries.py::test_no_screen_reaches_into_another_contexts_folder`
(`_web_context_of` returns `guestbook` for a module outside every context, and only
`frontend/src/router.tsx` is exempt), and transcribing the bounds instead is what
§ Choosing what proves what forbids. So the reader stays where it is and changes one import line;
the moved `frontend/src/lib/text.ts` has no test file of its own, with the reason written in the
live document. Consequences, all simplifications: the fitness allow-list for
`text-measurement.json`, `D-04`'s witness path in `contracts/invariants/guestbook.md`, and
`golden-set/README.md`'s two mentions of the reader stay true, so items 3 and the reader half of
item 1 in that fragment's "Found outside every write set" disappear. The edit to
`entryText.test.ts` is inside the boundary as it stands.

**Resolved as COH-design-3** (AUTO, on `spec/design/conventions.md` § Frontend — where a file
goes, which now says "Only the rule moves up"): the reader stays, and the architecture fragment
follows this reading. The live document cites that rule where it keeps the reader in place, and
§ Four file sets names `frontend/src/lib/text.ts` as the import's target.

The architecture's build-tests-unit set also lists `tests/unit/test_entry_text_rules.py`; with the
separate corpus file it needs no edit.

## Found outside this write set — for the orchestrator

- **`e2e/suite/golden_set.py` has no author in `.specconf/stack.json` § `skills`**, and it is the
  black box's only permitted crossing into the corpus (`tests/fitness/test_e2e_isolation.py`,
  `PERMITTED_CROSSING`). This design routes around it (departure 3), but any change whose Gherkin
  must read a new fixture file cannot be built today. A template fault: the profile's write sets.
- **The feature file's claim.** `tests/fitness/test_context_declarations.py::test_every_feature_file_is_claimed_by_exactly_one_context`
  goes red when build-tests-e2e writes `e2e/suite/features/todo_list.feature` (wave 1), and only
  `spec/contexts/todo_list.md`'s `features` clears it — a path no implement author holds. A claim
  written earlier turns `test_every_screen_and_feature_a_context_names_is_on_disk` red instead.
  Options for the coherence gate: (A) the convergence round claims the file at design close and the
  on-disk case is declared red until wave 1; (B) the implement stage ends with the claim case
  declared red and reconcile-spec claims it; (C) the profile lets one implement member write the
  context header's `features` line. The same timing holds, one stage earlier, for the screen
  document design-ui writes and `test_every_registered_screen_is_claimed_by_exactly_one_context`.
- **`golden-set/README.md` has no author**, and this change makes two of its sentences false: its
  § `seed/` names one file, and its exception names one browser reader of the corpus where there
  are now two, each of its own context's file.
- **A same-wave read.** `frontend/src/contexts/todo_list/lib/todoTask.test.ts` reads
  `golden-set/fixtures/todo-task-text.json` with `readFileSync`, and build-tests-frontend runs
  beside build-tests-integration, which writes that file. `readFileSync` is not an import, so
  `tests/fitness/test_wave_dependencies.py` sees no edge and would refuse an `after` that nothing
  justifies. The file's declared reds are to be observed after the whole test wave; design-plan
  should say so on the frontend task, whose author may otherwise see a missing-file failure first.

## Checked against the invariants

`D-01`–`D-03`: no new witness — the fitness sweeps reach `todo_tasks` through `Base.metadata`.
The task-text invariant design-data calls for (the convergence round writes it): witnesses named in
the live document — a round trip, a corpus read by both sides, and a generator. `spec/invariants.md`:
no test asks for an identity, and nothing assumes a retention policy.

<!-- z spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/ui.md -->
# Delta fragment — `design-ui`

*The to-do screen derived from the mock-up the user approved as drafted (`Q-14` → A, the 19
panels and the choices C-1…C-24 of `design/ui/index.html`), plus what the frame and the guestbook's
document had to say differently once the application has two screens. The screen document is
written into the live tree; this fragment says what moved and why. The two questions the mock-up
left open went to the person who asked for the change and are applied as answered (`Q-15` → A,
`Q-16` → A; § The two questions, answered).*




## The mock-up's choices, and where each one landed

| Choice | Landed in |
|---|---|
| C-1 lockup "Product name" / "P" | `system-states.md` § Regions, § Copy |
| C-2 two text links, "Screens", current marked | `system-states.md` § One column, § The navigation between the screens |
| C-3 `/todo-list` | `todo-list.md` front matter; `system-states.md` § Interactions |
| C-4 title and sentence; C-5 the task count | `todo-list.md` § Copy; § The task count in the header |
| C-6 footer per screen | `system-states.md` § Regions; `todo-list.md` and `guestbook.md` § Copy |
| C-7, C-8, C-9, C-10 the add field, when a refusal shows, the field after an add, the in-flight lock | `todo-list.md` § The add field, § Interactions |
| C-11, C-12, C-13 the row, how done looks, rows in one card | `todo-list.md` § A task's row, § Tokens, § Keyboard and accessibility |
| C-14 editing in place; C-15 a tick in flight | `todo-list.md` § A task's row, § Interactions |
| C-16 the delete question | `todo-list.md` § The delete question |
| C-17 success notices; C-18 failure words | `todo-list.md` § Notices, § Copy |
| C-19 the row stays after "no longer exists" | `todo-list.md` § Interactions |
| C-20 empty; C-21 failed to load; C-24 loading | `todo-list.md` § The list |
| C-22 not-found page | `system-states.md` § Copy |
| C-23 long texts wrap | `todo-list.md` § A task's row |

## Where the derivation read the mock-up, and the reading rejected

- **A correction that did not go through keeps the editor open with what was typed.** Panel P7
  says so for "no longer exists" ("the editor stays open with what was typed, as on the
  guestbook"); panel P11 says of a failed correction that "the old text … stays as it was". Both
  hold at once: the stored text is unchanged (the box keeps it as its name, "Cancel" brings it
  back, the new text appears nowhere in the list) while the editor keeps what was typed. The
  rejected reading closes the editor on failure, which throws away what the person typed and
  departs from the guestbook's editor, which C-14 copies.
- **A text the service refuses on an add shows under the field**, where the screen's own verdict
  stands, and the text stays. P5 says so for a correction; C-18's "a refusal with a sentence of
  its own shows that sentence" says what is shown, not where, and a notice for a text refusal
  would put the same three sentences in two places depending on which side caught the text.
- **A tick travelling locks only its own box.** C-15 names the box alone; P10 draws "Edit"
  locked on the ticking row because a correction was travelling in the same frame, which locks
  "Edit" on every row.
- **"An error of no sentence of its own" is an answer that carries no refusal sentence.** `Q-15`
  was asked with "for example an internal server error"; the document draws the line where the
  screen already reads the words — § Data: a refusal's `detail.message` is the words — so any
  answer that came and carries no such sentence gets "…the service answered with an error.",
  and one that carries it shows it (C-18). The rejected reading keys the words to a status code
  (every `5xx`), which leaves an answer outside `5xx` that carries no sentence with no words at
  all.
- **The focus goes back only when it was on the control that was locked or closed.** `Q-16` was
  asked as "while a change is being saved, its control is locked; where does the keyboard focus
  go when that control is unlocked again, or removed?", which presumes the focus was on it; the
  document says so, and says that a person who put the focus somewhere else while the write
  travelled keeps it there. The rejected reading moves the focus back on every answer, which
  pulls a keyboard user off the row they tabbed to while a slow tick was still travelling —
  "back where the person was" read against where the person now is. The add counts "Add task"
  as its control as well as the field (both are locked while an add travels), so a pointer
  press on "Add task" also brings the focus back to the field, as the answer's "after any add"
  says.

## The two questions, answered

The first attempt returned these two as `NEEDS_DECISION`; the person who asked for the change
answered both on 2026-09-24, and each answer is written into `spec/design/ui/todo-list.md` as
given; the two readings the writing-in needed are the last two items of § Where the derivation
read the mock-up, and the reading rejected. No state of the screen is left without defined
behaviour.

| Question | Answer | Landed in |
|---|---|---|
| `Q-15` — the words when a write fails and the service answered with an error of no sentence of its own (a server error, rather than a coded refusal or no answer) | A — `The task was not added: the service answered with an error.` for an add; `The change was not made: the service answered with an error.` for a tick, a correction and a deletion | § Copy (two rows, and the paragraph saying which sentence answers which case); § Interactions (the new failure branch on adding, ticking, correcting and deleting) |
| `Q-16` — where the focus goes when a control it was on is locked for a write and then unlocked, or removed | A — back where the person was: on the row's box after a tick settles, in the add field after any add, in the edit field after a correction that did not go through, and on the row's "Edit" when the editor closes on "Save" or "Cancel" | § Keyboard and accessibility (the bullet "The focus goes back where the person was", which replaces the sentence pointing at the open question) |

Rejected with those answers, as the options put them: for `Q-15`, the "could not be reached"
sentence for every failure with no sentence of its own (untrue when the service did answer), and
the bare sentence followed by the error's title as the browser names it; for `Q-16`, leaving the
focus to the browser as the guestbook does today (it can drop the focus to the page's start), and
giving the row's box the focus when the editor closes.

## Traceability — every requirement to where the screens carry it

| Requirement | Carried by |
|---|---|
| R-1 | `todo-list.md` § Regions 3–4, § The add field, § Interactions (adding), § Data (adding), § Keyboard and accessibility (the focus back in the add field after any add) |
| R-2 | `todo-list.md` § The add field (the screen's rule, no bound on input), § A task's row (`error`), § The refusals this screen can show |
| R-3 | `todo-list.md` § The list (every state; order as it arrives; no pieces), § The task count in the header |
| R-4 | `todo-list.md` § A task's row (`done`, `loading`), § Tokens (done text at 7.09:1), § Data (ticking), § Keyboard and accessibility (the focus back on the box after a tick settles) |
| R-5 | `system-states.md` § One column, § The navigation between the screens, § Copy (404), § Interactions; `todo-list.md` front matter (its own address); `guestbook.md` opening sentence |
| R-6 | `todo-list.md` § A task's row (`editing`, `saving`, `error`), § Interactions (correcting), § Keyboard and accessibility (the focus in the edit field after a failed correction, on "Edit" when the editor closes) |
| R-7 | `todo-list.md` § The delete question, § Interactions (deleting) |
| R-8 | `todo-list.md` § The refusals this screen can show (`todo_task_not_found`), § Interactions |
| R-9 | `todo-list.md` § Data: a tick sends `done` alone and the chosen state, a correction sends `text` alone; no screen state, since nobody is told |
| R-10 | `todo-list.md` § The list (`error` is not `empty`), § Notices, § Copy (the four failure sentences: nothing answered, or an error of no sentence of its own), § Interactions (each write's failure branches), § Data (nothing shown before the answer); `system-states.md` § `Toast` (an error stays until dismissed) |
| R-11 | no state of its own: example tasks are tasks like any other on this screen; the person who checks it by hand does so here. The seeder is `spec/design/architecture.md` § What a new environment starts with |

## Found outside this write set — for the orchestrator

1. **`spec/contexts/todo_list.md` front matter says `screens: []`.** With `spec/design/ui/todo-list.md`
   carrying `info_ref: S-02`,
   `tests/fitness/test_context_declarations.py::test_every_registered_screen_is_claimed_by_exactly_one_context`
   is red until the context claims it: `screens: [spec/design/ui/todo-list.md]`. That document's own
   rule ("the header claims a screen only once it exists") is now met. `spec/contexts/` is not in
   this skill's write set.
2. **`e2e/ui/test_smoke.py` names the lockup "Guestbook" and calls it "the only navigation this
   application has".** With the lockup renamed, the exact lookup of the link "Guestbook" finds the
   navigation link alone and still leads to `/guestbook`, so the assertions can hold; the comment and
   the constant's name are build-tests-e2e's.
3. **Pre-existing, not caused by this change, and left as they are:** `system-states.md` § Tokens
   still allows sizes off the Tailwind scale, which `spec/design/conventions.md` § Frontend
   forbids; `system-states.md` § Components still describes an `EmptyState` the code removed; the
   toast glyphs and the dialog backdrop in the shared primitives use colours outside
   `frontend/src/styles/theme.css`; field edges in `--color-hairline` sit below the 3:1 a control's
   edge needs, on both screens (the new box alone is given `--color-faint`). Each belongs to a
   change of its own or to reconcile-design.
4. **Code that still says "one screen"**: the docstrings of `frontend/src/components/shell/PageFrame.tsx`
   and the sentence in `frontend/src/pages/StatusPages.tsx` — build-frontend's, in its write set.

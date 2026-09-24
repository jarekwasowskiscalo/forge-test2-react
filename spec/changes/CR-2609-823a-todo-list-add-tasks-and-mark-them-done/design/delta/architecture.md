# Delta fragment — `design-architecture`

*Where the to-do list lives, which layer holds each of its rules, which files are created,
modified or removed, and which implementer writes each of them. The live document is
`spec/design/architecture.md` § The to-do list — where each rule lives; this fragment carries
what belongs to the change alone: the requirement per file, the nine write sets written out,
what the change leaves alone, what nobody in this composition can write, and the boundary.*

- `MODIFIED` `spec/design/architecture.md` — § What this is, and for whom (one paragraph
  added); § Contexts and their boundaries (the lead sentence, one table row, the diagram);
  § Rules between contexts (the lead-in paragraph, two bullets extended by one clause each);
  § What a new environment starts with (three paragraphs); § What a new feature adds (the
  Screen row, the paragraph on a second context); § The to-do list — where each rule lives
  (added, with four subsections)
  **Was:** "one deliberately trivial example feature: a guestbook"; "One domain context and one
  supporting technical slice", one row, one context node; "One domain context has nothing to
  border on, so today this section only says where the boundary **will** be"; a new environment
  filled when "the guest book" is empty, and "It will not seed a guest book that already has
  entries … one `GET`"; "the only files two contexts share are `app/api.py`,
  `app/contexts/__init__.py` and `frontend/src/router.tsx` … three places"; no placement for a
  second context anywhere.
  **Now:** the to-do list stands beside the example and survives its deletion; two contexts in
  the table and the diagram, both joined to Platform by the shared kernel; the boundary exists
  and its code belongs to neither context (`app/platform/schemas/text.py`, `frontend/src/lib/`);
  each list is filled on its own, a task added and then marked, one `GET` per list; four shared
  files with one appended line each, plus the frame and the seeder when a context has a screen or
  seed data; and a section giving the layer per rule for `BR-06`…`BR-13` and the three
  requirements no context owns, every file with its tree and its writer, the builders' pairwise
  intersections written out and empty, the three data edges that cross them, and the fitness
  tests that hold each boundary.
  **Why:** The to-do list is the second bounded context, and four sentences of this document became false the moment `spec/contexts/todo_list.md` was written: the system has two features, two contexts, a boundary with a declared pattern, and more than three shared files. The placement section is what lets the two implement waves run in parallel — design-plan turns its rows into tasks and the builders' allowlists are checked against it — and it has to exist before any code does, because a builder deciding its own layout is how a rule lands in a router or a second copy of the text rule appears in a context's folder. The seeding paragraphs record `Q-10` (each list filled on its own) and `Q-12` (at least one example done, reached by marking) where the filling rule already lives, instead of in a second home.
  **ADR:** none — every placement applies a rule this repository already holds: one file per layer under the context (`conventions.md` § Backend and § Frontend), the bound and the set beside the model (§ Rules between contexts), the browser text rule moving up to `frontend/src/lib/` on the day a second context needs it (`conventions.md` § Frontend, in those words), navigation in the frame (`ui/system-states.md` § One column), seeding through the API (§ What a new environment starts with, decision of 2026-09-05). The decision this layout follows — a to-do list context of its own, joined by a shared kernel — is the ADR `design/delta/domain.md` marks as required. The individual choices and their rejected alternatives are under § Decisions below.
  **Requirements:** CR-2609-823a/R-1, CR-2609-823a/R-2, CR-2609-823a/R-3, CR-2609-823a/R-4,
  CR-2609-823a/R-5, CR-2609-823a/R-6, CR-2609-823a/R-7, CR-2609-823a/R-8, CR-2609-823a/R-9,
  CR-2609-823a/R-10, CR-2609-823a/R-11

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
- **`app/platform/schemas/text.py`** — the kernel's server half is imported by the to-do schema
  as it stands; `app/platform/schemas/refusals.py` is reused as the envelope.
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
   `app/contexts/todo_list/`. `tests/fitness/test_context_declarations.py::test_every_registered_screen_is_claimed_by_exactly_one_context`
   goes red once design-ui's screen document carries an `info_ref` that `screens: []` does not
   claim, and `::test_every_feature_file_is_claimed_by_exactly_one_context` goes red when
   build-tests-e2e writes `e2e/suite/features/todo_list.feature` — and no implement member writes
   `spec/contexts/`.

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

# How this works today

*Descriptive only. No proposals — this is what the requirements author reads before
anyone decides anything.*

## What the request touches

The request (`request.md`, line 5, Polish, verbatim) asks for a to-do list: anybody can add a
new task, a task can be marked as done, one simple view with a field for adding tasks and a
list of the tasks added, and beside each task a way to mark it done and — "ew." — to delete or
edit it. In the glossary's words the system today has exactly one bounded context,
**Guestbook**, whose one stored thing is an **Entry** (`spec/glossary.md`, lines 14-15).
Neither *task*, *to-do* nor *done* is a domain word anywhere in the specification. The nearest
existing thing is an Entry — free text an unidentified person adds, amends and deletes — and
an Entry has no state beyond existing (`spec/contexts/guestbook.md` § `P-01`). The request
therefore reaches: the set of bounded contexts (a concept no context owns), the route register
and the HTTP contracts, the schema (whose one table is declared "the only table"), the page
frame (a second screen where the frame says there is one), and the system-level non-goals that
bind every screen.

## What the specification says

**The system has one context, and the specification says so in three places.**

- "The only bounded context of this system and the only feature it has" —
  `spec/contexts/guestbook.md`, line 13; "The only bounded context of this system" —
  `spec/glossary.md`, line 14; "One domain context and one supporting technical slice" —
  `spec/design/architecture.md` § Contexts and their boundaries (line 27).
- The guestbook is an example the template expects to be deleted "when your first real feature
  replaces it" — `spec/contexts/guestbook.md`, lines 17-19; `spec/design/architecture.md`
  § What this is, and for whom (lines 13-16); `CLAUDE.md` § What is an example.

**The path a new feature takes is written down.**

- Model, schema, service, router plus one line in `app/api.py`, the context's public API, a
  migration, a screen plus a route in `frontend/src/router.tsx`, `spec/contexts/<context>.md`
  plus entries in `api.md` and `data-model.md`, `contracts/openapi/<context>.yaml`, "one line
  in `.github/CODEOWNERS`", and proof in a unit test, an integration test and a `.feature`
  scenario — `spec/design/architecture.md` § What a new feature adds (lines 496-508).
- A second context shares exactly three files with the first: `app/api.py`,
  `app/contexts/__init__.py`, `frontend/src/router.tsx`, one appended line each —
  `spec/design/architecture.md`, lines 510-514.
- A context declares its neighbours as `<context>:<role>:<pattern>`; the guestbook declares
  `neighbours: []` — `spec/design/architecture.md` § Rules between contexts (lines 57-64);
  `spec/contexts/guestbook.md`, line 5 and § Boundaries.
- One file per layer, named after the concept, under the owning context; never `utils.py` /
  `helpers.py` — `spec/design/conventions.md` § Backend — where a file goes (lines 42-50); the
  frontend is cut the same way, `frontend/src/contexts/<name>/{pages,components,hooks,lib}` —
  § Frontend — where a file goes (lines 143-147).
- The tactical-modelling threshold: the domain "scores one or two", and "four operations on one
  table do not need an aggregate" — `spec/design/architecture.md` § When a context deserves
  tactical modelling (lines 578-584).

**Standing non-goals that bind every change and every screen.**

- Nobody is identified: no accounts, sessions or roles; "anybody may do anything" —
  `spec/design/architecture.md`, lines 18-23. The system-level wording in
  `spec/invariants.md` § Deliberate non-goals (lines 123-129) is "anybody may add, amend and
  delete any entry" — the guestbook's noun. No route returns `401`/`403` —
  `spec/design/api.md` § Conventions (lines 39-41). Authentication and personal data require a
  human decision — `spec/constitution.md`, Article XI (lines 154-155).
- No moderation (`spec/invariants.md`, line 145); no mobile version (lines 158-161); no data
  retention policy — "an entry lives until somebody deletes it" (lines 162-163); one database
  engine (lines 164-168). Paging and search were lifted for the guestbook alone, as `BR-05`
  (lines 146-150).

**Data.**

- Every primary key is a UUID generated application-side — `spec/design/data-model.md`
  § Identifiers (lines 66-73); `contracts/invariants/guestbook.md` § `D-03`. `D-01`…`D-03` are
  written in the guestbook's invariants file and swept over the whole of `Base.metadata`, not
  over one table — `spec/design/testing.md`, line 217.
- Every schema change is an Alembic revision with a working `downgrade`; `create_all()` is
  forbidden — `spec/design/data-model.md` § Owner of the schema (lines 9-16). Every schema change
  declares a compatibility mode; a new table is `backward compatible` — § Compatibility mode
  (lines 238-247).
- `guestbook_entries` — "The only table. No relations, no foreign keys, no lookup tables." —
  `spec/design/data-model.md`, lines 93-95. § Migrations: "One revision, and it is the head" —
  lines 212-219.
- Every text field is normalized to NFC, trimmed of a written 30-code-point set and measured in
  code points; `app/platform/schemas/text.py` is declared "a fact about EVERY text field this
  API accepts", while each bound lives beside its own model — `spec/design/conventions.md`,
  lines 91-99; `spec/design/api.md`, lines 146-154.

**HTTP.**

- The `/api` prefix is applied in `app/api.py` and nowhere else — `spec/design/api.md`,
  lines 27-30. A path identifier is a UUID and a non-UUID is a `422` — lines 33-35. Moments are
  ISO-8601 with an offset — lines 36-38. An empty collection is a `200` with empty `items`,
  never a `404` — lines 187-191. Every refusal carries a stable code and a finished English
  sentence kept beside the endpoint — § Refusals (lines 193-208).
- The route register names each route's context: `/api/health` (—), `/api/guestbook-entries`,
  `/api/guestbook-entries/{entry_id}` (`guestbook`) — `spec/design/api.md` § Routes and their
  contexts (lines 43-55).
- Every `/api/*` path the application serves falls under a prefix some contract claims, or the
  comparison fails — `contracts/README.md`, lines 41-47; `contracts/openapi/README.md`,
  lines 36-40. Two contracts exist, both Backward: `guestbook.yaml` (version `1.3.0`) and
  `health.yaml` — `contracts/openapi/README.md`, lines 7-8.

**Screens.**

- One document per screen under `spec/design/ui/`, front matter `route`, `info_ref` (`S-xx`),
  `requirements` — `spec/design/ui/README.md` § Naming. A change touching a screen delivers a
  mock-up at `spec/changes/<CR>/design/ui/index.html` — § HTML is the evidence (lines 9-10).
  Every component lists the states that exist — § Why states are enumerated.
- The frame is one centred column with no top bar and no navigation: "a product that adds a
  second screen **must add navigation here**" (`PageFrame`) — `spec/design/ui/system-states.md`
  § One column (lines 17-24) and § Out of scope. Every screen renders its own `PageFrame`; there
  is no layout route — lines 26-28.
- Copy that states a one-screen application: the 404 sentence "There is one screen in this
  application: the guestbook." (`spec/design/ui/system-states.md`, line 134), the footer
  "Entries are public and editable by anyone with this link." (line 132), `/` redirects to
  `/guestbook` (line 153). "The browser stores nothing" — no `localStorage`, no cookie —
  lines 156-157.
- The whole repository, interface copy included, is English — `spec/design/conventions.md`
  § Language (lines 297-304). The request is written in Polish.

**Decisions and history.** `spec/ADR/index.md` records no decision. `spec/changes/INDEX.md`
lists no earlier change touching a to-do list; the one merged feature change is `CR-2609-9b1e`
(the guestbook).

## What the domain document says

Only the guestbook context exists, and none of its rules or flows names a task.

- `P-01` — leaving and maintaining an entry: adding, reading, amending, deleting. "There are no
  intermediate states, no lifecycle, no transitions to police. An entry either exists or it does
  not." — `spec/contexts/guestbook.md` § `P-01`.
- `BR-01` — an entry requires a signature and a message; values are trimmed before they are
  measured; at most 80 / 1000 code points after NFC — `spec/contexts/guestbook.md` § `BR-01`.
- `BR-02` — an amendment moves the moment of amendment and never the moment of writing;
  "edited" is derived — § `BR-02`.
- `BR-03` — deletion is permanent; deleting somebody else's entry is possible; a second deletion
  refuses — § `BR-03`.
- `BR-04` — a total order, newest first by default, ties on the identifier, reversible —
  § `BR-04`.
- `BR-05` — narrowing by a phrase, reading a piece at a time, two counts — § `BR-05`.
- `S-01` — the guestbook screen at `/guestbook` — `spec/design/ui/guestbook.md`, front matter.
- There is no `I-xx` defect space in this repository: the identifier spaces are `P`, `BR`, `S`,
  `D`, `ADR`, `CR`, `R` (`spec/glossary.md` § Identifiers and their spaces), and no `I-NN`
  identifier occurs under `spec/` outside `spec/changes/`.

## What the code does

**Backend.**

- One context is registered, `from app.contexts import guestbook` —
  `app/contexts/__init__.py:20`; importing it is what fills `Base.metadata` before Alembic reads
  it — `alembic/env.py:11`, `app/contexts/guestbook/__init__.py:11`.
- The router aggregate includes the health router, then one line per context —
  `app/api.py:39` and `app/api.py:42`; there is no access check on it — `app/api.py:24`.
- The context's public API exports the model and the two length constants, not the routers —
  `app/contexts/guestbook/__init__.py:21`.
- `GuestbookEntry`, table `guestbook_entries`: `id` (`Uuid`, `default=uuid.uuid4`), `author`
  `String(80)`, `message` `Text`, `created_at` / `updated_at` `DateTime(timezone=True)`; the
  ordering index is declared in the model as well — `app/contexts/guestbook/models/guestbook_entry.py:36`.
  No column in the schema stores a state, a flag or a boolean —
  `app/contexts/guestbook/models/guestbook_entry.py:45`.
- Schemas: separate `Create` / `Update` / `Read` / `Page` classes; `Author` and `Message` are
  `NormalizedText` with `min_length=1` and the model's bound —
  `app/contexts/guestbook/schemas/guestbook_entries.py:50`; `PAGE_SIZE_MAX = 100`,
  `PAGE_SIZE_DEFAULT = 20`, `QUERY_MAX_LENGTH = 200` —
  `app/contexts/guestbook/schemas/guestbook_entries.py:28`; the sort is a closed `StrEnum` —
  `app/contexts/guestbook/schemas/guestbook_entries.py:54`.
- The service opens a `SessionLocal` per call, raises `GuestbookEntryNotFoundError` and names no
  status code — `app/contexts/guestbook/services/guestbook_entries.py:42`; one clock, `_now()` —
  `app/contexts/guestbook/services/guestbook_entries.py:46`; `create_entry` stamps both moments
  with one instant — `app/contexts/guestbook/services/guestbook_entries.py:190`; `update_entry`
  applies the fields given and stamps `updated_at`, with no version check, so the last write
  wins — `app/contexts/guestbook/services/guestbook_entries.py:206`; `delete_entry` refuses a
  missing id — `app/contexts/guestbook/services/guestbook_entries.py:229`.
- Five operations on `/guestbook-entries` and `/guestbook-entries/{entry_id}`; refusal codes
  `guestbook_entry_not_found` (`404`) and `guestbook_entry_empty_patch` (`422`), sentences as
  constants beside the endpoints — `app/contexts/guestbook/routers/guestbook_entries.py:99`,
  `app/contexts/guestbook/routers/guestbook_entries.py:115`. Domain exceptions are translated
  with `try` / `except` — `app/contexts/guestbook/routers/guestbook_entries.py:157`,
  `app/contexts/guestbook/routers/guestbook_entries.py:189`,
  `app/contexts/guestbook/routers/guestbook_entries.py:203`.
- One revision, `a1b2c3d4e5f6`, with no parent: it creates the table and the ordering index;
  `downgrade` drops the index, then the table —
  `alembic/versions/a1b2c3d4e5f6_create_guestbook_entries_table.py:24`.

**Frontend.**

- Three routes: `/` redirects to `/guestbook`, `/guestbook` renders `GuestbookPage`, `*` renders
  `NotFoundPage` — `frontend/src/router.tsx:28`. The only route constant is `GUESTBOOK_ROUTE` —
  `frontend/src/routes.ts:18`.
- `PageFrame`: the lockup links to `GUESTBOOK_ROUTE`, `PRODUCT_NAME = 'Guestbook'`, a fixed footer
  about entries, no navigation — `frontend/src/components/shell/PageFrame.tsx:24`,
  `frontend/src/components/shell/PageFrame.tsx:44`,
  `frontend/src/components/shell/PageFrame.tsx:72`.
- `NotFoundPage` says "There is one screen in this application: the guestbook." —
  `frontend/src/pages/StatusPages.tsx:14`.
- The guestbook screen: a composer card on top — `frontend/src/contexts/guestbook/pages/GuestbookPage.tsx:156`;
  a list of cards with in-place editing, at most one open (`editingId`) —
  `frontend/src/contexts/guestbook/pages/GuestbookPage.tsx:59`,
  `frontend/src/contexts/guestbook/pages/GuestbookPage.tsx:190`; deletion behind a confirmation
  dialog — `frontend/src/contexts/guestbook/pages/GuestbookPage.tsx:228`; a toast after each
  write — `frontend/src/contexts/guestbook/pages/GuestbookPage.tsx:109`; the empty state is drawn
  by the page itself — `frontend/src/contexts/guestbook/pages/GuestbookPage.tsx:208`.
- One TanStack Query hook per resource with a keys object; every mutation invalidates the
  resource's keys — `frontend/src/contexts/guestbook/hooks/useGuestbookEntries.ts:63`,
  `frontend/src/contexts/guestbook/hooks/useGuestbookEntries.ts:193`. Mutations never retry —
  `frontend/src/main.tsx:37`.
- Browser copies of the bounds, held equal to the Python literals by a fitness test —
  `frontend/src/contexts/guestbook/lib/guestbookEntry.ts:22` (`spec/design/data-model.md`,
  lines 155-160).
- Shared primitives any screen can use: `Button` / `LinkButton`, `Skeleton`, `ErrorState`,
  `Modal`, `Toast` (`success` / `warning` / `error`) — `frontend/src/components/ui/Button.tsx:67`,
  `frontend/src/components/ui/Feedback.tsx:26`, `frontend/src/components/ui/Modal.tsx:112`,
  `frontend/src/components/ui/Toast.tsx:33`. There is no checkbox or toggle primitive and no
  `EmptyState` — `frontend/src/components/ui/Feedback.tsx:14`.

**Operational surfaces a new resource meets.**

- The deploy smoke asks every parameterless `GET` it finds in `contracts/openapi/*.yaml`, so a
  new collection route joins it with no edit — `scripts/smoke_contract.py:16`.
- The e2e reset truncates every table in `public` except `alembic_version` —
  `e2e/harness/database.py:70`; the suite's `REQUIRED_TABLES` names `guestbook_entries` alone —
  `e2e/suite/conftest.py:47`.
- The seeder posts to `/guestbook-entries` only and refuses a guest book that already has
  entries — `scripts/seed_golden_set.py:70`; `spec/design/architecture.md` § What a new
  environment starts with (lines 407-414).
- API Gateway forwards every route (`route_key = "$default"`) —
  `infra/terraform/modules/api/main.tf:273`. *Guestbook* occurs under `infra/` only as the name
  prefix `sdd-guestbook` (state keys, role names, tags), e.g.
  `infra/terraform/modules/stack/variables.tf:4`. The image copies `alembic/`, `app/` and the
  built SPA whole — `Dockerfile:49`.
- CI selects jobs by path prefix and names no context — `.github/workflows/ci.yml:281`.
- `CODEOWNERS` has no per-context row; it states the five-row pattern "for the second" context —
  `.github/CODEOWNERS:65`.

## What the tests guarantee

What the suites pin that a second concept, table or screen meets:

- `tests/unit/test_guestbook_entry_model.py::test_this_schema_holds_exactly_one_table` —
  `set(Base.metadata.tables) == {"guestbook_entries"}`.
- `tests/integration/test_migrations.py::test_the_models_and_the_migrations_describe_the_same_schema` —
  autogenerate finds no difference between the models and the applied revisions.
- `tests/integration/test_migrations.py::test_upgrade_head_creates_the_guestbook_table_with_exactly_these_columns` —
  column equality against `spec/design/data-model.md`.
- `tests/fitness/test_context_boundaries.py::test_every_context_directory_is_registered_and_every_registration_exists` —
  both aggregates list every context directory, in both directions.
- `tests/fitness/test_context_boundaries.py::test_every_context_document_has_code_and_every_context_directory_has_a_document` —
  `spec/contexts/<name>.md` ⇔ `app/contexts/<name>/`, and `frontend/src/contexts/<name>/` when
  the document declares a screen.
- `tests/fitness/test_context_boundaries.py::test_no_context_imports_another_contexts_internals`
  and `::test_no_screen_reaches_into_another_contexts_folder` — the public-API boundary, on both
  sides of the wire.
- `tests/fitness/test_context_declarations.py::test_every_table_a_context_owns_is_declared_by_the_data_model`,
  `::test_every_registered_screen_is_claimed_by_exactly_one_context`,
  `::test_every_feature_file_is_claimed_by_exactly_one_context`,
  `::test_every_context_the_api_register_names_is_a_declared_context` — the front matter and the
  registers resolve.
- `tests/fitness/test_data_invariants.py` — `D-01`…`D-03` over all of `Base.metadata`.
- `tests/fitness/test_golden_set.py::test_every_entry_carries_the_keys_an_entry_has` — the
  corpus rules are written for guestbook entries and text cases (`golden-set/README.md`).
- `e2e/ui/test_smoke.py::test_the_root_redirects_to_the_one_screen` — `/` lands on `/guestbook`.
- `e2e/suite/features/guestbook.feature` — 22 scenarios, each tagged with one of
  `CR-2609-9b1e/R-1`…`R-7`; none concerns a task.
- `tests/tooling/test_e2e_harness.py::test_send_puts_a_json_body_on_the_wire_with_the_method_it_was_given` —
  the only test naming `/tasks`, a synthetic path proving the harness verb is resource-agnostic;
  not a feature.
- `spec/design/testing.md` (lines 200-201, 211, 217) records that the context, declaration,
  migration-safety and data-invariant sweeps are "vacuously true" with one context and one
  table, each carrying a known positive over synthetic input.

## Where these disagree

1. **How a router translates a domain exception.** `spec/design/conventions.md` § Layers
   (lines 36-40) says the router translates "explicitly, in a `match` block" and names
   `_not_found` in the guestbook router as the worked example; the router's own docstring says
   the same — `app/contexts/guestbook/routers/guestbook_entries.py:4`. No `match` statement
   exists under `app/`; the router translates with `try` / `except` —
   `app/contexts/guestbook/routers/guestbook_entries.py:157`. This is the file the conventions
   name as the one to copy for a new resource (`spec/design/conventions.md`, lines 76-79;
   `app/contexts/guestbook/routers/guestbook_entries.py:15`).
2. **The `EmptyState` primitive.** `spec/design/ui/system-states.md` lists `EmptyState` among
   the primitives in `frontend/src/components/ui/Feedback.tsx` (lines 11-13, § `EmptyState`).
   The module records that it was removed for having no caller, under
   `spec/design/conventions.md` § Frontend ("a primitive with no caller is removed") —
   `frontend/src/components/ui/Feedback.tsx:14`; the guestbook draws its own empty frame —
   `frontend/src/contexts/guestbook/pages/GuestbookPage.tsx:208`.
3. **The `Banner` primitive.** `spec/design/conventions.md` § Frontend (lines 155-157) cites
   "the `red` variant of `Banner`" as the example of intent encoded in variants in
   `components/ui/`. No `Banner` exists under `frontend/src/` (searched `Banner`).
4. **Per-context ownership.** `spec/design/architecture.md` § What a new feature adds (line 507)
   says a new feature adds "one line in `.github/CODEOWNERS`". `.github/CODEOWNERS:80` says
   per-context rows are noise while there is one context and gives **five** rows per context
   "for the second", each naming a team; the organisation has no team yet
   (`.github/CODEOWNERS:21`) and the guestbook has no row.

## What is missing

- **A to-do concept.** Searched `todo|to-do|todos|task|tasks|done|complete|completed|zadani|checkbox|checked`
  in `spec/glossary.md`, `spec/contexts/`, `spec/design/`, `spec/invariants.md`, `contracts/`,
  `app/`, `frontend/src/`, `alembic/`, `e2e/suite/`, `e2e/ui/`, `golden-set/`, `tests/`. Found
  only process words (a script "task", the `tasks` gate, "done" as a verb) and the synthetic
  `/tasks` path in `tests/tooling/test_e2e_harness.py:124`.
- **Any stored state or lifecycle.** `spec/contexts/guestbook.md` § `P-01` rules one out; the
  only model's columns (`app/contexts/guestbook/models/guestbook_entry.py:45`) and
  `spec/design/data-model.md` § `guestbook_entries` hold no boolean or status column.
- **A checkbox or toggle primitive.** `frontend/src/components/ui/` holds `Button`, `Feedback`,
  `Modal`, `Toast` and nothing else.
- **Navigation between screens.** `spec/design/ui/system-states.md` § One column;
  `frontend/src/components/shell/PageFrame.tsx:8`.
- **A mock-up for this change.** `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/ui/`
  is empty; `input/` holds only its own `README.md`.
- **Optimistic concurrency.** Searched `etag|if-match|version_id|optimistic|row_version` in
  `app/` and `frontend/src/`: nothing. The only update path overwrites —
  `app/contexts/guestbook/services/guestbook_entries.py:206`.
- **A precedent for a second context.** `spec/ADR/index.md` is empty; the guestbook declares
  `neighbours: []`; every context sweep is vacuously true (`spec/design/testing.md`,
  lines 200-201).

## What I could not determine

- **Beside the guestbook, or replacing it.** The request says "add a feature"; `CLAUDE.md` and
  `spec/contexts/guestbook.md` (lines 17-19) describe the guestbook as the example the first
  real feature replaces. `request.md` does not say whether the guestbook stays.
- **A context of its own, or a concept inside the guestbook.** `spec/glossary.md` (lines 4-6)
  keeps a context-only word in that context's document; nothing in the request relates a task
  to an entry. `new_context` is recorded lit on the absence alone; `contexts_touched_gt_1` is
  recorded lit on the reading that the concept gets its own document beside
  `spec/contexts/guestbook.md`, whose line 13 says it is the only context.
- **Whether "done" can be undone.** The request says "zaznaczyć, że zadanie jest zrealizowane"
  (mark the task as completed) and, one sentence later, "opcja odznaczenia, że zadanie zostało
  zrobione". In Polish *odznaczyć* reads both as "tick off" and as "untick".
- **Whether delete and edit are in scope.** "ew. usunięcie lub edycja" — *ew.* (*ewentualnie*)
  reads as "possibly" or "optionally".
- **What a task holds.** The request names one field. No bound, no second field (a guestbook
  entry requires a signature, `BR-01`), no moment of completion, no order, no statement on
  whether done tasks stay listed, and nothing on paging or search (`BR-04` / `BR-05` apply to
  the guestbook alone).
- **Whether deleting asks first.** The guestbook's deletion asks (`BR-03`;
  `spec/design/ui/guestbook.md`, lines 31-32 and § The delete dialog); the request is silent.
- **The address.** Which route the list lives at, whether `/` keeps redirecting to
  `/guestbook` (`frontend/src/router.tsx:29`, pinned by
  `e2e/ui/test_smoke.py::test_the_root_redirects_to_the_one_screen`), and whether the lockup's
  product name and the footer change (`frontend/src/components/shell/PageFrame.tsx:24`,
  `frontend/src/components/shell/PageFrame.tsx:72`).
- **Seed data for the list.** `scripts/seed_golden_set.py:70` knows `/guestbook-entries` alone;
  it is the one path under `scripts/` this change can reach, and only if the requirements give
  the list seed data. `tooling_touched` is recorded absent on that basis.
- **Copy.** The request is in Polish and the copy rule is English
  (`spec/design/conventions.md` § Language); no copy was supplied.
- **Two people acting on one task at once.** Anybody acts without identity, and the codebase's
  only update path has no version check
  (`app/contexts/guestbook/services/guestbook_entries.py:206`); what the list does then is not
  stated.

## Tier signals

*Measured, not judged. Each specification signal is the named surface grepped against the
specification tree; each path signal is the set of paths the change reaches. "Not lit" is a
measurement — an empty cell is not.*

| Signal | Lit | Evidence (what was found and where) |
|---|---|---|
| `contract_touched` | yes | A list anybody can add to is served by the backend, because "the browser stores nothing" (`spec/design/ui/system-states.md`, lines 156-157). A new route meets `spec/design/api.md` § Routes and their contexts (held by `test_context_declarations.py::test_every_context_the_api_register_names_is_a_declared_context`), the aggregate `app/api.py` named at `api.md` line 27, and the rule that every `/api/*` path falls under a contract prefix (`contracts/openapi/README.md`, lines 36-40; `contracts/README.md`, lines 41-47). |
| `schema_touched` | yes | Stored tasks meet `spec/design/data-model.md` § `guestbook_entries` ("The only table", lines 93-95) and § Migrations ("One revision, and it is the head", lines 212-219), pinned by `tests/unit/test_guestbook_entry_model.py::test_this_schema_holds_exactly_one_table`. |
| `screen_touched` | yes | "Prosty widok" is a second screen. It meets `spec/design/ui/system-states.md` § One column (a second screen "must add navigation here", `PageFrame`), the 404 copy "There is one screen in this application" (line 134) and the root redirect (line 153); `spec/design/ui/README.md` lines 9-10 (the mock-up a screen change delivers). |
| `rule_touched` | yes | The request changes what the system does — adding a task, marking it done, editing, deleting — and no `BR-*` or `P-*` in `spec/contexts/guestbook.md` covers it. The shared text rule binds every text field the API accepts (`spec/design/conventions.md`, lines 91-99). |
| `contexts_touched_gt_1` | yes | The concept is in no context document, so it arrives in a document of its own; `spec/contexts/guestbook.md` line 13 ("The only bounded context of this system and the only feature it has") is the second context document the change reaches. |
| `new_context` | yes | *Task*, *to-do* and *done* are absent from `spec/glossary.md` (Guestbook, Entry, Author, Message, Edited — lines 14-18) and from `spec/contexts/guestbook.md` § Language (Entry, Author, Edited). |
| `backend_touched` | yes | `app/api.py:42` (one line per context), `app/contexts/__init__.py:20` (the context list), and a revision under `alembic/versions/` (`spec/design/data-model.md` § Owner of the schema). |
| `frontend_touched` | yes | `frontend/src/router.tsx:28`, `frontend/src/routes.ts:18`, `frontend/src/contexts/<name>/` (`spec/design/conventions.md` § Frontend — where a file goes), `frontend/src/components/shell/PageFrame.tsx:8`. |
| `infra_touched` | no | API Gateway forwards every route (`infra/terraform/modules/api/main.tf:273`); CloudFront sends `/api/*` to it and `/*` to S3 (`spec/design/architecture.md` § The shape on AWS); *guestbook* under `infra/` is only the `sdd-guestbook` name prefix; `Dockerfile:49` copies `alembic/`, `app/` and the SPA whole. No path under `infra/` or `Dockerfile` is reached. |
| `tooling_touched` | no | Nothing under `scripts/`, `.claude/skills/` or `docker-compose.yml` has to change for a new resource: the deploy smoke is derived from the contracts (`scripts/smoke_contract.py:16`), the contract comparison claims by prefix (`scripts/openapi_contract.py:95`), the e2e reset is table-agnostic (`e2e/harness/database.py:70`), and `.claude/skills/build-tests-e2e/SKILL.md` names the guestbook only as a house-style example. The one reachable path, `scripts/seed_golden_set.py:70`, is reached only if the requirements give the list seed data (§ What I could not determine). |
| `ci_touched` | yes | `spec/design/architecture.md` § What a new feature adds (line 507) lists a line in `.github/CODEOWNERS`, and `.github/CODEOWNERS:65` states the per-context pattern for the second context. No workflow names a context (`.github/workflows/ci.yml:281`). |

**Resulting tier:** `p3` (strategic) — computed by `sdd-engine process_config --tier` over the
nine lit signals (`{"tier": "p3", "label": "strategic"}`, first rule matched: `new_context`) and
recorded with `sdd-engine change_state set-tier`, not by this paragraph.

*This table is for a human and nobody parses it. The machine truth is
`sdd-engine change_state set-signals`, recorded with nine signals present and `infra_touched`,
`tooling_touched` absent.*

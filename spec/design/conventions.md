# Conventions

Where a file goes, what it is called and what it may import. These are rules, not taste: each
is here because its absence produced a defect, and changing any of them needs an ADR exactly
as any other rule under `spec/design/` does.

What the system *is* — its contexts, containers and flows — is described by
[`architecture.md`](architecture.md). How it is run, tested and developed is stated by
[`CLAUDE.md`](../../CLAUDE.md).

## Layers

Layering is strict and one-directional:

```
app/contexts/<name>/ or app/platform/
  routers/   HTTP only: binding path/query/body, status codes, dependency injection
     ↓
  services/  business rules, transactions, the whole data-loading pipeline
     ↓
  models/    declarative SQLAlchemy mappings
  schemas/   Pydantic request and response contracts (never reused as ORM models)
```

**The layer is a directory inside a slice, never above one** (§ Backend — where a file goes).
Layering itself is unchanged by that; only the depth at which the directories are found.

**`services/`, `models/` and `schemas/` may not import `fastapi` or `starlette`.** Every module
in those packages says so in its docstring. This is what keeps business rules testable without
HTTP and reusable from an Alembic migration and a CLI script. Checked by
`tests/fitness/test_layering.py`.

**Dependencies point one way**: `routers` → `services` → `models`/`schemas`. A service
importing a router, or a model importing a service, is a defect.

A service **never names a status code**. It raises a domain exception; the router translates it,
explicitly, in a `match` block. `app/core/errors.py` registers three *framework* handlers and
knows nothing about the domain. The sentence an operator reads belongs beside the endpoint that
produced it, not in a shared table one edit away from telling somebody the wrong column to
correct. The worked example is `_not_found` in `app/contexts/guestbook/routers/guestbook_entries.py`.

## Backend — where a file goes

**The outermost cut is the bounded context; the layer is a directory inside it.** A new domain
concept adds **one file per layer, named after the concept**, under the context that owns it —
`app/contexts/guestbook/models/guestbook_entry.py`,
`app/contexts/guestbook/schemas/guestbook_entries.py`,
`app/contexts/guestbook/services/guestbook_entries.py`,
`app/contexts/guestbook/routers/guestbook_entries.py`. Never `utils.py`, `helpers.py` or
`common.py`: a name that describes nothing attracts everything.

The reason the context is outermost is **ownership**, not taste. `.github/CODEOWNERS` matches
paths, so a tree cut by layer can hand somebody every context's `services/` — a quarter of each —
and can never hand them one context. A path that holds one context and nothing else is what
makes a context something a person or a team can be given.

```
app/
  main.py            the composition root: middleware, the router, the assets, the SPA shell
  api.py             the one place the `/api` prefix is applied; one line per context
  contexts/<name>/   a bounded context and everything of it: models schemas services routers
  platform/          the supporting technical slice — HTTP with no domain rules in it
  core/  db/         infrastructure used by Platform and by every context alike
```

- **`app/contexts/<name>/__init__.py`** — the context's **public API**. Another context may
  import `app.contexts.<name>` and nothing below it; `tests/fitness/test_context_boundaries.py`
  refuses the rest. Importing it imports the context's models, which is what registers its
  tables on the shared `Base`.
- **`app/api.py`** — the aggregate, and **the `/api` prefix is applied there and nowhere else**,
  so a router registered anywhere else lands outside `/api` and is swallowed by the SPA
  catch-all. It is the **composition root**: the one module allowed to reach a context's router
  module, because a neighbouring context has business with a `GuestbookEntry` and none whatever
  with the function that binds it to a URL. One line per context, listed rather than
  discovered — so the registration can be checked in both directions.
- **`app/contexts/<name>/routers/`** — HTTP binding only, one module per resource, each
  exposing `router`. `guestbook` is the **only** domain context of this template and at the
  same time its worked example through every layer: copy it, and when your own context replaces
  it, delete it.
- **`app/contexts/<name>/services/`** — business rules. Owns the session and the transaction
  boundary.
- **`app/contexts/<name>/models/` + `alembic/versions/`** — one class per file, `Base` from
  `app/db/base.py`. Every schema change is a revision; `create_all()` is never called. Domain
  constants the whole application must agree on live beside the model they describe
  (`AUTHOR_MAX_LENGTH` in `app/contexts/guestbook/models/guestbook_entry.py`). See
  [`data-model.md`](data-model.md).
- **`app/contexts/<name>/schemas/`** — Pydantic request and response models, the file name
  plural per resource, the classes suffixed (`GuestbookEntryRead`, `GuestbookEntryCreate`).
  Read and write shapes are separate classes even when they are identical today. See
  [`api.md`](api.md).
- **`app/platform/`** — the technical slice: liveness, the health shape, the refusal envelope
  and the text rule. **Two files here are not named after a resource, and that is a rule rather
  than an exception to one.** `app/platform/schemas/refusals.py` carries the refusal envelope
  with a code, which is a fact about EVERY refusal this API makes rather than about guestbook
  entries; the sentences themselves stay beside the endpoint that produces them, and only the
  envelope is shared. `app/platform/schemas/text.py` carries how a text field is normalized,
  trimmed and measured, which is a fact about EVERY text field this API accepts; the *bounds*
  stay where their domain is (`AUTHOR_MAX_LENGTH` beside the model) and only the unit they
  count in is shared. The test of whether a third file belongs here is the same both times: not
  "is it generic" but "is it a fact about every one of these, rather than about one context's". `app/core/` and `app/db/` are **not** under this name, because they are used by
  Platform and by every context alike and filing them under one slice would say something
  untrue about who they belong to.
- **`tests/<group>/test_<subject>.py`** — one of four groups, with no mirroring of the package
  tree inside any of them. `unit/` does not touch the database, `integration/` needs it,
  `fitness/` reads this repository's source as text, `tooling/` covers `scripts/` and the
  end-to-end harness. **The directory is a declaration**: each of the three database-free groups
  carries a `conftest.py` that applies `no_db` to everything below it, so the marker cannot be
  forgotten, and `tests/fitness/test_test_layout.py` proves the converse. Shared helpers stay
  flat as `tests/_<subject>.py`. Reference data in `golden-set/`, located by
  `tests/_golden_set.py`, and the repository root by `tests/_repo.py` — never by counting
  directories, which broke eleven modules at once the first time the suite was grouped.
  **`golden-set/` is itself two declarations**: `fixtures/` is what a suite reads and asserts
  about, `seed/` is what a new environment opens with — the same rule as the test groups, one
  directory up. See [`testing.md`](testing.md).
- **One exception, and only one**: the tests of the SDD framework itself live beside the code
  they prove, as the engine's own tests. Most of them read their subject's
  *source* — which module defines a constant, which imports `fcntl`, which counts directories to
  find the repository root — and a check that reads source belongs beside it. The same `pytest`
  run collects them (`testpaths` names both roots), so this is an exception of layout rather
  than a second suite. The application's tests stay flat under `tests/`; this exception does not
  generalise.

**Placeholder columns stay unwritten**: a column whose owning feature has not landed is nullable
and no service writes it; the docstring names the blocking feature.

## Frontend — where a file goes

**Cut by context first, exactly as the backend is**, because a screen is owned by the context
whose rules it shows, and because the same argument about `.github/CODEOWNERS` applies on this
side of the wire. What is left at the top level is what genuinely belongs to no context.

```
frontend/src/
  contexts/<name>/   pages components hooks lib — one context's screen and everything of it
  components/ui/     design-system primitives, no business logic
  components/shell/  the frame every screen renders itself inside
  hooks/  lib/       rules and helpers that are about no context in particular
  api/               the generated contract and the client over it
  router.tsx         the composition root: the one module that binds a path to a screen
  routes.ts          the route constants, shared by the shell, the 404 page and the screen
```

- **`frontend/src/contexts/<name>/`** — one context's screen and everything only it uses:
  `pages/<Name>Page.tsx`, its `components/`, its `hooks/`, its `lib/`. A module here may not
  import another context's folder; `tests/fitness/test_context_boundaries.py` refuses it, and
  `router.tsx` is the one named exception because binding a path to a screen is what a
  composition root does.
- **`frontend/src/pages/`** — screens belonging to no context: today `StatusPages.tsx`, which
  is what a wrong address gets. A screen that shows a context's rules belongs in that context.
  **Route paths are English** (`/guestbook`), like everything else in this repository
  (§ Language), and they live in `frontend/src/routes.ts` — a route is the application's
  composition rather than a context's internals, which is why a shared layout component no
  longer owns one.
- **`frontend/src/components/ui/`** — design-system primitives, no business logic, no data
  fetching. Export the component **and** its props interface. **Encode intent in variants, not
  in callers**: the `red` variant of `Banner` means "this is a loss, not a warning", and that is
  why an irreversible message cannot accidentally be made to look like an ordinary one. **A
  primitive with no caller is removed**, not kept in reserve: a component nobody renders is a
  branch nobody reviews against a screen.
- **`frontend/src/hooks/`** — two kinds, both tied to React. One TanStack Query hook per resource
  (`use<Resource>.ts`, exporting a `<resource>Keys` object; **components never call `client.GET`
  directly**) and hooks for state in the URL — filters, sorting and paging live in the address,
  so a screen can be shared and survives a reload (`useEntryQueryParams.ts`). A parameter at its
  default value is **absent** from the address, and a write replaces the history entry rather
  than adding one. The *rules* those hooks apply live in `lib/`.
- **`frontend/src/lib/`** — pure rules and formatting that belong to no context, one concern
  per file, named after it (`datetime.ts`, `relativeTime.ts`, `number.ts`, `cn.ts`). A rule
  about one context's data lives in that context's `lib/`
  (`contexts/guestbook/lib/guestbookEntry.ts`, `contexts/guestbook/lib/entryListCopy.ts`,
  `contexts/guestbook/lib/entryText.ts`), and moves up here the day a second context needs it —
  never before, because a shared module with one caller is a boundary drawn in the wrong place.
  `entryText.ts` is the case worth naming: its Python counterpart sits in `app/platform/`
  because the server has more than one caller for it, and this one stays in the context because
  the browser has exactly one. The asymmetry is each tree following its own rule rather than an
  oversight in either.

  Rejected (decision of 2026-09-17, `cr: historical` — where the two halves of the text rule go,
  decided on GitHub issue #28, outside `/forge:sdd`):

  - **Put both in the context, and add no file to `app/platform/`.** It keeps the trees
    symmetrical and says something untrue: how this API trims and measures text is a fact about
    every text field it accepts, and the schemas and the service are already two callers. The
    next context would copy the rule rather than import it, which is how a shared fact becomes
    two facts.
  - **Put both above the contexts, in `app/platform/` and `frontend/src/lib/`.** Symmetrical the
    other way, and it breaks this section's own rule: a shared module with one caller is a
    boundary drawn in the wrong place, and the browser has exactly one caller today.
  - **Fold the rule into `guestbookEntry.ts` rather than giving it a file.** The search phrase is
    not an entry, and it is measured by the same rule — so the module would be named after one of
    its two subjects. Never `format.ts` or `utils.ts`. Nothing
  here imports from `components/` or from `contexts/` — both are dependency arrows pointing
  backwards.
- **`frontend/src/api/schema.d.ts`** — generated, never edited. Domain types are aliased from it
  (`type GuestbookEntry = components['schemas']['GuestbookEntryRead']`). Regenerate rather than
  widen.
- **`frontend/src/styles/theme.css`** — the application's colour tokens and the only place where
  colour and typeface are written down. Everything that is neither — sizes, spacing, radii,
  shadows — comes from the Tailwind scale. A token name may not collide with a class name from
  that scale (`spec/design/ui/system-states.md` § One palette). **Never a raw hex value or a
  bracketed value in a component** — a raw colour is a token nobody has named yet, and it is
  invisible to every later change of the palette.

**Frontend tests** are `vitest`, `*.test.ts(x)` placed beside the module they test. The weight is
carried by the pure rules in `lib/` and the generated-contract adapters in `api/`; a component
test that asserts only that it rendered is noise.

Screens are specified before they are built, one document per screen under [`ui/`](ui/) — that
rule, and the reason Markdown beats a mock-up, are given by [`ui/README.md`](ui/README.md).

Rejected (decision of 2026-09-07, `cr: historical` — the placement rule changed from
layer-first to context-first, and this document is where placement rules live; the recut was
done on the trunk and carries no `delta.md` in which to declare the edit. What the system is
now made of, and the alternatives weighed there:
[`architecture.md`](architecture.md) § What a new feature adds):

- **Leave placement alone.** The layer-first tree broke no rule in this document and produced
  no defect. It made exactly one thing impossible, and the thing is the reason for the change:
  a path that holds one context. Ownership is what sdd107 puts before hierarchy and before any
  automation, and a rule nobody can be given is a rule with no addressee.
- **Say the rule and move the files later.** A placement rule describing a tree that does not
  exist is the failure `docs/` is forbidden from having: a document read as normative that
  nothing holds. The fitness functions in `tests/fitness/test_context_boundaries.py` are what
  make this rule real, and they cannot be written against an absent shape.
- **Let a context's `lib/`, `hooks/` and `components/` stay shared and cut only the pages.**
  Half a boundary. The screen would move and the rules behind it would not, so two contexts
  would still meet in `frontend/src/lib/`, which is where the collision actually is.

## Boundaries — where a contract goes

A boundary is where the system meets something it does not compile together with itself. At a
boundary the contract is the authority and the code is validated against it (constitution,
article VI; the decision and its rejected alternatives:
[`contracts/README.md`](../../contracts/README.md)).

- **`contracts/<kind>/<area>.yaml|.md`** — one file per area, named after the area, **written by
  hand and committed**. `openapi/` for HTTP, `asyncapi/` for events, `invariants/` for data
  invariants. Every subdirectory carries a `README.md` with a declared compatibility mode; a
  directory with no contract declares `**Status:** empty starter` in it, because silence and a
  decision look identical in a file tree.
- **Never generate a file into this directory.** A copy of a dump has no authority over what it
  was copied from; `contracts` (`G20` until the rename) refuses a file with a generator banner, and one shell redirection is
  the whole way back to the state this decision reversed.
- **The database schema is not here, and that is a decision.** The set of revisions in
  `alembic/versions/` is its contract ([`data-model.md`](data-model.md) § Owner of the schema);
  the compatibility mode is declared beside the schema, in the same document.
- **A machine's output stays output.** `openapi.json` is gitignored and rebuilt on every run;
  `./scripts/contracts.sh` compares it against the contract.

## Documentation — where a document goes

A document that is not normative still has one home, and which home decides who it is written
for. Three trees, three readers, and the cut is by **subject** rather than by tone:

| Tree | Subject | Reader |
|---|---|---|
| [`docs/`](../../docs/README.md) | the system: how to set it up, run it, configure it, watch it, back it up and repair it | whoever operates or takes delivery of the application |
| [the marketplace's README](https://github.com/Scalo-Sales-Engineering-Consulting/claude-marketplace/blob/main/README.md), and the orchestrator's own document ([`skills/sdd/SKILL.md`](https://github.com/Scalo-Sales-Engineering-Consulting/claude-marketplace/blob/main/plugins/forge/skills/sdd/SKILL.md)) | the change process: how a change travels, and the decision table that drives it | whoever runs, ports or alters the process |
| [`../rationale/`](../rationale/README.md) | reasoning worth keeping that is not a decision — why a shape was chosen, what was tried, how it broke | whoever changes this in six months |

Four rules hold over `docs/`, and each exists because its absence has a named cost:

- **Nothing in `docs/` binds.** Where a rule holds, it holds because it stands in `spec/` or
  `contracts/`, and the document here **cites the one that owns it**. A descriptive document
  read as normative is a second home for one rule, which is the failure
  [`../README.md`](../README.md) exists to prevent. Every document therefore carries a
  `**For:**` line naming its reader and a `**Normative source:**` line naming what it defers to.
- **One subject per file, named after the subject.** `configuration.md`, `monitoring.md` — never
  `misc.md`, never a number in the filename. The same rule as § Naming, for the same reason: a
  directory that numbers its documents has stopped being able to say what is in them.
- **A procedure is a runbook and lives in `docs/runbooks/`.** A runbook says when to use it, the
  steps in order, and how you know it worked. A procedure with no last section cannot be
  finished by the person who did not write it, which is the person who reads it at three in the
  morning.
- **Every instruction invokes a script** (the constitution, article XII). A document that tells
  somebody to type `terraform apply` has taught them to skip the guard, and the guard is the
  point of `scripts/`. The named exception is the AWS CLI, which genuinely is the interface for
  the few steps no script wraps.

Rejected (decision of 2026-09-06, `cr: historical` — the process manual and the system's
documentation were both in `docs/`, and only one of them was there; framework changes are made
on the trunk and carry no `delta.md` in which to declare the edit):

- **Leave the process manual in `docs/` and give the system's documentation another directory.**
  It puts the tree a client reads one directory away from the tree explaining an agent
  framework, and names the visitor's directory after the resident. `docs/` is the first place
  anybody looks for a manual to the thing the repository builds.
- **One directory, two subjects, separated by a naming prefix.** The prefix is a convention a
  reader has to learn before the index is legible, and nothing enforces it. The directory
  boundary is enforced by the file system.
- **Leave `docs/` unwritten and let the operational facts stay where they are** — in
  `infra/README.md`, in `CLAUDE.md`, in script headers and in module docstrings. That was the
  state this replaces, and its cost is measurable: the rollback semantics lived only in
  `scripts/deploy.sh --help`, the log-level convention only in a Python docstring, and no
  document anywhere named a restore procedure. Facts that live only where they were written are
  facts only their author can find.

## Language

**The whole repository is written in English.** Prose, identifiers, file names and
directory names; `spec/` and `contracts/` along with everything else; the interface, the
route paths, the refusal sentences the backend produces, the Gherkin scenarios, the SDD
process layer and the scripts. Gate `english` enforces it, and it enforces both halves: the
sentences inside a file are judged by counting, and the name of the file is judged by
looking it up, because a path has no function words to count.

**A number in prose takes a comma as its thousands separator** — `10,000`, never `10 000`.
The spaced form is Polish typography that survived the translation in one document while its
neighbours used the comma, and a reader should not have to know the repository's history to
read a number.

**This reverses the decision of 2026-08-31**, which is recorded here rather than deleted.
That decision drew the line where a person starts reading a screen: interface copy became
English, while route paths, backend refusal sentences, the Gherkin suite and the whole of
`spec/` and `contracts/` stayed Polish. Its reasoning was sound at the time — the guestbook
screen was rebuilt from a Claude Design mock-up whose sentences are *content*, the routes
were already written down and linked, and refusal sentences are backend text that reaches
every client rather than one screen. What it produced was a repository with a seam through
it: two languages, and a rule for which side of the seam each artefact falls on. The
option this reverses to was named and rejected on that day as "English everywhere, routes
and refusals included"; the cost it was rejected for — broken links and backend text moving
during a frontend change — is a one-off cost that gets larger every month it is deferred,
while the seam is a cost paid at every reading.

**Rejected, again and for the same reasons as before:** a bilingual tree with translation
files (it solves a problem this product does not have and adds a second place for copy to
drift from the screen specification — it comes back with a second audience and its own
decision); and keeping historical documents in the language they were written in (an audit
nobody can read is not a record, and `spec/rationale/` exists to be read). Introducing i18n
later still does not require undoing this: English becomes one of the languages, rather
than a layer to take off.

**What is not translated, and why.** These are not exceptions to the rule; they are things
the rule was never about.

| What | Stays as it is |
|---|---|
| parsed keywords — EARS `WHEN`/`SHALL`, delta labels `ADDED`/`MODIFIED`/`REMOVED`, the `**ADR:** none` and `**Verified-by:** manual` markers, front-matter status values | already English, and a contract rather than prose |
| stable refusal codes (`guestbook_entry_not_found`) | a contract surface: the code is what a client matches on, and rewording it is a breaking change |
| the credential names `e2e/harness/client.py` redacts | a denylist, not prose — dropping a spelling narrows what gets redacted |
| non-ASCII text in `golden-set/` | evidence that bytes survive the round trip. **Each half** must carry characters above U+007F; neither need carry any particular language |
| a quoted Polish phrase, a proper noun, a historical file name | quotation. `english` has a floor of five lines so that quoting does not read as writing |
| `spec/rationale/mockup-guestbook/support.js` | vendored runtime of a design tool, not authored here |

**Domain terms keep their source form inside identifiers** (`GuestbookEntry`, `author`), so
a field can be grepped from the specification down to the column — see
[`../glossary.md`](../glossary.md).

## Naming

- **Python files and functions**: `snake_case`. Private helpers prefixed with `_`
  (`_normalize_iban`), kept in the module that uses them.
- **Python model files**: singular (`models/guestbook_entry.py`); schema, service and router
  files plural (`schemas/guestbook_entries.py`) — a model is one thing, an API is a collection.
- **TS components and files**: `PascalCase.tsx` matching the exported component. **Hooks**:
  `useThing.ts`; **libraries**: `camelCase.ts` (`lib/guestbookEntry.ts`).
- **Domain field names**: exactly as the source specification names them (`author`, `message`,
  `created_at`), so that a field can be grepped from the specification to the column.

### A gate is named, not numbered

A gate's identifier is the name of what it checks: `^[a-z][a-z0-9-]*$`, lower case, hyphens,
**no slash and no dot**. The register is
[the engine's `spec_gates.py`](https://github.com/Scalo-Sales-Engineering-Consulting/claude-marketplace/blob/main/plugins/forge/skills/_shared/sdd/spec_gates.py),
and it is the source the two documentation tables and the exemptable list are all compared
against.

The shape rule is not aesthetic. `backtick-paths` and `source-paths` read every backticked
token containing a slash as a repository path and check that it exists, so a gate called
`spec/links` would make every document that names it fail two other gates — and the failure
would be reported against the document rather than against the name. `test_sdd_spec_lint.py`
asserts the shape rather than trusting this sentence.

Rejected (decision of 2026-09-06, `cr: historical` — the gates were renamed from `G1`…`G20` to
descriptive names; this document is where naming rules live, and framework changes are made on
the trunk, so there is no `delta.md` in which to declare the edit):

- **Keep the numbers.** `G12` says nothing about what it checks, so every mention costs a
  reader a lookup in a table two directories away. Twenty of them, in three modules, two
  documentation tables and six regexes — and the audits under `spec/rationale/` are a record
  of that cost being paid.
- **Rename and renumber, closing the holes.** `G9` and `G13` are withdrawn, and renumbering
  would tidy the sequence by destroying the one thing a hole carries
  ([`../invariants.md`](../invariants.md)).
- **Keep both, a name beside a code.** Two homes for one fact, which this repository refuses
  everywhere else, and the second home is the one that goes stale.
- **Split `G4` or leave it whole.** It covered three unrelated rules — EARS discipline, a delta
  entry's `**Why:**`, and task shape — so a single name for it would have been vague where the
  three checks are precise, an exemption row naming it silenced all three, and a CI annotation
  titled with it named none of them. Split into `requirements`, `delta-entries` and `tasks`.

Consequences: `G9` and `G13` stay withdrawn and gain no name, because a name for a rule nobody
raises is an invitation to write an exemption for it. The old codes are neither reused nor
erased — `spec/rationale/` and `retro/` keep them verbatim, and
[the process's `spec_gates.py`](https://github.com/Scalo-Sales-Engineering-Consulting/claude-marketplace/blob/main/plugins/forge/skills/_shared/sdd/spec_gates.py) maps every
one to the name it became. The count went from eighteen to twenty on the day of the rename, and
stands at twenty-two now (`operations-doc` and `documentation-set` came afterwards). Enforced by
`test_sdd_spec_lint.py`, which compares the register against both documentation tables — names,
order, family and exemptability — and by `test_sdd_spec_summary.py`, which compares the rows the
job summary prints against the gates the code actually raises.

Rejected (decision of 2026-09-10, `cr: historical` — the forge plugin deleted its `docs/` tree
on 2026-09-10: the handbook, the reference and their index exist nowhere, so the documentation
table above names what the process still has — the marketplace's README for a person, the
orchestrator's own document for the table that drives a change — and the mapping from a retired
gate code to its name is read off `spec_gates.py`, the register where every gate declares the code
it carried. Framework changes are made on the trunk and carry no `delta.md`): keeping links that
return 404, or vendoring a copy of the deleted pages here — the second home this section argues
against.

## Type safety

- **Backend**: full annotations, `Mapped[...]` on every column. Optionality expressed in the
  type (`str | None`), not only in the column arguments. `mypy --strict` covers `app`,
  `scripts`, `e2e`, `.claude/skills`, `tests/unit` and `tests/fitness`.
- **Frontend**: `tsc --noEmit` is part of `build`. API types come from the generated
  `src/api/schema.d.ts` — regenerate rather than widen a type.
- **The syntax floor is lower than the runtime floor, and deliberately.** `pyproject.toml` pins
  `requires-python` to what the application runs on, and `ruff`'s `target-version` to what the
  code may be *written* in; the second is the older of the two. The bare-machine scripts start
  on whatever `python3` a machine has on PATH rather than on the interpreter `uv` provisions —
  `scripts/preflight.py` reporting what is missing, `scripts/ci_summary.py` in the aggregate CI
  job, `scripts/app_status.py` behind `status.sh` — and a script that reports a missing Python
  cannot ask for one before it parses. `tests/fitness/test_scripts_syntax_floor.py` parses them
  at that floor and holds `target-version` to it. The change process holds its own hooks to the
  same floor in its own suite, with a `target-version` of its own.

Rejected (decision of 2026-09-08, `cr: historical` — the project moved to Python 3.14 and the
first `ruff format` under `target-version = "py314"` rewrote `except (A, B):` into the PEP 758
form across the framework, which every older interpreter refuses with a SyntaxError; found the
same day, on the trunk, where there is no `delta.md` to declare the edit in):

- **Raise `target-version` with the runtime and mark the two entry points `# fmt: skip`.** One
  number instead of two, and it holds exactly until somebody adds a third module to the hooks'
  import closure without knowing the marker exists. What it buys is a SyntaxError raised before
  any of this project's own error handling runs, on a contributor's machine rather than in CI.
- **Require Python 3.14 on PATH.** Nothing can enforce it: the check that would say so is written
  in the syntax that fails to parse.

## Imports

Static, named imports only — no star imports. First-party imports in the backend are always
absolute, from `app.`; no relative imports between packages. The frontend uses the `@/` alias
for anything outside the current feature folder, and relative paths inside it.

```python
import datetime                      # standard library
from sqlalchemy import select        # third party
from app.contexts.guestbook.models.guestbook_entry import GuestbookEntry   # first party, absolute from `app.`
```

```typescript
import { useQuery } from '@tanstack/react-query'  // third party
import { client } from '@/api/client'             // absolute, outside this feature
import { EntryRow } from './EntryRow'             // relative, same feature
```

**One exception, mechanical rather than stylistic**: `e2e/suite/test_scenarios.py` star-imports
the step modules. A pytest-bdd step definition is not a decorated function — the decorator
writes a *fixture* into its defining module's globals under a generated name, and pytest sees
fixtures only in the module it collects, so a named import registers nothing. The two routes on
which this can break silently (an `__all__` in a step module, a step module nobody imports) are
both checked by `tests/fitness/test_e2e_scenarios.py`.

## After a change

- **After an API change**: `./scripts/generate.sh`, then commit what it changed.
  `frontend/src/api/schema.d.ts` is committed and CI regenerates and compares it;
  `openapi.json` itself is gitignored, because an intermediate product must never go stale in
  git.
- **Every task is one `.sh` script** over the shared `_lib.sh`; task scripts written in Python
  are libraries that the `.sh` calls, not a second entry point to the task. The scripts are
  POSIX (§ Scripts).

## Scripts

**Every task is one `.sh` script over the shared `_lib.sh`, and Windows is not a runtime
platform of this project** — it is supported through WSL or Git Bash and through nothing else.
This is a named absence of support, not an oversight (decision of 2026-08-31).

The history without which this rule looks like convenience: article XII once demanded every
task as a `.sh` **and** a `.ps1`, and one rule had six mechanisms holding it — gate `G13` (the
twins change in one diff), three loops in `hygiene.sh`, three CI steps, a `windows-latest` leg,
a 309-line fitness function reading PowerShell as text, and a module choosing the dialect.
Despite them the twins kept diverging: `test.ps1` read a variable it never defined, `start.ps1`
lost `--development`, `_lib.ps1` hard-coded the port. **A second copy of the same logic diverges
faster than the checks can detect it**, and the PowerShell half was written without any way of
running it even once, because `pwsh` was on no developer machine.

Rejected: keeping the twins (the status quo, at the price above); a `windows-latest` leg running
the `.sh` through Git Bash (no Linux Docker, no executable bit on NTFS, a different `PATH`
separator — a leg failing on the harness rather than on the subject of the test); generating the
`.ps1` from the `.sh` (a third artefact that returns to hand editing on the first script outside
the generator's grammar).

Consequences: `G13` is **withdrawn, not free** — the number in an archived change record still
means what it meant ([`../invariants.md`](../invariants.md)); the Python branches whose only
reason was Windows are gone; `check.sh` no longer fails to reproduce just one CI leg, and that
leg is macOS. This is enforced by `scripts/hygiene.sh` and the `scripts` job in CI (a loop over
`scripts/*.sh`: the executable bit, presence in `help.sh`, an answer to `--help`) and by
`test_sdd_paths.py::test_no_module_decides_what_platform_this_is`.

**`scripts/` is the application's interface and never calls the change process.** The process
has commands of its own — `sdd-specs`, `sdd-verify`, `sdd-retro`, `sdd-tests`,
`sdd-lint`, `sdd-preview-mock` — over a library of its own that sources nothing from here, and
what the process may call in `scripts/` is the script contract
([`script-contract.md`](https://github.com/Scalo-Sales-Engineering-Consulting/claude-marketplace/blob/main/plugins/forge/docs/script-contract.md)): `check`, `test`,
`setup` and the lifecycle scripts, by the names `.specconf/stack.json` declares. A script here
that reached into the process's own tree would be the one dependency in the direction the split forbids -- and since 2026-09-09 there is no such tree here to reach into.

Rejected (decision of 2026-09-09, `cr: historical` — the process became independent of the
application it works on, so that one process serves many templates; framework changes are made
on the trunk and carry no `delta.md`): keeping the process's five scripts (`specs.sh`,
`verify.sh`, `retro.sh`, `sdd-tests.sh`, `preview-mock.sh`) in this directory. They put the
process's gates into `check.sh`, its tests into this project's `pytest` and its verdicts into
this project's CI, and a template that wanted a different process would have had to edit five of
its own scripts to get one.

Rejected (decision of 2026-09-09, `cr: historical` — the seam above was cut in this repository
and the process still lived in it; on the same day it moved out entirely, into the plugin
`forge@scalo`. Every link here that reached it by a relative path
(`../../.claude/docs/…`, `../../.claude/skills/_shared/sdd/…`) named a path that exists in no
clone of this template, so each one is now either the URL of the document in the repository
that ships it, or the name of a command that arrives on PATH with the plugin. Framework
changes are made on the trunk and carry no `delta.md`): vendoring the process's documents into
`docs/` so the links could stay relative. That is the second home this section exists to
forbid, and it would go stale the first time the process changed without this template.

## When a decision is an ADR

The classic threshold — "an architectural decision with a rejected alternative" — is too low and
lets almost everything through, because choosing a column name also rejects an alternative. The
effect was observed: the directory swells, ADRs duplicate normative documents, and a question
arises that cannot be settled — does a rule hold because `spec/design/` says so, or because an
ADR says so.

**An ADR is written only when a decision meets BOTH conditions:** it is **cross-cutting**
(reversing it touches more than one module, one layer or one suite) and it is **expensive to
reverse** (undoing it needs a data migration, a rewritten contract or a change in CI, not an
edit to one file). A rejected alternative is necessary and **not sufficient**. A decision that
fails either condition has an address, and it is not `spec/ADR/`:

| Kind of ruling | Home |
|---|---|
| A fact always true of the data | `contracts/invariants/` |
| A deliberate non-goal | [`../invariants.md`](../invariants.md) |
| Where a file goes, what it is called, what it imports | this document |
| The choice of a suite, a fixture or a marker | [`testing.md`](testing.md) |
| A column, a type, a constraint | [`data-model.md`](data-model.md) |
| A contract field, a refusal code | [`api.md`](api.md) |
| A business rule or a flow | `spec/contexts/<context>.md` |

**An ADR is never edited after acceptance.** A later ADR supersedes it, with `supersedes`.
Rewriting a decision in place destroys the reasoning behind it, and then nobody can tell a
settled decision from an accident. Rejected: a lower threshold (it produces a directory in which
a rule has two homes); no ADRs at all (normative documents say what holds **now**, without a
date and without a rejected alternative — and that is the knowledge whose absence makes somebody
take the same lost decision again two years later); an ADR editable in place (after a year it
says what somebody thinks today, not what was decided then).

**The state of `spec/ADR/`: empty, until the first change carried out through `/sdd`.** Eleven
decisions taken between 2026-08-30 and 2026-09-02 without a change record (`cr: historical`)
were written on 2026-09-02 into the normative documents they concern — with a date, a reason and
the rejected alternatives, where the rule stands — because an ADR with no parent in
`spec/changes/` has no history to point back to, and two homes for one rule are the failure
described above. Every future ADR comes out of a change record (`design-adr` writes the draft,
`reconcile-design` gives it a number) and carries that change's `cr:`; the index
`spec/ADR/index.md` is generated by `gen_indexes.py`, and gate `frozen-ids` holds that a cited
`ADR-NNNN` exists.

**A decision taken on the trunk is written into the document whose rule it changes**, in the
shape those eleven used, and gate `recorded-decision` reads it:

```
Rejected (decision of <YYYY-MM-DD>, `cr: historical` — <why this was taken outside /sdd>):

- **The alternative** — and the reason it was not taken.
```

The date, the marker and a reason are all required. `cr: historical` on its own is a label on
the fact that no ADR was written rather than an answer, which is the same bar
`**ADR:** none — <reason>` has to clear in a `delta.md`.

The gate takes this answer **only from a diff that carries no change directory**. Inside `/sdd`
the duty is unchanged — `design-adr` writes the ADR, or the delta says why the edit was
editorial — because an exit available to a change that merely felt like typing it is a way round
both. It reads what the diff **added**, and it asks it of **each** rule document that moved: a
decision covers the edit it was written for, not every later edit of the same file, and a
decision recorded in one document says nothing about a rule that moved in another.

So a decision has four homes, and which one it gets is decided by where the work is done rather
than by preference:

| Where the work is | What records the decision |
|---|---|
| A change, and the decision is cross-cutting and expensive to reverse | an ADR under `spec/ADR/` |
| A change, and the edit carries no decision | `**ADR:** none — <reason>` in that change's `delta.md` |
| The trunk, and the decision is real | the block above, in the document it changes |
| Anything else | a dated row in [`../changes/EXEMPTIONS.md`](../changes/EXEMPTIONS.md), which expires |

Rejected (decision of 2026-09-05, `cr: historical` — this taught `G5` its third answer, and the
gate is the change process rather than the product, so it is recorded here):

- **Leave `G5` as it was.** It had three doors and, from the trunk, no key: both of its exits
  live inside a change directory, and the paragraph above forbids the ADR outright. The work it
  blocks is not hypothetical — `contracts/` and the golden-set split were both done this way —
  and it was invisible only because `.github/workflows/ci.yml` runs the diff-scoped gates on a
  pull request alone. A gate that holds because nothing runs it has been deleted without anyone
  saying so.
- **Send trunk edits through the `spec-exempt` label and a dated row.** It calls a satisfied duty
  an exception. The decision is recorded, in the place this section prescribes; a row would say
  the opposite in the register, expire on a morning when nobody committed anything, and silence
  eight diff-scoped gates in order to silence one — and `EXEMPTIONS.md` reserves rows for work
  stretched across several changes.
- **Write the ADR anyway.** It has no parent in `spec/changes/` to point back to, and it gives
  the rule the second home the whole section exists to prevent.
- **Match the block against the file on disk.** `architecture.md` already holds one. Read that
  way it would have exempted every future edit of the most-edited rule document in the tree, for
  ever, on the strength of a decision taken in September 2026.
- **Take one block anywhere in the diff, as the ADR exit does.** An ADR is a document about a
  decision and stands on its own; this block is a paragraph inside the rule it justifies, and
  its whole value is that the reason sits where the rule sits.

Rejected (decision of 2026-09-10, `cr: historical` — the marketplace moved organisation
and was renamed `scalo` there. Both halves of the citation had to move with it:
the absolute links, which named the organisation this repository was forked out of, and the
install id, because the marketplace's name is what an install resolves by. Framework changes
are made on the trunk and carry no `delta.md`): changing only the URLs and leaving the previous
install id standing in the prose. The id is the argument `claude plugin install` takes, so a
rule document that still names the retired one hands the next reader a command that fails, and
does it in the document that decides where a fact is allowed to live.

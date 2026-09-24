# sdd-app-template

An application template built with the SDD process: FastAPI (`app/`) + React/TS (`frontend/`) +
Postgres, one process on `:8080`. One example feature — **a guestbook** — and beside it a to-do
list, which is not an example and stays.

This repository's value is the **process**, not the product. The system's normative
specification lives in `spec/`; the change process's contract (SDD) in
the process's `project-context.md`.

## The project's structure

```
app/            the FastAPI backend, CUT BY BOUNDED CONTEXT: contexts/<name>/ holds one
                context whole (routers/ → services/ → models/ + schemas/, layered inside it),
                platform/ is the technical slice with no domain rules, core/ + db/ are the
                infrastructure both use, api.py is the aggregate where the /api prefix is
                applied. The cut is by context because CODEOWNERS matches paths, so a
                layer-first tree can never hand one context to one person
                (spec/design/conventions.md § Backend). A context's public API is its
                __init__.py and a fitness test refuses reaching past it
alembic/        migrations — the schema's only owner (never create_all())
infra/          Terraform: two long-lived environments (stage/prod) as DIRECTORIES, plus
                preview/ — one shared layer every per-branch preview borrows and one
                template root applied once per branch, whose state key is chosen at init
                rather than written down (spec/design/architecture.md § Environments)
frontend/src/   the SPA, cut the same way: contexts/<name>/ holds one screen and
                everything only it uses (pages/ components/ hooks/ lib/); components/ui/,
                components/shell/, hooks/, lib/, api/ and routes.ts are what belongs to no
                context; router.tsx is the composition root and the one module allowed to
                bind a path to a context's screen
tests/          pytest in four groups: unit/ (no database), integration/ (with one),
                fitness/ (reads the repository's source), tooling/ (scripts/ and the e2e
                harness). The directory IS the declaration: the three groups without a
                database apply no_db to themselves. fitness/ is a suite of its own
                (`test.sh fitness`, its own junit); `backend` is the other three
e2e/            the black box: harness/ (with no domain words) + suite/ (Gherkin + steps)
                + ui/ (a smoke of the built SPA in Chromium, ordinary pytest —
                spec/design/testing.md § The UI smoke in a browser)
golden-set/     the only corpus of committed data, CUT IN TWO by what the data is for:
                fixtures/ (what the suites read instead of inventing and assert about —
                ordinary, boundary, refused) and seed/ (what a freshly created environment
                opens with, posted through the API by scripts/seed.sh and asserted about by
                nothing). One locator, tests/_golden_set.py, decides where either half lies;
                a fitness test refuses a suite that reads the seed half
scripts/        the human interface to the application: start/stop/test/lint/build/db/…,
                every task one <name>.sh script over a shared _lib.sh. It never calls the
                change process; what the process may call here is the script contract
                (the forge plugin's docs/script-contract.md) — check, test, setup,
                start/stop/status, db, generate — by the names .specconf/stack.json declares
.claude/        the PIN on the change process, and this template's own workers.
                settings.json names one plugin — `forge@scalo`, from the marketplace
                Scalo-Sales-Engineering-Consulting/claude-marketplace — and nothing else, so a fresh clone is one
                command from having the process: `claude plugin install forge@scalo`
                (the marketplace is private, so `claude plugin marketplace add
                git@github.com:Scalo-Sales-Engineering-Consulting/claude-marketplace.git` comes first, once per
                machine — the ssh URL, not the owner/repo shorthand, which resolves
                anonymously and finds nothing).
                It registers NO hook: the plugin's hooks and a project's
                are not deduplicated, so a copy here would run each one twice.
                skills/ holds the eleven skills that are this template's own and could not
                be the process's, because they know FastAPI and React: the eight
                build-* members of the implement fan-out and the three run-* wrappers
                over scripts/. .specconf/stack.json declares them; the process's
                catalogue merges them with its own and refuses a name claimed by both
docs/           the documentation of the SYSTEM, for whoever operates it, and
                non-normative by declaration: how to set up the AWS account, deploy,
                configure, watch, back up, restore and repair it, plus runbooks/ for the
                procedures. Every fact here has its home in spec/ or contracts/ and this
                tree cites it
retro/          the DATA of the process's self-audit loop: corpus/ (archived sessions),
                rounds/, notes/ (dated, appended by the engine's notes.py), fixes.md and
                ledger.jsonl. How the loop works and the prompt that drives it are the
                process's and travel with the plugin.
                Session archives are NOT here — those live in spec/changes/<CR>/sessions/:
                one byte, one home
changelog/      the record of the changes that did NOT go through the process -- one
                <YYYY-MM-DD>-<slug>.md per pull request, written from TEMPLATE.md by
                scripts/changelog.sh and held by the `changelog` CI job. It is the other
                half of spec/changes/, never an overlap with it: a change with a directory
                there writes nothing here. Entries are never edited after the fact, which
                is why they name paths in backticks and never as links
contracts/      the system's boundaries as versioned contracts, WRITTEN BY HAND:
                openapi/ (HTTP), asyncapi/ (events), invariants/ (data invariants). A
                contract is the authority and the code is validated against it —
                the constitution, art. VI. The database schema is NOT here and that is a
                decision: the set of alembic/versions/ revisions is its contract
                (spec/design/data-model.md § Owner of the schema).
                ./scripts/contracts.sh compares it against a dump, and the `contracts` gate guards the shape
spec/           the specification cut by domain: contexts/ (one file per bounded context)
                + two registers (api, data-model) + architecture, conventions, testing,
                invariants, ui/ + ADR/ (the ADRs) + changes/ (the change records + the
                generated status.json: the register of every change)
.specconf/      the process's configuration, editable per project: the stack profile
                (stack.json — what the process knows about THIS template that is not a
                script: its trees, suites, port, refused runners, its own skills, and the
                vendor plugins, MCP servers and hand-off notes it brings), the document
                templates (templates/{change,system}/), the composition of the stages
                (process.json), the model rates (pricing.json — DATA, not code, with a
                calibration date) and the taskboard (taskboard.json — the owner, the project
                number and the field identifiers, because `gh` cannot address a work item's
                fields by name)
```

Two interfaces and two repositories, and the split is not aesthetic: you run `scripts/` and
CI runs them, so each answers `--help` and checks its own prerequisites. The process's own
commands — `sdd-specs`, `sdd-verify`, `sdd-tests`, `sdd-lint`, `sdd-retro`, `sdd-engine`,
`sdd-skill` — arrive on PATH with the plugin and call `scripts/` only by the contract's
names. The dependency runs one way and can be greped for: nothing under `scripts/`,
`tests/`, `pyproject.toml` or `conftest.py` reads the process. Both are one implementation
per platform: a second copy of the same logic always drifts.

The rules for where a file goes and how it is named: `spec/design/conventions.md`. One rule
above them all: a new domain concept = one file per layer, named after the concept; never
`utils.py` / `helpers.py` / `format.ts`.

The specification is organised around domains: a business rule and a flow live in a context
document, a contract field in `api.md`, a column in `data-model.md` — one fact, one home. A
context never lists columns; a register never explains a rule.

## What is an example, and what is the template

**The guestbook is an example and you may delete it.** Four operations through every layer:
`app/contexts/guestbook/models/guestbook_entry.py`, `schemas/guestbook_entries.py`,
`services/guestbook_entries.py`, `routers/guestbook_entries.py`, one Alembic revision, one
screen, a full set of tests in four suites plus Gherkin scenarios.

Deleting it deletes with it: `spec/contexts/guestbook.md`, `spec/design/ui/guestbook.md`, the
entries in `api.md` and `data-model.md`, `e2e/suite/features/guestbook.feature` and the steps
that bind it, the contracts `contracts/openapi/guestbook.yaml` and
`contracts/invariants/guestbook.md`, the guestbook's files in both halves of the corpus
`golden-set/` (never the to-do list's `todo-task-text.json` and `todo-tasks-*.json`), the mockup
`spec/rationale/mockup-guestbook/`, the user guide `docs/user-guide.md` and the request file
`http/guestbook-entries.http`.

**One thing moves before the guestbook goes: the words of the text rule.** Both contexts are held
to one rule for how a text is normalized, trimmed and counted, and its words live in
`spec/contexts/guestbook.md` § `BR-01`, which the to-do list cites. Move them into
`spec/contexts/todo_list.md` first; its § Neighbours says so, and the `frozen-ids` gate goes red on
a citation of `BR-01` left pointing nowhere (`spec/ADR/ADR-0001-todo-list-is-its-own-bounded-context.md`).
The rule's code is already outside the guestbook, in `app/platform/schemas/text.py` and
`frontend/src/lib/text.ts`, and stays. So does the seeder: it loses the half that posts the welcome
entries and keeps the half that posts the example tasks.

**Everything else is the template and stays**, the to-do list (`todo_list`) included: it is a
second domain context, not an example. There is no authentication and that is a named
non-goal (`spec/invariants.md`), not an absence nobody noticed.

## Running and developing

**The scripts are the interface** — run a script, never a command from inside one; each
checks its own prerequisites and takes `--help`. The full list: `./scripts/help.sh`.

```bash
./scripts/start.sh                 # Postgres (compose) + migrations + the app on :8080
./scripts/start.sh --development   # the backend on :8000 with reload + Vite on :5173
./scripts/start.sh --container     # EVERYTHING in Docker: the image + the migration + Postgres
./scripts/start.sh --port 8090     # another port — it decides the poll and TARGET_BASE_URL too
./scripts/start.sh --no-seed       # leave both lists empty; by default an empty guest book or
                                   # to-do list is filled from golden-set/seed/ once the app answers
./scripts/seed.sh --base-url ...   # fill some other environment — a preview, a stage
./scripts/stop.sh                  # stopping
./scripts/status.sh --json         # the state of the machine and the application
```

Migrations and the database:

```bash
./scripts/db.sh migrate            # alembic upgrade head
./scripts/db.sh status             # which revision is applied, what is left
./scripts/db.sh revision "text"    # autogeneration — A FIRST DRAFT, not an answer
./scripts/db.sh reset              # DESTRUCTIVE: drop the database and migrate from scratch
```

Tests and quality:

```bash
./scripts/test.sh                  # everything, in the order that fails fastest
./scripts/test.sh unit             # the rules with no database — seconds, no Docker
APP_TEST_DATABASE_URL=... ./scripts/test.sh backend   # on your own Postgres, no Docker
./scripts/test.sh frontend         # vitest
./scripts/test.sh e2e              # the black box against a live application
./scripts/lint.sh --fix            # ruff + mypy --strict + eslint + tsc
./scripts/check.sh                 # every gate of this application that CI runs
```

`check.sh` is the local answer and not quite the whole one: CI additionally runs
`package.sh --lambda`, the production image's runtime assertions, the macOS leg, the
routing verdict, the frontend suite census, the specification gates and the record a change
made outside the process leaves. `spec/design/testing.md` § What only CI can answer names all
seven, so the gap is a list rather than a surprise.

Run the two fastest of those gates on every commit instead of remembering to:

```bash
uv tool install pre-commit && pre-commit install   # once per clone
```

`.pre-commit-config.yaml` calls `lint.sh` — the same script CI runs, never a tool directly
(article XII). It is an accelerator, not a gate: `git commit --no-verify` walks
past it, which is why the same validators run server-side where nothing can.

Deploying to AWS (`infra/README.md` says what costs what):

```bash
./scripts/package.sh               # the Lambda zip + the SPA, into .sdd/build/
./scripts/infra.sh stage plan      # what would change; it changes nothing
./scripts/preview.sh slug          # which preview this branch gets
```

Deploying is GitHub's, not a workstation's: `deploy.sh` refuses outside Actions, and
the deployment role trusts GitHub's OIDC provider and nothing else, so a laptop has no
credentials for it either. A merge to the trunk deploys to stage on its own once
`AWS_DEPLOY_ROLE_ARN` is set; everything else is asked for — Actions → Preview for a
branch, Deploy → stage for UAT, Release for production. The way back is
`Deploy → mode: rollback`, which moves the alias to the previously published version
and reverts neither the schema nor the SPA (`./scripts/deploy.sh --help`).

After a change to the API contract:

```bash
./scripts/generate.sh              # openapi.json → frontend/src/api/schema.d.ts
```

`schema.d.ts` is committed, and CI regenerates and compares it. `openapi.json` is gitignored:
an intermediate artefact in git goes stale.

## The gates — what turns red and why

Twenty-three checks, in three families. **The gates scoped by a diff** (`check_change.py`) ask about
*this* change and stay silent when the diff does not concern them. **The content gates**
(`check_specs.py`) read the whole tree and answer the same on every pull request. **The two
summary gates** (`spec_summary.py`) report on modules that measure rather than refuse.

A gate is named after what it checks. It used to be numbered — `G1` to `G20` — and the
numbers are gone as of 2026-09-06; the process's `sdd-reference.md` § The old numeric codes maps every
one of them to the name it became, so an archived change record citing `G12` stays readable.
`G9` and `G13` were withdrawn before the rename and keep their numbers, because a name for a
rule nobody raises is an invitation to write an exemption for it.

The register is the engine's `spec_gates.py`; the table a person reads is
the process's `sdd-reference.md` § The gates, and `test_sdd_spec_lint.py` compares it against the
register — the names, their order, the family and the **exemptable** column — so a gate added in
the code and skipped there turns red. Three gates take no exemption: `exemptions`, because an
exemption from the check on exemptions switches it off from inside the file it guards; and the
two summary gates `generated-indexes` and `traceability`, because a stale index is fixed by
regenerating it and `**Verified-by:** manual` IS the exit, cheaper and more readable than any
row. The register imports no other module, which is what makes deriving safe: a gate is nameable
because it is declared, not because something happened to import the module that raises it.

Running them locally: `sdd-specs` (the specification gates — the process's own
command) or `sdd-verify --full` (them and the application's `./scripts/check.sh`, as
one verdict). `check.sh` alone is the application's gates: the tests and the build, nothing of
the process.

## Article XII — do not assemble commands by hand

Never run a tool the stack profile refuses directly — here `pytest`, `vitest`, `ruff`, `mypy`,
`eslint`, `alembic`, `uvicorn` and `docker compose` (`runners` in `.specconf/stack.json`). The
scripts are there for that, they check the prerequisites and they are what CI runs. A command
assembled by hand works for you and not in CI, or the other way round — and the difference is
invisible from a diff. The `PreToolUse` hook the plugin registers refuses such calls; its
message names the script to use instead. The process's own commands — on PATH once the
plugin is enabled — are the bridge from the process into Python; `scripts/` never calls
the process.

## A behaviour change goes through `/forge:sdd`

Every behaviour change goes through a process driven by the `/forge:sdd` skill: a change record in
`spec/changes/<CR>/`, a branch, stages, gates. The specification under `spec/` **never**
changes on its own or after the fact — it travels in the same pull request as the code,
declared line by line in that change's `delta.md`.

Start with `/forge:sdd`, or simply say what you want to change.

## The change flow — branch, pull request, CI, then merge

Nothing is committed to `main` directly. Not a typo, not a comment, not a one-line fix.

```bash
git switch -c <topic>/<slug>          # /forge:sdd cuts its own, sdd/<record>
./scripts/check.sh                    # every gate of this application that CI runs
git add <the files this change touched>   # explicit paths -- never -A, the hook refuses it
git commit                            # an imperative sentence: what the change makes true
git push -u origin HEAD
gh pr create                          # a draft counts, and that is the point
gh pr checks --watch                  # blocks until every check settles, non-zero if one failed
gh pr merge --squash --delete-branch
git switch main && git pull
```

A branch with no pull request open gets no CI run at all: the workflow answers a push to `main`
and a pull request, and nothing else (`.github/workflows/ci.yml`). `check.sh` and the pre-commit
hook cover the loop up to that point, and opening the pull request — as a draft, if it is not
ready to read — is what buys the rest.

The verdict is the aggregate `CI passed`, which waits on every other job, the advisory one
included, so the census stays honest. **It is a required check**: the ruleset on `main` (id
22747644, active since 2026-09-10) demands it, with no bypass actor, so the merge button refuses
what it used to only discourage. `gh pr checks --watch` is still the way to wait for it — it
exits non-zero when a check failed — but it is now a convenience rather than the only gate.

Because the ruleset is real, so is the metadata the checks read. `CI passed` recomputes on
`ready_for_review`, `converted_to_draft`, `labeled` and `unlabeled` as well as on a push, because
`spec-exempt` and `no-changelog` are **permissive** labels: applying one turns red into green and
taking it away turns green into red. A required status is a function of (SHA, pull-request
metadata), and every move of either side has its own event.

`/forge:sdd` cuts the branch and `deliver` opens the pull request, then stops at the URL: the
process never waits for CI, never merges, and nothing polls GitHub. The watch, the merge and the
record of it are yours — `sdd-engine change_state set-link --merge-commit <sha>`, then
`--status merged`.

Never force-push, rebase or amend a pushed commit. The branch carries a checkpoint from every
stage, and a rewrite discards proof somebody may be reading.

## A change this template cannot make alone

The guestbook is this repository's own, and so is everything only the application reads: change it
here and nothing else needs to know. The surface the **process** reads is shared with
`forge@scalo`, and a change to it is half a change until the plugin agrees.

That surface, by path: `.specconf/stack.json` and every semantic in it — the suites, the
traceability form, the signals, the refused runners; the script-contract names and their exit
codes (`0` did it, `1` did not, `4` did what it could and named a gap, `2` the machine was busy);
`.specconf/templates/{change,system}/`, which mirror the plugin's seed byte for byte;
`.specconf/process.json`; the skill names under `.claude/skills/`, which the engine's catalogue
merges with its own and refuses when both claim one; the junit `pytest` writes under the settings
in `pyproject.toml`, because the gate reads that file and never what a tool returned; the `spec/`
tree the gates read; the shape of a change record; and the two actions the workflow resolves at
`.github/actions/sdd-specs@main` and `sdd-tests@main`, which are live the moment they merge there.
The authority is `claude-marketplace/plugins/forge/docs/script-contract.md` and the `$comment`
blocks in the profile itself — read them before moving any of it.

The dependency runs one way and stays that way: nothing under `scripts/`, `tests/`,
`pyproject.toml` or `conftest.py` calls the process, imports it or names its files. **So this
repository never patches the plugin and never vendors a fix.**

When the fix belongs to the plugin, file it at the moment it is found — not at deliver, while the
evidence is still in hand. **These paragraphs address the half of the session that can file** —
the main conversation, which touches git and posts outward. A dispatched worker does neither: it
reports the fault in one line of `PROCESS_FAULT` in its closing block, and the orchestrator banks
that line and files from here. This page does not rank itself against the process on that, and it
does not have to: the precedence is settled in one place, and this is the citation of it —
`claude-marketplace/plugins/forge/skills/_shared/process-failure.md` § Which document wins.

Bank it first, because banking is the one step that cannot fail for want of a network:

```bash
sdd-engine change_state add-fault --cr <CR> \
  --signal '<what it did, and what it cost>' --owner engine
```

Then the `fault-report` skill files it — it runs `sdd-ownership`, fills the form and creates one
issue — and `resolve-fault --filed <url>` closes the entry, or `--unfiled --reason '<which of
them>'` when `gh` is absent, unauthenticated or refused. A fault found with no change record open
to bank into goes straight to the skill, which says so in its report.

**The destination and the label are computed, never written down here.** `sdd-ownership` prints
both from GitHub's own record of the lineage: run in this checkout it answers `template` and names
the marketplace repository for an engine fault, with the label that belongs to a template; run in
a repository created from this one it names a different label from the same command. That is why
neither value appears in this file. Fourteen issues in the marketplace register carry the
template's label and were raised from an instance repository — that is what a label typed from
memory looks like a year later.

Do not stop to ask, and do not search for a duplicate first: a duplicate costs a close and a link,
a report lost with the session that found it costs the evidence. The stack name the title carries
comes from `.specconf/stack.json` § `name`. The body follows the skill's `forms/engine.md`, which
mirrors `claude-marketplace/.github/ISSUE_TEMPLATE/forge-change-request.md` — the authority for
what each section holds — what must become true, the coupling surface, what was observed, what was
expected and by which authority, how it was discovered, the reproduction, the root cause,
**why this template cannot fix it alone**, the proposed resolution and the alternatives rejected,
the blast radius on the other stack, the acceptance criteria and the test that proves them, what
this repository does meanwhile, and the non-goals.

Cite the issue URL in the pull request body and in the change record or the changelog entry, and
say what this repository does until it lands. The opposite direction is the plugin's: its pull
request template carries "Anything a template must follow".

## Every other change leaves an entry in `changelog/`

Not every change is a behaviour change. The scripts, CI, the documentation, the infrastructure
and a repair on the trunk are made with no change record at all — `spec/constitution.md` says
so where it records why the process's files moved. **Those changes write one file per pull
request under `changelog/`**, named `<YYYY-MM-DD>-<slug>.md`, saying what changed, why, from
what to what, how the thing works now, what it means for the process, what it does not change,
and how it was verified.

```bash
./scripts/changelog.sh new "Say what the change makes true"   # the form, dated and named
./scripts/changelog.sh check --base main                      # the gate CI runs
```

The two registers never overlap: a change with a directory under `spec/changes/` is recorded
there and writes no entry, and an entry is never a substitute for a change record. The rules,
and why these files are not under `docs/`: `changelog/README.md`.

The CI job is exempt for three reasons and names the one it used: the diff carries a change
directory, the author is a bot, or the pull request has the `no-changelog` label. That label,
like every label CI branches on, is a repository **setting** and not a file: `git` has never seen
one and a fresh clone carries none, so the exemption is inert until somebody creates it.
`.github/labels.md` registers the three and carries the commands that make them.

## Skills and MCP servers this template brings

None beyond the process's own: the two MCP servers (`sdd-history`, `claude-history`) are
the process's and arrive declared in the plugin's own manifest — there is no `.mcp.json`
here, and `.specconf/stack.json` § `mcp` matches them by the `mcp__plugin_forge_*` names the
client gives them; and the `build-*` and `run-*` skills are this template's
workers, declared in `.specconf/stack.json` § `skills`. A template may bring more — a Flutter
one brings the vendor `dart-flutter` plugin, its skills and the Dart MCP server — and the way to
do it is the same for all of them: enable the plugin in `.claude/settings.json`, declare it under
`plugins`, its server under `mcp` (with the tools the template refuses and the script to run
instead), and what each step of the process should load or may use under `hand_off`. The process
validates every name, renders the hand-off into the worker's preflight brief, checks the plugin
is enabled at session start and refuses the listed tools — and understands none of the content.
`stack.json` is the authority; this section only explains it.

**Every one of those skills is inside the discipline measurement, and each one says so and names
the rule it is charged against** — a `**Measured.**` paragraph citing
`${CLAUDE_PLUGIN_ROOT}/skills/_shared/process-failure.md`, because whoever is charged with a rule
has to have had somewhere to read it. The builders reach it through the worker contract a dispatch
hands them; the `run-*` skills are loaded in this conversation, get nothing from a dispatch, and
cite it themselves. `tests/fitness/test_skill_measurement.py` refuses a skill that carries
neither, and the profile's own § `skills` comment says why the declaration is the tree rather than
a key there.

**The breach count this stack reports went up when that measurement arrived, and the rise is not a
regression.** The engine used to read the parent conversation's calls alone — 30 of 286 in one
measured session, with 3 622 of 5 201 requests executing inside dispatches — so every number
published before `claude-marketplace#211` was a lower bound rather than a measurement. Read a
larger number as the scope widening. The converse is written down as well and holds here: a
falling count of Bash calls is not by itself a measure of quality, and the answer to a number that
grew is never to narrow what is counted.

## Privacy in artefacts (the constitution, art. XI)

An assertion message can quote any value a test saw. That is why `pyproject.toml` sets
`junit_logging = "no"`, the reports from `e2e/reports/` are not committed, and the screenshots
of failed smokes land in the gitignored `.sdd/ui-artifacts/`. **Do not load JUnit files or
application logs into a session** — that is the same road, only longer.

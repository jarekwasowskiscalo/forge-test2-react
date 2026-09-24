# Testing

What proves this system works, with which suite and why that one. Where a test file goes and
what it is called is stated by [`conventions.md`](conventions.md).

## The suites, and what each is for

Four tools, four different questions. A suite chosen wrongly is not slower — it is an answer to
a different question than the one asked.

| Suite | Tool | Asks |
|---|---|---|
| `tests/unit/` | pytest, no database | whether a pure rule is correct, in seconds |
| `tests/integration/` | pytest + Postgres | whether a rule is correct **over real storage** |
| `tests/fitness/` | pytest, reads the repo source as text | whether the structure no compiler holds still holds |
| `tests/tooling/` | pytest, no database | whether `scripts/` and the e2e harness do what they promise |
| `frontend/src/**/*.test.ts` | vitest, node | whether a pure frontend rule is correct |
| `frontend/src/**/*.test.tsx` | vitest, jsdom | whether the screen is **wired** to that rule |
| `e2e/suite/` | pytest-bdd, a live application | whether the behaviour described in business language actually happens |
| `e2e/ui/` | Playwright, Chromium, the built SPA | whether the built application comes up at all and can be used |

**Four groups, two pytest suites.** `.specconf/stack.json § suites` declares
`fitness` — `tests/fitness/` alone, with its own junit at `.sdd/reports/fitness.junit.xml` —
and `backend`, which is the other three groups (`./scripts/test.sh backend` and `--no-db` pass
`--ignore=tests/fitness`). They are apart because they answer different questions — a red
detector says the structure moved, a red service test says a rule broke — and because the
change process attributes a case to exactly one suite: a fitness case collected by both would
land in two junits and be read as whichever came last, so a `**Must be red:**` naming a
fitness case could not be told from a backend one. `check.sh` runs `Fitness tests` as a gate of
its own, before the backend; CI runs it as a step of the `backend` job and on the macOS leg.
`tests/fitness/test_gate_parity.py` holds the two suites disjoint and covering every group.

Rejected (decision of 2026-09-23, `cr: historical` — the `fitness` suite was declared on the trunk
from issue #62 of the 2026-09-20 audit; framework changes are made on the trunk and carry no
`delta.md`):

- **Declare `fitness` and leave `backend` collecting everything.** The smallest diff, and the one
  that makes the declaration a lie: every fitness case would sit in both junits, and the process
  attributes a case to whichever report it read last, so a red detector could still be filed as
  a red backend.
- **One suite per group — `unit`, `integration`, `tooling`, `fitness`.** The ticket asked for the
  one layer the profile was missing, not for `backend` cut finer. `unit` and `tooling` answer the
  same question as `integration` about the product and its tools, and they already have
  `test.sh` entry points; only `fitness` asks about the repository instead.
- **A CI job of its own for `fitness`.** It needs the backend job's locked environment and
  nothing else, so a job would pay for the setup twice. A step with `if: !cancelled()` keeps
  its verdict visible when the backend step is red.

**The directory is a declaration.** The three database-free groups carry a `conftest.py` that
applies `no_db` to everything below, so the marker cannot be forgotten.
`tests/fitness/test_test_layout.py` proves the converse: nothing under `tests/integration/`
carries `no_db`, because such a test would run on a leg that does not stand up a Postgres and
would fail there for a reason unrelated to its subject.

## Backend

`./scripts/test.sh backend` stands up its own throwaway Postgres through testcontainers. There
is no mode in which the suite writes to a developer's database.

A test that needs a **fresh** database — because it counts rows or starts from an empty schema —
asks for the `fresh_database` fixture. It is the **only place that rebinds `SessionLocal`**, and
it rebinds it in every module that holds one, by *discovery* rather than by listing three names.
A service added later is then bound automatically; a hand-written list misses it silently, and
the symptom is one test's data visible in another, arbitrarily far from the cause.

## One machine, one database

Postgres is the **only** engine ([`architecture.md`](architecture.md) § One engine), so every
test in this suite runs on what production runs on — and a green test says something about it.

A machine without Linux Docker is not cut off by this: `APP_TEST_DATABASE_URL` points at a
server that machine already has, and the suite creates its own uniquely named, migrated database
inside it per run and drops it at the end. The macOS leg in CI takes this route, on a Homebrew
Postgres.

A machine that has **neither** a daemon **nor** its own Postgres runs the database-free subset
(`./scripts/test.sh --no-db`), and `check.sh --no-docker` **names the rest a gap** and exits
with code 4. A gate that could not answer is not a gate that passed — and that is the same rule
as with `**Verified-by:** manual`: an omission counted and written down is a considered gap, an
omission passed over in silence is a gap.

The `postgres_only` marker existed while a second engine existed, and it went with it.
`tests/fitness/test_test_layout.py` now refuses its return and refuses the removed engine's name
in first-party Python — because a second engine does not come back as a decision, but as a
branch nobody reviewed as a backend.

## What only CI can answer

`./scripts/check.sh` is the local definition of "will CI pass" and reproduces almost everything.
What it cannot reproduce, named rather than implied:

- **The cross-platform leg.** Proof that the suite runs on macOS, and not only on Linux, needs a
  macOS machine. CI now answers it weekly, on the trunk, on request, and on a pull request
  carrying the `cross-platform` label — not on every pull request, because a macOS runner bills
  at 10× on a private plan.
- **The specification gates.** They are the change process's, not this application's, and
  `check.sh` runs nothing of the process by decision. CI calls them through the composite
  action the forge plugin publishes, which supplies the one thing the process's own CI
  cannot: a pull request in *this* repository, with its merge base, its draft flag and its
  `spec-exempt` label — and the `specs` job recomputes when any of the three moves, because
  `ci.yml` fires on `ready_for_review`, `converted_to_draft`, `labeled` and `unlabeled` as
  well as on a push. Locally the same verdict comes from `sdd-specs`, which arrives with
  the plugin.
- **`./scripts/package.sh --lambda`.** The Lambda package resolving for its target platform is
  asserted in the `backend` job and has no gate on the local list.
- **The image's runtime assertions.** `check.sh` builds the production image; only CI runs it and
  checks that it is non-root, ships the SPA, and answers `/api/health` with no database.
- **The routing verdict.** `changes` reads the diff to decide what a run could skip, which is a
  question that does not exist on a workstation: `check.sh` runs everything, because somebody
  asking "will CI pass" is asking about all of it.
- **The record of a change made outside the process.** The `changelog` job asks whether *this
  pull request* adds an entry under `changelog/`, and reads its base, its author and its labels
  to answer. None of the three exists on a workstation. Rejected (decision of 2026-09-14,
  `cr: historical` — a local run would have to invent a base, an author and a label set, and a
  gate answering a question nobody asked is a gate whose green means nothing): wiring
  `./scripts/changelog.sh check` into `check.sh` as a gate. The same command with `--base main`
  is there for whoever wants the answer before pushing; it is a question about a branch rather
  than a gate over the tree.
- **The frontend suite census.** A vitest run that collects zero tests reads on a dashboard
  exactly like one that passed, and only CI refuses it — the `frontend` job's
  `The frontend suite collected tests` step. `test.sh e2e` has the equivalent for the black box
  (`test_sdd_suite_census.py`, run from inside the script, so `check.sh` reaches it) and the
  frontend has no such thing. This entry is a **declared gap rather than a design**: moving the
  census into `scripts/test.sh frontend` is what Article XII actually asks for, and until that
  happens the gap is on this list instead of being a surprise.

Rejected (decision of 2026-09-16, `cr: historical` — `CI passed` became a required check on
2026-09-10, and a metadata run's aggregate replaces the previous one for the same SHA, so a
partial run is not a cheaper answer to the same question but an answer to a different one):
routing the heavy jobs off a run fired by a pull-request metadata event — leaving a label move
or a draft transition to recompute `specs` and `changelog` alone. It would have saved two to
three minutes and cost the gate: a pull request with a red `backend` would need only a label
added or removed to publish a green required check assembled from the two jobs that did run.
Every type on `ci.yml`'s `pull_request` trigger is a full run, and
`tests/fitness/test_ci_parity.py` refuses a job that starts branching on
`github.event.action`. The saving is available again the day the aggregate can prove that the
jobs it did not run were green on this same SHA; until then it is not.

## A test that flickers is not a gate

**A test whose result varies on an unchanged tree above roughly 2% of runs goes to
quarantine before it is allowed to block anything.** Quarantine means: still run, still
reported, not on the required check — the same tier `ci-advisory` exists for.

The threshold is not the interesting part; the direction is. A gate that fails at random
teaches everybody to re-run it, and a re-run reflex is indistinguishable from ignoring the
gate — so the first genuine failure after a run of false ones is re-run too. Google operated
at roughly 1.5% flakiness and still described it as a burden, which is the scale worth
calibrating against: this is not a threshold you clear comfortably.

**There is deliberately no `--reruns` here, and no plugin that provides one.** An automatic
retry converts a measurement into a silence: the suite goes green and the variability that
would have told somebody stops being visible at all. If a test needs a retry to pass, that is
the finding. Quarantine it, and fix it or delete it — a test nobody trusts and nobody removes
is the worst of the three states.

## The JUnit report — who sees it and for how long

**A JUnit report may leave the runner as a CI artefact with a retention of no more than 7 days.
It may not be committed and its contents may not be printed into a job summary.** This is one
rule for all four suites — backend, fitness, frontend and e2e — and it holds in the direction it is
written in.

The rule exists because for a while the repository said two things at once: a comment beside the
backend suite promised the report would **never** become an artefact, while the same workflow
uploaded two other JUnit reports with a 7-day retention. An absolute promise that is not applied
is worse than a rule with a bound — it teaches that comments beside gates are aspirations.

The bound is article XI of the constitution, so two conditions hold and both are checkable:

- **Captured output is disabled at the source, not at the reader.** `pyproject.toml` sets
  `junit_logging = "no"` for pytest; `frontend/vitest.config.ts` sets
  `includeConsoleOutput: false` for vitest's junit reporter. Without the second, the frontend
  report carried `<system-out>` **on a green run** — the reporter does that by default.
- **Reporter options stand where the reporter is NAMED.** Selecting it from the command line
  (`--reporter=junit`) replaces the whole array from the configuration and takes its options with
  it, so a flag at the caller silently restores the default behaviour.

What remains is the **assertion message**, which no setting removes and which can quote a
field's value. Hence 7 days, and hence an artefact rather than a printout: an artefact has an
expiry date and requires a login, while a job summary is public and stays.

## Coverage is measured and never gated

A threshold invites writing lines for the counter, and a line written for the counter proves
nothing. A number that **falls** is, however, a suite that has stopped reaching somewhere — and
that is a signal worth reading. `--coverage` measures and prints; nothing goes red on the
result.

## Fitness functions

Rules a review would otherwise have to catch every time are checked mechanically. Most read
source rather than importing it; two import `app` for the constants they compare against
(`test_length_constants.py` and `test_golden_set.py` read the length bounds,
`test_data_invariants.py` sweeps `Base.metadata`). None of them needs a database:

| Test | Rule |
|---|---|
| `test_layering.py` | nothing under `services/`, `models/`, `schemas/` imports `fastapi` or `starlette`; dependencies point one way; no router reaches for `SessionLocal` |
| `test_context_boundaries.py` | the bounded context has a **public API** and reaching past it fails the build: no context imports another's submodules (only `app.contexts.<name>`), only the composition root `app/api.py` reaches a context's wiring, every context directory is registered in both aggregates **and** every registration has a directory, the frontend mirrors all of it with `frontend/src/router.tsx` as its root, and the specification and the code agree on which contexts exist — the link being the directory NAME, so there is nothing to keep in sync. **Vacuously true** with one context, so every rule carries a known positive over synthetic input |
| `test_context_declarations.py` | the bounded context's front matter is read rather than decorative: it parses with the repository's one reader, every table it owns is declared by the data model, every screen and feature it names is on disk, every registered screen and feature is claimed by **exactly one** context, every neighbour carries a role/pattern pairing Context Mapper's semantics allow, and every context the API register cites is one that exists. Most of it is **vacuously true** today — one context, no neighbours — so each sweep carries a known positive over synthetic input |
| `test_e2e_isolation.py` | `e2e/` may not import `app`, `alembic`, `scripts` or `tests` — without exception |
| `test_e2e_scenarios.py` | every pytest-bdd step is bound, no step module defines `__all__`, no scenario lacks a `Then`, and a `.feature` contains no wire language |
| `test_golden_set.py` | the corpus obeys its own rules: every file reachable through the locator **and declared in the half it sits in**, an "ordinary" entry really passes `BR-01`, a "boundary" entry stands **to the code point** on the bound computed from the model's constants and the shared trimming rule, a "refused" entry really breaks a rule, no value looks like a real person's data — and **no suite names the seed half**, which is what keeps the two halves apart. It holds `text-measurement.json` to rules of its own (a closed set of verdicts, a length stated exactly when one exists, every input an escape, and known positives proving the corpus can see both halves of the defect it was written for), and names the single frontend module allowed to read it |
| `test_evidence_map.py` | a file handed to an author in § Four file sets **as a new product** has a row in § Evidence map — because an author who got a file and did not get a row picks the claim themselves |
| `test_requirement_citations.py` | a requirement citation names something: every `@pytest.mark.req`, `@req:` tag and `[req:…]` name on a surface `.specconf/stack.json` § `traceability` declares resolves to a record under `spec/changes/` and an `R-n` that record declares, every citation-shaped string on a surface is one its form reads in full (`CR-YYMM-xxxx/R-n`, never a bare `R-n`), and `tests/fitness/`, `tests/tooling/` and `e2e/ui/` cite nothing. The process's `traceability` accounts per change and cannot see a citation of no change; this reads from the citation to the record. A record still carrying the scaffold's `TEMPLATE:` marker comment declares nothing (`tests/_change_record.py`), and the reverse direction — a requirement nobody cites yet — is left to the process, because it is phased |
| `test_test_layout.py` | the directory is a declaration: the database-free groups carry a `conftest.py` with `no_db`, nothing outside `integration/` reaches for the database, the session is rebound only by the shared fixture, the removed engine returns neither as a name in first-party Python nor as a marker, and the table above agrees with the directory |
| `test_command_references.py` | a command named in prose exists: every `npm run <name>` in the scripts, the frontend and CI resolves to a `scripts` entry in `frontend/package.json` |
| `test_infra_layout.py` | the Terraform roots stay the shapes they are meant to be: the environment set is discovered rather than listed, no two roots share a state key or a network, `preview/branch` declares **no** state key and creates no shared infrastructure, every environment is built from the same module, only `prod` pays for a capacity floor, `scripts/infra-check.sh` checks every root that exists, and nowhere is an account identifier or a key written down |
| `test_edge_contract.py` | the edge serves the SPA fallback without rewriting a status or a body it did not produce: no `custom_error_response` anywhere under `infra/` (it is a member of the distribution, so it cannot be narrowed to a behaviour and rewrote the API's refusals too), the fallback is a viewer-request function attached to the static behaviour and **not** to `/api/*`, the function excludes `/api/` and `/assets/`, and the bucket policy can answer that a missing key is missing. The **configuration**, read as text — the behaviour needs a live distribution and is confirmed on the next deploy |
| `test_migration_safety.py` | what a revision may do to a table that already holds rows: a destructive operation in `upgrade()` names why it is safe (`downgrade()` is exempt — it is *supposed* to destroy what its own `upgrade()` built), an index on a table the revision did not create is built `CONCURRENTLY`, and a revision touching a pre-existing table sets a `lock_timeout` so it backs off rather than queueing every query behind itself. The last two are **vacuously true** today — the one revision creates its table and its index together — and say so, because the deploy runs the migration before the code and has no way back |
| `test_documentation_is_current.py` | what `docs/` claims resolves against the code that owns it: every script and flag it tells somebody to type, every variable in both directions — the application's and the reference's — every AWS name and every per-environment number, the repository variables the workflows really read, that no credential or account identifier is written down there, and that every page is indexed, declares its reader and, where it is a runbook, says how you know it worked |
| `test_deploy_surface.py` | no workflow assumes the deployment role without declaring a GitHub Environment, the trust policy accepts environment claims and no `ref:` claim, and the environments the workflows name are exactly the ones it accepts |
| `test_withdrawn_claims.py` | a sentence this repository decided against does not come back into the live tree: the label argument `ci.yml` closed, the equivalence `check.sh` used to claim between itself and CI, the two halves of the withdrawn free-plan paragraph, and any naming of the change process's own workflow file, which the script contract forbids. Phrases rather than meanings, proved on a known positive first. `changelog/`, `spec/changes/` and `spec/rationale/` are excluded rather than exempted: a dated record has to be able to quote what was withdrawn |
| `test_ui_suite.py` | the browser belongs to the smoke: `playwright` imported only under `e2e/ui/`, no Gherkin and no `pytest-playwright` plugin in the lock (§ The UI smoke in a browser) |
| `test_design_tokens.py` | article XIII, the half with no mechanism: no component carries a raw hex or an arbitrary pixel value (`rounded-[14px]`), no stylesheet writes `border-radius` as a number, and every declared radius and type-size token is used somewhere. The only file in which a value may be written as a number is `frontend/src/styles/theme.css`. It also holds the palette's **contrast floor** (`spec/design/ui/system-states.md` § Tokens): every text token clears 4.5:1 against every surface it can be painted on, with one written exemption (`--color-disabled`, which WCAG 1.4.3 exempts) |
| `test_data_invariants.py` | the data invariants `D-01`…`D-03` swept over `Base.metadata` rather than checked on one table: no table is another's archive, no column is a copy of somebody else's with no key between them, every primary key is a UUID with an application-side default. The first two are **vacuously true** today — one table — and that is why each carries a known positive over synthetic metadata |
| `test_invariant_witnesses.py` | every invariant in `contracts/invariants/` carries a `**Witness:**` and a `**Kind of evidence:**`, and the witness resolves to an existing test. `none — <reason>` is a legal answer and costs a sentence: a gap counted is a different thing from a gap passed over |
| `test_length_constants.py` | the three length bounds have one home beside the model or the schemas and one named copy in the browser (`frontend/src/contexts/guestbook/lib/guestbookEntry.ts`), and the copy is legal only while the literals are equal — the generated contract carries no `maxLength`, so nothing else binds them. **It compares numbers and cannot compare units**, which is why `golden-set/fixtures/text-measurement.json` exists beside it: for the whole life of this repository all four literals read `80` while the browser counted UTF-16 code units and every other layer counted code points |
| `test_alembic_env_metadata.py` | the metadata `alembic/env.py` hands to autogeneration knows every table: the file's own `app.*` imports are replayed in a fresh interpreter and `Base.metadata` is asked what it holds. The integration suite could not see an empty metadata, because the session fixture imports every `app.*` module first — this asks about the imports `env.py` itself makes, which is what `--autogenerate` reads |
| `test_gate_parity.py` | the script contract's mechanical half, from this template's side: `check.sh` still files exit 4 as a named gap rather than a failure, it leaves the junit of every suite handed `--junitxml` (backend, fitness) at the path `.specconf/stack.json` names, the two pytest suites are disjoint and cover every group under `tests/`, and every contract script the profile names is committed executable |
| `test_profile_mechanisms.py` | `.specconf/stack.json` answers all four mechanism questions the engine renders into a worker's brief (`storage_contract`, `migration_mechanism`, `readiness`, `binding_target`), every path those sentences name exists, and the readiness route is the one `scripts/_lib.sh` polls and `app/platform/routers/health.py` serves. The engine keeps the four optional, so a key dropped here fails nothing there; this row is what does |
| `test_wave_dependencies.py` | the implement fan-out is ordered by the files its members pass between them: every Python and TypeScript import that crosses from one worker's `writes` into another's — walking on through a module nobody owns — is ordered by `after` in `.specconf/stack.json`, the corpus locator `tests/_golden_set.py` is finished before anything reads it, every implementer waits for every test author, and no `after` stands that neither an import nor that RED rule justifies. Disjoint write sets say two members will not collide; this row is what says one is not reading the other half-written (§ Four file sets, disjoint). Proved on the crossings it was written for first |
| `test_repair_composition.py` | a repair round dispatches the authors its own scope needs: the arithmetic the engine runs over `.specconf/process.json` § `conditional` ∪ `fix_conditional`, re-run from the files, holds that a repair lighting no backend and no specification surface sends `cr-requirements` alone, that no consumer declaring `requires` (this stack's workers, and the engine's `build-tests-uat`) is dispatched by a scope that leaves the author of its input home — which is why a backend repair keeps `cr-scenarios`, whose `§ Test data` `build-tests-integration` takes every fixture value from — that `cr-requirements` carries every declared signal, and that no `cr-*` member narrows the first pass through `conditional`. The detector is proved on the entry as the other stack writes it, which leaves the integration author with no fixtures |
| `test_ci_parity.py` | every `check.sh` gate runs in a named `ci.yml` job and every job is accounted for; the routing census of the top-level paths. This template's, importing nothing of the process |
| `test_action_pins.py` | every `uses:` in a workflow runs a commit and not a tag, with the tag kept beside it for a reader and for Dependabot, and something proposes the bump the pin freezes. What may move is **listed with its reason** -- the process's two composite actions, which track its trunk while it is at 0.x -- and the list clears itself when a reference stops being used. This template's: the engine's own `ci_meta.check_pins` judges the tree the plugin ships from and never reads this one |
| `test_scripts_discipline.py` | no script commits, and `release.sh` is the one that pushes -- a commit from a script is one nobody reviewed, and a second push convention is a reviewed act |
| `test_pipeline_verdicts.py` | a script's verdict survives the pipe that carries it: every executed `scripts/*.sh` sets `set -euo pipefail` and `_lib.sh` sets `set -o pipefail` of its own, no pipeline stands as a condition and no `\|\| true` forgives a whole pipeline outside `lists_line` / `lists_match`, and those two are the only readers of `PIPESTATUS`. Under `pipefail` a condition reads a producer that never ran as "no", and the script contract lives in the exit code alone (issue #61, audit ticket E3-03); `tests/tooling/test_pipeline_helpers.py` runs the helpers, both shells and the stderr verdict |
| `test_junit_config.py` | the junit `test.sh` leaves is xunit2 with attributes only — what the script contract promises the process, and Article XI |
| `test_skill_measurement.py` | every skill under `.claude/skills/` declares that it is inside the discipline measurement (`**Measured.**`) and cites the rule it is charged against, `${CLAUDE_PLUGIN_ROOT}/skills/_shared/process-failure.md`, at the plugin root and never by a path to open. The engine counts every dispatch's calls since claude-marketplace#211, not only the parent conversation's; a `measured` key in the profile would be refused by `stack.py`, so the declaration is the tree and the document the model reads |
| `test_process_pin.py` | `.claude/settings.json` names the process this template installs (`forge@scalo`) and the marketplace it comes from -- and registers **no** hook of its own: the plugin's hooks and a project's are not deduplicated, so a second copy here would run each one twice. It also holds the rule for a vendor plugin this stack does not have yet: `.specconf/stack.json` § `plugins` keeps its stated absence with the rule beside it, and any entry pins one concrete `version` (never a range or the name alone), and a plugin that brings an MCP server is pinned with it -- vacuous until the first entry, and written before it |
| `test_fault_reporting.py` | `CLAUDE.md` says *that* a process fault is filed and never *where* or *under which label*: it names the `fault-report` skill, types neither `from-template` nor `from-instance` and no `--label` onto a `gh issue create`, and cites `process-failure.md`, the document that outranks it on who may post outward. `sdd-ownership` computes the destination and the label from the repository's lineage, so a value written here is right in one repository and wrong in every one created from it |
| `test_process_schema.py` | `.specconf/process.json` declares schema 6 or later and no tier carries `max_lines`. The engine refuses the key at 6 and only names it at 5, so what it cannot see is a profile walking back to 5 to keep a budget; the budgets were withdrawn (claude-marketplace#204) because all six were exceeded on one change and every stage closed anyway, and this stack's numbers were the Flutter template's, byte for byte |
| `test_scripts_syntax_floor.py` | the bare-machine scripts (`preflight.py`, `ci_summary.py`, `app_status.py`, `scenario_census.py`) parse on Python 3.12, and ruff's `target-version` agrees |
| `test_label_registry.py` | the labels CI branches on are declared rather than only promised: every label an `if:`, a `case` arm or Dependabot reads has a row in `.github/labels.md`, every row has a reader, and every row's cited document still names its label. A label is a repository **setting** and not a file, so a clone carries none — this suite proves the names agree, and the registry carries a dated claim for the half that needs the API |

This table may be cited **only** for `tests/fitness/`; `tests/fitness/test_test_layout.py` holds
that. Agreement between the schema and the specification is proved by
`tests/integration/test_migrations.py` — on a real database, so in the integration suite, not
here.

Rejected (decision of 2026-09-23, `cr: historical` — the artefact line budgets were withdrawn and
the profile raised to schema 6, `test_process_schema.py`, taken on the trunk from issue #64 of the
2026-09-20 audit; framework changes are made on the trunk and carry no `delta.md`):

- **Re-derive the numbers for this stack.** A budget the engine prints a multiplier for and
  refuses nothing on is advice however well it is measured. It was exceeded six times out of six
  on one change, with every stage closing anyway. The engine withdrew the key
  (claude-marketplace#204), and a stack-specific number would be a key nobody reads.
- **Keep the Flutter numbers as a shared default.** Byte-identical values were the evidence that
  nobody had measured this stack. Keeping them would state the opposite.
- **Stay on schema 5 and just delete the key.** At 5 the engine tolerates the key and only names
  it, so a budget could come back without a refusal. At 6 it is refused, and this module keeps the
  profile there.

Rejected (decision of 2026-09-23, `cr: historical` — who files a process fault, and under which
label, stopped being written into `CLAUDE.md`, `test_fault_reporting.py`, taken on the trunk from
issue #65 of the 2026-09-20 audit; framework changes are made on the trunk and carry no `delta.md`):

- **Keep the `gh issue create` line and only correct the label.** The label depends on where the
  command is run from, not on this stack. A repository created from this template inherits the
  page, and any value that is right here is wrong there. `sdd-ownership` reads the lineage every
  time.
- **Rank this page against `worker-contract.md` in words of its own.** That would be a third
  statement of one rule. The precedence is settled in `process-failure.md` § Which document
  wins, and this page cites it.
- **Require a duplicate search before filing.** A duplicate costs a close and a link; a report
  lost with the session that found it costs the evidence. The rule stays as it was.

Rejected (decision of 2026-09-23, `cr: historical` — every skill declares that it is inside the
discipline measurement and cites the rule it is charged against, `test_skill_measurement.py`,
taken on the trunk from issue #67 of the 2026-09-20 audit; framework changes are made on the trunk
and carry no `delta.md`):

- **Declare it as a `measured` key in `.specconf/stack.json` § `skills`.** `stack.py` allows an
  `operational` skill `kind` and nothing else, so the key would refuse the profile at import. The
  declaration is the tree, and it goes where the model reads it.
- **Leave the workers to the worker contract alone.** The `run-*` skills are loaded in the main
  conversation and get no contract from a dispatch. A rule reaches only the readers it is written
  for, and 66 of 69 charges in one audited session fell on a reader nothing had pointed at it.
- **Keep the breach count comparable by narrowing what is counted.** The count went up because
  the engine now reads the dispatches (claude-marketplace#211). The old number was a lower bound,
  and narrowing the scope would make it one again.

Rejected (decision of 2026-09-23, `cr: historical` — a script's verdict gained a rule that it
survives the pipe carrying it, `test_pipeline_verdicts.py`, taken on the trunk from issue #61 of
the 2026-09-20 audit; framework changes are made on the trunk and carry no `delta.md`):

- **Prove it only by running the scripts.** `tests/tooling/test_pipeline_helpers.py` does run
  the helpers, the five contract codes under bash and zsh, and the stderr verdict. But a pipe
  standing as a condition fails only when its producer fails. That is the case no ordinary run
  reaches, so a new site would pass every behavioural test until the incident. Reading the
  source is what finds it before then.
- **Let shellcheck hold it.** Shellcheck has no rule for a pipeline read as a condition under
  `pipefail`, and the one it does have for `$?` (SC2181) points the other way. A rule nobody
  enforces is a comment.
- **Read `${PIPESTATUS[0]}` at each site.** It is bash's spelling (zsh's is
  `${pipestatus[1]}`), it is overwritten by the next command, and each copy is one more place
  to get the SIGPIPE case wrong. The first draft of the shared helpers got that case wrong
  themselves. Two helpers are the only reader, and this module keeps them the only one.

Rejected (decision of 2026-09-23, `cr: historical` — requirement citations gained a reader on
this side, `test_requirement_citations.py`, taken on the trunk from issue #59 of the 2026-09-20
audit; framework changes are made on the trunk and carry no `delta.md`):

- **Trust the process's `traceability` alone.** It accounts per change, from the record to the
  citation, so a citation of a record that does not exist belongs to no change and is never read
  — and over a tree with no record it is green on an empty set.
- **Import the engine's patterns instead of copying them.** Nothing under `tests/` may reach the
  process. The three citation forms and the declaration heading are copied from its
  `traceability.py`, which keeps a drift visible in a diff rather than silent.
- **Check the reverse direction too — every declared requirement cited.** It is phased: between
  the requirements stage and the first implement wave real identifiers exist and no test cites
  them yet. Knowing the stage is the process's (claude-marketplace#192), and a fresh record
  turning this suite red would be a false alarm on every change.

Rejected (decision of 2026-09-23, `cr: historical` — the profile's four mechanism sentences
gained a reader on this side, `test_profile_mechanisms.py`, taken on the trunk from issue #69 of
the 2026-09-20 audit; framework changes are made on the trunk and carry no `delta.md`):

- **Let the engine hold them.** It keeps all four optional until every template declares them, so
  a key dropped here would load cleanly and just print `(none declared)` in the brief. Making them
  mandatory is the engine's call, filed as claude-marketplace#281. This module refuses the gap on
  this side until then.
- **Check only that the four keys are present.** A sentence that names a moved file or a
  different health route is worse than no sentence, because the brief outranks the skill. So the
  paths and the readiness route are read against the tree too.
- **Compare this profile with the Flutter one key for key.** A profile is allowed to describe its
  own stack (`junit_flag`, `no_db_args`, `ui`), and the other repository is out of reach from
  here. The differences are stated in `.specconf/stack.json`'s top comment instead.

Rejected (decision of 2026-09-23, `cr: historical` — a repair round's composition gained a reader
on this side, `test_repair_composition.py`, taken on the trunk from issue #60 of the 2026-09-20
audit together with the three `fix_conditional` entries it holds; framework changes are made on the
trunk and carry no `delta.md`):

- **Copy the Flutter entries as they stand.** There, `cr-scenarios` carries only the observable
  surfaces. Here `build-tests-integration` also requires `scenarios.md` and takes every fixture value
  from its `§ Test data`, so the same entry would send a backend repair's test author out with no
  author for its fixtures. The known positive in the module is exactly that entry.
- **Narrow a backend repair to `cr-requirements` alone, for a clean 3→1.** It is the narrowing
  #60 § 13 names as forbidden: it leaves out an author who has something to write.
- **Leave `cr-requirements` absent instead of listing every signal.** To the engine, absence and
  completeness read the same. To a person they do not: absence is the state that let a repair round
  cost as much as its change, and it says nobody measured.
- **Ask the engine for the composition.** Nothing under `tests/` may reach the process. The one-line
  arithmetic is re-run from the two profile files. The one fact copied from the plugin is
  `build-tests-uat`'s `requires`.

Rejected (decision of 2026-09-07, `cr: historical` — the context declaration gained a reader,
and which surface reads it is a choice about suites, which is what this document owns;
specification-shape changes are made on the trunk and carry no `delta.md`):

- **Put it in `check_specs.py` with the other content gates.** It is a rule about `spec/`, and
  that is where rules about `spec/` are enforced. Against it: the content gates answer the same
  on every pull request and must stay importable with nothing installed, while this check reads
  `spec/design/data-model.md`, `spec/design/api.md`, `e2e/suite/features/` and `spec/design/ui/`
  and cross-references all four. That is a detector over the repository's own source, which is
  the definition this document gives of a fitness function.
- **Leave the header unread and check the same facts by grep in CI.** A grep answers "the string
  is there"; it cannot answer "claimed by exactly one context", which is the half that fails in
  practice — an orphan and a double claim both read as ordinary text.
- **Write no known positives, since the rules hold today.** Every sweep here is vacuously true
  with one context and no neighbours, so without them the module would assert nothing and pass
  for ever. `test_data_invariants.py` settled this argument first, over a single table.

Rejected (decision of 2026-09-09, `cr: historical` — the process's gate no longer restates
`check.sh` gate by gate and no label-parity test compares the two; framework changes are made
on the trunk and carry no `delta.md`): keeping the mirror. The gate now calls `check.sh` by the
name the script contract fixes and reads the suites' junits it leaves behind
(the process's `script-contract.md`), so "the gate is CI" holds by construction; what the
template still owes the contract — the three-state exit, the junit path, the executable bit —
is proved here by `test_gate_parity.py`, from the template's own files and without importing
the process. Also rejected: proving those three things from the process's side, which would
make the template's tests depend on the process — the direction the split forbids.

Rejected (decision of 2026-09-16, `cr: historical` — `test_scripts_discipline.py` allowed
exactly one script to commit, and the script that did can no longer do it, so the rule is
amended here rather than left describing a repository that does not exist; framework changes
are made on the trunk and carry no `delta.md` in which to declare the edit):

- **Keep "one script commits, and it is `release.sh`".** It described a release that wrote a
  version into `pyproject.toml` and put the result on the trunk. The branch ruleset refuses
  that push to everybody — `bypass_actors` is empty — so the allowance covered something that
  could not happen, and the commit it allowed left `uv.lock` naming the version before it.
  A release now tags a commit a pull request already put there. Allowing a commit nothing
  makes is an exemption waiting to be used by the next script that wants one.
- **Drop the commit half and police only the push.** The detector would then be silent about
  the thing that caused the incident this test exists for — three commit conventions side by
  side — and a rule that once had a reason reads as arbitrary the moment its reason is
  deleted rather than tightened.

Rejected (decision of 2026-09-16, `cr: historical` — the CloudFront edge was rewriting the API's
own refusals into `200 text/html`, and no suite in this repository could have seen it, so the
table gains `test_edge_contract.py`; the repair was made on the trunk and carries no `delta.md`
in which to declare the edit):

- **Put the assertions in `test_infra_layout.py`.** That file is about the Terraform **roots** —
  which ones exist, what they pin, which state key they hold — and an edge behaviour is a
  property of one module's inside. A file that guards a shape and also guards a rule is the
  `utils.py` of test modules: the next unrelated rule goes there too, because it already went
  there once.
- **Pin nothing, and rely on the issue's acceptance criteria.** Those are measured through a
  live distribution, which is the honest way to prove the behaviour and no way at all to stop
  the configuration coming back — the two `custom_error_response` blocks would have returned
  through a green suite. **The gap is named rather than closed:** what is checked here is the
  configuration, and the behaviour is confirmed on the next apply.

Rejected (decision of 2026-09-16, `cr: historical` — three labels decide what CI does and two of
them did not exist, so the table gains `test_label_registry.py`; a label is a repository setting
and the repair was made on the trunk, so it carries no `delta.md` in which to declare the edit):

- **Ask the GitHub API whether the labels exist.** It is the question that actually went
  unanswered, and it is the one this suite may not ask: every module here runs with no network
  and no token (`tests/fitness/conftest.py`), so such a test would be red on an aeroplane, red
  on a fork, and green only where a credential happened to be. **The gap is named rather than
  closed:** what is checked is that the register and the automation agree on the names, and
  `.github/labels.md` carries a dated claim, re-checkable in one `gh` command, for the rest.
- **Check it in CI instead, where a token exists.** That buys the real answer and spends the
  property that makes this directory worth having: a fitness function answers the same on a
  workstation as in a run, which is why an author can see the rule before a reviewer does. A
  check only CI can run belongs in § What only CI can answer, and this one is not worth a job.
- **Keep the labels in the modules that read them.** `changelog.sh` knows its own arm and
  `ci.yml` knows its own `if:`, and neither can know it is the last reader of a name nothing
  created. The register exists because the fact is about the repository rather than about
  either file, and a fact split between two files is the one nobody owns.
- **Assert the number of labels.** The first draft did, and it would have turned red on the
  correct act of retiring one. What is asserted is that no row is skipped by the parser — the
  failure that would make every other rule here vacuous.

Rejected (decision of 2026-09-16, `cr: historical` — every `uses:` in the five workflows ran a
mutable tag, so the table gains `test_action_pins.py`; the repair was made on the trunk against
issue #31 and carries no `delta.md` in which to declare the edit):

- **Rely on the engine's `ci_meta.check_pins`.** It states the same rule, and it has never read a
  line of this repository: its `github_dir()` walks up from the **plugin's** own root, so it
  judges the tree the process ships from. A rule enforced somewhere else, over somebody else's
  files, is a rule this repository does not have — and the 47 unpinned steps are what that reads
  like from here.
- **Put the assertions in `test_ci_parity.py`.** It already opens `ci.yml`, which is exactly the
  argument that makes it the wrong home: that file is about the **map between gates and jobs**,
  and a pin is a property of one step. The same reasoning `test_edge_contract.py` records against
  `test_infra_layout.py` above — a file that guards a shape and also guards a rule is the
  `utils.py` of test modules.
- **Pin the process's two composite actions along with the rest.** `ci.yml` argues `@main` where
  it uses them and `CLAUDE.md` makes "live the moment they merge there" a property rather than an
  oversight; pinning would have traded a reviewed decision for a pin-bump pull request per engine
  release. They are **named in the module with their reason**, and the list clears itself when a
  reference stops being used — which is the difference between a decision and a blind spot.

## The reference corpus (golden set)

`golden-set/` is the only home of committed data this project ships, and it is **cut in two by
what the data is for**. What each half is, and what it owes, is
[`golden-set/README.md`](../../golden-set/README.md); what belongs to testing is here.

| Half | What it is | Read by | Lifetime |
|---|---|---|---|
| `golden-set/fixtures/` | what the suites read instead of inventing | pytest, the black box | wiped before every scenario |
| `golden-set/seed/` | what a freshly created environment opens with | `scripts/seed_golden_set.py` | the life of the environment |

The seeder reads the **boundary fixture too**, and only under `./scripts/seed.sh --boundary`,
when somebody asks for a preview that shows the limits. That is the one crossing between the
halves and it is deliberate (`golden-set/README.md` § Rules only `fixtures/` obeys); it means
the fixture half has a second reader whose reason to change lives outside the test suites.

**Only the fixture half is a testing artefact.** The seed half is an environment's initial
state and is specified in [`architecture.md`](architecture.md) § What a new environment starts
with. It is named here because for a while it was not named anywhere: the seeder posted
`entries-ordinary.json`, this section said the corpus had two readers, and both statements were
about the same three files.

**No suite asserts about the seed half, and `tests/fitness/test_golden_set.py` enforces it.**
A test that reaches for it makes the two halves one corpus again under two directory names:
the seed data could then no longer change for the reason it exists — to make a screen worth
judging — without reddening a suite. That is the coupling the split removed, and the rule is a
check rather than a convention because it was rediscovered rather than foreseen.

### The fixture half

Three files, each with one story:

| File | Story | Read by |
|---|---|---|
| `entries-ordinary.json` | ordinary entries in **writing** order — non-ASCII characters, a multi-line message, single-character entries | `test_guestbook_entries_corpus.py`, the e2e scenarios |
| `entries-boundary.json` | values **exactly** on the bound, each of which must be accepted | as above |
| `entries-refused.json` | entries the rules refuse, each with a refusal code | as above |
| `text-measurement.json` | how a field is trimmed and how long it is — **cases, not entries** | `test_entry_text_rules.py` **and** `frontend/src/contexts/guestbook/lib/entryText.test.ts` |

**One file in that table is read by the browser, and it is the only one.** Every other fixture
is sized by what the server must prove, so a component asserting against one acquires a
dependency whose reasons to change live in another suite. `text-measurement.json` is sized by
what the two sides must AGREE about — and a claim about agreement cannot be checked from one
side, while a second copy beside the browser's test would be two lists nothing holds equal.
`tests/fitness/test_golden_set.py` names the one module that may read it and refuses every
other file in `frontend/src` exactly as before; `golden-set/README.md` § The frontend carries
the reasoning.

Rejected (decision of 2026-09-17, `cr: historical` — where the shared corpus lives and what
binds the two sides, decided on GitHub issue #28, outside `/forge:sdd`):

- **Put the corpus under `contracts/` instead, where no rule forbids the frontend to read it.**
  It is defensible — the file does describe a boundary — and it costs more than it saves:
  `contracts/<kind>/<area>.yaml|.md` admits no `.json`, a new subdirectory owes a `README.md`
  with a declared compatibility mode, and the `english` gate's non-ASCII exemption names
  `golden-set/` and nothing else. Three documents would have had to move so that one fitness
  rule need not gain one named exception.
- **Give each language its own copy, held equal by a fitness test.** It is the shape this
  repository already uses for the length constants — and it is the shape that produced the
  defect. A test can compare two literals; it cannot compare what two languages do with them.
- **Keep `test_length_constants.py` as the only binding and widen its assertions.** It reads the
  TypeScript as text with a regular expression. It can see that a literal is `80`; there is no
  extension of it that can see what `.length` counts.

**The fixture half is a feeder for parametrisation, not a set of files to look at.** A test
takes all its cases at once (`pytest.mark.parametrize`), and a Gherkin scenario takes one **by
the sentence** the corpus carries for it. That is what lets a `.feature` say `the signature is
all spaces` rather than `author_whitespace_only`, with no second list that has to agree with the
corpus.

**Bounds are computed from the model's constants, never transcribed.** The boundary file was
produced from `AUTHOR_MAX_LENGTH` and `MESSAGE_MAX_LENGTH`, and
`tests/fitness/test_golden_set.py` checks that agreement on every run — so moving a rule reddens
the corpus instead of silently invalidating it.

**The order in `entries-ordinary.json` is WRITING order.** The list returns the reverse
(`BR-04`), and the test asserts **the reversal of the file** rather than a hand-written list —
because the first is a claim about a rule and the second is a second copy of the data.

**Hostile input does not belong in the corpus.** The boundary runs where what a guest could
really send ends: a signature of nothing but spaces **belongs** (that happens), while bytes
built to break a parser do not. Those live in the test's code, beside the assertion that
explains them.

**The frontend reads neither half.** Component fixtures are synthetic and written on the
spot: a component test that needs committed reference data is a test asking a question about the
corpus. Two suites read the fixture half — pytest and the black box — and `seed_golden_set.py`
reads the seed half always and the boundary fixture on request.

Rejected (decision of 2026-09-05, `cr: historical` — both corrections were found by auditing
this document against the code it describes, on the trunk, where `spec/ADR/` is not yet open
and there is no `delta.md` to declare an edit editorial in):

- **Remove `seed.sh --boundary` so the sentence becomes true again.** It is the cheaper
  sentence and the worse product: the flag exists so a person can raise a preview that shows
  the limits, which is exactly when a reviewer wants to see them. The coupling it creates is
  real and belongs in this document rather than being designed away to keep a table tidy.
- **Make the two fitness modules stop importing `app`.** That means transcribing
  `AUTHOR_MAX_LENGTH` and `MESSAGE_MAX_LENGTH` into the tests — which is the exact practice
  § Bounds are read from the constant forbids two sections below, and which
  `test_length_constants.py` exists to catch.
- **Say nothing and let the preamble stand.** It is the sentence a reader uses to decide
  whether a new fitness test may import the application. Wrong, it answers "no" to a question
  the tree answers "yes" to twice.

### The black box owns the database it runs against

The e2e suite truncates before every scenario (§ End-to-end), so it and seed data cannot share
an environment: whichever ran second would be looking at the other's world. `test.sh` therefore
starts the application with `--no-seed`, and `reset_target_database` refuses any database that
is not marked as this run's to empty — so pointing the black box at a seeded preview takes a
deliberate act, and empties it.

**The mark is content of the database, not a property of the connection string**, and that
distinction is the rule rather than an implementation note. "The host reads as local" is a
statement about text: an SSH tunnel or a `kubectl port-forward` to a shared database answers on
`127.0.0.1`, and `hostaddr`, `service=` and `PGHOST` each let a string name one target while
libpq reaches another. So ownership is read where it cannot be forged by configuration —
`COMMENT ON DATABASE`, carrying the run id `test.sh e2e` minted, read back on the very
connection that will truncate and before any statement that deletes is composed.
`E2E_ALLOW_REMOTE_RESET` is compared by equality, never for truthiness, and takes either `1` or
the name of the one database it consents to; `test.sh` accepts only the second form as leave to
mark a database it did not itself provision. The tables `REQUIRED_TABLES` names remain a sanity
check and are not permission: a shared environment has them too.

Rejected (decision of 2026-09-05, `cr: historical` — the golden-set split was carried out on
the trunk, so its reasoning is recorded where the rule lives rather than in `spec/ADR/`;
[`conventions.md`](conventions.md) § When a decision is an ADR says why):

- **Leaving the corpus one directory and telling authors to be careful.** That is what stood,
  and care is not a mechanism: the seeder and the suites pulled the same file in opposite
  directions for months without either author noticing.
- **Naming the seed half a testing artefact too**, so one author owned both. It is the shape
  that produced the conflation; what a new environment shows is a product decision, and
  § Four file sets hands out only the fixture half in consequence.
- **Letting the black box run against a seeded environment**, with the seeder re-running
  afterwards. Two mechanisms would then own one database, and a scenario that failed would not
  say which. The rule above is the cheaper answer: one owner, and a deliberate act to cross it.

Rejected (decision of 2026-09-16, `cr: historical` — the mark replaced the address check on the
trunk, so its reasoning is recorded where the rule lives rather than in `spec/ADR/`;
[`conventions.md`](conventions.md) § When a decision is an ADR says why):

- **Proving the guard on a fake connection alone.** That is what stood, and it made exactly two
  claims: one connection-string shape and one opt-in value — the only two cases the old
  implementation got right. What a fake cannot say is that the mark the guard reads is one
  Postgres stores and gives back, so a guard that refused every run would have looked identical
  to one that worked. The negative cases stay on a fake, because
  `tests/tooling/test_e2e_harness.py` may not hold a real connection string; the positive
  control moved to `tests/integration/`, where a test can make a database of its own.
- **Asserting that the refusal raised.** "It raised" and "it sent no instruction that deletes"
  are different claims, and only the second is what a guard on this function promises. Hence the
  `connect` seam: every negative case drives the real `reset_target_database` and asserts the
  connection was handed nothing destructive.
- **A fixture holding one open connection for the whole file.** `reset_target_database` takes an
  ACCESS EXCLUSIVE lock, so a session the test was still holding would turn a refusal into a
  wait and then into a `statement_timeout` — a green-looking fault with an entirely wrong name.

## Choosing what proves what

Five rules, each of which has already been got wrong here once.

**A numeric bound gets a fixture on both sides, not only the breaking one.** A bound proved only
where it fails is a bound nobody has shown to stand in the right place: the test passes
identically whether the limit is 80 or 8000. Hence the pair of claims in
`tests/unit/test_guestbook_entry_schemas.py` — exactly the maximum passes, one character more
falls.

**A bound is read from the constant, never transcribed as a literal.** A test that writes `80`
is a test that, once the rule moves, proves the old number. The fixtures import
`AUTHOR_MAX_LENGTH` and `MESSAGE_MAX_LENGTH` from the model — on both sides of the bound at
once.

**A rule the index holds is proved by a concurrent insert — never by a single call.**
Constitution, article VI: a constraint not enforced by the storage layer falls over under
concurrency. A unit test and one service call pass **identically** over an index and over a
read-before-write — and those are two different systems, only one of which is a rule. This
schema has no uniqueness constraint today, so there is nothing of that class to break; it comes
back with the first one.

**A rule about a VALUE gets a generator; a rule about SHAPE gets a sweeper.** An invariant saying
"every primary key is a UUID" is a claim about a value and a generator proves it: an identifier
drawn from the whole space must survive the trip to storage and back. An invariant saying "an
entity has one row for its whole lifecycle" is a claim about the shape of the schema and **a
generator has nothing to draw for it** — it is proved by a sweeper over `Base.metadata`, which
will see the NEXT table rather than the one somebody remembered. A property-based test put
behind a rule about shape always passes, says nothing, and looks like the strongest test in the
suite while doing it: that is a state worse than having no test, because it stops anybody from
checking. That is why an invariant's witness in `contracts/invariants/` declares a **kind of
evidence** rather than only a path. Both halves are visible on `D-03`:
`tests/fitness/test_data_invariants.py` asks about shape, and
`tests/unit/test_data_invariant_properties.py` — with a generator — about value.

**A rule copied into the browser is proved on both sides, on the same bound.** `BR-01` lives in
Pydantic and in `frontend/src/contexts/guestbook/lib/guestbookEntry.ts`. The copy is deliberate — a guest should see
"the entry is too long" while typing rather than after a round trip — and that is why both sides
have a test on the same bound. Without it the copy diverges silently, and the symptom is a form
that lets through something the server will refuse.

## Evidence map — how it is read and written

This section is the map the implementation stage's test authors write from. `traceability` does
not read it — the gate reads the change's `requirements.md` and the test files themselves — but this is where the
assignment it will go looking for is decided: every requirement has an **owner in exactly one
suite**, and the citation is in a form that surface can carry, which the gate now enforces rather
than merely documenting.

Rejected (decision of 2026-09-05, `cr: historical` — the gate is the change process rather than
the product, and this document is where the choice of a marker lives, so it is recorded here):

- **Leave `traceability` matching the bare identifier, and soften this section instead.** The gate scanned
  every eligible file for `CR-YYMM-xxxx/R-n` and counted it wherever it fell — in a comment, in a
  docstring, in a plain string, in a skipped test. Softening the documents to match would have
  been honest about the mechanism and wrong about the intent: five `SKILL.md` files instruct
  their authors to write one of the three forms above, and `build-tests-e2e` tells its agent
  outright that the gate "parses them verbatim". The measurement settled it — all twenty-five
  references in the tree were already in their documented form, so the strict reading cost
  nothing and the loose one was protecting no existing work. A gate looser than the instruction
  its authors are given teaches that the instruction is decorative.
- **Assign `R-3` a frontend witness by writing one.** The screen's honest share of an ordering
  rule is that it does not impose an order of its own, and a test for that already existed —
  this section already named it. Writing a second would have produced a citation whose subject
  was the counter it satisfied.

The identifier is always fully qualified — `CR-2608-a7f3/R-3`, never a bare `R-3`, because two
changes in flight numbering from one collide at the moment the gate reads them. The rest of this
document names this section **§ Evidence map** and it is the same section.

**In the template this map is empty, and that is correct.** There is no open change, so there are
no requirements to assign. What remains is the *shape*: both tables below show what a filled map
looks like, on the example of the files the guestbook actually has. The first real change fills
them with its own.

| Rule | Owner | Proof |
|---|---|---|
| `BR-01` — an entry requires a signature and a message, measured AFTER trimming | `tests/unit/` | `tests/unit/test_guestbook_entry_schemas.py` (the bound from both sides, from the constants) · `tests/integration/test_guestbook_entries_corpus.py` (every corpus case, on `POST` and on `PATCH`) · `frontend/src/contexts/guestbook/lib/guestbookEntry.test.ts` (the copy of the rule in the browser, the same bound) · `frontend/src/contexts/guestbook/components/EntryComposer.test.tsx` (the composer card is wired to it — the button stays closed until both fields have content) · `frontend/src/contexts/guestbook/components/EntryCard.test.tsx` (and the editor in the card: an amendment may not do what a new entry is forbidden) |
| `BR-02` — an amendment moves `updated_at` and never `created_at` | `tests/integration/` | `tests/integration/test_guestbook_entries_service.py` · `frontend/src/contexts/guestbook/components/EntryCard.test.tsx` (the "edited" marker is derived, not read from a column) · `e2e/suite/features/guestbook.feature` |
| `BR-03` — deletion is permanent, a second one refuses | `tests/integration/` | `tests/integration/test_guestbook_entries_service.py` · `tests/integration/test_guestbook_entries_corpus.py` (over the whole seeded guestbook) · `frontend/src/contexts/guestbook/components/DeleteEntryDialog.test.tsx` (the warning, focus, not closeable mid-flight) |
| `BR-04` — the guestbook has an order both ways, a total order | `tests/integration/` | `tests/integration/test_guestbook_entries_service.py` (a tie is settled by `id` and turns with the direction) · `tests/integration/test_migrations.py` (an index behind the promise) · `frontend/src/contexts/guestbook/pages/GuestbookPage.test.tsx` (the screen does not re-sort) · `e2e/suite/features/guestbook.feature` |
| `BR-05` — narrowing by a phrase, reading a piece at a time, two numbers | `tests/integration/` | `tests/integration/test_guestbook_entries_service.py` (signature or message, case, wildcards literally, `total` ≠ the length of the piece) · `tests/integration/test_guestbook_entries_router.py` (the parameters and their bounds on the wire) · `tests/integration/test_guestbook_entries_corpus.py` (over the corpus, walking the pieces) · `frontend/src/contexts/guestbook/lib/entryListCopy.test.ts` (the sentences about the numbers, and the one an unsettled answer carries) · `frontend/src/contexts/guestbook/lib/entryPaging.test.ts` (which piece to ask for, at and past the contract's ceiling — the arithmetic no screen test can see, because it answers correctly for every guestbook smaller than a hundred) · `frontend/src/contexts/guestbook/hooks/useEntryQueryParams.test.tsx` (the address is the source of truth and a navigation cancels a deferred write) · `frontend/src/contexts/guestbook/pages/GuestbookPage.test.tsx` (the question travels to the server and lives in the address) · `e2e/suite/features/guestbook.feature` |
| Contract: refusal codes and statuses | `tests/integration/` | `tests/integration/test_guestbook_entries_router.py` · `frontend/src/api/problem.test.ts` |
| Schema: columns, types, the index | `tests/unit/` + `tests/integration/` | `tests/unit/test_guestbook_entry_model.py` (what the model **declares**) · `tests/integration/test_migrations.py` (what Alembic **creates**) — two independent claims about one schema, so a divergence reddens exactly one |
| The screen's cache | `frontend` | `frontend/src/contexts/guestbook/hooks/useGuestbookEntries.test.tsx` (the key carries the question, every mutation invalidates, a `204` resolves) |
| An entry's age in words | `frontend` | `frontend/src/lib/relativeTime.test.ts` (the thresholds from both sides, an instant without a zone read as UTC) |
| The palette does not shadow the Tailwind scale | `frontend` | `frontend/src/styles/theme.test.ts` (a token named like a text size painted white text on a white card) |
| The corpus is what it claims to be | `tests/fitness/` | `tests/fitness/test_golden_set.py` |
| Both sides measure and trim text identically (`D-04`) | `tests/unit/` | `tests/unit/test_entry_text_rules.py` (the rule, the wiring into the schema, and three detectors that fire on the old behaviour) · `frontend/src/contexts/guestbook/lib/entryText.test.ts` (the same corpus, the same verdicts and lengths, from the browser) · `tests/integration/test_guestbook_entries_service.py` (what actually reached the column) · `tests/fitness/test_length_constants.py` (the literals are still equal — necessary, and on its own not sufficient) |

The "Owner" column names the suite in which the **deciding claim** lives; the rest of the proof
column is supplementary. A rule copied into the browser always has its owner on the server side —
a copy is a convenience for whoever writes it, not a second authority.

### Four file sets, disjoint

The test authors of the implementation stage write into files that are theirs alone, so the
boundaries are files rather than an agreement. They are not all one wave — the corpus locator
`tests/_golden_set.py` is imported across those boundaries, by the unit suite and by the e2e
steps, and `.specconf/stack.json` § `skills` orders `build-tests-integration` before both —
but the ownership below holds whichever wave each is dispatched in. A path appears in **exactly
one** set — **and in one of them**: these sets are disjoint *and* complete with respect to the
change's test files. **Every path the
change's architecture creates or modifies, and whose test file is excluded from the implementer's
write set, MUST stand in one of these sets** — a service module, a pure rule, a page, a component
directory, it makes no difference; standing in none, it will be written by nobody, and the
omission then looks exactly like a decision. A path may be left here without a test **only** with
a sentence saying why — silence is not allowed.

Rejected (decision of 2026-09-23, `cr: historical` — the test authors stopped being one wave,
because `tests/_golden_set.py` is imported across their boundaries, and `test_wave_dependencies.py`
holds the order; taken on the trunk from issue #63 of the 2026-09-20 audit, and framework changes
are made on the trunk and carry no `delta.md`):

- **Keep every test author in one wave and call the sets independent.** Disjoint sets prove that
  two authors will not write one file. They do not prove that one is not reading the other's file
  half-written, and the unit suite and the e2e steps read the locator.
- **Give the locator to each reader instead of ordering them.** That would be three owners for one
  file, which breaks the disjointness this section exists for.
- **Order `build-tests-integration` after `build-tests-e2e`.** Its tests of `e2e/harness/` import
  the harness, but they are tests OF it, which is the RED shape between two authors. The e2e steps
  read the locator as finished infrastructure, and that direction cannot wait.

The table below is an example filling, taken from the guestbook:

| Author | Writes |
|---|---|
| `build-tests-unit` | **tests/unit/test_guestbook_entry_schemas.py**, **tests/unit/test_guestbook_entry_model.py** (new) · **tests/fitness/test_golden_set.py** (new — the corpus obeys its own rules) · edits to `tests/unit/test_health.py`, `tests/unit/test_spa_fallback.py` |
| `build-tests-integration` | **tests/integration/test_guestbook_entries_service.py**, **tests/integration/test_guestbook_entries_router.py**, **tests/integration/test_guestbook_entries_corpus.py** (new) · edits to `test_migrations.py`, `test_app_integration.py`, `test_storage_swap.py` · **the whole backend suite's infrastructure**: `tests/conftest.py` · **the corpus's fixture half**: `golden-set/fixtures/` and `tests/_golden_set.py` |
| `build-tests-frontend` | **frontend/src/contexts/guestbook/lib/guestbookEntry.test.ts**, **frontend/src/lib/relativeTime.test.ts**, **frontend/src/contexts/guestbook/lib/entryListCopy.test.ts**, **frontend/src/styles/theme.test.ts**, **frontend/src/contexts/guestbook/pages/GuestbookPage.test.tsx**, **frontend/src/contexts/guestbook/hooks/useGuestbookEntries.test.tsx**, **frontend/src/contexts/guestbook/components/EntryComposer.test.tsx**, **frontend/src/contexts/guestbook/components/EntryCard.test.tsx**, **frontend/src/contexts/guestbook/components/DeleteEntryDialog.test.tsx** (new) · edits to `frontend/src/api/client.test.ts`, `frontend/src/api/problem.test.ts` |
| `build-tests-e2e` | **e2e/suite/features/guestbook.feature** (new) · `e2e/ui/test_smoke.py` · **the black box's infrastructure**: `e2e/harness/`, `e2e/suite/conftest.py` and `e2e/suite/golden_set.py` |

Two of the guestbook context's files have no test file of their own **deliberately** — the screen's toolbar
(`frontend/src/contexts/guestbook/components/EntryToolbar.tsx`) and the debounce
(`frontend/src/hooks/useDebouncedValue.ts`). Their
only observable behaviour is the state of the screen, so the guestbook page's test proves them; a
hook test in isolation would repeat the same scenario without the screen. The sentence stands
here rather than in the table, because the table lists an author's products and these files are
not a test product.

It was three until 2026-09-16, when `frontend/src/contexts/guestbook/hooks/useEntryQueryParams.ts`
gained `useEntryQueryParams.test.tsx`. The reason it was exempt stopped holding when the hook
started **reading** the question out of the address as well as writing it: the cases that matter
are navigations arriving at a mounted hook — Back, Forward, a link followed in place — and the
page's test would have to build the same harness of history controls to reach them. A screen test
that has to fake a browser to observe a hook is a hook test with a screen attached.

Rejected (decision of 2026-09-16, `cr: historical` — this reverses the exemption recorded in the
paragraph above, and the rule about which files carry their own test lives in this document; the
repair was made on the trunk and carries no `delta.md`):

- **Keep proving the hook through `GuestbookPage.test.tsx` alone.** It is where the rule came from
  and it costs no new file. What it could not reach is the case the hook was repaired for: a
  navigation arriving while the hook is mounted, with a write already deferred. Driving that from
  the page means rendering history controls beside the screen and pressing them, which is the hook
  harness — built in the page's file, where the next reader will not look for it.
- **Give `frontend/src/hooks/useDebouncedValue.ts` one too, while here.** Its behaviour did not
  move and still shows only through a caller. A test added because a neighbour got one is a test
  written for symmetry rather than for a claim.

### The UI smoke is not a traceability surface

`e2e/ui/` is **always supplementary, never the owner** of a citation, and that is why its files
have no row in the map. The reason is exact: the smoke asserts roles, selectors and fixed
interface texts — it can say "the screen came up and can be clicked", not "the rule is correct".
A requirement assigned to the smoke would be a requirement whose proof is that the page rendered.

The same applies to `tests/tooling/` and `tests/fitness/`: they prove tools and structure rather
than product requirements, so they do not own citations.

## End-to-end

`./scripts/test.sh e2e` runs **one** gate: the HTTP scenarios (`pytest-bdd`) plus the UI smoke
(Playwright), one junit. Against a live application, which it starts itself if there is none.

A `.feature` is read by somebody who does not write code. **Not a single HTTP code, not a single
path, not a single column name.** The translation is done by the steps in `e2e/suite/steps/`, and
that is the only place in the repository that knows which endpoint a scenario means.

The world is cleaned **before every scenario**, not before the run: it costs milliseconds and
removes every ordering dependency between scenarios. After cleaning comes the coherence question
— "did the reset reach the application I am talking to" — because an application left on a port
from a previous session can read a different database, and then a wrong number in a business
assertion reads like a defect in the application.

The port is one variable: `APP_PORT` decides where the application listens, where the poll knocks
and what `TARGET_BASE_URL` gets. `APP_PORT=8090 ./scripts/test.sh e2e` works on a machine where
something else holds 8080.

## The UI smoke in a browser

Three tools covered three levels — `pytest` the backend, `vitest` the pure rules and components,
`pytest-bdd` the HTTP contract as a black box — and none of them saw the **built** application: a
bundle that does not build; entering an SPA route directly returning a 404 because `app/static/`
is empty; a screen rendering a blank page instead of an error state because `role="alert"`
disappeared in a refactor. Hence the fourth: **Playwright for Python, only under `e2e/ui/`, as
plain `pytest`** (decision of 2026-08-30).

Three constraints are part of the decision, not its style:

1. **The bare `playwright` package, never the `pytest-playwright` plugin.** The plugin brings a
   CLI (`--screenshot`, `--video`, `--tracing`) with which any run can start recording the
   contents of the screen — exactly the data article XI of the constitution keeps out of
   artefacts. The artefact policy is code in `e2e/ui/conftest.py`, not a flag.
2. **No Gherkin.** A `.feature` file under `e2e/ui/` would be a costume: a reader would take it
   for a description of business behaviour, and this is a technical smoke.
3. **Chromium and only Chromium.** A browser matrix is a different and far more expensive
   promise.

The smoke asserts roles, selectors, fixed interface texts, counts and **computed styles** — never
a value read from the page, apart from one it typed itself. A screenshot is produced **only** on
failure and lands in the gitignored `.sdd/ui-artifacts/`.

Computed styles joined that list on 2026-09-16, and the addition is narrower than it sounds: a
colour, an `outline-*` property and `:focus-visible` are facts about the **stylesheet the browser
assembled**, not about the guestbook's contents, so Article XI is untouched. They are here
because there is nowhere else they can be asked. The component suite runs in jsdom, which loads
no application CSS, implements no `@layer` and does not support `:focus-visible` — so a question
like "which layer won" cannot be posed there at all, and the focus ring this screen promises was
absent from the built bundle while every suite was green. `e2e/ui/styles.py` holds the reading
and the WCAG arithmetic; assertion messages still name selectors and ratios, never page text.

Rejected (decision of 2026-09-16, `cr: historical` — the repair was made from the trunk, where
neither an ADR nor a `delta.md` is available, and this document is where the choice of a suite
lives, so the decision is recorded here):

- **Assert the focus ring in `vitest` instead.** jsdom is structurally unable to answer: it loads
  no application CSS, implements no `@layer` and does not support `element.matches(':focus-visible')`.
  A test for the ring's presence in the *source* would have been green on a screen with no visible
  ring at all — which is the state the repository was actually in.
- **Read the background from the token list rather than from the DOM.** It is the cheaper test and
  it asserts its own assumption: which surface a piece of text lands on is a property of where a
  component put it, and that is the half that goes wrong. `e2e/ui/styles.py` walks up to the
  ancestor that actually paints.
- **Add an accessibility library (`axe-core`) and run its whole ruleset.** It would answer far more
  than was asked, and a suite whose failures are a list of rules nobody chose is a suite whose
  first red run ends in a configuration file of exclusions. Two named rules, measured here, are
  the ones this screen promised; the rest is a decision for the day somebody makes it.
- **Leave the artefact policy's sentence as it stood and add the tests anyway.** A suite asserting
  something its own governing document does not list is how a policy stops being read.

Rejected: `vitest` + `@testing-library` instead of a browser (jsdom does not build a bundle, does
not serve `index.html` and does not perform routing — the three failures above are invisible to
it by definition); "open the screen" steps in the `pytest-bdd` suite (it mixes two levels in a
file meant for a non-programmer); the plugin with its flags disabled (one `uv add` and the
default setting comes back). This is enforced by `tests/fitness/test_ui_suite.py`: `playwright`
imported only under `e2e/ui/`, no `.feature` in that directory, no `pytest-playwright` in the
lock.

## Where the change process lives

The tests of the SDD process itself are the only exception to the `tests/` layout: they live
beside the code they prove, as the engine's own tests. Most of them read their
subject's **source**, and a check that reads source belongs beside it. They are a suite of
their own rather than a second root of this one: the process runs them with its own toolchain
from its own tree (the process's `pyproject.toml` and `sdd-tests`, in CI of its own), and this
project's `pytest` collects `tests/` alone. The exception is one of layout — and it **does not
generalise**.

Rejected (decision of 2026-09-09, `cr: historical` — the process became independent of the
application it works on: two trees, two toolchains, two workflows, one script contract between
them; framework changes are made on the trunk and carry no `delta.md`): one `pytest` run over
both roots. It made this project's `pyproject.toml` the process's toolchain, its `conftest.py`
the process's fixture and its `backend` job the process's CI — three dependencies in the one
direction the split forbids, and a template that could not drop the process without editing
its own test configuration.

Rejected (decision of 2026-09-09, `cr: historical` — later the same day the process left this
repository altogether, for the plugin `forge@scalo`, so "beside the code they prove" is no
longer a sentence about anything here: its tests are in its own repository. What this section
still records is the rule that made the move possible, and the one thing this project's CI
gained instead — the `specs` job, which calls the process's own action to run its gates and its
suite against this stack. Framework changes are made on the trunk and carry no `delta.md`):
deleting this section as no longer applicable. The exception it names is why the split could
happen at all, and a reader who finds `.claude/skills/_shared/sdd/test_*.py` in an old commit
needs the sentence that explains it.


## The gates were renamed

Every gate this document names is called after what it checks — `traceability`,
`e2e-scenario`, `english`. They were numbered `G1` to `G20` until 2026-09-06.

Rejected (decision of 2026-09-06, `cr: historical` — the naming rule and the rejected
alternatives live in one place, and this is a pointer to it rather than a second copy;
framework changes are made on the trunk and carry no `delta.md`): recording the argument again
here. See [`conventions.md`](conventions.md) § A gate is named, not numbered, and
[the process's `spec_gates.py`](https://github.com/Scalo-Sales-Engineering-Consulting/claude-marketplace/blob/main/plugins/forge/skills/_shared/sdd/spec_gates.py), where every gate declares the numeric
code it carried, for the mapping from every retired code.

## The manual this document cites has moved

The reference tables it points at travel with the process now — the gate register with its retired codes is [the process's `spec_gates.py`](https://github.com/Scalo-Sales-Engineering-Consulting/claude-marketplace/blob/main/plugins/forge/skills/_shared/sdd/spec_gates.py) — and not in `docs/`. `docs/` holds
the documentation of the **system** — setting up the AWS account, deploying, configuring,
operating it — and the manual for the **change process** moved beside the framework it
describes.

Rejected (decision of 2026-09-10, `cr: historical` — the forge plugin deleted its `docs/` tree
on 2026-09-10 and kept only what the process runs on, so `sdd-reference.md` and its table of
old numeric codes exist nowhere; the mapping from a retired code to a gate's name lives in the
gate register itself, `spec_gates.py`, where every gate declares the code it carried, and the
links here name that. Framework changes are made on the trunk and carry no `delta.md`): leaving
links that return 404, or copying the mapping into this document — the second home this section
argues against.

Rejected (decision of 2026-09-06, `cr: historical` — the rule and its rejected alternatives
live in one place, and this is a pointer to it rather than a second copy; framework changes are
made on the trunk and carry no `delta.md`): recording the argument again here. See
[`conventions.md`](conventions.md) § Documentation — where a document goes.

Rejected (decision of 2026-09-10, `cr: historical` — the pin this document describes now
names `forge@scalo`, from the marketplace in the Scalo organisation, and `test_process_pin.py` was
moved to match it in the same commit. Framework changes are made on the trunk and carry no
`delta.md`): leaving the description at the retired install id and letting the test be the only
statement of the truth. This document is where somebody looks first when that test fails, and
a testing document that misnames the thing under test sends them to look for a bug in the
wrong place.

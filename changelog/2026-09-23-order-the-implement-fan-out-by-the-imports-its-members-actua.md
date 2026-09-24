---
date: 2026-09-23
branch: chore/wave-edges
pr: 83
kind: process
---

# Order the implement fan-out by the imports its members actually share

Closes #63, audit ticket **E4-05**, the template half. Epic #58. The engine half it waited on,
Scalo-Sales-Engineering-Consulting/claude-marketplace#166, is merged, and this repository
resolves `.github/actions/*@main`, so it is already live in this repository's CI. The Flutter
half is forge-template-flutter#97, which this entry mirrors.

## What changed

- **`.specconf/stack.json` § `skills`**: two measured file edges, plus the RED rule written out
  instead of left implied. `build-tests-unit` and `build-tests-e2e` now run `after`
  `build-tests-integration`. All four implementers (`build-backend`, `build-frontend`,
  `build-migration`, `build-platform`) now name all four test authors. Before this change the
  four named three, two, one and two of them. The section's `$comment` no longer claims that
  "the two implement waves are disjoint by construction". It records what was measured instead,
  why the one pair that imports in both directions is ordered the way it is, and why there are
  no `consumed`/`produced` keys. `build-platform`'s own `$comment` said "second wave" and now
  says "builders' wave".
- **`tests/fitness/test_wave_dependencies.py`** (new, 9 tests): the witness. It resolves every
  Python import (`ast`) and every TypeScript import (the `@/` alias and relative specifiers) in
  every file a worker owns. When a file is owned by no worker, it follows that file's own
  imports. Each target is mapped to the worker whose `writes` covers it. Where a `tests: only`
  member and a `tests: never` member share a prefix, as the two frontend authors share
  `frontend/src/`, the file's shape decides the owner. The test then refuses the profile in any
  of these cases:
  - a crossing import is not ordered by `after`;
  - the ordering has a cycle;
  - a reader of the corpus locator does not run after the locator's author;
  - an `after` is justified by neither a crossing import nor the RED rule;
  - an implementer does not wait for every test author;
  - the fan-out has turned into a queue.

  Before any of that, it checks that it can still see the three crossings it was written for.
- **`spec/design/testing.md`**: two edits.
  - § Four file sets, disjoint opened with "The first wave of the implementation stage writes
    tests in parallel". The edges above made that false, and the sentence now says what is true.
  - § Evidence map said "first-wave test authors" and now says "the implementation stage's test
    authors".

  § Four file sets also gains a dated `Rejected (decision of 2026-09-23, `cr: historical` …)`
  block naming the three alternatives, which the diff-scoped `recorded-decision` gate asks for
  when a design document changes on the trunk. § Fitness functions gains the row for the new
  module. `test_test_layout.py` refuses a fitness module that has no row.
- **The eight `.claude/skills/build-*/SKILL.md`**:
  - The `description:` front matter no longer says "Runs in the first/second implement wave".
    Each one now says where the worker sits in the order.
  - The fan-out contracts of `build-tests-unit`, `build-tests-integration` and `build-tests-e2e`
    now state the edge that replaces "running beside me" and "dispatched in parallel".
  - The two authors of a shared tree carry the rule for moving a file out of it: `tests/_golden_set.py`
    and `tests/conftest.py` for `build-tests-integration`, `e2e/harness/` for `build-tests-e2e`.
  - `build-backend` and `build-migration` say why they are not ordered against each other.

**ADR:** none. The `spec/design/testing.md` edits decide nothing new about suites. The rule there, that the test
authors' boundaries are files and not an agreement, has not changed. Only the opening clause
counted waves, and this change made that count wrong. The decision this diff does contain, which
edges the fan-out declares and why, is taken in `.specconf/stack.json`. It is recorded in the
`$comment` beside the edges and enforced by `tests/fitness/test_wave_dependencies.py`, so an
ADR would be a third copy.

## Why

Disjoint write allowlists prove that two workers will not collide on a file. They say
**nothing** about whether one worker's output is another's input, and this profile treated the
first as if it answered the second. The audit of 2026-09-20 saw a shared fixture pass through
three roles before its producer had finished. Every allowlist was legal the whole time (E4-05,
§ 3).

This stack had the same shape, recorded as normal: `build-tests-unit/SKILL.md` said "the other
three test authors are writing their halves in parallel", and `build-tests-integration/SKILL.md`
said the unit author was "running beside me". If the unit author runs at the same moment as
the integration author, it can import a corpus locator that is only half written. Its suite then
fails to **collect**. That red cannot be told apart in the junit from the red the author was sent
to produce, so the wave either converges on a false result or spends a debug round finding out.

## From what, to what

Every import in the repository was resolved against the profile's `writes`. Eight (importer,
owner) pairs cross an author boundary:

- Five run in the RED direction and were already ordered. In four of them a test author imports
  the `app/` or `frontend/src/` its implementer has not written yet, which is the failing test on
  purpose. In the fifth, `build-backend`'s `scripts/` imports a locator or a harness that a test
  author owns.
- **Three were not ordered at all:**

| importer | owner | evidence |
|---|---|---|
| `build-tests-unit` | `build-tests-integration` | `tests/fitness/test_golden_set.py` and `tests/unit/test_entry_text_rules.py` import `tests/_golden_set.py` |
| `build-tests-e2e` | `build-tests-integration` | `e2e/suite/steps/guestbook_steps.py` imports `e2e/suite/golden_set.py`, **which no member writes**, and that module imports `tests/_golden_set.py`. A resolver that stopped at the unowned file would not see this edge |
| `build-tests-integration` | `build-tests-e2e` | `tests/tooling/test_e2e_harness.py` (4 modules) and `tests/integration/test_e2e_reset.py` import `e2e/harness/` |

The last two rows are one pair importing in both directions. `after` cannot express both, so the
files decide which way it goes:

- The integration suite's imports are tests **of** the harness. That is the RED shape between
  two authors: importing what the e2e author may be about to change is the purpose, exactly as a
  unit test imports `app/`.
- The steps' import is the opposite case. They read the locator as finished infrastructure, and
  they cannot run beside the author who writes it.

So `build-tests-e2e` follows `build-tests-integration`. The first draft of this change made it
the other way round, which is how the transitive edge was found.

The implement fan-out before and after, for a change that dispatches every member
(`sdd-engine compositions --all`, the composition with all nine members, the engine's
`build-tests-uat` included):

```text
before  [build-tests-unit build-tests-integration build-tests-frontend build-tests-e2e build-tests-uat]
        [build-backend build-frontend build-migration build-platform]

after   [build-tests-integration build-tests-frontend build-tests-uat]
        [build-tests-unit build-tests-e2e]
        [build-backend build-frontend build-migration build-platform]
```

## How it works now

The order of the implement fan-out comes from the files its members pass between them.
`skill_gate.waves` layers the members using `Contract.after`, and also using `requires` matched
against another member's `produces`. That second source stays empty here, because the engine
joins a `produces` entry to the change directory: it is for a change record's artefacts, never
for a source tree. The profile declares the edges, and `test_wave_dependencies.py` recomputes
them from the sources on every run. A new cross-tree import that nobody ordered turns the suite
red, and the message names the importing file and the imported path.

The same test also works the other way: every `after` must be **justified**. Either a crossing
import justifies it, or the RED rule does. The RED rule is an implementer (`tests: never`)
running after a test author (any other policy), because the proof comes before the code. Nothing
may be serialised just in case, which is what the ticket's § 13 asks.

A file in your tree that another author's tree imports is **shared**. Moving it takes three tasks
in the plan: create it at the new path, switch the imports, delete the old one. The delete goes in
a later wave than the switch. `build-tests-integration` carries that rule for `tests/_golden_set.py`
and `tests/conftest.py`, and `build-tests-e2e` carries it for `e2e/harness/`. These are the shared
trees this repository has.

## What it means for the process

A change that reaches both the integration suite and either the unit or the e2e suite now costs
one more dispatch round than before. That is the price of each author starting over a locator
that is finished, and it is what the ticket is about. Inside every wave the parallelism is the
same as before: all four implementers still run together, and `build-tests-frontend` still runs
with the first authors because it imports nothing that belongs to another author.

**The plan's waves and the dispatch waves no longer coincide, and neither of them moved.** In
`tasks.md`, § `Wave 1 — tests` and § `Wave 2 — implementation` group the plan's tasks by author.
That is the plugin's seed, and this repository mirrors it byte for byte. The engine's dispatch
waves are layered from the contracts. The two happened to be the same two waves until now. Every
skill that says "the wave-1 entries in `tasks.md` owned by me" still finds exactly its own tasks,
because a task is found by its owner, not by a number.

**The RED rule is now written down rather than free.** Every implementer waits for every test
author. While the fan-out had two waves this was true by accident, because the wave boundary and
the role boundary were the same line. With two test authors in the second wave, the two lines
come apart. `build-migration` named only `build-tests-integration`, so it would have shared a
wave with the unit and e2e authors. The engine refuses that over every subset of the signals a
repair round can narrow to (`test_every_fix_composition_that_dispatches_a_builder_dispatches_a_test_author_first`),
so all four implementers now name all four authors. None of those edges is a file edge. They are
the RED rule, stated explicitly.

## What it does not change

- **No `consumed`/`produced` keys.** The issue body asks for those names. The engine's resolution
  of the same ticket declined them and gave its reason in `compositions.py` `ordering`: a second
  spelling for one fact is how the two spellings drift apart. So the declaration uses `requires`,
  `produces` and `after`, as forge-template-flutter#97 does.
- **No `build-migration` → `build-backend` → `build-frontend` chain.** The issue names it as the
  place where one worker's output is most plainly another's input. It was checked and it is not an
  import edge:
  - `alembic/versions/` imports nothing under `app/`, and nothing under `app/` imports a revision.
    Both are built from the frozen `spec/design/data-model.md`.
  - `frontend/src/` imports nothing under `app/`. Both sides are built from the frozen
    `spec/design/api.md`, which is that document's whole purpose.

  The witness refuses `build-backend after build-migration` as unjustified; that was tried, and
  it went red. The one real hand-over between the implementers is not an import.
  `build-backend` runs `./scripts/generate.sh`, which rewrites `frontend/src/api/schema.d.ts`
  inside `build-frontend`'s tree. That hand-over is left unordered on purpose: the engine checks a
  wave against the **union** of its members' allowlists, so the regeneration is legal only while
  the two share a wave. The test's docstring names this as the one edge it does not see.
- **No write set moves**, and no allowlist gains or loses a path. That includes
  `e2e/suite/golden_set.py` and `e2e/suite/target.py`, which § Four file sets gives to
  `build-tests-e2e` but no allowlist covers. That is a separate finding and a separate change.
- **Nothing about `scripts/`, the suites, CI or the application.** No code under `app/` or
  `frontend/src/` was touched, and no behaviour test was added or changed.
- **The engine is not patched and no fix is vendored.**

## How it was verified

| what was run | what it said |
|---|---|
| `./scripts/test.sh fitness` | **318 passed**: 309 before, plus the nine new tests |
| the RED proof: both edges deleted from the profile, then the new module alone | **2 failed, 7 passed**. The ordering test names **8** unordered crossings: the 5 `e2e/harness/` imports, the 2 `tests/_golden_set.py` imports, and the transitive one through `e2e/suite/golden_set.py`. The locator test names both readers. With the edges restored, it is green |
| the e2e edge reversed (`build-tests-integration after build-tests-e2e`, which was this change's first draft) | **1 failed**, the locator test: `build-tests-e2e reads tests/_golden_set.py from e2e/suite/steps/guestbook_steps.py and does not run after build-tests-integration` |
| `build-backend after build-migration` added, and `build-migration` cut back to its old single author | **2 failed**, the justification test (`build-backend after build-migration`) and the RED-rule test (`build-migration does not wait for build-tests-frontend`, `... build-tests-unit`) |
| `sdd-engine stack --check` | `OK .specconf/stack.json (fastapi-react-postgres: 8 contract scripts, 3 suites, 11 skills)` |
| `sdd-engine compositions --all` | the three waves quoted above. The declaration reaches the planner, not only the file |
| `sdd-specs` (forge 0.1.124), on the committed branch | `Specs: OK`: `0 problem(s) in 13 check(s)`, skill lint `0 problem(s) over 295 documents`, traceability `7 declared, 7 referenced`, and the diff-scoped gates against `main` `0 gate(s) failed over 12 changed file(s)`. The first run failed `recorded-decision`, because `spec/design/testing.md` changed with no dated block. The `Rejected (decision of 2026-09-23, …)` block in § Four file sets is the answer |
| the engine's suite, `sdd-tests` with `SDD_PROJECT_DIR` at this clone | `SDD tests: OK`, **3754 passed, 6 skipped**. That includes `test_every_fix_composition_that_dispatches_a_builder_dispatches_a_test_author_first` over every signal subset. An earlier run on the uncommitted tree failed two tests that read the committed tree (an untracked changelog file and a tree digest), and both pass once the change is committed |
| `./scripts/check.sh --no-docker` | `Check: INCOMPLETE`, **exit 4**. Every gate this machine could answer said OK: static checks, generated code, the frozen API contract, backend tests (909 passed, 157 skipped for want of a database), frontend tests (213 passed), the frontend build, and the dependency audit. The named gaps are the Docker image, the e2e suite, the database tests, `actionlint` (absent) and Terraform (absent). Exit 4 means the script did what it could and named each gap; it is not a pass in disguise. CI runs all of them |
| `./scripts/changelog.sh check --base main` | `Changelog: OK` |

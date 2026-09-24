---
date: 2026-09-23
branch: chore/declare-fitness-suite
pr: 85
kind: process
---

# Declare the fitness suite, and take it out of the backend

## What changed

- `.specconf/stack.json` § `suites`: a fourth suite, `fitness` (`test.sh fitness`, junit
  `.sdd/reports/fitness.junit.xml`, `needs: []`, an `isolate` recipe over `tests/fitness`).
  The backend's `isolate.targets` narrow from `tests` to `tests/unit`, `tests/integration`,
  `tests/tooling`. The `$comment` says why the two pytest suites are disjoint and why
  `fitness`, too, declares no `allowed_skips`; the `build-tests-unit` hand-off note names the
  new suite.
- `scripts/test.sh`: `backend` and `--no-db` pass `--ignore=tests/fitness` (a path given on the
  command line is still collected). `fitness` runs through `run_fitness`, which announces
  itself as `Fitness tests`, and `all` runs it between the frontend and the backend.
- `scripts/check.sh`: a gate of its own, `Fitness tests`, which writes the fitness junit and
  runs before `Backend tests`.
- `.github/workflows/ci.yml`: the `backend` job gets a `Fitness tests` step
  (`if: !cancelled()`, so a red backend step does not hide it) and a second block in its
  Summary. The macOS leg gets a `fitness` step after `--no-db`, so the fitness modules still
  run there. `scripts/ci_summary.py` has the matching row.
- `tests/fitness/test_gate_parity.py`: `check.sh` must leave the junit of every suite that is
  handed `--junitxml` (backend and fitness). New assertions: the two suites' `isolate` targets
  are disjoint and together cover every group under `tests/`, and `test.sh`'s backend forms
  keep off `tests/fitness`. `SUITE_SOURCES` maps each suite to its trees, and
  `RECORDED_AS_SKIPPING` gains `fitness`. `tests/fitness/test_ci_parity.py` maps the new gate
  to the `backend` job.
- `spec/design/testing.md` (the suites section, the JUnit rule, the `test_gate_parity.py`
  row), `CLAUDE.md` (the `tests/` line) and `.claude/skills/build-tests-unit/SKILL.md` (which
  script runs a fitness case, and how a `**Must be red:**` spells one).
- `docs/troubleshooting.md`: a new entry, "`test.sh backend` is green and `Fitness tests` is
  red", for the operator who meets the split for the first time.

## Why

Issue #62 (B-4 of roadmap #58). The profile declared three suites and `tests/fitness/` (33
modules, 318 cases) was in none of them: it ran inside `backend`, with no junit of its own. So
the engine could not say "fitness green, backend red", and a `**Must be red:**` naming a
fitness case was filed as a backend case. The Flutter template declares `fitness` as a suite.

Declaring the suite was not enough by itself. The engine attributes a case id
(`classname::name`) to exactly one suite: `gate._suites_of` keeps the last outcome it reads
and `resolve_node_ids` keeps one node per case. If `backend` had gone on collecting
`tests/fitness`, every fitness case would sit in two junits, and which suite it belonged to
would depend on the order the reports were read. So the split goes both ways: `backend` stops
collecting what `fitness` now owns.

## From what, to what

| | before | after |
|---|---|---|
| suites in the profile | `backend`, `frontend`, `e2e` | `backend`, `fitness`, `frontend`, `e2e` |
| a fitness case's junit | `.sdd/reports/backend.junit.xml` | `.sdd/reports/fitness.junit.xml`, and only there |
| `test.sh backend` / `--no-db` | every group under `tests/` | unit, integration, tooling |
| `check.sh` | one `Backend tests` gate | `Fitness tests`, then `Backend tests` |
| CI | fitness inside the backend step and inside macOS `--no-db` | its own step in `backend`, and on macOS |

## How it works now

`./scripts/test.sh fitness` runs `tests/fitness` with no database and no Docker. The engine
hands it `--junitxml`, and it belongs to every gate profile, `unit-no-db` included. A failing
fitness case is re-run alone through the suite's own `isolate` recipe. `test_gate_parity.py`
turns red if the two pytest suites overlap, if a group under `tests/` belongs to neither, or if
`check.sh` stops writing either junit.

## What it means for the process

A test author's `**Must be red:**` for a fitness case is now `tests/fitness/test_x.py::test_y`,
and the RED proof reads it from the fitness junit. A stage boundary reports four suites. A new
group under `tests/` has to be given to one of the two suites before the fitness suite goes
green. The contract fixture in the marketplace needs no change: suite names are open
vocabulary in `contract_lint.shape`, and `fitness` uses only child keys the fixture already
has. Compared with the fixture on `origin/main` (`fadc94a`), the template has no key the
fixture lacks.

## What it does not change

- No test moves. The 316 fitness cases on `main` are green before and after, and none was
  broken to show a red; the two new cases in `test_gate_parity.py` were seen red only under the
  mutations listed below.
- `backend` is not split any further, and `unit`, `integration` and `tooling` stay entry
  points of `test.sh` rather than suites of the profile.
- `fitness` is not a traceability surface (`spec/design/testing.md` § The UI smoke is not a
  traceability surface), so it cites no requirement.
- Coverage still comes from the backend step and is never gated. It may drop a little, since
  the fitness modules that import `app` no longer count.

## How it was verified

- `sdd-engine stack --check`: `OK … 4 suites`. `sdd-engine stack` lists `fitness` with its
  own junit, `needs: nothing`, `isolate: yes`.
- `sdd-verify --full` on forge 0.1.117: `Suite backend — 748 tests, 724 executed (24 skipped)`,
  `Suite fitness — 318 tests`, `Suite frontend — 213 tests`, and the specification gates `ok`.
  So the engine reads the fitness junit that `check.sh` leaves behind. `Suite e2e` read 0 tests
  because port 5432 is held by another worktree's Postgres. Run separately as
  `POSTGRES_HOST_PORT=5963 APP_PORT=8963 ./scripts/test.sh e2e`, it passed 52, with 32 of 32
  scenarios collected.
- `./scripts/test.sh --no-db --collect-only` collects no `tests/fitness` node.
  `./scripts/test.sh backend tests/fitness/test_gate_parity.py --no-db` still runs the file it
  was given (10 passed).
- Mutations. Deleting the `Fitness tests` gate from `check.sh` turned
  `test_check_leaves_every_flagged_junit_where_the_profile_says` and `test_ci_parity`'s map
  test red. Dropping `--ignore=tests/fitness` from the `--no-db` arm turned
  `test_test_sh_keeps_the_backend_forms_off_tests_fitness` red. Restoring each turned it green.
- After rebasing onto `57951fb`: `./scripts/test.sh fitness` 324 passed, `./scripts/lint.sh` OK,
  `./scripts/changelog.sh check` OK.
- The contract fixture: `contract_lint.shape` of this profile compared with
  `plugins/forge/contracts/python-react/.specconf/stack.json` at marketplace `fadc94a`. The
  profile has no key the fixture lacks.

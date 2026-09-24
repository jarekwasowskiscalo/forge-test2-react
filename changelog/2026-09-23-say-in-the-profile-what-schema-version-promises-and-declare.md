---
date: 2026-09-23
branch: claude/roadmap-task-implementation-ab8c68
pr: 78
kind: process
---

# Say in the profile what schema_version promises, and declare the four mechanisms

## What changed

- `.specconf/stack.json`: the four mechanism sentences the engine renders into a worker's
  brief (`storage_contract`, `migration_mechanism`, `readiness`, `binding_target`) are now
  declared at the foot of the file, each true for this stack and naming the files where its
  rule lives. The top `$comment` gains a paragraph saying what `schema_version: 1` promises
  (the engine's mandatory key set) and names every key this profile uses beyond that set, or
  leaves out, compared with the Flutter template, with the reason for each. It also records
  the `sdd-contract --against-pins` measurement below.
- `tests/fitness/test_profile_mechanisms.py` (new): all four keys are declared and non-empty,
  every repository path they name exists, and the readiness route is the one
  `scripts/_lib.sh`'s `APP_HEALTH_URL` polls and `app/platform/routers/health.py` serves.
- `spec/design/testing.md` § the fitness table: the row for that module
  (`tests/fitness/test_test_layout.py` requires one per file).

## Why

Issue #69 (B-11 of roadmap #58): both templates say `schema_version: 1`, yet their top-level
key sets differed. Flutter declared the four mechanisms and this profile did not, while this
profile's suites carry `junit_flag` and `no_db_args` and Flutter's don't. A reader could learn
that only by diffing two files in two repositories, and `schema_version` looked like a promise
about shape that it wasn't keeping.

The measurement split the differences into two kinds. The engine's `stack.py` says the four
mechanisms are optional *for a deployment reason only*, and that the moment every template
declares them they come out of `_OPTIONAL_TOP_LEVEL`. So their absence here was a gap, not a
stack property: each has a real mechanism in this repository (a store-level constraint, an
Alembic revision with a declared mode, `GET /api/health`, the endpoint through the generated
client). Without them, `design-data`, `design-ui` and `reconcile-design` got a brief with no
MECHANISMS lines and fell back on the skill's generic wording. `junit_flag` / `no_db_args`,
on the other hand, are genuinely this stack's: optional suite keys with engine defaults that
Flutter's database-free, `--junitxml`-taking suites have no use for.

The engine-side half, making the four mandatory now that both templates carry them, is filed as
[claude-marketplace#281](https://github.com/Scalo-Sales-Engineering-Consulting/claude-marketplace/issues/281).

## From what, to what

| | before | after |
|---|---|---|
| mechanism keys | absent: `sdd-engine stack` printed `(none declared)` for all four | declared: the brief names this stack's mechanism for each |
| key-set difference from Flutter | discoverable only by diffing two profiles | stated in the top `$comment`, key by key, with the reason |
| a mechanism key dropped or its file moved | nothing fails | `test_profile_mechanisms.py` fails |

## How it works now

`schema_version` names the engine's mandatory key set and moves only when that set does. The
optional keys are the stack's choice, and this profile's top comment lists the ones it takes
(the four mechanisms, `suites.<name>.no_db_args`, `suites.<name>.junit_flag`) and the one it
leaves out on purpose (`ui`, the switch that lets the design stage draft a mock-up). The four
mechanism sentences reach a worker's preflight brief, where they outrank the skill's own
body. The fitness test keeps them pointing at files that exist and keeps the readiness route
in line with the probe the scripts use.

## What it means for the process

A design or reconcile worker on this template now reads this stack's answer to "how does an
at-most-one rule survive two writers", "how does a schema change ship", "what counts as up"
and "what does a screen field bind to", instead of the skill's generic wording. Whoever moves
one of the files a sentence names has to update the sentence, and the fitness suite says so.
The profile needs forge >= 0.1.55 (the keys arrived in claude-marketplace#115); the installed
plugin is 0.1.117.

## What it does not change

- `schema_version` stays `1`: the mandatory set did not move. If claude-marketplace#281 makes
  the four mandatory, that change decides whether the number moves.
- The profiles are not aligned by force: `junit_flag` / `no_db_args` stay, `ui` stays absent.
- No application code, script, schema or contract changes.

## How it was verified

- `sdd-contract --against-pins` in a fresh marketplace clone (`50ebb85`), with
  `templates/python-react` at this repository's `ab056be` and `templates/flutter` at
  `8b34f31`, forge 0.1.117: `0 finding(s) and 0 drift(s) over 2 contract fixture(s)`, exit 0.
  Re-run with the pin at this branch: same result.
- `sdd-engine stack --check`: `OK`. `sdd-engine stack` lists all four under MECHANISMS.
- `./scripts/test.sh fitness`: 309 passed. Mutation check: pointing `readiness` at
  `/api/healthz` and a non-existent router file turned two cases red, and restoring it turned
  them green again.
- `./scripts/lint.sh`: OK. `./scripts/check.sh`: every gate OK except e2e, which could not bind :5432 (another worktree's Postgres holds it); `POSTGRES_HOST_PORT=5962 APP_PORT=8962 ./scripts/test.sh e2e` passed 52, with 32 of 32 scenarios collected.

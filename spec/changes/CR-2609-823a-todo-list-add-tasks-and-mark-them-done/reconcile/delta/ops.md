# Delta fragment — `reconcile-ops`

*The operator's documentation under `docs/`, read against what the branch does to running the
system. Every edit this member made is under `docs/`, which binds nothing and is not part of the
`spec/` set Article IV makes a delta declare. So this fragment carries **no `ADDED` / `MODIFIED` /
`REMOVED` entry** and no boundary table. It records what changed operationally, which page took
each change, what was confirmed correct and left alone, the one runbook the change earned, and the
findings that belong to somebody else.*

## What changed about running the system

Read from `git diff main...HEAD` over the operational trees `.specconf/stack.json` declares
(`infra/`, `.github/workflows/`, `scripts/*.sh`, `alembic/versions/`, `Dockerfile`,
`docker-compose.yml`), the schema tree, and every environment read.

| # | What changed | Where it is in the code | Pages that took it |
|---|---|---|---|
| 1 | Revision `5c58af1f8e8a` (parent `a1b2c3d4e5f6`) creates `todo_tasks` (`id`, `text` `String(200)`, `done`, `created_at`) and `ix_todo_tasks_created_at_id`. Backward compatible, no data, a plain index build on a table created one step earlier, no manual step: it runs as deployment step 3 | `alembic/versions/5c58af1f8e8a_create_todo_tasks_table.py` | `docs/backup-and-recovery.md` (what cannot be rebuilt now names both tables); `docs/runbooks/restore-the-database.md` (both lists rewind together, count both tables, a restore to a moment before the to-do list has no `todo_tasks`, and option B can copy one table alone); `docs/runbooks/roll-back-a-release.md` (the table and its tasks survive a rollback) |
| 2 | A new HTTP surface, `GET`/`POST /api/todo-tasks` and `PATCH`/`DELETE /api/todo-tasks/{todo_task_id}`, and a second screen at `/todo-list`. The post-deploy smoke now asks `GET /api/todo-tasks` too, derived from `contracts/openapi/todo_list.yaml` with no script edit. The collection read takes no parameters and returns every task | `app/contexts/todo_list/`, `contracts/openapi/todo_list.yaml`, `scripts/smoke_contract.py` (unchanged, reads the new contract), `frontend/src/router.tsx` | `docs/solution-overview.md` (two screens, two tables, the to-do list not an example); `docs/security.md` (anybody may add, correct, tick and delete any task); `docs/operations.md` § Capacity (the unpaged whole-list read and the absence of any ceiling); `docs/runbooks/roll-back-a-release.md` (past the first to-do release, the rollback smoke gets a 404 on `/api/todo-tasks` and the unreverted shell shows "The tasks could not be loaded."); `docs/runbooks/release-to-production.md` (check `/todo-list` too, and an empty production list is correct); `docs/troubleshooting.md` (new symptom: the to-do list fails to load while the guest book works, told apart by `404` or `500`) |
| 3 | The seeder fills two lists, each on its own condition: welcome entries while the guest book holds none, example tasks while the to-do list's `total` is zero. Tasks are added not done and the done one is marked afterwards. It prints one line per list, costs one `GET` per list on a later run, refuses production before reading either list, and gives an environment that existed before the to-do list its examples on the next run. A part-way or simultaneous fill is a state it never repairs | `scripts/seed.sh`, `scripts/seed_golden_set.py`, `golden-set/seed/todo-tasks-example.json` | `docs/operations.md` § Filling an environment; `docs/deployment.md` (the seed line after the steps, and § A new environment is not empty); `docs/runbooks/preview-environment.md` and `docs/aws-account-setup.md` § 11 (what a raised preview shows); `docs/troubleshooting.md` (new symptom: too few example tasks, none done, or each twice); `docs/runbooks/refill-the-example-data.md` (new); `docs/runbooks/README.md` (the index row) |
| 4 | Restore and incident wording that said "the whole book" and "entries" now covers both lists | follows from 1 | `docs/runbooks/incident-first-response.md` step 4; `docs/runbooks/README.md` |
| 5 | The vitest suite reads a second corpus file, `golden-set/fixtures/todo-task-text.json`, which is one more reason `golden-set/` routes the frontend CI job | `frontend/src/contexts/todo_list/lib/todoTask.test.ts` | `docs/troubleshooting.md` § A CI job I expected to run was skipped |
| 6 | **No environment read added or removed.** `git diff main...HEAD -- app frontend/src scripts alembic` holds no `os.environ`, `getenv`, `import.meta.env` or `process.env` line on either side, and no Terraform, workflow, Dockerfile or compose file changed | — | none. `docs/configuration.md` confirmed as it stands |

## Confirmed correct and left alone

- `docs/configuration.md`: no variable, no Terraform value, no environment number moved.
  `APP_ENV` still "is what stops the seeder writing to production", word for word what the seeder
  does.
- `docs/deployment.md` § The order the steps happen in: the migrate step and the smoke are
  described generically ("every read-only endpoint `contracts/openapi/` declares"), which is true
  of the new route with no edit.
- `docs/runbooks/run-a-migration.md`: generic and true. The new revision builds its index on an
  empty table it has just created, so "a table lock on a large table" does not apply to it, and the
  300-second timeout is not approached.
- `docs/monitoring.md`: nothing new is observable or monitored. The to-do list's modules write no
  log line of their own (no logger anywhere under `app/contexts/`).
- `docs/runbooks/rotate-database-credentials.md`, `docs/README.md`: untouched by this change.
- `docs/user-guide.md`: it is the guestbook's page (`CLAUDE.md` deletes it with the example) and
  still true of the guestbook. See F-2.

## The runbook this change earned

`docs/runbooks/refill-the-example-data.md`. With this change the seeder has two independent
conditions and a two-phase add-then-mark for tasks. A fill that stopped part way leaves five
tasks with none done, or fewer than five; two fills at once leave the examples twice. The seeder
never repairs either, because it fills only an empty list (`spec/design/data-model.md` § Two writers
on one task, "Filling an empty list is the one rule here the store does not hold"; requirements
edge `E-21`, races `W-5` and `W-6`). The repair is a person's to make on a live preview or stage:
confirm the environment is not `prod`, empty the one list on its screen, run
`./scripts/seed.sh --base-url`, and read the header counts. The page says at the top that the procedure **has not been
performed on a deployed environment**, and names the only thing that proves it
(`tests/tooling/test_seed_golden_set.py`, against a faked API).

## Findings — outside this member's write set

- **F-1. The seeder's two lists are not yet in the scripts' own help and comments.**
  `./scripts/start.sh --help` still says `--no-seed` will "leave the guest book empty. By default a
  guest book that has no entries is filled from golden-set/seed/…" (`scripts/start.sh` lines
  48-51). The comments at `scripts/start.sh` lines 106, 113-114 and 170, `scripts/deploy.sh` lines
  620-622 and `scripts/preview.sh` lines 199-201 still describe one list. `CLAUDE.md` line 148
  (`--no-seed  # leave the guest book empty; …`) says the same. The behaviour is two lists, each on
  its own condition. `--help` is what an operator reads, and `scripts/` is outside `docs/`, so it
  is reported rather than edited: `scripts/*.sh` to a `build-platform` repair, `CLAUDE.md` to
  `reconcile-docs`, whose write set carries it.
- **F-2. The to-do screen has no user guide.** `docs/user-guide.md` is the guestbook's. A guide for
  the person using `/todo-list` is not operations documentation, so it is not written here, and no
  other `spec_sync` member's write set names `docs/`. Whether it should exist is the orchestrator's
  call.
- **F-3. Present before this change, left alone because the edits are differential.**
  `docs/operations.md` § The logs gives `app.services.guestbook_entries: entry amended id=…` as the
  application's line format, but no module under `app/contexts/` logs anything. `docs/deployment.md`
  says "seven steps" and lists eight.
- **F-4. No rule without a home.** Every behaviour these pages describe cites where it is
  specified: `spec/design/architecture.md` § What a new environment starts with,
  `spec/design/data-model.md` § Two writers on one task, `spec/contexts/todo_list.md` § Open
  questions, `spec/design/ui/todo-list.md` § Copy. Nothing here needs a decision.

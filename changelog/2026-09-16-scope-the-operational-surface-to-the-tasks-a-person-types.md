---
date: 2026-09-16
branch: chore/cut-operational-to-the-tasks-a-person-types
pr: 38
kind: process
---

# Scope the operational surface to the tasks a person types

## What changed

- `.specconf/stack.json` — `trees.operational` names `scripts/*.sh` where it named
  `scripts/`, and the `$comment` paragraph that already argues the same case for `app/`
  now argues it for the `.py` files beside the scripts.
- `spec/changes/EXEMPTIONS.md` — the `operations-doc` row over `scripts/ci_summary.py`,
  opened 2026-09-16 and due to expire 2026-09-30, is deleted. It was the only row this
  change was holding.

## Why

`operations-doc` refuses a change to `trees.operational` that leaves `docs/` untouched. The
tree named all of `scripts/`, so a repair to `scripts/ci_summary.py` — the reporter that
writes each job's summary block, is invoked only from workflow steps, runs on no deployed
copy and is described by no page under `docs/` — demanded a documentation edit with nothing
to write.

That is a gate firing outside its own sentence. Its declaration says operational means
*what somebody has to be told about to keep a deployed copy running*, and the reporter is
not that. Pull request #36 paid for the mismatch with a dated exemption row, which is the
expensive way to say a rule is aimed slightly wrong: a row has to be renewed or deleted,
and `exemptions` turns the build red on the day it expires.

The boundary this uses is not a new one. `hygiene.sh` checks `scripts/*.sh`, `help.sh`
lists `scripts/*.sh`, and `hygiene.sh` states what the line turns on: *whether a file is a
task with a `--help` a person asks for, and none of these is*. The same comment names
`ci_summary.py` as called by a workflow rather than by a script. The declaration now quotes
a line this repository had already drawn twice.

## From what, to what

**Before.** `trees.operational` carried `scripts/`, so all 38 files under it were
operational — 28 tasks and 10 `.py` helpers, the workflow-only reporter among them. A
`.py`-only repair either edited `docs/` for no reason or bought a row in the register.

**After.** It carries `scripts/*.sh`. The 28 tasks are operational and the 10 helpers are
not, which is the same cut `hygiene.sh` and `help.sh` already make. No exemption is owed
for a reporter repair, and the register is back to the two rows the 2026-09-08 audit opened.

## How it works now

`operations-doc` fires when a diff touches a path in `trees.operational` and nothing under
`docs/`. A change to `scripts/start.sh`, `scripts/deploy.sh`, `scripts/db.sh`, `infra/`,
`.github/workflows/`, `alembic/versions/`, the `Dockerfile` or `docker-compose.yml` still
owes the operator documentation an edit. A change to `scripts/ci_summary.py`,
`scripts/preflight.py`, `scripts/app_status.py` or any other helper does not.

The `matches` rule makes this a one-word edit rather than a list: a pattern carrying a glob
character is `fnmatch`, so `scripts/*.sh` matches the tasks and nothing else. There is no
negation in that rule, which is why the cut is stated as what IS operational rather than as
`scripts/` minus an exception.

## What it means for the process

A `.py`-only change under `scripts/` no longer demands an edit to `docs/`, and no longer
needs a row in `EXEMPTIONS.md` to say so. Everything else about raising, proving and
recording a change is unmoved.

## What it does not change

- **What the gate is for.** The operator documentation still has to move when the surface an
  operator drives moves; that is 28 scripts and four other trees, and none of them left.
- **The other half of the duty.** What a helper exposes to an operator — a flag, a variable,
  a `--help` — is held from the tree side by
  `tests/fitness/test_documentation_is_current.py`, on every run, diff or no. That test's own
  docstring draws the division: the tree-side question is a test, the did-anybody-touch-`docs/`
  question is a diff gate. This moves the second one only.
- **The two rows the audit opened.** `change-directory` and `e2e-scenario`, both expiring
  2026-09-22, are untouched.
- **The other stack.** `forge-template-flutter` declares its own trees; nothing here reaches it.
- **Any engine file.** `trees` is this repository's declaration. `stack.matches` is unchanged.

## How it was verified

- **The classification, path by path**, through the engine's own `stack.matches` against the
  edited declaration: `scripts/ci_summary.py`, `scripts/preflight.py` and
  `scripts/app_status.py` are **not** operational; `scripts/start.sh`, `scripts/deploy.sh`,
  `scripts/db.sh`, `infra/main.tf`, `.github/workflows/ci.yml`, `alembic/versions/x.py` and
  `Dockerfile` still are; `app/main.py` still is not. **0 failures over 11 cases.**
- **The gate end to end, on a constructed diff.** A commit touching only
  `scripts/ci_summary.py` and no `docs/`: `operations-doc` **silent**, where the same diff
  before this change named it. A commit touching only `scripts/start.sh` and no `docs/`:
  `operations-doc` **fires**. Both scratch commits discarded.
- `sdd-specs`: **OK** — every specification gate, the `exemptions` gate over the shortened
  register included.
- `sdd-specs --diff-gates` against the trunk over this branch's own diff: **0 gates failed**.
- `./scripts/check.sh --fast`: **OK**.
- `./scripts/test.sh tooling` and `./scripts/test.sh fitness`: green.
- `./scripts/changelog.sh check --base main`: **OK** on this entry.
- Not run here: the e2e leg, whose Postgres cannot bind while an unrelated container on this
  workstation holds port 5432, and the macOS leg, which needs a macOS runner. Neither reads
  the stack profile's path patterns.

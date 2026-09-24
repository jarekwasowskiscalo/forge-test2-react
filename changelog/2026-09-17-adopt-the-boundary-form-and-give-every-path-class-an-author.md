---
date: 2026-09-17
branch: process/adopt-the-boundary-form-and-name-a-platform-author
pr: <the number, once the pull request is open>
kind: process
---

# Adopt the boundary form, and give every path class an author

## What changed

- `.specconf/templates/change/delta-fragment.md` — gains the `## This change owns` section:
  the heading, the `| Path | Why |` table, the placeholder row and the paragraph naming who
  fills it in. Copied byte for byte from the plugin's seed.
- `.specconf/templates/change/tasks.md` — the scope section stops naming
  `design/delta/architecture.md` as the authority and reads the recorded boundary instead.
  Also byte for byte from the seed.
- `.specconf/stack.json` § `signals` — `Dockerfile` joins `infra_touched`,
  `docker-compose.yml` joins `tooling_touched`. Both files previously lit nothing at all.
- `.specconf/stack.json` § `skills` — `build-backend` gains `uv.lock`; a new worker
  `build-platform` owns `infra/`, `.github/`, `.claude/skills/`, `Dockerfile` and
  `docker-compose.yml`.
- `.specconf/process.json` — `build-platform` is conditioned on
  `[infra_touched, ci_touched, tooling_touched]` and listed in every tier's `implement`;
  `build-backend` now answers `tooling_touched` as well as `backend_touched`;
  `fix_conditional`'s `build-tests-unit` gains the same three platform signals.
- `.claude/skills/build-platform/` — new: `SKILL.md` plus the two five-statement shims.
- `.specconf/stack.json` § `hand_off` — `design-data` stops claiming a "worked partial
  index" that does not exist; `design-plan` and `build-debug` name the new member and what
  it owns; `build-platform` gets a note of its own.
- `.claude/skills/build-migration/SKILL.md` — the same false partial-index claim, removed
  where a worker actually reads it.
- `CLAUDE.md`, `README.md` — ten skills became eleven; the fourteen worker shims' docstring
  count went with it.

## Why

The engine began requiring a change to declare what it owns before leaving `design`, and
began asking *before dispatch* whether every planned path has an author
(`claude-marketplace#118`, merged 2026-09-16). This repository had realised neither half, and
the engine's own suite recorded both against this stack by name.

Two things were therefore broken in a way nobody could work around:

- An author who filled the delta fragment in correctly produced a fragment that
  `set-boundary --from-design` then refused, because the heading it parses was not in the
  form. Both real change records in this tree have `boundary = []`: the control had never
  once fired.
- Five path classes had no writer in any composition. `uv.lock` is the sharpest: it is in
  `trees.cold_required`, CI runs `uv sync --locked`, so the file is tracked and its drift
  breaks the build — and no member of any wave was allowed to touch it. "Add a backend
  dependency" was by definition a change with one author missing.

## From what, to what

**Before.** `delta-fragment.md` ended at the `MODIFIED` list; `tasks.md` pointed at
`design/delta/architecture.md`, a file three legal compositions on every tier never produce.
Measured on this profile with every signal lit, on p3: `uv.lock`, `infra/`, `.github/`,
`Dockerfile` and `docker-compose.yml` had no owner at all, and `scripts/` had one that was
conditioned on `backend_touched`, so a tooling-only change never dispatched it. `Dockerfile`
and `docker-compose.yml` additionally lit no signal, so changing the image the application
ships as scored the same tier as fixing a typo.

**After.** Both forms match the seed byte for byte. Every path signal this stack lights has a
member in the composition that signal alone produces, and that member may write its paths.

## How it works now

A change declares its boundary in the `## This change owns` table of a delta fragment; one
author per composition fills it in — `design-architecture` when the composition runs it,
`design-spec` when it does not — and `set-boundary --from-design` records it. Every wave's
diff is then compared against that record, and `tasks.md` reads the scope from it rather than
from a file that may not exist.

Implement has an eighth member. `build-platform` writes the machinery that is not the
application: Terraform, the workflows, the image, the compose file and this template's own
skills. It is dispatched when `infra_touched`, `ci_touched` or `tooling_touched` is lit.

`scripts/` stays with `build-backend`, which now answers `tooling_touched` too. That is the
one place the design bent: the engine asserts by name that `scripts/` is in `build-backend`'s
allowlist (`test_sdd_skill_gate.py` `_SHARED_PLUMBING`, bought by a change that stopped with
nobody able to write a bootstrap script), so the author could not be moved and had to be
summoned instead. Two members serve `tooling_touched`, each owning a disjoint half of its
paths — `scripts/` on one side, `.claude/skills/` and `docker-compose.yml` on the other.

## What it means for the process

A design stage now has to fill in the boundary table before it may close; that is the
engine's requirement and this repository can finally satisfy it.

A change touching `infra/`, `.github/`, the image or the compose file now summons
`build-platform` and is refused before dispatch if the plan names a path nobody owns, rather
than after the wave by a worktree check. A change touching only `scripts/` now dispatches
`build-backend` instead of leaving `build-tests-unit` alone with work it may not do.

**This change is half a change until `claude-marketplace` agrees.** The engine records both
gaps against this stack — `ALLOWED_DRIFT` in `test_sdd_document_templates.py` and
`UNCOVERED_SIGNALS` in `test_sdd_process_config.py` — and both entries clear themselves: a
recorded gap that has stopped being a gap fails its own assertion. This repository's CI
resolves `sdd-tests@main` live, so the paired pull request deleting those entries —
`Scalo-Sales-Engineering-Consulting/claude-marketplace#136` — merges first, and this one is
red until it does.

## What it does not change

- No application behaviour. Nothing under `app/`, `frontend/src/`, `alembic/` or
  `golden-set/` moves, and no gate this repository runs locally was touched.
- `build-debug` still writes only `trees.behaviour` — `app/`, `frontend/src/`,
  `alembic/versions/` — so it cannot repair the new tree. Widening that is a separate
  decision with a much larger blast radius, and is named as a follow-up rather than done
  quietly here.
- No new signal was invented. `Dockerfile` and `docker-compose.yml` joined two signals that
  already meant what they mean, so `detection.rules` and the three `conditional` lists that
  name those signals are untouched.
- `.specconf/templates/system/ui-screen.md` is already identical to the seed; the screen-form
  half of the reporting issue was closed upstream before this.

## How it was verified

The engine's own suite, run from a `claude-marketplace` checkout at `main` against this
worktree — this repository's local suites read none of `process.json` or `stack.json`
§ `signals`/`skills`, so they cannot answer for the profile:

```
cd ~/Projects/Forge/claude-marketplace
SDD_PROJECT_DIR=<this worktree> plugins/forge/bin/sdd-tests
```

It was that run, not review, that corrected the design twice: it refused moving `scripts/`
off `build-backend`, and it refused leaving `build-platform` out of p0's `implement` list,
where the repair tail computes its composition from a fix's scope rather than from the tier.

`./scripts/check.sh` — **OK**, every gate including the black box (52 e2e items, 32 scenarios
collected against a census of 32). It needed `POSTGRES_HOST_PORT=5732` on this machine: a
container from a sibling checkout holds 5432, which is a fact about the laptop and not about
this change. `./scripts/test.sh --no-db` — 837 passed, 157 skipped.
`./scripts/changelog.sh check` — OK.

The two engine failures that remain are the paired reminders described above, and they name
the entries to delete in `claude-marketplace`. They go green when that pull request merges,
and not before.

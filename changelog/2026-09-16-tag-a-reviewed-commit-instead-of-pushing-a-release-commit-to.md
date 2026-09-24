---
date: 2026-09-16
branch: release/tag-a-reviewed-commit
pr: 37
kind: ci
---

# Tag a reviewed commit instead of pushing a release commit to the trunk

Closes [#19](https://github.com/Scalo-Sales-Engineering-Consulting/forge_template_python_react/issues/19)
(audit findings `A01` and `A02`, both P1). They are one change because they were one
run of instructions in one function: the lines that wrote the version and the lines
that pushed it had no boundary between them.

## What changed

- `scripts/release.sh` — no longer writes a version into `pyproject.toml` and makes no
  commit. It tags `HEAD` and pushes `refs/tags/vX.Y.Z` alone. Three refusals run
  **before** the tag exists, on the push path only: `uv lock --check`, `HEAD` equal to
  `origin/<trunk>` after a fetch, and a `CI passed` check run on that SHA that is
  `completed`/`success`. The last-tag lookup moved from `git describe --tags
  --abbrev=0` to `git for-each-ref --count=1 --sort=-v:refname --merged HEAD`.
- `scripts/_lib.sh` — a `require_gh`, beside `require_uv` and `require_node`.
- `scripts/release_version.py` — the `write` verb and `set_project_version` are gone.
  `next` is untouched.
- `.github/workflows/release.yml` — `checks: read`; `GH_TOKEN` on the `Cut it` step;
  `app_version` passed to the `prod` job; `previous` read the same way the script
  reads it.
- `.github/workflows/deploy.yml` — a `workflow_call` input `app_version`, defaulting
  to `""`, reaching the `Deploy` step as `APP_VERSION`.
- `tests/tooling/test_release_script.py` — the fixture gains a bare `origin`, a `uv`
  stub that dispatches on its subcommand and a `gh` stub each test steers. Six new
  tests cover the push path, which had none.
- `tests/unit/test_release_version.py` — the four tests of the deleted writer are
  gone; `tests/unit/test_health.py` gains the one of them that was really guarding
  `build_info`'s fallback.
- `tests/fitness/test_scripts_discipline.py` and its row in `spec/design/testing.md` —
  the rule is now "no script commits, and `release.sh` is the one that pushes".
- Documentation: `docs/runbooks/release-to-production.md`, `docs/aws-account-setup.md`,
  `docs/configuration.md`, `docs/operations.md`, `scripts/help.sh`,
  `app/core/build_info.py`, `infra/terraform/envs/{prod,stage}/variables.tf`, and the
  `--frozen` comment in `scripts/package.sh`.

## Why

**The release could not succeed, and had not been tried.** `release.sh` pushed a
commit to `main`. Read live on 2026-09-16, ruleset `22747644` is `active` over
`~DEFAULT_BRANCH` with `bypass_actors: []` and `current_user_can_bypass: never`,
requiring a pull request and the `CI passed` context. `release.yml` checks out with
the default `GITHUB_TOKEN` and there is no GitHub App or PAT anywhere in
`.github/workflows`. The repository had already written down the missing
precondition — "It needs `github-actions[bot]` on the branch rule's bypass list" — and
that list is empty. Putting the bot on it removes the protection rather than
configuring it.

The script also contradicted itself: it refused a release off the trunk because
"Everything a release contains has to have been reviewed on the way in", then thirty
lines later added an unreviewed commit to the trunk. And the comment claiming
`--follow-tags` gave "one push, so there is no window" was wrong twice over —
`--atomic` appears nowhere in the repository, and the window it described is not the
one that exists. Only `main` is covered by a ruleset; `refs/tags/*` is covered by
nothing. A half-completed push left `vX.Y.Z` on a commit absent from `main`, and the
"$NEXT already exists" refusal then blocked every later release until somebody deleted
the tag by hand.

**Every release commit was unbuildable.** It staged `pyproject.toml` alone, and
`uv.lock` holds this project's version as checked metadata, so `uv sync --locked`
failed on it. The lock was never recomputed even by accident: the `uv run` that wrote
the version did its implicit lock+sync *before* the process started, on the old
manifest. The only locked sync in the release ran *before* the bump, and the first one
that would have caught it runs in `deploy.yml` — after the tag and the release page are
published. The blast radius was wider than the deploy: that commit landed on the trunk,
`ci.yml` runs on every push to `main`, and its `backend` job has no path filter and is
never cleared to skip. Every release would have reddened the trunk.

## From what, to what

Before: compute `vX.Y.Z` → write it into `pyproject.toml` → commit it → tag that commit
→ `git push origin main --follow-tags`. Two refs, one of them refused by the server, and
a commit whose lockfile disagreed with its manifest.

After: compute `vX.Y.Z` → check the lockfile, the trunk and the verdict → tag `HEAD` →
`git push origin refs/tags/vX.Y.Z`. One ref, which no ruleset covers, on a commit that
reached the trunk through a pull request. There is no release commit, so there is
nothing for `uv.lock` to fall out of step with.

The version used to be recorded twice, in the tag and in `pyproject.toml`. It is
recorded once now, in the tag, and reaches the running application through
`APP_VERSION` — which both readers already preferred (`app/core/build_info.py`,
`scripts/infra.sh`). `release.yml` passes the tag to `deploy.yml`, which had no way to
carry it before; `preview.sh` was already doing the same thing with `<version>+<sha>`.

## How it works now

`Actions → Release → Run workflow`, pick a bump. The `tag` job tags the head of the
default branch and pushes that one ref, then publishes the release page and calls
`deploy.yml` for `prod` with the tag as both the ref and the version.

Before it tags, `release.sh` refuses three things, and each refusal leaves nothing at
all behind — no local tag, no pushed ref, no release page:

- `uv lock --check` fails: the commit is not reproducible from its own lockfile.
- `HEAD` is not what `origin/<trunk>` carries: the commit has been through no pull
  request and no ruleset.
- `CI passed` on that SHA is not `completed`/`success`, including when there is no such
  check run at all — a commit CI never judged reads like good news to anybody skimming.

The checks are ordered to fail fastest and are on the push path only: `--dry-run` and
`--no-push` publish nothing, need no network and no GitHub login, and still work from a
train. `pyproject.toml`'s version is the package's own and tracks no release; a checkout
reporting it at `/api/health` is the honest answer to "which release is this", because
it is not one.

## What it means for the process

Nothing about running or changing this repository moves — `./scripts/release.sh` takes
the same arguments and still prints the version as its last line of stdout.

One thing an operator does differently: step 3 of the release runbook no longer asks for
`github-actions[bot]` on a bypass list, and `docs/aws-account-setup.md` now says to leave
that list empty. A release needs no write access to the trunk.

## What it does not change

- **`ci.yml` is untouched**, including the paragraph at its trigger block saying rulesets
  return 403 on this plan and `CI passed` "is a verdict nothing can require". That is now
  false — the ruleset exists and requires it — but the same claim sits in `CLAUDE.md`, and
  both belong to issue #24, which is open and scoped to exactly that. Fixing half of it
  here would take work off that ticket and collide with it later.
- The deploy itself: `deploy.sh`, the migration order, the alias move and the rollback path
  are all as they were. The one edit to `deploy.yml` is a new optional input, kept minimal
  because issue #20 also edits that file.
- Stage and preview. `app_version` defaults to `""`, which `infra.sh` treats as unset and
  falls through to `pyproject.toml` — exactly what they did before the input existed.
- `contracts/openapi/health.yaml`. Its prose describes the local fallback, which is
  unchanged.

## How it was verified

- `./scripts/test.sh tooling` — 222 passed. Fifteen of them are `test_release_script.py`,
  six new: one ref pushed and `origin/main` unmoved; no commit made and the worktree
  byte-identical; a HEAD the trunk does not carry refused; three flavours of a
  non-green verdict refused; a drifted lockfile refused; and `--no-push`/`--dry-run`
  working with a `gh` that fails outright.
- `./scripts/test.sh unit` — 108 passed. `./scripts/test.sh fitness` — 225 passed.
- `./scripts/lint.sh --fix` — ruff, `mypy --strict` over 100 files, eslint, tsc, all OK.
- `./scripts/check.sh` — the local definition of "will CI pass".
- The ruleset was read live rather than taken from the audit
  (`gh api repos/.../rulesets/22747644`), as was the shape of the check-runs answer on
  `main`'s head: `CI passed | status=completed | conclusion=success`.

**Two of the ticket's acceptance criteria are not met, and are not claimed.** Criterion 1
wants a test repository carrying an identical ruleset, with a real `Release` dispatch run
to completion; that means creating a repository and publishing a release, which is not
something to do unasked. Standing in its place: the ruleset's `target` is `branch` over
`~DEFAULT_BRANCH`, so `refs/tags/*` is outside it, plus the test proving only a tag ref is
pushed. Criterion 5 wants `/api/health` on prod returning the cut tag; there is no prod —
`AWS_DEPLOY_ROLE_ARN` is unset and this repository has zero GitHub Environments. The
nearest proof is `test_health_reports_the_copy_that_answered`, which already asserts a
`v`-prefixed `APP_VERSION` wins, plus the `app_version` wiring being present in both
workflows.

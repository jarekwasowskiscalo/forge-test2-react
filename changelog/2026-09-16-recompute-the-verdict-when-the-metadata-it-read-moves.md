---
date: 2026-09-16
branch: ci/recompute-on-metadata-moves
pr: 44
kind: ci
---

# Recompute the verdict when the metadata it read moves

## What changed

`.github/workflows/ci.yml` fires on three more `pull_request` types — `unlabeled`,
`ready_for_review` and `converted_to_draft` — and the comment blocks around the trigger and
around the aggregate were rewritten, because both stated things about this repository that
stopped being true. Two comment blocks that had drifted onto the wrong jobs were re-paired:
the one describing the specification gates now sits above `specs:` instead of above
`ci-advisory:`, and the one describing the required aggregate sits above `ci:` instead of
above `specs:`.

Documents that described a repository that no longer exists: `scripts/check.sh`,
`scripts/help.sh`, `CLAUDE.md`, `docs/aws-account-setup.md`, `spec/design/testing.md`,
`spec/constitution.md` and `scripts/deploy.sh`. Every citation of the change process's own
workflow file left `.pre-commit-config.yaml`, `pyproject.toml`, `scripts/check.sh`,
`scripts/help.sh`, `scripts/ci_summary.py`, `spec/design/testing.md`,
`tests/fitness/test_ci_parity.py` and `tests/tooling/test_ci_summary.py`.

Three test surfaces hold the corrections: `tests/fitness/test_ci_parity.py` gains the trigger
and blind-spot-list rules, `tests/tooling/test_toolchain_versions.py` reads the constitution's
Allowed list against the manifests, and `tests/fitness/test_withdrawn_claims.py` is new — it
refuses the return of a sentence this repository has decided against.

## Why

`CI passed` is the check the branch ruleset requires, and a required status is a function of
(SHA, pull-request metadata). The workflow could only see half of that function move.

Both labels this repository reads are **permissive**. `spec-exempt` is the only road from
`check_change.py` exit 1 to exit 0; `no-changelog` is a path to `ok` in `scripts/changelog.sh`.
Applying one turns red into green — which is why `labeled` was already on the trigger — and
taking one away turns green into red, which fired no event at all. The comment explaining that
omission argued from restrictive labels, of which this repository has none.

`ready_for_review` was the same hole in a second place. `check_change.py` skips its `stage` and
`status` asserts while a pull request is a draft, and says of them that they start deciding the
moment you take it out of draft. That sentence could not be true while leaving the draft
produced no event: without a new commit, those two asserts never ran at all.

The second half is a documentation failure of one shape. `ci.yml` said `CI passed` was a verdict
nothing could require because the organisation was on a plan that refused rulesets, and cited
the marketplace repository as agreeing. Ruleset `main` id 22747644 has been active since
2026-09-10, and the marketplace records the opposite of what it was cited for: the obstacle was
never the plan, it was a fork network, and detaching the fork was the whole fix. The file had
been edited after the fact changed and carried the old fact forward.

## From what, to what

| | Before | After |
|---|---|---|
| `pull_request` types | `opened, synchronize, reopened, labeled` | those four plus `unlabeled`, `ready_for_review`, `converted_to_draft` |
| Taking `spec-exempt` off | no event; the green stands | a full run; `specs` recomputes and refuses |
| Leaving draft | no event; two asserts never run | a full run; both asserts decide |
| `CI passed` in prose | a verdict nothing can require | required by ruleset `main` since 2026-09-10, no bypass actor |
| `check.sh` in prose | an equivalence with CI | a containment, pointing at a list of seven |
| `CLAUDE.md` on that list | names all five | names all seven |
| Article XIII | React 18 | React 19, which is what is installed |
| The process's workflow file | named in nine places | named nowhere |

## How it works now

Every `pull_request` type on the trigger produces a **full** run. No job branches on
`github.event.action`, and `tests/fitness/test_ci_parity.py` refuses one that starts to.

That is a decision against the cheaper shape, and the reason is written beside the trigger. A
metadata run's aggregate *replaces* the previous one for the same SHA. If the heavy jobs were
skipped on such a run, a pull request with a red `backend` would need only a label added or
removed to publish a green `CI passed` assembled from `specs` and `changelog` alone — a larger
hole than the one being closed. The whole workflow runs in two to three minutes, and `labeled`
has been paying that since the day it was added.

`converted_to_draft` travels with `ready_for_review` and must never be added alone: on its own
it is a path from a red `specs` to a green one, because the two asserts are skipped for a draft.
Paired it is closed, and a test refuses the unpaired form.

## What it means for the process

Nothing about running or changing this repository moves, with one thing worth knowing at the
merge button: taking `spec-exempt` or `no-changelog` off a pull request now starts a CI run, and
the pull request goes red if the gate that label was hiding still refuses. That was always the
intended reading of those labels; until now it only held until the next push.

## What it does not change

No routing was added and `scripts/ci_summary.py` gained no new class of cleared skip — its
verdict logic is untouched. The `concurrency` group is untouched: with full re-runs, a metadata
run and a commit run superseding each other is the correct behaviour rather than a hazard.
`spec/constitution.md`'s "Python ≥ 3.12" was left alone deliberately — it is a permitted floor
that `requires-python = ">=3.14"` satisfies, not drift, and narrowing it would be a change to a
CRITICAL article.

Two claims in the originating issue turned out not to hold and were not acted on: the sentence
it quotes from `scripts/deploy.sh`, that no previous copy of the SPA shell is kept, is in no
file of this repository — the real gap was an omission, and the help text now says that the
bucket keeps ten noncurrent versions while nothing restores them automatically. And the issue's
own reading of urgency was stale: it expected the ruleset to arrive later, so this was a
correctness fix in the answer rather than in the merge button. The ruleset was already active.

## How it was verified

`POSTGRES_HOST_PORT=5482 ./scripts/check.sh` → `Check: OK`, every gate, including the 44
end-to-end tests and the production image. The port override is local only: another worktree on
this machine held 5432.

`sdd-specs` → `Specs: OK`, 13 checks, 0 problems.

`./scripts/test.sh fitness` → 244 passed; `./scripts/test.sh tooling` → 298 passed.

The new rules were proved against the pre-change tree rather than only against the fixed one:
the trigger parser reads `[opened, synchronize, reopened, labeled]` off `origin/main` and reports
all three types missing; the version rule reads `React 18` off `origin/main`'s Article XIII
against `react@^19.2.8` and fails; `CLAUDE.md` on `origin/main` says five where the section lists
seven. A rule that passes equally before and after proves nothing, and two of the additions —
the no-routing rule and the blind-spot job census — are ratchets rather than fixes, which is said
here rather than left to be discovered.

What could not be verified locally: the event types themselves. Whether GitHub fires a run on
`ready_for_review` and on `unlabeled` is a fact about GitHub, observable only on a real pull
request. It was exercised on the pull request this entry travels on, with no new commit between
the transitions, and the runs are listed in its description.

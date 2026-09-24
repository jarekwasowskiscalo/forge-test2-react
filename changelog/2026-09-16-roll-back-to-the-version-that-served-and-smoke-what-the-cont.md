---
date: 2026-09-16
branch: claude/github-ticket-implementation-953f1a
pr:
kind: fix
---

# Roll back to the version that served, and smoke what the contract declares

Issue: `Scalo-Sales-Engineering-Consulting/forge_template_python_react#20` (audit findings A03, A42, A19).

## What changed

- `scripts/smoke_contract.py` — **new**. Reads `contracts/openapi/*.yaml` and answers two
  questions: which read-only endpoints a deployment can be asked about (every `get` with no path
  parameter and no required query parameter, with `?limit=1` where the contract declares `limit`),
  and whether one answer honours the envelope it promised. The smoke's question is no longer
  written down anywhere.
- `scripts/release_manifest.py` — **new**. Pure rules over the register of what served: `append`
  (newest last, trimmed to a Standard SSM parameter's 4 KB), `rollback_target` (the entry before
  the one the alias is on, skipping any version a rollback has already moved away from), and four
  refusals with the sentence each one prints.
- `scripts/deploy.sh` — the smoke asks what `smoke_contract.py` derives and distinguishes three
  failures instead of one; `--rollback` reads the manifest rather than choosing by version number,
  checks the recorded `CodeSha256` before moving anything, and carries the manual
  `aws lambda update-alias` command in every refusal; the deploy records what served after its
  smoke passes and the rollback records what it rolled away from; neither SPA sync passes
  `--delete` any more. The header and `--help` say all of this.
- `scripts/openapi_contract.py` — `_ref_name` and `_json_body` are now `ref_name` and `json_body`:
  a name two modules read is not a private one.
- `infra/terraform/modules/stack/main.tf` — `aws_ssm_parameter "releases"` at
  `/<project>/<environment>/releases`, `value = "[]"` with `lifecycle { ignore_changes = [value] }`.
  Exposed through `modules/stack/outputs.tf` and `infra/terraform/envs/{stage,prod}/outputs.tf`.
- `infra/terraform/modules/web/main.tf` — `aws_s3_bucket_lifecycle_configuration "site"`: expire
  noncurrent versions after 30 days while keeping the newest ten, clear delete markers whose
  versions have expired, abort interrupted uploads after 7. The comment says why no rule may
  expire a current object.
- `infra/terraform/modules/web/spa-fallback.js`, `docs/deployment.md`,
  `docs/runbooks/roll-back-a-release.md`, `docs/runbooks/release-to-production.md`,
  `.github/workflows/deploy.yml`, `scripts/ci_summary.py` — the sentences that stopped being true.
- `tests/tooling/test_smoke_contract.py`, `tests/tooling/test_release_manifest.py` — **new**.
  `tests/tooling/test_deploy_script.py` — eleven cases added over a fake AWS CLI.

## Why

Three findings, one file, one shared decision. Each was serious on its own and the first made the
second worse.

**A03.** The smoke asked `/api/entries?limit=1` for a field `matching`. The application serves
`/api/guestbook-entries` and the third field of the page was `total_all` before either line was
typed, so this had never passed against a real deployment. The same function is the rollback's
verdict, which closes a loop: a healthy release goes red, the failure message tells the operator to
roll back, and the rollback goes red too — so both versions look broken while both work.

**A42.** `--rollback` took the highest published version below the alias. `publish = true` mints a
version on every apply, and anything that stops between the apply and the alias move leaves one
that nothing ever routed to — as does `infra.sh apply` on its own. There was no record anywhere of
which version had actually served. On a real account the consequence is production traffic moved
onto a version that was never live, reported as `Rollback: OK`.

**A19.** `aws s3 sync --delete` over `assets/`, from a directory `package.sh` empties before every
build, permanently removed every previous release's hashed bundles. Versioning does not undo it:
the sync writes a delete marker and CloudFront asks for the plain key. A browser holding the older
shell then fails to load a module — a blank screen from a deploy that reported itself green.

## From what, to what

| | before | after |
|---|---|---|
| what the smoke asks | `/api/entries?limit=1`, keys `items, total, matching`, written in the script | every read-only endpoint `contracts/openapi/` declares, with the keys it freezes, read at the moment of asking |
| how a smoke fails | one sentence, "the list endpoint did not answer with the contract's envelope" | three: no answer / a status the contract does not document / an answer that is not JSON, with its media type / JSON missing named keys |
| how a rollback chooses | highest published version below the alias | the entry before the serving one in the release manifest, skipping versions already rolled away from |
| what proves that version is right | nothing | it is in the register, it still exists, and its `CodeSha256` is the one recorded |
| when it cannot choose | it chose anyway | it refuses, says which of five cases it is in, and prints the manual `update-alias` |
| what records a release | nothing | an SSM parameter per environment: version, digest, commit, environment, timestamp |
| publishing the SPA | `--delete` on both syncs | additive; nothing an earlier release wrote is removed |
| bucket retention | no lifecycle configuration at all | noncurrent versions, emptied delete markers and interrupted uploads age out; current objects never do |

## How it works now

A deploy ends by asking every read-only endpoint the contract declares and then writing one entry
into `/<project>/<environment>/releases`. An entry means *this version served this environment and
answered its contract* — which is the sentence a rollback needs and the one a Lambda version list
cannot supply.

`--rollback` reads that register, takes the entry before the version the alias is on, skips any
version some rollback already moved away from (without which the second rollback of an incident
walks forward into the release the first one escaped), confirms the version still exists and that
its digest is the recorded one, and only then moves the alias. Afterwards it records itself,
naming what it rolled away from.

The refusals are the point. No manifest, a serving version nothing recorded, the oldest entry,
everything earlier already rejected, a digest that no longer matches — each says which case it is
and prints the `aws lambda list-versions-by-function` / `update-alias` pair, because the behaviour
this replaces always moved a pointer and during an incident a refusal without a way forward is its
own kind of failure.

## What it means for the process

Nothing. No stage, no gate, no skill and no `.specconf/` semantic moves. It is a repair to
`scripts/`, `infra/` and the documents that describe them, so it takes this register rather than a
change record — `CLAUDE.md` § *Every other change leaves an entry*.

## What it does not change

- **The order of a deployment.** Build, apply, migrate, roll, publish, invalidate, smoke — the
  schema still goes first, and that is still what makes rolling the code back safe on its own.
- **What a rollback undoes.** Still one pointer: not the schema, and not `index.html`. What did
  change is the reason the SPA is not reverted — the bundles the older shell names survive now, so
  the screen loads; before, they had been deleted.
- **Nothing is smoked that writes.** Every question is a GET, which is what makes this safe to run
  against production. A release that breaks a POST still passes, and is still found by the first
  guest. That is a non-goal, not an oversight.
- **The migration function's payload.** Recording the Alembic revision with each release was
  considered and rejected: it would mean changing what that function returns, which is application
  code, and nothing in the rollback reads it.
- **`--delete` is gone from the shell sync too**, and the cost is named in the script: a root-level
  file somebody removes from the build stays in the bucket at its old URL. That is the cheaper side
  of never deleting something an older shell may still name.

## How it was verified

- `./scripts/check.sh` — **OK**, every gate: hygiene, lint (`ruff`, `mypy --strict` over 103 files,
  `eslint`, `tsc`), infrastructure, generated-code drift, the frozen contract, 718 backend tests,
  100 frontend tests, the SPA build, the dependency audit, the production image and 44 e2e tests.
  Run with `POSTGRES_HOST_PORT=5472 APP_PORT=8072`, because an unrelated project on this machine
  holds 5432.
- `./scripts/infra-check.sh` — **OK**. `terraform fmt -check` and `terraform validate` over every
  root, through the pinned image, so the new SSM parameter, the two outputs and the lifecycle
  configuration are known to parse and type-check.
- `./scripts/test.sh tooling -k deploy` — 18 passed. The load-bearing ones: with versions 4 and 6
  recorded and an unrouted 5 on the account, the alias moves to **4**; a missing manifest, an alias
  no green deploy recorded, a version that is gone and a version whose digest no longer matches
  each refuse **and move nothing**; a healthy rollback writes `"rolled_back_from":"6"`; the smoke
  asks `/api/guestbook-entries`, names `total_all` when it is missing, reports a 404 as a 404
  rather than as a bad envelope, and names `text/html` when the answer is not JSON.
- **What could not be run here, and why.** Nothing reaches AWS from this machine — the deployment
  role's trust policy names GitHub's OIDC provider and nothing else — so no SSM parameter was
  written, no alias was moved and no bucket lifecycle was applied. Those paths are proved by
  `terraform validate` and by the tooling tests over a fake AWS CLI, not against an account. The
  first real deploy after this merges is what creates the parameter and writes the first entry;
  until a green deploy has recorded one, **`--rollback` will refuse** on every environment, and the
  refusal names the manual command.

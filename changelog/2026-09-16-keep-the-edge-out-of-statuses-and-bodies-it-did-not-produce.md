---
date: 2026-09-16
branch: claude/github-ticket-implementation-29409a
pr:
kind: fix
---

# Keep the edge out of statuses and bodies it did not produce

Issue: `Scalo-Sales-Engineering-Consulting/forge_template_python_react#21` (audit finding A04).

## What changed

`infra/terraform/modules/web/main.tf` — both `custom_error_response` blocks are gone. In their
place, `aws_cloudfront_function.spa_fallback` (runtime `cloudfront-js-2.0`, `publish = true`) is
associated with `default_cache_behavior` on the `viewer-request` event, and with nothing else. The
bucket policy gains an `s3:ListBucket` statement on the bucket ARN, under the same `AWS:SourceArn`
condition as the `s3:GetObject` one.

`infra/terraform/modules/web/spa-fallback.js` — new, the function's source. Referenced by
`file("${path.module}/spa-fallback.js")`; it is the first non-`.tf` file under `infra/`.

`scripts/deploy.sh` — `wait_for_health` reads the response body instead of discarding it, and
requires the `status` field that `contracts/openapi/health.yaml` freezes.

`tests/fitness/test_edge_contract.py` — new, eight checks over the Terraform and the function source
as text. `spec/design/testing.md` § Fitness functions gains its row, which
`tests/fitness/test_test_layout.py` requires of every module in that directory.

`tests/tooling/test_deploy_script.py` — two cases for the health probe, with `curl` stubbed.

`infra/README.md` — the `modules/web/` row names the mechanism.

`docs/troubleshooting.md` — "A health probe reports 200 while the service is broken" gains its second
cause, and the one-line test that says whether a given environment has been applied since.

## Why

`CustomErrorResponses` is a member of `DistributionConfig`. `CacheBehavior` has no equivalent field,
so there is no narrower form of it and no partial fix: the two blocks applied in front of **both**
origins at once, and one distribution serves both halves of this application.

Everything the API refused was therefore rewritten on the way out. A missing entry —
`404 application/json`, `{"code": "guestbook_entry_not_found"}`, a refusal the application gets right
and `tests/unit/test_spa_fallback.py` proves it gets right — arrived at the browser as
`200 text/html` carrying the app shell. So did any 403 from API Gateway, and so did a request for a
hashed bundle that the previous deploy had already deleted: a failed module load became a blank
screen with nothing in the console to say why.

The single-process arrangement never had this problem. `app/main.py` answers
`if full_path.startswith("api/"): raise HTTPException(404)` and says in its own comment why —
otherwise "the frontend would then fail on `JSON.parse("<!doctype …")`". That rule was never carried
to the edge.

It also blinded the gate that exists to catch exactly this. `deploy.sh`'s health probe ran
`curl -fsS "$url/api/health" >/dev/null` **through CloudFront**, so an environment whose API answered
nothing at all could pass it on the 200 the edge manufactured.

## From what, to what

| | before | after |
|---|---|---|
| `GET /entries/<uuid>` (deep link) | S3 answers 403, the distribution rewrites it to `200 text/html` | the function rewrites the URI to `/index.html` before the cache is consulted; `200 text/html` |
| `GET /api/guestbook-entries/<unknown-uuid>` | `200 text/html`, the shell | `404 application/json`, the refusal the application wrote |
| `GET /api/no-such-route` | `200 text/html` | `404 application/json` |
| a 403 from API Gateway | `200 text/html` | `403` |
| `GET /assets/index-<hash>.js`, file deleted | `200 text/html` — a blank screen | `404` |
| `wait_for_health` against an HTML 200 | green | red, naming what came back |

## How it works now

CloudFront invokes one function on the viewer request for the static behaviour. It returns the
request untouched for `/api/` and for `/assets/`; otherwise, if the last path segment carries no dot,
it sets `request.uri` to `/index.html`. Anything with an extension is a file that either exists in
the bucket or does not, and both of those are answers.

`/api/*` is a separate `ordered_cache_behavior` with no function association, so the API path never
enters the function at all. The `/api/` check inside it is belt and braces — the defect being fixed
here was a rule that held everywhere except where somebody assumed it did.

A viewer-request function runs before the cache lookup, so the cache key is the URI it leaves behind:
every deep link now shares `/index.html`'s entry, and the single-path invalidation in step 6 of
`deploy.sh` covers all of them rather than only the shell.

`s3:ListBucket` is granted to change a **status**, not to expose a listing. Without it S3 will not
admit that a key it would not have let you read is absent, and answers 403 — so a bundle a deploy
deleted reads as a permissions fault and sends whoever is debugging it to the policy instead of to
the publication order. A real listing stays unreachable: it is `GET /?list-type=2`, and
`Managed-CachingOptimized` forwards no query string to the origin.

## What it means for the process

Nothing about running or changing this repository moves. Two notes for whoever deploys:

Both long-lived environments need `terraform apply` for this to take effect —
`infra/terraform/envs/stage/` and `infra/terraform/envs/prod/` are separate roots and neither is
applied by merging. Previews are unaffected: `modules/preview_app/` has no CloudFront by design and
serves the SPA through `app/main.py`, which already has the correct exclusion.

The change is recorded here rather than in `spec/changes/` because it was made outside the
`/forge:sdd` flow, at the user's instruction. One `spec/` file is edited all the same —
`spec/design/testing.md` — and that edit is enforced rather than discretionary: a fitness module with
no row in that table fails `test_test_layout.py`. Editing it then owes the `recorded-decision` gate a
reason, which off the process's path means a dated `Rejected (decision of …, `cr: historical` — …)`
block in the document itself; it is there, naming the two alternatives (folding the assertions into
`test_infra_layout.py`, and pinning nothing at all).

## What it does not change

`post_deploy_smoke` is **not** touched, and it is red before this change and red after it: it asks
for `/api/entries` (the application serves `/api/guestbook-entries`) and looks for a field `matching`
that was renamed `total_all`. That is issue #20 (A03), still open, and this change neither fixes nor
worsens it — the failure mode moves from a `JSONDecodeError` on the HTML shell to a failed `curl` on
a genuine 404. Rollback is likewise untouched (#20, A42), and so is the asset-publication window
(#20, A19): removing the masking makes that window fail loudly instead of silently, which is the
point, but the window itself is still there.

No application code changes. No contract changes: `contracts/openapi/` already promised the statuses
the edge was overwriting — the code kept that promise and the edge broke it, which is why the repair
is entirely in `infra/` and in the gate that failed to notice.

The three ASCII diagrams (`infra/README.md`, `spec/design/architecture.md` § Deployment,
`docs/solution-overview.md`) still read `+ fallback → index`, which is still true.

## How it was verified

`./scripts/infra-check.sh` — `terraform fmt -check` OK, and `terraform validate` Success on all five
roots (`bootstrap`, `preview/shared`, `preview/branch`, `envs/stage`, `envs/prod`).

`./scripts/test.sh fitness` — 233 passed, including the eight new checks. The `custom_error_response`
detector carries a known positive, because the sweep would pass on an empty tree too.

`./scripts/test.sh tooling -k deploy` — 7 passed. The two new cases lift `wait_for_health` out of the
shipped script with `sed` and run it against a stubbed `curl`: an HTML 200 is refused with a message
naming what came back, and the health document the contract promises is accepted. A copy of the
function in the test file would have passed forever after the real one rotted.

`./scripts/check.sh` — **Check: OK**. Every gate: repository hygiene, lint, infrastructure,
`generate --check`, the frozen API contract, the backend suite, the frontend suite, the Docker image,
the dependency audit, and the black box (44 passed, 30 of 30 scenarios collected). It was run with
`POSTGRES_HOST_PORT=5452`, because another checkout on this machine held 5432 — the first attempt
failed there, on the port and on nothing else.

**What could not be run, and why.** The issue's own acceptance criteria 1–5 are measured through a
live CloudFront distribution, and nothing in this repository reaches the edge: the unit suite stops
at the FastAPI process, the e2e suite talks to an application directly, and `infra-check.sh`
deliberately does no `plan` because that is a question about an account rather than about a commit.
So what is proved here is the **configuration**; the **behaviour** is confirmed on the next apply to
`stage`, and step 6 of `docs/runbooks/release-to-production.md` is where it would show. The criteria
also ask that cases 2–5 be seen red on the same distribution before the fix — that ordering is not
reproducible after the fact and was not performed.

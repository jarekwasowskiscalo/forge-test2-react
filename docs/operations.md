# Running it, day to day

**For:** whoever is responsible for a deployed environment.
**Normative source:** [`spec/design/architecture.md`](../spec/design/architecture.md) § Environments;
[`spec/constitution.md`](../spec/constitution.md) article XII, which is why every instruction here
is a script rather than the command inside it.

## Is it up?

```bash
curl -s https://<the environment>/api/health
```

```json
{ "status": "ok", "environment": "prod", "version": "v1.4.0" }
```

`status` is always `"ok"` — answering at all *is* the signal. The two useful fields are the other
two: they say **which copy answered**, which is the question actually asked after a release. The
check deliberately does not touch the database, because a health check that does turns a slow query
into an outage. "The process answers" and "the database is reachable" stay separate questions, and
the second one is answered by a collection read:

```bash
curl -s "https://<the environment>/api/guestbook-entries?limit=1"
```

Locally, `./scripts/status.sh --json` answers for the whole machine — Docker, the application, the
freshness of the build.

## The logs

Everything the application writes goes to stderr, which on AWS means CloudWatch Logs. Four groups
per long-lived environment:

| Group | What is in it |
|---|---|
| `/aws/lambda/sdd-guestbook-<env>-api` | the application |
| `/aws/lambda/sdd-guestbook-<env>-migrate` | the migration function, once per deploy |
| `/aws/apigateway/sdd-guestbook-<env>` | access logs, as structured JSON |
| `/aws/lambda/sdd-guestbook-preview-maintenance` | dropping a preview's database |

Retention is 14 days on stage and 30 on prod, and it is set explicitly so that "forever" is never
the accident.

**The application's line format:**

```
2026-09-06 11:04:22,118 INFO    [7f3a9c21] app.services.guestbook_entries: entry amended id=…
```

The bracketed value is a **request id**, stamped on every record by middleware — including
uvicorn's own — and returned to the caller as `X-Request-ID` on **every** response, a `500`
included. So a person holding a failed response and a person reading the log are holding the same
handle, which is what the first-response runbook's step 5 assumes. It is the handle for following
one request through everything it touched:

```
fields @timestamp, @message | filter @message like "7f3a9c21" | sort @timestamp asc
```

The access log carries `requestId`, `httpMethod`, `path`, `status` and `latency` — and deliberately
no query string and no body, because article XI of the constitution keeps personal data out of
artefacts. For the same reason **an application log line carries identifiers and counts, never
values**: you will find `id=…` and `matched=12`, never the message somebody wrote.

**That holds for a failure too, and it is worth knowing what one looks like** — you will read these
rather than tracebacks. An unhandled exception logs a block naming the exception's type and, one
line per frame, the file, the line and the function it passed through, for the whole
`caused by:` chain. What it never carries is the exception's own text: not a bind parameter, not
Postgres's `DETAIL:` line, not the value Pydantic refused. The bracketed request id is on the line
above, so the block is still the one you follow the request by.

Four levels are in use. `INFO` is business events, `DEBUG` is per-decision, `TRACE` — this
application's own level, below `DEBUG` — is per-row. `LOG_LEVEL` changes it; on AWS that means a
Terraform variable and an apply, because the function's environment is Terraform's.

## Capacity, and the pause you should expect

Stage and preview run the database at a minimum capacity of zero, so **the first request after a
longer silence waits ten to fifteen seconds** while the cluster wakes. The API function's timeout is
30 seconds, so it fits — but a stage smoke test run cold looks like a hang and is not one.
Production keeps a floor of 0.5 ACU and does not pause.

The API function's reserved concurrency — 20 on stage, 40 on prod — is not a throughput setting, it
is **the connection ceiling**. One connection per execution environment means a request storm is
unrepresentable rather than merely queued, which is why this stack has no RDS Proxy. Raising it
raises the number of database connections by the same number.

**And a proxy is not the release valve for that.** `enable_proxy` exists in the database module and
refuses anything but `false` — a `validation` block rejects `true` at `terraform validate`, naming
the two things the proxy would still need before it could serve a connection. So the budget to
manage is this ceiling against Aurora's maximum capacity, not a proxy somebody can switch on. What
it would take is written in `infra/terraform/modules/database/main.tf` § header.

## Filling an environment with something to look at

```bash
./scripts/seed.sh --base-url https://<the environment>/api
```

Safe to run at any time: it refuses production, and it refuses a guest book that already has
entries. `--boundary` adds the fixture entries that sit exactly on the published limits, which is
worth doing when the thing being reviewed is the screen rather than the flow. No deployment passes
that flag.

## Previews

```bash
./scripts/preview.sh slug            # which preview this branch gets
```

Raising and tearing one down is [`runbooks/preview-environment.md`](runbooks/preview-environment.md).
Two things worth knowing before you go looking: a preview's URL is a **public, unauthenticated**
Lambda function URL, and the whole layer is shared — one VPC and one Aurora cluster for every
branch, with a database per slug. A branch that is not being looked at costs essentially nothing.

## Migrations

They run as part of a deployment, before the new code goes live, and never from a workstation
against a deployed database. [`runbooks/run-a-migration.md`](runbooks/run-a-migration.md) covers
both the ordinary case and the one where it fails.

Locally:

```bash
./scripts/db.sh status
./scripts/db.sh migrate
```

## What you cannot do from here

**Deploy from a workstation.** The roles trust GitHub's OIDC provider and nothing else. There is a
break-glass path and it lives in IAM rather than in a flag — see [`security.md`](security.md).

**Destroy production through a pipeline.** `scripts/infra.sh` refuses `prod destroy` outside a
terminal and asks twice inside one.

**Read the master database password without noticing.** It is in Secrets Manager and in the
Terraform state; both are reachable only with the deploy role, and CloudTrail records the read.

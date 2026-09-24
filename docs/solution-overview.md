# What this system is

**For:** anybody meeting the system for the first time — a new maintainer, a reviewer, whoever
inherits it.
**Normative source:** [`spec/design/architecture.md`](../spec/design/architecture.md). Where this
page and that document disagree, that document is right and this one is a defect.

## In one paragraph

A guestbook. One screen, one resource, one table. A visitor signs an entry with a name and a
message; the entries can be searched, sorted, read a page at a time, corrected and deleted. It is
a **worked example** — the point of this repository is the process that produced it, and the
guestbook exists so that every step of that process has something real to travel through. It is
meant to be deleted once a first real feature replaces it.

## The parts

```
                    ┌───────────── CloudFront (one domain) ───────────────┐
   the browser ───▶ │  /api/*  ──▶ API Gateway ──▶ Lambda (zip, arm64)    │
                    │  /*      ──▶ S3 (private, OAC) + fallback → index   │
                    └────────────────────────────────────────────────────┘
                                                  │ VPC, 2 AZ, no NAT
                                                  ▼
                                   Aurora Serverless v2 (Postgres 16)
```

| Part | What it is |
|---|---|
| The API | FastAPI, cut by bounded context (`app/contexts/<name>/`) and layered inside each one: `routers/` → `services/` → `models/` + `schemas/` |
| The screen | React and TypeScript, built by Vite into `app/static/` and served by the same process |
| The database | Postgres 16. Aurora Serverless v2 on AWS, a container locally, and **the only engine** — there is no SQLite fallback anywhere |
| The schema | Owned by `alembic/versions/`. The application never calls `create_all()` |
| The client | Generated from the API contract into `frontend/src/api/schema.d.ts`, committed, and regenerated and compared by CI |

Locally the whole thing is one process on `:8080`. On AWS the screen and the API answer on one
CloudFront domain, which is why there is not a single line of CORS in the repository.

## Four behaviours that will surprise you

These are the things that have actually cost somebody an afternoon.

**The mounting order in `app/main.py` is load-bearing.** The SPA catch-all matches *every* path,
`/api/...` included. Registered before the API router it would make every API call return the HTML
shell with status 200 — and the symptom is not a 404 but a frontend breaking on
`JSON.parse("<!doctype ...")`.

**The health check is `/api/health`, never `/health`.** Plain `/health` is swallowed by that same
catch-all: it answers 200 with HTML wherever a frontend build exists, and 404 where one does not, so
it is never a liveness signal. Every probe, every script and the container's `HEALTHCHECK` use the
prefixed path.

**The `/api` prefix is applied in exactly one place** — `app/api.py`. A router
registered anywhere else lands outside the prefix and gets swallowed by the catch-all.

**The application does not create the schema.** A model change with no Alembic revision is not an
error; it is a divergence that surfaces on somebody else's machine, later.

## What is deliberately not here

**There is no authentication and no authorisation.** Anybody who can reach the URL can read, write,
amend and delete. That is a named non-goal in [`spec/invariants.md`](../spec/invariants.md) rather
than an absence nobody noticed, and it is the first thing to change if this template becomes a
product with users. [`security.md`](security.md) says where the hook point is.

**There is no alerting.** Logs are collected and retained; nothing watches them. See
[`monitoring.md`](monitoring.md), which says so plainly and prices the alternative.

**There is no NAT gateway and no RDS Proxy**, both by decision rather than omission, and both
recorded with their consequences in [`infra/README.md`](../infra/README.md).

## Where everything else is written down

| Question | Document |
|---|---|
| What the system must do | [`spec/contexts/guestbook.md`](../spec/contexts/guestbook.md) — the business rules |
| What the API promises | [`spec/design/api.md`](../spec/design/api.md), and [`contracts/openapi/`](../contracts/README.md) as the contract |
| What the tables are | [`spec/design/data-model.md`](../spec/design/data-model.md) |
| What the screen does, state by state | [`spec/design/ui/guestbook.md`](../spec/design/ui/guestbook.md) |
| How anybody knows it works | [`spec/design/testing.md`](../spec/design/testing.md) |
| How to set the AWS account up | [`aws-account-setup.md`](aws-account-setup.md) |
| How to deploy it | [`deployment.md`](deployment.md) |
| How to run it day to day | [`operations.md`](operations.md) |
| How a change is made | [the marketplace's README](https://github.com/Scalo-Sales-Engineering-Consulting/claude-marketplace/blob/main/README.md) |

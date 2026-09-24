# Infrastructure

This application on AWS, described in Terraform: two long-lived environments, and one
disposable environment per branch. The decisions behind them and the rejected
alternatives: [`spec/design/architecture.md`](../spec/design/architecture.md)
§ Deployment — two artefacts from one source and § Environments.

**The interface is the scripts, not `terraform` directly** (the constitution, art. XII):
[`scripts/infra.sh`](../scripts/infra.sh), [`scripts/deploy.sh`](../scripts/deploy.sh),
[`scripts/preview.sh`](../scripts/preview.sh) and
[`scripts/release.sh`](../scripts/release.sh). Stepping into `envs/prod/` and typing
`terraform apply` works and is exactly the shape of mistake the wrapper protects against —
one `cd` into the wrong place and you change the wrong environment, with the same confirming
question in both cases.

**Deployments come from GitHub Actions, and that is a control rather than a convention.**
No human-assumable role carries write permissions; the roles that do trust GitHub's OIDC
provider and nothing else. A workstation therefore has no credentials to deploy with,
whatever any script does or does not check.

## What comes into being

A long-lived environment:

```
                    ┌───────────── CloudFront (one domain) ───────────────┐
   the browser ───▶ │  /api/*  ──▶ API Gateway ──▶ Lambda (zip, arm64)    │
                    │  /*      ──▶ S3 (private, OAC) + fallback → index   │
                    └────────────────────────────────────────────────────┘
                                                  │ VPC, 2 AZ, NO NAT
                                                  ▼
                                   Aurora Serverless v2 (Postgres 16)
```

A branch's preview, on the shared layer:

```
   the browser ───▶ Lambda Function URL ──▶ Lambda (zip + the SPA inside it)
                                                  │  the SHARED preview VPC
                                                  ▼
                       Aurora Serverless v2  ──▶  database `preview_<slug>`
                       (one cluster, every branch)
```

**One domain for the screen and for the API**, so the requests are same-origin and there is
not a single line of CORS in the whole repository. A preview keeps that property the cheap
way: one function answers both, which is also what `./scripts/start.sh --container` does
locally.

**No NAT gateway.** The function reaches for exactly one thing and that thing is in the same
VPC. A NAT would cost ~30 USD a month per environment for traffic nobody sends. The price of
that decision: the function cannot call any AWS API during a request — which is why it
authenticates with an IAM token signed locally
([`app/db/iam_auth.py`](../app/db/iam_auth.py)) rather than with a password from Secrets
Manager.

**Two names in this stack are globally unique and neither is chosen by you.** The state bucket
you name yourself, and it is unique across all of S3 — but so are the web buckets, and those are
derived: `sdd-guestbook-stage-web` and `sdd-guestbook-prod-web`. If somebody else in the world
already holds one of those names, the first `apply` of that environment fails on the bucket, part
way through. Change `project` in the environment's `main.tf` and the derived names change with it.

**No RDS Proxy, anywhere, and `enable_proxy` now REFUSES `true`.** It is billed by the hour
whether or not anything connects, and this stack has a stricter substitute: with one
connection per execution environment (`app/db/session.py`), the API function's
`reserved_concurrent_executions` **is** its connection ceiling, so a storm is
unrepresentable rather than merely queued.

The proxy code stays in `infra/terraform/modules/database/main.tf` behind `enable_proxy`,
and the flag is a **barrier rather than a choice**: a `validation` block on the variable
rejects `true` with a message naming both of the things the proxy would still need — see
§ What was wrong before. It is a `validation` and not a `lifecycle` `precondition` because
that is the form `terraform validate` raises, and `validate` is the only Terraform CI runs.
`infra/terraform/refusals/database-proxy/` is a root that exists to be rejected, and
`./scripts/infra-check.sh` fails if it is ever accepted.

## The directories

| Path | What it is |
|---|---|
| `infra/terraform/bootstrap/` | once per account: the state bucket and the roles GitHub assumes — **two** of them, plus a third read-only one only if you name who may assume it |
| `infra/terraform/preview/shared/` | once per account: the VPC and the cluster every preview borrows, plus the maintenance function that drops a branch's database |
| `infra/terraform/preview/branch/` | once **per branch**: two functions and a public URL, and nothing else |
| `infra/terraform/modules/network/` | the VPC, two private subnets, two security groups |
| `infra/terraform/modules/database/` | Aurora Serverless v2, IAM auth, an optional proxy |
| `infra/terraform/modules/api/` | two Lambdas from one zip + an HTTP API + the roles + the logs |
| `infra/terraform/modules/web/` | S3, CloudFront, OAC, the cache policies, and the SPA fallback as a viewer-request function on the static behaviour alone — so the API's own statuses and bodies reach the browser unchanged |
| `infra/terraform/modules/stack/` | assembles the above into one environment |
| `infra/terraform/modules/preview_app/` | the per-branch composite: no VPC, no cluster, no bucket |
| `infra/terraform/envs/{stage,prod}/` | **the differences only** — about twenty lines each |
| `infra/terraform/refusals/*/` | roots that exist to **fail** `validate`, one per parameter this stack declares unsupported. Never planned, never applied, and deliberately not reachable from `infra.sh` |

`dev` used to be here and is gone. A branch gets a preview instead, which is cheaper, faster
and closer to what a reviewer actually wants — and it hands back the VPC that keeps the
account inside its quota.

### Set `TF_PLUGIN_CACHE_DIR` before your first `init`

Each root downloads **its own** copy of the AWS provider — around 775 MB, five times over.
It is gitignored, so it is not the repository's problem; it is the laptop's, and a structural
one rather than an accident.

```bash
export TF_PLUGIN_CACHE_DIR="$HOME/.terraform.d/plugin-cache"
mkdir -p "$TF_PLUGIN_CACHE_DIR"
```

Five copies come down to one. Put it in your shell profile, because it works only on an
`init` run AFTER the variable is set — it does nothing to copies already downloaded.

## How the environments differ

| | preview | stage | prod |
|---|---|---|---|
| lifetime | one branch | permanent | permanent |
| the database | one per branch, on a shared cluster | its own, never reset | its own |
| `min_capacity` | 0 | 0 | **0.5** |
| `max_capacity` | 2 (shared) | 4 | 8 |
| backup retention | 1 day | 7 days | 14 days |
| log retention | 3 days | 14 days | 30 days |
| how the SPA is served | by the function | S3 + CloudFront | S3 + CloudFront |
| `destroy` deletes without a trace | yes | no | no |

**`min_capacity = 0` means that at rest you pay for storage alone** — and that the first
request after a longer silence waits 10–15 seconds for the cluster to wake. The API
function's timeout is 30 seconds, so it fits; prod buys its way out of that pause with a
floor of 0.5 ACU.

**Stage's database is never reset.** Migrations accumulate on it exactly as they do on
production, which is what makes it worth testing against: a migration that works on an empty
database and not on one with data is the migration this catches.

## The first run

**The procedure is [`docs/aws-account-setup.md`](../docs/aws-account-setup.md)** — which
credentials you need, what goes in the bootstrap's variables, what the apply creates by name, the
four backend blocks you fill in by hand, the three GitHub environments and the one repository
variable, and the first four runs in the order they have to happen in.

It used to stand here, and it moved on 2026-09-06 for a reason worth stating: this document answers
*what exists in AWS and why*, and that is a different question from *what do I type, in order*. The
second one belongs with the rest of the documentation somebody operating this system reads, rather
than inside a code directory. The rule is
[`spec/design/conventions.md`](../spec/design/conventions.md) § Documentation — where a document
goes.

Two things from that procedure are worth repeating here, because they are properties of the
infrastructure rather than steps in a setup:

- **The state bucket's name is a literal in four `backend.tf` files.** A backend block takes no
  variables. `grep -rn REPLACE-ME infra/terraform` names any root that cannot reach its state.
- **The `preview` environment's `AWS_DEPLOY_ROLE_ARN` is what downgrades a preview from
  administrator.** See § The roles below, which is where that lives.

## Seed data

**A new environment fills itself from `golden-set/seed/`.** A preview with an empty
guest book is a preview of a screen nobody can judge, so `scripts/deploy.sh` and
`scripts/preview.sh` both call [`scripts/seed.sh`](../scripts/seed.sh) once the
environment answers — the same script `scripts/start.sh` calls on this machine, so
"an environment nobody has written in yet" is one condition and not two. It posts
through the application's own HTTP API — not into the database — so what a reviewer
looks at arrived the way a guest's entry arrives, and could not be something the
rules would have refused.

**The seed half, not the fixture half**, and the difference is the point. `golden-set/`
is cut in two: `fixtures/` is what the suites assert about, `seed/` is what an
environment opens with. They used to be one directory, and it showed — an entry added
to make a preview look richer weakened a paging test that counted them.
[`spec/design/architecture.md`](../spec/design/architecture.md) § What a new
environment starts with is the specification; [`golden-set/README.md`](../golden-set/README.md)
holds the rules each half owes.

Two refusals are what make it safe to run unconditionally:

- **It will not seed production.** It asks `/api/health`, which reports the
  environment Terraform gave the deployment, and stops. Test data in production
  cannot be undone by hand once somebody has replied to it.
- **It will not seed a guest book that already has entries.** So "seed every new
  environment" and "run on every deploy" are the same instruction, and every deploy
  after the first costs one GET.

Pointing it anywhere by hand, including at a stage that was emptied on purpose:

```bash
./scripts/seed.sh --base-url https://example/api --boundary
```

`--boundary` adds the FIXTURE entries that sit exactly on the published limits — the
one deliberate borrow across the split, worth making when the thing being reviewed is
the screen rather than the flow. No deployment passes it.

The corpus belongs to the guest book, and so do both scripts: deleting the example
deletes `golden-set/` and them with it (`CLAUDE.md`).

## How a deployment is triggered

**Nothing deploys on a merge.** Every deployment is somebody's decision.

| Target | How | Gate |
|---|---|---|
| a branch's preview | Actions → **Preview** → Run workflow | write access |
| `stage` | Actions → **Deploy** → Run workflow, any branch | write access, plus any reviewer you add |
| `prod` | Actions → **Release**, which tags and then calls the deploy | the required reviewer on `prod` |
| `prod`, by hand | push a `v*` tag | the required reviewer on `prod` |

A release does **not** rely on its own tag to trigger the deployment, and that is deliberate:
a tag pushed with `GITHUB_TOKEN` does not fire `push:` workflows, so a release that stopped
at the tag would leave production behind with every step green. `release.yml` calls
`deploy.yml` as a job instead, which keeps `environment: prod` — and the required reviewer —
exactly where it was.

## The roles, and what each may do

| Role | Assumed by | May |
|---|---|---|
| `deploy` | the `preview`, `stage` and `prod` environments | everything (`AdministratorAccess`) |
| `preview` | the `preview` environment | everything, **except** the long-lived environments' state and secrets |
| `plan` | people, and only if `plan_role_principals` names them | read everything, change nothing |

**`preview` is in the deploy role's trust policy too, and that is the one thing here worth
reading twice.** `bootstrap/main.tf` lists all three environments, because
[`tests/fitness/test_deploy_surface.py`](../tests/fitness/test_deploy_surface.py) keeps that list
equal to the environments the workflows declare, and `preview.yml` declares one. So which role a
preview run actually gets is decided **entirely** by the `AWS_DEPLOY_ROLE_ARN` variable set on the
`preview` environment overriding the repository-level one. Set the repository variable, forget the
environment one, and every preview quietly runs with unrestricted administrator rights and read
access to the stage and production state — where the Aurora master password is stored in cleartext.
Nothing fails, nothing warns, and the `Deny` below never applies because the role carrying it was
never assumed.

`AdministratorAccess` is said outright rather than hidden. This stack creates resources in
more than a dozen services, and a badly narrowed policy fails in the middle of an `apply` and
leaves an environment half built — which is worse than either extreme.

What protects the account is the **trust policy**, not the permissions policy. It accepts
`environment:` claims only; the `ref:` claims it used to carry never authorised anything (a
job that declares an environment presents no ref claim) and could only ever have let some
future job on the trunk take an administrator role with no reviewer.
[`tests/fitness/test_deploy_surface.py`](../tests/fitness/test_deploy_surface.py) keeps that
list equal to the environments the workflows actually declare.

The preview role's narrowing is a **`Deny`**, not a shortened `Allow`, and the difference
matters: a Deny cannot fail for a permission somebody forgot to grant, so it cannot leave a
stack half built. It refuses the state and the secrets of `stage` and `prod` — the state
files are where the Aurora master password is, in cleartext.

**That Deny names `sdd-guestbook` as a literal**, four times, in `bootstrap/main.tf`. Rename the
project — `modules/stack/variables.tf`, `preview/shared/variables.tf` — and the Deny goes on
matching resources that no longer exist, which is a Deny that refuses nothing. The state half is
guarded by `test_the_preview_role_is_denied_every_environment_state_key_that_exists`; the secrets
half is not, so it is written down here instead.

**Break-glass is in IAM, not in a flag.** If you genuinely have to deploy while GitHub is
down, an account admin attaches the deploy policy to themselves for the duration, and
CloudTrail records it. `SDD_DEPLOY_BREAK_GLASS=1` exists in `scripts/deploy.sh` as a signpost
for the person who tries it without credentials; it is not the control and cannot be.

## What it costs when nobody visits

Orders of magnitude, not a quote — check the AWS calculator for your region:

- **preview**: one Aurora cluster's storage (~0.10 USD/GB/month) shared across every branch,
  plus per-request Lambda. In practice a few dollars a month no matter how many branches, and
  a branch that is not being looked at costs essentially nothing.
- **stage**: its own cluster storage, S3 and the logs. The cluster sleeps.
- **prod**: the same, plus 0.5 ACU around the clock.

This architecture's two largest savings are the absence of a NAT gateway and the absence of
an RDS Proxy.

## What was wrong before, and is fixed here

Three defects, all of them invisible until somebody read the code together, and all of them
fatal on a real account. They are recorded because each was a failure that would have been
diagnosed from the wrong end.

- **The migration function could not connect at all on stage or prod.** Its URL was built
  from the endpoint output, which is the proxy where a proxy exists, while it authenticated
  with a password against an `iam_auth = "REQUIRED"` entry. `modules/database` now publishes
  a separate `cluster_endpoint` for exactly this client.
- **`app_iam` could not log in through the proxy either** — a proxy matches a client by the
  username inside one of its secrets, and it had none. It could not simply be given one:
  `GRANT rds_iam` makes the server authenticate that role by token only. **And a second,
  independent blocker sat underneath it:** `modules/network` creates a self-referencing
  *egress* rule on the database group and no self-referencing *ingress* rule, so the proxy
  would have reported every target unavailable even with the auth fixed. Both are moot with
  the proxy off — and since 2026-09-17 they are more than moot: `enable_proxy` refuses
  `true`, so the two are named in a refusal rather than left as a comment. The arrangement
  to build instead is written down in that module's header, and it is **not** the one that
  header used to recommend: the pinned provider exposes `default_auth_scheme = "IAM_AUTH"`,
  which needs no second secret and lets `app_iam` stay in `rds_iam`.
- **Alembic refused every deployed database URL.** It stores options in a `ConfigParser`,
  which reads `%` as the start of an interpolation and raises when the value is *set* — and a
  deployed URL carries a percent-encoded password. So the migration failed on import, before
  applying a single revision, with a message naming neither Alembic nor a database, on every
  environment and on no developer's machine. [`app/db/alembic_url.py`](../app/db/alembic_url.py)
  is the one-line escape and the whole story.

A fourth was the deployment order itself. `scripts/deploy.sh` applies the infrastructure —
which used to update the API function's code — **before** it runs the migration, so despite what
the script's own header said, there was a window in which new code stood over the old schema. It
is closed: the function publishes an immutable version on every apply, the gateway routes to an
alias Terraform never moves, and `deploy.sh` moves that alias once, after the migration returns.
The step list in that script's header is now the order that actually happens, and its failure
message ("the previous version is still serving") is now true. Previews were always immune —
they have no previous version.

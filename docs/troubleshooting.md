# Troubleshooting

**For:** whoever is looking at something that does not work.
**Normative source:** none — this is a symptom index. Where it names a rule, the rule's home is
cited beside it.

Start with [`runbooks/incident-first-response.md`](runbooks/incident-first-response.md) if something
is down right now. This page is for "why is it doing that?".

## The API returns HTML, and the browser throws on `JSON.parse`

**Cause.** The SPA catch-all is matching an API path. It matches *every* path, `/api/...` included,
and it is registered last in `app/main.py` for exactly that reason. A router registered outside
`app/api.py` lands outside the `/api` prefix and gets swallowed.

**Fix.** Register the router in `app/api.py`, which is the only place the prefix is
applied. `tests/unit/test_spa_fallback.py` is what should have caught it.

## A health probe reports 200 while the service is broken

**Cause.** The probe is calling `/health` rather than `/api/health`. Plain `/health` is matched by
the catch-all and answers 200 with the HTML shell wherever a frontend build exists — so it is never
a liveness signal. It answers 404 where no build exists, which is why this only bites in the
environments that matter.

**Fix.** Use `/api/health` everywhere. The container's `HEALTHCHECK`, every script and the
deployment smoke already do.

**A second cause, on an environment last deployed before 2026-09-16.** CloudFront carried two
`custom_error_response` rules that turned *every* 403 and 404 in front of either origin into
`200 text/html` with the shell in it — so the right path answered 200 as well, however broken the
API was. The distribution no longer does that (`infra/terraform/modules/web/`), but the fix is a
`terraform apply` per environment, not a merge. `curl -s https://<env>/api/health | head -c 20`
tells you which world you are in: a `{` means the edge is honest, a `<` means that environment has
not been applied since.

## The first request after a quiet period takes fifteen seconds

**Not a fault.** Stage and preview run Aurora at a minimum capacity of zero, so the cluster is
asleep and the first request waits for it to wake. The function's timeout is 30 seconds, so it fits.
Production keeps a floor of 0.5 ACU and does not do this.

If it happens on **production**, that is a fault, and the capacity floor is the thing to check.

## A deployment failed at the migration step

**What has happened.** Nothing is live. The alias has not moved, and `deploy.sh` says so: *"the
migration failed. The code has NOT been rolled; the previous version is still serving."* That is the
whole point of migrating before moving the alias.

**Where to look.** `/aws/lambda/sdd-guestbook-<env>-migrate` in CloudWatch Logs. The script searches
the invocation payload for `errorMessage` because a Lambda that raises still returns 200 — so the
payload in the workflow log carries the real message too.

**Then.** [`runbooks/run-a-migration.md`](runbooks/run-a-migration.md) § When it fails.

## The to-do list says "The tasks could not be loaded." while the guest book works

**How to tell which cause.** Ask the route directly:

```bash
curl -s -o /dev/null -w '%{http_code}\n' https://<the environment>/api/todo-tasks
```

| It answers | Cause | Fix |
|---|---|---|
| `404` | the version serving has no to-do list. A rollback past the first release that carried it moved the alias to an older version, and the SPA, which a rollback never reverts, still offers the screen | expected. Roll forward — [`runbooks/roll-back-a-release.md`](runbooks/roll-back-a-release.md) § What it did not undo. The tasks are still in the database |
| `500` | the version serving has the route, and its database has no `todo_tasks` table: revision `5c58af1f8e8a` has not run against it. Two ways lead here: an alias moved by hand onto a version whose deployment stopped at the migration, and a restore to a moment before the first deployment that carried the to-do list | `/aws/lambda/sdd-guestbook-<env>-migrate` says how far the last migration got. Deploy again: step 3 applies what is missing before the alias moves. For a restore, [`runbooks/restore-the-database.md`](runbooks/restore-the-database.md) step 3 |

The `500` leaves the catch-all's block in the application log, and its frames run through
`app/contexts/todo_list/services/todo_tasks.py`. The to-do list's modules write no log line of
their own, so that block and the access log are all there is to read.

## A new environment's to-do list has too few example tasks, none done, or each twice

**Cause.** The seeder checks once that the list is empty and then writes, and nothing in the
database holds that check ([`spec/design/data-model.md`](../spec/design/data-model.md) § Two writers
on one task). A run that stopped part way is the warning *"the seed corpus did not go in; the
deployment itself is fine"* in the deploy log, with the seeder's `error: seeding <env> failed: …`
line above it naming the task and the status it got. It leaves a list that is no longer empty, so
every later run prints `the to-do list of <env> already holds a task; left alone`. The seeder adds
all five example tasks before it marks the done one, so a run that stopped between the two leaves
five tasks and none done. Two runs at the same moment both find the list empty and both fill it.
The guest book's welcome entries have the same exposure.

**Fix.** Nothing is broken, and no deployment will change it. If somebody is going to judge the
screen by it: [`runbooks/refill-the-example-data.md`](runbooks/refill-the-example-data.md).

## Requests are being throttled

**Cause.** The API function's reserved concurrency has been reached — 20 on stage, 40 on prod. That
is not a throughput setting, it is the **connection ceiling**: one connection per execution
environment means a request storm is unrepresentable rather than merely queued, which is why this
stack has no RDS Proxy.

**What it looks like.** Throttling is invisible in the application's own logs — the request never
reaches the application. It is a Lambda `Throttles` metric and a 429 at the gateway.

**Fix.** Raise `api_reserved_concurrency` in that environment's `main.tf`, knowing that it raises
the database connection count by the same number, and that Aurora's maximum capacity is the other
half of that budget.

**Not the fix.** `database_enable_proxy = true`. It looks like the obvious relief and is refused at
`terraform validate` with a message naming why — the proxy's only `auth` block names the master
secret while the function connects as `app_iam` by token, and the database security group has no
self-referencing ingress rule, so the proxy would reach no target. Better a refusal in a plan than
an environment that stops serving; `infra/terraform/modules/database/main.tf` § header says what
would have to be built.

## `terraform init` fails on the backend

**Cause, almost always.** `REPLACE-ME-terraform-state` is still in that root's `backend.tf`. There
are four of them and the setup step is a table rather than a command, which is why it is the step
most often half-done.

```bash
grep -rn REPLACE-ME infra/terraform
```

**Second cause.** A Terraform version other than `1.13.3`. Two versions write two state formats, and
the newer one locks the older out of the state for everybody. `scripts/infra.sh` uses the pinned
image when the pinned binary is not on `PATH`; running `terraform` by hand is what gets past that.

## `terraform apply` on bootstrap fails with `EntityAlreadyExists`

**Cause.** The account already has GitHub's OIDC provider, and there can be only one.

**Fix.** `create_oidc_provider = false` in `infra/terraform/bootstrap/terraform.tfvars`.

## The first apply of an environment fails on an S3 bucket

**Cause.** The web bucket names are derived — `sdd-guestbook-stage-web`, `sdd-guestbook-prod-web` —
and S3 bucket names are globally unique. Somebody else in the world holds it.

**Fix.** Change `project` in that environment's `main.tf`; every derived name changes with it. Note
that the preview role's `Deny` names the project as a literal, so a rename there needs the same edit
in `infra/terraform/bootstrap/main.tf` — otherwise the Deny goes on matching resources that no
longer exist, which is a Deny that refuses nothing.

## A preview run has more permission than it should

**Cause.** `AWS_DEPLOY_ROLE_ARN` is set at the repository level and *not* on the `preview`
environment. The deploy role is trusted by `preview` too, so without the environment-level override
a preview assumes the unrestricted role.

**How to tell.** The workflow log names the role ARN it assumed. If it is `sdd-guestbook-deploy` on
a preview run, this is what happened.

**Fix.** [`aws-account-setup.md`](aws-account-setup.md) § 7.

## The preview and teardown workflows skip without running

**Cause.** `AWS_DEPLOY_ROLE_ARN` is not set at the **repository** level. Both workflows test it in a
job-level `if:`, and a job's `if:` is evaluated before the environment resolves — so an
environment-level value alone is invisible to it.

## A deployed database URL breaks Alembic on import

**Already fixed, recorded because the message names neither Alembic nor a database.** Alembic stores
options in a `ConfigParser`, which reads `%` as the start of an interpolation and raises when the
value is *set* — and a deployed URL carries a percent-encoded password. It failed before applying a
single revision, on every environment and on no developer's machine. `app/db/alembic_url.py` is the
one-line escape.

## A second teardown of the same preview

**Not a fault.** Teardown is best-effort by design and must exit green when the stack is already
gone: a pull request closed twice, or a branch deleted after the PR closed, fires it twice.

## The end-to-end suite refuses to run

**Cause.** The harness truncates tables between scenarios, and it does so only against a database
that says — in itself — that this run may empty it. The mark is a `COMMENT ON DATABASE` carrying
the run id, written by `./scripts/test.sh e2e` on the database it provisioned. That interlock
exists so that pointing the suite at a shared environment cannot empty it by accident, and it is
written into the database rather than read out of the connection string because a tunnel or a
port-forward to a shared database answers on `127.0.0.1` exactly as a throwaway container does.

**Which refusal you are looking at.** Each names its own cause in one sentence:

| The message says | What to do |
|---|---|
| it does not carry the mark of a disposable database | run the suite through `./scripts/test.sh e2e`, which marks the database it resolves |
| marked disposable by a different run | the same — the mark left by an earlier run is not consent for this one |
| `E2E_RUN_ID` is not set | you ran pytest by hand; `./scripts/test.sh e2e` mints the id and writes the mark |
| refusing to mark `<name>` disposable | `DATABASE_URL` was already set, so the script did not create that database. Unset it, or set `E2E_ALLOW_REMOTE_RESET=<name>` |
| refusing to empty a database on `<address>` | the target is not this host. Set `E2E_ALLOW_REMOTE_RESET` to `1` or to the database's name |
| `E2E_ALLOW_REMOTE_RESET=...` does not switch this guard off | the variable is compared by equality. `0`, `false` and `no` are not "off" — remove it |
| the connection string does not locate the database, or names it through a service file | libpq would take the target from `PGHOST`, `PGHOSTADDR` or `pg_service.conf`, which this guard cannot read. Put the host in the connection string |

## A UI test fails against code you have already fixed

**Cause, before 2026-09-16.** `./scripts/test.sh e2e` and `./scripts/test.sh ui` enter real
screens, and a screen is the bundle under `app/static/`. The preparation step asked only whether
`app/static/index.html` **existed**, so a bundle built from the previous sources was reused
silently and the smoke reported on code nobody was looking at. The mirror image is the one that
costs more: a stale bundle still holding the old, *passing* behaviour reports green for a screen
that was never built. Neither shape is visible from the suite's output.

**Not a fault now.** The preparation step compares instead of counting: it rebuilds when the
bundle is missing **or** older than `frontend/src`, `frontend/index.html`, `frontend/package.json`,
`frontend/package-lock.json`, `frontend/tsconfig.json` or `frontend/vite.config.ts`, and says which
file decided it. A current bundle is reused and the comparison is printed, so a run that skipped the
build says what it compared rather than only that it skipped.

**If you are on an older checkout, or you want to look.** `./scripts/status.sh --json` reports
`frontend_build` as `missing`, `stale` or `current` from the same comparison, and
`./scripts/build.sh --if-stale` compiles only when one is due. Plain `./scripts/build.sh` always
compiles, which is what [`check.sh`](../scripts/check.sh) and CI run — a clean checkout has no
`app/static/` at all, so CI has never been exposed to this.

**One case is not a fault and stops the run on purpose.** A source saved *while* the compiler was
running leaves a bundle that is already not a bundle of those sources; the build warns, exits 4,
and the suite stops with "the SPA was not built from these sources … Nothing was started and
nothing was run". Run the command again.

**Never diagnosed by mtimes.** An edit that leaves a file's timestamp alone — a checkout that
restores timestamps, a file copied in with its metadata — is invisible to the comparison.
`./scripts/build.sh` with no flag is the answer when in doubt; it costs tens of seconds and
compares nothing.

## `check.sh` passes locally and CI fails

**Expected, and the gap is a list rather than a surprise.** CI additionally builds the Lambda
package, asserts the production image's runtime properties, runs a macOS leg, computes the
routing verdict and refuses a frontend suite that collected no test.
[`spec/design/testing.md`](../spec/design/testing.md) § What only CI can answer names all five.

## `test.sh backend` is green and `Fitness tests` is red

**Expected since 2026-09-23: they are two suites.** `tests/fitness/` is the `fitness` suite in
`.specconf/stack.json`, with its own junit (`.sdd/reports/fitness.junit.xml`), and
`./scripts/test.sh backend` and `./scripts/test.sh --no-db` no longer collect it. A red detector
shows up as the `Fitness tests` gate in `check.sh` and as the `Fitness tests` step of the
`backend` CI job (and the `fitness` step on the macOS leg), never inside the backend's count.
Reproduce it with `./scripts/test.sh fitness`, which needs no database and no Docker.

## A script failed, and `$?` says 0

**Cause.** The script was piped. `$?` after `./scripts/test.sh backend | tail -1` is `tail`'s
status, and that is always 0. The script contract — `0` did it, `1` did not, `4` did what it
could and named the gap, `2` the machine was busy, `124` it was killed — lives only in the exit
code, so the pipe replaced the answer.

**Fix.** Read the status unpiped, or put `set -o pipefail` in front: bash and zsh both honour it
and keep all five codes. Do not rely on `${PIPESTATUS[0]}` in a command you hand somebody else.
zsh spells it `${pipestatus[1]}`, so it works in one shell only.

**Which stream carries what.** stdout is the payload: a runner's log, a `--json` block, a
version. stderr is the verdict: `warn`, `failed:`, `error:`, the `Failed gates:` / `Not run:`
lists and the closing `…: OK | INCOMPLETE | FAILED` banner. On a terminal the two land together.
`./scripts/check.sh >run.log` leaves the whole answer on screen however much the suites printed.

Inside `scripts/`, `lists_line` / `lists_match` in `scripts/_lib.sh` are the only place a
pipeline may be read as a condition. They answer yes, no, or *the producer could not be asked*.
`tests/fitness/test_pipeline_verdicts.py` refuses a fourth copy of the old
`producer | grep -q` shape.

## A CI job I expected to run was skipped

**Most jobs are routed by which paths the diff touches**, so a job that did not run usually
means the filter that gates it does not name the directory you changed. The filters are in
`.github/workflows/ci.yml`, in the `changes` job, one `verdict <name> '<regex>'` line each; the
job summary prints the verdict it computed, so start there rather than guessing.

The routing set is an **allow-list**, and an allow-list fails in the dangerous direction: a
directory no filter names matches nothing, every routed job skips it, and the required check
goes green over a change nobody looked at. `tests/fitness/test_ci_parity.py` refuses a top-level
path that no filter names and that `_UNROUTED` does not declare, which is what keeps that from
happening quietly — so if you add a top-level directory, expect that test to ask you where it
belongs.

Two entries are worth knowing because they are not obvious from the job names:

- **`app/` routes the frontend job.** `dump_openapi.py` generates the contract from the Pydantic
  models, so a backend-only change is exactly how the committed TypeScript goes stale.
- **`golden-set/` routes the frontend job too**, since 2026-09-17. The vitest suite reads
  `text-measurement.json`, and `todo-task-text.json` for the to-do list's text rule, to prove the
  browser and the server measure text identically, so a corpus-only edit that skipped the frontend
  job would leave half of that claim unrechecked.

## Something else

The four failures this stack produced before anybody deployed it — a migration function that could
not connect, a proxy login that could not work, the Alembic one above, and a deployment order with a
window in it — are written up in [`infra/README.md`](../infra/README.md) § What was wrong before,
with the reasoning that found each. They are worth reading once: three of the four would have been
diagnosed from the wrong end.

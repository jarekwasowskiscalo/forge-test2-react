# Configuration reference

**For:** whoever has to change how a deployed copy behaves, or find out why one behaves as it does.
**Normative source:** the code that reads each variable — this table is derived from it, and
`tests/fitness/test_documentation_is_current.py` fails the build when the two disagree.

There is **no settings module and no configuration file**. Every value below is read from the
process environment at the point of use, which is why this page exists: nothing else in the
repository lists them together.

## What the application reads

Every one of these is read once, at import, in the module named.

| Variable | Read at | Default | What it does |
|---|---|---|---|
| `DATABASE_URL` | `app/db/session.py` | `postgresql+psycopg://app:app@localhost:5432/app` | The connection. On AWS it is built by Terraform and carries no password — see `DB_IAM_AUTH` |
| `APP_ENV` | `app/core/build_info.py` | `local` | Reported by `/api/health`. Drives the `noindex` header on previews, and is what stops the seeder writing to production |
| `APP_VERSION` | `app/core/build_info.py` | the version in `pyproject.toml`, then `0.0.0+unknown` | Reported by `/api/health`. This is how you tell which release answered. On prod it is the release tag, passed by `release.yml` to `deploy.yml`; on a preview `<version>+<sha>`. The `pyproject.toml` fallback is the package's own version and tracks no release — the tag is the only record of one |
| `LOG_LEVEL` | `app/core/logging_config.py` | `INFO` | One of `TRACE`, `DEBUG`, `INFO`, `WARNING`, `ERROR`. `TRACE` is this application's own level, below `DEBUG` |
| `LOG_FILE` | `app/core/logging_config.py` | empty — console only | A path turns on a rotating file handler, 5 MB × 3. The container leaves it empty deliberately: its filesystem is read-only |
| `FRONTEND_STATIC_DIR` | `app/main.py` | `app/static` | Where the built SPA is served from. Overriding it is how a test points at a throwaway build |
| `DB_IAM_AUTH` | `app/db/iam_auth.py` | unset | `1` makes the process sign an RDS IAM token instead of sending a password. Terraform sets it on the API function |
| `AWS_REGION` | `app/db/iam_auth.py` | — | Needed to sign that token. Provided by the Lambda runtime |
| `DB_IAM_USER` | `app/lambda_handler.py` | — | The role the migration function creates and grants `rds_iam` to. `app_iam` in every environment |
| `PREVIEW_DATABASE` | `app/lambda_handler.py` | unset | Set only on a preview's migration function. Its presence is what switches on "create the branch's database, then migrate it" |
| `AWS_LAMBDA_FUNCTION_NAME` | `app/db/session.py` | set by the runtime | Not configuration — the process reads it to know it is in Lambda, and pins the pool to one connection per execution environment. That pool size is why this stack needs no RDS Proxy |

**The SPA has no runtime configuration at all.** There is not one `import.meta.env` read in
`frontend/src/`, and that is a consequence of the architecture rather than an omission: the screen
and the API answer on one domain, so there is no API base URL to configure and no CORS anywhere in
the repository. The one `VITE_` variable, `VITE_API_PROXY_TARGET` in `frontend/vite.config.ts`, is
read by the **dev server's** proxy and never reaches the browser.

## What Terraform sets, and where

You do not set these by hand; this is where to look when a deployed copy behaves unexpectedly.

| Function | Variables |
|---|---|
| API (stage, prod) | `DATABASE_URL` without a password, `DB_IAM_AUTH=1`, `APP_ENV`, `APP_VERSION` |
| Migration (stage, prod) | `DATABASE_URL` with the master credentials, against the **cluster** endpoint rather than the proxy endpoint, `DB_IAM_USER=app_iam`, `APP_ENV`, `APP_VERSION` |
| API (preview) | as the long-lived API, with `APP_ENV=preview` |
| Migration (preview) | as above, plus `PREVIEW_DATABASE` |
| Maintenance (preview layer) | `DATABASE_URL` with the master credentials, `APP_ENV=preview`, `APP_VERSION` |

## What each environment declares

The numbers, in one place. They live in `infra/terraform/envs/<environment>/main.tf` and
`infra/terraform/preview/shared/main.tf`; a fitness test holds this table equal to them.

| | preview | stage | prod |
|---|---|---|---|
| database capacity, minimum | 0 | 0 | **0.5** |
| database capacity, maximum | 2, shared by every branch | 4 | 8 |
| backup retention | 1 day | 7 days | 14 days |
| log retention | 3 days | 14 days | 30 days |
| API reserved concurrency | — | 20 | 40 |
| VPC | `10.45.0.0/16`, shared | `10.43.0.0/16` | `10.44.0.0/16` |

**A minimum of 0 means you pay for storage alone at rest** — and that the first request after a
longer silence waits ten to fifteen seconds for the cluster to wake. The API function's timeout is
30 seconds, so it fits. Production buys its way out of that pause with a floor of 0.5 ACU.

## What the scripts read

| Variable | Read by | Default | What it does |
|---|---|---|---|
| `APP_PORT` | `scripts/_lib.sh` | `8080` | One variable decides the port, the health poll and the address the end-to-end suite knocks at |
| `APP_HEALTH_URL` | `scripts/_lib.sh` | derived from `APP_PORT` | |
| `POSTGRES_HOST_PORT` | `scripts/_lib.sh`, `docker-compose.yml` | `5432` | The clean room picks a free one instead |
| `POSTGRES_HOST_BIND` | `docker-compose.yml` | `127.0.0.1` | **Which addresses the local database answers on.** Loopback, so it is reachable from this machine and from nothing else. `0.0.0.0` publishes it to the network — a deliberate act, because the credentials below are fixed and documented |
| `APP_TEST_DATABASE_URL` | `tests/_database.py` | — | Points the backend suite at your own Postgres, so a machine without Docker can still run it |
| `E2E_ALLOW_REMOTE_RESET` | `e2e/harness/database.py`, `scripts/e2e_database.py` | unset | **A safety interlock.** The end-to-end harness truncates tables between scenarios; this opts out of its address check. Compared by equality — `1`, or the name of the one database you mean. Any other value is refused rather than ignored, so an inherited `=0` cannot read as "off" |
| `E2E_RUN_ID` | `e2e/harness/database.py` | minted by `scripts/test.sh e2e` | The run a database's disposability mark has to name. Never set this by hand: it is what stops an old mark authorising a new run |
| `TARGET_BASE_URL` | `e2e/harness/client.py` | `http://127.0.0.1:8080/api` | Which application the black box is aimed at |
| `PREVIEW_SLUG`, `PREVIEW_BRANCH` | `scripts/infra.sh` | — | Required for `preview-branch`; the slug becomes the state key |
| `SDD_DEPLOY_BREAK_GLASS` | `scripts/deploy.sh` | unset | A signpost for somebody trying to deploy from a workstation, not a control — see [`security.md`](security.md) |
| `TERRAFORM_VERSION` | `scripts/_lib.sh` | `1.13.3` | Pinned. Two Terraform versions write two state formats |

## The local stack

`docker-compose.yml` runs Postgres with `app` / `app` / `app` as user, password and database — a
development credential, never used anywhere else. The application container maps `APP_PORT` to 8000
inside, and waits both for the database to be healthy and for the migration container to have
**completed successfully**: the image never migrates on start.

**That database answers on loopback only.** The mapping is
`${POSTGRES_HOST_BIND:-127.0.0.1}:${POSTGRES_HOST_PORT:-5432}:5432` — the address and the port are
two variables because they are two decisions. A mapping with no address publishes on every
interface, which for the one service that carries a credential means the whole network can reach it
with a password printed in this file. Set `POSTGRES_HOST_BIND=0.0.0.0` when you actually want that;
nothing in the project does. Container mode (`./scripts/start.sh --container`) does not use the
published port at all — `app` and `migrate` reach the database by service name over the compose
network — so it works with the port bound narrowly, or not published at all.

`Dockerfile` pins both base images by digest with the tag beside it, runs as uid 10001 on a
read-only filesystem, and health-checks `/api/health` — not `/health`, which the SPA catch-all
answers with the HTML shell.

## Changing one of these

A variable added to the application is added here in the same commit. That is not a convention —
`operations-doc` refuses a change to the operational surface that leaves `docs/` untouched, and the
fitness test refuses a variable the application reads and this page does not name, in both
directions: a variable documented here and no longer read anywhere is a ghost, and a ghost in a
reference is worse than a gap, because somebody will set it and wait for something to happen.

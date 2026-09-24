# Security

**For:** whoever has to say who can do what, and what is protecting the account.
**Normative source:** [`spec/invariants.md`](../spec/invariants.md) for the non-goals;
[`spec/design/architecture.md`](../spec/design/architecture.md) § Environments for the deployment
controls; [`infra/README.md`](../infra/README.md) § The roles for the IAM detail.

## The first thing to know

**The application has no authentication and no authorisation.** Anybody who can reach the URL can
read every entry, write one, amend anybody's and delete anybody's. This is a *named non-goal*, not
an oversight — it is written down in [`spec/invariants.md`](../spec/invariants.md), and the hook
point is `app/api.py`, where the `/api` prefix is applied and where a dependency would
go.

The consequences to state to whoever takes delivery:

- A preview's URL is a **public, unauthenticated Lambda function URL**. Anything posted into a
  preview is world-readable by anybody with the link. Previews carry `X-Robots-Tag: noindex,
  nofollow` so they do not end up in a search index, which is a mitigation and not a control.
  **Every response, a `500` included.** That last sentence was untrue until 2026-09-16: Starlette
  answers an unhandled exception from a layer built outside the one that adds the header, so a
  crashed route was the one page a crawler could have indexed. `app/core/errors.py` now catches it
  inside that layer.
- `stage` and `prod` are equally open. There is no IP allow-list and no basic auth.
- **Nothing in this system should hold personal data** until authentication exists.

## What protects the AWS account

Not much needs to, because there is very little to steal — but the deployment path is the part that
matters, and it is genuinely well defended.

**No long-lived AWS credentials exist anywhere.** No access keys, no GitHub Actions secrets — not
one workflow reads `secrets.*`. GitHub authenticates by OIDC and assumes a role.

**The trust policy is the control, not the permissions policy.** Both deployment roles carry
`AdministratorAccess`, said outright rather than hidden: this stack creates resources in more than a
dozen services, and a badly narrowed policy fails mid-`apply` and leaves an environment half built.
What stops anybody else using them is the `sub` condition, which accepts
`repo:<owner>/<name>:environment:<name>` and nothing else — environments only, no `ref:` claims, no
wildcard. A fork, a pull request from one, and any other repository on GitHub are all excluded by it.

| Role | Assumable by | May |
|---|---|---|
| `sdd-guestbook-deploy` | the `preview`, `stage` and `prod` environments | everything |
| `sdd-guestbook-preview` | the `preview` environment | everything **except** the stage and prod state and secrets |
| `sdd-guestbook-plan` | people, if you named any | read everything, change nothing |

> **The preview environment's variable is a security control.** The deploy role is trusted by
> `preview` too, so which role a preview actually gets is decided entirely by the environment-level
> `AWS_DEPLOY_ROLE_ARN` overriding the repository-level one. Forget it and every preview runs as an
> unrestricted administrator, with read access to the stage and production Terraform state — where
> the Aurora master password is stored in cleartext. Nothing fails and nothing warns. See
> [`aws-account-setup.md`](aws-account-setup.md) § 7.

The preview role's narrowing is a **`Deny`**, not a shortened `Allow`, and the difference matters: a
Deny cannot fail for a permission somebody forgot to grant, so it cannot leave a stack half built.

**Break-glass is in IAM, not in a flag.** If GitHub is down and something must be deployed, an
account administrator attaches the deploy policy to themselves for the duration, and CloudTrail
records it. `SDD_DEPLOY_BREAK_GLASS=1` in `scripts/deploy.sh` is a signpost for the person who tries
it without credentials; it is not the control and cannot be.

## Where the secrets are

| Secret | Where it lives | Who reads it |
|---|---|---|
| Aurora master password | Secrets Manager, `sdd-guestbook-<env>/database/master` | the migration function, and a human doing a restore |
| The same password, in cleartext | the Terraform state, in the state bucket | whoever holds the deploy role |
| The application's database credential | **there isn't one** — the API function signs an RDS IAM token locally, as `app_iam` | — |

Nobody types the master password: Terraform generates 40 characters of it. The API function holding
no password at all is the single best property of this arrangement — a compromised function has a
token that expires in fifteen minutes and is scoped to one database user.

Both deployment workflows upload only their log as an artefact, never the state and never a plan,
for exactly the reason in the second row.

## The network

Two private subnets in two availability zones, and **no internet gateway, no NAT and no VPC
endpoints**. The function reaches exactly one thing and it is in the same VPC. The saving is real
(~30 USD a month per environment) and so is the consequence: the function cannot call any AWS API
during a request, which is why it authenticates with a locally signed token rather than fetching a
password from Secrets Manager.

The database's security group accepts traffic from the Lambda security group and from nothing else.
Neither cluster is publicly accessible.

## Data, and what leaves the machine

Article XI of [`spec/constitution.md`](../spec/constitution.md): personal data does not leave the
machine that needs it. In practice:

- Application logs carry **identifiers and counts, never values** — and that is enforced rather
  than agreed. `ExceptionSummaryFilter` sits on every sink `app/core/logging_config.py` configures
  and reduces any exception on a record to its type and its frames, so a traceback, a bind
  parameter, a driver's `DETAIL:` line and a cause chain cannot reach a log the way the message
  text could not. **One residual and it is named rather than implied:** on Lambda, an exception
  that escapes the handler is printed by the runtime itself, outside Python logging, so it reaches
  CloudWatch unfiltered. The catch-all in `app/core/errors.py` is what keeps one from escaping.
- The API Gateway access log carries no query string and no request body.
- `pyproject.toml` sets `junit_logging = "no"`, so a failing assertion's captured output never
  reaches a test report.
- End-to-end reports are not committed, and screenshots of failed browser smokes land in a
  gitignored directory.

**Do not paste application logs or JUnit files into an agent session.** That is the same road,
only longer.

## Supply chain

Both container base images are pinned **by digest**, with the tag beside them, and a test holds the
pin. The Python and the Node those images name are the same the CI runs, the Lambda function runs
on and the preflight asks for — one value in every home (3.14 and 26 since 2026-09-08), held by
`tests/tooling/test_toolchain_versions.py`, because they had drifted three ways before anything
asked. Python dependencies are locked in `uv.lock`; the frontend's in `package-lock.json`.
Every workflow step runs a 40-character commit rather than a tag, with the tag in a comment
beside it, and `tests/fitness/test_action_pins.py` holds the pins — a tag is a mutable ref, so an
unpinned step is code running here that no commit of ours reviewed. Two references are exempt and
named there: the change process's own composite actions track its trunk while it is at 0.x.

Dependabot watches npm, uv, GitHub Actions, Docker and Terraform, and leaves the base images'
majors to a human: a bump of one home alone is a red build by construction. `./scripts/audit.sh`
reports known vulnerabilities **one section per ecosystem**, and CI runs it: `npm audit` over
`frontend/package-lock.json` (fails at high) and `uv audit` over `uv.lock` (fails at any severity —
`uv audit` has no threshold to set, and it is still flagged experimental by uv). The base images,
the Terraform providers and the actions get **no advisory query**, and each line says so rather
than staying silent: they are pinned by digest, by `.terraform.lock.hcl` and by commit
respectively, with Dependabot proposing each bump. An ecosystem whose tool is absent is a named
gap — exit 4, never a pass.

Terraform is pinned to `1.13.3` exactly — not a floor. Two Terraform versions write two state
formats, and the newer one locks the older out of the state for everybody.

## Rotating things

The database credential is rotated by
[`runbooks/rotate-database-credentials.md`](runbooks/rotate-database-credentials.md). There is
nothing else to rotate: no API keys, no service accounts, no long-lived AWS credentials. If that
list ever grows, it belongs here.

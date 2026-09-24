# Setting the AWS account up

**For:** whoever is putting this application into an AWS account for the first time.
**Normative source:** [`spec/design/architecture.md`](../spec/design/architecture.md) § Environments
for the rulings behind this; [`infra/README.md`](../infra/README.md) for what each Terraform root
contains and what it costs.

Follow this once per AWS account. It takes about an hour, most of which is Terraform waiting on
AWS. At the end a branch can raise its own preview, `stage` can be deployed to, and a release can
go to production behind a required reviewer.

## Which keys, and where — the short answer

**There are none.** That is not a simplification and it is the single most important thing on this
page:

- **No AWS access keys anywhere.** GitHub Actions authenticates by OIDC and assumes a role. There
  is no key to rotate, leak or forget.
- **No GitHub Actions secrets.** Not one workflow reads `secrets.*`. The only repository setting
  you create is a **variable**, `AWS_DEPLOY_ROLE_ARN`, and an ARN is not a secret — an ARN in a log
  is exactly what you want when a deployment goes to the wrong account.
- **No database password to choose or store.** Terraform generates a 40-character master password,
  puts it in Secrets Manager, and never shows it to a human. The application never uses it: the API
  function signs an RDS IAM token instead.

The only credential a person ever holds is **an administrator session on your own AWS account, used
for step 4 and never again**. Everything after that is done by a role that only GitHub can assume.

## 1. What you need on your machine

| Thing | Why | Checked by |
|---|---|---|
| AWS administrator credentials for the target account — SSO or an IAM user | the bootstrap creates IAM roles and an OIDC provider | the `apply` fails without them |
| The AWS CLI on `PATH` | `deploy.sh` and `preview.sh` call it directly | `scripts/deploy.sh`, `scripts/preview.sh` refuse without it |
| Terraform **exactly `1.13.3`**, or Docker | two Terraform versions write two state formats, and the newer one locks the older out of the state for everybody | `scripts/infra.sh` uses the pinned binary if you have it and the pinned image otherwise |

Set the provider cache **before your first `init`**, or five Terraform roots each download their own
copy of the AWS provider — about 775 MB, five times over:

```bash
export TF_PLUGIN_CACHE_DIR="$HOME/.terraform.d/plugin-cache"
```

Put it in your shell profile. It only affects an `init` run *after* the variable is set; it does
nothing to copies already on disk.

## 2. Decide the region

`eu-central-1` is written into **thirteen** files: four `backend.tf`, five `variables.tf` defaults,
three workflow `AWS_REGION` values and `infra/README.md`. Change them together or not at all — a
state bucket in one region and a backend block naming another is an `init` that fails with a
message about neither.

```bash
grep -rl eu-central-1 infra/ .github/workflows/
```

## 3. Fill in the bootstrap's variables

Copy [`infra/terraform/bootstrap/terraform.tfvars.example`](../infra/terraform/bootstrap/terraform.tfvars.example)
to `terraform.tfvars` beside it. Neither required value is a secret, and that file is deliberately
**not** gitignored: an account whose settings are written down is an account whose next operator
does not have to guess.

| Variable | Required | What it is |
|---|---|---|
| `state_bucket_name` | **yes** | The S3 bucket every other Terraform state goes in. Globally unique across all of S3 — put the account id or the company name in it. |
| `github_repository` | **yes** | `owner/name`. This string decides which repository's workflows may assume the deploy role, and it is the **only** thing standing between an `AdministratorAccess` role and any workflow on GitHub. Get it wrong and you have given away the account. |
| `create_oidc_provider` | no, `true` | Set `false` if the account already has `token.actions.githubusercontent.com`. There can be only one per account; a second `apply` fails with `EntityAlreadyExists`. |
| `plan_role_principals` | no, `[]` | Who may assume the read-only role and run `plan`. **Empty creates no role at all** — the right default until you have decided who. |

**In this repository `terraform.tfvars` is already filled in and committed**, so this account's
settings are readable rather than remembered. Anything that genuinely should not be committed goes
in a `*.tfvars.local` file, which is gitignored.

## 4. Apply the bootstrap

```bash
./scripts/infra.sh bootstrap apply
```

Its state stays **local**, in that directory: the bucket that stores every other state cannot store
its own. That is an ordinary chicken and egg, solved the ordinary way — and it means this one
directory's `terraform.tfstate` is worth keeping.

What now exists in the account, by name:

| Resource | Name | Notes |
|---|---|---|
| S3 bucket | whatever you set `state_bucket_name` to | versioned, AES256, all public access blocked, `prevent_destroy` |
| OIDC provider | `token.actions.githubusercontent.com` | audience `sts.amazonaws.com` |
| IAM role | `sdd-guestbook-deploy` | `AdministratorAccess`. Trusted by the `preview`, `stage` and `prod` environments |
| IAM role | `sdd-guestbook-preview` | `AdministratorAccess` **plus an inline `Deny`** on the stage and prod state prefixes and their Secrets Manager entries. Trusted by the `preview` environment only |
| IAM role | `sdd-guestbook-plan` | read-only, **and only if you named principals** |

**There is no DynamoDB lock table.** Locking is `use_lockfile = true` — S3 conditional writes. If
you are following an older runbook that tells you to create one, it is out of date.

`AdministratorAccess` is said outright rather than hidden. This stack creates resources in more than
a dozen services, and a badly narrowed policy fails in the middle of an `apply` and leaves an
environment half built, which is worse than either extreme. What protects the account is the trust
policy, not the permissions policy.

Note the four outputs — `state_bucket`, `deploy_role_arn`, `preview_role_arn`, `plan_role_arn`:

```bash
./scripts/infra.sh bootstrap output
```

## 5. Paste the bucket name into four backend blocks

A Terraform backend block takes no variables, so the bucket name is a literal in each root and you
fill it in by hand. Replace `REPLACE-ME-terraform-state` in **all four**:

| File | Its state key |
|---|---|
| `infra/terraform/envs/stage/backend.tf` | `sdd-guestbook/stage/terraform.tfstate` |
| `infra/terraform/envs/prod/backend.tf` | `sdd-guestbook/prod/terraform.tfstate` |
| `infra/terraform/preview/shared/backend.tf` | `sdd-guestbook/preview/shared/terraform.tfstate` |
| `infra/terraform/preview/branch/backend.tf` | **none, deliberately** — one state per branch, and the key is supplied at `init` as `sdd-guestbook/preview/<slug>/terraform.tfstate` |

This is the step that is easiest to skip, because nothing asks you for it and the failure comes
later, from a different command. Check it:

```bash
grep -rn REPLACE-ME infra/terraform
```

Anything still printed is a root that cannot reach its state —
`infra/terraform/bootstrap/terraform.tfvars.example` will always print, and should: it is the
form the next operator copies, not a root.

**In this repository the four are already filled in**, with the bucket this account's bootstrap
creates. A fork starting from a different account replaces them, and there is no way round
doing it by hand: a backend block takes no variables, so the name cannot come from a `.tfvars`
the way every other value does.

## 6. Raise the shared preview layer

```bash
./scripts/infra.sh preview-shared apply
```

Once per account. It creates the VPC, the Aurora cluster and the maintenance function that every
per-branch preview borrows, and publishes ten SSM parameters under `/sdd-guestbook/preview/` — which
is the entire contract between this layer and a branch's own root. A branch creates two Lambda
functions and a public URL, and nothing else.

## 7. GitHub → Settings → Environments

Create three. **The environment's name is half the authorisation**: the roles' trust policies accept
`environment:<name>` as the OIDC `sub` claim and nothing else, so an environment that does not exist
is a deployment that cannot happen.

| Environment | Deployment branches | Reviewers | Environment variables |
|---|---|---|---|
| `preview` | **All branches** | none | **`AWS_DEPLOY_ROLE_ARN` = `preview_role_arn`** |
| `stage` | **All branches** — this is what lets you test a branch before merging it, and it also receives every merge to the trunk | optional | — |
| `prod` | **Selected**: a **tag** rule `v*`, and no branch rule | **required, at least one** | — |

> **The `preview` variable is a control, not a convenience.** The deploy role is trusted by the
> `preview` environment too — it has to be, because `preview.yml` declares that environment. The
> environment-level variable overriding the repository-level one is the *only* thing that makes a
> preview run use the restricted role. Set the repository variable, forget this one, and every
> preview runs as an unrestricted administrator with read access to the stage and production state,
> where the Aurora master password sits in cleartext. Nothing fails and nothing warns.

Two more things worth knowing before you start. Deployment-branch rules on a **private** repository
need GitHub Pro or Team; environments are unrestricted only on public ones. And `prod` having a tag
rule and no branch rule is what makes production unreachable by a manual dispatch even if somebody
re-adds it to the dropdown.

## 8. GitHub → Settings → Secrets and variables → Actions → Variables

- **`AWS_DEPLOY_ROLE_ARN`** = `deploy_role_arn`, at the **repository** level.

It has to be set at the repository level even though `preview` overrides it, because two workflows
test it in a job-level `if:` — and a job's `if:` is evaluated *before* the environment resolves. Left
unset there, the preview and teardown jobs skip silently.

## 9. GitHub → Settings → Secrets and variables → Actions → Secrets

**None. Do not create any.** No workflow in this repository reads a secret.

## 10. GitHub → Settings → Rules on the default branch

**Already done on this repository, and the history is worth keeping.** Ruleset `main` (id
22747644) has been active since 2026-09-10: it requires a pull request, requires `CI passed`,
and its bypass list is empty. A fork of this template starts without it and has to create it.

It could not be created before that date, and the symptom named the wrong cause: the API
answered 403 with "Upgrade to GitHub Pro or make this repository public", which reads like a
billing fault. The organisation was on Team the whole time. The obstacle was that this
repository was a **fork** of a private repository in another organisation, and GitHub gates the
feature on the root of the fork network rather than on the owner. Detaching the fork was the
whole fix, and it cost nothing — same URL, same history, same pull requests. If the API answers
403 here, check the fork network before checking the invoice.

What the ruleset carries:

- Require the status check named **`CI passed`**.
- **Leave the bypass list empty.** `release.yml` needs nothing on it: the release makes no commit
  and pushes only `refs/tags/vX.Y.Z`, which a `branch` ruleset does not cover. The tag is the only
  record of a version, and the commit it names got onto the trunk by being reviewed. Putting
  `github-actions[bot]` on the list would not configure the protection, it would remove it.

## 11. First runs, in this order

1. Push a branch → Actions → **Preview** → Run workflow. The URL arrives as a comment on the pull
   request. Confirm the guest book has entries in it and the to-do list its example tasks — a new
   environment seeds itself.
2. Close the pull request → confirm **Preview teardown** ran and the stack is gone.
3. Actions → **Deploy** → `stage`, from that same branch. This is where acceptance testing happens,
   before the merge rather than after it.
4. Merge → Actions → **Release** → `minor` → approve the `prod` gate → confirm `/api/health` reports
   the new `version` and `environment: prod`.

`workflow_dispatch` runs the workflow file **from the branch you pick**, so a branch cut before these
workflows landed has to be rebased before its buttons appear.

## 12. The database, which needs nothing from you

Aurora Serverless v2, `aurora-postgresql 16.6` — one cluster per long-lived environment, plus one
shared cluster holding a database per preview branch. There is no manual step here at all, and this
section exists so that nobody goes looking for one.

| Question | Answer |
|---|---|
| Where is the master password? | Secrets Manager, at `sdd-guestbook-<environment>/database/master`. Terraform generates it; nobody types it |
| Does the application use it? | **No.** The API function holds no password and signs an RDS IAM token locally as the user `app_iam`. Only the migration function uses the master credentials |
| Who creates `app_iam`? | The migration function, on its first run, together with `GRANT rds_iam` |
| Is it in the Terraform state? | Yes, in cleartext. That is exactly why the preview role is denied the stage and prod state prefixes, and why the deploy workflows upload only their log and never the state or the plan |
| Is there an RDS Proxy? | No, in any environment, and **it cannot be turned on**: `enable_proxy` refuses anything but `false` at `terraform validate`, because the proxy's auth and one security-group rule are both missing. The API function's `reserved_concurrent_executions` is its connection ceiling instead — 20 on stage, 40 on prod. `infra/terraform/modules/database/main.tf` § header names what would have to be built first |

## What you are not asked to configure

No DynamoDB table. No `TF_VAR_*` — every variable goes through `-var` inside `scripts/infra.sh`. No
access keys. No NAT gateway and no VPC endpoints (the function reaches exactly one thing and it is in
the same VPC). No custom domain or ACM certificate by default; if you add one, the certificate
**must** be in `us-east-1`, because CloudFront reads it from there.

One thing you do not choose but should know about: the web bucket names are derived —
`sdd-guestbook-stage-web` and `sdd-guestbook-prod-web` — and S3 bucket names are globally unique. If
somebody else in the world holds one, the first `apply` of that environment fails part way through.
Change `project` in that environment's `main.tf` and the derived names change with it.

## When it goes wrong

[`troubleshooting.md`](troubleshooting.md) has the failures this stack has actually produced, with
what each one looks like from the outside.

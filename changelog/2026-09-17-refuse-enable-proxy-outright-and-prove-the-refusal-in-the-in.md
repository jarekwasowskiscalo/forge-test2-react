---
date: 2026-09-17
branch: claude/github-ticket-implementation-22f0d3
pr: 56
kind: fix
---

# Refuse `enable_proxy` outright, and prove the refusal in the infrastructure gate

## What changed

- `infra/terraform/modules/database/variables.tf` — `enable_proxy` gains a `validation`
  block rejecting `true`, with an `error_message` naming both blockers and pointing at the
  module header. Its description no longer reads as a settled cost decision.
- `infra/terraform/modules/stack/variables.tf` — `database_enable_proxy`'s description says
  it is a passthrough to a parameter that refuses everything but `false`.
- `infra/terraform/refusals/database-proxy/` — **new**, and the first of a fourth kind of
  root: `main.tf` calls `../../modules/database` with `enable_proxy = true` so that
  `validate` has something to reject. No `backend.tf`, no variables, no outputs. Its
  `.terraform.lock.hcl` is `envs/stage`'s, so the fixture pins what the environments pin.
- `scripts/infra-check.sh` — a `REFUSALS=(...)` array and a third step that requires
  `validate` to **fail** there, and to fail with the expected phrase. Header and `usage()`
  say three questions rather than two.
- `tests/fitness/test_infra_layout.py` — five assertions and the fourth kind in the module
  docstring: parity between the tree's `refusals/*` and the script's list, the grepped phrase
  is text some `error_message` really contains, no refusal root is in `ROOTS`, none is
  reachable from `infra.sh`, and each pins its provider, its language and no backend.
- `infra/terraform/modules/database/main.tf` — header rewritten: the refusal, both blockers,
  and the arrangement to build, which is no longer the one it used to recommend.
- `infra/terraform/modules/network/main.tf` — the comment above
  `aws_vpc_security_group_egress_rule.database_to_itself` stops promising an ingress rule
  that does not exist, and says why it is left undone.
- `infra/README.md` — § No RDS Proxy carries the refusal; the directories table gains
  `refusals/*/`; the § What was wrong before bullet names the second blocker.
- `docs/aws-account-setup.md`, `docs/operations.md`, `docs/troubleshooting.md` — the three
  places an operator meets this decision. The account FAQ row says the switch cannot be
  turned on; the concurrency-ceiling paragraph says a proxy is not the release valve for it;
  and the throttling entry gains a **Not the fix** paragraph, because that is where somebody
  under pressure reaches for `database_enable_proxy = true`.

## Why

`modules/database` offered `enable_proxy` as an ordinary `bool` with no `validation` and a
description promising a ready operational choice ("on where a connection storm would actually
happen"). It is not one. Setting it produces a stack whose API function cannot connect, for
two independent reasons:

1. **Auth.** The proxy's single `auth` block names the *master* secret, while the API
   function connects as `app_iam` by an IAM token (`modules/api/main.tf`,
   `app/db/iam_auth.py`). And `endpoint` *becomes* the proxy when the flag is on
   (`modules/database/outputs.tf`), so the application is routed at a proxy holding no entry
   for it.
2. **Network.** `modules/network` has a self-referencing *egress* rule on the database group
   and no self-referencing *ingress* rule; the group's only ingress admits the `lambda`
   group. The proxy-ENI to cluster-ENI hop is evaluated in both directions, so the proxy
   would report every target unavailable. Fixing the auth alone would still not connect.

The second one was not recorded anywhere — not in `infra/README.md`, not in either earlier
audit — and the comment above the egress rule read as though the requirement were already
met, so whoever came to check would have read it and stopped looking.

Nothing was broken: every caller passes `false`, and the module defaults to it. The exposure
was that `terraform validate` — the only Terraform CI runs — would have waved `true` through,
and `git grep enable_proxy` over `tests/`, `scripts/` and `.github/` found nothing at all.

Raised as [#32](https://github.com/Scalo-Sales-Engineering-Consulting/forge_template_python_react/issues/32)
out of the 2026-09-15 audit (A43, P3).

## From what, to what

**Before.** `enable_proxy = true` passed `terraform fmt`, passed `terraform validate`, passed
every gate, and produced a stack that could not serve a request. The module header explained
the auth half in a comment and recommended a fix — a second secret, with `app_iam` taken out
of `rds_iam` — resting on the premise that a proxy can only reach a database by password.

**After.** `enable_proxy = true` is refused at `validate`, by a message naming both reasons
and where to read about them. `false` remains legal and is exercised by all five real roots
on every pull request. The recommended arrangement is corrected: the pinned provider
(`~> 6.0`, locked at 6.62.0) exposes `default_auth_scheme`, whose accepted values are `NONE`
and `IAM_AUTH`, and end-to-end IAM authentication needs no Secrets Manager secret for the
client — so `app_iam` stays in `rds_iam` and `app/db/iam_auth.py` needs no change. The
premise the old recommendation rested on was stale, not wrong at the time.

## How it works now

`./scripts/infra-check.sh` asks three questions instead of two. After `fmt -check` and the
five `validate`s that must succeed, it walks `REFUSALS` — `<root>|<phrase>` pairs, a pair
list rather than an associative array because macOS ships bash 3.2 — and for each one
requires `validate` to fail **and** the output to contain that phrase. Whitespace is squeezed
first, because Terraform wraps an `error_message` at the terminal width.

Both halves are load-bearing. An exit code alone would report a typo, a moved module or a
provider that would not install as the barrier working, which is how a barrier stops
existing. And the negative step means something only because the loop before it passes the
same parameter with the supported value: together they say the barrier rejects one value
rather than every value.

Nothing changed in `.github/workflows/ci.yml`. The `infra` job runs this script, so the step
arrived with it — and `./scripts/check.sh` runs the same file, so a green local run and a
green pull request stay the same claim.

A refusal root is the one kind here that is neither in `ROOTS` nor reachable from
`infra.sh`. Both absences are deliberate — there is nothing to plan and nothing to apply, and
offering `./scripts/infra.sh refusals-database-proxy apply` would offer a command whose only
outcome is an error — and both are asserted in `tests/fitness/test_infra_layout.py`, so they
are rules rather than oversights somebody helpfully corrects. That file's `refusals/*` list
is **discovered**, like its environment list, so a second refusal added later is covered
without anybody remembering the file.

## What it means for the process

Nothing about running or changing this repository moves. One habit is now enforced instead of
hoped for: a module parameter this stack cannot honour gets a `validation` block and a root
under `infra/terraform/refusals/`, and the gate proves the refusal rather than the prose
claiming it.

## What it does not change

- **The proxy is not implemented.** This change builds no proxy and fixes neither blocker. It
  makes the unsupported parameter say so.
- **No deployed environment is touched.** `stage`, `prod` and the preview layer all passed
  `false` before and after; the plan for each is unchanged. The `validation` fires only on a
  value nothing sets.
- **The missing self-referencing ingress rule is left missing**, on purpose. With the switch
  shut there is no proxy for it to serve, and adding it now would be a rule guarding nothing
  — and would take with it the only record of why the switch is shut. It is named in the
  module header as one of the two things to build.
- **Acceptance criterion 2 of #32 is not met and cannot be**: the proxy target reporting
  `AVAILABLE`, `app_iam` connecting through the proxy endpoint, and a role without
  `rds-db:connect` being refused are all questions about a live AWS account with a proxy
  deployed. The ticket scopes that as a separate change, and its own criterion 3 says
  `terraform validate` proves nothing about authentication. It still does not.
- **One documented contradiction is left open rather than resolved.** The AWS page that
  documents `IAM_AUTH` also still states that a proxy "always connects to the database using
  password authentication through Secrets Manager". The module header records the conflict;
  settling it needs an account, not a reading.

## How it was verified

- `./scripts/infra-check.sh` — green: `fmt -check`, the five roots validating, and
  `refusals/database-proxy` refused with the message naming the reason. Ran through Docker
  (`hashicorp/terraform:1.13.3`), there being no local Terraform on this machine.
- **The new gate step was made to fail, both ways.** Flipping the fixture to
  `enable_proxy = false` → `error: refusals/database-proxy was ACCEPTED…`, exit 1. Weakening
  the `error_message` so it no longer names the parameter → `error: … refused, but for the
  wrong reason…`, exit 1. Both reverted, and the gate green again afterwards.
- **Each new fitness assertion was made to fail.** Pointing the script's entry at a
  directory that does not exist, adding the refusal root to `ROOTS`, offering it from
  `infra.sh`, and drifting the grepped phrase from the `error_message` each turn exactly the
  intended test red — and the corresponding pre-existing test too, where one applies.
- `./scripts/test.sh fitness` — 275 passed. `./scripts/test.sh unit` — 234 passed,
  23 skipped.
- `./scripts/check.sh` — every gate this application's CI runs. Its e2e leg needed
  `POSTGRES_HOST_PORT` set, this machine already having a Postgres on 5432; that is
  configuration and not a finding.
- `sdd-specs` — Specs: OK, and `sdd-specs --diff-gates --base <merge-base>` clean. The
  `operations-doc` gate is what found that `infra/README.md` had moved and `docs/` had not,
  which is how the three documents above came to be edited rather than forgotten.
- `./scripts/changelog.sh check --base main`.
- Not run, and it is the honest gap: no `terraform plan` and no apply, here or in CI. The
  `infra` job deliberately has no credentials, so nothing in this change has been seen by an
  AWS account.

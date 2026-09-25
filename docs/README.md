# `docs/` — the documentation of the system

**For:** whoever operates, maintains or takes delivery of this application.
**Normative source:** [`spec/README.md`](../spec/README.md) — every fact here has a home there, and
this tree cites it rather than restating it.

Start with [`solution-overview.md`](solution-overview.md) if the system is new to you, with
[`aws-account-setup.md`](aws-account-setup.md) if you are putting it into an AWS account for the
first time, and with [`runbooks/incident-first-response.md`](runbooks/incident-first-response.md) if
something is broken right now.

## The documents

| Document | What it answers |
|---|---|
| [`solution-overview.md`](solution-overview.md) | what the system is, what it is made of, and the four behaviours that will surprise you |
| [`aws-account-setup.md`](aws-account-setup.md) | how to set the AWS account up: which credentials, which values, and where each one is pasted |
| [`configuration.md`](configuration.md) | every variable the system reads, its default, and who sets it |
| [`deployment.md`](deployment.md) | how a version reaches preview, stage and production, and what a rollback does not undo |
| [`operations.md`](operations.md) | running it day to day: health, logs, capacity, seeding, migrations |
| [`monitoring.md`](monitoring.md) | what is observable, what is **not** monitored, and what to add first |
| [`backup-and-recovery.md`](backup-and-recovery.md) | what is backed up, for how long, and what a restore costs |
| [`security.md`](security.md) | who can do what, where the secrets are, and the fact that the application authenticates nobody |
| [`troubleshooting.md`](troubleshooting.md) | symptom → cause → fix |
| [`user-guide.md`](user-guide.md) | the guest book, for the person using it |
| [`user-guide-todo-list.md`](user-guide-todo-list.md) | the to-do list, for the person using it |
| [`runbooks/`](runbooks/README.md) | the procedures somebody carries out on a running environment |

## Two things to know before you rely on any of it

**There is no authentication.** Anybody who can reach the URL can read, write, amend and delete.
That is a named non-goal in [`spec/invariants.md`](../spec/invariants.md), not an oversight, and it
is the first thing to change if this stops being a template.

**There is no alerting.** The system is observable and unmonitored: logs are collected and retained,
and nothing watches them. [`monitoring.md`](monitoring.md) says so plainly and prices the fix.

## Nothing here binds

A document in this directory is operational and explanatory, never normative. Where a rule holds, it
holds because it stands in [`spec/`](../spec/README.md) or
[`contracts/`](../contracts/README.md), and the document here cites the one that owns it. A
descriptive document read as normative is a second home for one rule, which is the failure
[`spec/README.md`](../spec/README.md) exists to prevent. The rule for what goes in here and how it is
shaped: [`spec/design/conventions.md`](../spec/design/conventions.md) § Documentation — where a
document goes.

Three things keep these documents from drifting away from the system they describe, and they are
listed so a reader knows how much to trust the pages above: the `operations-doc` gate refuses a
change to the operational surface that leaves this directory untouched; the `documentation-set` gate
holds every file here to the shape declared above; and
`tests/fitness/test_documentation_is_current.py` resolves what these pages *claim* — every script
and flag, every variable, every AWS name and every environment number — against the code that owns
it, in both directions.

## What is not here

| Question | Where |
|---|---|
| What the system must do, and what must always be true | [`spec/`](../spec/README.md) |
| What the boundaries promise | [`contracts/`](../contracts/README.md) |
| The commands used while developing | [`CLAUDE.md`](../CLAUDE.md), and each script's `--help` |
| What each Terraform root contains, and what it costs | [`infra/README.md`](../infra/README.md) |
| What was changed outside the process, and why | [`changelog/`](../changelog/README.md) — one entry per pull request. A change that went through the process is recorded in `spec/changes/` instead |
| How a change is made — the SDD process | [the marketplace's README](https://github.com/Scalo-Sales-Engineering-Consulting/claude-marketplace/blob/main/README.md). What the process knows about this template -- its scripts, suites, paths and port -- it reads from [`.specconf/stack.json`](../.specconf/stack.json), the stack profile; the scripts it may call are the [script contract](https://github.com/Scalo-Sales-Engineering-Consulting/claude-marketplace/blob/main/plugins/forge/docs/script-contract.md). The process is independent of this application: it is a plugin, its commands (`sdd-specs`, `sdd-verify`, `sdd-engine`, …) arrive on PATH with it, its CI is its own, and nothing under `scripts/` calls it |

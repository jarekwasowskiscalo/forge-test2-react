# sdd-app-template

A template for a web application whose **specification is normative**: every behaviour change
travels through an agent-driven process, the specification changes in the same pull request as the
code, and twenty-odd gates make sure the two do not drift apart quietly.

The stack is FastAPI, Alembic and Postgres behind React and TypeScript, with four test suites, a
black box in Gherkin and a smoke in a real browser. One process on `:8080` serves the API and the
screen. On AWS it is a Lambda behind CloudFront with an Aurora Serverless cluster, and there is a
disposable environment per branch.

**There are two features, and only one of them is an example.** The guest book exists so that every
step of the process has something real to travel through, and it is meant to be deleted once your
first feature replaces it. The to-do list beside it (one shared list of one-line tasks, ticked done
and back) was added through the process as change `CR-2609-823a`, and it stays when the guest book
goes. [`CLAUDE.md`](CLAUDE.md) § What is an example, and what is the template says exactly what
goes with the guest book, and the one thing that has to move before it does.

## Start here

```bash
./scripts/install.sh
```

On a machine that already has `uv`, Docker and Node, `./scripts/start.sh` is enough. Either way the
application is at <http://127.0.0.1:8080>. The guest book already has entries in it, and the to-do
list, one link away in the header, opens with five example tasks, one of them already done.

**Every task has a script, and the scripts are the interface** — not the commands inside them, and
not this file. `./scripts/help.sh` lists them all and each takes `--help`. Before a push,
`./scripts/check.sh`, whose definition is "will CI pass".

## Where to go next

| If you want to | Read |
|---|---|
| understand what the system is | [`docs/solution-overview.md`](docs/solution-overview.md) |
| put it into an AWS account | [`docs/aws-account-setup.md`](docs/aws-account-setup.md) |
| run, deploy or repair a live copy | [`docs/`](docs/README.md) — configuration, deployment, operations, monitoring, backup, security, troubleshooting, and the runbooks |
| know what the system must do | [`spec/`](spec/README.md) — the normative specification |
| know what the boundaries promise | [`contracts/`](contracts/README.md) |
| develop it day to day | [`CLAUDE.md`](CLAUDE.md) — the structure, the commands, the gates |
| change something | say what you want to change, or call `/forge:sdd` |
| understand the process itself | [the marketplace's README](https://github.com/Scalo-Sales-Engineering-Consulting/claude-marketplace/blob/main/README.md) — what the process is, what a project must provide, and how it is checked |

## The directories

| Directory | What is in it |
|---|---|
| [`spec/`](spec/) | **The normative specification.** When it and the code contradict each other, one of the two is a defect |
| [`contracts/`](contracts/) | The boundaries as versioned contracts, written by hand |
| [`docs/`](docs/README.md) | **The system's documentation**, for whoever operates it |
| [`app/`](app/) | The backend, cut by bounded context: `contexts/<name>/` holds one context whole, layered inside it (`routers/` → `services/` → `models/` + `schemas/`), with `platform/`, `core/` and `db/` beside it |
| [`frontend/src/`](frontend/src/) | The SPA: screens, components, hooks, pure rules, the generated client |
| [`alembic/`](alembic/) | The migrations — the schema's only owner |
| [`tests/`](tests/) | Four pytest groups: `unit/`, `integration/`, `fitness/`, `tooling/` |
| [`e2e/`](e2e/) | The black box: Gherkin, plus a UI smoke in Chromium |
| [`golden-set/`](golden-set/README.md) | The only committed data, cut in two: what the suites assert about, and what a new environment opens with |
| [`scripts/`](scripts/) | The human interface — one task, one `.sh` |
| [`infra/`](infra/README.md) | Terraform: stage and prod as directories, plus a per-branch preview |
| [`.claude/`](.claude/) | The **pin** on the SDD process — `forge@scalo`, installed from [Scalo-Sales-Engineering-Consulting/claude-marketplace](https://github.com/Scalo-Sales-Engineering-Consulting/claude-marketplace) — plus the eleven skills that are this template's own, because they know FastAPI and React |
| [`retro/`](retro/) | The data of the process's self-audit loop: the session corpus, the rounds and the fix ledger |

## Two things that are true of this template and might not be of yours

**There is no sign-in.** The application authenticates nobody, which is a
[named non-goal](spec/invariants.md) rather than an absence somebody overlooked.
[`docs/security.md`](docs/security.md) says what follows from it.

**There is no alerting.** Logs are collected and retained; nothing watches them.
[`docs/monitoring.md`](docs/monitoring.md) says so plainly and lists what to add first.

## Changing it

A behaviour change goes through the process: a change record, a branch, stages and gates — and how
many steps each stage runs is computed by arithmetic over measured signals rather than by a
conversation. The specification never changes on its own or after the fact; it travels in the same
pull request as the code, declared line by line in that change's delta.

Starting your own product from here is three steps, in this order: run `./scripts/check.sh` and see
it green, walk `/forge:sdd` through **one real change**, and only then delete the guest book — by which
point you will know what you are replacing.

## Prerequisites

`uv` (Python 3.14), Node 26, and Docker with Linux containers. `./scripts/preflight.sh` says what is
missing. Docker is needed for Postgres and the integration suite; a machine with its own Postgres 16
points at it with `DATABASE_URL` and `APP_TEST_DATABASE_URL`, and a machine with neither gets a
named gap from `./scripts/check.sh --no-docker` rather than a green. The scripts are POSIX — on
Windows, run them through WSL or Git Bash.

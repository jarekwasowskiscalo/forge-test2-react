---
date: 2026-09-23
branch: chore/fault-report-label
pr: 81
kind: docs
---

# Compute the label of a process fault, and name the skill that files it

## What changed

`CLAUDE.md` § A change this template cannot make alone: the raw `gh issue create` line has been
removed. It typed `--label from-template`, the repository slug and the title prefix. In its place:

- banking the fault first with `sdd-engine change_state add-fault`;
- filing it with the `fault-report` skill, which runs `sdd-ownership`, fills the form and creates
  one issue;
- closing the entry with `resolve-fault --filed <url>`, or `--unfiled --reason` when it could not
  be filed.

The page says the destination and the label are computed and never written down. It cites
`process-failure.md` § Which document wins for who may post outward: the main conversation files,
and a worker reports a `PROCESS_FAULT` line.

`tests/fitness/test_fault_reporting.py` is new. It checks that the page names `fault-report`,
types no ownership label and no `--label` onto `gh issue create`, and cites `process-failure.md`.

`spec/design/testing.md` has the row for the new module and the alternatives rejected.

## Why

forge_template_python_react#58 / #65, audit ticket E5-03; the engine half is
claude-marketplace#206. Before this change, `CLAUDE.md:331` typed the label that `sdd-ownership`
computes from GitHub's record of the lineage. A repository created from this template inherits the
page, and with it a label that is wrong there. Fourteen issues in the marketplace register carry
the template's label and were raised from an instance.

The word `fault-report` appeared nowhere in the page, although it is the skill that does the
filing. And the page told a session to file at once, while `worker-contract.md` tells a worker it
never files. Nothing ranked the two.

## From what, to what

Before: one `gh issue create` line, with its destination, label and title prefix typed out and no
ranking against the process's documents. `grep -c 'label from-template' CLAUDE.md` = 1.

After: bank, then `fault-report`, then `resolve-fault`, with the precedence cited rather than
restated. The count is 0, and the fitness suite keeps it at 0.

## How it works now

When the fault belongs to the plugin, the main conversation banks it on the change record, and the
`fault-report` skill files it wherever `sdd-ownership` says, under the label `sdd-ownership`
prints. A worker reports the fault in one `PROCESS_FAULT` line and files nothing. Nobody searches
for a duplicate first.

## What it means for the process

The session stops assembling the `gh issue create` command by hand and uses the skill. Nothing else
moves.

## What it does not change

Filing is not forbidden, and a duplicate search is still not required. The stack name in a title
still comes from `.specconf/stack.json` § `name`. `.github/labels.md` and CI's labels are
untouched: they are the labels this repository's own workflow reads, not the ownership labels.

## How it was verified

- `./scripts/test.sh fitness`: 312 passed.
- Seen failing first: against `main`'s `CLAUDE.md` all three assertions fail. `fault-report` is
  absent, `from-template` is on line 331, and `process-failure.md` is absent.
- `./scripts/check.sh --fast --no-docker`: see the pull request. Its gaps are the database, Docker
  and e2e.
- `sdd-specs` (forge 0.1.124): OK. `./scripts/changelog.sh check`: OK.

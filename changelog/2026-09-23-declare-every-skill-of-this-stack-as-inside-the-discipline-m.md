---
date: 2026-09-23
branch: chore/measured-skills
pr: 84
kind: process
---

# Declare every skill of this stack as inside the discipline measurement

## What changed

`.claude/skills/*/SKILL.md`: all eleven skills gain a `**Measured.**` paragraph that cites
`${CLAUDE_PLUGIN_ROOT}/skills/_shared/process-failure.md`.

- The eight `build-*` workers carry it straight after the worker-contract line. It says their
  dispatch's calls are counted, and that a fault goes back as one `PROCESS_FAULT` line for the
  orchestrator to file.
- The three `run-*` skills carry it before their first section. It says this conversation's
  window is counted, and that a fault met here is filed at once with `fault-report`.

`.specconf/stack.json` § `skills.$comment` explains why the declaration is the tree and not a key:
`stack.py` allows an `operational` skill `kind` and nothing else.

`CLAUDE.md` § Skills and MCP servers gains two paragraphs. One says every skill is measured and
cites the rule. The other says a rise in the reported breach count is the scope widening, not a
regression.

`tests/fitness/test_skill_measurement.py` is new. It checks that every skill declares the marker,
cites `process-failure.md`, and does so at the plugin root, never as a path to open. The module's
row is added to `spec/design/testing.md`.

## Why

forge_template_python_react#58 / #67, audit ticket E5-08; the engine half is
claude-marketplace#211. The engine read only the parent conversation's calls: 30 of 286 in one
measured session, while 3 622 of 5 201 requests ran inside dispatches. The count was a lower
bound. And 66 of 69 charges in one audited session fell on a reader nothing had pointed at the
rule. The engine now counts every dispatch, and this repository's half is saying which skills are
in scope and giving each one the rule to read.

## From what, to what

Before: no skill named `process-failure.md` or said it was measured.

After: all eleven do, and the fitness suite fails the first skill that stops doing so.

## How it works now

A worker reads, in its own skill, that its calls are counted and where the rule is. A `run-*` skill
in the main conversation reads the same and files a fault as soon as it meets one. A new skill
under `.claude/skills/` is in the measurement by existing, and it must say so to pass.

## What it means for the process

Breach counts on this stack will rise, because the engine now reads the dispatches. Read the rise
as wider coverage and nothing else. A falling count of Bash calls is not by itself a measure of
quality.

## What it does not change

No skill's contract, `writes`, `requires` or model changes. No key is added to the profile. The
engine's counting is not reproduced here: this repository only states the scope.

## How it was verified

- `./scripts/test.sh fitness`: 323 passed. Seen failing first: with the skill edits set aside, 3
  failed (marker, rule and plugin-root form) and 320 passed.
- `sdd-specs` (forge 0.1.124), which lints every skill: OK. `sdd-engine stack --check`: OK.
- `./scripts/check.sh --fast --no-docker`: exit 4, and every gate that ran passed. The gaps it named
  are the database, Docker/Terraform and e2e.

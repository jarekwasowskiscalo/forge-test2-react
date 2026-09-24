---
date: 2026-09-15
branch: docs/say-how-a-change-travels
pr: 16
kind: process
---

# Say how a change travels, and where a change that belongs to forge goes

## What changed

`CLAUDE.md` gains two sections, between `## A behaviour change goes through /forge:sdd` and
`## Every other change leaves an entry in changelog/`.

`## The change flow — branch, pull request, CI, then merge` states the flow and the commands that
carry it, and names the three facts that were only discoverable from `.github/workflows/ci.yml`:
a branch with no pull request open gets no CI run at all, the verdict is the aggregate
`CI passed`, and that check cannot be required on this plan.

`## A change this template cannot make alone` names the surface shared with `forge@scalo` path by
path, restates the one-way dependency as a prohibition on patching the plugin, and gives the
`gh issue create` that files the ticket instead.

The Flutter template takes the same two sections in the same words, wherever the stacks agree.

## Why

`CLAUDE.md` is the brief an agent reads at session start, and it did not say how a change travels.
It never named the trunk — `main` appeared once, as a `--base main` flag — never said a pull
request was required, and said nothing about the merge. The facts existed in
`spec/constitution.md` Article IV, `.github/pull_request_template.md`, the header comment of
`ci.yml` and `docs/aws-account-setup.md`, but scattered across four files, none of which is read
at session start. The sharpest of them was buried deepest: that `CI passed` is a verdict nothing
can require while the repository is private on the free plan, so it is enforced by whoever is
holding the keyboard.

The second gap was larger, because nothing anywhere covered it. The coupling to the plugin is
real, and a template that found the engine in its way had no route for saying so: the one-way rule
forbids patching the process, and `claude-marketplace` had no issue template and the plugin no
`gh issue` call. The report died with the session that found it.

## From what, to what

Before: the flow was known to whoever already knew it. A change could be committed to `main` with
nothing in this file to say otherwise, and a coupling problem found mid-change had nowhere to go
but a sentence in a window that was about to close.

After: the flow is eight lines of bash in the brief, and a coupling problem becomes an issue on
`Scalo-Sales-Engineering-Consulting/claude-marketplace` at the moment it is found, shaped by a
form that asks for the evidence while it is still in hand.

## How it works now

Every change cuts a branch — `/forge:sdd` cuts its own, `sdd/<record>`; anything else is cut by
hand — runs `./scripts/check.sh`, stages explicit paths, pushes and opens a pull request. A draft
is enough and is the point: it is what buys CI. `gh pr checks --watch` blocks until every check
settles and exits non-zero if one failed; on green the merge is a squash and the branch goes.
After the merge the change record takes the SHA, because nothing polls GitHub.

When the fix belongs to the plugin, one `gh issue create --label from-template` files it against
the marketplace, with the title prefixed by the stack name from `.specconf/stack.json` § `name`
and the body shaped by the form committed there. The URL is then cited in the pull request and in
the record.

## What it means for the process

Nothing about running the process moves: no stage, no gate, no skill and no profile key changes.
What changes is what an agent is told at session start — that the trunk is never committed to,
that the process stops at the pull request URL and the watch and the merge are the operator's, and
that a coupling problem is filed rather than worked around.

## What it does not change

The one-way dependency stands exactly as it was, and this change restates it rather than relaxing
it: nothing under `scripts/`, `tests/`, `pyproject.toml` or `conftest.py` calls the process,
imports it or names its files. An issue is a report, not a call.

`spec/constitution.md` is untouched — changing an article needs an ADR, and these are operating
rules that cite Articles IV and XII rather than replace them. No script, workflow, gate or
`.specconf/` file moves, and `CI passed` is not made a required check: that is a plan upgrade,
not a workflow edit.

Nothing is enforced by machinery. A pre-commit guard refusing a commit on the trunk was considered
and rejected for this change: `git commit --no-verify` walks past a local hook exactly as it walks
past `lint.sh` today, so it would have been an accelerator described as a gate.

## How it was verified

`./scripts/changelog.sh check --base main` and `sdd-specs` — the second because the content gates
read the whole tree, and `backtick-paths`, `english` and `documentation-set` all bite on prose of
exactly this kind. `backtick-paths` earned its place: on the Flutter template it failed the first
draft of the same prose on two paths that live in another repository and so read as if they were
local, and both templates now write them fully qualified.

`./scripts/check.sh` was not run: the diff is two Markdown files, touching no Python, no
TypeScript, no test, no migration and no script, and the gates above are the ones that can say
anything about it. CI runs the rest on the pull request.

The `gh issue create` in the new section was not rehearsed — the installed `gh` (2.100.0) has no
`--dry-run` for it, and a rehearsal would file a real issue. Its three preconditions were confirmed
instead: the `from-template` label exists on the marketplace, issues are enabled there, and the
token carries `repo` scope.

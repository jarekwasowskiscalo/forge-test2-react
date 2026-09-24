---
date: 2026-09-23
branch: process/runner-mode-probe-for-evidence-digest
pr: 77
kind: process
---

# Record the runner's file mode as the probe the evidence digest now sees

## What changed

- `spec/rationale/AUDIT-2026-09-23-evidence-digest-and-file-mode.md` — new, dated. The
  measurement of `chmod 755 → 644` on `scripts/test.sh` against five observers: `git status`,
  `git ls-files -s`, `./scripts/hygiene.sh`, and the engine's `git.content_digest()` on forge
  `0.1.76` and on forge `0.1.117`. It carries the reproduction, where the engine reads the
  digest, the two assertions of `#68 §11` with today's answer to each, and what this
  repository deliberately does not do.
- This entry.

## Why

Audit ticket E1-06 found that the evidence digest, built from git blob hashes, could not see a
mode change: a runner stripped of its exec bit left the digest byte-identical while
`git status` reported it modified, so a gate verdict stayed "fresh" over a tree on which the
gate could no longer run. The fix is the engine's
(Scalo-Sales-Engineering-Consulting/claude-marketplace#193, closed 2026-09-21); this
repository's share is the material the defect is visible on — `scripts/test.sh`, the file
`.specconf/stack.json § scripts` binds to `test` — and the check that the fix holds here
(`#68`, epic `#58`).

## From what, to what

- **Before:** the probe existed only as a reproduction in the audit and in
  `forge-template-flutter#82`, measured on the other stack before the fix. Nothing in this
  repository said whether the engine it runs under sees a runner's mode.
- **After:** a dated record in `spec/rationale/` says it, measured on this tree: forge
  `0.1.76` is blind (`1d6625a3…` before and after), forge `0.1.117` is not (`5de94ed1…` →
  `81378c59…`, and back on restore).

## How it works now

The digest the engine binds a gate verdict to hashes each path's mode beside its blob. A
`chmod` on `scripts/test.sh` changes it; restoring the mode restores it; committing identical
content leaves it alone. Anyone doubting that on a later engine re-runs the block in the
rationale document — and first checks the digest is 64 hex characters, because two empty
answers compare equal.

## What it means for the process

None — nothing about running or changing this repository moves. The rationale document is the
statement a reader checks the engine against when it next changes how the digest is built.

## What it does not change

- `scripts/test.sh` — untouched, by `#68 §13`; its value here is that it is ordinary.
- `scripts/hygiene.sh` — its exec-bit check reads the **committed** mode and stays that way; it
  is not a substitute for the engine's digest and nothing here makes it one.
- No test was added: nothing under `scripts/`, `tests/`, `pyproject.toml` or `conftest.py`
  reads the process, so a test of the engine's digest cannot live here.
- `.specconf/`, `spec/` outside `rationale/`, the application — unchanged.

## How it was verified

- The reproduction, on forge `0.1.76` and `0.1.117` in turn, at `2387476`: the table in the
  rationale document. `git status --porcelain` was empty after the restore.
- `#68 §11` assertion 2 — a commit of identical content does not move the digest — measured on
  this pull request's first commit, with its own two files as the uncommitted work
  (forge `0.1.117`): **holds**. The digest read
  `cec492d56fca69868d740994a85696c412ac5144596fa7a1bf1070c1a74b8374` with both files
  untracked, the same after `git add`, and the same after the commit `aa65015`.
- `./scripts/changelog.sh check --base origin/main`, `sdd-specs` and `./scripts/check.sh`
  locally; CI on the pull request.

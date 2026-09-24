# AUDIT 2026-09-23 — the evidence digest and a runner's file mode

**This document is dated and is not edited after the fact.** It describes the tree, and the
engine standing over it, on the day of the measurement. Where it names a line number in the
forge plugin, it names the version it read.

**What it is for:** `scripts/test.sh` is this repository's whole share of audit ticket E1-06.
The defect was the engine's; the material is ours. This is the material, written down — the
probe, what the engine answered before
[claude-marketplace#193](https://github.com/Scalo-Sales-Engineering-Consulting/claude-marketplace/issues/193),
and what it answers now that the fix has landed.

**Tickets:** `forge_template_python_react#68` (this half) · `claude-marketplace#193` (the
engine's half, closed 2026-09-21) · epic `forge_template_python_react#58`. The same probe on the
other stack: `forge-template-flutter#82`, recorded there before the fix.
**Source:** `audyt_finalny/tikety/EPIK-1-sterowanie.md § E1-06`.

## What was measured

- **Repository:** `forge_template_python_react`, at `2387476`, clean worktree.
- **Engines:** forge `0.1.76` (the version the audit reproduced on, still in this machine's
  plugin cache) and forge `0.1.117` (the version enabled that day, carrying the #193 fix).
  Both read the same tree, one after the other, for every step.
- **The single action:** `chmod 755 → 644` on `scripts/test.sh`, and nothing else. No byte of
  the file changed; `wc -c` reads 17486 before and after.

Five observers were asked the same question — *did anything move?*

| observer | answer after `chmod 644` | what it read |
|---|---|---|
| `git status --porcelain scripts/test.sh` | ` M scripts/test.sh` | the worktree against the index |
| `git ls-files -s scripts/test.sh` | `100755`, unchanged | the index alone, which an unstaged `chmod` does not touch |
| `./scripts/hygiene.sh` | exit **1**, `warning: test.sh does not answer --help` | the consequence — a script that cannot be executed cannot be asked |
| `git.content_digest()`, forge `0.1.76` | `1d6625a3097f323f2d8bfe2e63b13010f8830092d074b770327d82ad29b4a441` **before and after** | git blob hashes, which do not encode a mode — **blind** |
| `git.content_digest()`, forge `0.1.117` | `5de94ed1c0b9fa722e21cda46784c07455360fd29efd509a84e4039b0092651b` before, `81378c593be1bc23284df0b1f972b45bf9136f4ed21f31a3948930af89191d9f` after | the blob hash **and** the mode beside it — **sees it** |

Restoring the mode returns every observer to its first answer: `git status` prints nothing,
`hygiene.sh` exits 0, and forge `0.1.117` reads `5de94ed1…` again — the digest follows the
mode both ways, so it is a function of the tree and not a counter of events.

**The finding, in one sentence:** before #193 the proof meant to be stronger than
`git status` was the only observer that could not see the change; with #193 it sees it, and
the repair costs this repository nothing.

## Why `scripts/test.sh` and not some other file

Because it is the file whose mode decides whether a gate can produce any evidence at all.

`.specconf/stack.json § scripts` binds the script contract's `test` entry to
`scripts/test.sh`, and the engine calls it per suite with the junit path the suite declares.
Every suite in `§ suites` is reached through it, and the RED proof, the flaky re-run and the
baseline all read the junit it writes — the engine reads that file and never what a tool
returned. Strip the executable bit and none of that can happen: the runner cannot start, so no
junit exists, so there is no evidence to be fresh about.

A document losing its exec bit is untidy. A runner losing it changes the outcome — and an
identity that guards outcomes has to see every change that can alter one.

`scripts/test.sh` is also the file the audit and `forge-template-flutter#82` reproduced on, so
the three records name the same probe and a reader comparing them compares like with like.

## Where the digest is consumed

In forge `0.1.117`, `content_digest` is defined at `skills/_shared/sdd/git.py:241`, and its
docstring now names #193 and says the mode is hashed beside the blob. It is read where work is
accepted:

| site | the question it asks |
|---|---|
| `skills/_shared/sdd/gate.py:1433` and `:1469` | taken before the first gate and after the last: *did this run judge one tree, or two?* |
| `skills/_shared/sdd/gate.py:809-816` | does a banked baseline still describe the tree it is compared against? |
| `skills/_shared/sdd/close_stage.py:705-726` | the most accurate freshness key: *does this green verdict still describe the tree being closed?* |
| `skills/_shared/sdd/loop.py:1302` | may a banked report be reused instead of re-run? |

Before the fix, a runner de-executed between a gate run and any of these reads left the pair of
digests equal, so each of them accepted a verdict over a tree on which that verdict could not
have been produced.

## The reproduction

Run from the repository root. It restores the mode at the end; run the restore by hand if you
interrupt it.

```bash
PY=<plugin>/skills/_shared            # e.g. ~/.claude/plugins/cache/scalo/forge/<version>/skills/_shared

D1=$(PYTHONPATH=$PY python3 -c 'from sdd import git; print(git.content_digest())')
chmod 644 scripts/test.sh
D2=$(PYTHONPATH=$PY python3 -c 'from sdd import git; print(git.content_digest())')

echo "$D1" | grep -Eq '^[0-9a-f]{64}$' || echo 'NO ANSWER -- the module did not import'
[ "$D1" = "$D2" ] && echo 'IDENTICAL -- the digest is blind to the mode change'
git status --porcelain scripts/test.sh    # ' M scripts/test.sh' -- git is not
./scripts/hygiene.sh; echo "hygiene exit=$?"   # 1 -- this repository is not either

chmod 755 scripts/test.sh                 # restore
```

**Check that `D1` is 64 hexadecimal characters before believing the comparison.** Two empty
strings compare equal, and the audit's first attempt announced a match that was only a failed
import. An empty digest is *no answer*, and every caller in the engine treats it as such.

## The two assertions, and their answer on 2026-09-23

They are the acceptance criteria of `#68 §11`, and they pull in opposite directions on
purpose — a fix that satisfied the first by hashing anything other than content would break
the second.

1. **`chmod` on the runner invalidates the proof.** Forge `0.1.117`: **holds** — `D1 != D2`,
   measured above. Forge `0.1.76`: fails, which is the defect as the audit found it.
2. **A commit of identical content does not invalidate it.** Digest a tree with uncommitted
   work, commit exactly that work, digest again: the two agree. Measured on the first commit of
   the pull request that adds this document, whose own two files were the uncommitted work; the
   values are in its `changelog/` entry, because a file cannot carry the digest of a tree that
   contains it.

## What this repository deliberately does not do

**It does not compensate.** No guard is added here that would make an engine's blindness
harmless, because a template that quietly covers for the process makes the process's defect
unmeasurable — and `#68 §13` refuses it in as many words. The dependency runs one way: nothing
under `scripts/`, `tests/`, `pyproject.toml` or `conftest.py` names the process, so a fitness
test that watches the digest could not be written here even if it were wanted.

**It does not edit `scripts/test.sh`.** The file's value in this ticket is that it is ordinary.

**`scripts/hygiene.sh:128-134` is left as it is.** It refuses any `scripts/*.sh` **committed**
as something other than `100755`, and it reads the index, so it answers about the commit and is
silent on a worktree whose mode drifted since. It is not the missing guard; the window between
a commit and a gate run was the engine's to close, and #193 closed it.

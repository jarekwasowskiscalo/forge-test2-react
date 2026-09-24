---
date: 2026-09-16
branch: fix/macos-argv0-probe
pr: 52
kind: fix
---

# Name a process by a path no interpreter can rewrite

## What changed

`tests/tooling/test_app_status.py`, one test — `test_a_long_executable_path_is_not_truncated_into_a_command_name`.
It used to start the real interpreter under a borrowed `argv[0]`
(`subprocess.Popen([str(stranger), "-c", ...], executable=sys.executable)`). It now
**symlinks** the long path to `sleep` and runs that, so the long name is in the path
actually executed rather than in an argument a runtime may replace. `shutil` joins the
imports; nothing else moves.

## Why

`macos-latest` was **red on the trunk** — runs `35141839707` and `35146006445` on
`main`, both on this one assertion, with `command` coming back as `Python` rather than
`lonelyserver3`.

`argv[0]` is whatever the caller says it is, until the interpreter re-execs itself. A
macOS **framework** build does exactly that, through
`Python.app/Contents/MacOS/Python`, and overwrites `argv[0]` on the way. Which build
you get is a property of the machine: `uv sync` on the macOS runner reports
`Using CPython 3.14.7 interpreter at: /opt/homebrew/opt/python@3.14/bin/python3.14` —
Homebrew's framework build — while a developer's uv-managed interpreter is a plain
Mach-O executable that rewrites nothing. So the test passed on every workstation and
failed on the only machine that is not one.

The cross-platform leg runs weekly, on the trunk, on a pull request carrying the
`cross-platform` label, or when `.github/` itself changes. That is why the trunk
carried the red without anybody's pull request going red for it — it took a change to
CI (#51) to run the leg and surface it.

## From what, to what

**Before:** the long name lived in `args[0]` and the process ran `sys.executable`. A
framework interpreter replaced `argv[0]` and the assertion read the app bundle's own
name. Green on a workstation, red on the runner, for a reason neither machine printed.

**After:** the long name lives in the path that is executed. `ps -o args=` reports
`…/sixteen/lonelyserver3 30` whatever interpreter the machine happens to ship, because
no interpreter is involved.

## How it works now

The test makes `<tmp>/a/very/long/path/past/sixteen/lonelyserver3` a symlink to
whatever `shutil.which("sleep")` finds, starts it, and asks `app_status._process_facts`
what `ps` says. The subject is unchanged: `command` must be `lonelyserver3` and not a
sixteen-character slice of the path, which is the defect `app_status.py` stopped having
when it read `args` instead of `comm`.

Two alternatives do **not** work and the docstring says so, so the next person does not
spend the afternoon finding out: a copy of a signed system binary will not start on
macOS at all, and a `#!` script puts the interpreter in `argv[0]` — `ps` reports
`/bin/sh <path>`, which is the same defeat by a different route.

## What it means for the process

Nothing moves. No script, no gate, no workflow changes.

Worth carrying forward: a test that pins how a **process** presents itself is testing
the machine as much as the code, and `sys.executable` is not one thing across machines.

## What it does not change

`scripts/app_status.py` is untouched — it was right. It reads `args` rather than the
truncated `comm`, and this repair defends that rule instead of weakening it. The
assertion was **not** loosened to accept `Python`: that would have retired the rule
rather than tested it.

The cross-platform leg's trigger is unchanged. It still runs weekly, on the trunk, on a
labelled pull request and on a change to `.github/` — this entry is not an argument for
running it on every pull request, which `spec/design/testing.md` prices at 10× a Linux
runner.

## How it was verified

`./scripts/test.sh tooling` — 315 passed. `./scripts/lint.sh` OK.

The new form was probed directly before it was written: with the symlink,
`app_status._process_facts` returns `command='lonelyserver3'` and an argv carrying the
whole path. The two rejected forms were probed too — a `#!/bin/sh` script returns
`command='sh'` with argv `/bin/sh <path>`.

**Named gap:** the failing condition could not be reproduced on this workstation —
Homebrew's `python@3.14` is not installed here, and the uv-managed interpreter
(`cpython-3.14.7-macos-aarch64-none`, a plain Mach-O) passes the OLD test too. The
evidence for the mechanism is the runner's own log, which names the interpreter, plus
the observed value `Python`. The proof that the repair holds on the runner is the
`macos-latest` leg of this pull request.

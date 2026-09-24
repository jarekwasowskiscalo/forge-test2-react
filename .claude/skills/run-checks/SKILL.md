---
name: run-checks
description: Use when the user asks to test, lint, type-check or verify sdd-app-template - "test the application", "run the tests", "check that it works", "validate it", "check before commit", "will CI pass", "is the machine ready", "preflight", "fix the formatting". Runs the project's own scripts; do not assemble pytest/vitest/ruff/mypy/eslint commands by hand.
---

# Test and check the application

Every operation is a script in `scripts/`. Run the script and report what it
says. Do not reconstruct the underlying commands — each script also checks the
prerequisites, and those checks exist because their absence produced buried
failures that cost a day each.

`scripts/help.sh` lists everything available.

**Measured.** Every command you run under this skill is read by the session audit: this
conversation's own window is inside its scope, and a command assembled by hand instead of the
script that wraps it is counted there by name. What it counts, and what to do when the process
itself is the thing in your way:
[`${CLAUDE_PLUGIN_ROOT}/skills/_shared/process-failure.md`](https://github.com/Scalo-Sales-Engineering-Consulting/claude-marketplace/blob/main/plugins/forge/skills/_shared/process-failure.md).
This is the half of a session that can file, so a fault met here is filed when it is met rather
than at the end of the session — the `fault-report` skill does it.

## Pick the script from what was asked

| The user wants | Run |
|---|---|
| all the tests | `./scripts/test.sh` |
| the Python tests | `./scripts/test.sh backend` |
| one Python test | `./scripts/test.sh backend -k <expression>` |
| the frontend tests | `./scripts/test.sh frontend` |
| the e2e suite | skill `run-e2e-tests`, or `./scripts/test.sh e2e` |
| tests without Docker, quickly | `./scripts/test.sh --no-db` (only the tests that need no database) |
| ...without Docker and without skipping anything | set `APP_TEST_DATABASE_URL` to a Postgres that exists, then `./scripts/test.sh backend` |
| linting and types | `./scripts/lint.sh` |
| formatting fixed | `./scripts/lint.sh --fix` |
| "will CI pass?", "validate everything" | `./scripts/check.sh` |
| the same, quickly | `./scripts/check.sh --fast` |
| the same, on a machine with no Docker | `./scripts/check.sh --no-docker` |
| "is this machine ready?", "preflight" | `./scripts/preflight.sh` (bare machine: `python3 scripts/preflight.py`) |
| "what is running right now?" | `./scripts/status.sh` (or skill `run-app`) |

`check.sh` is the one to run before a commit or a push: it is every gate CI
runs, in one command. It takes several minutes because it includes the Docker
image and the e2e suite; `--fast` skips those two and is the right choice
mid-edit, not before pushing.

**`--fast` is not a no-Docker mode.** It deselects the image and e2e, but the
backend gate still needs a database. `--no-docker` is the mode for a machine with
no daemon: it runs every gate that can honestly run, names the ones that could
not, and **exits 4 (INCOMPLETE)** rather than 0. Report that as what it is -- a
run with gates missing, never as a pass. With `APP_TEST_DATABASE_URL` set the
same flag runs the backend gate in full, and only the image and e2e stay out.

Exit codes from `check.*` and `hygiene.*`: `0` everything ran and passed, `1`
something ran and failed, `4` everything that ran passed but something did not
run.

## Reporting the result

State the counts and the outcome plainly. If something failed, quote the actual
failure — the assertion, the type error, the lint rule — rather than
paraphrasing it, and say which gate it came from.

`check.sh` runs every gate even when an early one fails and lists the failures
at the end, so one run gives the whole picture. Do not stop at the first
failure and re-run.

## Two things that make a green run meaningless

- **A stale application process.** The e2e suite drives whatever is listening
  on :8080. If that is a server from an earlier session it is serving the old
  build, and the suite will happily report success. `test.sh e2e` starts its
  own application when nothing is up, but it cannot tell a *stale* one from a
  current one. After changing backend code, restart before trusting an e2e run.
- **Reporting a suite that did not run.** A skipped suite is not a passing
  suite. If Docker was unavailable and the backend tests were skipped, say so.

## Related

- Running the app: skill `run-app`.
- Regenerating the committed contracts after an API change:
  `./scripts/generate.sh`, then commit what it changed.

---
name: run-e2e-tests
description: Use when the user says "run the e2e tests" / "run e2e" / "fire the black box" for sdd-app-template - runs the black box (BDD scenarios plus the Playwright UI smoke, one junit) against a live application and reports the result per scenario with timings, not just the aggregate counts. For unit tests or a pre-commit check use the run-checks skill instead.
---

# Run the E2E tests

```bash
./scripts/test.sh e2e
```

That is the whole run, and it takes no flags. The
script checks that both black-box trees collect (`e2e/suite` scenarios and the `e2e/ui`
smoke), builds the SPA if `app/static/index.html` is missing, installs Chromium if it is
not there yet, starts the application if nothing is answering on :8080, waits for it,
runs both trees into one junit, runs the scenario census against that report, and stops
the application again if it was the one that started it. The JUnit report path lives in
the script, so there is nothing to pass and nothing to keep in sync.

`./scripts/test.sh ui` runs the UI smoke alone — same prerequisites, faster loop.

Everything after `e2e` is forwarded to `pytest`, so `-k`, `-x` and `-v` work.

Do not assemble the `TARGET_BASE_URL` and the `DATABASE_URL` by hand. The
default target already carries the `/api` prefix, and getting that wrong makes
every scenario fail at once on a 405 that names nothing — it cost this suite
five days once.

**Measured.** Every command you run under this skill is read by the session audit: this
conversation's own window is inside its scope, and a command assembled by hand instead of the
script that wraps it is counted there by name. What it counts, and what to do when the process
itself is the thing in your way:
[`${CLAUDE_PLUGIN_ROOT}/skills/_shared/process-failure.md`](https://github.com/Scalo-Sales-Engineering-Consulting/claude-marketplace/blob/main/plugins/forge/skills/_shared/process-failure.md).
This is the half of a session that can file, so a fault met here is filed when it is met rather
than at the end of the session — the `fault-report` skill does it.

## Report per scenario, not just the totals

`pytest`'s own summary line gives `N passed`. That is too thin to report back on
its own. Two ways to get more:

```bash
./scripts/test.sh e2e -v --gherkin-terminal-reporter
```

prints each scenario with its steps as it runs. Or read the attributes out of
`e2e/reports/junit.xml`, which the run always writes:

```bash
grep -oE '<testcase[^>]*name="[^"]*"[^>]*time="[0-9.]*"' e2e/reports/junit.xml
```

**Do not `Read` that file.** A `<failure>` element carries the assertion message,
which can name a real field value, and reading the whole file floods the
context for no benefit. There is no `<system-out>` in it — pytest writes none and
`junit_logging = "no"` is pinned in `pyproject.toml` to keep it that way.

Present one table: every scenario with its status and duration, then the total.
Scenario names in the report are pytest-bdd's mangling of the title
(`test_paging_through_cases_never_shows_the_same_case_twice`); turn the
underscores back into spaces when you present them. A `<testcase>` carries no
`status` attribute — the outcome is whether it has a `<failure>`, `<error>` or
`<skipped>` child.

If something failed, pull the assertion for that scenario from pytest's own
output, and read the application's side of the story from the logs the run
leaves behind: `.sdd/logs/e2e-app.log` (the app the script started) and
`.sdd/logs/app.log` (its DEBUG log). Both obey the no-personal-data rule —
identifiers and counts — so quoting their last error back is safe and usually
names the cause faster than the assertion does. Re-run with `-s` only when a
failure genuinely needs the raw HTTP exchange to diagnose — and remember that
exchange contains personal data, so do not paste it back wholesale.

## A green run against a stale server proves nothing

The suite drives whatever is listening on :8080. If that is an application
process from an earlier session, it is serving the previous build and the suite
will report success anyway — that has happened here. After changing backend code,
restart the application (`./scripts/stop.sh`, then let `test.sh e2e` start a
fresh one) before trusting the result.

The suite now notices one shape of this by itself: after emptying the database it
asks the application whether it agrees, so an application pointed at a *different*
database fails with a sentence saying so rather than with twenty-one wrong counts.

## The suite's own guards

Different, faster, and needing neither a live application nor Docker — these test
the harness and the scenarios rather than the domain. They are ordinary pytest
files, so they are already part of:

```bash
./scripts/test.sh backend
```

`tests/tooling/test_e2e_harness.py`, `tests/fitness/test_e2e_isolation.py` and
`tests/fitness/test_e2e_scenarios.py`. The last one is the replacement for
`behave --dry-run`: it proves every step of every scenario resolves to a
definition. If it fails, no scenario will pass and there is no point starting an
application.

## Related

- Everything else: skill `run-checks`, or `./scripts/help.sh`.
- What the suite proves and why it is built this way: `spec/design/testing.md`.
  Do not read it for a routine run — only when something above no longer matches
  reality.

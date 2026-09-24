---
date: 2026-09-17
branch: process/answer-allowed-skips-for-every-suite
pr: 57
kind: process
---

# Answer allowed_skips for every suite, and keep the answer true

## What changed

- `.specconf/stack.json` § `suites` `$comment` — records the answer and the measurement
  behind it: no suite declares `allowed_skips`, which suite skips what, and what would have
  to change upstream before that answer does. **No `allowed_skips` key is added anywhere.**
- `tests/fitness/test_gate_parity.py` — four assertions that keep the answer true as the
  tests change, plus the module docstring's third bullet and the `ast` import they need.
  `SUITE_SOURCES` maps each declared suite to the tree its cases live in; a skip is found by
  walking the syntax tree for `pytest.skip` / `pytest.mark.skip` / `pytest.mark.skipif` and
  by reading comment-stripped TypeScript for vitest's `.skip` / `.todo` / `.skipIf`.

## Why

`claude-marketplace#113` split the gate's counting into cases **collected** and cases
**executed**. A suite that collects cases and executes none is now `ERROR` unless the run is
degraded or the suite declared its skips under `suites.<name>.allowed_skips`. The engine filed
one follow-up per template asking each to declare the key for the suites that really skip;
ours is [#33](https://github.com/Scalo-Sales-Engineering-Consulting/forge_template_python_react/issues/33),
and it asks a question rather than asserting an answer.

Measuring before declaring is what made the answer *no*. The key buys a suite one thing and
costs it another (`stack.py:344-350`): a blackout stops being a wrong record, and in exchange
**any** run in which that suite skipped anything is filed as incomplete. `_skip_gaps`
(`gate.py:1083-1103`) reads the junit's `skipped` total and nothing finer, so a suite is
charged for every skip it has and not only for the kind its declaration names.

For this stack that trade is one-sided in both directions:

- **It buys nothing.** The backend suite cannot black out. `tests/unit/`, `tests/fitness/` and
  `tests/tooling/` each mark everything below them `no_db`, so `--no-db` always leaves the
  greater part of the suite executing — and the one profile that runs without a database,
  `unit-no-db`, is degraded, where `gate.py:1172-1173` already excuses every suite with no
  declaration at all. `frontend` and `e2e` skip nothing, so they have nothing to declare.
- **It would cost the delivery boundary.** A `full` run with Docker and a database skips 24
  cases that have nothing to do with a missing database: 23 in
  `tests/unit/test_entry_text_rules.py`, where only an `accepted` corpus case carries a
  length, and one in `tests/unit/test_log_content_policy.py`, where alembic's `fileConfig` has
  replaced the root handlers by the time it runs. Declaring would file every green run
  incomplete under a sentence false about all 24, and `close_stage._refuse_partial_delivery`
  refuses a boundary on exactly that list when a run carries no classified gaps — which a
  clean `full` run never does.

Filed upstream as
[claude-marketplace#140](https://github.com/Scalo-Sales-Engineering-Consulting/claude-marketplace/issues/140),
because the rule, the counting and the refusal are all engine-side and this repository never
patches the plugin. Until it lands, the answer stands and nothing here declares the key.

`forge-template-flutter#46` is the same follow-up and was closed the same way
([its PR #59](https://github.com/Scalo-Sales-Engineering-Consulting/forge-template-flutter/pull/59)):
the answer in the profile's comment, no key, and a fitness test so the comment cannot rot. The
reasons differ — nothing skips over there, and our backend suite skips on every run — so the
guard differs with them.

## From what, to what

**Before.** `.specconf/stack.json` was silent about `allowed_skips`. Silence and a decision
read identically, so the next person to meet #33 would have re-derived the measurement, or —
worse — taken the issue's proposed form at face value and declared. Nothing in the repository
would have stopped them: the key loads, the profile stays valid, the local gates stay green,
and the failure arrives at somebody's delivery boundary weeks later.

**After.** The profile says no, per suite, with the numbers and the date it was measured,
and names the upstream issue that has to land before the answer is worth re-asking. Four
assertions fail the moment the measurement stops being true.

## How it works now

`.specconf/stack.json` § `suites` carries the answer. `tests/fitness/test_gate_parity.py`
holds it to the repository's own sources, in four directions:

- a suite in the profile that this module does not map fails, so a new suite must say where
  its cases live before the other three can be trusted to cover it;
- a suite that declares `allowed_skips` and cannot skip fails — the declaration would name
  nothing and would only change how a blackout reads;
- `backend`, recorded as skipping, must still skip: if every skip goes away it could afford
  the key after all, and that is a decision to re-make rather than a test to delete;
- `frontend` and `e2e`, recorded as skipping nothing, must still skip nothing.

Which suites are in which half is one constant, `RECORDED_AS_SKIPPING`. Detection reads the
Python syntax tree rather than the text, so a `skipif` named in a docstring —
`tests/tooling/test_preflight.py`, `e2e/suite/conftest.py` — is not a false positive; the
TypeScript half strips comments first and replaces them with the newlines they spanned, so a
reported line number is still the line in the file.

## What it means for the process

Nothing today. No suite declares `allowed_skips`, no gate changes colour, and no run changes
its exit code. The engine's blackout rule applies to this stack exactly as it did yesterday.

What changes is the next conversation: adding a `skip` to the frontend or the black box, or
removing the last one from `tests/`, now fails a fitness test that says which decision has to
be re-made and where it is written down.

## What it does not change

- **No application behaviour.** Nothing under `app/`, `frontend/src/`, `alembic/` or
  `golden-set/` moves, and no test is added to or removed from a product suite.
- **No suite's `args`, `no_db_args`, `needs`, `junit` or `isolate` moves**, and no script, CI
  workflow or `spec/` document is touched.
- **The 23 corpus skips stay.** Filtering `test_entry_text_rules.py`'s parametrisation to
  `accepted` cases would be a real improvement and would cut a full run's skips from 24 to 1 —
  but one skip still refuses delivery, so it does not make declaring safe, and #33's scope is
  the profile plus a sentence in `test_gate_parity.py`. Named here as a follow-up rather than
  done quietly.
- **`tests/unit/test_log_content_policy.py` keeps its skip.** It is load-bearing: the test
  proves the *live* sink carries the policy filters, and reconfiguring logging to avoid the
  skip would reduce it to the declaration test one function above it.

## How it was verified

`./scripts/check.sh` — **OK**, every gate including the black box (52 e2e items, 213 frontend
tests, the production image). It needed `POSTGRES_HOST_PORT=5822` on this machine: containers
from sibling worktrees hold 5432 and everything up to 5732, which is a fact about the laptop
and not about this change.

`./scripts/lint.sh` — **OK** (ruff, ruff format over 171 files, mypy --strict over 113 source
files, eslint, tsc). `sdd-specs` — **OK**, 0 problems over 269 documents.
`./scripts/changelog.sh check` — OK.

**The 24 was measured, not inferred.** That same `check.sh` run reports `979 passed, 24
skipped` for the backend suite with Docker and a database. `./scripts/test.sh unit -rs` — which
runs under `--no-db`, where the logging test does *not* skip — reports `234 passed, 23 skipped`,
every one of them `tests/unit/test_entry_text_rules.py:96: only an accepted case carries a
length`. 23 + 1, exactly as the profile comment says.

All four new assertions proved to bite, by hand, every mutation reverted:

- `allowed_skips` on `suites.frontend` → *"suites.frontend declares allowed_skips ['a skip
  that does not exist'] and nothing under frontend/src/ skips"*;
- an `it.skip(...)` in a file under `frontend/src` → *"records frontend as skipping nothing,
  and it now skips at: frontend/src/…:4"*;
- `frontend` added to `RECORDED_AS_SKIPPING` → *"nothing under frontend/src/ skips any more,
  and .specconf/stack.json § `suites` rests on the opposite"*;
- a fourth suite added to the profile → *"the profile declares ['backend', 'e2e', 'frontend',
  'smoke'] and this module maps ['backend', 'e2e', 'frontend']"*.

**Not run:** nothing that would exercise `allowed_skips` itself, because nothing declares it.
The engine-side claims in this entry were read off forge 0.1.62 — the version installed on
this machine — and are cited by file and line in claude-marketplace#140.

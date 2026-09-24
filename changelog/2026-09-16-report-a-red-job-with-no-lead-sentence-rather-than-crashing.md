---
date: 2026-09-16
branch: fix/ci-summary-empty-lead-crash
pr: 36
kind: fix
---

# Report a red job with no lead sentence, rather than crashing the reporter

## What changed

- `scripts/ci_summary.py` — in `render_checks`, the failed-job lead guards the context
  sentence with a conditional instead of multiplying by `bool(context)`.
- `tests/tooling/test_ci_summary.py` — a new
  `test_a_red_job_renders_whether_or_not_it_has_a_lead`, parametrised over every job id
  in `_CHECKS` and one that is in none of them, on both `failure` and `cancelled`.
- `spec/changes/EXEMPTIONS.md` — one dated row, `operations-doc` over
  `scripts/ci_summary.py`, expiring 2026-09-30.

One line of behaviour, twenty-four of test, and a row that says why the third file is not
a page under `docs/`.

## Why

On 2026-09-16, run 35088488387, the job *A change outside the process leaves a record*
refused a pull request that carried no changelog entry — correctly, which is the point.
The `Summary` step that reports the refusal then died with `IndexError: string index out
of range`, so the page a reader opens to find out **which** check refused carried a Python
traceback where the verdict belongs.

The guard was written as a multiplication:

```python
+ f". {context[0].upper() + context[1:]}." * bool(context)
```

`bool(context)` is applied to the **result** of the f-string, and an f-string is
interpolated before anything multiplies it. So `context[0]` was indexed on every red job,
whether or not there was a `context` to index, and `"" * 0` never got the chance to be the
empty string it was written to be. The same file gets it right eleven lines above, in the
success branch: `(f", {context}." if context else ".")`.

`_CHECKS_LEAD` carries a sentence for four of the seven jobs in `_CHECKS`. The three
without one — `changelog`, `frontend`, and any job id the workflow renames out from under
the table — crashed the moment they went red, and only when they went red: the success
branch was always correct, so the fault was invisible on a green run and waited for the
one run where the report was worth reading.

## From what, to what

**Before.** A red `changelog` or `frontend` job rendered a traceback instead of a summary
block. A red `quality`, `scripts`, `image` or `cross-platform` job rendered correctly. No
test covered the difference, because `_every_block` builds its checks block from `quality`,
`infra` and a skipped `cross-platform` — three job ids that all take a path around the
line.

**After.** Every job id renders a block on every result. A job with no lead sentence gets
the count and a full stop — `0 of 1 check passed, 1 never reached.` — and then its table,
which is the part that names the check that refused.

## How it works now

`render_checks` builds the lead for a failed job from three pieces: how many of the
declared checks passed, how many were never reached, and the job's sentence from
`_CHECKS_LEAD` if it has one. The third piece is now conditional in the same shape as the
success branch, so a job with no sentence ends its lead with a full stop rather than
indexing position zero of nothing.

The step is unchanged in every other respect. It still reads step **outcomes** and never
step logs, and it still cannot fail a build: `census` remains the only thing in the module
that returns a non-zero code, and `test_only_the_census_can_return_non_zero` still holds it
there.

## What it means for the process

Nothing about running or changing this repository moves: the change is inside the reporter,
and the reporter is a step the workflow already runs with `if: always()`.

One thing is owed rather than changed. `operations-doc` refuses a change to
`trees.operational` that leaves `docs/` untouched, and that tree names all of `scripts/`.
`ci_summary.py` is in it without being of it — it writes a job summary on a GitHub Actions
runner and runs nowhere else, so no page under `docs/` describes it and none was made stale
here. The gate's own second escape, *say in the delta fragment that nothing operational
changed*, does not exist on the trunk: a repair here writes an entry in this directory and
has no change record to carry a fragment. So the route taken is the register's — one dated
row in `spec/changes/EXEMPTIONS.md`, narrower than the `spec-exempt` label and, unlike the
label, expiring.

**Delete the row once this has merged.** It covers one file in one pull request, and a row
left behind is a permit nobody renewed. The lasting answer is to cut `scripts/` so that
CI-only tooling is not operational, which is a change to what a gate means and belongs in
its own pull request.

## What it does not change

- **The changelog gate's own verdict.** It refused correctly on run 35088488387 and refuses
  the same way now; what changes is that the refusal is now readable.
- **The two jobs' closing sentences.** `_CHECKS_CLOSING` carries no entry for `changelog`
  or `frontend`, so their blocks still end with a table row rather than the sentence the
  house style asks for — on a green run as much as a red one. That is a separate defect
  with a separate cause (a missing constant, not a guard), and it needs prose somebody has
  to write for each job; it is not folded in here.
- **The other stack.** `forge-template-flutter` has no such line, so this repairs nothing
  there and asks nothing of it.
- **The reporter's contract.** No signature, no subcommand and no output shape moves for
  any job that already rendered.

## How it was verified

- `./scripts/test.sh tooling -k test_a_red_job_renders_whether_or_not_it_has_a_lead`, with
  `scripts/ci_summary.py` reverted to `main`: **6 failed, 10 passed** — red on exactly
  `changelog`, `frontend` and the undeclared job id, on both results, each with the
  `IndexError` at `ci_summary.py:692`. The four jobs that carry a lead passed, which is
  what says the test measures the guard and not the renderer.
- `./scripts/test.sh tooling` with the fix in place: **230 passed**.
- `./scripts/check.sh --fast`: **OK** — hygiene, lint (`ruff`, `mypy --strict`, `eslint`,
  `tsc`), infrastructure, generated-code drift, the frozen API contract, the backend suite
  on its own throwaway Postgres, the frontend suite, the frontend build and the dependency
  audit.
- The Docker image gate: **OK**, from a full `./scripts/check.sh` in the same working tree.
- `sdd-specs`: **OK** — every specification gate, the `exemptions` gate over the new row
  included, and `sdd-specs --diff-gates` against the trunk over this branch's own diff:
  **0 gates failed over 3 changed files**, where the same command before the row named
  `operations-doc`.
- `./scripts/changelog.sh check --base main`: **OK** on this entry.
- The block the crash denied a reader, rendered by hand from the failing job's own
  arguments, reads `**Failed.** 0 of 1 check passed, 1 never reached.` above the check
  table.

**Not run here, and why.** The e2e leg of `./scripts/check.sh` could not start: an
unrelated container on this workstation holds port 5432, so its Postgres refused to bind.
It is left to CI rather than taken by force from another workspace, and nothing in this
change touches the application the black box exercises. The macOS leg needs a macOS runner.
The new test sits under `tests/tooling/`, which that directory's `conftest.py` marks
`no_db`, so the macOS leg does collect it and needs no database to.

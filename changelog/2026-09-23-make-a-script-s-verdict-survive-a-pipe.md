---
date: 2026-09-23
branch: process/exit-code-survives-the-pipe
pr: 76
kind: fix
---

# Make a script's verdict survive a pipe

## What changed

- `scripts/_lib.sh`:
  - sets `set -o pipefail` of its own. It was the one file of twenty-seven that declared
    nothing;
  - gains `lists_line`, `lists_match` and the `_pipeline_answer` they share. The first two
    are the only place in `scripts/` that reads `${PIPESTATUS[@]}`;
  - `summary` prints its banner to **stderr**;
  - `ensure_db_running` asks compose through `lists_line`.
- `scripts/db.sh` — `status` asks alembic through `lists_match`. When alembic cannot answer,
  that is now an error, not advice to migrate.
- `scripts/audit.sh` — the GitHub Actions section reads the workflows first and judges them
  second, with one `grep -v` over a here-string. The four-stage pipeline is gone.
- `scripts/infra.sh`, `scripts/infra-check.sh` — `terraform version` is captured and its
  first line compared, in place of `terraform version | head -1 | grep -q`. The refusal
  check in `infra-check.sh` normalises into a variable and matches in the shell.
- `scripts/changelog.sh`:
  - `front_matter_value` is one `awk`, where it used to be `sed | head -1`;
  - the change-directory test is a here-string;
  - the added-entries filter separates grep's "no match" from a failure.
- `scripts/release.sh` — the trunk is resolved without `| sed … || true`, and the comment
  about the banner states where it goes now.
- `scripts/_install-docker.sh` — group membership is captured with `id -nG` and matched by
  word.
- New: `tests/fitness/test_pipeline_verdicts.py`, which reads the source for the rule, and
  `tests/tooling/test_pipeline_helpers.py`, which runs the shell.
- `tests/tooling/test_audit_script.py`:
  - one case added: workflows that cannot be read are not reported as pinned;
  - its banner assertions, and those in `tests/tooling/test_check_script.py`, read stderr.
- `docs/troubleshooting.md` — a section: "A script failed, and `$?` says 0".
- `spec/design/testing.md` — the fitness table gains the row for `test_pipeline_verdicts.py`,
  and the document gains a dated `Rejected (… cr: historical …)` block saying why the rule
  reads the source. The `spec_change` gate demands one for a spec edit made without a
  change record, and it turned the first CI run red until it was there.

## Why

The whole script contract is carried in the exit code: `0` did it, `1` did not, `4` did what
it could and named the gap, `2` the machine was busy, `124` it was killed. The audit of
2026-09-20 counted `PIPESTATUS` in this repository at **0** (issue #61, audit ticket E3-03,
epic #58). Nothing held the rule, and two shapes were losing an answer.

1. **A pipeline standing as a condition.** Under `pipefail`, `producer | grep -q X` is
   non-zero both when X is absent and when the producer never ran, and a condition reads any
   non-zero as "no". Ten sites had this shape:
   - `db.sh status` told an operator whose alembic could not reach the database that it was
     "behind head -- run: db.sh migrate";
   - `audit.sh` fed an empty stream to its filters when `grep -r` could not read the
     workflows. "Nothing left after filtering" is what a fully pinned tree looks like, so a
     failed read printed the coverage claim, and the new tooling case shows the old script
     exiting 0 there.

   The shape has a second failure that points the other way: `grep -q` quits at the first
   match, a producer still writing gets SIGPIPE, and `pipefail` then turns a *found* answer
   into "no". `terraform version | head -1 | grep -q` and `printf … | grep -q` over a large
   diff were both exposed to it.
2. **`|| true` over a whole pipeline** forgives the consumer's "no match" and the producer's
   failure with one token. That was the case in `changelog.sh` (the added-entries filter)
   and in `release.sh` (the trunk).

The banner moved for the ticket's second acceptance criterion: a log above 100 KB must not
push the reason for a refusal out of what a reader sees first.

This is the template's half. The engine's half — the warning where the contract is defined,
and `sdd-lint` over the plugin's shipped commands — is claude-marketplace#234 (issue #200).
The other stack's half is forge-template-flutter#84. This one follows that PR's shape, so
both templates answer the same way.

## From what, to what

| | before | after |
|---|---|---|
| `PIPESTATUS` in `scripts/` | 0 occurrences | read in `scripts/_lib.sh` only, and a fitness test keeps it there |
| a pipeline as a condition | 10 sites, each reading a failed producer as "no" | 0 outside the two helpers, and a fitness test refuses an eleventh |
| `\|\| true` over a pipeline | 2 sites | 0 |
| `scripts/_lib.sh` shell options | none | `set -o pipefail`, with the reason `-e`/`-u` stay the caller's |
| `db.sh status`, alembic cannot answer | "the database is behind head — run: db.sh migrate" | `error: alembic could not read the applied revision …`, exit 1 |
| `audit.sh`, workflows unreadable | the pin claim printed, exit 0 | `failed: the workflows … could not be read`, exit 1 |
| `lists_match` over a producer cut off after its match | n/a (the bare pipe said "no") | yes |
| the closing banner | stdout, at the far end of however large the log was | stderr, beside the reason |

## How it works now

A pipeline may answer a yes/no question in `scripts/` only through `lists_line <line>
<producer…>` or `lists_match <regex> <producer…>`. Both give three answers:

- `0` yes;
- `1` no;
- `2` the producer could not be asked.

Every caller handles the third, as `die` or `fail`, and none folds it back into "no". The
decision comes from grep's own status and the producer's, never from the pipeline's. Under
`pipefail` a producer that `grep -q` cut off with SIGPIPE (141) after a match makes the
pipeline non-zero, and the helpers read that as the yes it is.

Where a value is needed rather than a verdict, the producer is captured into a variable with
its status checked, and the variable is then tested with a here-string or a `[[ … ]]` match.
No pipe carries the verdict.

stdout is the payload and stderr is the verdict. The banner joins `warn`, `fail`, `die` and
`check.sh`'s `Failed gates:` / `Not run:` lists on stderr. So `./scripts/check.sh >run.log`
leaves the whole answer on the terminal, and a suite that printed 100 KB before failing hides
none of its answer behind that. On a terminal the two streams land together, and nothing a
person sees changes.

## What it means for the process

**None.** Every exit code keeps its meaning. `0`, `1`, `2`, `4` and `124` are untouched, and
the script-contract names and their codes are the coupling surface this repository may not
move alone. Nothing changes in junit or in the stack profile. Under `spec/` the only change
is the fitness table's new row, which `test_test_layout.py` requires, and its dated block. Anyone who reads
a script's answer from its exit code reads the same answer as before. Where a pipeline's
producer had failed, the answer is now truer.

A reader who scraped the banner from **stdout** alone now finds it on stderr. Nothing in this
repository, its workflows or the process did that. The tests that did are updated here.

## What it does not change

- **No exit code changes.** §13 of the ticket forbids them outright.
- **Pipes are not banned** (§13 again). A pipeline that produces a value is fine. What is
  refused is a verdict lost silently.
- **The workflows.** The three steps that pipe a verdict (`deploy.sh | tee`,
  `preview.sh | tee`, `release.sh | tail -1`) already declare `shell: bash`, which is
  `-eo pipefail`. The other pipes are a retry loop and a path filter whose last stage is the
  verdict.
- **Display-only pipes**: `hygiene.sh`'s version lines, and `build.sh`'s `sed` over a
  variable it already holds.
- **No timeouts** and no bounded runner.

## How it was verified

- `./scripts/test.sh fitness -k pipeline`, run **before** the scripts were touched: red on
  exactly the ten sites in the table, plus `_lib.sh` without `pipefail`, plus 0 readers of
  `PIPESTATUS`. No false positives. After the fix: 5 passed.
- `./scripts/test.sh tooling -k pipeline_helpers`: 23 passed. That covers:
  - the three answers;
  - the SIGPIPE case, which **failed on the first draft of the helpers** (they judged the
    pipeline's status) and is why `_pipeline_answer` reads grep's;
  - `0/1/2/4/124` under bash and zsh, both bare and through `set -o pipefail; … | tail -1`;
  - the known positive that without `pipefail` both shells answer for `tail`;
  - a planted 210 KB log whose reason and banner arrive on stderr in under 1 KB.
- `./scripts/test.sh tooling -k "audit or check_script"`: 12 passed. The new unreadable
  workflows case, run against `origin/main`'s `audit.sh`, **fails**, so it is not vacuous.
- The terraform probe, against a stub `terraform` on PATH: the pinned version → local, another
  version → image, a failing binary → image. There is no real Terraform on this machine.
- `./scripts/lint.sh`: OK, after `--fix` reformatted the two new test files.
- `./scripts/check.sh` on the committed tree (with `POSTGRES_HOST_PORT=5912`, because other
  worktrees' databases held 5432): `Check: OK`, exit 0, every gate run and passed. The same run
  shows the split: 16 KB on stdout, and every banner plus the verdict on stderr. The first
  run also caught `tests/fitness/test_test_layout.py` asking for the new fitness module's row
  in `spec/design/testing.md`, which this change adds, as #75 did for its own module.
- `./scripts/test.sh e2e`: 52 passed, starting its database through the new `lists_line` in
  `ensure_db_running`.
- The ticket's reproduction, after: `grep -rl PIPESTATUS scripts/` → `scripts/_lib.sh`, and
  `grep -L 'pipefail' scripts/*.sh` → empty.

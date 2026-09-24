---
date: 2026-09-16
branch: ci/declare-the-labels-ci-branches-on
pr: 45
kind: ci
---

# Create the labels CI branches on, and declare them where a test can read them

## What changed

- **Two labels created in the repository**, by hand, with `gh label create`: `no-changelog`
  (`FBCA04`, the same yellow as `spec-exempt`, because both are break-glass) and
  `cross-platform` (`1D76DB`, because it asks for *more* checking rather than waiving any).
  Neither existed. Nothing in the diff does this — a label is a repository setting, and this
  section is the record that it was done.
- **`.github/labels.md`** — new. The register of the three labels the automation branches on:
  what reads each one, what it does, where its meaning lives, and the three `gh label create`
  commands that put them in a fresh repository. It carries a dated claim about the half no
  offline test can reach.
- **`tests/fitness/test_label_registry.py`** — new, eight tests. It reads
  `.github/workflows/ci.yml`, `scripts/changelog.sh` and `.github/dependabot.yml` and refuses
  a disagreement with the register in either direction.
- **`spec/design/testing.md`** — a row for the new module in § Fitness functions, which
  `tests/fitness/test_test_layout.py` demands and which is how the gap above was caught while
  this change was being written, plus the dated `Rejected (decision of 2026-09-16, …)` block
  the `recorded-decision` gate asks of a specification edit made on the trunk. It records the
  four alternatives: asking the GitHub API, moving the check into CI where a token exists,
  leaving each label in the module that reads it, and asserting how many there are.
- **`CLAUDE.md`** and **`changelog/README.md`** — the two places that offer the `no-changelog`
  exemption now also say that the label is a setting rather than a file, and point at the
  register.
- **`tests/fitness/test_withdrawn_claims.py`** — one assertion message and one docstring line
  said "both labels this repository reads"; three are read, so both now say so.

## Why

`no-changelog` was matched by `scripts/changelog.sh`, handed to it by `.github/workflows/ci.yml`
in `CHANGELOG_LABELS`, and offered to the author by `changelog/README.md`, `CLAUDE.md` and
`.github/pull_request_template.md`. It did not exist. Three documents promised an exemption
that could not be taken, and the only way to find that out was to try it on a pull request
already failing the gate.

Checking that one turned up a second: the `cross-platform` job's `if:` is the only way a pull
request can ask for the macOS leg, `spec/design/testing.md` says so, and that label did not
exist either. Both had been absent since the mechanisms were written.

The failure is quiet by construction. A `case` arm that never matches and an `if:` that is
never true look exactly like a rule nobody reached for — there is no error, no warning, and
nothing red. `spec-exempt` had the same hole and it was found the expensive way: in the middle
of the pull request that needed it (#40), which had to stop and create it.

So the durable half is not the two labels. It is that the repository now *declares* which
labels its behaviour depends on, in a file a test reads — because this template is cloned, and
a clone starts with GitHub's defaults and none of these.

## From what, to what

**Before.** Three labels branched on by the automation. One existed. Nothing in the repository
listed them, nothing checked them, and the prose describing two of them was false.

**After.** Three branched on, three exist, and `.github/labels.md` names all three with what
reads each. `tests/fitness/test_label_registry.py` fails if a fourth appears in the automation
without a row, if a row loses its reader, or if a row's cited document stops naming its label.
The question no offline test can answer — do they exist on GitHub — is a dated sentence and a
one-line `gh` command rather than a silence.

## How it works now

Reaching for an exemption or asking for the macOS leg is unchanged: put the label on the pull
request. `CI passed` recomputes, because `labeled` and `unlabeled` are on the workflow's
trigger.

Adding a label to the automation is now three steps instead of one, and the suite says so at
the moment you skip one: wire the branch, add a row to `.github/labels.md` naming what reads
it and where its meaning lives, and create the label with `gh label create`. Miss the row and
`test_label_registry.py` names the label and the file that branches on it. Miss the reader and
it names the ghost row. The third step is the one no test can see, which is why the register
carries the command and the date it was last checked.

Setting up a fresh repository from this template: run the three commands in
`.github/labels.md` § Creating them in a fresh repository, once, with admin rights.

## What it means for the process

Nothing about running or changing this repository moves, and no script, gate or script-contract
name changes. One habit is added and it belongs to whoever adds a label: the register is part
of the change that branches on it, not a follow-up.

Nothing here is the change process's. `.github/labels.md` and the new module are this
template's, the test imports nothing of the process, and no plugin surface is touched — so
there is no issue to file against `forge@scalo`.

## What it does not change

- **What any label means.** `changelog/README.md`, `spec/design/testing.md` and
  `spec/changes/EXEMPTIONS.md` still own the three meanings; the register points at them and
  explains none of them. The test holds the pointer, not the prose.
- **`.github/dependabot.yml`.** It still sets no `labels:`, and the long comment explaining why
  the `spec-exempt` it used to carry was a standing, never-expiring exemption still stands. The
  new scanner reads that file so a future `labels:` key would have to be declared — it is
  proved on a fabricated positive, and it asserts the real file still sets none.
- **Whether the labels exist.** No test asserts it and none can: the fitness suite takes no
  network by construction, and a test that reached for the API would be red on an aeroplane
  and on every fork without a token. The register carries the date instead.
- **The other labels.** `bug`, `enhancement`, `auto`, the dated audit label and the rest of
  GitHub's defaults are for humans sorting issues. Nothing in `scripts/`, `.github/workflows/`
  or `.github/dependabot.yml` reads them, so none of them can break by being absent, and none
  is in the register.
- **`CI passed` and the ruleset.** Untouched.

## How it was verified

- **The labels, against the live repository.**
  `gh api repos/Scalo-Sales-Engineering-Consulting/forge_template_python_react/labels` before:
  twelve labels, `spec-exempt` among them, no `no-changelog` and no `cross-platform`. After the
  two `gh label create` calls: both present, with the colours and descriptions above.
- **The new module goes red for each thing it claims to catch**, and the messages were read
  rather than assumed. Deleting the `no-changelog` row: *Undeclared -- create the label and add
  its row: {'no-changelog': ['scripts/changelog.sh']}*. Renaming that row to a label nothing
  reads: the same failure plus *Declared but unread ... ['ship-it']* and *a row cites a document
  that no longer names its label: ['ship-it -> changelog/README.md']*. Removing the dated line:
  the message that says the line is the whole of the claim and to re-check it rather than
  delete it. Every scanner also carries a positive — two live ones for the workflow and the
  gate, a fabricated one for Dependabot, which sets no labels today.
- **The count guard was wrong on the first draft and was rewritten.** It asserted at least
  three rows, which would have turned red on the correct act of retiring a label. It now asserts
  that no row is *skipped* by the parser and says why a count is not the check.
- **The repository caught a gap in this change before CI could.**
  `tests/fitness/test_test_layout.py` refused the new module for having no row in
  `spec/design/testing.md` § Fitness functions. That row is in this diff because of it.
- `./scripts/test.sh fitness`: **252 passed**.
- `./scripts/lint.sh --fix`: **OK** — `ruff`, `ruff format` over 161 files, `mypy --strict` over
  107 source files, `eslint`, `tsc`.
- `sdd-specs`: **OK** — every content gate. `links` and `backtick-paths` both grew by one
  document and resolved everything the new file names.
- `./scripts/changelog.sh check --base main`: **OK** on this entry.
- `sdd-specs --diff-gates --base main`: `recorded-decision` fired on the first run — a
  specification edit with no ADR, no change directory and no dated block — and the block
  described above cleared it. **0 gates failed over 7 changed files.** No exemption was
  reached for and `spec/changes/EXEMPTIONS.md` is untouched.
- `./scripts/check.sh`: every gate **OK** — 779 backend tests and 1 skipped, 100 frontend, the
  frozen contract, the infrastructure and the production image. The end-to-end leg failed on
  the first run for a reason outside this diff: an unrelated container on this machine held
  `0.0.0.0:5432`, so compose could not bind the host port. Re-run on the knob
  `docker-compose.yml` carries for exactly that collision —
  `POSTGRES_HOST_PORT=5462 ./scripts/test.sh e2e` — it is **44 passed**, 30 scenarios plus the
  UI smoke, census reconciled.
- **Not run, and why.** The macOS leg needs a macOS runner. Nothing else was skipped.

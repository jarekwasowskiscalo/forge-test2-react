---
date: 2026-09-16
branch: deps/audit-every-ecosystem-and-pin-the-actions
pr: 51
kind: ci
---

# Audit every ecosystem this repository executes, and pin the actions

## What changed

`scripts/audit.sh` rewritten around one section per ecosystem, on the counter-and-gaps shape
`scripts/hygiene.sh` already uses: npm over `frontend/package-lock.json` and **`uv audit` over
`uv.lock`** are audited; the base images, the Terraform providers and the GitHub Actions are
reported as covered by a pin rather than by a query, each line naming the mechanism and
confirming it is still in place before printing the claim. Its `--help` gains an exit-code table.

`.github/workflows/ci.yml`, `deploy.yml`, `preview.yml`, `preview-teardown.yml`, `release.yml` —
all **47** third-party `uses:` steps rewritten from a tag to a 40-character commit with the tag in
a `#` comment. `.github/workflows/ci.yml`'s `audit` job gains `astral-sh/setup-uv`, without which
the new section would be a permanent named gap on the runner.

`tests/fitness/test_action_pins.py` is new: every `uses:` runs a commit, every pin keeps its tag,
what may move is listed with its reason, and the list clears itself. Registered in
`spec/design/testing.md` § Fitness functions.

`.github/dependabot.yml` gains the `terraform` ecosystem over the five roots.
`tests/tooling/test_audit_script.py` grows a tree matching what the script now reads, and three
cases: an absent `uv` is INCOMPLETE, a Python advisory FAILS with its own remediation, and a real
advisory outranks a named gap. `scripts/ci_summary.py`'s `render_audit`, `scripts/help.sh`,
`docs/security.md` and `.specconf/stack.json`'s `review-code` hand-off note stop describing a
frontend-only audit.

## Why

`scripts/audit.sh` promised "the dependencies this repository ships and builds with" and read one
tree. The verdict was published under an unqualified name — `summary "Dependency audit"`,
`gate "Dependency audit"`, `name: Dependency audit` — so a green gate was a statement about a
repository whose `uv.lock` had never been the subject of a single advisory query.

The gap was load-bearing rather than theoretical: `ci.yml`'s `deps` filter already counts
`pyproject.toml` and `uv.lock` as dependency manifests, so a backend dependency change made this
gate **blocking** over a tree it did not read. And the script states the rule it was breaking in
another dimension, at its own line 19: *"a gate that quietly does not run reads on a dashboard
exactly like one that found nothing."* It honoured that for an absent `npm` and had no equivalent
for an ecosystem it never tried.

Separately, not one workflow step was pinned. A tag is a mutable git ref; an unpinned `uses:` is
code that runs on this repository's runners, with this repository's token, and changed with no
commit here to review. This was the only repository of the three in this family that did not pin.

## From what, to what

**Before:** `audit.sh` = `npm audit` over `frontend/package-lock.json`, four `summary` sites, exit
4 only when `npm` or its lockfile was missing. 47 `uses:` steps on moving tags, none pinned.
Dependabot: four ecosystems. Nothing in `tests/` asserted anything about a `uses:` line.

**After:** five ecosystems reported, two of them audited and three stated as pinned-not-scanned.
Exit 4 available per ecosystem. Every action on a commit. Dependabot: five ecosystems. A fitness
test holds the pins and a tooling test holds the three-state exit per ecosystem.

## How it works now

`./scripts/audit.sh` prints one `==>` section per ecosystem and ends in one verdict. An advisory
that fails its section sets a failure; an ecosystem whose tool is absent is appended to a named
`gaps` list. A gap only speaks when nothing failed — a real advisory is the louder fact — so the
exit is 1 if anything failed, else 4 if anything was skipped, else 0.

The severity rule is not symmetric and the header says so: `--level` (default `high`) governs npm,
while `uv audit` exposes no threshold, so **any** Python advisory fails. `uv audit` is also still
flagged experimental by uv itself.

The three unscanned ecosystems are not silent. Each line names what freezes the bytes (a digest, a
`.terraform.lock.hcl`, a commit), which Dependabot ecosystem proposes the bump, and which test
holds it — and the script checks each of those is still there before printing the claim, because a
coverage line that asserts nothing is the same fault one level up.

Two references may still move, and they are listed in `tests/fitness/test_action_pins.py` with the
reason: the change process's own composite actions resolve at `@main` while the process is at 0.x,
which `ci.yml` already argued beside them and `CLAUDE.md` treats as a property. The list clears
itself — an entry no workflow uses fails the test, so the exemption cannot outlive its subject.

## What it means for the process

Nothing about running or changing this repository moves. `./scripts/check.sh` and
`./scripts/audit.sh` are called the same way and answer with the same three codes.

One habit does change: a bump of an action is now a SHA edit, and the tag comment beside it is
what Dependabot reads to propose "v7 → v8" rather than two opaque hashes. Resolve a tag with
`gh api repos/<owner>/<repo>/commits/<tag> -q .sha`, which dereferences annotated tags correctly.

## What it does not change

The gate keeps the name **Dependency audit**. The finding asked to narrow the label *or* widen the
measurement; widening is the half worth having, and the report now enumerates each ecosystem's
coverage, so the name stops over-claiming by becoming true. Renaming would have churned
`tests/fitness/test_ci_parity.py`'s `_RUN_IN`, `scripts/ci_summary.py`, `ci.yml` and three tooling
tests for no gain.

No advisory scanner was added for the base images or the Terraform providers, and the exit code
does **not** become a permanent 4 for them. A gate that reads INCOMPLETE on every run teaches
people to ignore it, which is the failure this repair is about, inverted.

The two `@main` references are not pinned, by decision. The moderate React Router advisories in
`frontend/` remain moderate and remain reported and not blocking.

## How it was verified

`./scripts/audit.sh` — five sections, `Dependency audit: OK`. `./scripts/test.sh fitness` (258),
`./scripts/test.sh tooling` (318), `./scripts/lint.sh`, `./scripts/check.sh`, and `sdd-specs`.

The pin detector was **shown to fire**: run over `git show main:.github/workflows/*`, it convicts
all 47 steps; over the branch, none. The audit's new branches are proved on a stubbed tree rather
than on this machine's real opinion of the lockfiles — an absent `uv` yields exit 4 and names
`backend (Python)`, a Python advisory yields exit 1 with `uv lock --upgrade-package`, and an
advisory beside an absent tool yields 1 and not 4.

Not verifiable here: whether Dependabot actually opens Terraform provider pull requests, which
needs a week and the GitHub side. `GHSA` lookups by `uv audit` need the network, exactly as
`npm audit` already did.

Closes https://github.com/Scalo-Sales-Engineering-Consulting/forge_template_python_react/issues/31

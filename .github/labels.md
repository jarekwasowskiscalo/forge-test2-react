# The labels this repository's automation branches on

A label is a **repository setting, not a file.** `git` has never seen one, a clone carries
none, and a repository created from this template starts with GitHub's defaults and nothing
else. So a branch in the automation that waits for a label is inert until somebody with admin
rights types a command — and inert *silently*: a `case` arm that never matches and an `if:`
that is never true read exactly like a rule nobody reached for.

That silence is why this file exists. `no-changelog` was matched by `scripts/changelog.sh`,
fed to it by `.github/workflows/ci.yml`, and offered to the author by `changelog/README.md`
and `.github/pull_request_template.md` — in a repository where it did not exist, so the one
exemption those three documents promise could not be taken. `cross-platform` was the same
defect in the same week. `spec-exempt` was created by hand in the middle of the pull request
that first needed it ([#40](https://github.com/Scalo-Sales-Engineering-Consulting/forge_template_python_react/pull/40)),
which is the version of this that gets noticed; the other two are the version that does not.

## The three

| Label | What branches on it | What it does | Where its meaning lives |
| --- | --- | --- | --- |
| `no-changelog` | `scripts/changelog.sh`, over the names `.github/workflows/ci.yml` hands it in `CHANGELOG_LABELS` | Waives the entry a change made outside the process owes, for a typo or a whitespace fix | `changelog/README.md` |
| `cross-platform` | the `cross-platform` job's `if:` in `.github/workflows/ci.yml` | Asks for the macOS leg on this pull request, which otherwise runs weekly, on the trunk and on request | `spec/design/testing.md` |
| `spec-exempt` | the `specs` job's `exempt:` input in `.github/workflows/ci.yml` | Waives the diff-scoped gates named in an open register row, and is inert without one | `spec/changes/EXEMPTIONS.md` |

**No other label is here, and the boundary is the point.** `bug`, `enhancement`, `duplicate`
and the rest of GitHub's defaults are for humans sorting issues; `auto` and the dated audit
labels are for humans too. Nothing in `scripts/`, `.github/workflows/` or `.github/dependabot.yml`
reads any of them, so none of them can break by being absent. This table is the set whose
absence changes what CI does.

## Creating them in a fresh repository

Three commands, once per repository, by somebody with admin rights. They are not idempotent —
`gh label create` fails on a name that already exists, which is the answer to "do I need to
run this".

```bash
gh label create no-changelog --color FBCA04 --description "Waives the changelog entry, for a typo or a whitespace fix -- changelog/README.md"
```

```bash
gh label create cross-platform --color 1D76DB --description "Asks for the macOS leg on this pull request -- spec/design/testing.md"
```

```bash
gh label create spec-exempt --color FBCA04 --description "Waives the diff-scoped spec gates, on a dated row in spec/changes/EXEMPTIONS.md"
```

The two waivers share a colour on purpose: both are break-glass, and a reviewer should see
the same yellow on a pull request that has excused itself from a gate. `cross-platform` asks
for *more* checking rather than less, so it does not wear that colour.

## What holds this table to the code, and what cannot

`tests/fitness/test_label_registry.py` reads the automation and this file and refuses a
disagreement in either direction: a label the automation branches on and this table omits, a
row here nothing branches on, and a row whose cited document has stopped naming its label. It
runs in the offline suite, so it proves the *names* agree.

It cannot prove the labels exist. That question is answered by the GitHub API, the fitness
suite takes no network, and a test that did would turn red on an aeroplane and on every fork
without a token — which is a worse trade than a claim with a date on it. So the claim carries
a date instead, and whoever doubts it can settle it in one command:

```bash
gh label list --json name --jq '.[].name'
```

**Last verified against the live repository: 2026-09-16** — all three exist. `no-changelog`
and `cross-platform` were created on that date, by the pull request that added this file;
`spec-exempt` has existed since #40.

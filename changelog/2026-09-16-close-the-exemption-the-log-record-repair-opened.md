---
date: 2026-09-16
branch: chore/close-the-log-record-exemption
pr: 43
kind: chore
---

# Close the exemption the log-record repair opened

## What changed

- `spec/changes/EXEMPTIONS.md` — one row removed: `change-directory` over
  `app/core/errors.py`, `app/core/logging_config.py`, `app/core/request_id.py` and
  `app/db/session.py`, opened 2026-09-16 and dated to expire 2026-09-30.

Nothing else. No code, no test, no document.

## Why

The row was opened for [#40](https://github.com/Scalo-Sales-Engineering-Consulting/forge_template_python_react/pull/40)
and for nothing else. `change-directory` refuses a diff touching `trees.behaviour` — which
names `app/` — without a change directory in it, and that repair was made outside
`/forge:sdd` by decision. A row cannot silence that particular failure on its own (it carries
no paths, so nothing can be matched against it); what it does is give the `spec-exempt` label
a reason and an expiry to stand on, and the label is what reaches it.

#40 merged as `2740ccb`. From that moment the row covers no diff and grants no exemption to
any future one: it is a standing permit that would sit there until 2026-09-30 and then turn
the build red on a morning when nobody committed anything — which is exactly the alarm clock
`EXEMPTIONS.md` describes, ringing for a conversation that is already over.

The entry for #40 said so in as many words — *"Delete the row once this has merged."* This is
that deletion, and it is a separate pull request because the row had to exist while #40 was
open.

## From what, to what

**Before.** Three open rows: two from the 2026-09-08 audit, expiring 2026-09-22, and this
one. `sdd-specs` reported `exemptions: 0 problem(s) in 3 rows`.

**After.** Two open rows, both from the 2026-09-08 audit. `exemptions: 0 problem(s) in 2 rows`.

## How it works now

Exactly as before, with one fewer permit outstanding. A future diff that touches `app/`
without a change directory meets `change-directory` with nothing to wave it through, which is
the rule doing its job: the next such change either goes through `/forge:sdd` and gets a
change directory, or argues for its own dated row on its own merits.

## What it means for the process

Nothing about running or changing this repository moves.

One habit is worth naming, because this is the second time the pattern has appeared in two
days: a row opened to get one pull request past a gate is closed by the pull request that
follows it, not by its expiry date. [#36](https://github.com/Scalo-Sales-Engineering-Consulting/forge_template_python_react/pull/36)
opened an `operations-doc` row and [#38](https://github.com/Scalo-Sales-Engineering-Consulting/forge_template_python_react/pull/38)
closed it by making the lasting fix. This one has no lasting fix to make — the gate was right
and the change genuinely was a behaviour change without a change record — so the close is the
whole of it.

## What it does not change

- **The two audit rows.** `change-directory` over the 2026-09-08 audit's files and
  `e2e-scenario` over `frontend/src/components/ui/**` both stand, with their own dates.
- **The `spec-exempt` label.** It stays in the repository; it was created for #40 and is the
  documented escape for a failure no row can express. It is inert without a row naming a gate
  that actually failed.
- **What #40 did.** No line of `app/`, `tests/`, `docs/` or `spec/design/` is touched here.

## How it was verified

- `sdd-specs`: **OK** — every content gate, `exemptions` over the remaining 2 rows included.
- `sdd-specs --diff-gates --base main`: **0 gates failed over 2 changed files.** This diff
  touches no behaviour path, so `change-directory` does not fire and the removed row is not
  needed to get this pull request through — which is the check that matters, and the reason
  this is safe to do in a pull request of its own.
- `./scripts/changelog.sh check --base main`: **OK** on this entry.
- `./scripts/check.sh`: not run, and it does not apply: the diff is one deleted table row and
  one new file under `changelog/`, neither of which any suite reads. CI runs it regardless.

---
date: 2026-09-16
branch: chore/close-the-error-envelope-exemptions
pr: <the number, once the pull request is open>
kind: chore
---

# Close the exemptions the error-envelope repair opened

## What changed

- `spec/changes/EXEMPTIONS.md` — two rows removed, both opened 2026-09-16 and dated to expire
  2026-09-30: `change-directory` over `app/contexts/guestbook/routers/guestbook_entries.py`,
  `app/core/errors.py`, `app/main.py` and `frontend/src/api/schema.d.ts`, and `e2e-scenario`
  over that same router.

Nothing else. No code, no test, no document.

## Why

Both rows were opened for
[#46](https://github.com/Scalo-Sales-Engineering-Consulting/forge_template_python_react/pull/46)
and for nothing else. `change-directory` refuses a diff touching `trees.behaviour` — which names
`app/` and `frontend/src/` — without a change directory in it, and `e2e-scenario` refuses one
touching `trees.observable` with nothing under `e2e/`. That repair was made outside `/forge:sdd`
by decision, so neither could be satisfied.

#46 merged as `6a33ec3`. From that moment the rows cover no diff and grant no exemption to any
future one. What is left is two standing permits that would sit there until 2026-09-30 and then
turn the build red on a morning when nobody committed anything — which is exactly the alarm clock
`EXEMPTIONS.md` describes, ringing for a conversation that is already over.

The entry for #46 said so in as many words — *"Delete them once this has merged."* This is that
deletion, and it is a separate pull request because the rows had to exist while #46 was open.
[#43](https://github.com/Scalo-Sales-Engineering-Consulting/forge_template_python_react/pull/43)
did the same for #40, one finding earlier.

## From what, to what

**Before.** Four open rows: two from the 2026-09-08 audit, expiring 2026-09-22, and these two.
`sdd-specs` reported `exemptions: 0 problem(s) in 4 rows`.

**After.** Two open rows, both from the 2026-09-08 audit. `exemptions: 0 problem(s) in 2 rows`.

## How it works now

Exactly as before, with two fewer permits outstanding. A future diff touching `app/` or
`frontend/src/` meets `change-directory` with nothing standing between it and the gate, and one
touching a router meets `e2e-scenario` the same way — which is the state both gates are supposed
to be in.

## What it means for the process

None — nothing about running or changing this repository moves. The rule that produced this
pull request is `EXEMPTIONS.md`'s own: a row is closed when the change it was opened for has
merged, rather than left to expire.

## What it does not change

- **The repair itself.** #46 is merged and none of it is touched here.
- **The two 2026-09-08 audit rows.** They expire 2026-09-22 and belong to work that is not this.
- **The `spec-exempt` label on #46.** A label on a merged pull request is part of its record.

## How it was verified

`sdd-specs` — `exemptions: 0 problem(s) in 2 rows`, and all thirteen content checks green.
`./scripts/changelog.sh check --base main` — OK.

The diff-scoped gates are not exercised by this change and could not be: it touches neither
`trees.behaviour` nor `trees.observable`. That is the point of it being its own pull request.

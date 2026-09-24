# Gate exemptions

Standing, dated exemptions from the `specs` gate. **Every row expires, and the `exemptions` gate breaks
the build on an expired one.**

That was not true until 2026-08-14. This file spent its whole life claiming it was — first
promising an enforcement no version of the linter had, and then, after a correction, admitting
outright that no gate read it and that expiry was a promise between people. That admission was an
honest form of the same problem: a documented way out that nothing holds is a way out with no way
back, while every other escape hatch here is audited at the moment it is used. `check_specs.py`
now reads this table.

One consequence is worth stating rather than leaving to be discovered: **`exemptions` can turn the
build red on a morning when nobody committed anything.** An expiry is an alarm clock, and an alarm
clock nobody hears is a date somebody picked to end a conversation. The fix is one line — renew
the row with a date you would defend again, or delete it, because the exemption is over.

This file exists because of what happens without it. A gate with no way out gets switched off the
first time it blocks something urgent and justified, and a gate once switched off is never
switched back on. So the way out is here: it costs a dated line of prose in git, it is visible in
review, and it rots loudly rather than quietly.

Use this only for work stretched across several changes — a migration, a vendored import, a
feature whose prerequisite is not built. For a single case, choose the escape in the artefact,
which is cheaper and reads better:

- **`traceability`** — write `**Verified-by:** manual — <reason>` under the requirement.
- **`recorded-decision`** — write `**ADR:** none — <why this is editorial>` under the entry in
  `delta.md`. **On the trunk there is no `delta.md`**, and
  [`../design/conventions.md`](../design/conventions.md) § When a decision is an ADR forbids the
  ADR until the first change has gone through `/sdd` — so the decision goes into the document
  whose rule it changes, as a dated `Rejected (decision of <date>, `cr: historical` — <why>)`
  block, and the gate reads it there. A row here is not the route for that: it would call a
  recorded decision an exception.

For a pull request that really is not a change of behaviour, the `spec-exempt` label lets
through **all eight diff-scoped gates at once** — `change-directory`, `change-record`,
`delta-coverage`, `e2e-scenario`, `one-open-change`, `operations-doc`, `recorded-decision` and
`screen-spec` — and
prints the exemption to the job summary. That breadth is the reason a dated row here is the better way out
whenever a row can express the scope.

**The label no longer works on its own.** It is honoured only while a row in the table below
names a gate that actually failed; without such a row the gates block and CI says why. The label
still reaches what a row cannot — `change-directory`'s missing directory and `change-record`'s
stage and status carry no paths, so no row can cover them — but it reaches them with a reason and an expiry date behind
it rather than silently. A permit nobody has to renew is a rule that was deleted rather than
waived, and this is the register where the renewal comes due.

## Open exemptions

| Gate | Paths or identifiers | Reason | Opened | Expires |
|---|---|---|---|---|
| `change-directory` | `frontend/src/contexts/guestbook/**`, `e2e/ui/test_smoke.py` | The four findings of the 2026-09-15 audit that this repairs (A27, A28, A31, A32) arrived as GitHub issue #26 against a delivered screen, and the repair was taken on the trunk by the repository's owner rather than through `/forge:sdd`, so there is no change record for the gate to find. What a `delta.md` would have declared is declared instead where each rule lives: the reversed paging decision and the two new screen states in `spec/design/ui/guestbook.md`, the test-file rule in `spec/design/testing.md`, both as dated `cr: historical` blocks, plus a changelog entry naming every path. The behaviour is provable from outside -- `e2e/ui/test_smoke.py` gained the case a change record would have demanded, and it fails against the defect. This row buys the missing directory and nothing else. | 2026-09-16 | 2026-09-30 |
| `change-directory` | `frontend/src/styles/theme.css`, `frontend/src/components/ui/Modal.tsx`, `frontend/src/components/ui/Modal.test.tsx`, `frontend/src/contexts/guestbook/components/EntryComposer.tsx`, `frontend/src/contexts/guestbook/components/EntryCard.tsx`, `frontend/src/contexts/guestbook/components/EntryToolbar.tsx`, `frontend/src/contexts/guestbook/components/DeleteEntryDialog.test.tsx` | GitHub issue #27 (audit findings A29 and A30) repairs two accessibility defects in which the code failed a promise the specification had ALREADY made: `spec/design/ui/guestbook.md` said the composer shows "a focus ring in the accent colour" and the built stylesheet shipped `outline-style: none`, and `Modal` declared `aria-modal="true"` while leaving focus on the control behind it. No rule moved -- no route, no column, no refusal code, no screen state -- and the black box passed unchanged on both sides of the repair. It was made outside `/forge:sdd` by decision, the same route findings A25 and A26 took in #46, so there is no change directory for this gate to find. What a change record would have carried is in the places the rules live: the cascade decision and the rejected native `<dialog>` as dated `Rejected` blocks in `spec/design/ui/guestbook.md`, the contrast floor as one in `spec/design/ui/system-states.md`, the choice of suite as one in `spec/design/testing.md`, and the evidence -- every new test seen failing first -- in the `changelog/` entry. The row names the seven files so the label reaches exactly them. | 2026-09-16 | 2026-09-30 |
| `change-directory` | `app/contexts/guestbook/**`, `app/platform/schemas/text.py`, `frontend/src/contexts/guestbook/**`, `e2e/suite/features/guestbook.feature`, `e2e/ui/test_smoke.py`, `contracts/openapi/guestbook.yaml`, `contracts/invariants/guestbook.md`, `golden-set/fixtures/**` | GitHub issue #28 (audit finding A33) repairs a defect in which the browser measured text in UTF-16 code units while the column, the published contract and Pydantic measured code points -- so a signature of 41 emoji was refused by the screen and stored by the API with a 201, with a green suite on both sides, because the only binding between them compared a number with a number. It was taken on the trunk by the repository's owner rather than through `/forge:sdd`, the same route issues #26 and #27 took, so there is no change record for this gate to find. What a `delta.md` would have declared is declared instead where each rule lives, as dated `cr: historical` blocks: the unit and the rejected graphemes in `spec/contexts/guestbook.md` (`BR-01`), the phrase's ordering in `spec/design/api.md`, the absent backfill in `spec/design/data-model.md`, the corpus's home in `spec/design/testing.md`, the two modules' placement in `spec/design/conventions.md`, and the removed `maxLength` in `spec/design/ui/guestbook.md` -- plus a changelog entry naming every path and `D-04` in the invariants contract. The behaviour is provable from outside: `e2e/ui/test_smoke.py` gained the case a change record would have demanded, and it fails against the defect -- Playwright reports the field holding 40 of the 41 characters typed. This row buys the missing directory and nothing else. | 2026-09-17 | 2026-10-01 |

## How to add an exemption

One row, with all five columns filled in:

- **Gate** — one row per gate, written in backticks and named from the table in `CLAUDE.md`. An
  exemption from "the specs job" is not a thing; name the rule. A numeric code names no gate: the
  gates were `G1`…`G20` until 2026-09-06 and
  [the process's `spec_gates.py`](https://github.com/Scalo-Sales-Engineering-Consulting/claude-marketplace/blob/main/plugins/forge/skills/_shared/sdd/spec_gates.py) maps every
  one to the name it became. `exemptions` itself is not subject to exemptions, because an
  exemption from the check over exemptions is a way of switching that gate off from inside the
  file it guards. The first cell of the table header stays the English word `Gate` — it is what
  the parser recognises the header row by, so that it skips it rather than judging it a malformed
  exemption.

  A row reaches the diff-scoped gates whose failures carry paths — `change-directory` (the
  two-directory case), `change-record` (a missing record), `delta-coverage`, `e2e-scenario`,
  `one-open-change`, `operations-doc`, `recorded-decision`, `screen-spec` — and the content gates
  of the specification lint: `backtick-paths`, `contracts`, `delta-entries`, `documentation-set`,
  `english`, `frozen-ids`, `links`, `requirements`, `screen-states`, `session-archives`,
  `source-paths`, `tasks`. It does **not** reach
  `traceability` or `generated-indexes`: traceability has its own escape in the artefact
  (`**Verified-by:** manual — <reason>`), and a stale generated index is fixed by regenerating it,
  which is cheaper than any exemption. A row for those two parses, passes the `exemptions` gate —
  and silences nothing.
- **Paths or identifiers** — as narrowly as you can. `changes/CR-2607-4d81/R-9..R-12`, not
  `changes/**`. A single path segment (`spec/**`, `app`) is a blanket rather than a scope: the
  gates skip it and `exemptions` reports it. The only permitted single-segment subject is a file that
  exists in the repository root, such as `CLAUDE.md`.
- **Reason** — what makes the rule impossible to satisfy now, not why it is inconvenient. A reason
  that would still be true in a year is a sign the rule is wrong and should be changed rather than
  worked around. At least 30 characters, because "temporarily" and "blocked" are labels on the
  fact that a rule is unmet rather than answers to the question.
- **Opened** — `YYYY-MM-DD`.
- **Expires** — `YYYY-MM-DD`, after the opening date, and pick one you would defend. `exemptions` compares
  it against today's date on every run.

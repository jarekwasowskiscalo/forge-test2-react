# Impact — the guestbook, the template's worked example

> Retrospective. This section describes the world **as it was before** the guestbook
> existed, which for this change is the emptiest possible starting point: the template had
> no bounded context at all.

## How the area works today

It does not. Before `b025cc5` there was no domain concept, no table, no screen and no
scenario file. Everything the guestbook touches, it creates.

That is worth writing down rather than skipping, because it fixes the shape of every later
change: the first context establishes the layering inside a context (`routers/` → `services/` →
`models/` + `schemas/` under `app/contexts/guestbook/`, since the recut of 2026-09-07), the four test groups, and the rule that one domain concept
gets one file per layer named after the concept.

## What the change touches

| Area | Before | After |
|---|---|---|
| Domain | nothing | one bounded context, `spec/contexts/guestbook.md` |
| Schema | no table | one table, one Alembic revision |
| Contract | no `/api/guestbook-entries` | `contracts/openapi/guestbook.yaml`, hand-written |
| Screen | no screen | one, `spec/design/ui/guestbook.md` |
| Corpus | none | four files under `golden-set/`, in two declared halves: three fixtures the suites assert about and one seed a fresh environment opens with |

## Measured tier signals

Recorded with `change_state.py set-signals` rather than argued about. Every one of the
eleven is measured, the unlit ones included: "not lit" is a measurement, and silence is not.
This table is the human-readable copy of what the verb recorded; the machine truth is the
record itself, read with `change_state.py show`.

| Signal | Lit | Evidence (what was found and where) |
|---|---|---|
| `contract_touched` | yes | `contracts/openapi/guestbook.yaml` and the entry endpoints in `spec/design/api.md` |
| `schema_touched` | yes | one table, `guestbook_entries`, and the Alembic revision that creates it |
| `screen_touched` | yes | one screen, `spec/design/ui/guestbook.md` |
| `rule_touched` | yes | five business rules, `BR-01` to `BR-05`, in `spec/contexts/guestbook.md` |
| `contexts_touched_gt_1` | no | one context, and it is the first — there is no second to touch |
| `new_context` | yes | `spec/contexts/guestbook.md` did not exist before this change |
| `backend_touched` | yes | one file per layer under `app/contexts/guestbook/{models,schemas,services,routers}/` |
| `frontend_touched` | yes | `frontend/src/contexts/guestbook/pages/GuestbookPage.tsx` and the components, hooks and rules it composes |
| `infra_touched` | no | `infra/` belongs to the template; the example adds nothing to it and would remove nothing from it |
| `tooling_touched` | no | as measured: no script existed for this example's sake. The corpus seeder came later, with the split of `golden-set/` |
| `ci_touched` | no | the workflow runs the same scripts whichever example the template carries |

**Resulting tier:** `p3` — computed by `process_config.py --tier --signal …` from the eleven
above and recorded with the verb `change_state.py set-tier`, not by this paragraph. The record
carried `p2` from init, before the signals were measured.

## Risks the change carries

- **The example teaches by being copied.** A shortcut here is a shortcut in every fork. That
  is why the guestbook carries a full set of suites rather than a token test.
- **Deletion is permanent by decision** (`BR-03`). A fork that needs recovery has to
  contradict this rule rather than extend it.
- **There is no authentication**, so anybody can amend or delete any entry. Named as a
  non-goal in `spec/invariants.md`, not left as an absence somebody has to notice.

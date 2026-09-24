<!-- TEMPLATE: filled in by the requirements stage; the file counts as non-existent until this marker is gone -->
# How this works today

*Descriptive only. No proposals — this is what the requirements author reads before
anyone decides anything.*

## What the request touches
<one paragraph, in the words of the glossary>

## What the specification says
- <claim> — `spec/design/<document>.md § <heading>`

## What the domain document says
- `BR-xx` — <rule>, `spec/contexts/<context>.md`

## What the code does
- <behaviour> — `app/contexts/<context>/services/<file>.py:<line>`
- <endpoint> — `app/contexts/<context>/routers/<file>.py:<line>`
- <screen> — `frontend/src/contexts/<context>/pages/<file>.tsx:<line>`

## What the tests guarantee
- `tests/test_<file>.py::test_<name>` — <what it nails down>
- `e2e/suite/features/<file>.feature` — <a scenario a non-programmer can read>

## Where these disagree
<the most valuable section. Empty is a good answer — write that outright.>

## What is missing
- <what is absent> — searched for `<phrases>` in `<places>`, not found

## What I could not determine
- <question> and why the code does not answer it

## Tier signals

*Measured, not judged. `cr-impact` greps surface names against the specification tree and
writes the result down; that same set of signals then selects the conditional steps in every
later stage. "Not lit" is a measurement — an empty cell is not.*

| Signal | Lit | Evidence (what was found and where) |
|---|---|---|
| `contract_touched` | yes / no | |
| `schema_touched` | yes / no | |
| `screen_touched` | yes / no | |
| `rule_touched` | yes / no | |
| `contexts_touched_gt_1` | yes / no | |
| `new_context` | yes / no | |
| `backend_touched` | yes / no | |
| `frontend_touched` | yes / no | |
| `infra_touched` | yes / no | |
| `tooling_touched` | yes / no | |
| `ci_touched` | yes / no | |

**Resulting tier:** `<p0 | p1 | p2 | p3>` — computed by
`process_config.py --tier --signal …` and recorded with the verb `change_state.py set-tier`,
not by this paragraph.

*This table is for a human and nobody parses it. The machine truth is
`change_state.py set-signals` — and for the whole time only this table existed, the measured
signals died as prose the moment a worker returned, and the eleven-entry `conditional` block
had nothing to read and selected nothing.*

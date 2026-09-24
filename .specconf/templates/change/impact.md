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
- <behaviour> — `<path>:<line>`, in the form this stack's `HAND-OFF` note for `cr-impact` gives
- <surface> — `<path>:<line>`
- <screen> — `<path>:<line>`

## What the tests guarantee
- `<test file>::<test name>` — <what it nails down>
- `<black-box file>` — <a scenario a non-programmer can read>

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
| `<path signal>` | yes / no | one row per path signal this stack declares in `.specconf/stack.json` § `signals`; the dispatch names them |

**Resulting tier:** `<p0 | p1 | p2 | p3>` — computed by
`sdd-engine process_config --tier --signal …` and recorded with the verb `sdd-engine change_state set-tier`,
not by this paragraph.

*This table is for a human and nobody parses it. The machine truth is
`sdd-engine change_state set-signals` — and for the whole time only this table existed, the measured
signals died as prose the moment a worker returned, and the eleven-entry `conditional` block
had nothing to read and selected nothing.*

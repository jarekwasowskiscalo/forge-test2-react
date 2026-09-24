# The ledger of process fixes

This is the file that makes the loop converge. Without it every round starts from zero and
"the process is better now" stays an impression.

**An entry with no target metric does not get in.** Not "simplify the `design-plan` brief", but
"the Bash share on the plan stage below 30 %". The direction is part of the metric: a number
with no direction is not a promise that can be refuted.

The `before` column is filled in by the round that proposed the fix, from that round's
`metrics.json`. The `after` and `verdict` columns are filled in by the **next** round, from
`previous-round.md`, where both of those fields are already computed. Nobody computes this from
memory.

## States

| state | means |
|---|---|
| `proposed` | a round named it, a human has not decided yet |
| `accepted` | a human accepted it, nobody has implemented it yet |
| `rejected` | a human rejected it — with a reason, because a rejection with no reason comes back in the next round |
| `implemented` | the change is in the repository, the metric has not been measured yet |
| `verified` | the metric moved in the promised direction |
| `reverted` | the metric moved the other way, or a regression appeared |

## The register

| id | date | symptom | artefact | target metric | state | before | after | verdict |
|---|---|---|---|---|---|---|---|---|
| `R0-1` | 2026-09-08 | the retro was prose: `close_stage.py` printed it as "Optional" below its own stop line, and no other module named it | `close_stage.py`, `checkpoint.py`, `next_action.py`, `.specconf/process.json`, `sdd/SKILL.md`, `sdd-retro/SKILL.md` | session archives per closed stage ≥ 1.00 | `implemented` | 0.00 | — | — |

The identifier is `R<round number>-<number within the round>`, so that one round can be
subtracted from another without reading dates. **`R0-*` is the exception and there will
be only one class of them:** fixes made before the first round could run, because the
corpus a round reads was empty. `R0-1` is why it was empty.

`R0-1`'s `after` is filled by the first round that runs with archives in the corpus. If it
reads 0.00 again, the mechanism did not work and the entry becomes `reverted` — which is
the whole point of writing the `before` down on the day the fix shipped.

## Why it is like this, and not in a change record

A fix to the process is not a change to the application's behaviour and does not go through
SDD: there is no change record, no ADR, and it does not touch `spec/`. If it did, correcting one
sentence in a `SKILL.md` would cost the full chain of stages — and then nobody would do it, and
that is exactly the cost this loop is meant to lower.

The price is that nobody guards those promises but this file. That is why it stands in the
repository rather than in `.sdd/`.

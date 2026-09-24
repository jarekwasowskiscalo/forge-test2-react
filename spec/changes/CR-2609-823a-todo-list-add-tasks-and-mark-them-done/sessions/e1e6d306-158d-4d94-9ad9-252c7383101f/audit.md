# Session audit

## Verified

- **The cold run is green.** `sdd-verify --cold` exited 0 and printed `VERDICT GREEN (from scratch, 4 steps)`: setup 3.9s, migrate 9.2s, generate 4.9s, check 298.5s.
- **The cleanroom evidence exists.** `add-evidence --kind cleanroom --from-report .sdd/reports/cleanroom.json` printed `OK kind=cleanroom`; `ls spec/changes/CR-2609-823a-*/evidence/` shows `cleanroom.md`.
- **The boundary gate is green on the tree the close committed.** `sdd-engine loop close --next spec_sync` printed `VERDICT GREEN (profile boundary, 143.87s, head 44615bb4)`: backend 832 executed / 24 skipped, fitness 364, frontend 243, e2e 78, and the specification gates ok. `NEW since baseline: none`.
- **The stage moved.** `change_state show --field stage` → `spec_sync`, and `git log` shows `a694639 … the “a run from nothing” stage is closed`.

## Unverified

- **What the cold run proved does not cover the one uncommitted file.** Its warning said `1 files are uncommitted … NOT proved by it`. I judged that file to be the previous session's `transcript.jsonl` (the only modified path in the gitStatus at session start) and did not re-run the cold verification after committing it. The judgement is plausible but I did not confirm it with `git status` at the moment the cold run started.

## Divergences

- **The design gate reads as approved in the record, but `loop next` says it is open again.** Both `loop next` outputs printed `NOTE the design gate was approved against delta.md, and that file has changed since`. `change_state show --field gates` still has `design.approved: true` with `artifact_sha256: 068b5436…`; `shasum -a 256 delta.md` now gives `10ae6feb…`. `loop close` re-assembled `delta.md` from 8 fragments (including `design/delta/converge.md`, written during implement convergence), so the hash will keep moving whenever a fragment does. `next_action` answered row 42 / 42b and never row 15. Under the table's precedence rule ("the rows below enter at their own positions — narrower than group D's generic rows, so before them") that is what the table says, so I followed it and did not re-ask the approval. The effect is that a stage-gate approval now covers a different `delta.md` from the one the user approved, and nothing in this stage forced the question.

## Bent rules

- **Row 15 was passed over on the table's own precedence.** It was not broken, because the stage rows outrank group D by the table's own statement. But Phase 5 of the orchestrator says "a reconciled document that carried an approved gate re-opens that gate … re-ask the approval in THIS window, while the author is looking". This session closed a stage with that gate showing as re-opened. It has not been filed: it is a question about the process, not a fault this session hit, and it may be intentional (the reconcile stage rewrites `delta.md` again anyway).
- **PROC-37 (owner `here`, from an earlier session) is still `reported`, with no reason recorded.** It is a lesson for `tasks.md` § Lessons about Vite resolving a literal `import()` at transform time. Nobody has confirmed whether that lesson was written down. This session did not touch it.
- **This session added no process faults.** No worker was dispatched (clean_room is a script row), and I did not improvise a step. The queue shows 58 entries, all from earlier sessions: 57 filed, and PROC-37 above.

## Checked and clean

- The constitution and `process-failure.md` were read in full before the first state-changing action, as iron rules 0 and 10 require.
- I checked `next_action`'s `why` against the digest (row 42: stage `clean_room`, `not_started`) and against the `--explain` table before acting.
- No `change.json` was written by hand. Every mutation went through `add-evidence` or `loop close`.
- No command the stack profile refuses was run. No inline interpreter code was run, and no scratch scripts were written.
- The stop line was held: I did not open `spec_sync` after the close.

## What worked

- **Clean room as a script row.** One command, a four-line verdict and a report file the evidence verb reads. The whole stage took three tool calls and no agent. Compare the ladder history (attempt 4), where earlier entries cost far more.
- **`loop close` assembled the delta, ran the gate, committed and printed the boundary sequence in one call**, so there was nothing for the orchestrator to sequence by hand.
- **Running the cold verification in the background** kept the conversation free, and I used the wait to read the constitution.

## For the user to decide

- **Re-approve the design gate?** `delta.md` has changed since it was approved (hash `068b5436…` → `10ae6feb…`). The process did not ask in this stage. Either re-approve it at the start of the next session, or confirm that the reconcile stage's own re-assembly makes it moot.
- **PROC-37** is an owner-`here` fault with no reason recorded. Decide whether the `tasks.md` § Lessons entry it names was written, and resolve it.

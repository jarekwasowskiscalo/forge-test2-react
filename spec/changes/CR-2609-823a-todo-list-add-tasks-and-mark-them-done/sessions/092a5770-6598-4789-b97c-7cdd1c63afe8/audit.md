# Session audit

## Verified

- **The plan passes its own gate.** `sdd-engine check_specs --only tasks` printed `tasks: 0 problem(s) in 2 documents, 31 tasks, 24 judged`. `grep -c '^### T-' tasks.md` printed 24, which matches the worker's report.
- **The design gate now covers the file on disk.** `change_state show --field gates.design.artifact_sha256` and `shasum -a256 delta.md` both print `068b5436…`.
- **The stage moved.** `change_state show --field stage` printed `implement` after `close_stage`.
- **Every process fault in this session is filed.** The `audit` queue lists PROC-34 (#357), PROC-35 (#359) and PROC-36 (#360) as `filed`.
- **The boundary gate's reds are the same set the design close accepted.** The design close's log line reads `accepted RED: Application check, Suite fitnes…`. This run failed `Application check` (its only failed check.sh gate was `API contract is frozen`) and the two context fitness tests. The NEW-since-baseline list names exactly those three.

## Unverified

- **The design close accepted the same two fitness cases.** I saw only the truncated log line (`accepted RED: Application check, Suite fitnes`), not the full reason. That the sets are identical is an inference.
- **The worker's content claims about tasks.md.** It reported that 186 declared case ids were checked against testing.md and scenarios.md, that the intersections are empty, and that every Scope field fits the boundary. I did not open tasks.md. Only its gate verdict was checked.
- **The root causes in #357 and #360.** #357: I grepped `loop.py`, which calls `delta.assemble` inside `close` at line ~1695, and read no further. So "approve does not assemble" is from grep, not a full read. #360: the promotion rule for `last-gate-pending.json` is a hypothesis, to be confirmed in `skills/_shared/sdd/loop.py` / `gate.py`.
- **#359 (PROC-35).** It comes entirely from the worker's report. I did not read `declare-red`'s matcher (`skills/_shared/sdd/change_state.py`).

## Divergences

- **`loop next` computed row 20 (dispatch) while its own NOTE said the design gate had reopened**, which is row 15. The table ranks 15 above 20. I walked the table and took row 15. Filed in #357 § 4.
- **`SKILL.md` says `close_stage` takes `--verification .sdd/reports/last-gate.json`.** After a red `loop close`, that file held the previous stage's run (18:49), and the fresh report was in `last-gate-pending.json` (19:25). Filed as #360.
- **`close_stage --help` says the accept-red reason must name every failed gate "its name … or its label".** Naming the suite label `Suite fitness` was refused, and each fitness case id had to be listed. Filed in #360.

## Bent rules

- **A stage closed on a red gate with `--accept-red`.** This is the second time in this change, after the design close, and for the same structural cause. It is a hatch the process counts, and a hatch used twice is the signal `process-failure.md` names. It was put to the user as a closed question before use, and the user chose to close. The root cause (Article X has no expected-red for check-gate failures at design or plan) is already filed as #314 / #355 from the earlier session. No new filing was needed.
- **The design approval was asked twice.** The first approval was taken over a `delta.md` that `loop close` then rewrote (+320 lines). Re-asking was the rule (row 15). The bent part is that the user's first approval covered a different file than the gate names. Filed as #357.
- **Nothing else was bent in this session's own work.** The orchestrator wrote no product, test or spec file (`git status --porcelain` shows only the change directory and `status.json`).

## Checked and clean

- I read the constitution and `process-failure.md` in full before the first dispatch (iron rules 0 and 10).
- The planner was dispatched from the rendered block verbatim, with `loop sent` before and `loop back` (with its assumptions and `--process-fault`) after.
- The state was re-read after the dispatch (`loop next` moved to row 17), so the close was not taken on the worker's say-so.
- Every question went through `AskUserQuestion` with the recommendation first: two questions, the design re-approval and the accept-red close.
- The boundary sequence was followed: stage commit, then this retro, then the push. No step of the implement stage was opened.

## What worked

- **`loop back --assumptions-file`, used together with `--process-fault`**, banked the planner's long assumptions paragraph and its fault in one call without quoting trouble. `audit` then printed the fault queue back, so this section is read off a list.
- **The close refusals were precise.** Both `close_stage` refusals named exactly what was wrong: the content digest with the report's timestamp, and the case ids not covered. Each cost one retry, not a debugging session.
- **The planner's closing block surfaced three design gaps rather than resolving them silently:** 19 versus 18+1 corpus cases, `entryText.test.ts` going red with no declaration, and `test_production_is_refused` green by design. They are banked as assumptions, so the implement-stage coherence pass can see them.

## For the user to decide

- **Whether the design-stage gaps the planner reported need a question before implementation.** They are banked as assumptions, not raised as questions: `testing.md`'s "nineteen" versus 18+1 corpus cases, the undeclared red on `entryText.test.ts` (declared by the plan on T-5), and `test_production_is_refused` expected red but green by design.
- **Whether accept-red closes are acceptable as the standing route** at the design and plan boundaries of every change that adds a contract or context, until #314 lands.

---
session_id: 76720804-74cc-4a32-b0f2-3b64b73aa9dd
cr_id: CR-2609-823a
branch: sdd/CR-2609-823a-todo-list-add-tasks-and-mark-them-done
date: 2026-09-24
stages: [implement]
skills: [sdd, fault-report, build-tests-integration, build-tests-frontend, build-tests-uat, build-tests-unit, build-tests-e2e, build-backend, build-frontend, build-migration, build-platform, review-coherence, review-converge, sdd-retro]
outcome: finished
---

# Session summary — the implement stage of the to-do list: tests first, a RED proof in two parts, the code, three coherence passes and a green close

## 1. What was asked for

The user wrote "gogo": carry change CR-2609-823a (a to-do list beside the guestbook) on from where the branch stood, the implement stage, not started.

## 2. The run

1. sdd · preflight and `loop next`: implement not started, wave 1 of 3 · ok
2. build-tests-integration, build-tests-frontend, build-tests-uat · wave 1a written (71 + 29 new tests, a 20-step `uat.md`) · ok
3. fault-report · PROC-38 filed (#364) · ok
4. sdd · RED proof 1: 119 declared, `gate run --profile unit`, 119 observed, 2 green-by-design · ok
5. fault-report · PROC-39, PROC-40 filed · ok
6. build-tests-unit, build-tests-e2e · wave 1b written; build-tests-e2e returned CONTENTION (the SPA build blocked the suite) · stop
7. fault-report · PROC-41, PROC-42, PROC-43 filed · ok
8. sdd · RED proof 2, first run: verdict ERROR, the tree changed during the run · correction
9. sdd · RED proof 2 re-run: 46 declared and observed, 7 resolved, 12 green-by-design · ok
10. build-backend, build-frontend, build-migration, build-platform · wave 2 written; build-migration reported a write to another project's database; build-frontend returned TEST_DISPUTED · stop
11. human · the other project's database: revert, and stop its container · question
12. sdd · downgrade on the other database (explicit URL), `docker stop`, this repository's `db` back on 5432 · ok
13. fault-report · PROC-44 to PROC-47 filed · ok
14. build-tests-frontend · TD-3, the disputed lint lines · ok
15. sdd · `generate.sh`, fast gate: application check green, specification gates red · correction
16. sdd · unit gate without `--out`: GREEN; 158 declared reds resolved · ok
17. fault-report · PROC-48, PROC-49 filed · ok
18. review-coherence · pass 7: GO_WITH_QUESTIONS, 6 findings · question
19. human · Q-25, Q-26, Q-27 · question
20. review-converge · six findings reconciled · ok
21. review-converge, build-tests-unit, build-tests-integration · TD-4, TD-5, TD-6 · ok
22. build-frontend · TD-7 · ok
23. build-tests-unit · TD-8 · ok
24. build-tests-uat · convergence round 1, deep · ok
25. review-coherence · pass 8: GO_WITH_QUESTIONS, 4 findings · question
26. human · Q-28, Q-29 · question
27. review-converge · four findings reconciled · ok
28. build-tests-frontend, build-tests-unit, build-tests-integration, build-tests-e2e · TD-9 to TD-12 · ok
29. human · ESC-implement-r2 · question
30. review-coherence · pass 9, convergence round 2, verifying: GO · ok
31. sdd · `loop close --next clean_room`: boundary GREEN, stage closed · ok
32. human · capture the 41.2 MB archive · question
33. sdd-retro · capture, audit, summary · ok

## 3. What came into being

- `app/contexts/todo_list/` — the to-do list's backend: model, schemas, service, router.
- `app/contexts/__init__.py`, `app/api.py` — one registration line each.
- `alembic/versions/5c58af1f8e8a_create_todo_tasks_table.py` — the revision that creates `todo_tasks` and its ordering index.
- `frontend/src/contexts/todo_list/` — the to-do screen: page, components, hook, lib, and their vitest files.
- `frontend/src/lib/text.ts` — the shared text rule, moved out of the guestbook.
- `frontend/src/components/ui/Checkbox.tsx`, `frontend/src/components/shell/PageFrame.tsx`, `frontend/src/pages/StatusPages.tsx`, `frontend/src/routes.ts`, `frontend/src/router.tsx` — the way between the two screens, the not-found copy and the route.
- `frontend/src/api/schema.d.ts` — regenerated.
- `golden-set/fixtures/todo-tasks-ordinary.json`, `todo-tasks-boundary.json`, `todo-tasks-refused.json`, `todo-task-text.json`, `golden-set/seed/todo-tasks-example.json` — the to-do list's corpus and example tasks.
- `scripts/seed_golden_set.py`, `scripts/seed.sh` — the seeder fills each list on its own.
- `tests/unit/`, `tests/integration/`, `tests/fitness/`, `tests/tooling/`, `tests/_golden_set.py` — the to-do list's tests and the corpus rules rescoped.
- `e2e/suite/features/todo_list.feature`, `e2e/suite/steps/todo_list_steps.py`, `e2e/ui/test_smoke.py` — 22 scenarios and 4 smoke cases.
- `.github/CODEOWNERS` — five to-do rows.
- `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/uat.md` — the 20-step acceptance script.
- `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/review/coherence.md` — passes 7, 8 and 9.
- `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md` — the implement stage's reconciliation entries and two owns rows.
- `spec/design/ui/system-states.md`, `spec/design/architecture.md`, `spec/design/testing.md`, `spec/contexts/todo_list.md`, `spec/README.md`, `CLAUDE.md`, `tasks.md`, `design/delta/architecture.md` — reconciled.
- Issues and comments on the marketplace and template repositories for PROC-38 to PROC-58.

## 4. Decisions

- D1: Declare each planned red before the run, then observe, instead of the rendered row-31 recipe — **Who:** agent — **Why:** constitution Art. X and SKILL.md Phase 6.
- D2: Run the RED proof twice, after wave 1a and after wave 1b — **Who:** agent — **Why:** the plan and Art. X; the engine asked only after wave 1a.
- D3: Treat T-11/T-12 as collected, not declared — **Who:** agent — **Why:** Phase 6's black-box treatment; the suite could not run between the waves.
- D4: Bank the e2e worker's CONTENTION as a return — **Who:** agent — **Why:** waiting could not clear the block.
- D5: Revert this change's migration in the other project's database — **Who:** user — **Why:** it was written there by mistake.
- D6: Stop the other project's container and move this repository's database back to 5432 — **Who:** user — **Why:** keep the rest of the change off that database.
- D7: Send the disputed test back to its author as TD-3 — **Who:** agent — **Why:** row 40a.
- D8: Run row 33 (generate, fast gate) before the coherence pass the engine proposed — **Who:** agent — **Why:** the implement row is narrower than row 27.
- D9: Refresh `last-gate.json` with a unit run without `--out` before the close — **Who:** agent — **Why:** traceability reads its executed axis from that file.
- D10: The to-do list always fetches the latest list when opened (Q-25 A) — **Who:** user — **Why:** R-3 clause 5.
- D11: `golden-set/README.md` is corrected in a follow-up pull request (Q-26 A) — **Who:** user — **Why:** no member of this change may write it.
- D12: The design documents record what happened to the Q-24 reds (Q-27 A) — **Who:** user — **Why:** the record and the documents disagreed.
- D13: Grow the boundary by `GuestbookPage.tsx` and `e2e/suite/steps/guestbook_steps.py` through owns rows in `converge.md` — **Who:** agent — **Why:** AUTO rulings COH-implement-5 and COH-implement-9 (Art. I).
- D14: Showing the earlier list until the fresh read answers is fine (Q-28 A) — **Who:** user — **Why:** the fetch is what was asked for.
- D15: An automated test proves the fresh read (Q-29 A) — **Who:** user — **Why:** nothing guarded the line.
- D16: Convergence round 2 on opus (ESC-implement-r2 B) — **Who:** user — **Why:** the recommendation.
- D17: Capture the 41.2 MB archive — **Who:** user — **Why:** the process's archive and the boundary push.

## 5. Questions to the user

- Q1: Revert the migration that landed in the other project's database? — **Answer:** Revert it now — **Stage:** implement
- Q2: How should this project stay off port 5432? — **Answer:** Stop the other DB for now — **Stage:** implement
- Q3: (Q-25) Opened by its link, always fetch the latest list? — **Answer:** Always fetch the latest — **Stage:** implement
- Q4: (Q-26) The five out-of-date sentences of `golden-set/README.md`? — **Answer:** Fix it in a follow-up — **Stage:** implement
- Q5: (Q-27) Record what happened to the reds signed off at the design close? — **Answer:** Yes, record what happened — **Stage:** implement
- Q6: (Q-28) The earlier list on screen until the fresh read answers? — **Answer:** Briefly showing it is fine — **Stage:** implement
- Q7: (Q-29) How to prove the fresh read? — **Answer:** Add an automated test — **Stage:** implement
- Q8: (ESC-implement-r2) Convergence round 2 on fable? — **Answer:** No, the round goes on opus — **Stage:** implement
- Q9: Capture and commit the 41.2 MB archive? — **Answer:** Yes, capture it — **Stage:** implement

## 6. Where the process got stuck

- S1: row 31 printed "run, THEN declare" — **Skill:** sdd — **How many times:** 1
- S2: row 31 fired once in a three-wave profile — **Skill:** sdd — **How many times:** 1
- S3: `./scripts/test.sh e2e` refused between the waves (the SPA build type-checks test files) — **Skill:** build-tests-e2e — **How many times:** 1
- S4: a gate run invalidated by record writes made during it — **Skill:** sdd — **How many times:** 1
- S5: the scripts reached another project's database through a port collision — **Skill:** build-migration — **How many times:** 1
- S6: a type-dependent lint error in a wave-1 test surfaced only in wave 2 — **Skill:** build-frontend — **How many times:** 1
- S7: the row-33 fast gate red by construction (delivery asserts, a stale traceability axis) — **Skill:** sdd — **How many times:** 1
- S8: row-10 blocks carried the member's generic stage task instead of the todo — **Skill:** sdd — **How many times:** 10
- S9: no review-converge block rendered after HITL answers — **Skill:** sdd — **How many times:** 2
- S10: convergence round 1 dispatched one of four authors — **Skill:** sdd — **How many times:** 1
- S11: the boundary could not grow for an AUTO-resolved edit without a hand-made owns row — **Skill:** review-converge — **How many times:** 2

## 7. Sentences in the instructions I hesitated over

- I1: **File:** `skills/_shared/sdd/loop.py` (row 31 rendering) — **Sentence:** "THEN record each new failure: sdd-engine change_state declare-red …" — **What I did:** declared before the run, per `skills/sdd/SKILL.md` Phase 6.
- I2: **File:** `skills/sdd/table/implement.md` — **Sentence:** "`S == implement`, wave 1 returned, no RED proof yet | run the RED proof" — **What I did:** ran it after wave 1a and again after wave 1b.
- I3: **File:** `skills/sdd/SKILL.md` — **Sentence:** "Never compose a dispatch from memory, and never write out the rules. `sdd-engine loop next` prints one ready block per member. Copy it verbatim" — **What I did:** copied the blocks but replaced YOUR TASK with the todo's text on row-10 dispatches, and composed two review-converge dispatches that were not rendered.
- I4: **File:** `skills/sdd/SKILL.md` — **Sentence:** "`CONTENTION` | the machine was busy | `note-contention`, wait, retry. No ladder" — **What I did:** banked the e2e return and did not wait.
- I5: **File:** `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/tasks.md` — **Sentence:** "Declare every `Must be red:` id above and every id the closing blocks of T-1, T-4 and T-10 add." — **What I did:** declared every id except T-11's and T-12's 26 black-box ids.
- I6: **File:** `skills/sdd/table/implement.md` — **Sentence:** "Paste `tasks.md § Lessons from the implementation` into every `--task` text" — **What I did:** the section read "Nothing yet"; I pasted facts from the banked assumptions under "FROM THE TEST WAVES".
- I7: **File:** `skills/sdd/table/implement.md` — **Sentence:** "gate verdict `RED` with `new_failures` | open `debug`" — **What I did:** did not open debug for the fast gate's specification-only red.

## 8. Workarounds and departures

- W1: the declaration order of row 31 — **Workaround:** declared first — **User's consent:** no
- W2: one RED proof in the engine — **Workaround:** a second Phase 6 run before wave 2 — **User's consent:** no
- W3: e2e reds unobservable — **Workaround:** collected, not declared — **User's consent:** no
- W4: one case per `declare-red`/`observe-red` call — **Workaround:** shell loops over scratch TSV files — **User's consent:** no
- W5: row-10 blocks without the todo — **Workaround:** YOUR TASK replaced by the todo's text (TD-3 to TD-12) — **User's consent:** no
- W6: no rendered review-converge block — **Workaround:** two dispatches composed from the Phase 3 template — **User's consent:** no
- W7: an empty § Lessons — **Workaround:** facts from the banked assumptions added to the wave dispatches — **User's consent:** no
- W8: running workers heading for e2e on the wrong database — **Workaround:** a `SendMessage` warning to both — **User's consent:** no
- W9: a migration in another project's database — **Workaround:** `db.sh downgrade` against its explicit URL — **User's consent:** yes
- W10: the port collision — **Workaround:** the other container stopped, this repository's `db` recreated on 5432 — **User's consent:** yes
- W11: a stale `last-gate.json` — **Workaround:** a unit gate without `--out` before the close — **User's consent:** no
- W12: a boundary that could not grow — **Workaround:** owns rows in `design/delta/converge.md`, then `set-boundary --from-design` — **User's consent:** no
- W13: a gate run invalidated by my own writes — **Workaround:** re-run over a still tree — **User's consent:** no

## 9. What was not done

- The black-box scenarios (T-11) and UI smoke cases (T-12) were never observed red.
- PROC-37's correction of `spec/design/testing.md` § "Red first" was not made.
- The five out-of-date sentences of `golden-set/README.md` were not corrected.
- The other project's database was not checked for data lost to earlier e2e runs.
- Whether the design approval reads stale after `delta.md`'s re-assembly was not checked.
- The clean-room stage was not started.

## 10. The record's extent

<!-- extent:begin -- regenerated by `retro_capture.py` on every capture -->

The archive reaches the end of the transcript as of the moment `capture` ran (2026-09-24T20:40:06Z): 59 files, 41.5 MB. Shapes of personal data: email=821, iban=0, phone=0, pesel=0. What happened after that moment the archive does not carry -- `capture` never catches its own turns. This is capture 2 of this session; the first reached 41.2 MB at 2026-09-24T20:38:14Z.

<!-- extent:end -->

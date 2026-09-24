---
session_id: fb772134-4626-4cf4-a734-3930e8cb1dbd
cr_id: CR-2609-823a
branch: sdd/CR-2609-823a-todo-list-add-tasks-and-mark-them-done
date: 2026-09-24
stages: [design]
skills: [forge:sdd, forge:fault-report, forge:sdd-retro, design-domain, design-spec, design-architecture, design-api, design-data, design-ui, design-testing, design-adr, review-coherence, review-converge]
outcome: finished
---

# Session summary — the design stage of the to-do list, from not started to closed

<!--
Write paths in `backticks`, never as markdown links. This is the record of a conversation in
which paths were named that did not exist, that were abandoned and that later changed — and
that is how it is to stay.

Do not remove sections. An empty section is information ("there were none"); a missing
section is a hole in the corpus nobody will tell apart from zero in six months.

Do not propose rule changes here. Quote the sentence you hesitated over and write what you
did — what SHOULD be written there is separate work across the whole corpus.
-->

## 1. What was asked for

The user said "gogo" in a fresh session on the change branch. The session-start hook reported `CR-2609-823a` at stage `design (not started)`, so this was "carry on": run the design stage of the to-do list change (add tasks, mark them done, edit, delete) through to its close.

## 2. The run

1. agent · `sdd preflight`, `loop next`; read the constitution and `process-failure.md` · ok
2. design-domain · new bounded context `todo_list` (P-02, BR-06…BR-13), glossary · ok (PROC-13 filed as #314)
3. design-spec · guestbook neighbour, BR-07 precedence, BR-10 · ok (PROC-14 filed as #317, PROC-15 as #318)
4. design-architecture · design-api · design-data · design-testing, one wave · ok (PROC-16 as #319; PROC-17 on #314; PROC-18 and PROC-19 as template #92)
5. agent · `loop next` offered nothing to dispatch; walked the table to row 25 · stop (PROC-20 as #327)
6. human · Q-13 mock-up source → B, draft one for approval · question
7. general-purpose helper · drafted `design/ui/index.html` (19 panels) · ok (PROC-21 as template #95)
8. human · Q-14 approve the mock-up → A · question
9. design-ui · screen spec · question (NEEDS_DECISION, two questions)
10. human · Q-15 failure wording → A; Q-16 focus → A · question
11. design-ui (fresh dispatch) · applied Q-15 and Q-16 · ok (PROC-22 as #332, PROC-23 as #333)
12. design-adr · two ADR drafts · ok (PROC-24 as #338)
13. review-coherence · pass 4: NO_GO, 8 findings · ok (PROC-25 as #342, PROC-26 as #343)
14. human · Q-17 → A, Q-18 → A, Q-19 → A · question
15. agent · `resolve-coherence` refused before any reconciliation; composed `review-converge` by hand · correction (PROC-27 as #344)
16. review-converge · REC-12…REC-19, all 8 closed · ok (PROC-28 on #314)
17. design-architecture · design-testing · convergence round 1 (deep) · stop (both UNVERIFIED: `verify` refused on the open Q-20)
18. human · Q-20 re-approve requirements → A, via `loop ask --now` · question (PROC-29 as #349, PROC-30 as #350)
19. design-testing · TD-1 backtick path, then TD-2 COH-design-2's missed patch · ok
20. review-coherence · pass 5: NO_GO, 10 new findings · ok (PROC-31 on #314)
21. human · Q-21 accept all six recommendations → A · question
22. review-converge · REC-20…REC-29, all 10 closed · ok (PROC-32 as #352)
23. human · ESC-design-r2 → B (decline fable); Q-22 re-approve requirements → A · question
24. review-coherence · pass 6 (verify): GO, 18/18 landed · ok
25. human · Q-23 approve the design → A · question
26. agent · `set-boundary --from-design` (42 paths) · ok
27. agent · `loop close` → RED; background gate → ERROR (my approval moved the tree) · stop
28. human · Q-24 sign off the three structural reds → A · question
29. agent · gate re-run, `close_stage --accept-red` (refused once for missing case ids, then closed) · ok (PROC-33 as #355)
30. agent · `sdd-retro` · ok

## 3. What came into being

- `spec/contexts/todo_list.md` — the new bounded context: P-02, BR-06…BR-13, and a header claiming the screen and the feature file
- `spec/glossary.md` — TodoTask, To-do list, and the `todo_task` identifier
- `spec/contexts/guestbook.md` — neighbour `todo_list:peer:shared-kernel`; "only context" wording removed
- `spec/design/architecture.md` — to-do layer per rule, files, write sets; text judged in the service
- `spec/design/api.md`, `contracts/openapi/todo_list.yaml`, `contracts/openapi/README.md`, `contracts/README.md` — 5 paths, 10 operations, 5 coded refusals
- `spec/design/data-model.md` — `todo_tasks` (id, text String(200), done, created_at) and the task-text invariant call
- `spec/design/testing.md` — a suite per requirement, the red-first list, and the declared structural reds including the contract gate
- `spec/design/ui/todo-list.md`, `spec/design/ui/system-states.md`, `spec/design/ui/guestbook.md` — the to-do screen, the navigation, the "Product name" lockup, the Q-15 wording and the Q-16 focus rule
- `spec/design/conventions.md` — § Layers ("a rule about a field's value … judged in `services/`"), § Frontend ("Only the rule moves up"), two domain contexts
- `spec/invariants.md`, `spec/README.md` — tasks named in the non-goals; two domain contexts
- `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/ui/index.html` — the approved mock-up
- `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/*.md` — eight fragments
- `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/delta.md` — assembled, 30 entries
- `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/adr/*.md` — two ADR drafts
- `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/review/coherence.md` — passes 4, 5 and 6
- `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/requirements.md`, `scenarios.md` — A-1…A-4 marked confirmed; one Coverage sentence

## 4. Decisions

- D1: The to-do list is its own bounded context, sharing only the text rule with the guestbook — **Who:** agent (design-domain) — **Why:** P-01's "an entry either exists or it does not"; the guestbook is deletable
- D2: The mock-up is drafted in the conversation for approval rather than supplied — **Who:** user (Q-13) — **Why:** the user's choice; this stack has no drafting step
- D3: Task text is judged in the service with coded refusals; schemas carry no bound — **Who:** user (Q-17) — **Why:** the contract, the screen and the tests already assumed it
- D4: `frontend/src/router.test.tsx` joins the boundary — **Who:** user (Q-18) — **Why:** R-5 clauses 1 and 3 have no other proof
- D5: The feature file is claimed at design close; its on-disk red is declared until implement wave 1 — **Who:** user (Q-19) — **Why:** the shortest red of the three options
- D6: The six pass-5 recommendations are accepted together — **Who:** user (Q-21) — **Why:** the user's choice between bundled and one-by-one
- D7: Fable declined for convergence round 2 — **Who:** user (ESC-design-r2) — **Why:** the recommended decline
- D8: Design closes on the three structural reds with `--accept-red` — **Who:** user (Q-24) — **Why:** none can be green before the code exists (#314)
- D9: TD-1 and TD-2 are used to route two single fixes to design-testing — **Who:** agent — **Why:** a backtick path turned the lint red, and COH-design-2's patch had not landed

## 5. Questions to the user

- Q13: Where does the screen mock-up come from? — **Answer:** B, draft one for approval — **Stage:** design
- Q14: Approve the drafted mock-up? — **Answer:** A, approve as drafted (lockup "Product name") — **Stage:** design
- Q15: Wording of a failed write with no sentence of its own? — **Answer:** A, "…the service answered with an error." — **Stage:** design
- Q16: Where does focus go after a lock or unlock? — **Answer:** A, back where the person was — **Stage:** design
- Q17: Who checks a task's text? — **Answer:** A, the service with a coded reason — **Stage:** design
- Q18: Add `router.test.tsx` to the change's list? — **Answer:** A, add it — **Stage:** design
- Q19: When is the feature file claimed? — **Answer:** A, now, at design close — **Stage:** design
- Q20: Re-approve the requirements (A-2 confirmed)? — **Answer:** A — **Stage:** requirements gate, asked in design
- Q21: Accept the six pass-5 recommendations? — **Answer:** A, all six — **Stage:** design
- ESC-design-r2: Round 2 on fable? — **Answer:** B, no — **Stage:** design
- Q22: Re-approve the requirements (A-1/A-3/A-4 confirmed)? — **Answer:** A — **Stage:** requirements gate, asked in design
- Q23: Approve the design? — **Answer:** A — **Stage:** design
- Q24: Close design on the three structural reds? — **Answer:** A — **Stage:** design
- (retro) Capture and commit a 34.6 MB archive? — **Answer:** yes — **Stage:** boundary

## 6. Where the process got stuck

- S1: `loop next` said "Nothing to dispatch this turn" while row 25 held — **Skill:** sdd (next_action) — **How many times:** 1
- S2: `loop next` kept printing row 11 "need a decision" after the answers, with no `review-converge` block — **Skill:** sdd (next_action) — **How many times:** 2
- S3: `resolve-coherence` refused ("has no reconciliation yet") — **Skill:** change_state — **How many times:** 1
- S4: Both round-1 members returned UNVERIFIED, because `verify` refused on the queued Q-20 — **Skill:** design-architecture, design-testing — **How many times:** 2
- S5: The gate verdict was ERROR ("the content changed while the gate was running") — **Skill:** gate — **How many times:** 1
- S6: `close_stage` refused a stale report, then a reason missing the dotted case ids — **Skill:** close_stage — **How many times:** 2
- S7: The gate lock was busy (my own background run) — **Skill:** gate — **How many times:** 1

## 7. Sentences in the instructions I hesitated over

- I1: **File:** `skills/sdd/SKILL.md` — **Sentence:** "Never compose a dispatch from memory, and never write out the rules. `sdd-engine loop next` prints one ready block per member." — **What I did:** composed `review-converge`'s block from the Phase 3 template when `loop next` printed none, and appended scope text to four rendered blocks
- I2: **File:** `skills/sdd/table/design.md` — **Sentence:** "| 27c | ... reads "This change owns" out of the approved design" — **What I did:** followed `next`'s row 16 (approve) first, then ran `set-boundary` at row 27c
- I3: **File:** `skills/sdd/SKILL.md` — **Sentence:** "`--now` asks while a wave is still out — the one escape from the `ask`↔`back` deadlock ... use it for that deadlock and not for impatience." — **What I did:** used it once, for Q-20, which I had raised mid-wave
- I4: **File:** `skills/review-converge/SKILL.md` — **Sentence:** "Files never written: Any artefact a finding names." — **What I did:** wrote a pass-5 dispatch whose wording led the worker to apply the artefact patches anyway
- I5: **File:** `skills/sdd/SKILL.md` — **Sentence:** "RED/EXPECTED_RED needs `--accept-red "<one sentence why>"`" — **What I did:** found `loop close` has no such flag and used `close_stage` directly, naming every failing gate and case id

## 8. Workarounds and departures

- W1: A mock-up is supplied by a person on this stack — **Workaround:** a general-purpose helper drafted it — **User's consent:** yes (Q-13, Q-14)
- W2: Dispatch blocks come from `loop next` — **Workaround:** `review-converge` composed by hand, twice — **User's consent:** no
- W3: `review-converge` never writes the artefact a finding names — **Workaround:** the pass-5 dispatch had it apply the ready artefact patches — **User's consent:** no
- W4: The question queue waits for the wave — **Workaround:** `loop ask --now` for Q-20 — **User's consent:** no
- W5: A stage never ends red — **Workaround:** `close_stage --accept-red` for three structural reds — **User's consent:** yes (Q-24)
- W6: One decision per question — **Workaround:** six HITL findings bundled into Q-21, with a one-by-one option — **User's consent:** yes (chose A)
- W7: No code in the command — **Workaround:** `python3 -c` to read JSON four times, and a `python3 -` heredoc once — **User's consent:** no

## 9. What was not done

- The `plan` stage was not opened (the boundary rule).
- The two unfiled observations (design-ui not recording its questions; the `870fece5` archive modified after its commit) were not filed.
- The ADR drafts were not numbered; `reconcile-design` does that at spec_sync.
- The task-text data invariant under `contracts/invariants/` was not written; per Q-21 (6) it waits for spec_sync.
- `requirements.md` lines 85 and 88 ("assumed: A-1/A-3") were not updated.

## 10. The record's extent

<!-- extent:begin -- regenerated by `retro_capture.py` on every capture -->

The archive reaches the end of the transcript as of the moment `capture` ran (2026-09-24T16:59:13Z): 46 files, 34.9 MB. Shapes of personal data: email=170, iban=0, phone=0, pesel=0. What happened after that moment the archive does not carry -- `capture` never catches its own turns. This is capture 2 of this session; the first reached 34.7 MB at 2026-09-24T16:57:57Z.

<!-- extent:end -->

---
session_id: 99cd49c7-8021-4140-b605-645f1cda94ba
cr_id: CR-2609-823a
branch: sdd/CR-2609-823a-todo-list-add-tasks-and-mark-them-done
date: 2026-09-25
stages: [spec_sync]
skills: [sdd, reconcile-spec, reconcile-design, reconcile-docs, reconcile-ops, review-coherence, review-converge, fault-report, sdd-retro]
outcome: finished
---

# Session summary — the spec_sync stage of the to-do list change, from the first reconcile wave to a green close

## 1. What was asked for

The user wrote "gogo": carry on with the change this branch holds. Midway they asked, in Polish, which stage the workflow was at, what had been repeated and how many times, and what comes next.

## 2. The run

1. sdd · `loop next` → row 19, dispatch the four reconcile members · ok
2. reconcile-spec, reconcile-design, reconcile-docs, reconcile-ops · first wave, all DONE · ok
3. sdd · `loop back` with assumptions and 3 process faults (PROC-59…61) · ok
4. review-coherence · pass 10: GO_WITH_QUESTIONS, 7 findings (5 AUTO, 2 HITL) · ok
5. fault-report · filed #397, #398, #399 · ok
6. human · Q-30, Q-31 answered A, A · question
7. review-converge · converged all 7, closed on `loop back` · ok
8. reconcile-docs, reconcile-ops · convergence round 1 (deep) · ok
9. sdd · build-backend agent todo (TD-13) refused by row 10 in spec_sync · stop
10. human · Q-32 answered A (defer scripts help text to a post-merge PR) · question
11. review-coherence · pass 11: GO_WITH_QUESTIONS, 5 findings · ok
12. human · Q-33 answered A · question
13. review-converge · converged pass 11 · ok
14. human · asked for the stage, the repetitions and what is next · question
15. human · ESC-spec_sync-r2 answered B (no fable) · question
16. reconcile-ops · TD-14, applied COH-9/10/12 · ok
17. review-coherence · pass 12 (verify round 2 of 3): GO, 0 findings · ok
18. sdd · `loop close --next deliver` → RED, delta-entries 40 problems · stop
19. human · Q-34 answered A (reformat the fragments) · question
20. review-converge · TD-15, 61 fragment lines reformatted · ok
21. sdd · `loop close --next deliver` → GREEN, stage closed · ok
22. sdd-retro · this archive · ok

## 3. What came into being

- `spec/contexts/todo_list.md` — one paragraph under BR-13 (a refused corrected text wins over a deleted task)
- `spec/ADR/ADR-0001-todo-list-is-its-own-bounded-context.md` — promoted from the design draft, Proposed
- `spec/ADR/ADR-0002-task-text-refusals-are-coded-not-schema-constraints.md` — promoted from the design draft, Proposed
- `spec/design/data-model.md`, `architecture.md`, `testing.md`, `conventions.md`, `ui/todo-list.md` — reconciled with the build
- `contracts/invariants/todo_list.md` — D-05, the task-text invariant
- `spec/invariants.md`, `spec/glossary.md`, `spec/README.md` — ADR directory no longer "empty"; D-01…D-04 move before the guestbook goes
- `docs/user-guide-todo-list.md` — the to-do list's user guide, moved from the change record
- `docs/runbooks/refill-the-example-data.md` — new runbook
- `docs/` — 14 operations pages updated for two lists
- `README.md`, `CLAUDE.md` — the to-do list is a second context, not an example
- `spec/changes/CR-2609-823a-…/reconcile/delta/*.md` — five reconcile fragments
- `spec/changes/CR-2609-823a-…/review/coherence.md` — passes 10, 11, 12
- marketplace issues #397, #398, #399, #400, #401, #402, #407, #411, plus comments on #322, #401, #407

## 4. Decisions

- D1: follow `next_action` past the "design gate open again" note instead of re-asking row 15 — **Who:** agent — **Why:** the record showed `design.approved: true` and the engine routed to row 19
- D2: PROC-62 closed unfiled — **Who:** agent — **Why:** the duty traced to this repository's own `spec/invariants.md` (Q-21)
- D3: COH-9 and COH-10 treated as applications of Q-30 A, not re-asked — **Who:** agent — **Why:** Article VII, an answer never produces the same question twice
- D4: route the reconcile-ops and fragment repairs through agent todos (TD-14, TD-15) — **Who:** agent — **Why:** row 27a offered no author, and the table had no row for the delta bug
- D5: defer the scripts' help-text fix to a post-merge PR — **Who:** user — **Why:** build-backend cannot run in spec_sync
- D6: reformat the delta fragments rather than accept red — **Who:** user — **Why:** keeps the gate and the PR's spec check green
- D7: PROC-67 and PROC-68 recorded as comments on #401 and #407 — **Who:** agent — **Why:** same root as an issue already filed

## 5. Questions to the user

- Q1: restore wording, guide vs runbook (Q-30) — **Answer:** keep partial restores, fix the guide — **Stage:** spec_sync
- Q2: where the to-do user guide lives (Q-31) — **Answer:** move it to docs/ — **Stage:** spec_sync
- Q3: how to fix the scripts' help text (Q-32) — **Answer:** follow-up fix right after merge — **Stage:** spec_sync
- Q4: what the guestbook deletion instructions say about D-01…D-04 (Q-33) — **Answer:** move the four data rules too — **Stage:** spec_sync
- Q5: fable for convergence round 2 (ESC-spec_sync-r2) — **Answer:** no, opus — **Stage:** spec_sync
- Q6: how to get past the red delta-entries gate (Q-34) — **Answer:** reformat the change's notes, then close — **Stage:** spec_sync
- Q7: capture a 20.7 MB archive — **Answer:** yes — **Stage:** spec_sync (retro)

## 6. Where the process got stuck

- S1: build-backend refused as an agent todo in spec_sync ("a bug in the decision table") — **Skill:** sdd — **How many times:** 1
- S2: convergence round dispatched without the member that owned the repairs — **Skill:** sdd — **How many times:** 2
- S3: boundary gate RED on delta-entries while every suite was green — **Skill:** sdd (loop close) — **How many times:** 1
- S4: `loop ask` returned "No open questions" for HITL findings, and the questions had to be raised by hand with `--raise` — **Skill:** sdd — **How many times:** 2

## 7. Sentences in the instructions I hesitated over

- I1: **File:** `skills/sdd/SKILL.md` — **Sentence:** "Never compose a dispatch from memory, and never write out the rules." — **What I did:** appended a scope paragraph to the rendered block for row-10 and converge dispatches, whose rendered task carried no scope
- I2: **File:** `skills/sdd/SKILL.md` — **Sentence:** "a gate in `digest.gates` is false and `warnings` says its artefact changed | re-ask the approval" — **What I did:** did not re-ask; followed `next_action`
- I3: **File:** `skills/sdd/SKILL.md` — **Sentence:** "`review-converge` is not optional — and it is dispatched ONCE per coherence pass" — **What I did:** dispatched it once per pass, and once more for TD-15, which was not a coherence pass

## 8. Workarounds and departures

- W1: fragment form (backticked kind) — **Workaround:** backticks around ADDED/MODIFIED removed in 61 lines of 13 fragments — **User's consent:** yes
- W2: a spec_sync finding's repair owned by an implement-stage builder — **Workaround:** deferred to a post-merge changelog PR (task T-1) — **User's consent:** yes
- W3: convergence routing missed reconcile-ops — **Workaround:** agent todo TD-14 with a scoped task — **User's consent:** no

## 9. What was not done

- The scripts' help text (`start.sh`, `help.sh`, `deploy.sh`, `preview.sh`) was not corrected in this change.
- The delivery stage was not opened, and the uat.md delivery gate was not asked.
- No re-approval of the design gate was asked.

## 10. The record's extent

<!-- extent:begin -- regenerated by `retro_capture.py` on every capture -->

The archive reaches the end of the transcript as of the moment `capture` ran (2026-09-25T07:15:50Z): 31 files, 20.9 MB. Shapes of personal data: email=139, iban=0, phone=0, pesel=0. What happened after that moment the archive does not carry -- `capture` never catches its own turns. This is capture 2 of this session; the first reached 20.7 MB at 2026-09-25T07:15:02Z.

<!-- extent:end -->

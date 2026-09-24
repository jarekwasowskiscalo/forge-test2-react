---
session_id: 870fece5-b8f9-4a47-84da-b3456aa1de97
cr_id: CR-2609-823a
branch: sdd/CR-2609-823a-todo-list-add-tasks-and-mark-them-done
date: 2026-09-24
stages: [requirements]
skills: [sdd, cr-impact, fault-report, cr-brainstorm, cr-requirements, cr-scenarios, review-coherence, review-converge, sdd-retro]
outcome: finished
---

# Session summary — the requirements stage of the to-do list, from the impact measurement to an approved requirements.md

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

The user wrote "gogo" to carry on change CR-2609-823a, a to-do list in which anybody adds a task, marks it done and edits or deletes it. The change was at the start of its requirements stage. The session ran that stage to its close: impact, brainstorm, requirements, scenarios, three coherence passes with their convergence, the approval, and the boundary gate.

## 2. The run

1. sdd · preflight and `loop next`, row 14a: dispatch cr-impact · ok
2. cr-impact · `impact.md`, 9 signals lit and 2 absent, tier p3 · ok
3. fault-report · PROC-3 filed as #296 · ok
4. cr-brainstorm · round 1, Q-1 to Q-4 · question
5. human · Q-1 to Q-4, all A · ok
6. cr-brainstorm · round 2, Q-5 to Q-8 · question
7. human · Q-5 to Q-8, all A · ok
8. cr-brainstorm · read-back, Q-9 · question
9. human · Q-9 A: summary and eight assumptions confirmed · ok
10. sdd · signals re-recorded with `tooling_touched` lit, after Q-8 · correction
11. fault-report · PROC-4 filed as #298 · ok
12. cr-requirements · `requirements.md` with 11 requirements; NEEDS_DECISION on D1 to D3 · question
13. human · Q-10 to Q-12 (asked with `ask --now`), all A · ok
14. fault-report · PROC-5 filed as #299 · ok
15. cr-scenarios · `scenarios.md`, 53 seeds · ok
16. fault-report · PROC-6 filed as #300 · ok
17. review-coherence · pass 1: NO_GO, 6 findings · stop
18. sdd · `loop ask --raise` refused: the stage had asked 12 of 12 questions · stop
19. review-converge · dispatched by hand; 6 findings resolved, A-1 and A-2 written as named assumptions · ok
20. fault-report · PROC-7 (#305), PROC-8 (#306) and PROC-9 (#309) filed · ok
21. cr-impact, cr-requirements, cr-scenarios · convergence round 1, deep · ok
22. fault-report · PROC-10 filed as #310 · ok
23. review-coherence · pass 2: GO_WITH_QUESTIONS, 3 findings · question
24. review-converge · dispatched by hand; 3 findings resolved, A-3 and A-4 written as named assumptions · ok
25. fault-report · PROC-11 filed as #311 · ok
26. human · ESC-requirements-r2 declined (B) · ok
27. review-coherence · pass 3, verify: GO · ok
28. human · approved `requirements.md`, including A-1 to A-4 · ok
29. sdd · `add-requirements` (11), then `loop close`: RED on `recorded-decision` · stop
30. review-converge · dispatched by hand; fixed the ADR line, reworded the retention non-goal · ok
31. sdd · `loop close`: GREEN, stage closed, next is design · ok
32. sdd-retro · archive and audit · ok

## 3. What came into being

- `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/impact.md` — how the area works today, the tier signals, and a dated note on the re-measurement.
- `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/brainstorm.md` — the nine answered questions and what each settled.
- `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/requirements.md` — 11 EARS requirements, edge cases, bounds and named assumptions A-1 to A-4; approved.
- `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/scenarios.md` — 53 Gherkin seeds and the test data behind them.
- `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/review/coherence.md` — three coherence passes.
- `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md` — the delta entry for `spec/invariants.md`.
- `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/delta.md` and `delta-history.md` — assembled by `loop close`.
- `spec/invariants.md` — the no-login and the retention non-goals now name to-do tasks as well as guestbook entries.
- Nine issues on Scalo-Sales-Engineering-Consulting/claude-marketplace, #296 to #311, and one comment on #305.

## 4. Decisions

- D1: The change walks the strategic path, p3 — **Who:** agent (engine arithmetic over the measured signals) — **Why:** `new_context` is lit.
- D2: The to-do list is a second screen and the guestbook stays — **Who:** user (Q-1) — **Why:** the smaller change; removing the guestbook is not part of it.
- D3: Done can be switched back to not done — **Who:** user (Q-2) — **Why:** a mis-click is fixed with one more click.
- D4: Edit and delete are in this change — **Who:** user (Q-3) — **Why:** "ew." read as "and also".
- D5: A done task stays in its place, shown as done — **Who:** user (Q-4) — **Why:** the list never jumps.
- D6: The main address keeps opening the guestbook — **Who:** user (Q-5) — **Why:** nothing people already use moves.
- D7: Newest task at the top — **Who:** user (Q-6) — **Why:** a new task appears right under the field.
- D8: The screen is in English — **Who:** user (Q-7) — **Why:** the project rule.
- D9: A fresh environment starts with example tasks — **Who:** user (Q-8) — **Why:** a preview somebody can judge.
- D10: The eight smaller assumptions (200 characters, a delete confirmation, editing leaves done-ness alone, duplicates allowed, one list, no dates or priorities, the later change wins, no live updates) — **Who:** user (Q-9) — **Why:** confirmed at the read-back.
- D11: Each list is filled with examples on its own — **Who:** user (Q-10) — **Why:** existing test environments get examples too.
- D12: A line break inside a task is refused, with its own message — **Who:** user (Q-11) — **Why:** "one line" becomes a rule the app enforces.
- D13: One example task starts done — **Who:** user (Q-12) — **Why:** both looks are visible at once.
- D14: Re-record the signals with `tooling_touched` lit — **Who:** agent — **Why:** Q-8 met the condition `impact.md` itself stated.
- D15: Raise D1 to D3 with `ask --now` — **Who:** agent — **Why:** the documented exit for a NEEDS_DECISION from a member still recorded as dispatched.
- D16: Resolve findings 1-3 and 6 from the recorded answers without asking again, and take A-1 to A-4 to the gate as named assumptions — **Who:** agent — **Why:** constitution Art. VII, and the budget refusal naming that exit.
- D17: Compose the review-converge dispatches by hand — **Who:** agent — **Why:** `loop next` rendered none.
- D18: Run convergence round 2 on opus, not fable — **Who:** user (ESC-requirements-r2) — **Why:** the recommended decline.
- D19: Approve `requirements.md` with A-1 to A-4 as written — **Who:** user (the gate) — **Why:** —
- D20: Send the one-character ADR-line fix back to review-converge instead of editing the fragment — **Who:** agent — **Why:** the fragment is that worker's product, and the orchestrator writes no specification document.

## 5. Questions to the user

- Q1: The to-do list beside the guestbook, or replacing it? — **Answer:** beside it, the guestbook stays — **Stage:** requirements
- Q2: Can a done task be switched back to not done? — **Answer:** yes — **Stage:** requirements
- Q3: Which of "ew usuniecie lub edycja" belong in this change? — **Answer:** both delete and edit — **Stage:** requirements
- Q4: What happens to a task once it is marked done? — **Answer:** it stays in place, shown as done — **Stage:** requirements
- Q5: Which screen opens at the main address? — **Answer:** the guestbook, as today — **Stage:** requirements
- Q6: In what order are the tasks listed? — **Answer:** newest at the top — **Stage:** requirements
- Q7: Which language does the to-do screen use? — **Answer:** English, like the rest — **Stage:** requirements
- Q8: Does a fresh copy of the app start with example tasks? — **Answer:** yes, a few — **Stage:** requirements
- Q9: The read-back: is the summary right, including the eight assumptions? — **Answer:** looks right, go ahead — **Stage:** requirements
- Q10: Does an existing environment with guestbook entries and an empty list get example tasks? — **Answer:** yes, each list is filled on its own — **Stage:** requirements
- Q11: What happens to a line break sent inside a task's text? — **Answer:** refuse it, with its own message — **Stage:** requirements
- Q12: Is one of the example tasks already done? — **Answer:** yes, at least one — **Stage:** requirements
- Q13: Send convergence round 2 on fable (ESC-requirements-r2)? — **Answer:** no, opus — **Stage:** requirements
- Q14: Approve `requirements.md` with A-1 to A-4 as written? — **Answer:** approve as written — **Stage:** requirements

## 6. Where the process got stuck

- S1: The signals were measured before the brainstorm could change them, and nothing re-measured — **Skill:** cr-impact — **How many times:** 1
- S2: HITL findings had no way forward once the question budget was spent; `loop next` kept returning row 11 — **Skill:** sdd — **How many times:** 2
- S3: The answers to a member's NEEDS_DECISION never reached its artefact before the next wave — **Skill:** cr-requirements / review-coherence — **How many times:** 1
- S4: The convergence round re-applied edits already on disk — **Skill:** cr-impact, cr-requirements — **How many times:** 1
- S5: The stage close went RED on `recorded-decision`, because the fragment read `**ADR:** none.` — **Skill:** review-converge — **How many times:** 1
- S6: The `--edited` usage line was misread and the call exited 2 — **Skill:** review-converge — **How many times:** 2
- S7: The signal definitions did not fit a concept the specification does not name yet — **Skill:** cr-impact — **How many times:** 1

## 7. Sentences in the instructions I hesitated over

- I1: **File:** `skills/sdd/SKILL.md` — **Sentence:** "Never compose a dispatch from memory, and never write out the rules. `sdd-engine loop next` prints one ready block per member." — **What I did:** composed the review-converge dispatches from the Phase 3 template when `loop next` printed none.
- I2: **File:** the engine's budget refusal (output of `loop ask --raise`) — **Sentence:** "What is still open is a named assumption in this stage's document ("Assumed: ..., say so if not"), or one question carried to the stage that can answer it with the code in front of it -- never another round." — **What I did:** had review-converge write A-1 to A-4 into `requirements.md`, and put them to the user at the approval.
- I3: **File:** `spec/constitution.md` — **Sentence:** "A free-text answer is interpreted, announced and recorded; it never produces the same question a second time." — **What I did:** did not ask Q-10 to Q-12 again, and folded findings 1-3 and 6 into one confirmation question, which the budget then refused.
- I4: **File:** `skills/sdd/SKILL.md` — **Sentence:** "`--now` asks while a wave is still out ... It is counted as an escape hatch, so use it for that deadlock and not for impatience." — **What I did:** used it once, for D1 to D3.
- I5: **File:** `skills/sdd/SKILL.md` — **Sentence:** "You dispatch; you do not implement." — **What I did:** sent the one-character fix of the ADR line back to review-converge.
- I6: **File:** `skills/sdd/SKILL.md` — **Sentence:** "When `close_stage.py` prints its boundary message, print it to the user verbatim" — **What I did:** printed the part my own `tail -60` had kept.

## 8. Workarounds and departures

- W1: Signals are recorded by cr-impact — **Workaround:** the orchestrator re-ran `set-signals` after the brainstorm — **User's consent:** no
- W2: Dispatch only the blocks `loop next` renders — **Workaround:** review-converge composed by hand, three times — **User's consent:** no
- W3: A HITL finding goes through a recorded question — **Workaround:** named assumptions, confirmed at the approval — **User's consent:** yes
- W4: After the close, only the boundary sequence — **Workaround:** one `loop next` to confirm the close — **User's consent:** no

## 9. What was not done

- The design stage was not started; the boundary stops here.
- The "**Status:** assumed, awaiting the user" lines of A-1 to A-4 in `requirements.md` were not updated, because that would re-open the approved gate.
- No question was asked about the lockup name or the form of the navigation; they are left to the mock-up.
- No code and no test was written.

## 10. The record's extent

<!-- extent:begin -- regenerated by `retro_capture.py` on every capture -->

The archive reaches the end of the transcript as of the moment `capture` ran (2026-09-24T13:00:25Z): 26 files, 16.5 MB. Shapes of personal data: email=98, iban=0, phone=0, pesel=0. What happened after that moment the archive does not carry -- `capture` never catches its own turns. This is capture 2 of this session; the first reached 16.3 MB at 2026-09-24T12:59:02Z.

<!-- extent:end -->

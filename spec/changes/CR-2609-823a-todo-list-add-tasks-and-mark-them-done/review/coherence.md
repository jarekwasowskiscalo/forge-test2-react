# Coherence — the to-do list: add tasks and mark them done

*ONE file for the whole change, one section per pass.*

## Pass 1 — the `requirements` stage

First pass of the stage (a full hunt). There are no recorded resolutions yet, so Phase 1b had
nothing to verify. Artefacts read: `brainstorm.md`, `impact.md`, `requirements.md` (with Edge
cases and Impact analysis), `scenarios.md` (with Test data), and the three `ASSUMPTIONS` blocks
from the preflight. The ranked documents read above them: `spec/constitution.md`,
`spec/invariants.md`, `spec/glossary.md`, `contracts/README.md`.

The answers to `Q-10`, `Q-11` and `Q-12` were read from the record, because no Markdown
document carries them. Command:
`sdd-engine change_state show --cr CR-2609-823a --field open_questions`. Output: `Q-10` →
`A` "Yes, each list is filled on its own" (answered 2026-09-24T12:14:04Z); `Q-11` → `A` "Refuse
it, with its own message" (12:14:05Z); `Q-12` → `A` "Yes, at least one is done" (12:14:05Z).

Pairs compared: brainstorm ↔ requirements (every `Q-1`…`Q-9` answer and all eight read-back
assumptions); requirements § Requirements ↔ scenarios (all 53 seeds, one by one); requirements
§ Requirements ↔ § Edge cases and § Non-Goals; requirements ↔ impact; scenarios § Test data ↔
the corpus rules and the trim set; every artefact ↔ the glossary; every artefact ↔
`spec/invariants.md` and `contracts/invariants/guestbook.md`; each author's assumptions ↔ what
its neighbour wrote.

### COH-requirements-1 — Is a line break inside a task's text refused, or still an open question?

- **kind:** gap
- **severity:** major
- **decision_mode:** HITL
- **auto_basis:**
- **ambiguity_source:** spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/requirements.md § R-2
- **artifacts:** requirements.md, scenarios.md

**What each says.** `requirements.md` § R-2 clause 4: "(A line break inside the text is an open
question, `D2` in § Open questions.)". § Open questions `D2` says it "blocks the contract's
refusal set" and "is for the user". § Attacks E-9 says "The requirements do not say (`D2`)".
§ R-6 clause 4 refuses an edit only when it is empty or over 200. `scenarios.md` S-8 asserts
"the task should be refused as being more than one line". S-33's last row refuses such an edit.
S-9 asserts that a trailing line break is trimmed and the text accepted. The fixture
`tasks-refused.json` case `text_line_break_inside` and the `text-measurement.json` addition add
a fourth verdict. All of these rest on `Q-11`.

**Why they cannot both be true.** One document says the behaviour is undecided and blocks the
design stage. The other asserts a specific refusal, under the tags `CR-2609-823a/R-2` and `R-6`,
which state no such clause. Suppose the stage closes as it is. Design then either stops to ask
`Q-11` a second time, or `design-spec` writes a context document without the rule while the tests
enforce it (constitution, Article I). That is the change shipping wrong.

**What settles it.** No document on the ladder. The product decision exists (`Q-11` → A), but
only in the change record, which is not a citable document. So this is HITL by iron rule 2. The
human step is to confirm that `requirements.md` adopts the answer already given. It is **not**
a new question (constitution, Article VII: an answered question is never asked again).

**Resolution.** `review-converge` writes `Q-11` → A into `requirements.md`: § R-2, § R-6, E-9,
§ With no defined behaviour, § Open questions, § Impact analysis and Self-check 4.

Ready patch, `requirements.md`:
- § R-2 clause 4. Replace "the system SHALL keep that whitespace unchanged. (A line break inside
  the text is an open question, `D2` in § Open questions.)" with "the system SHALL keep that
  whitespace unchanged."
- § R-2, a new clause 6: "IF a task's text carries a line break between its first and last
  visible character, THEN the system SHALL refuse it, store nothing, and tell the person, with a
  reason of its own, that a task is one line (`Q-11`). A line break at either end is removed by
  clause 1 and is not refused." Which characters are a line break: COH-requirements-4.
- § R-2 acceptance, a new **R-2.7**: "GIVEN the text "Buy bread", a line feed, then "and milk",
  WHEN it is submitted as a new task, THEN it is refused with the one-line reason, not as empty or
  too long, and the list is unchanged. GIVEN "Buy bread" followed by one line feed, THEN it is
  accepted and stored as "Buy bread"."
- § R-6 clause 4. Replace "is empty after trimming or longer than 200 code points after
  normalizing and trimming" with "is empty after trimming, is longer than 200 code points after
  normalizing and trimming, or carries a line break between its first and last visible
  character". Append to R-6.3: "An edit to a text with a line break between two words is refused
  the same way."
- E-9. Replace "The requirements do not say (`D2`)." with "The requirements say `R-2` clause 6,
  `R-2.7` (`Q-11`)."
- § With no defined behaviour: delete the `D2` bullet. § Open questions: replace the `D2` bullet
  with "**`D2`: answered.** `Q-11` → A, refuse it with its own message (`R-2` clause 6)."
- § Impact analysis, the sub-bullet on
  `::test_the_corpus_exercises_a_message_with_line_breaks`. Replace "This runs straight into
  `D2`." with "Under `Q-11` no task file may carry an inner line break, so that rule has to be
  scoped to guest book entries." Evidence that the rule demands one: `sed -n 324,326p
  tests/fitness/test_golden_set.py` prints `assert any("\n" in e["message"] for e in
  entries_of(path))` for every file in `_SEQUENCE_FILES`.

**What was ambiguous.** Nothing in the wording. `cr-requirements` was dispatched at 14:05 and
wrote `requirements.md` before `Q-11` was put to the user at 14:13 (session trace). It correctly recorded the gap as `D2`. No step wrote the
answer back before `cr-scenarios` read the file. The scenarios author flagged exactly this (its
finding 8 and its assumption: "The coherence round has to amend R-2 and R-11").

**What was not found.** S-9 (a trailing line break is trimmed, not refused) is not an invention.
It follows from `R-2` clause 4's own definition of "inside", "between its first and last visible
character", and from line feed being in the trim set. `spec/contexts/guestbook.md` § `BR-01`
names Unicode `White_Space`, and `text-measurement.json` has the case `only_the_line_feed`.

### COH-requirements-2 — Does an existing environment with guestbook entries and an empty to-do list get example tasks?

- **kind:** gap
- **severity:** major
- **decision_mode:** HITL
- **auto_basis:**
- **ambiguity_source:** spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/requirements.md § R-11
- **artifacts:** requirements.md, scenarios.md

**What each says.** `requirements.md` § R-11 clause 1 fills example tasks "WHEN a freshly created
environment, one in which neither the guestbook nor the to-do list holds anything, is filled".
That is the condition of `Q-10`'s rejected option B ("examples appear only where both lists
start empty"). § Open questions `D1` calls the other case open, and says it "blocks the design of
`R-11` and the change to `scripts/seed_golden_set.py`". `scenarios.md` S-52 asserts that an
environment with guestbook entries and an empty list "should show the example tasks". S-53
asserts that the guestbook is filled when only the list holds tasks. § Seed data says "the to-do
list is filled when it holds no task, **whatever the guestbook holds** (`Q-10`)".

**Why they cannot both be true.** S-52 and S-53 prove, under the tag `CR-2609-823a/R-11`,
behaviour that `R-11` either leaves open (`D1`) or words as the option the user rejected. Suppose
the design is built from `R-11` as written. Then stage and every open preview keep an empty list,
against the recorded decision, and S-52 fails at acceptance.

**What settles it.** No document on the ladder. `Q-10` → A is recorded only in the change
record. The human step is to confirm adoption. It is not a new question.

**Resolution.** `review-converge` writes `Q-10` → A into `R-11` and removes `D1`.

Ready patch, `requirements.md`:
- § R-11 clause 1. Replace "WHEN a freshly created environment, one in which neither the
  guestbook nor the to-do list holds anything, is filled with example data, the system SHALL put
  at least three example tasks on the to-do list." with "WHEN an environment whose to-do list
  holds no task is filled with example data, whatever the guestbook holds, the system SHALL put at
  least three example tasks on the to-do list (`Q-10`: each list is filled on its own)."
- § R-11, a new clause: "WHEN an environment is filled with example data, the system SHALL decide
  whether to give the guestbook its welcome entries by what the guestbook holds alone, whatever
  the to-do list holds (`Q-10`)."
- § R-11 acceptance, a new **R-11.5**: "GIVEN an environment whose guestbook holds its welcome
  entries and whose to-do list is empty, WHEN it is filled, THEN the list shows the example tasks
  and the guestbook holds exactly the entries it held before." A new **R-11.6**: "GIVEN a to-do
  list holding one task and an empty guestbook, WHEN it is filled, THEN the guestbook gets its
  welcome entries and the list still holds exactly that one task."
- § With no defined behaviour: delete the `D1` bullet. § Open questions: replace the `D1` bullet
  with "**`D1`: answered.** `Q-10` → A, each list is filled on its own (`R-11` clause 1)."
- § Impact analysis, the `spec/design/architecture.md` § What a new environment starts with
  bullet. Replace "`R-11` clauses 1–4 are consistent with it. `D1` is exactly where the "one
  condition" wording and the per-guestbook refusal stop giving the same answer." with "`Q-10` → A
  fills each list on its own. The seeder gains a refusal per list beside "It will not seed a guest
  book that already has entries", which is a design edit to that section."
- § Impact analysis, Tests that would fail. Replace "**goes red under `D1` option A**" with
  "**goes red, because `Q-10` chose option A**: tasks are now posted where the guestbook holds
  entries". Evidence: `grep -n left_alone tests/tooling/test_seed_golden_set.py` prints
  `116:def test_a_guest_book_with_entries_is_left_alone(guestbook) -> None:`.

**What was ambiguous.** As in COH-requirements-1: `requirements.md` recorded `D1` honestly before
the user answered at 14:14, and nothing wrote the answer back.

**What was not found.** S-53 is not a change to the guestbook (§ Non-Goals). An empty guestbook
is filled today whatever else the environment holds. Q-10 keeps that, and the refusal "will not
seed a guest book that already has entries" (`spec/design/architecture.md` § What a new
environment starts with) is untouched.

### COH-requirements-3 — Is one of the example tasks done?

- **kind:** gap
- **severity:** minor
- **decision_mode:** HITL
- **auto_basis:**
- **ambiguity_source:** spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/requirements.md § R-11
- **artifacts:** requirements.md, scenarios.md

**What each says.** `requirements.md` § R-11 states no done example. § Bounds gives "Example
tasks, minimum | 3" and nothing about state. § Open questions `D3` says it "blocks the shape of
the seed corpus". `scenarios.md` S-49 asserts "at least one of them should be shown as done".
§ Seed data marks example 3 done, and has the seeder "then mark number 3 done (`Q-12`)".

**Why they cannot both be true.** S-49's done line proves, under `CR-2609-823a/R-11`, a clause
`R-11` does not have, while `requirements.md` still calls it undecided. This is graded minor, not
major. The consequence is one flag in a seed file and one call in the seeder, under a
`**Verified-by:** manual` requirement, so it costs a later edit rather than a wrong contract.

**What settles it.** No document on the ladder. `Q-12` → A is recorded only in the change record.
Confirm adoption. It is not a new question.

**Resolution.** `review-converge` writes `Q-12` → A into `R-11` and § Bounds and removes `D3`.

Ready patch, `requirements.md`:
- § R-11, a new clause: "WHEN the example tasks have been put on the to-do list, at least one of
  them SHALL be done (`Q-12`). It is added not done and then marked, because a new task is never
  born done (`R-1` clause 3)."
- § R-11 acceptance, a new **R-11.7**: "GIVEN a to-do list just filled with example tasks, WHEN it
  is shown, THEN at least one example task is shown as done."
- § Bounds, a new row: "| Example tasks done, minimum | 1 | `Q-12` |".
- § Open questions: replace the `D3` bullet with "**`D3`: answered.** `Q-12` → A, at least one
  example is done." § With no defined behaviour: delete the `D3` bullet.

**What was ambiguous.** The same write-back gap as COH-requirements-1 and COH-requirements-2.

**What was not found.** There is no floor on not-done examples (`scenarios.md` § Bounds the
requirements did not give, item 5). That is not a contradiction: the seed file shows four not
done, which satisfies any reading of `Q-12`.

### COH-requirements-4 — Which characters count as "a line break" inside a task?

- **kind:** quality
- **severity:** major
- **decision_mode:** HITL
- **auto_basis:**
- **ambiguity_source:** spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/requirements.md § R-2
- **artifacts:** requirements.md, scenarios.md

**What each says.** `requirements.md` § R-2 clause 4 uses "a line break" without naming its
characters, and clause 5 demands that the screen accept "exactly the texts the service accepts".
`scenarios.md` uses U+000A alone. Its § Bounds the requirements did not give, item 1, reports that
U+000D, U+0085, U+2028, U+2029, U+000B and U+000C are unstated. It also notes that the guestbook
keeps a next line inside a signature (`text-measurement.json` case `next_line_inside_is_kept`,
present: checked by loading the file).

**Why they cannot both be true.** Clause 5 cannot hold if the two sides each take their own
language's default, and the defaults disagree. Command: `python3 -c` over
`str.splitlines()`, then `node -e` over `/^.*$/`. Output: `python splitlines breaks on: ['LF',
'VT', 'FF', 'CR', 'NEL', 'LS', 'PS']` against `js ... breaks on: [ 'LF', 'CR', 'LS', 'PS' ]`. A
task carrying VT, FF or NEL between two words would be refused by the service and let through by
the screen. That is the `D-04` class of defect `requirements.md` § Edge cases lists as having
happened, and the reason `spec/contexts/guestbook.md` § `BR-01` writes its trim set down ("the
two languages this system is built in disagree about six of them").

**What settles it.** Nothing. Which texts a person may store is a product rule.

**Resolution.** Ask one closed question. (A, recommended) A line break is any of U+000A, U+000B,
U+000C, U+000D, U+0085, U+2028, U+2029: one written set that both sides read and no language
default, so a pasted text is refused identically everywhere. (B) U+000A and U+000D only: the
others stay content, as in a guestbook signature, and the written set is those two. Then add the
chosen set to the new `R-2` clause 6 (COH-requirements-1) and to § Bounds as "| Line break inside
a task | refused; the set is … | `Q-11`, this decision |".

**What was ambiguous.** `requirements.md` § R-2 clause 4 introduced "line break" as a term.
`Q-11`'s wording ("a line break inside a task's text") inherited it, and neither gave the set.

**What was not found.** No artefact asserts which refusal wins when a text is both over 200 and
multi-line. Neither says it, so nothing contradicts. It is not raised here.

### COH-requirements-5 — Does the standing non-goal on authentication and retention cover tasks?

- **kind:** gap
- **severity:** minor
- **decision_mode:** HITL
- **auto_basis:**
- **ambiguity_source:** spec/invariants.md § Deliberate non-goals
- **artifacts:** requirements.md, spec/invariants.md

**What each says.** `requirements.md` § Non-Goals: "This is the standing non-goal
(`spec/invariants.md` § Deliberate non-goals): anybody adds, marks, edits and deletes any task",
and "a task lives until somebody deletes it". `spec/invariants.md` § Deliberate non-goals, lines
123-125: "anybody may add, amend and delete any entry". Line 162: "An entry lives until somebody
deletes it."

**Why they cannot both be true.** `requirements.md` cites the standing non-goal as covering tasks,
and the cited text covers entries only. `requirements.md` itself says so, "By intent yes, by
wording no" (Self-check 23, and § Impact analysis). It reports this for the convergence round,
the only route that may edit that file (`spec/invariants.md` § Deliberate non-goals: "an author
who sees a divergence here reports it as a finding"). This block is that report, so it reaches
`review-converge`. Nothing ships wrong, because the behaviour is specified in `R-1` and `R-7`.
Graded minor.

**What settles it.** Nothing above both documents. Only `spec/constitution.md` ranks above
`spec/invariants.md`, and it does not word non-goals. The user confirmed the intent at the Q-9
read-back (`brainstorm.md` § Deliberately out of scope: "the standing non-goal ... holds for the
to-do list as it does for the guestbook").

**Resolution.** In the convergence round, reword the two items so they name everything the system
stores. This is a rewording that lifts nothing, so no "lifted by" line is added.

Ready patch, `spec/invariants.md` § Deliberate non-goals:
- Replace "anybody may add, amend and delete any entry." with "anybody may add, amend and delete
  anything the system stores: any guestbook entry and any to-do task."
- Replace "An entry lives until somebody deletes it." with "An entry, like a to-do task, lives
  until somebody deletes it."

**What was ambiguous.** `spec/invariants.md` § Deliberate non-goals states system-wide non-goals
in the guestbook's noun, and there was only one thing to store when it was written.

**What was not found.** No other non-goal is worded narrowly for tasks. Moderation, CSRF, a mobile
version, a second engine and paging (lifted for the guestbook alone as `BR-05`) are all worded
system-wide or not at all, and `requirements.md` is consistent with each one.

### COH-requirements-6 — Does the change reach `scripts/`?

- **kind:** contradiction
- **severity:** minor
- **decision_mode:** HITL
- **auto_basis:**
- **ambiguity_source:** spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/impact.md § Tier signals
- **artifacts:** impact.md, requirements.md

**What each says.** `impact.md` § Tier signals lists `tooling_touched | no` and closes "recorded
with nine signals present and `infra_touched`, `tooling_touched` absent". `requirements.md`
§ Impact analysis (Dependencies) says "`R-11` reaches `scripts/seed_golden_set.py`".
`brainstorm.md` Q-8 says "**This reaches `scripts/`.**". The record was re-measured after the
brainstorm: the session trace, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/sessions/870fece5-b8f9-4a47-84da-b3456aa1de97/trace.md`,
shows `[14:05] signals_set: present: ..., tooling_touched`.

**Why they cannot both be true.** The same signal reads absent in the human table and present in
the record and in the requirements. The row carries its own condition ("reached only if the
requirements give the list seed data"), and that condition is now met. Only the flat "no" and the
closing sentence are stale, so this is graded minor. A design-stage reader of `impact.md` would
underestimate what the change reaches.

**What settles it.** Nothing on the ladder. The process root is already banked as `PROC-4`
(cr-impact measures before the brainstorm it feeds), filed as
`https://github.com/Scalo-Sales-Engineering-Consulting/claude-marketplace/issues/298`.

**Resolution.** Keep the measurement as dated. Add one line under the table: "Re-measured after
`Q-8` (`brainstorm.md`): `tooling_touched` is lit, because `R-11` reaches
`scripts/seed_golden_set.py`. The record holds ten signals present and `infra_touched` alone
absent."

**What was ambiguous.** The `tooling_touched` row states a conditional measurement in a yes/no
cell.

**What was not found.** No other signal moved. `Q-1`…`Q-12` light nothing under `infra/`, and
`infra_touched` stays absent, consistent with every artefact.

### What was checked and agrees

- **brainstorm ↔ requirements.** Every `Q-1`…`Q-9` answer and all eight read-back assumptions
  map to an `R-n` or a Non-Goal. "The later change wins" and `R-9` clause 2 (an edit and a mark
  both kept) look like a contradiction but are not. The same read-back says "Editing changes the
  text only, never done or not done", so "later wins" applies per aspect. `R-4` clause 3 (set the
  chosen state) agrees with `Q-2`'s two-way tick and with "the later change wins".
- **requirements ↔ scenarios.** Every seed except those in COH-requirements-1…3 cites a clause
  that states it. Every `R-1`…`R-11` has a seed and acceptance criteria. The `text_absent` case
  ("not given at all", sent as `""`) copies the guestbook corpus's own `author_empty` /
  `message_empty` wording, so it follows house style. The `@req:CR-2609-823a/R-n` form matches
  `e2e/suite/features/guestbook.feature`.
- **R-11's manual marker.** It is honest. `spec/design/testing.md` § The UI smoke is not a
  traceability surface says `tests/tooling/` and `tests/fitness/` "do not own citations".
  `scenarios.md` keeps S-49…S-53 for acceptance, and `PROC-6` already banks the tagging friction.
- **Test data ↔ the corpus.** The seed lengths were recomputed after NFC as 112, 94, 93, 72 and
  108, all under the 150 margin (`room = 0.75`, `tests/fitness/test_golden_set.py:723`). Tab,
  ideographic space and space are all in the `BR-01` set, so `text_all_whitespace` is empty as
  claimed. The citations resolve: `D-04`, § Choosing what proves what, § Components and their
  states ("Emptiness **always carries a sentence about what to do**"), § Tokens, § Interactions.
- **Edge cases ↔ non-goals.** E-13, E-14, E-20 and E-22 each land on a stated non-goal. None
  contradicts one.
- **Glossary.** No domain word is used for two things. "Seed data" and "filled with example
  data" name one thing.
- **Invariants.** A done task stays one record in place (`D-01`, `R-3.4`). The task text follows
  `D-04`'s normalization and unit (`R-2` clause 1).

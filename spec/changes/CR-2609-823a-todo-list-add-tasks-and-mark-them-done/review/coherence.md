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

## Pass 2 — the `requirements` stage

The preflight printed convergence round 1 of 3, mode DEEP. Phase 1b ran first, over the six
recorded resolutions. A full hunt over the reconciled text came after it. Artefacts read:
`brainstorm.md`, `impact.md`, `requirements.md` (with Edge cases, Impact analysis, Bounds and
Named assumptions), `scenarios.md` (with Test data), `input/request.md`,
`design/delta/converge.md`, and the four `ASSUMPTIONS` blocks from the preflight. The ranked
documents read above them: `spec/constitution.md`, `spec/invariants.md`, `spec/glossary.md`,
`contracts/README.md`.

### Recorded resolutions

- COH-requirements-1: landed. `requirements.md`:77 (clause 4 without the `D2` note), :81-87
  (clause 6), :106-109 (`R-2.7`), :219-221 (`R-6` clause 4), :228-230 (`R-6.3`), :400-402 (E-9),
  :603-605 (Impact analysis), :699 (`D2` answered), :746-748 (Self-check 4). § With no defined
  behaviour, :495-505, has no `D2` bullet left.
- COH-requirements-2: landed. `requirements.md`:4-5 (Source), :328-330 (clause 1), :337-339
  (clause 5), :353-357 (`R-11.5`, `R-11.6`), :553-558 (Decisions), :609-613 (Tests that would
  fail), :698 (`D1` answered), :798-801 (Self-check 21).
- COH-requirements-3: landed. `requirements.md`:340-342 (clause 6), :358-359 (`R-11.7`), :688
  (Bounds), :700 (`D3` answered).
- COH-requirements-4: landed. `requirements.md`:83-87 (the set in clause 6), :681 (Bounds),
  :718-727 (`A-1`).
- COH-requirements-5: landed, exactly as its resolution describes. `spec/invariants.md`:123-124 now
  names "any to-do task". Line 162, the retention line, is deliberately unchanged, and that half is
  carried as `A-2` at `requirements.md`:728-733. The rest: `requirements.md`:520-522 (Impact
  analysis), :806-809 (Self-check 23). `design/delta/converge.md` declares the edit. Its Was and
  Now match `git diff main -- spec/invariants.md` word for word.
- COH-requirements-6: landed. `impact.md`:381-385.

I grepped `requirements.md` for the wording from before the resolutions ("open question, `D2`",
"under `D1` option", "blocks the design of"). It printed nothing.

Pairs compared: `Q-10`…`Q-12` (as the preflight quotes them) ↔ `requirements.md`;
`requirements.md` § Requirements ↔ `scenarios.md` (every converged clause and criterion against
its seed); § Requirements ↔ § Edge cases and § Non-Goals; § Requirements ↔ § Named assumptions
and § Bounds; § Success criteria ↔ § Open questions and `brainstorm.md` § Open; `scenarios.md`
§ Test data ↔ the written trim set and the corpus; `impact.md` ↔ the branch's
`spec/invariants.md`; every artefact ↔ the glossary and the invariants; each author's
assumptions ↔ what its neighbour wrote.

### COH-requirements-7 — Can a line break reach the one-line field, or only the API?

- **kind:** contradiction
- **severity:** minor
- **decision_mode:** HITL
- **auto_basis:**
- **ambiguity_source:** spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/requirements.md § Attacks
- **artifacts:** requirements.md

**What each says.** § Attacks E-9 calls a line break inside a task "malformed, rarely (only
through the API; the field is one line)". It gives the cost as "a stored value nobody can type
into the field". After convergence, § R-2 clause 6 makes "a line break" any of seven characters:
U+000A, U+000B, U+000C, U+000D, U+0085, U+2028 and U+2029 (assumption `A-1`). Clause 5 requires
the screen to refuse exactly what the service refuses. `scenarios.md` S-8 says what E-9 says, but
only about its own data, a line feed. It sends the other six to "the rule, on both sides", through
the additions to `text-measurement.json`.

**Why they cannot both be true.** A one-line field removes only a line feed and a carriage return
from its value. It keeps the other five characters of the set. Command, run in `frontend/` with
jsdom, which implements the HTML value-sanitization algorithm: `node -e`. It sets an
`<input type=text>` to "Buy bread", then each character, then "and milk", and compares the value
it reads back. Output:
`one-line field, a break between two words: {"LF":"stripped","CR":"stripped","VT":"kept","FF":"kept","NEL":"kept","LS":"kept","PS":"kept"}`.
The helper it calls is `node_modules/jsdom/lib/jsdom/living/helpers/strings.js:39`,
`return s.replace(/[\n\r]+/g, "");`.

So under `A-1`, a pasted U+2028 or U+0085 reaches the screen, and clause 5 obliges the screen to
refuse it with the one-line reason. E-9 says the screen never meets one. A `design-ui` author who
reads E-9 draws no one-line refusal state and no copy for it, in the field or in the editor. A
`design-testing` author who reads clause 5 and the text-measurement rows in the scenarios asserts
one.

Graded minor. The shared cases that `scenarios.md` specifies already hold the verdict on both
sides. What can go missing is a screen state and its words, and that costs a later edit. This was
not measured in Chromium. jsdom follows the standard's algorithm, and the UI smoke is where a real
browser would confirm it.

**What settles it.** Nothing ranked above both. The correction follows from `R-2` clauses 5 and 6
of `requirements.md` itself, which stand on the same rung as E-9.

**Resolution.** `review-converge` corrects E-9's route and cost, so the design stage knows that the
screen meets five of the seven characters.

Ready patch, `requirements.md` § Attacks, E-9. Replace "**E-9: malformed, rarely (only through the
API; the field is one line).** A text with a line break inside it. It costs a task that renders on
several lines, or a stored value nobody can type into the field." with "**E-9: malformed,
rarely.** A text with a line break inside it. A line feed or a carriage return arrives only
through the API, because a one-line field strips those two. The other five characters of `R-2`
clause 6's set (`A-1`) paste into the field, so the screen meets them and refuses them for the
same reason the service does (`R-2` clause 5). It costs a task that renders on several lines, or a
text the screen lets through and the service refuses."

**What was ambiguous.** E-9 was written when "a line break" meant a line feed. The pass 1
convergence round rewrote E-9's closing sentence for `Q-11`, and `A-1` then widened the set to
seven characters. Nothing went back to the premise in E-9's parenthesis.

**What was not found.** S-8's own note in `scenarios.md` ("Only a caller that goes around the
screen can send it") is true of its data, a line feed, and is not part of this finding. Suppose
the user overrules `A-1` with U+000A and U+000D alone. Then E-9 as written is true again, and the
patch is dropped.

### COH-requirements-8 — Is a line break next to an invisible character "inside" the text?

- **kind:** quality
- **severity:** minor
- **decision_mode:** HITL
- **auto_basis:**
- **ambiguity_source:** spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/requirements.md § R-2
- **artifacts:** requirements.md, scenarios.md

**What each says.** `requirements.md` § R-2 clause 6 refuses a line break "between its first and
last visible character". The clause closes: "Every one of them is in clause 1's trim set, so a
line break at either end is removed by clause 1 and is not refused." Clause 4 and § R-6 clause 4
use the same phrase. No document defines "visible". I grepped for `visible` across
`requirements.md`, `scenarios.md`, `spec/contexts/guestbook.md`, `spec/design/conventions.md`,
`spec/design/api.md` and `contracts/invariants/guestbook.md`. In this sense it occurs only at
`requirements.md`:76, :81 and :220.

`scenarios.md` S-9 reads the rule the other way. It fails if "the line break rule runs before
trimming", so any line break that trimming leaves in the text is refused.
`spec/contexts/guestbook.md` § `BR-01`, whose set clause 1 borrows, says: "Whitespace *inside* a
value is content and is kept; only the ends go". That defines "inside" by the trim.

**Why they cannot both be true.** Some content characters are invisible. `text-measurement.json`
holds `zero_width_space_is_content` (U+200B) and `mongolian_vowel_separator_is_content` (U+180E).
Command: `python3`, trimming with the fixture's own `only_every_trimmed_code_point` input as the
set. Output: `trim set size: 30`, then
`ZWSP after the break: after clause 1 = 'Buy bread\n​'; line feed still inside = True`. The
same run with U+200D before the break printed `line feed still inside = True`.

Under the literal clause 6, that line feed comes after the last visible character, so clause 6
does not refuse it. Clause 1 does not remove it either, so it is stored, and the closing sentence
of clause 6 is false for this text. Under S-9's reading the text is refused. If a backend author
and a frontend author each implement a different reading, they disagree about this text. That is
the clause 5 failure `R-2` exists to prevent. Graded minor: such texts are rare, and the fix is
only a change of wording.

**What settles it.** Nothing ranked above both. `BR-01` defines "inside" by the trim, but it is the
guestbook's rule and binds entries, not tasks. `R-2` clause 1 borrows its set, not its wording.

**Resolution.** Word the three clauses by the trim, which is the reading S-9 and `BR-01` already
use.

Ready patch, `requirements.md`:
- § R-2 clause 4. Replace "WHERE a text carries whitespace other than a line break between its
  first and last visible character, the system SHALL keep that whitespace unchanged." with "WHERE
  a text, once clause 1 has trimmed it, still carries whitespace other than a line break, the
  system SHALL keep that whitespace unchanged."
- § R-2 clause 6. Replace "IF a task's text carries a line break between its first and last
  visible character, THEN" with "IF a task's text, once clause 1 has trimmed it, still carries a
  line break, THEN". Append to the clause: "A character that shows nothing but is not in the trim
  set, such as U+200B, is content, so a line break beside it is inside the text."
- § R-6 clause 4. Replace "or carries a line break between its first and last visible character"
  with "or, once trimmed, still carries a line break".

**What was ambiguous.** The phrase "first and last visible character" came into `R-2` clause 4 in
the first draft, as a gloss on "inside". When clause 6 began to refuse by it, the gloss became the
rule. "Visible" and "not trimmed" are not the same set of characters.

**What was not found.** No scenario and no fixture puts an invisible character beside a line
break, so no seed asserts either reading. The disagreement is between the clause's wording and the
defect S-9 names, not between two seeds.

### COH-requirements-9 — Does the UI smoke run unchanged when the mock-up may rename the lockup?

- **kind:** contradiction
- **severity:** minor
- **decision_mode:** HITL
- **auto_basis:**
- **ambiguity_source:** spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/requirements.md § Success criteria
- **artifacts:** requirements.md, brainstorm.md

**What each says.** `requirements.md` § Success criteria, SC-5, measures success as follows: "The
existing guestbook suites run unchanged on every CI run of this branch (the same 22 scenarios plus
the UI smoke)". `brainstorm.md` § Open gives "the lockup's product name 'Guestbook'" to the
mock-up, "for the user to approve there". `requirements.md` § Open questions leaves it there.
`requirements.md` Self-check 14 allows that "the smoke's locator changes in the same change" if a
navigation link is named exactly "Guestbook".

**Why they cannot both be true.** The smoke finds the lockup by that exact name. Commands:
`grep -n "_LOCKUP, exact=True" e2e/ui/test_smoke.py` and
`grep -n PRODUCT_NAME frontend/src/components/shell/PageFrame.tsx`. Output: lines `93:` and `373:`
read `expect(page.get_by_role("link", name=_LOCKUP, exact=True)).to_be_visible()`, beside
`40:_LOCKUP: Final[str] = "Guestbook"` and `24:const PRODUCT_NAME = 'Guestbook'`.

Suppose the approved mock-up renames the lockup, or adds a navigation link named "Guestbook". Then
`test_the_built_spa_boots_and_a_deep_link_resolves` and `test_an_unknown_address_says_so` fail
unless they are edited, so the smoke cannot run unchanged. Read strictly, SC-5 decides in advance a
copy question the brainstorm left to the user. Read loosely, it contradicts nothing. The design
fan-out cannot tell which reading is meant, so its authors diverge: a `design-testing` author holds
the smoke fixed because of SC-5, while a `design-ui` author proposes a new lockup name. Graded
minor: the smoke goes red at implement, and the cost is an edit.

**What settles it.** Nothing ranked above both. Whether the guestbook's smoke may be edited is a
test-strategy call that this change has to make.

**Resolution.** Let SC-5 promise what the guestbook's tests assert, not their exact text.
Recommended: the 22 scenarios run unchanged, and the smoke's guestbook tests keep asserting what
they assert today. A locator may follow a name the user approves in the mock-up. The alternative
keeps SC-5 strict and writes into § Open questions that the lockup stays "Guestbook" and no
navigation link takes that exact name.

Ready patch, `requirements.md` § Success criteria, the "How measured" cell of SC-5. Replace "The
existing guestbook suites run unchanged on every CI run of this branch (the same 22 scenarios plus
the UI smoke), and the requester checks at UAT." with "The 22 scenarios of
`e2e/suite/features/guestbook.feature` run unchanged on every CI run of this branch. The UI smoke's
guestbook tests keep asserting what they assert today; a locator that names the lockup or a
navigation link may follow the names the user approves in the mock-up (§ Open questions;
Self-check 14). The requester checks at UAT."

**What was ambiguous.** In SC-5, "unchanged" can mean "still passing, with the same meaning" or
"not edited". Only the first reading survives the decision that `brainstorm.md` § Open leaves open.

**What was not found.** The smoke asserts no copy that `R-5` clause 4 removes.
`test_an_unknown_address_says_so` (`e2e/ui/test_smoke.py`:367-373) checks the heading "Nothing
here" and the lockup link, not the sentence "There is one screen in this application". So `R-5`
on its own forces no edit to the smoke. Only a change of name does.

### What was checked and agrees

- **`Q-10`…`Q-12` ↔ `requirements.md`.** The quoted answers in `R-2` clause 6, `R-11` clause 1
  and `R-11` clause 6 match the user's words that the preflight prints for COH-requirements-1…3.
- **Requirements ↔ scenarios after convergence.** S-8 and S-9 match `R-2` clause 6 and `R-2.7`.
  The third row of S-33 matches `R-6` clause 4 and `R-6.3`. S-49 matches `R-11.1` and `R-11.7`,
  S-52 matches `R-11.5`, and S-53 matches `R-11.6` and clauses 4 and 5. The seed file's "then
  marks number 3 done" matches clause 6's "added not done and then marked". Every `R-1`…`R-11`
  still has a seed and acceptance criteria.
- **The trim-set claim in `R-2` clause 6.** All seven characters are in the written set. They
  appear in `app/platform/schemas/text.py` at :47 (0x000B), :51 (0x0085) and :65-66 (0x2028,
  0x2029), and in the fixture's `only_every_trimmed_code_point` input, which holds U+0009 to
  U+000D. The set's size is 30.
- **`A-1` ↔ scenarios.** The seven line-break rows among the text-measurement additions are
  `A-1`'s set. The five rows that flip under the other reading are `A-1`'s "the other five".
- **`A-2` ↔ the rest.** § Non-Goals, § Impact analysis, E-14 and the unchanged
  `spec/invariants.md`:162 all say the same thing.
- **The authors' assumptions.** cr-impact: `impact.md`:58-59 still quotes "any entry". That is
  the trunk's wording (`git diff main -- spec/invariants.md` shows it as the removed line), and
  `impact.md` describes the trunk, so both documents are true. cr-requirements: it says the
  scenarios' line-break data "uses U+000A only", which is narrower than the file, because the
  text-measurement additions carry all seven characters. Its conclusion, that the data fits within
  `A-1`, still holds. cr-scenarios: every clause and criterion it names exists as it says.
  review-converge: the retention line is unchanged, as it says.
- **The new half of E-21.** It records a failure-mode exposure of `R-11` clause 6 in the same way
  its first half records one for clause 1, which pass 1 read as agreeing. `R-11` is
  `**Verified-by:** manual`. E-21 contradicts no non-goal.
- **`delta.md`.** It still reads "No author wrote a delta fragment". It is an assembled file, as
  its own marker says, and not an artefact of this stage, so it is not judged here. Its one
  fragment matches the diff.
- **Glossary and invariants.** "To-do task" in `spec/invariants.md`:124 and "task" in
  `requirements.md` name one thing, and no word is used for two. The new text leaves
  `D-01`…`D-03` unaffected.

## Pass 3 — verification

The preflight printed `CONVERGENCE ROUND: 2 of 3 -- MODE: VERIFYING`, so only Phases 1, 1b and 4
ran. There was no hunt. The question was whether each of the nine recorded resolutions of the
`requirements` stage landed in the document its reconciliation named. Artefacts read whole:
`brainstorm.md`, `impact.md`, `requirements.md`, `scenarios.md`, this file, and the four
`ASSUMPTIONS` blocks from the preflight. The ranked documents read above them:
`spec/constitution.md`, `spec/invariants.md`, `spec/glossary.md`, `contracts/README.md`.

Line numbers were taken from the working tree with `grep -n` over each resolution's own
wording. `git status --short` shows no uncommitted edit to any artefact or to
`spec/invariants.md`. Every line cited below is committed at `35a2234`.

### Recorded resolutions

- COH-requirements-1: landed. `requirements.md`:76-77 (clause 4, no `D2` note), :81-89 (clause 6,
  refused "with a reason of its own", `Q-11`), :108-111 (`R-2.7`), :221-223 (`R-6` clause 4),
  :230-232 (`R-6.3`), :402-407 (E-9, "The requirements say `R-2` clause 6, `R-2.7` (`Q-11`)"), :704
  (`D2` answered), :608-610 (Tests that would fail), :774-776 (Self-check 4). § With no defined
  behaviour, :500-510, has no `D2` bullet. The resolution words the rule as "between a task's
  first and last visible character". COH-requirements-8's later resolution changed that wording
  to the trim reading. The refusal itself, its own reason, add and edit alike, and the trimmed
  ends all stand.
- COH-requirements-2: landed. `requirements.md`:4-5 (Source), :330-332 (clause 1), :339-341
  (clause 5), :355-359 (`R-11.5`, `R-11.6`), :558-563 (Decisions), :614-618 (Tests that would
  fail), :703 (`D1` answered), :826-829 (Self-check 21). § With no defined behaviour has no `D1`
  bullet.
- COH-requirements-3: landed. `requirements.md`:342-344 (clause 6), :360-361 (`R-11.7`), :693
  (Bounds, "Example tasks done, minimum | 1"), :705 (`D3` answered). § With no defined behaviour
  has no `D3` bullet.
- COH-requirements-4: landed. `requirements.md`:83-85 (the seven-character set in clause 6), :686
  (Bounds, "Line break inside a task"), :723-732 (`A-1`).
- COH-requirements-5: landed, as its resolution describes. `spec/invariants.md`:123-124 reads
  "anything the system stores: any guestbook entry and any to-do task". `spec/invariants.md`:162,
  the retention line, still reads "An entry lives until somebody deletes it". That half is
  carried as `A-2` at `requirements.md`:733-738. The other edits: `requirements.md`:521-527 (Impact
  analysis, Collisions with invariants), :834-837 (Self-check 23).
- COH-requirements-6: landed. `impact.md`:381-385 holds the dated re-measurement note. The
  original row at :370 and the sentence at :377-379 are kept as the first measurement wrote them.
- COH-requirements-7: landed. `requirements.md`:402-407. E-9 matches the pass 2 ready patch word
  for word and keeps its closing sentence, "The requirements say…".
- COH-requirements-8: landed. `requirements.md`:76-77 (clause 4, "once clause 1 has trimmed it"),
  :81-89 (clause 6, the same wording, with the U+200B sentence at :86-89), :221-223 (`R-6`
  clause 4, "once trimmed, still carries a line break"), :720 (preamble, now "No item below is a
  human decision yet"; `git show 35a2234` shows the removed line "Neither item below…"), :739-751
  (`A-3`). `grep -n "visible character"` finds the phrase only at :745, inside `A-3`, where it
  names the rejected reading.
- COH-requirements-9: landed. `requirements.md`:27 (the SC-5 "How measured" cell, with the
  pass 2 ready patch's text plus "assumed: `A-4`"), :752-761 (`A-4`).

A grep of `requirements.md` for the wording these resolutions replaced found no occurrence. The
strings searched were "open question, `D2`", "under `D1` option", "blocks the design of", "only
through the API; the field is one line" and "unchanged (the same 22 scenarios plus".

The authors' assumptions match the text. The cr-impact author says `impact.md` still quotes the
trunk's "any entry" and keeps the pre-`Q-8` sentence. Both are there, at `impact.md`:58-59 and
:343-345. review-converge says the retention line is unchanged, and `spec/invariants.md`:162
confirms it.

No `verification` finding. All nine resolutions landed.

## Pass 4 — the `design` stage

The preflight printed `COHERENCE PASS: the first one (before any round) -- a full hunt`. No
finding of this stage is recorded yet, so Phase 1b had nothing to verify. Artefacts read whole:
the eight fragments under `design/delta/` (`converge.md` included, although the preflight's list
leaves it out), the live documents they edit (`spec/contexts/todo_list.md`, the diff of
`spec/contexts/guestbook.md`, `spec/glossary.md`, and the diffs of `spec/design/api.md`,
`architecture.md`, `data-model.md`, `testing.md`, `ui/system-states.md` and `ui/guestbook.md`),
`spec/design/ui/todo-list.md`, `contracts/openapi/todo_list.yaml` with the
`contracts/openapi/README.md` diff, the copy of `design/ui/index.html`, the opening of both ADR
drafts, `requirements.md`, and the nine `ASSUMPTIONS` blocks from the preflight. The ranked
documents read above them: `spec/constitution.md`, `spec/invariants.md`, `spec/glossary.md`,
`contracts/README.md`, and `spec/design/conventions.md` § Layers, § Backend and § Frontend.

Pairs compared: `data-model.md` ↔ `api.md`; `api.md` ↔ `todo_list.yaml`; `api.md` ↔
`ui/todo-list.md`; `api.md` ↔ `architecture.md`; `api.md` ↔ `testing.md`; `architecture.md`
(live and fragment) ↔ `testing.md` (live and fragment); `architecture.md` ↔ `data-model.md`;
`architecture.md` ↔ the screen documents; `data-model.md` ↔ `testing.md`; `ui/todo-list.md` ↔
`ui/system-states.md` ↔ `ui/guestbook.md`; `ui/todo-list.md` ↔ the approved mock-up's copy;
`todo_list.md` ↔ `guestbook.md` (the kernel, both sides); `todo_list.md` ↔ every register;
`requirements.md` `R-1`…`R-11` ↔ each design artefact; `requirements.md` ↔ `testing.md` (a suite
per requirement); `scenarios.md` § Test data ↔ `data-model.md` (through the data-model
fragment's table); the ADR drafts ↔ `api.md` and `domain.md`; `converge.md` ↔ `requirements.md`;
every artefact ↔ the glossary, `spec/invariants.md` and `contracts/invariants/guestbook.md`; each
author's assumptions ↔ what its neighbour wrote.

### COH-design-1 — Who refuses a task's text, and in what shape: the service, with a coded refusal, or the schema, with FastAPI's list?

- **kind:** contradiction
- **severity:** critical
- **decision_mode:** HITL
- **auto_basis:**
- **ambiguity_source:** spec/design/conventions.md § Layers
- **artifacts:** spec/design/api.md, spec/design/architecture.md

**What each says.** `spec/design/api.md` § Shapes, `TodoTaskCreate` (:160-161): "The bounds are
refusals with a code, not schema constraints. A text outside them is refused with one of the
three `todo_task_text_*` codes of § Refusals, never with FastAPI's list". § The to-do list's
refusals (:364-367): every refusal about a task carries a code, "the three about its text
included", and the sentences "live beside the to-do list's endpoints, in its router module". The
api fragment's ADR entry: the verdict is "decided outside Pydantic's field constraints", and "the
router only translates". `spec/design/architecture.md` § The layer per rule (:588-589): `BR-06`
and `BR-07` are held by "the task's text type in the context's `schemas/`", and a check in the
service "would run after the schema had already refused the text". § The files (:613):
`schemas/todo_tasks.py` holds "the task's text type — normalize, then one line, then measure".
:600-603: "the empty, too-long and more-than-one-line refusals never reach it, because the schema
refuses them before the route runs." The architecture fragment's Decision 2 rejects the service
placement outright.

The assumptions confirm it from both sides. design-api assumed "design-architecture places the
text rule … in the service; the router translates it into the 5 coded refusals". design-architecture
assumed "the empty, too-long and not-one-line refusals come from the schema as a 422 … The wire
spelling is api.md's." Each is false of the neighbour. design-adr drafted
`task-text-refusals-are-coded-not-schema-constraints.md` on api's side and said so.

**Why they cannot both be true.** A text refused in `schemas/`, before the route runs, reaches the
client as FastAPI's validation `422`, the list of `{loc, msg, type}`. `api.md`:365 says exactly
that of the guestbook's schema-held bounds. So under `architecture.md` no `Refusal` body is sent,
no `detail.code` exists, and no code sits in the router module. Three consumers depend on the
opposite:

- The contract gate. `sed -n 34,35p scripts/openapi_contract.py` prints "lists the codes and this
  module looks for each one as a literal in every router module / under `app/`". Three of the five
  `x-refusals` in `todo_list.yaml` would never close.
- The screen. `spec/design/ui/todo-list.md` § The refusals this screen can show places each text
  refusal under its field by `detail.code`. `sed -n 86p frontend/src/api/problem.ts` prints
  `bucket.push(error.msg ?? 'Invalid value')` for a validation list. The only branch that reads a
  code is :150, `return { ...base, type: refusalType(detail.code), detail: detail.message }`.
- The tests. `spec/design/testing.md` § CR-2609-823a gives each `todo_task_text_*` code a router
  test on `POST` and `PATCH`.

Under `api.md`, the router row and Decision 2's reason in `architecture.md` are false instead.
build-backend is handed both as instructions, and the contract freezes at the end of this stage.
The design stage cannot close with the frozen contract and the placement it is built against
saying opposite things, because design-plan would turn one of them into tasks. Hence critical.

**What settles it.** Nothing ranked above both. Both documents are `spec/design/**`.
`spec/design/conventions.md` § Layers puts "business rules" in `services/` and "Pydantic request and
response contracts" in `schemas/`. It also names the guestbook as the worked example, and the
guestbook holds its text bounds as schema constraints. `requirements.md` § R-2 clause 6 asks for "a
reason of its own" and names no layer, and it ranks below `spec/design/**` anyway. A person decides.

**Resolution.** Recommended (A): `api.md`'s reading. The verdict is decided outside the schema,
in the service, as one domain exception per verdict, and the router translates each into its
code. `architecture.md` and the architecture fragment's Decision 2 change to match. The
alternative (B) is `architecture.md`'s reading. It rewrites `api.md` § Shapes and § Refusals,
`todo_list.yaml` `x-refusals`, `ui/todo-list.md` § The refusals this screen can show, the router
tests and ADR draft 2, and the screen loses `detail.code` for three refusals. A is recommended
because four artefacts and the contract gate already assume it. B's own reason, that "Pydantic's
length bound runs before the route", does not arise when the published schema carries no length
bound.

Ready patch for A, `spec/design/architecture.md`:
- § The layer per rule, row `BR-06`, "Where it is held". Replace "the task's text type in the
  context's `schemas/`" with "the context's `services/todo_tasks.py`, which judges the text
  before any write (normalize, then empty, then one line, then measure) and raises one domain
  exception per verdict". "Why that layer": replace the whole cell with "a business rule is
  decided in `services/` (`conventions.md` § Layers); a constraint in the schema would answer with
  FastAPI's list and no code (`spec/design/api.md` § Shapes, `TodoTaskCreate`)".
- Row `BR-07`, "Where it is held". Replace "the same text type, between the normalization and the
  measurement" with "the same judgement in the service, after the empty check and before the
  measurement". Its "Why": replace "and it can be one sequence only where the length is decided. A
  check in the service would run after the schema had already refused the text as too long" with
  "and it is one sequence because the schema carries no length bound to answer first".
- Row `BR-13`, "Where it is held". Replace "the service raises its one domain exception,
  `TodoTaskNotFoundError`," with "the service raises `TodoTaskNotFoundError`".
- § The files, `todo_list/schemas/todo_tasks.py`. Replace "the task's text type — normalize, then
  one line, then measure — and the read and write shapes" with "no text rule, only the read and
  write shapes".
- § The files, `todo_list/services/todo_tasks.py`. Replace "`TodoTaskNotFoundError`" with
  "`TodoTaskNotFoundError`, and the text's judgement with its three domain exceptions".
- :600-603. Replace "and turns the service's one domain exception into the not-found refusal,
  explicitly; the empty, too-long and more-than-one-line refusals never reach it, because the
  schema refuses them before the route runs." with "and turns each of the service's domain
  exceptions into its coded refusal, explicitly: the not-found refusal and the three about a
  task's text, with the sentences `spec/design/api.md` § The to-do list's refusals gives."
- The architecture fragment's Decision 2 and its § The layer per requirement row `R-2` change the
  same way: the text is judged in the service, and the schema carries no bound.

**What was ambiguous.** `conventions.md` § Layers puts business rules in `services/` and request
contracts in `schemas/`. The worked example it names holds `BR-01`'s bounds as schema constraints.
A task's text rule is both a bound and a business rule, so one author followed the sentence
(design-api) and the other followed the worked example (design-architecture).

**What was not found.** The order is not disputed. Both refuse the text before any write, and
both give the one-line reason precedence over too long (`BR-07`). `data-model.md`'s "the schemas
import it" (`TODO_TASK_TEXT_MAX_LENGTH`) is true under either reading, because an import is not a
constraint.

### COH-design-2 — Do the create and update shapes refuse a text, and with its code?

- **kind:** contradiction
- **severity:** major
- **decision_mode:** HITL
- **auto_basis:**
- **ambiguity_source:** spec/design/conventions.md § Layers
- **artifacts:** spec/design/testing.md, spec/design/api.md

**What each says.** `spec/design/testing.md` § CR-2609-823a, the `R-2` row (:759): every case of
`todo-task-text.json` gets its verdict "through the rule and through the create and update shapes,
so a path that skips the shared rule is seen". The red-first list (:859-860) declares
`test_the_create_and_update_shapes_give_every_case_the_same_verdict`, "(a refused case is refused
with the code of its verdict and an accepted one comes out as the stated text)". `spec/design/api.md`
§ Shapes: `TodoTaskCreate.text` is "a required `string` with no `minLength` or `maxLength`", and
`TodoTaskUpdate.text` is "as in `TodoTaskCreate`". The api fragment's ADR entry rejects "(2) custom
Pydantic error types raised from a schema validator".

**Why they cannot both be true.** Under `api.md`, a `TodoTaskCreate` built from `""` or from 201
code points is a valid shape. Nothing in it refuses, so a unit case asserting that the shape
refuses with `todo_task_text_empty` stays red. The one way to turn it green is a validator in the
shape carrying the code, which is the alternative (2) that `api.md`'s author rejected, and it
answers inside FastAPI's list. Under COH-design-1's reading B, the shape does refuse, but with a
Pydantic error type rather than a contract code. So the case as worded holds only through a
rejected design. design-adr flagged it: the test "sits between the two". Graded major. A declared
red-first case that the design forbids from turning green either stalls the wave or pushes
build-backend into the rejected shape, and the three text refusals would then ship without a code.

**What settles it.** Nothing ranked above both. It follows COH-design-1's ruling.

**Resolution.** Under COH-design-1 (A), the unit file proves the rule and proves that the shapes
carry no bound. The code each verdict earns on the wire is already proved by the integration
router and corpus tests.

Ready patch for A, `spec/design/testing.md`:
- :759. Replace "through the rule and through the create and update shapes, so a path that skips
  the shared rule is seen" with "through the rule, while every case builds a valid create and update
  shape, so only the rule can refuse a text".
- :859-860. Replace "`test_the_create_and_update_shapes_give_every_case_the_same_verdict` (a refused
  case is refused with the code of its verdict and an accepted one comes out as the stated text)"
  with "`test_the_create_and_update_shapes_carry_no_bound` (every case, refused ones included,
  builds a valid shape; the code each verdict earns is proved on the wire by
  **tests/integration/test_todo_tasks_corpus.py**)".

**What was ambiguous.** The same sentence as COH-design-1. It lets the text rule sit in `schemas/`
or in `services/`, so "through the shapes" could be read as a test of either.

**What was not found.** No other case in the unit or integration lists assumes a layer. The
router's three code tests, the corpus tests and the contract test hold under COH-design-1 (A) as
they are written.

### COH-design-3 — Does the text-measurement corpus reader move to `frontend/src/lib/text.test.ts`?

- **kind:** contradiction
- **severity:** minor
- **decision_mode:** AUTO
- **auto_basis:** spec/design/conventions.md § Frontend — where a file goes
- **ambiguity_source:** spec/design/conventions.md § Frontend — where a file goes
- **artifacts:** design/delta/architecture.md, design/delta/testing.md

**What each says.** The architecture fragment's Decision 4 says "its corpus-reading test moves with
it". Its build-tests-frontend write set (:138) reads "`frontend/src/lib/text.test.ts` (moved in),
`frontend/src/contexts/guestbook/lib/entryText.test.ts` (moved out)". § This change owns (:243,
:245) repeats both. The testing fragment, § Where this departs from `design/delta/architecture.md`,
says "Decision 4's second half does not hold". `spec/design/testing.md` :988-990 says
`entryText.test.ts` "**stays** in the guestbook's folder and changes one import line", and § Four
file sets (:1097) agrees.

**Why they cannot both be true.** The reader asserts the guestbook's verdicts, so it needs
`AUTHOR_MAX_LENGTH`, `MESSAGE_MAX_LENGTH` and `QUERY_MAX_LENGTH` from `./guestbookEntry`. From
`frontend/src/lib/`, that import lands in a context. Command: `sed -n 377,379p
tests/fitness/test_context_boundaries.py`. Output: `mine: str | None = None` / `if WEB_CONTEXTS in
path.parents:` / `mine = path.relative_to(WEB_CONTEXTS).parts[0]`. A module outside every context
has no context of its own, so every import that reaches `contexts/guestbook/` is an offender.
Graded minor. The fragment names a file nobody will write and marks as removed a file that stays.
Its § Found outside items 1 and 3 also route edits (`D-04`'s witness path, `golden-set/README.md`
lines 104 and 156, two `testing.md` lines) that are then not needed.

**What settles it.** `spec/design/conventions.md` § Frontend — where a file goes, on
`frontend/src/lib/` (:190-192): "Nothing here imports from `components/` or from `contexts/` — both
are dependency arrows pointing backwards." It ranks above both fragments, which are a change's
design. The fitness test is its mechanism.

**Resolution.** The reader stays where it is, and the architecture fragment follows `testing.md`.

Ready patch, `design/delta/architecture.md`:
- Decision 4. Replace ", and its corpus-reading test moves with it." with ". Its corpus-reading
  test, `entryText.test.ts`, stays in the guestbook's folder and changes one import line, because it
  needs the guestbook's bounds and `frontend/src/lib/` imports no context (`conventions.md`
  § Frontend)."
- § The write sets, build-tests-frontend. Replace "`frontend/src/lib/text.test.ts` (moved in),
  `frontend/src/contexts/guestbook/lib/entryText.test.ts` (moved out)" with
  "`frontend/src/contexts/guestbook/lib/entryText.test.ts` (one import line)".
- § This change owns. Delete the `frontend/src/lib/text.test.ts` row. In the `entryText.test.ts`
  row, replace "removed: the corpus reader's old home (build-tests-frontend)" with "one import
  line, to the rule's new home (build-tests-frontend)".
- § Found outside every write set. In item 1, delete "and lines 104 and 156 name
  `frontend/src/contexts/guestbook/lib/entryText.test.ts`, which moves —". In item 3, delete the
  clauses on `contracts/invariants/guestbook.md` line 115 and on `spec/design/testing.md` lines 488
  and 697.

**What was ambiguous.** `conventions.md` § Frontend says a context's rule "moves up here the day a
second context needs it". It says nothing about the rule's corpus test, whose cases carry one
context's bounds, so the architecture author moved the test with the rule.

**What was not found.** The move of `entryText.ts` to `frontend/src/lib/text.ts` is agreed by both,
and so are the three guestbook import edits.

### COH-design-4 — Is `frontend/src/router.test.tsx` inside the change's boundary?

- **kind:** contradiction
- **severity:** major
- **decision_mode:** HITL
- **auto_basis:**
- **ambiguity_source:** spec/design/architecture.md § Who writes what, and where the sets meet
- **artifacts:** design/delta/architecture.md, spec/design/testing.md

**What each says.** `spec/design/testing.md` § Four file sets (:1097) gives build-tests-frontend
**frontend/src/router.test.tsx** as a new file. § CR-2609-823a makes it the proof of `R-5` for "the
to-do list's own address" and "the main address" (:762), and the characterisation test (:831). The
architecture fragment's build-tests-frontend write set (:138) does not name it, and neither does its
§ This change owns, the table that `set-boundary --from-design` records. Commands:
`grep -c router.test.tsx design/delta/architecture.md` printed `0`, and
`ls frontend/src/router.test.tsx` printed `No such file or directory`.

**Why they cannot both be true.** The implement wave's gate judges the worktree diff against the
recorded boundary. The plugin's `skill_gate.py` says so at :1070-1073: "the boundary says *this
change* owns one named module under it. A path satisfies the first and violates the second
exactly where scope grows without anybody deciding it did." So the file is refused at implement,
or its author drops it to pass the gate. The same module records a builder that reverted its own
necessary edit for exactly that reason (`boundary_refusal`'s docstring). `R-5` clauses 1 and 3
have no other citing proof: `PageFrame.test.tsx` proves clause 2 and `StatusPages.test.tsx` proves
clause 4. Graded major, because those two clauses would ship with no citing proof.

**What settles it.** Nothing ranked above both.

**Resolution.** Add the file to the fragment's write set and to its boundary table.

Ready patch, `design/delta/architecture.md`:
- § The write sets, build-tests-frontend. Append ", `frontend/src/router.test.tsx`".
- § This change owns. After the `frontend/src/router.tsx` row, add "| `frontend/src/router.test.tsx`
  | the vitest cases for the to-do list's own address, the main address and an unknown address
  (`R-5`) (build-tests-frontend) |".

**What was ambiguous.** `spec/design/architecture.md` § Who writes what describes the test authors'
sets by tree and shape ("the vitest files"). So the fragment wrote the test rows of the boundary
from a guess ("if testing.md puts R-5's proof there"), while `testing.md`, written in the same
wave, decided the files.

**What was not found.** Every other path that `testing.md` hands a test author falls under a
boundary row. That covers `tests/unit/`, `tests/fitness/`, `tests/integration/`, `tests/tooling/`,
`tests/_golden_set.py`, `golden-set/fixtures/`, `frontend/src/contexts/todo_list/`,
`PageFrame.test.tsx`, `StatusPages.test.tsx`, `entryText.test.ts` and the four `e2e/` paths.

### COH-design-5 — Does the to-do list claim the screen that now exists?

- **kind:** contradiction
- **severity:** critical
- **decision_mode:** AUTO
- **auto_basis:** spec/constitution.md § Article X — Between two steps the application works
- **ambiguity_source:** spec/contexts/todo_list.md, the paragraph "The header claims a screen and a black-box file only once they exist"
- **artifacts:** spec/contexts/todo_list.md, spec/design/ui/todo-list.md

**What each says.** `spec/contexts/todo_list.md`:7 has `screens: []`, and :23 says "The header
claims a screen and a black-box file only once they exist." `spec/design/ui/todo-list.md` exists,
with `info_ref: S-02` (:4). design-ui's fragment (item 1) and design-domain's assumption both say
the header has to claim it. Neither author could write `spec/contexts/` at that point.

**Why they cannot both be true.** The screen exists, so by the context document's own sentence its
header claims it, and the header does not. Command: `./scripts/test.sh fitness`. Output:
`FAILED tests/fitness/test_context_declarations.py::test_every_registered_screen_is_claimed_by_exactly_one_context`
and `2 failed, 337 passed`. The other failure,
`test_every_context_document_has_code_and_every_context_directory_has_a_document`, is the red that
`testing.md` § Existing detectors declares until build-backend runs. This one is declared nowhere,
and it is not a test written before its implementation. No implement author writes
`spec/contexts/`, so it would stay red until `spec_sync`.

**What settles it.** `spec/constitution.md` § Article X: "A stage never ends red", except for
declared failures of a test written before its implementation. The screen document is this stage's
product, so the only edit that ends the stage green is the claim. Graded critical, because the
stage cannot close without it.

**Resolution.** The convergence round writes the claim and declares the edit in its fragment.

Ready patch, `spec/contexts/todo_list.md` front matter: replace `screens: []` with
`screens: [spec/design/ui/todo-list.md]`.

**What was ambiguous.** The header's sentence says when a screen is claimed, but not who claims it.
The author whose file makes the claim true, design-ui, cannot write `spec/contexts/`.

**What was not found.** No other context claims `S-02`. `spec/contexts/guestbook.md` claims
`spec/design/ui/guestbook.md` alone.

### COH-design-6 — Which step claims `e2e/suite/features/todo_list.feature`, and which stage carries the red meanwhile?

- **kind:** gap
- **severity:** major
- **decision_mode:** HITL
- **auto_basis:**
- **ambiguity_source:** spec/contexts/todo_list.md, the paragraph "The header claims a screen and a black-box file only once they exist"
- **artifacts:** spec/design/testing.md, spec/contexts/todo_list.md

**What each says.** `spec/design/testing.md` § Existing detectors (:976-980):
`test_every_feature_file_is_claimed_by_exactly_one_context` is "red from the test wave … until
`spec/contexts/todo_list.md` claims it; no implement author writes `spec/contexts/`, and a claim
written before the file exists turns `test_every_screen_and_feature_a_context_names_is_on_disk`
red instead. **Unresolved, and handed to the coherence gate.**" The testing fragment offers options
A, B and C. `todo_list.md` has `features: []` and the "only once they exist" rule. The architecture
fragment's item 4 and design-domain's assumption describe the same timing.

**Why it is a gap.** No artefact disagrees about the facts, and none picks an option. Every option
inside this change leaves a structural red standing at a stage boundary. Article X allows only a
declared failure of a test written before its implementation. So design-plan has nothing to
declare the red against, on any task.

**What settles it.** Nothing. Article X narrows the choice and does not make it. Which stage
carries a declared structural red is a process decision for a person.

**Resolution.** Recommended (A): the convergence round writes
`features: [e2e/suite/features/todo_list.feature]` at design close. design-plan then declares
`test_every_screen_and_feature_a_context_names_is_on_disk` red on build-tests-e2e's task, expiring
when that author writes the file in the first implement wave. It is the shortest red of the three,
declared before the run that shows it. It is also the same kind of red the stage already carries,
the specification ahead of the code (the red on the context document with no code). (B): the
implement stage ends with the claim case red and reconcile-spec claims the file. The red then spans
the whole implement stage. (C): the profile lets one implement member write the header's
`features` line. That is a change to the template, filed upstream, and this change cannot make it.

**What was ambiguous.** The same header sentence as COH-design-5. It says when a file is claimed,
and the implement composition has nobody who can claim it.

**What was not found.** The screen half of this timing is not a gap. The screen document exists
now, so COH-design-5 closes it in this stage.

### COH-design-7 — Does the retention non-goal name tasks, or is `A-2` still awaiting the user?

- **kind:** contradiction
- **severity:** minor
- **decision_mode:** AUTO
- **auto_basis:** spec/invariants.md § Deliberate non-goals
- **ambiguity_source:** spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/requirements.md § Named assumptions
- **artifacts:** requirements.md, design/delta/converge.md

**What each says.** `requirements.md` § Impact analysis (:525-527): "the retention item stays
worded for entries while `A-2` (§ Named assumptions) waits for the user". `A-2` (:737-738): "Until
this is confirmed, that non-goal keeps its wording for entries alone. **Status:** assumed, awaiting
the user." `design/delta/converge.md` says the user approved `requirements.md` at the stage gate,
so `A-2` is a human decision and the retention item now names tasks. `spec/invariants.md`:162
reads "An entry, like a to-do task, lives until somebody deletes it." Commands: `git log --oneline
-- spec/invariants.md` printed `1c51b88` (the review-converge after pass 3) on top, and the same for
`requirements.md` printed `35a2234`, an earlier commit.

**Why they cannot both be true.** `requirements.md` describes the non-goal's wording as covering
entries alone, and the non-goal names tasks. A design reader of the requirements is told the
opposite of the document that binds every change. Graded minor, because no behaviour differs.
design-domain and design-spec read `spec/invariants.md` directly, and both wrote "the non-goal names
tasks".

**What settles it.** `spec/invariants.md` § Deliberate non-goals, which ranks above both and names
the task.

**Resolution.** review-converge brings the two sentences level with the non-goal.

Ready patch, `requirements.md`:
- § Impact analysis. Replace "and the retention item stays worded for entries while `A-2`
  (§ Named assumptions) waits for the user." with "and, since the user approved this document with
  `A-2` standing, the retention item names tasks too (`design/delta/converge.md`)."
- `A-2`. Replace "Until this is confirmed, that non-goal keeps its wording for entries alone.
  **Status:** assumed, awaiting the user." with "**Status:** confirmed at this document's approval;
  `spec/invariants.md` § Deliberate non-goals names tasks since."

**What was ambiguous.** § Named assumptions says in its preamble that the approval confirms or
overrules each assumption. It names no step that writes the outcome back into the Status lines.

**What was not found.** `A-1`, `A-3` and `A-4` carry the same "awaiting the user" status, while
`todo_list.md` § Language and § `BR-07` state the set and the trim reading as rules, and
`ui/system-states.md` renames the lockup under `A-4`. No document says those three are still open,
so they are not graded here. The same write-back would correct them.

### COH-design-8 — Is the guestbook still the only domain context?

- **kind:** contradiction
- **severity:** minor
- **decision_mode:** AUTO
- **auto_basis:** spec/constitution.md § Article IV — The specification changes on the same branch as the code
- **ambiguity_source:** spec/design/conventions.md § Backend — where a file goes
- **artifacts:** spec/design/conventions.md, spec/README.md, spec/design/architecture.md

**What each says.** `spec/design/architecture.md` § Contexts and their boundaries: "Two domain
contexts and one supporting technical slice." `spec/design/conventions.md` § Backend (:77):
"`guestbook` is the **only** domain context of this template". `spec/README.md` (:58-59): "The
only domain context is the **guestbook**, and it is deliberately trivial: four operations, one
table, one screen."

**Why they cannot both be true.** Once `spec/contexts/todo_list.md` exists, the count is two. No
design author's write set holds either sentence. design-spec reported `spec/README.md` for others.
Nobody reported `conventions.md` § Backend. Graded minor, because it costs a later edit.

**What settles it.** `spec/constitution.md` § Article IV: "A change of behaviour and the
specification edit that describes it land in one pull request. Never in the next one." The count is
a fact this change creates, not a product choice.

**Resolution.** Correct both sentences in this change and declare the edits. The convergence round
can do it, or reconcile-design for `conventions.md` and whichever member holds `spec/README.md`.

Ready patch:
- `spec/design/conventions.md` § Backend. Replace "`guestbook` is the **only** domain context of
  this template and at the same time its worked example through every layer: copy it, and when your
  own context replaces it, delete it." with "`guestbook` is this template's worked example through
  every layer: copy it, and when your own context replaces it, delete it. The to-do list
  (`todo_list`) is a second domain context and is not an example."
- `spec/README.md`. Replace "The only domain context is the **guestbook**, and it is deliberately
  trivial: four operations, one table, one screen." with "The example domain context is the
  **guestbook**, and it is deliberately trivial: four operations, one table, one screen. The to-do
  list beside it is not an example and stays when the guestbook is deleted."

**What was ambiguous.** `conventions.md` § Backend states a count of contexts inside a sentence
about where routers go, so the next context makes it false without touching routers.

**What was not found.** `conventions.md` § Frontend :172-175 ("the browser has exactly one"
caller) becomes false with the move. The architecture fragment already routes it to
reconcile-design (its item 3), so it is not repeated here. `spec/glossary.md`:8 is historical and
true.

### What was checked and agrees

- **`data-model.md` ↔ `api.md`.** The fields match: `id`, `text`, `done` and `created_at`, all
  `NOT NULL` and all required on the wire. So do the ordering (`created_at DESC, id DESC`, with no
  pieces), the "exactly 1" of each write, the 404 when no row is returned (the statement shape), and
  the combined `PATCH`. That last one names only the columns the person sent, which is § Two writers
  on one task's general rule.
- **`api.md` ↔ `todo_list.yaml`.** The two paths, four operations, four shapes, `total ≥ 0`, the
  five codes and their statuses, and the `anyOf` on both `422`s all match.
- **`api.md` ↔ `ui/todo-list.md` ↔ the mock-up.** Every binding is to a field the contract returns
  (`total`, `items[].id/.text/.done`). A tick sends `done` alone and a correction sends `text`
  alone. `created_at` is not shown. The four refusal sentences, the empty and failure sentences, the
  footer and the 404 sentence are byte-identical in `api.md`, the screen documents and
  `design/ui/index.html` (grep over the mock-up).
- **`ui/todo-list.md` ↔ `system-states.md` ↔ `guestbook.md`.** The navigation links, the marked
  screen, the per-screen footer, the lockup's "Product name" / "P" and the error toast that stays
  until dismissed all match. `testing.md`'s R-6 case "keeps the old text and says why" agrees with
  the screen's reading. The stored text stays the box's name and comes back on "Cancel", while the
  editor keeps what was typed.
- **`todo_list.md` ↔ `guestbook.md`.** The kernel is declared on both sides as
  `peer:shared-kernel`. `BR-01` names its second holder, and neither side restates the other's rules.
  `BR-06`…`BR-13` are carried consistently by the registers, the screen and the tests. `BR-07`'s
  precedence is identical in `api.md`, the screen, `todo_task_text_multiline`'s `when` and the
  testing corpus case.
- **`requirements.md` ↔ the design.** Every `R-1`…`R-11` is carried by a rule, a register entry or
  the frame, and each has an owning suite in `testing.md` (`R-11` stays manual, as it states). The
  row staying on screen after "no longer exists" (C-19) agrees with `R-8.1`'s "after a reload".
- **`scenarios.md` § Test data ↔ `data-model.md`.** Every fixture fits the schema. The data-model
  fragment's table uses the scenarios' file names (`tasks-welcome.json`) because it judges
  `scenarios.md`. `testing.md` renames them `todo-tasks-*` and says so, with every value standing.
- **Glossary.** *Task* (domain, `TodoTask`) and *Task (process)* stay apart in every artefact. No
  identifier uses a bare `task`.
- **Invariants.** `D-01`, `D-02` and `D-03` hold (one row per task, no foreign key, an
  application-side UUID). The task-text invariant that `data-model.md` calls for is unwritten, and
  it is left to the convergence round as its fragment says. When it is written, its witnesses name
  test files that do not exist until implement, and `test_invariant_witnesses.py` requires a
  witness to resolve. Whoever writes it has to account for that.
- **The authors' assumptions.** Checked one by one. design-api's and design-architecture's are false
  of each other (COH-design-1). design-testing's and design-adr's both name COH-design-3 and
  COH-design-2. design-domain, design-ui and design-testing name COH-design-5 and COH-design-6.
  Every other stated assumption matches what the neighbour wrote. That includes `todo_tasks` and
  `TodoTask`, the route `/todo-list`, the seed file `todo-tasks-example.json`, `Checkbox.tsx`, the
  answer-only cache, the five codes and the seven line breaks.

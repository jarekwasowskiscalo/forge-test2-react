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

## Pass 5 — the `design` stage

The preflight printed `CONVERGENCE ROUND: 1 of 3 -- MODE: DEEP`, so Phase 1b ran first over the
eight recorded resolutions, and a full hunt followed it. Artefacts read whole: the eight
fragments under `design/delta/` (`converge.md` included), both ADR drafts, `design/ui/index.html`
(searched), `spec/contexts/todo_list.md`, `spec/design/ui/todo-list.md`,
`contracts/openapi/todo_list.yaml`, the diffs against `main` of `spec/design/api.md`,
`architecture.md`, `data-model.md`, `conventions.md`, `ui/system-states.md`, `ui/guestbook.md`,
`spec/contexts/guestbook.md`, `spec/glossary.md`, `spec/README.md` and
`contracts/openapi/README.md`, `spec/design/testing.md` § Fitness functions and
§ CR-2609-823a whole, `requirements.md` whole, `scenarios.md` § Coverage and its preamble, and
the nine `ASSUMPTIONS` blocks from the preflight. The ranked documents read above them:
`spec/constitution.md`, `spec/invariants.md`, `spec/glossary.md`, `contracts/README.md`. The
material this round changed was read against `git diff 6cde44b HEAD`.

### Recorded resolutions

- COH-design-1: landed. `spec/design/conventions.md`:42-52 (§ Layers, the paragraph with the
  user's words). Its artefact-level patches: `spec/design/architecture.md`:588-589 (`BR-06`,
  `BR-07` held in the service), :600-603 (the router translates each domain exception), :613-614
  (the schema holds no text rule; the service holds the judgement and its three exceptions);
  `design/delta/architecture.md`:45-54 (Decision 2) and :87 (row `R-2`).
- COH-design-2: landed. `spec/design/conventions.md`:42-52; `spec/design/testing.md`:759 ("through
  the rule, while every case builds a valid create and update shape") and :859-861
  (`test_the_create_and_update_shapes_carry_no_bound`).
- COH-design-3: landed. `spec/design/conventions.md`:184-187 ("Only the rule moves up");
  `design/delta/architecture.md`:60-68 (Decision 4), :142 (the write set), :245 (§ This change
  owns); no `text.test.ts` row is left.
- COH-design-4: landed. `spec/design/architecture.md`:664-673; `design/delta/architecture.md`:142
  and :256.
- COH-design-5: landed. `spec/contexts/todo_list.md`:7 and :23-32.
- COH-design-6: landed. `spec/contexts/todo_list.md`:8 and :23-32.
- COH-design-7: landed. `requirements.md`:525-527, :673-675, :737-738, :836-837.
- COH-design-8: landed. `spec/design/conventions.md`:89-91; `spec/README.md`:58-61.

No `verification` finding. What the landed resolutions left standing beside them is below, as
new contradictions (COH-design-9, COH-design-13, COH-design-14).

Pairs compared: `data-model.md` ↔ `api.md`; `api.md` ↔ `todo_list.yaml`; `api.md` ↔
`ui/todo-list.md`; `api.md` ↔ `architecture.md` (live and fragment); `conventions.md` § Layers ↔
`architecture.md` ↔ `data-model.md` ↔ the guestbook's worked example; `testing.md` ↔
`todo_list.md` (the header's claims) ↔ the fitness run; `testing.md` ↔ the api fragment (the
contract gate); `testing.md` ↔ `ui/todo-list.md`; `testing.md` ↔ `data-model.md`; `testing.md` ↔
both ADR drafts; `requirements.md` ↔ itself and ↔ `converge.md`; `contracts/README.md` ↔
`todo_list.yaml`; `requirements.md` `R-1`…`R-11` ↔ each design artefact; every artefact ↔ the
glossary and the invariants; each author's assumptions ↔ what its neighbour wrote.

### COH-design-9 — Which fitness case is red until the black-box file exists: the claim case, or the on-disk case?

- **kind:** contradiction
- **severity:** major
- **decision_mode:** AUTO
- **auto_basis:** spec/constitution.md § Article X — Between two steps the application works
- **ambiguity_source:** spec/design/testing.md § CR-2609-823a, the to-do list
- **artifacts:** spec/design/testing.md, spec/contexts/todo_list.md

**What each says.** `spec/design/testing.md` § CR-2609-823a, "Existing detectors that go red on
the way", third bullet (:977-984): `test_every_feature_file_is_claimed_by_exactly_one_context` is
"red from the test wave, when **e2e/suite/features/todo_list.feature** appears, until
`spec/contexts/todo_list.md` claims it", then "**Unresolved, and handed to the coherence gate.**"
The list says of itself that "each is declared on the task whose product closes it", and it does
not name `test_every_screen_and_feature_a_context_names_is_on_disk`. `spec/contexts/todo_list.md`
:8 claims `features: [e2e/suite/features/todo_list.feature]` since the convergence round, and
:23-32 says "the plan declares `test_every_screen_and_feature_a_context_names_is_on_disk` red on
the task that writes the file" (`Q-19`). review-converge's assumption says the same.
`design/delta/architecture.md` § Found outside every write set, item 4, still describes the
timing from before the claim.

**Why they cannot both be true.** Command: `./scripts/test.sh fitness`. Output: `FAILED
tests/fitness/test_context_declarations.py::test_every_screen_and_feature_a_context_names_is_on_disk`,
the context-document case, and `2 failed, 337 passed`. The claim case iterates the feature files
on disk (`tests/fitness/test_context_declarations.py`:273-284, `present = {... FEATURES.glob("*.feature")}`)
and finds each claimed once, so it cannot go red when the file appears. So `testing.md` names a
declared red that will never occur and omits the one that is red now. design-plan turns this list
into `**Must be red:**` lines. If it follows `testing.md`, the gate refuses the declaration (a
declared red with no run where it failed) and finds the real red undeclared. Graded major: the
list the plan is built from would close the stage red.

**What settles it.** `spec/constitution.md` § Article X: a deliberate red "is declared *before*
the run that shows it, must be proved to have actually occurred". Only the on-disk case meets
both halves. It is declared before any implement run and its failure is observed above. The claim
case can meet neither.

**Resolution.** `testing.md`'s third detector names the on-disk case, declared on build-tests-e2e's
task, and drops "Unresolved".

Ready patch, `spec/design/testing.md` § CR-2609-823a, the third bullet of "Existing detectors that
go red on the way". Replace the whole bullet with: "`tests/fitness/test_context_declarations.py::test_every_screen_and_feature_a_context_names_is_on_disk`
— red since the design stage's convergence round claimed **e2e/suite/features/todo_list.feature**
in `spec/contexts/todo_list.md` before the file exists (`CR-2609-823a`, `Q-19`), and declared on
build-tests-e2e's task, whose product is the file, in the first implementation wave.
`test_every_feature_file_is_claimed_by_exactly_one_context` and
`test_every_registered_screen_is_claimed_by_exactly_one_context` stay green throughout, because
the header claims both files." In `design/delta/architecture.md` § Found outside every write set,
item 4, replace the two sentences on the screen and feature claim cases with "Both claims are in
`spec/contexts/todo_list.md` since the convergence round (COH-design-5, COH-design-6); the
on-disk case is red until build-tests-e2e writes the feature file."

**What was ambiguous.** The bullet handed the timing to the coherence gate and named no route for
the answer to come back. COH-design-6's resolution landed in the context header. The
re-dispatched design-testing was scoped to COH-design-2 alone (TD-2), so the bullet was never
revisited.

**What was not found.** The first bullet (the context-document case) is still true. Its measured
count, "1 failed, 338 passed", is dated 2026-09-24 and was true on that run.

### COH-design-10 — Who declares that `./scripts/check.sh` is red on the contract gate from design close until the backend exists?

- **kind:** gap
- **severity:** major
- **decision_mode:** HITL
- **auto_basis:**
- **ambiguity_source:** spec/design/testing.md § CR-2609-823a, the to-do list
- **artifacts:** design/delta/api.md, spec/design/testing.md

**What each says.** `design/delta/api.md` § What the contract gate says today: `./scripts/contracts.sh`
"exits 1 on this tree with 11 findings … they close when the backend's routers and schemas exist.
Until then `./scripts/check.sh`, which runs this gate, is red on it." `spec/design/testing.md`
§ CR-2609-823a, "Existing detectors that go red on the way", lists "the structural cases" the
specification runs ahead with, "each … declared on the task whose product closes it". It lists
fitness and corpus cases only, and says nothing of the contract gate.

**Why it is a gap.** Commands and outputs. `./scripts/contracts.sh` printed `11 problem(s)
against 3 contracts, 5 paths, 10 operations` and `API contract is frozen: FAILED`.
`grep -n contracts scripts/check.sh` printed `120:gate "API contract is frozen"
"$REPO_ROOT/scripts/contracts.sh"`. The engine's `gate.py`:233 runs a stage boundary as
`"boundary": (check, specs_boundary)`, with `check` as one opaque gate. `plan_grammar.py`:62 and
:102-108 accept a declared red only as `classname::name` out of a junit, and no junit carries a
contract finding. So the design boundary, and every implement boundary before build-backend's
wave, meets a red in `check` that no `**Must be red:**` line can name. `close_stage` then demands
an `--accept-red` whose reason names the gate. No artefact writes that reason before the run,
while Article X requires the declaration before the run. Graded major. The fact is known and
recorded only in a change fragment, and the list that plans the reds leaves it out.

**What settles it.** Nothing ranked above both. `spec/constitution.md` § Article X excuses "a
test written before its implementation", and a contract written before its implementation
reddens a gate, not a test. Whether such a red may cross a stage boundary under a named
acceptance is a process decision for a person.

**Resolution.** Recommended (A): `testing.md` names the contract gate among the reds the
specification runs ahead with, closing with build-backend's schemas and routers. Each boundary
until then accepts the gate by that name and reason. The per-case gap is filed as a process fault.
(B): `contracts/openapi/todo_list.yaml` lands with build-backend's wave, and `spec/design/api.md`
alone is frozen at design close. That undoes design-api's ADDED entry and the frozen machine
contract the two implementers were to build against.

Ready patch for A, `spec/design/testing.md` § CR-2609-823a, "Existing detectors that go red on the
way", a new last bullet: "`./scripts/contracts.sh`, a gate of `./scripts/check.sh` — red since
`contracts/openapi/todo_list.yaml` exists, with 11 findings (four schemas and two paths the dump
does not have yet, five refusal codes no router module holds yet), green when build-backend's
schemas and routers exist. It is a gate, not a test case, so no `**Must be red:**` line can name
it. The design boundary, and each implementation boundary before build-backend's wave, accepts
`check` red on this gate alone, with this sentence as the reason."

**What was ambiguous.** The detectors paragraph scopes itself to "structural cases", so the one
red the specification runs ahead with on purpose and no case carries fell outside its list. The
api author reported it in the fragment, which nothing reads when planning reds.

**What was not found.** No other gate of `check` is red for this change: the fitness run above
shows the two cases already discussed, and `contracts.sh` raises nothing against `guestbook.yaml`
or `health.yaml`.

### COH-design-11 — Does the to-do screen send a new task's text as typed, or as the shared rule leaves it?

- **kind:** contradiction
- **severity:** minor
- **decision_mode:** HITL
- **auto_basis:**
- **ambiguity_source:** spec/design/ui/guestbook.md § Data
- **artifacts:** spec/design/ui/todo-list.md, spec/design/testing.md

**What each says.** `spec/design/ui/todo-list.md` § Data (:240): adding "sends `text` as typed".
`spec/design/testing.md` § CR-2609-823a, red-first list (:913-916), gives
**frontend/src/contexts/todo_list/components/TodoTaskComposer.test.tsx** the case "sends the text
as the shared rule leaves it" (`[req:CR-2609-823a/R-1]`).

**Why they cannot both be true.** For "  Buy bread  " the first sends the padding and the second
sends "Buy bread". build-frontend works from the screen document, and build-tests-frontend writes
the case first, from `testing.md`. A composer built to the screen document fails a test its
builder may not edit. The guestbook does the second.
`sed -n 53,58p frontend/src/contexts/guestbook/components/EntryComposer.tsx` prints the comment
"what is sent should be what the browser measured" above `author: normalizeEntryField(author)`.
Graded minor. The service normalizes either way, so nothing stored differs. The cost is one
disputed test in the implement wave.

**What settles it.** Nothing ranked above both. `requirements.md` § R-2 clause 5 fixes the verdict
on both sides and says nothing of the payload.

**Resolution.** Recommended: the screen sends the text as the shared rule leaves it, as the
guestbook does.

Ready patch, `spec/design/ui/todo-list.md` § Data, the adding row. Replace "sends `text` as typed"
with "sends `text` as the shared rule leaves it — normalized and trimmed, the text the screen
judged". The alternative edits `testing.md`:915-916 to "sends the text as typed".

**What was ambiguous.** `spec/design/ui/guestbook.md` § Data names the posting hook
(`useCreateGuestbookEntry()`) and not what it sends. The worked example's payload rule lives only
in its code, so design-ui derived one reading and design-testing copied the other.

**What was not found.** The correction row ("sends `text` alone") takes no side, and no other
payload differs between the two documents.

### COH-design-12 — Where is `todo_task_empty_patch` decided: beside the endpoint, or in the service?

- **kind:** contradiction
- **severity:** minor
- **decision_mode:** HITL
- **auto_basis:**
- **ambiguity_source:** spec/design/conventions.md § Layers
- **artifacts:** spec/design/conventions.md, spec/design/architecture.md

**What each says.** `spec/design/conventions.md` § Layers (:42): "**A rule whose refusal carries a
code of its own is judged in `services/`**". `spec/design/architecture.md` § The layer per rule
(:600-603): the router "turns each of the service's domain exceptions into its coded refusal,
explicitly: the not-found refusal and the three about a task's text". § The files (:614) gives the
service `TodoTaskNotFoundError` and "the text's judgement with its three domain exceptions". Neither
places `todo_task_empty_patch`, a coded refusal (`spec/design/api.md`:374). `spec/design/api.md`
§ Shapes, `GuestbookEntryUpdate` (:120-121), says of the same refusal on the guestbook: "the
refusal is about the request, and that is why it lives beside the endpoint rather than in the
schema". design-api assumed "the router translates it into the 5 coded refusals".

**Why they cannot both be true.** The guestbook's router decides its empty patch itself:
`sed -n 184-188p app/contexts/guestbook/routers/guestbook_entries.py` prints `if data.author is
None and data.message is None:` then `raise HTTPException(` … `"code":
"guestbook_entry_empty_patch"`. Read literally, the new sentence in § Layers forbids that for
every coded refusal. `architecture.md` names four service exceptions, which leaves the to-do
list's empty patch to the router. So build-backend meets a rule that pulls the check into the
service, and a placement that leaves it outside. Graded minor. The contract's order
(`spec/design/api.md` § The to-do list's refusals, items 2-4) holds either way, so the cost is
one edit.

**What settles it.** Nothing ranked above both. `spec/constitution.md` § Article XIII forbids
"Business logic in routers" and does not say whether a body that sets no field is business
logic.

**Resolution.** Recommended: the sentence in § Layers speaks of a rule about a field's value. A
refusal about the request as a whole is decided beside the endpoint, as `api.md` says, and
`architecture.md` names it.

Ready patch. In `spec/design/conventions.md` § Layers, replace "**A rule whose refusal carries a
code of its own is judged in `services/`, and `schemas/` holds no part of it.**" with "**A rule
about a field's value whose refusal carries a code of its own is judged in `services/`, and
`schemas/` holds no part of it.** A refusal about the request as a whole, a `PATCH` that sets no
field, is decided beside the endpoint before the service is called (`spec/design/api.md`
§ Shapes, `GuestbookEntryUpdate`)." In `spec/design/architecture.md` § The layer per rule, append
to the router paragraph: "It answers `todo_task_empty_patch` itself, before it calls the service,
as the guestbook's router answers its empty patch."

**What was ambiguous.** The paragraph was written to settle schemas against services
(COH-design-1). Its subject, "a rule whose refusal carries a code", also covers a refusal the
router already decides.

**What was not found.** No test fixes the layer: `test_a_patch_setting_neither_field_is_refused`
(`spec/design/testing.md`:777) goes through the router and holds under either placement.

### COH-design-13 — Does the to-do list's schema import any part of the text rule?

- **kind:** contradiction
- **severity:** minor
- **decision_mode:** HITL
- **auto_basis:**
- **ambiguity_source:** spec/design/conventions.md § Layers
- **artifacts:** spec/design/data-model.md, design/delta/architecture.md

**What each says.** `spec/design/data-model.md` § `todo_tasks`, "The bound, beside the model"
(:252-253): "the column is declared from it and the schemas import it".
`design/delta/architecture.md` § What this change does not move (:192-193):
"`app/platform/schemas/text.py` — the kernel's server half is imported by the to-do schema as it
stands". Against both: `spec/design/conventions.md` § Layers (:42-52), "`schemas/` holds no part
of it", with the rule spelled "normalize, then empty, then one line, then measure", and
`spec/design/architecture.md` § The files (:613), `todo_list/schemas/todo_tasks.py` holds "no text
rule, only the read and write shapes". The fragment's own Decision 2 and row `R-2` put the kernel
under the service's judgement.

**Why they cannot both be true.** The kernel's `normalize` and `length`
(`app/platform/schemas/text.py`:96, :115) and the bound are the rule's parts. An import is only
kept if it is used: `pyproject.toml` § `[tool.ruff.lint]` selects `"F"`, commented "unused
imports". The guestbook's schema uses its bounds as `Field(min_length=1,
max_length=AUTHOR_MAX_LENGTH)` (`app/contexts/guestbook/schemas/guestbook_entries.py`:50), which
is the form Q-17 rejected. So the two sentences can come true only through a use the design
forbids, or a use nothing needs. Pass 4 read the import as harmless, "an import is not a
constraint". That was before § Layers said the schema holds no part of the rule. Graded minor.
Every other document names the service, and the router tests would catch a bound in the schema.

**What settles it.** Nothing ranked above `data-model.md`. For the fragment alone,
`spec/design/architecture.md` § The files ranks above it and says the schema holds no text rule.

**Resolution.** The service's judgement imports the kernel and the bound, and the to-do schema
imports neither.

Ready patch. `spec/design/data-model.md` § `todo_tasks`: replace "the column is declared from it
and the schemas import it" with "the column is declared from it and the service's judgement of a
text imports it; the schemas do not (`spec/design/conventions.md` § Layers)".
`design/delta/architecture.md` § What this change does not move: replace "imported by the to-do
schema as it stands" with "imported by the to-do service's judgement as it stands".

**What was ambiguous.** "`schemas/` holds no part of it" does not say whether importing the
bound or the kernel counts as holding it. Both sentences copy the guestbook's pattern
(`spec/design/data-model.md` § `guestbook_entries`, "imported by the schemas"), and COH-design-1's
patch list named neither line.

**What was not found.** `spec/design/architecture.md` § Rules between contexts ("live the same
way, beside `TodoTask`") says where the constants live and not who imports them. It is true under
the resolution.

### COH-design-14 — Were `A-1`, `A-3` and `A-4` confirmed at the approval that confirmed `A-2`?

- **kind:** contradiction
- **severity:** minor
- **decision_mode:** HITL
- **auto_basis:**
- **ambiguity_source:** spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/requirements.md § Named assumptions
- **artifacts:** requirements.md, design/delta/converge.md

**What each says.** `requirements.md` § Named assumptions: the preamble (:720-721), "No item below
is a human decision yet. The user confirms or overrules each one at the approval of this
document"; `A-1` (:732), `A-3` (:751) and `A-4` (:761), "**Status:** assumed, awaiting the user";
§ Impact analysis (:519), "(assumed: `A-2`)". Against these: `A-2` (:737-738), "confirmed at this
document's approval"; § Impact analysis (:526), in the same bullet as :519; § Non-Goals
(:674-675); Self-check 23 (:837). `design/delta/converge.md` says the user approved the document
and that "none was overruled, so `A-2` is a human decision".

**Why they cannot both be true.** One approval confirmed the document. The file now says it
confirmed one assumption and left the other three awaiting, and its own preamble says it
confirmed none. The design treats all four as settled. `spec/contexts/todo_list.md` § Language
states `A-1`'s seven characters and § `BR-07` states `A-3`'s trim reading as rules.
`spec/design/ui/system-states.md` § Copy renames the lockup, which is `A-4`'s premise. Graded
minor, because no behaviour differs. COH-design-7 wrote back `A-2` alone, and review-converge
flagged the other three as needing "the same write-back later", with no owner.

**What settles it.** Nothing ranked above `requirements.md` records the approval's outcome. It is
recorded only in the change record and in `converge.md`, which rank below. The human step is to
confirm that the approval covered all four. It is not a new question.

**Resolution.** The preamble and the three Status lines say what the approval did.

Ready patch, `requirements.md`. The § Named assumptions preamble: replace "No item below is a
human decision yet. The user confirms or overrules each one at the approval of this document,
which ends the stage." with "The user confirmed or overruled each one at the approval of this
document, which ended the stage; none was overruled." `A-1`, `A-3`, `A-4`: replace "**Status:**
assumed, awaiting the user." with "**Status:** confirmed at this document's approval." § Impact
analysis :519: replace "(assumed: `A-2`)" with "(`A-2`, confirmed at approval)". Self-check 4
(:775-776): replace "for the user to confirm at this document's approval" with "confirmed at this
document's approval".

**What was ambiguous.** The preamble says the approval confirms or overrules each assumption. It
names no step that writes the outcome back, which is COH-design-7's ambiguity again, now
resolved for one item of four.

**What was not found.** The SC-5 cell (:27, "assumed: `A-4`") describes the measurement, not a
status, and needs no edit beyond the `A-4` line it cites.

### COH-design-15 — Does the black box tell the three text refusals apart?

- **kind:** contradiction
- **severity:** minor
- **decision_mode:** AUTO
- **auto_basis:** spec/design/testing.md § CR-2609-823a, the to-do list
- **ambiguity_source:** spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/scenarios.md § Coverage
- **artifacts:** design/adr/task-text-refusals-are-coded-not-schema-constraints.md, design/delta/testing.md

**What each says.** The ADR draft, § Context (:20-21): "The black box has to tell the three
reasons apart (`S-6`, `S-8`, `S-33`)." The api fragment's **Why** (:12) says the same. The testing
fragment, § Where this departs from `scenarios.md`, item 3: "The black box does not bind S-5, S-6,
S-8, S-13 or S-33."

**Why they cannot both be true.** The draft's premise is a claim about a suite, and the design has
decided the opposite. Once reconcile-design numbers the ADR it is never rewritten, so the false
premise would stand in the one record that "cannot be edited out" (constitution, Article IX). The
decision itself survives, because `R-2` clause 6 and the screen's placement by `detail.code` each
still need the three codes. Graded minor.

**What settles it.** `spec/design/testing.md` § CR-2609-823a, the to-do list, "What the black box
binds": the seeds that look a text up in a fixture file, "the refused outline, the one-line
refusal … and the refused corrections", are proved by **tests/integration/test_todo_tasks_corpus.py**
"and not bound in the black box". It is the home for the choice of a suite (Article IX) and ranks
above both change documents.

**Resolution.** The draft and the api fragment name the suite that tells the three apart.

Ready patch. In the ADR draft's § Context, replace "The black box has to tell the three reasons
apart (`S-6`, `S-8`, `S-33`)." with "The scenarios tell the three reasons apart (`S-6`, `S-8`,
`S-33`), and the integration corpus test proves each on the wire (`spec/design/testing.md`
§ CR-2609-823a)." In `design/delta/api.md`'s **Why**, replace "and the black box has to tell "no
text", "too long" and "more than one line" apart (`S-6`, `S-8`, `S-33`)" with "and the scenarios
tell "no text", "too long" and "more than one line" apart (`S-6`, `S-8`, `S-33`), which the
integration corpus test proves on the wire".

**What was ambiguous.** `scenarios.md` marks those seeds "application" and says of that kind "The
black box can bind it". Both design authors read "can" as "does", and the choice was
design-testing's.

**What was not found.** No other sentence in either draft leans on a suite `testing.md` does not
assign. The draft's "Enforced by" names router, corpus and contract tests that `testing.md` lists.

### COH-design-16 — Which document calls for the task-text invariant, and which round writes it?

- **kind:** contradiction
- **severity:** minor
- **decision_mode:** HITL
- **auto_basis:**
- **ambiguity_source:** spec/invariants.md § Data invariants
- **artifacts:** spec/design/testing.md, spec/design/data-model.md

**What each says.** `spec/design/testing.md` § CR-2609-823a, "The witness for a task's text"
(:802-804): "`data-model.md` calls for a data invariant of the to-do list's own, the counterpart of
`D-04` … and the convergence round writes it". It then names three witnesses. `spec/design/data-model.md`
contains no such call: `grep -n -i invariant spec/design/data-model.md` prints lines 72, 74, 127,
136 and 215, all about `D-03`, `D-04` and the non-goals. The call is only in
`design/delta/data-model.md` § Found outside this write set. design-data assumed that the
convergence round would write it. That round has run (`design/delta/converge.md`, REC-12…REC-19)
and neither wrote it nor mentions it. `ls contracts/invariants/` prints `README.md guestbook.md`.

**Why they cannot both be true.** `testing.md` cites a normative home that does not carry the
call, and a writer that did not write it. The witnesses are test files the implement stage
creates, and `tests/fitness/test_invariant_witnesses.py::test_every_invariant_names_a_witness_that_exists`
refuses a witness that does not exist. So no design-stage round could have written the invariant
green, and no implement author writes `contracts/`. Graded minor. The proofs are in the red-first
list either way. What can go missing is the invariant itself, the counterpart of `D-04` that the
design decided a task's text has.

**What settles it.** Nothing ranked above both on the timing. `spec/invariants.md` § Data
invariants gives `contracts/invariants/` edits to the convergence round, and does not say which
stage's.

**Resolution.** Recommended: `data-model.md` § `todo_tasks` states the call. `testing.md` names
the `spec_sync` stage's convergence round as the writer, because it is the first round after the
witnesses exist.

Ready patch. `spec/design/testing.md` :802-804: replace "`data-model.md` calls for a data invariant
of the to-do list's own, the counterpart of `D-04` for a task's text — NFC, trimmed at both ends, 1
to 200 code points, no line break inside — and the convergence round writes it." with
"`data-model.md` § `todo_tasks` calls for a data invariant of the to-do list's own, the counterpart
of `D-04` for a task's text — NFC, trimmed at both ends, 1 to 200 code points, no line break
inside. The convergence round of the `spec_sync` stage writes it, the first round after its
witnesses exist, since `tests/fitness/test_invariant_witnesses.py` refuses a witness that does not."
`spec/design/data-model.md` § `todo_tasks`, after the column table, add: "Every `text` in this table
is NFC, trimmed at both ends, 1 to 200 code points and one line: a data invariant of the to-do
list's own under `contracts/invariants/`, whose witnesses `spec/design/testing.md` names."

**What was ambiguous.** `spec/invariants.md` § Data invariants names who edits `contracts/` within a
change and not when. An invariant whose witnesses are written in implementation cannot be written
by the stage that decides it.

**What was not found.** `D-01`…`D-03` need no new witness, as `testing.md` says. The sweeps reach
`todo_tasks` through `Base.metadata`.

### COH-design-17 — How many revisions does the migration-safety row describe?

- **kind:** contradiction
- **severity:** minor
- **decision_mode:** AUTO
- **auto_basis:** spec/constitution.md § Article IV — The specification changes on the same branch as the code
- **ambiguity_source:** spec/design/testing.md § Fitness functions
- **artifacts:** spec/design/testing.md, spec/design/data-model.md

**What each says.** `spec/design/testing.md` § Fitness functions, row `test_migration_safety.py`
(:211): the last two rules "are **vacuously true** today — the one revision creates its table and
its index together". `spec/design/data-model.md` § Migrations: "Two revisions, and the second is the
head", and § The revision that creates `todo_tasks` builds its index in the same revision.

**Why they cannot both be true.** After this change there are two revisions. The rules stay
vacuous, because each revision creates its own table and index, but the count is false. design-testing
corrected the other fitness rows' counts (:200, :201, :217) and not this one. Graded minor.

**What settles it.** `spec/constitution.md` § Article IV: the specification edit lands in the same
pull request as the change it describes. The count is a fact this change creates.

**Resolution.** Replace "the one revision creates its table and its index together" in
`spec/design/testing.md` :211 with "each of the two revisions creates its table and its index
together".

**What was ambiguous.** The row states a count inside a claim about vacuity, so a second revision
makes the count false and leaves the claim true.

**What was not found.** No other row of § Fitness functions counts contexts, tables or revisions as
one.

### COH-design-18 — How many paths and operations do the hand-written contracts hold?

- **kind:** contradiction
- **severity:** minor
- **decision_mode:** AUTO
- **auto_basis:** spec/constitution.md § Article IV — The specification changes on the same branch as the code
- **ambiguity_source:** contracts/README.md § Why a contract is written rather than generated
- **artifacts:** contracts/README.md, contracts/openapi/todo_list.yaml

**What each says.** `contracts/README.md` § Why a contract is written rather than generated (:44-45):
"for this template that is three paths, six operations and eight schemas". With
`contracts/openapi/todo_list.yaml` the gate's own scale line reads otherwise:
`./scripts/contracts.sh` printed `against 3 contracts, 5 paths, 10 operations`.

**Why they cannot both be true.** Two paths and four operations were added. The schema count, on
the old figure's own convention (FastAPI's two validation shapes not counted, a schema defined in
two files counted once), goes from eight to twelve: `TodoTaskCreate`, `TodoTaskUpdate`,
`TodoTaskRead`, `TodoTaskList`. Command: the per-file schema listing over
`contracts/openapi/*.yaml`. design-api reported the sentence as outside its allowlist. Pass 4 did
not raise it. Graded minor.

**What settles it.** `spec/constitution.md` § Article IV, as for COH-design-8. The count is a fact
this change creates. `contracts/` is the convergence round's to edit (`spec/invariants.md` § Data
invariants).

**Resolution.** Replace "three paths, six operations and eight schemas" in `contracts/README.md`
with "five paths, ten operations and twelve schemas".

**What was ambiguous.** The README states the template's contract size inside its argument for
writing contracts by hand, so the next contract makes the argument's figure false.

**What was not found.** `contracts/openapi/README.md` was updated by design-api ("Compatibility mode
of all three") and is true.

### What was checked and agrees

- **`data-model.md` ↔ `api.md` ↔ `todo_list.yaml`.** They agree as pass 4 found. The combined
  `PATCH` writes the columns it carries. A `null` field reads as absent, and a body of two `null`s
  is the empty patch (`api.md`:180, `testing.md`:777). On `POST` a `null` text is the standard
  validation `422`.
- **The verdict order.** `architecture.md`:625's "`BR-07` then `BR-06`" for the browser gives the
  same verdict as "empty, then one line, then measure", because an empty text holds no line break
  (`api.md` § The to-do list's refusals, item 3). It is not a contradiction.
- **design-ui's `Q-15` assumption.** A server error carries no `detail.message`:
  `app/core/errors.py`:55 is `{"detail": "internal server error"}`. So "the service answered with
  an error" is the sentence it gets.
- **The authors' assumptions.** design-api's "5 coded refusals" translated by the router is
  COH-design-12. design-api's "importing `TODO_TASK_TEXT_MAX_LENGTH` is fine" is COH-design-13.
  design-data's "writing it belongs to the convergence round" is COH-design-16. review-converge's
  "`A-1`, `A-3` and `A-4` … need the same write-back later" is COH-design-14. design-domain's
  "screens: [] and features: [] stay empty" is superseded by `Q-19` and landed as COH-design-5 and
  COH-design-6. Every other stated assumption matches what the neighbour wrote.
- **Known and routed, not raised again.** `spec/design/conventions.md` § Frontend :188-190 ("the
  browser has exactly one") now sits right after the new "Only the rule moves up". It stays false
  and is routed to reconcile-design (`design/delta/architecture.md` item 3; review-converge). The
  deletion lists in `CLAUDE.md` and `spec/README.md`:63-69 do not say that `BR-01`'s words move into
  `spec/contexts/todo_list.md` first. They are incomplete rather than false, and design-spec and
  ADR draft 1 report them.
- **Glossary and invariants.** *Task* and *Task (process)* stay apart, and no identifier uses a bare
  `task`. `D-01`…`D-03` hold, and the non-goals name tasks.

## Pass 6 — verification

The preflight printed `CONVERGENCE ROUND: 2 of 3 -- MODE: VERIFYING`, so only Phases 1, 1b and 4
ran. There was no hunt. The question was whether each of the eighteen recorded resolutions of the
`design` stage landed in the document its reconciliation named. Read for it: this file whole, the
diff of the last convergence round (`git diff 33d8b66 bc3dc15` over `contracts/README.md`,
`spec/design/`, `spec/invariants.md`, both ADR drafts, the api and architecture fragments,
`requirements.md` and `scenarios.md`), the passages each resolution names in the working tree, and
the ten `ASSUMPTIONS` blocks from the preflight. The ranked documents read above them:
`spec/constitution.md` (Article VIII in full), `spec/invariants.md`, `spec/glossary.md`,
`contracts/README.md`.

Line numbers were taken from the working tree with `grep -n` over each resolution's own wording.
`git status --short` shows no uncommitted edit to any artefact or to any file under `spec/`
outside the process's own state files, so every line cited below is committed at `bc3dc15`.

### Recorded resolutions

- COH-design-1: landed. `spec/design/conventions.md`:42-59 (§ Layers, the service judges a coded
  field rule, with the user's `Q-17` words at :56). The artefact-level patches stand:
  `spec/design/architecture.md`:588-589 (`BR-06`, `BR-07` held in the service), :595 (`BR-13`),
  :600-603 (the router translates each domain exception), :615-616 (the schema holds no text
  rule; the service holds the judgement and its three exceptions);
  `design/delta/architecture.md`:45-54 (Decision 2) and :87 (row `R-2`).
- COH-design-2: landed. `spec/design/conventions.md`:48-50 (a shape built from a refused value is
  still valid); `spec/design/testing.md`:759 ("through the rule, while every case builds a valid
  create and update shape, so only the rule can refuse a text") and :861-863
  (`test_the_create_and_update_shapes_carry_no_bound`, the code proved on the wire by
  **tests/integration/test_todo_tasks_corpus.py**).
- COH-design-3: landed. `spec/design/conventions.md`:191-194 (§ Frontend, "Only the rule moves
  up"); `design/delta/architecture.md`:60-68 (Decision 4), :142 (the write set, "one import
  line"), :243 (§ This change owns). No `text.test.ts` row is left.
- COH-design-4: landed. `spec/design/architecture.md`:666-674 (§ Who writes what, with the user's
  `Q-18` words); `design/delta/architecture.md`:142 and :254.
- COH-design-5: landed. `spec/contexts/todo_list.md`:7 (`screens: [spec/design/ui/todo-list.md]`)
  and :23-32.
- COH-design-6: landed. `spec/contexts/todo_list.md`:8
  (`features: [e2e/suite/features/todo_list.feature]`) and :23-32, which names the on-disk case as
  the declared red and its expiry.
- COH-design-7: landed. `requirements.md`:525-527 (§ Impact analysis, "the retention item names
  tasks too"), :673-675 (§ Non-Goals), :738-739 (`A-2`, "confirmed at this document's approval;
  `spec/invariants.md` § Deliberate non-goals names tasks since"), :835-838 (Self-check 23).
- COH-design-8: landed. `spec/design/conventions.md`:96-98 (§ Backend, "a second domain context
  and is not an example"); `spec/README.md`:58-60.
- COH-design-9: landed. `spec/design/testing.md`:979-985 (the third detector names
  `test_every_screen_and_feature_a_context_names_is_on_disk`, declared on build-tests-e2e's task,
  and says both claim cases stay green; "Unresolved" is gone);
  `design/delta/architecture.md`:228-230 (item 4, "the on-disk case is red until build-tests-e2e
  writes the feature file").
- COH-design-10: landed. `spec/design/testing.md`:986-993 (the `./scripts/contracts.sh` bullet,
  11 findings, accepted by name at each boundary before build-backend's wave, with the user's
  `Q-21` words).
- COH-design-11: landed. `spec/design/ui/guestbook.md`:400-403 (§ Data, "What is posted and
  amended is the text the screen judged"); `spec/design/ui/todo-list.md`:240 (the adding row sends
  `text` "as the shared rule leaves it"). It now agrees with `spec/design/testing.md`:917-918
  ("sends the text as the shared rule leaves it").
- COH-design-12: landed. `spec/design/conventions.md`:42-45 (a rule about a field's value; a
  `PATCH` that sets no field is decided beside the endpoint) and :57-59 (`Q-21`);
  `spec/design/architecture.md`:603-605 (the router answers `todo_task_empty_patch` itself).
- COH-design-13: landed. `spec/design/conventions.md`:50-53 ("Holding no part of the rule means
  importing none of it"); `spec/design/data-model.md`:256-258 ("the service's judgement of a text
  imports it; the schemas do not"); `design/delta/architecture.md`:192-193 ("imported by the to-do
  service's judgement").
- COH-design-14: landed. `requirements.md`:718-722 (the § Named assumptions preamble, with the
  user's `Q-21` words), :733 (`A-1`), :752 (`A-3`), :762 (`A-4`), each "confirmed at this
  document's approval"; :519 (§ Impact analysis, "`A-2`, confirmed at approval"); :777
  (Self-check 4). The pointers "assumed: `A-1`" at :85 and "assumed: `A-3`" at :88, and the SC-5
  cell at :27, remain. The resolution did not name them, and they point at the assumption rather
  than state its status, as pass 5 said of the SC-5 cell.
- COH-design-15: landed. `scenarios.md`:40-43 (§ Coverage, "'Observed through' says where a seed
  can be seen, not which suite binds it");
  `design/adr/task-text-refusals-are-coded-not-schema-constraints.md`:20-22 (§ Context, "the
  integration corpus test proves each on the wire"); `design/delta/api.md`:12 (the **Why** of the
  `spec/design/api.md` entry).
- COH-design-16: landed. `spec/invariants.md`:98-106 (§ Data invariants, the stage is settled by
  the witnesses, with the user's `Q-21` words); `spec/design/data-model.md`:198-200 (§
  `todo_tasks`, the call for the invariant); `spec/design/testing.md`:802-806 (the `spec_sync`
  stage's convergence round writes it).
- COH-design-17: landed. `spec/design/testing.md`:211 ("each of the two revisions creates its table
  and its index together").
- COH-design-18: landed. `contracts/README.md`:45 ("five paths, ten operations and twelve
  schemas").

A `grep -cF` of each named document for the wording its resolution replaced counted 0 every time.
The strings searched were "the task's text type in the context's", "schema refuses them before the
route runs", "test_the_create_and_update_shapes_give_every_case_the_same_verdict", "through the
rule and through the create and update shapes", "Unresolved, and handed", "the one revision
creates", "and the convergence round writes it", "`text.test.ts` (moved in)", "moves with it",
"if testing.md puts", "imported by the to-do schema", "screens: []", "features: []", "awaiting the
user", "No item below is a human decision", "(assumed: `A-2`)", "for the user to confirm", "stays
worded for entries while", "**only** domain context", "A rule whose refusal carries a code of its
own is judged", "The only domain context", "sends `text` as typed", "and the schemas import it",
"black box has to tell" (both the ADR draft and the api fragment) and "three paths, six
operations".

The authors' assumptions that speak of these edits match the text. review-converge says it left
`requirements.md` :85, :88 and the SC-5 cell alone, and they are as it says. design-testing says
`design/delta/converge.md`:42 still describes the rejected case historically, which is a dated
record, not a resolution's target. design-architecture's list of applied patches (COH-design-1, 3
and 4) is the set of fragment lines cited above.

No `verification` finding. All eighteen resolutions landed.

## Pass 7 — the `implement` stage

The preflight printed `COHERENCE PASS: the first one (before any round) -- a full hunt`. It listed
no recorded finding of this stage, so Phase 1b had nothing to verify. The preflight named `uat.md`
as the stage's only artefact and gave no diff base. The skill names the wave's diff, so the diff
was read as `git diff 3c74dfd 72ff77e`: 69 files, from the commit before the first test wave to
the TD-3 re-dispatch.

Read whole: every source, test and fixture file in that diff, plus `requirements.md`, `uat.md` and
`tasks.md`. Read in the parts the diff answers to:
- `spec/design/api.md`, the to-do parts of § Shapes, § Endpoints and § Refusals;
- `spec/design/ui/todo-list.md`, `spec/design/ui/system-states.md` and `spec/contexts/todo_list.md`;
- `spec/design/architecture.md`, from § What a new environment starts with to § What holds the
  boundaries;
- `spec/design/data-model.md` § `todo_tasks` and § Migrations;
- `spec/design/testing.md` § Fitness functions and § CR-2609-823a through § Four file sets;
- `scenarios.md`: the titles, S-49…S-53 and § Seed data;
- `golden-set/README.md`, and the nine `ASSUMPTIONS` blocks from the preflight.

The ranked documents read above them: `spec/constitution.md` (Article VIII in full),
`spec/invariants.md`, `spec/glossary.md` and `contracts/README.md`.

Two gates were run for evidence rather than trusted. `./scripts/contracts.sh` printed `0
problem(s) against 3 contracts, 5 paths, 10 operations, 18 responses, 9 parameters, 40 fields,
7 refusals` and `API contract is frozen: OK`. `./scripts/generate.sh --check` printed `Generate
--check: OK`.

Pairs compared:
- `api.md` ↔ the router, the schemas and the service: the routes, the five codes and their
  sentences word for word, the refusal order, `id` on `todo_task_not_found` alone, the strict
  types, and `total ≥ 0`;
- `data-model.md` ↔ the model and the revision;
- `architecture.md` § The layer per rule and § The files ↔ where each rule landed;
- `ui/todo-list.md` ↔ the page, the composer, the row, the dialog and the hook: every state, every
  string of § Copy and § Accessibility labels, the focus rules and the tokens;
- `ui/system-states.md` ↔ the frame, the not-found page and the router;
- `contexts/todo_list.md` `BR-06`…`BR-13` ↔ the service and the browser rule;
- `requirements.md` `R-1`…`R-11` ↔ the code and the tests;
- `testing.md` § CR-2609-823a ↔ the test files and their case names;
- `tasks.md` ↔ each task's product;
- `scenarios.md` ↔ the feature file (22 titles) and the seed file (five texts);
- `uat.md` ↔ the requirements, the screen documents, the scripts it tells a person to run, and
  the frontend's cache policy;
- the live documents that describe the corpus, the example context and the structural tests ↔
  what this stage wrote;
- each author's assumptions ↔ what its neighbour wrote.

### COH-implement-1 — Does opening a screen by its header link read its list again?

- **kind:** contradiction
- **severity:** minor
- **decision_mode:** HITL
- **auto_basis:**
- **ambiguity_source:** spec/design/ui/system-states.md § Interactions
- **artifacts:** requirements.md, uat.md, frontend/src/contexts/todo_list/hooks/useTodoTasks.ts

**What each says.** Three documents promise that opening a screen reads it:
- `requirements.md` § R-3 clause 5: "WHEN the list is opened or reloaded, the system SHALL show
  the tasks exactly as they are stored at that moment, including tasks other people have added,
  marked, edited or deleted."
- `spec/design/ui/todo-list.md` § Interactions: "Opening the to-do list's own address, or
  reloading it → the list is read".
- `uat.md` step 14 runs `./scripts/seed.sh`, then opens the guestbook "with the header link
  "Guestbook"" and expects `5 entries`.

The code does not always read:
- The to-do query sets no freshness of its own. `grep -c "staleTime\|refetchOnMount"
  frontend/src/contexts/todo_list/hooks/useTodoTasks.ts` printed `0`.
- So it inherits `frontend/src/main.tsx`:35, `staleTime: 30_000`, as the guestbook's query does.
- TanStack Query 5.102.8 refetches cached data on mount only when that data is stale. Line 326
  of `frontend/node_modules/@tanstack/query-core/build/modern/queryObserver.js` is `return value
  === "always" || value !== false && isStale(query, options);`.

**Why they cannot both be true.** Open a screen by its header link within 30 seconds of its last
read, and it shows that read without asking the service. R-3 clause 5 and the screen document
promise what is stored at that moment. On the to-do list, the gap is other people's changes from
the last 30 seconds. A person's own changes always refetch (`useTodoTasks.ts`).

In the UAT, the gap can produce a false "no":
1. The Part D set-up reads the guestbook while it is empty after the reset.
2. Step 14 comes after one added task and one `seed.sh` run.
3. If that takes under 30 seconds, the header link shows the cached "No entries yet. Be the
   first.", and the tester fails a working system.

Graded minor: nothing is stored wrong, and the cost is a UAT re-run or one line of code. This
was traced through the code, not observed in a browser.

**What settles it.** Nothing ranked above both. `main.tsx` predates this change, and no
specification document states its 30 seconds.

**Resolution.** Two options, and under both, step 14 of the UAT changes:
- (A), recommended: the to-do list reads its list every time it opens, and the UAT reloads before
  step 14. The guestbook's hook stays untouched, as `SC-5` and the architecture's freeze require.
- (B): R-3 clause 5 means an address entered or reloaded, the screen documents say so, and the
  UAT reloads before step 14.

Ready patch:
- `uat.md` step 14, "What to do". Replace "In terminal B run `./scripts/seed.sh`. When the prompt
  returns, open the guestbook with the header link "Guestbook"." with "In terminal B run
  `./scripts/seed.sh`. When the prompt returns, reload window A, then open the guestbook with the
  header link "Guestbook"."
- For (A): `frontend/src/contexts/todo_list/hooks/useTodoTasks.ts`, `useTodoTasks`. Add
  `staleTime: 0,` to the `useQuery` options, with a comment that cites R-3 clause 5.
- For (B): `spec/design/ui/todo-list.md` § Interactions. After "Nothing pushes their changes to an
  open screen." add "A header link that opens the list shows it as last read while that read is
  under 30 seconds old (`frontend/src/main.tsx`)."

**What was ambiguous.** `system-states.md` § Interactions calls the header link "React Router
navigation … without a reload". It does not say whether the screen reads its list again. The link
opens the list's own address, and `todo-list.md` § Interactions says that opening the address
reads the list. The 30-second rule lives only in a comment in `main.tsx`. So the requirement and
the UAT author both read "opening" as "reading".

**What was not found.** No other UAT step depends on it:
- Steps 16, 17, 19 and 20 reload or enter the address.
- Steps 15 and 18 expect what the cached read already holds.
- `refetchOnWindowFocus: false` agrees with steps 9 and 11: "nothing is pushed to a screen that is
  already open".

### COH-implement-2 — Which document describes the corpus now that the to-do list's files are in it?

- **kind:** contradiction
- **severity:** minor
- **decision_mode:** HITL
- **auto_basis:**
- **ambiguity_source:** spec/design/architecture.md § Who writes what, and where the sets meet
- **artifacts:** golden-set/README.md, golden-set/seed/todo-tasks-example.json

**What each says.** `golden-set/README.md` makes five claims about the corpus:
- :23, of `fixtures/`: "Four files, each with one story".
- :30, of `text-measurement.json`: "the one file both languages read".
- :32: "Three hold entries; the fourth holds cases."
- :48, § `seed/`: "One file: `entries-welcome.json`".
- :98: "The frontend reads neither half, with one named exception."

This stage wrote the to-do half of the corpus:
- `ls golden-set/fixtures | wc -l` printed `8`, and `ls golden-set/seed` printed
  `entries-welcome.json todo-tasks-example.json`.
- `frontend/src/contexts/todo_list/lib/todoTask.test.ts` is a second browser reader, of
  `todo-task-text.json`. `tests/fitness/test_golden_set.py` now allows it, and
  `spec/design/testing.md` § The fixture half says so.

**Why they cannot both be true.** All five claims are now false, and they sit in the corpus's own
rules document, which `testing.md` cites as what every corpus file owes. No member of this change
may write it:
- `architecture.md` § Who writes what gives build-backend `golden-set/seed/` and the integration
  author `golden-set/fixtures/`. Nobody gets the README.
- `design/delta/architecture.md` § Found outside every write set, item 1, found it ownerless.
- `tasks.md` § Outside every task, item 3, left it "still open".
- The `spec_sync` boundary does not name it (`tasks.md` § Scope against the design).

So it merges false unless somebody routes it. The process half is banked as `PROC-18` and filed as
`https://github.com/Scalo-Sales-Engineering-Consulting/forge_template_python_react/issues/92`.
Graded minor: no behaviour differs.

**What settles it.** Nothing on the ladder. The file is outside `spec/`, and which member writes it
is a composition question.

**Resolution.** Recommended: one member edits `golden-set/README.md` in this change with the patch
below. build-tests-integration fits, because it owns the locator and the fixture half, and the
fragment proposed it. The alternative is to name the false sentences in the pull request body and
leave them to issue 92.

Ready patch, `golden-set/README.md`. The table rows reuse `spec/design/testing.md` § The fixture
half's own stories.
- :23. Replace "Four files, each with one story" with "Eight files, four for the guest book and
  four for the to-do list, each with one story". Then add four rows to the table under it:
  - "| `todo-tasks-ordinary.json` | ordinary tasks in **adding** order, each with its done mark |"
  - "| `todo-tasks-boundary.json` | task texts **exactly** on the bound; every one must be
    accepted |"
  - "| `todo-tasks-refused.json` | task texts the rules refuse, each naming the refusal code the
    contract gives |"
  - "| `todo-task-text.json` | how a task's text is judged — **cases, not tasks** — read by both
    languages |"
- :30. Replace "and the one file both languages read" with "and the guest book's file both
  languages read".
- :32. Replace "Three hold entries; the fourth holds cases." with "Three hold entries, three hold
  tasks, and two hold cases."
- :48. Replace "One file: `entries-welcome.json`. A preview with an empty guest book" with "Two
  files: `entries-welcome.json` and `todo-tasks-example.json`, one per list. A preview with an
  empty list".
- :98. Replace "with one named exception" with "with two named exceptions, one per context". After
  the paragraph on `text-measurement.json`, add: "The to-do list's `todo-task-text.json` is the
  second, read by `frontend/src/contexts/todo_list/lib/todoTask.test.ts` alone, for the same
  reason."

**What was ambiguous.** `architecture.md` § Who writes what hands out the corpus by directory, so
the README beside those directories went to nobody. The design saw the gap and proposed an owner,
but the proposal needs a stack-profile change that this change cannot make.

**What was not found.** `spec/design/testing.md` § The fixture half, which was updated at design,
agrees with the files row by row.

### COH-implement-3 — Does deleting the guestbook delete the to-do list's corpus?

- **kind:** contradiction
- **severity:** minor
- **decision_mode:** AUTO
- **auto_basis:** spec/constitution.md § Article IV — The specification changes on the same branch as the code
- **ambiguity_source:** spec/README.md § This directory describes a template
- **artifacts:** spec/README.md, CLAUDE.md, scripts/seed_golden_set.py

**What each says.** The two deletion lists say the corpus goes with the example:
- `spec/README.md`:59-60: "The to-do list beside it is not an example and stays when the
  guestbook is deleted."
- The same section, :63-66, then says: "Deleting the example deletes with it: … both halves of
  the corpus `golden-set/`".
- `CLAUDE.md`:127-130, § What is an example, and what is the template, carries the same list.

The work of this stage says otherwise:
- It put five of the to-do list's files in `golden-set/`: the four fixtures and
  `golden-set/seed/todo-tasks-example.json`.
- `scripts/seed_golden_set.py`:62 says the opposite of the lists: "Deleting the guest book
  deletes `entries-welcome.json` and the half of this file that posts entries".
- `./scripts/seed.sh --help` says "the example tasks belong to the to-do list, which stays".

**Why they cannot both be true.** Followed as written, the lists delete the to-do list's four
fixtures and its example tasks. `tests/unit/test_todo_task_text_rules.py`,
`tests/integration/test_todo_tasks_corpus.py` and `todoTask.test.ts` then lose the files they read.
Pass 5 read these lists as incomplete, not false, but that was before the files existed. Graded
minor: the suites would go red loudly.

**What settles it.** `spec/constitution.md` § Article IV: the specification edit that describes a
fact this change creates lands in the same pull request. Two sentences already say that the to-do
list stays: `spec/README.md`:59-60 and `spec/design/conventions.md` § Backend — where a file goes
("a second domain context and is not an example").

**Resolution.** Both lists name the guestbook's files in the corpus, and say that the to-do list's
files stay.

Ready patch:
- `spec/README.md` § This directory describes a template. Replace "both halves of the corpus
  `golden-set/`" (split across :65-66) with "the guestbook's files in both halves of the corpus
  `golden-set/` — never the to-do list's `todo-task-text.json` and `todo-tasks-*.json`".
- `CLAUDE.md`:130. Make the same replacement.

**What was ambiguous.** The lists name a directory rather than the guestbook's files in it. That
was accurate only while every corpus file belonged to the guestbook.

**What was not found.** Every other item in both lists names a file that is the guestbook's alone.

### COH-implement-4 — Do the structural tests still say there is one context, one table and one revision?

- **kind:** contradiction
- **severity:** minor
- **decision_mode:** AUTO
- **auto_basis:** spec/constitution.md § Article I — The specification is the source of truth
- **ambiguity_source:** spec/design/testing.md § Four file sets, disjoint
- **artifacts:** spec/design/testing.md, tests/fitness/test_context_declarations.py, tests/fitness/test_context_boundaries.py, tests/fitness/test_data_invariants.py, tests/fitness/test_migration_safety.py, tests/integration/test_migrations.py

**What each says.** `spec/design/testing.md` § Fitness functions was corrected at design:
- :200-201: `test_context_boundaries.py` and `test_context_declarations.py` "were vacuously true
  while there was one context", and the sweeps now read real headers.
- :217: for `test_data_invariants.py`, "`todo_tasks` made them real".
- :211: for `test_migration_safety.py`, "each of the two revisions".

The tests' docstrings still state the old facts, in the present tense:
- `tests/fitness/test_context_declarations.py`:31: "Most of these are **vacuously true today** --
  there is one context". :299: "Vacuously true while there is one context, and it says so."
- `tests/fitness/test_context_boundaries.py`:28: "**Every rule here is vacuously true today**:
  there is one context". :145: "Vacuously true with one context". :213: "With one context
  nothing can cross".
- `tests/fitness/test_data_invariants.py`:16-18: "vacuously true today … the guest book is one
  table". :92: "Vacuously true while the guest book is the only table".
- `tests/fitness/test_migration_safety.py`:27: "the one revision here creates a table and its
  index together".
- `tests/integration/test_migrations.py`:128: "`BR-04` is read on every load of the only screen".
  This stage edited that file (T-4).

Command: `grep -rn "vacuously true today\|Vacuously true with one context\|Vacuously true while
there is one context\|With one context nothing\|one revision here\|the only screen\|only table"
tests/fitness/*.py tests/integration/test_migrations.py
frontend/src/contexts/guestbook/pages/GuestbookPage.tsx`. It printed every line cited here and in
COH-implement-5.

**Why they cannot both be true.** The specification says these sweeps now judge real material. The
tests' own docstrings say they are vacuous. Article IX makes the module docstring the place where a
check's intent is kept. A reader who trusts it will take a red from these sweeps for a synthetic
known positive, not a real breach. Graded minor: no assertion is affected.

**What settles it.** `spec/constitution.md` § Article I: "Code contradicting `spec/` is either a
defect in the code or a change not applied to the specification." The specification changed at
design, so the code's text is the defect.

**Resolution.** The docstrings say what `testing.md` says. Text only: no assertion changes and no
case is renamed. Each file goes to the author whose tree holds it: build-tests-unit for
`tests/fitness/`, build-tests-integration for `test_migrations.py`.

Ready patch:
- `test_context_declarations.py`:31-32. Replace "Most of these are **vacuously true today** --
  there is one context, and it borders on nothing." with "Most of these were **vacuously true**
  while there was one context bordering on nothing; since `CR-2609-823a` two contexts declare each
  other, and the sweeps read real headers."
- `test_context_declarations.py`:299. Replace "Vacuously true while there is one context, and it
  says so." with "Vacuously true while there was one context; since `CR-2609-823a` it reads two
  real neighbours."
- `test_context_boundaries.py`:28-29. Replace "**Every rule here is vacuously true today**: there
  is one context, so no import can cross a boundary that does not exist." with "**Every rule here
  was vacuously true** while there was one context, since no import could cross a boundary that
  did not exist; since `CR-2609-823a` there are two."
- `test_context_boundaries.py`:145. Replace "Vacuously true with one context; the detector is
  proved below." with "Real since `CR-2609-823a` brought a second context; the detector is proved
  below."
- `test_context_boundaries.py`:213-214. Replace "This is where the rule lives today. With one
  context nothing can cross, so the sweeps above would pass over a reader that always answered
  None." with "This is where the rule lived while there was one context: nothing could cross, so
  the sweeps above would have passed over a reader that always answered None."
- `test_data_invariants.py`:16-18. Replace "**Two of these are vacuously true today and that is
  said out loud**" with "**Two of these were vacuously true while the guest book was the only
  table, and that was said out loud**". Replace "the guest book is one table, so nothing can
  mirror it and nothing can copy from it." with "the guest book was one table, so nothing could
  mirror it and nothing could copy from it; `todo_tasks` made them real."
- `test_data_invariants.py`:92. Replace "Vacuously true while the guest book is the only table,
  and that is fine:" with "Vacuously true while the guest book was the only table:".
- `test_migration_safety.py`:27. Replace "the one revision here creates a table and its index
  together" with "each of the two revisions here creates its table and its index together".
- `test_migrations.py`:128. Replace "read on every load of the only screen" with "read on every
  load of the guestbook's screen".

**What was ambiguous.** `testing.md` § Four file sets lists every edit a test author makes to an
existing test, and it names none of these five files. Yet § Fitness functions, in the same
document, was corrected for exactly the facts they state; COH-design-17 corrected the
migration-safety row. `requirements.md` § Impact analysis even predicted that two of them "stop
being vacuously true". The specification moved, and no write set carried the move into the
tests' prose.

**What was not found.** No assertion rests on these sentences, and every known positive still runs.
Two other passages are dated records of an incident and are true as history:
`tests/fitness/test_alembic_env_metadata.py`:8 and `tests/fitness/test_migration_safety.py`:94.

### COH-implement-5 — Does the guestbook screen still call itself the only screen?

- **kind:** contradiction
- **severity:** minor
- **decision_mode:** AUTO
- **auto_basis:** spec/constitution.md § Article I — The specification is the source of truth
- **ambiguity_source:** spec/design/architecture.md § The files
- **artifacts:** frontend/src/contexts/guestbook/pages/GuestbookPage.tsx, spec/design/ui/system-states.md

**What each says.** `frontend/src/contexts/guestbook/pages/GuestbookPage.tsx`:30: "`S-01` -- the
only screen in this application." `spec/design/ui/system-states.md` § One column: "The
application has two screens, the guestbook and the to-do list".

Two documents freeze the guestbook's frontend:
- `spec/design/architecture.md` § The files, row for the three guestbook modules: "nothing else
  about the guestbook moves".
- `design/delta/architecture.md` § What this change does not move: "Its frontend changes by three
  import paths and nothing else".

`GuestbookPage.tsx` is not one of the three modules. T-22 made the frame's docstrings stop saying
there is one screen, but it did not reach this one.

**Why they cannot both be true.** A module docstring states a fact that the specification now
contradicts. It sits in the first file a reader opens for the guestbook's screen, and Article IX
says module docstrings cite the specification. The claim is not on screen, so `R-5` clause 4 is
not broken. Graded minor.

**What settles it.** `spec/constitution.md` § Article I, as for COH-implement-4.

**Resolution.** One line in `GuestbookPage.tsx`, taken as a behaviour-neutral exception to the
freeze.

Ready patch, `GuestbookPage.tsx`:30. Replace "`S-01` -- the only screen in this application." with
"`S-01` -- the guestbook's screen, one of this application's two
(`spec/design/ui/system-states.md` § One column)."

**What was ambiguous.** `architecture.md` § The files freezes the guestbook's frontend for its
behaviour. It makes no exception for the file's prose, which the second screen made false.

**What was not found.** The same freeze is why `PageFrame.tsx` carries the guestbook's footer as
the default of `footer`, which build-frontend reported. Each screen still shows its own sentence
and the not-found page shows none, as `system-states.md` § Regions requires. So that is a debt,
not a contradiction. If the file is opened for this line, the footer can move into it too.

### COH-implement-6 — Were the reds that ran ahead of the code declared on a task, or signed off at the design close?

- **kind:** contradiction
- **severity:** minor
- **decision_mode:** HITL
- **auto_basis:**
- **ambiguity_source:** spec/design/testing.md § CR-2609-823a, the to-do list
- **artifacts:** tasks.md, spec/design/testing.md, spec/contexts/todo_list.md

**What each says.** The specification says every red was declared on a task:
- `spec/design/testing.md` § CR-2609-823a, "Existing detectors that go red on the way" (:958-960):
  "each is declared on the task whose product closes it".
- Its third bullet (:979-982) says the on-disk case is "declared on build-tests-e2e's task".
- `spec/contexts/todo_list.md`:30-32: "the plan declares
  `test_every_screen_and_feature_a_context_names_is_on_disk` red on the task that writes the file.
  The declaration expires when that task writes the file".

`tasks.md` did otherwise:
- T-11 says the on-disk case "has been red since … (`Q-19`, signed off at the design close,
  `Q-24`), and the implement baseline carries it … It is not declared".
- T-14 carries the context-boundaries case the same way.
- § What can go in parallel: "The `Turns green:` cases carried from the design close … are
  baseline reds, not declarations."
- The seed-file cases were declared on T-10 and T-4, the tasks that turned them red, and T-17
  closed them.

The session trace records the sign-off: `[18:49] stage_closed: closed design, opened plan
(boundary -> RED; accepted RED: Application check, Suite fitness: structural at the design
boundary`, right after `Q-24 -> A`.

**Why they cannot both be true.** The specification says each red was declared on the task that
closes it. The plan and the record tell a different story: two reds were accepted by name at the
design boundary and carried as a baseline, and the rest were declared on the task that turned
them red. The merged specification can keep only one account.

A red that already stood at the design close could not be declared on a task of a plan not yet
written, before the run that showed it (constitution Article X). That is why `Q-24` accepted it,
following the pattern COH-design-10 set for `./scripts/contracts.sh`. Graded minor.

**What settles it.** Nothing on the ladder. `Q-24` is recorded only in the change record, so this
is HITL by iron rule 2. The human step is to confirm the account; it is not a new question.

**Resolution.** The `spec_sync` stage writes down what happened: reconcile-design in `testing.md`,
reconcile-spec in `todo_list.md`.

Ready patch:
- `spec/design/testing.md`:960. Replace "each is declared on the task whose product closes it:"
  with "each was declared red on the task that turned it red or, when it already stood at the
  design close, accepted by name at that boundary (`Q-24`) and carried as a baseline red; the
  task whose product closes it names it under **Turns green:** in the change's `tasks.md`:".
- `spec/design/testing.md`:981-982. Replace ", and declared on build-tests-e2e's task, whose
  product is the file, in the first implementation wave." with ", accepted by name at the design
  close (`Q-24`), and turned green by build-tests-e2e's feature file in the first implementation
  wave."
- `spec/contexts/todo_list.md`:30-32. Replace "the plan declares
  `test_every_screen_and_feature_a_context_names_is_on_disk` red on the task that writes the file.
  The declaration expires when that task writes the file in the first implementation wave." with
  "`test_every_screen_and_feature_a_context_names_is_on_disk` was red from the design close,
  accepted by name at that boundary (`Q-24`), and went green when the first implementation wave
  wrote the file."

**What was ambiguous.** `testing.md` described the mechanism for a red that starts inside the
design stage as if the red started inside the implementation stage. The engine carries a red
across a stage boundary only by acceptance. The document's fourth bullet says so for
`./scripts/contracts.sh`, but the fitness cases got no such sentence.

**What was not found.** The fourth bullet matches `tasks.md` and the gate run above: accepted by
name, and turned green by T-16.

### What was checked and agrees

- **The backend against the contract.**
  - `contracts.sh` and `generate.sh --check` both pass, as above.
  - The router's five sentences match `api.md` § The to-do list's refusals word for word.
  - The refusal order comes from where each question is asked: the empty patch in the router, the
    text in the service before the write, and not-found from the `UPDATE … RETURNING` that finds
    no row.
  - `StrictStr` and `StrictBool`, `id` on `todo_task_not_found` alone, and `total` `ge=0` all
    match.
  - The combined `PATCH` goes through `change_todo_task`, which build-backend named as its one
    addition. It is what `api.md` § `TodoTaskUpdate` asks for: "a body carrying both applies both
    in one write".
- **The schema.** The model and revision `5c58af1f8e8a` match `data-model.md` § `todo_tasks` and
  § The revision that creates `todo_tasks`: four `NOT NULL` columns, no server default, the literal
  200, a plain index build, and the index dropped before the table.
- **The screen against its documents.**
  - Every state in `todo-list.md` § Components and their states appears in the page, the composer,
    the row, the dialog or the checkbox. So does every string of § Copy and § Accessibility
    labels, and the tests quote the same strings.
  - A tick sends `done` alone and a correction sends `text` alone. Adding sends the text as the
    shared rule leaves it. The cache is written only by a refetch after a 2xx.
  - The frame matches `system-states.md`: the navigation (`Screens`, `aria-current`), the lockup
    "Product name"/"P", the not-found sentence, no footer on the not-found page, and the redirect
    from `/`.
  - Where the mock-up and the Markdown differ (the Save hover; Edit during a tick), the build
    follows the Markdown, and `todo-list.md` says "this document is the specification".
- **Requirements against proofs.**
  - Every `R-1`…`R-10` row in `testing.md` § CR-2609-823a names test files that exist, with the
    case names it lists.
  - The 22 scenario titles are `scenarios.md`'s, verbatim.
  - The seed file holds the five texts of `scenarios.md` § Seed data in adding order, with number 3
    done.
  - The seeder fills each list on its own condition, adds the tasks and then marks the done one,
    and refuses production before it reads either list (`R-11`; `architecture.md` § What a new
    environment starts with).
- **`uat.md`.**
  - Its steps cite S-49…S-53 correctly, and its copy matches the screen documents.
  - The scripts it names behave as it says: the reset refuses a `DATABASE_URL` it did not create,
    the seeder prints the prod refusal, and `start.sh` treats a failed seed as a warning.
  - Steps 9 and 11 hold because `refetchOnWindowFocus` is `false`.
  - Its one exposure is COH-implement-1.
- **The authors' assumptions.** Each was checked one by one against the neighbour's file, and all
  match:
  - the service's names and exceptions (build-tests-integration, build-tests-unit);
  - the shape of the constants (build-tests-unit, build-migration);
  - the contract fields (build-frontend, build-tests-e2e);
  - the seed file (build-tests-uat, build-tests-unit);
  - TD-3's `act()` form, at `useTodoTasks.test.tsx`:185, 255, 265, 281 and 292.

  build-backend reported four scripts that still describe the guest book alone: `scripts/help.sh`:89,
  `start.sh`:106-113, `deploy.sh`:620-621 and `preview.sh`:198-199. They were routed to
  reconcile-ops, along with `start.sh --help`'s `--no-seed` line. These are incomplete rather than
  false. No `spec_sync` member's write set holds `scripts/`, so that routing cannot land as
  addressed. This is noted, not graded.
- **Known and routed, not raised again.**
  - `testing.md`'s "nineteen … and one more" against the file's 19 cases: `tasks.md` § Outside
    every task, item 2, routed to reconcile-design.
  - `conventions.md` § Frontend's "the browser has exactly one" caller, false since the move:
    item 4, reconcile-design.
  - The task-text data invariant: the `spec_sync` convergence round writes it (item 5).
- **Glossary and invariants.** No identifier uses a bare `task`, and `D-01`…`D-03` hold.

## Pass 8 — the `implement` stage

The preflight printed `CONVERGENCE ROUND: 1 of 3 -- MODE: DEEP`. So Phase 1b ran first, over the
six recorded resolutions of this stage. A full hunt followed, over the material this round
changed. That material is `git diff d5d5832 643976a`: the convergence round (`094bf90`,
`181eeb2`) and the re-dispatches TD-4…TD-8 that applied its artefact-level patches.

Read whole:
- that diff, `uat.md` and `design/delta/converge.md`;
- `spec/design/ui/system-states.md` § Interactions;
- `spec/design/testing.md` § CR-2609-823a from "Existing detectors" on, and § Four file sets,
  disjoint;
- `spec/design/architecture.md` § The files and § Who writes what;
- the header and first section of `spec/contexts/todo_list.md`;
- `useTodoTasks.ts`, `TodoListPage.tsx` and `frontend/src/main.tsx`.

Read in the parts the diff answers to:
- `requirements.md` § R-3;
- `spec/design/ui/todo-list.md` § Components and their states, § Data, § Interactions and § Out of
  scope;
- `spec/design/ui/guestbook.md` § Data;
- `tasks.md` T-11, T-14, T-22, § What can go in parallel and § Outside every task;
- `design/delta/architecture.md` § What this change does not move and § This change owns;
- `.specconf/stack.json`'s write sets and `golden-set/README.md`;
- the ten `ASSUMPTIONS` blocks from the preflight.

The ranked documents read above them: `spec/constitution.md` (Article VIII in full),
`spec/invariants.md`, `spec/glossary.md` and `contracts/README.md`. `./scripts/test.sh fitness`
printed `364 passed in 3.06s`.

Pairs compared:
- each recorded resolution ↔ the document its reconciliation edited, and ↔ the artefact-level
  patch it named;
- `system-states.md` § Interactions ↔ `useTodoTasks.ts`, `TodoListPage.tsx`, `main.tsx` and the
  TanStack Query build they run on;
- `system-states.md` ↔ `todo-list.md` § Interactions, § The task count in the header and § The
  list ↔ `guestbook.md` § Data;
- `system-states.md` ↔ `requirements.md` § R-3 clause 5;
- `uat.md` ↔ `testing.md`'s `R-3` row ↔ the tests that exist, for what proves `Q-25`;
- `uat.md` steps 9, 11 and 14-18 ↔ the cache the code now keeps;
- the new rule in `testing.md` § Four file sets ↔ every test, step and harness comment that counts;
- `architecture.md` § The files ↔ `design/delta/architecture.md`, `tasks.md` and the guestbook's
  diff;
- `architecture.md` § Who writes what ↔ `.specconf/stack.json` and `golden-set/README.md`;
- the two deletion lists ↔ `ls golden-set/fixtures golden-set/seed`;
- `testing.md` "Existing detectors" and `todo_list.md` ↔ `tasks.md`, the session trace and the
  fitness run;
- each author's assumptions ↔ what its neighbour wrote.

### Recorded resolutions

- COH-implement-1: landed. `spec/design/ui/system-states.md`:194-200 (§ Interactions, "Opening
  the to-do list reads its list, every time — the header link included", with the user's `Q-25`
  words). Its artefact-level patches: `frontend/src/contexts/todo_list/hooks/useTodoTasks.ts`:72-77
  (`staleTime: 0`, with a comment citing `R-3` clause 5 and `Q-25`) and `uat.md`:80 (step 14,
  "reload window A, then open the guestbook"). What the paragraph says beyond the resolution is
  COH-implement-7.
- COH-implement-2: landed. `spec/design/architecture.md`:678-689 (§ Who writes what: the README
  "is in no member's set", its five sentences, template issue #92 and the user's `Q-26` words).
  The five sentences stand, unchanged as the resolution intends, at `golden-set/README.md`:23, :30,
  :32, :48 and :98. Its claim about the profile holds: `grep -n golden-set .specconf/stack.json`
  finds only `golden-set/seed` and `golden-set/fixtures` in any write set.
- COH-implement-3: landed. `spec/README.md`:65-67 and `CLAUDE.md`:130-131 read "the guestbook's
  files in both halves of the corpus `golden-set/` (never the to-do list's `todo-task-text.json`
  and `todo-tasks-*.json`)". The glob covers all five to-do files that
  `ls golden-set/fixtures golden-set/seed` lists.
- COH-implement-4: landed. `spec/design/testing.md`:1054-1059 (the rule) and :1117-1118 (the two
  cells). The nine ready patches:
  - `test_context_declarations.py`:31-37 and :301-302, plus :337-342 from TD-8;
  - `test_context_boundaries.py`:28-30, :146-147 and :215-217;
  - `test_data_invariants.py`:16-20 and :93-94;
  - `test_migration_safety.py`:27-28;
  - `tests/integration/test_migrations.py`:128.

  What the rule reaches beyond these five files is COH-implement-9.
- COH-implement-5: landed. `spec/design/architecture.md`:630 (the `GuestbookPage.tsx` row),
  `frontend/src/contexts/guestbook/pages/GuestbookPage.tsx`:30, and `design/delta/converge.md`
  § This change owns. What the landed row left standing beside it is COH-implement-10.
- COH-implement-6: landed. `spec/design/testing.md`:958-963 (the lead sentence) and :982-986 (the
  third bullet), and `spec/contexts/todo_list.md`:29-32. The fitness run above confirms that the
  on-disk case "went green".

A `grep -F` of each edited file for the wording its resolution replaced found nothing. The strings
searched were "vacuously true today", "Vacuously true with one context", "With one context
nothing", "the one revision here creates", "the only screen in this application", "each is
declared on the task whose product closes it", "The declaration expires", "every load of the only
screen" and "Vacuously true while there is one context".

No `verification` finding. All six resolutions landed.

### COH-implement-7 — Does the to-do list, opened by its header link, show the copy it read earlier until the new read answers?

- **kind:** contradiction
- **severity:** minor
- **decision_mode:** HITL
- **auto_basis:**
- **ambiguity_source:** spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/requirements.md § R-3
- **artifacts:** spec/design/ui/system-states.md, frontend/src/contexts/todo_list/hooks/useTodoTasks.ts

**What each says.** `spec/design/ui/system-states.md` § Interactions (:194-197), written by this
round, says the list is opened "by its address, by a reload or by the link "To-do list"". Then
"the screen shows the tasks as they are stored at that moment, other people's changes of the last
few seconds included, and never a copy it read earlier".

The code TD-7 wrote for it (`useTodoTasks.ts`:77) sets `staleTime: 0` and nothing else, so opening
the screen starts a fresh read. What is drawn while that read travels is decided by TanStack Query
and the page:
- `frontend/node_modules/@tanstack/query-core/build/modern/queryObserver.js`:195-199. On mount, a
  query that must refetch takes `fetchState(state.data, …)`.
- `query.js`:345-354. `fetchState` sets `status: "pending"` only when `data === void 0`. With a
  cached list, the status stays `success`, and the data is the cached list.
- `removable.js`:17. With no `gcTime` set, the cache keeps a list for `3e5` ms, five minutes.
  `grep -rn gcTime frontend/src` printed nothing.
- `TodoListPage.tsx`:147, :166 and :176 draw the count and the rows whenever `list.isSuccess`. The
  outline rows at :157 appear only while `list.isPending`.

**Why they cannot both be true.** Leave the to-do list and come back by its header link within
five minutes, and the screen first draws the list it read earlier. It replaces that list only when
the new read answers. For the length of one read, "never a copy it read earlier" is false.

On the slow network `requirements.md` E-27 names, a read can take seconds. The earlier list then
stands for seconds, with no sign that it is being read, because `todo-list.md` § The list draws
`loading` only before any read. A failed read does hide the old copy, through `isError`.

This was traced through the code, not observed in a browser. Graded minor: the final state is
right, nothing is stored wrong, and the cost is one edit, to the sentence or to the code.

**What settles it.** Nothing ranked above both. The user's words, "Always fetch the latest"
(`Q-25`), speak of fetching, not of what is drawn while the fetch is under way.
`requirements.md` § R-3 clause 5 ranks below `spec/design/**`.

**Resolution.** Recommended (A): the paragraph says what the code does and what the user asked
for. (B): the code drops the list when the screen closes, with `gcTime: 0` on this query alone.
Every opening then shows the outline rows first, and then the list as stored.

Ready patch for A, `spec/design/ui/system-states.md` § Interactions. Replace "the screen shows
the tasks as they are stored at that moment, other people's changes of the last few seconds
included, and never a copy it read earlier" with "the screen reads its list afresh and shows the
tasks as they are stored at that moment, other people's changes of the last few seconds included.
A list it read earlier in the same tab stays on screen only until that read answers, and is then
replaced".

**What was ambiguous.** `requirements.md` § R-3 clause 5 says the system "SHALL show the tasks
exactly as they are stored at that moment". That says what is shown once the list has been read,
not what is shown while the read is under way. The convergence round read it as "nothing else is
ever shown". build-frontend read it as "a read is always made".

**What was not found.** A reload and an entered address hold "never a copy" exactly as written,
because both start with an empty cache. No test and no UAT step can tell the two readings apart
(COH-implement-8).

### COH-implement-8 — What proves that the header link reads the to-do list again?

- **kind:** gap
- **severity:** minor
- **decision_mode:** HITL
- **auto_basis:**
- **ambiguity_source:** spec/design/testing.md § CR-2609-823a, the to-do list
- **artifacts:** uat.md, spec/design/testing.md

**What each says.** `uat.md`:8-9 says: "Everything else the change promises is proved by the
suites `spec/design/testing.md` § CR-2609-823a, the to-do list maps, and is not repeated here."
`uat.md`:123-126 says the same of everything `R-1` to `R-10` promise: "The suites … prove all of it
on every run."

This round added a promise to `R-3` clause 5: the header link reads the list (`system-states.md`
§ Interactions, `Q-25`). `spec/design/testing.md`:760, the `R-3` row, proves clause 5 only through
"A task somebody else added appears after a reload". build-frontend's assumption agrees: "No
vitest case asserts the header-link read; R-3 clause 5 is proved in the suites only by the reload
scenarios."

**Why it is a gap.** Nothing proves the new promise:
- `grep -rn staleTime frontend/src` prints `main.tsx`:35 and `useTodoTasks.ts`:77 and nothing
  else.
- `grep -rn "new QueryClient" frontend/src` lists the five query clients the tests build, and
  none sets a `staleTime`. They take TanStack's default of 0. So even a case that remounts the
  screen could not tell the hook's `staleTime: 0` from `main.tsx`'s 30 seconds.
- `e2e/ui/test_smoke.py`:630-653 follows both header links. It asserts headings and addresses, not
  a read.
- The UAT cannot tell either. Before step 15, window A's cache already holds the one task that
  step 14's reload read. The header link shows "Water the plants" whether or not it reads again.

So the one line that carries `Q-25` could be deleted and every suite and every UAT step would stay
green. Meanwhile `uat.md` says the suites prove it. Graded minor: the behaviour ships as decided,
and what is missing is its guard.

**What settles it.** Nothing ranked above both. `spec/constitution.md` § Article III is met,
because `R-3` has citing tests. Which suite proves a decision is `testing.md`'s to say, and it
does not say.

**Resolution.** Recommended (A): `testing.md` names a frontend case, and build-tests-frontend
writes it. The case opens the to-do list, leaves by the header link, changes the stubbed answer,
and comes back by the header link within 30 seconds. It uses a query client with `main.tsx`'s
defaults, so it fails if the hook loses `staleTime: 0`. (B): `uat.md` gains a step, and its two
sentences name that step as the proof. In the step, window B ticks a task, and window A goes to
the guestbook and back by the header links within 30 seconds and shows the tick.

Ready patch for A, `spec/design/testing.md`:760, the `R-3` row. After the closing parenthesis of
the `TodoListPage.test.tsx` entry, insert " · **frontend/src/router.test.tsx** (the to-do list
opened a second time by its header link is read again and shows what is stored then, under a
query client with `frontend/src/main.tsx`'s defaults, so that the case fails if the list inherits
their 30 seconds — `Q-25`, `spec/design/ui/system-states.md` § Interactions)".

**What was ambiguous.** The convergence round wrote `Q-25` into the screen document. It sent the
code to build-frontend and the UAT line to build-tests-uat, and it sent nothing to a test author.
The `R-3` row in `testing.md` still reads clause 5 as "reloaded".

**What was not found.** The guestbook needs no such case. Its behaviour did not change, and
`system-states.md` states it as `main.tsx`'s default.

### COH-implement-9 — Do three more test comments still count one table or one resource?

- **kind:** contradiction
- **severity:** minor
- **decision_mode:** AUTO
- **auto_basis:** spec/constitution.md § Article I — The specification is the source of truth
- **ambiguity_source:** spec/design/testing.md § Four file sets, disjoint
- **artifacts:** spec/design/testing.md, tests/unit/test_guestbook_entry_model.py, tests/integration/test_e2e_reset.py, e2e/suite/steps/guestbook_steps.py

**What each says.** `spec/design/testing.md` § Four file sets, disjoint (:1054-1059) is new this
round: "An existing test whose prose the change makes false stands here too, even when no
assertion moves. A module or case docstring that states a count the change alters — one context,
one table, one revision, one screen — is an edit to that test". The cells at :1117-1118 name the
five files of COH-implement-4. Three more still count one:
- `tests/unit/test_guestbook_entry_model.py`:163-164, in `test_the_entity_carries_no_relationship`:
  "The template's schema is one table and no edges. A relationship appearing here means a second
  context arrived". The same file asserts at :82 `assert set(Base.metadata.tables) ==
  {"guestbook_entries", "todo_tasks"}`. build-tests-unit edited this file in this change, and it
  is in that author's cell.
- `tests/integration/test_e2e_reset.py`:43: "The one table in this application's schema that
  holds a scenario's state." The reset empties every base table except `alembic_version`
  (`e2e/harness/database.py`:460 and :485), so `todo_tasks` is emptied before every to-do scenario.
  The file is in no cell.
- `e2e/suite/steps/guestbook_steps.py`:25: "The one resource this suite drives."
  `e2e/suite/test_scenarios.py`:26 now also imports `todo_list_steps`, whose own comment at :53
  reads "The one resource this module drives".

The command was one case-insensitive `grep -rn -E` for one-context, one-table, one-revision and
one-screen wording over `tests`, `e2e`, `frontend/src`, `app` and `alembic`. These three are the
lines that still count one; the other matches are generic or already corrected. `git diff main
--stat` over the last two files printed nothing, so this change never touched them.

**Why they cannot both be true.** `testing.md` now makes each of these comments an edit this
change owes. `spec/design/data-model.md` and `spec/design/api.md` say there are two tables and two
resources, and the comments still say one. Graded minor: no assertion rests on them.

**What settles it.** `spec/constitution.md` § Article I, as for COH-implement-4: code
contradicting `spec/` is a defect in the code.

**Resolution.** Text only, each edit made by the author whose tree holds the file, and
`testing.md`'s cells name all three. `guestbook_steps.py` needs two more things:
- It is outside the recorded boundary, whose rows name `e2e/suite/steps/todo_list_steps.py`
  alone (`design/delta/architecture.md` § This change owns). So it needs a row in
  `design/delta/converge.md` § This change owns.
- It sits under the fragment's freeze of the guestbook's "steps (`SC-5`)". So the freeze needs a
  prose exception, as COH-implement-5 made for `GuestbookPage.tsx`.

Ready patch:
- `tests/unit/test_guestbook_entry_model.py`:163-164. Replace "The template's schema is one table
  and no edges. A relationship appearing here means a second context arrived, and `spec/contexts/`
  has to say so." with "The guestbook's table has no edges. Since `CR-2609-823a` the schema holds
  two tables, and no foreign key joins them. A relationship appearing here means one context
  reached into another's data, and `spec/contexts/` has to say so."
- `tests/integration/test_e2e_reset.py`:43. Replace "The one table in this application's schema
  that holds a scenario's state." with "The table that marks this application's schema. Since
  `CR-2609-823a`, `todo_tasks` holds a scenario's state too. Discovery finds it because it
  exists, as `e2e/suite/conftest.py` says of `REQUIRED_TABLES`."
- `e2e/suite/steps/guestbook_steps.py`:25. Replace "The one resource this suite drives." with "The
  one resource this module drives."
- `spec/design/testing.md`:1117, the `build-tests-unit` cell. Replace
  "`tests/unit/test_guestbook_entry_model.py` (the schema holds two tables)" with
  "`tests/unit/test_guestbook_entry_model.py` (the schema holds two tables, in an assertion and in
  the docstring that counted one)".
- :1118, the `build-tests-integration` cell. After "and a docstring that called the guestbook's
  screen the only one)", add "and `tests/integration/test_e2e_reset.py` (text only: the comment
  on `REQUIRED` that counted one table)".
- The `build-tests-e2e` cell. Append "and, text only, `e2e/suite/steps/guestbook_steps.py` (the
  comment on `ENTRIES` that counted one resource)".

**What was ambiguous.** The new rule in § Four file sets names a class of prose, while its cells
name a closed list. The list came from COH-implement-4's own grep, which covered only
`tests/fitness/*.py` and `tests/integration/test_migrations.py`.

**What was not found.**
- `alembic/versions/a1b2c3d4e5f6_create_guestbook_entries_table.py`:3 ("The template's only
  revision") and :40 ("every load of the only screen") are false in the same way. They are not
  raised, because a released revision is never edited (`contracts/README.md` § Four boundaries,
  three directories), so that text stands as a record.
- `tests/fitness/test_migration_safety.py`:94 and `tests/fitness/test_alembic_env_metadata.py`:8
  narrate an incident in the past tense, as pass 7 found.
- The counts of "twenty-one" scenarios in `e2e/harness/database.py` and
  `tests/fitness/test_e2e_scenarios.py` were already off before this change. The guestbook alone
  has 22 (`SC-5`). They are left out.

### COH-implement-10 — Is `GuestbookPage.tsx` inside this change, or outside it?

- **kind:** contradiction
- **severity:** minor
- **decision_mode:** AUTO
- **auto_basis:** spec/design/architecture.md § The files
- **ambiguity_source:** spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/architecture.md § What this change does not move
- **artifacts:** design/delta/architecture.md, tasks.md, frontend/src/contexts/guestbook/pages/GuestbookPage.tsx

**What each says.** Two change documents still call the file untouched:
- `design/delta/architecture.md` § What this change does not move (:190-191): "Its frontend
  changes by three import paths and nothing else." `delta-history.md`:273 carries the same
  sentence into the assembled record.
- `tasks.md` T-22 (:724-726): "`frontend/src/contexts/guestbook/pages/GuestbookPage.tsx` is
  outside this change, because the guestbook's frontend changes by three import paths and nothing
  else". § Outside every task, item 6 (:950): "the architecture keeps `GuestbookPage.tsx`
  untouched".

Three sources say otherwise:
- This round's row in `spec/design/architecture.md` § The files (:630): "the one exception to
  "nothing else moves", and prose alone".
- `design/delta/converge.md` § This change owns.
- The diff: `git diff main --stat -- frontend/src/contexts/guestbook` lists `GuestbookPage.tsx`
  (`2 +-`).

**Why they cannot both be true.** The change edits the file, and two of its own documents say it
does not. The final review reads the diff against these documents. A reader of `tasks.md` or
`delta-history.md` would take the edit for scope that grew without a decision. Graded minor.

**What settles it.** `spec/design/architecture.md` § The files ranks above both change documents,
and names the file as the one exception.

**Resolution.** Both change documents name the exception.

Ready patch:
- `design/delta/architecture.md`:190-191. Replace "Its frontend changes by three import paths and
  nothing else." with "Its frontend changes by three import paths and one line of
  `GuestbookPage.tsx`'s module docstring (`spec/design/architecture.md` § The files,
  COH-implement-5), and nothing else." If COH-implement-9 lands, the same bullet's "its steps"
  also names the one comment in `guestbook_steps.py`.
- `tasks.md`:724-726. Replace "is outside this change, because the guestbook's frontend changes
  by three import paths and nothing else (`design/delta/architecture.md` § What this change does
  not move)" with "is outside this task. The guestbook's frontend changes by three import paths,
  and later by one line of that file's docstring, which the implement stage's convergence round
  gave build-frontend (`spec/design/architecture.md` § The files, COH-implement-5)".
- `tasks.md`:950. Replace "keeps `GuestbookPage.tsx` untouched" with "keeps what
  `GuestbookPage.tsx` does untouched".

**What was ambiguous.** The fragment restates the live row's freeze as its own count of three
import paths, so the freeze has two homes. COH-implement-5's resolution edited the live row. The
count was not on its patch list, and `tasks.md` quotes the count.

**What was not found.** The freeze on what the guestbook does holds. `git diff main --
frontend/src/contexts/guestbook/pages/GuestbookPage.tsx` changes one docstring line.

### What was checked and agrees

- **The authors' assumptions, TD-4…TD-8.** Each matches what the neighbour wrote:
  - build-frontend (TD-7): `staleTime: 0` sits in the `useTodoTasks` options alone, and
    `GuestbookPage.tsx`:30 matches the ready patch word for word.
  - build-tests-uat: step 14 reads as it says, and steps 16, 17, 19 and 20 do reload or enter the
    address.
  - build-tests-unit (TD-8): the three passages of `test_context_declarations.py` read as it says,
    and both headers declare `peer:shared-kernel` (`spec/contexts/todo_list.md`:5,
    `spec/contexts/guestbook.md`:5).
  - build-tests-integration (TD-6): one line changed.
  - review-converge (TD-4): one row added.

  build-frontend's "No vitest case asserts the header-link read" is COH-implement-8. Pass 7
  checked the older blocks, and nothing they speak of moved.
- **The two freshness rules.** The guestbook's sentence in `system-states.md` matches `main.tsx`:34-35
  (`refetchOnWindowFocus: false`, `staleTime: 30_000`), and no guestbook hook sets a `staleTime`
  of its own. `refetchOnWindowFocus` is still `false`, so UAT steps 9 and 11 hold: a screen that
  stays open is not read again. Steps 14, 15 and 18 give the answers they expect under the new
  option.
- **The reds, told the way they happened.** `testing.md`'s lead sentence matches `tasks.md`:
  - T-11 and T-14 name the two baseline reds under **Turns green:** (:520, :581-583).
  - :916-917 calls them baseline reds.
  - The fitness run is green, as `todo_list.md` says.

  The session trace also records an acceptance at the plan close (`[19:43] stage_closed: closed
  plan, opened implement (boundary -> RED; accepted RED: Application check, Suite fitness, …`).
  Neither document says the design close was the only acceptance, so this is incomplete rather
  than false, and it is not raised.
- **The corpus's rules document.** Its five sentences stand where `architecture.md` names them.
  Both deletion lists still count `text-measurement.json` among the guestbook's files, although
  the kernel's two halves are tested against it. That is the incompleteness pass 5 recorded as
  known and routed (design-spec, ADR draft 1). This round's parenthesis does not change it.
- **The front matter of `system-states.md`** lists `R-5` and `R-10`, and the new paragraph cites
  `R-3`. Not raised: the behaviour is the to-do screen's, and the front matter of `todo-list.md`
  carries `R-3`.
- **`tests/integration/test_migrations.py`:128**, "read on every load of the guestbook's screen",
  reads as a page load. It argues for an index and claims nothing about a header link, so it does
  not contradict the 30 seconds in `system-states.md`.
- **Glossary and invariants.** No identifier this round added uses a bare `task`. `D-01`…`D-03`
  hold.

## Pass 9 — verification

The preflight printed `CONVERGENCE ROUND: 2 of 3 -- MODE: VERIFYING`, so only Phases 1, 1b and 4
ran. There was no hunt. The question was whether each of the ten recorded resolutions of the
`implement` stage landed in the document its reconciliation named. Pass 8 found the first six
landed, and they were checked again here, because a later round can move text.

Read for it:
- this file whole;
- `uat.md`, the stage's one listed artefact;
- the diff of the last convergence round and its re-dispatches, `git diff 6009ac2 c24ac49`
  (review-converge `fa1c951`, then TD-9…TD-12);
- the passages each resolution names, in the working tree;
- the ten `ASSUMPTIONS` blocks from the preflight.

The ranked documents read above them: `spec/constitution.md` (Article VIII in full),
`spec/invariants.md`, `spec/glossary.md`, `contracts/README.md`.

Line numbers were taken from the working tree with `grep -n` and `sed -n` over each resolution's
own wording. `git status --short` shows no uncommitted edit outside the process's own state
files, so every line cited below is committed at `c24ac49`.

### Recorded resolutions

- COH-implement-1: landed (`spec/design/ui/system-states.md`:194-198). § Interactions opens with
  "Opening the to-do list reads its list, every time — the header link included", and carries the
  user's `Q-25` words at :196-198. The artefact-level patches still stand. They are
  `frontend/src/contexts/todo_list/hooks/useTodoTasks.ts`:72-77 (`staleTime: 0` at :77, the
  comment citing `R-3` clause 5 and `Q-25`) and `uat.md`:80 (step 14, "reload window A, then open
  the guestbook with the header link").
- COH-implement-2: landed (`spec/design/architecture.md`:678-689, under § Who writes what, and
  where the sets meet, :644). The README "is in no member's set", with template issue #92, the
  five sentences and the user's `Q-26` words at :688-689. As intended, the five sentences stand
  unchanged at `golden-set/README.md`:23, :30, :32, :48 and :98.
- COH-implement-3: landed (`spec/README.md`:65-67, `CLAUDE.md`:130-131). Both read "the
  guestbook's files in both halves of the corpus `golden-set/` (never the to-do list's
  `todo-task-text.json` and `todo-tasks-*.json`)". The two names cover all five to-do files that
  `ls golden-set/fixtures golden-set/seed` lists.
- COH-implement-4: landed (`spec/design/testing.md`:1054-1059 for the rule; :1117 and :1118 for
  the cells). The docstrings:
  - `tests/fitness/test_context_declarations.py`:31-33, :301 and :340;
  - `tests/fitness/test_context_boundaries.py`:28-30, :146 and :215-217;
  - `tests/fitness/test_data_invariants.py`:16-19 and :93;
  - `tests/fitness/test_migration_safety.py`:27;
  - `tests/integration/test_migrations.py`:128.
- COH-implement-5: landed (`spec/design/architecture.md`:630, the `GuestbookPage.tsx` row). The
  file itself, `frontend/src/contexts/guestbook/pages/GuestbookPage.tsx`:30, reads "the
  guestbook's screen, one of this application's two". Its row in § This change owns is at
  `design/delta/converge.md`:237.
- COH-implement-6: landed (`spec/design/testing.md`:958-963 for the lead sentence, :982-986 for the
  third bullet; `spec/contexts/todo_list.md`:30-32). Each now says a red was declared on the task
  that turned it red, or accepted by name at the design close (`Q-24`) and carried as a baseline
  red. Neither document quotes the user's `Q-27` words, and the resolution does not ask for them.
- COH-implement-7: landed (`spec/design/ui/system-states.md`:195-201).
  - :195 reads "the screen reads its list afresh and shows the tasks as they are stored at that
    moment".
  - :198-199 reads "A list it read earlier in the same tab stays on screen only until that read
    answers, and is then replaced".
  - The user's `Q-28` words are at :199-200.
  - `grep -c "never a copy it read earlier"` over the file printed `0`.

  The resolution's "the code stays as it is" also holds: `git diff --stat 6009ac2 c24ac49 --
  frontend/src/contexts/todo_list frontend/src/main.tsx` printed nothing, and `grep -rn gcTime
  frontend/src` found nothing.
- COH-implement-8: landed (`spec/design/testing.md`:760, the `R-3` row). It names
  **frontend/src/router.test.tsx**, under `main.tsx`'s defaults, with the user's `Q-29` words. The
  case exists at `frontend/src/router.test.tsx`:176. Its query client at :112-119 copies
  `frontend/src/main.tsx`:34-35 (`refetchOnWindowFocus: false`, `staleTime: 30_000`).
  `./scripts/test.sh frontend` printed `✓ |dom| src/router.test.tsx (4 tests)` and
  `Tests  243 passed (243)`.
- COH-implement-9: landed. The cells are `spec/design/testing.md`:1117 ("in an assertion and in
  the docstring that counted one"), :1118 (`tests/integration/test_e2e_reset.py`, text only) and
  :1120 (`e2e/suite/steps/guestbook_steps.py`, text only). The new row in § This change owns is
  `design/delta/converge.md`:238. The freeze exception is `design/delta/architecture.md`:190-193,
  "save one comment in `e2e/suite/steps/guestbook_steps.py` … prose alone". The three comment
  edits are:
  - `tests/unit/test_guestbook_entry_model.py`:163-165;
  - `tests/integration/test_e2e_reset.py`:43-45, with `REQUIRED` unchanged at :48;
  - `e2e/suite/steps/guestbook_steps.py`:25.
- COH-implement-10: landed. `design/delta/architecture.md`:193-195 reads "three import paths and
  one line of `GuestbookPage.tsx`'s module docstring … COH-implement-5". `tasks.md`:724-727, in
  T-22, reads "outside this task … and later by one line of that file's docstring". `tasks.md`:950-952
  (§ Outside every task, item 6) reads "keeps what `GuestbookPage.tsx` does untouched".

A grep of each named document for the wording its resolution replaced found nothing, and every
exit code was 1. The strings searched were:
- "vacuously true today", "Vacuously true with one context", "With one context nothing", "one
  revision here creates", "every load of the only screen" and "the only screen in this
  application", over `tests/fitness/*.py`, `tests/integration/test_migrations.py` and
  `GuestbookPage.tsx`;
- "The template's schema is one table", "The one table in this application's schema" and "The one
  resource this suite drives", over `tests` and `e2e`;
- "three import paths and nothing else", over the architecture fragment and `tasks.md`;
- "keeps `GuestbookPage.tsx` untouched", over `tasks.md`.

The only copy of the old COH-implement-10 sentence left is `delta-history.md`:273. That file is
assembled from the fragments, as its own header says, and the resolution did not name it.
review-converge's assumption says the same.

The authors' assumptions that speak of these edits match the text:
- review-converge left `requirements.md` § R-3 clause 5 unedited. COH-implement-7's resolution
  names `system-states.md` alone.
- build-frontend's `staleTime: 0` sits in `useTodoTasks.ts` only, and `main.tsx` keeps 30 seconds.
- build-tests-frontend's case is green with its one extra `open()` parameter.
- build-tests-integration, build-tests-unit and build-tests-e2e each changed one comment, word for
  word from the ready patch.

No `verification` finding. All ten resolutions landed.

## Pass 10 — the `spec_sync` stage

The preflight printed `COHERENCE PASS: the first one (before any round) -- a full hunt.` It listed
no recorded finding of this stage, so Phase 1b had nothing to check. A full hunt followed.

Read whole:
- the four fragments under `reconcile/delta/`, and `reconcile/user-guide-todo-list.md`;
- `delta.md`, which is what the design promised;
- `git show 00c97dc`, the wave's commit, over `spec/`, `CLAUDE.md`, `README.md` and `docs/`;
- both promoted ADRs, `docs/runbooks/refill-the-example-data.md` and `docs/runbooks/restore-the-database.md`.

Read in the parts the fragments answer to:
- `requirements.md` § R-6, § R-8 and § Impact analysis;
- `scenarios.md` § Test data;
- `spec/design/api.md` § The to-do list's refusals;
- `spec/design/architecture.md` § What a new environment starts with and § The files;
- `spec/design/ui/todo-list.md` § Components and their states, § Copy and § Keyboard and
  accessibility;
- `spec/design/conventions.md` § Documentation — where a document goes and § When a decision is
  an ADR;
- `spec/contexts/todo_list.md` § `BR-13` and § Neighbours;
- the to-do service, router, row, page, `PageFrame.tsx` and `StatusPages.tsx`;
- `scripts/seed_golden_set.py`, `scripts/start.sh`, `scripts/deploy.sh`, `scripts/preview.sh` and
  `scripts/help.sh`;
- the four `ASSUMPTIONS` blocks from the preflight, all captured.

The ranked documents read above them: `spec/constitution.md` (Article VIII in full),
`spec/invariants.md`, `spec/glossary.md`, `contracts/README.md` and
`contracts/invariants/README.md`.

Pairs compared:
- each fragment ↔ the edits of `00c97dc`, in both directions;
- `reconcile/delta/spec.md` ↔ `api.md`'s refusal order ↔ `requirements.md` § R-6 and § R-8 ↔
  the service and the row's editor;
- `reconcile/delta/design.md` ↔ the revision, the corpus, the service, the frame, the page and the
  fitness tests it cites;
- the promoted ADRs ↔ `CLAUDE.md` and `reconcile/delta/docs.md`;
- the ADR promotion ↔ every sentence that states what `spec/ADR/` holds;
- the user guide ↔ `todo-list.md` § Copy, the router's and the browser rule's sentences, the
  context document, and the operator pages;
- the operator pages ↔ `architecture.md` § What a new environment starts with, `data-model.md` and
  the seeder;
- what `delta.md` promised ↔ what stands now;
- the scripts' own help ↔ `seed.sh --help`, `CLAUDE.md` and the architecture;
- each author's assumptions ↔ what its neighbours wrote.

### COH-spec_sync-1 — Is the task-text data invariant written under `contracts/invariants/`?

- **kind:** gap
- **severity:** major
- **decision_mode:** AUTO
- **auto_basis:** spec/invariants.md § Data invariants
- **ambiguity_source:** spec/invariants.md § Data invariants
- **artifacts:** spec/design/data-model.md, spec/design/testing.md, contracts/invariants/README.md

**What each says.** `spec/design/data-model.md` § `todo_tasks` (:198-200): "Every `text` in this
table is NFC, trimmed at both ends, 1 to 200 code points and one line: a data invariant of the
to-do list's own under `contracts/invariants/`, the counterpart of `D-04`". `spec/design/testing.md`
§ CR-2609-823a, the to-do list (:802-806): "The convergence round of the `spec_sync` stage writes
it, the first round after its witnesses exist", with three witnesses named.

`ls contracts/invariants/` prints `README.md` and `guestbook.md`. The README's **Contracts:** line
names `guestbook.md` alone. reconcile-design's assumption says the same: "The to-do text invariant
under contracts/invariants/ is still unwritten; testing.md hands it to the spec_sync convergence
round." None of the four fragments writes under `contracts/`, and each says so of itself.

**Why they cannot both be true.** The data model says, in the present tense, that the invariant is
a contract under `contracts/invariants/`. There is none. The one obstacle `spec/invariants.md`
names is gone, because the witnesses exist:
- `tests/integration/test_todo_tasks_service.py`:134;
- `tests/unit/test_todo_task_text_rules.py`:165;
- the generator at :391-393 of the same file,
  `test_any_text_is_either_refused_or_kept_normalized_one_line_and_within_the_bound`.

Graded major. Merged as it stands, the data model cites a contract that does not exist, and the
user's decision `Q-21` (6) is not carried out.

**What settles it.** `spec/invariants.md` § Data invariants: "an invariant decided in design whose
witnesses the implementation stage writes is written by the first convergence round after they
exist — the `spec_sync` stage's". The user's `Q-21` words follow it.

**Resolution.** This stage's convergence round writes `contracts/invariants/todo_list.md` under the
next free identifier, `D-05` (`grep -rn D-05 contracts spec` finds nothing). It names the file in
`contracts/invariants/README.md`, and declares both in `delta.md`, as `contracts/README.md`
§ What enforces this requires of a contract change.

Ready patch:
- `ADDED` `contracts/invariants/todo_list.md`. The front matter follows `guestbook.md`'s
  (`contract: invariants`, `domain: todo_list`, `version: 1`), with a two-line lead. The entry:
  "## `D-05` — a stored task's text is normalized, one line, and within its bound in code points.
  Every `text` in `todo_tasks` is in Unicode NFC, carries no member of the written trim set at
  either end, holds none of the seven code points of `LINE_BREAKS`, and is between 1 and
  `TODO_TASK_TEXT_MAX_LENGTH` (200) code points long (`BR-06`, `BR-07`). It is `D-04` for the to-do
  list's one field, plus the one-line rule the guestbook does not have.
  **Witness:** `tests/integration/test_todo_tasks_service.py::test_a_stored_text_is_normalized_one_line_and_within_the_bound_in_code_points`,
  `tests/unit/test_todo_task_text_rules.py::test_every_case_gets_the_verdict_the_corpus_states`
  and `tests/unit/test_todo_task_text_rules.py::test_any_text_is_either_refused_or_kept_normalized_one_line_and_within_the_bound`.
  **Kind of evidence:** three, because the invariant is about a value, about agreement, and about
  every text. The round trip is an invocation only a database can answer. The corpus is read by
  the browser's rule test too. The generator draws from every text rather than the listed ones."
- `MODIFIED` `contracts/invariants/README.md`, the **Contracts:** line. It becomes "`guestbook.md` —
  `D-01`…`D-04`; `todo_list.md` — `D-05`; each with a witness and a kind of evidence." The line
  reads `D-01`…`D-03` today, although `guestbook.md`:85 holds `D-04`, so this also corrects a
  count this change did not break.

**What was ambiguous.** `spec/invariants.md` names "the first convergence round after they exist"
as the writer. It does not say what makes that round run. No member of the stage writes
`contracts/`, so the round exists only if the stage's coherence pass records something for it. A
clean pass would have closed the stage with the invariant unwritten.

**What was not found.** No second invariant is owed. `testing.md` says `D-01` to `D-03` need no new
witness, and the sweeps in `tests/fitness/test_data_invariants.py` reach `todo_tasks`.

### COH-spec_sync-2 — Is `spec/ADR/` empty, or does it hold two decisions?

- **kind:** contradiction
- **severity:** minor
- **decision_mode:** AUTO
- **auto_basis:** spec/constitution.md § Article IV — The specification changes on the same branch as the code
- **ambiguity_source:** spec/glossary.md § Identifiers and their spaces
- **artifacts:** spec/glossary.md, spec/README.md, spec/design/conventions.md

**What each says.** `spec/design/conventions.md` § When a decision is an ADR (:580-581), edited
this stage: "The state of `spec/ADR/`: the decisions of changes carried out through `/sdd`, the
first two from `CR-2609-823a`. It was empty until that change." `spec/ADR/index.md` lists
`ADR-0001` and `ADR-0002`. Two sentences still say otherwise:
- `spec/glossary.md`:56: "`spec/ADR/` (empty today — `design/conventions.md` § When a decision is
  an ADR)".
- `spec/README.md`:14-17: "The directory is empty today: … the first ADR will come out of the
  first change through `/forge:sdd`".

reconcile-design found both and left them, because they are outside its allowlist.

**Why they cannot both be true.** The directory holds two ADRs, and two documents say it holds
none. The glossary cites as its authority the very paragraph that now says otherwise. Graded minor.

**What settles it.** `spec/constitution.md` § Article IV. The specification edit that describes a
fact this change creates lands in the same pull request. COH-design-8 was settled the same way,
for a count this change made false.

**Resolution.** Both sentences stop stating the directory's state and point at its one home.

Ready patch (text only; an existing link stays a link):
- `spec/glossary.md`:56. Replace "(empty today — `design/conventions.md` § When a decision is an
  ADR)" with "(what it holds: `design/conventions.md` § When a decision is an ADR)".
- `spec/README.md`:14-17. Replace "The directory is empty today: the template's decisions, taken
  without a change record, stand as "decision of <date>" paragraphs in the normative documents,
  and the first ADR will come out of the first change through `/forge:sdd`" with "The template's
  decisions taken without a change record stand as "decision of <date>" paragraphs in the
  normative documents. The ADRs here come out of changes carried out through `/forge:sdd`, the
  first two from `CR-2609-823a`".

**What was ambiguous.** The glossary and the README restate the directory's state instead of only
pointing at its home. So the promotion edited the home and left the two copies. Neither is in
reconcile-design's write set. reconcile-design's assumption names reconcile-spec as the glossary's
writer, and it ran beside the promotion without seeing it.

**What was not found.** `spec/constitution.md`:219 ("`spec/ADR/` stays empty until the first change
goes through `/forge:sdd`") sits inside a dated Rejected block, is conditional, and stays true as
a record. The index's own header says nothing about the directory being empty.

### COH-spec_sync-3 — Does ADR-0001 still say that no write set of this change holds the `CLAUDE.md` edit?

- **kind:** contradiction
- **severity:** minor
- **decision_mode:** AUTO
- **auto_basis:** spec/constitution.md § Article IV — The specification changes on the same branch as the code
- **ambiguity_source:** spec/ADR/ADR-0001-todo-list-is-its-own-bounded-context.md § Consequences
- **artifacts:** spec/ADR/ADR-0001-todo-list-is-its-own-bounded-context.md, CLAUDE.md

**What each says.** reconcile-design promoted ADR-0001 "the body as drafted". Its § Consequences
says (:109-111): "The list in `CLAUDE.md` § What is an example also has to say this. That edit is
outside every write set of this change and was reported by `design-spec`, and nothing enforces
it."

In the same wave, reconcile-docs wrote that paragraph into `CLAUDE.md`:136-143: "One thing moves
before the guestbook goes: the words of the text rule." `reconcile/delta/docs.md`:20 says why:
"This stage's write set is the first to hold `CLAUDE.md`."

**Why they cannot both be true.** The ADR states a fact about the whole change, and this change's
last stage made it false. Once the ADR is accepted, it is never edited
(`spec/design/conventions.md`:577), so the false sentence would stand for good. Graded minor.

**What settles it.** `spec/constitution.md` § Article IV, as for COH-spec_sync-2. The ADR is still
`Proposed`, and conventions forbids an edit only "after acceptance".

**Resolution.** Correct the one sentence before the change merges.

Ready patch, ADR-0001:110-111. Replace "That edit is outside every write set of this change and
was reported by `design-spec`, and nothing enforces it." with "`design-spec` reported that the list
was silent, `reconcile-docs` wrote the paragraph in the `spec_sync` stage of this change, and
nothing enforces it."

**What was ambiguous.** The draft said "this change" when it meant the stages its author could
see, design and implement.

**What was not found.** ADR-0002's phrases "which the implement stage writes" are true as of the
ADR's date, and the implement stage did write those tests. They are not raised. Nothing else in
ADR-0001 is contradicted by this wave.

### COH-spec_sync-4 — Is a new environment filled when "nobody has written in it yet", or list by list?

- **kind:** contradiction
- **severity:** minor
- **decision_mode:** AUTO
- **auto_basis:** spec/constitution.md § Article IV — The specification changes on the same branch as the code
- **ambiguity_source:** spec/design/architecture.md § What a new environment starts with
- **artifacts:** spec/design/architecture.md, reconcile/delta/docs.md, scripts/seed_golden_set.py

**What each says.** `spec/design/architecture.md` § What a new environment starts with says two
things six lines apart:
- :410-412: "**Each list is filled on its own:** the guest book gets its welcome entries when it
  holds none, whatever the to-do list holds, and the to-do list gets its example tasks when it
  holds none, whatever the guest book holds."
- :416-418: "It applies to a fresh clone exactly as it applies to a preview, because "an
  environment nobody has written in yet" is one condition and not two."

`reconcile/delta/docs.md` entry 12 (:246-249) cites this section as its source. It names that
phrase as the alternative that lost: "One condition for the whole environment, "nobody has written
in it yet". An environment that existed before the to-do list … would never get its example tasks
(`Q-10`)." The seeder asks each list on its own (`scripts/seed_golden_set.py`:222-240).
reconcile-design reported that the section held.

**Why they cannot both be true.** Take an environment where somebody has written a guest book entry
and nobody has added a task. It gets its example tasks, so the seeder is not asking about "an
environment nobody has written in yet". The section names both conditions, and the change's own
intent note calls one of them rejected. Graded minor.

**What settles it.** `spec/constitution.md` § Article IV. A sentence this change made false is
corrected in this pull request, as in COH-design-8.

**Resolution.** Ready patch, `spec/design/architecture.md`:418. Replace "because "an environment
nobody has written in yet" is one condition and not two." with "because "a list that holds nothing
yet" is one condition, asked of each list, whatever kind of environment holds it."

**What was ambiguous.** `requirements.md` § Impact analysis (:558-563) read that sentence as the
fill condition, and asked for it to change with `Q-10`. The design edited the paragraphs around it
and kept it, reading "one condition" as clone against preview. Both readings are grammatical.

**What was not found.** `docs/operations.md`, `docs/deployment.md`, the refill runbook and
`./scripts/seed.sh --help` all describe the per-list condition. The only other copy of the phrase
is `requirements.md`:560, which quotes it.

### COH-spec_sync-5 — Do the scripts' help and comments still describe one list?

- **kind:** contradiction
- **severity:** minor
- **decision_mode:** AUTO
- **auto_basis:** spec/constitution.md § Article I — The specification is the source of truth
- **ambiguity_source:** spec/design/architecture.md § The files
- **artifacts:** scripts/start.sh, scripts/help.sh, scripts/deploy.sh, scripts/preview.sh, spec/design/architecture.md

**What each says.** Three sources describe two lists:
- `spec/design/architecture.md` § What a new environment starts with fills each list on its own,
  and "every run after the first costs one `GET` per list" (:439). Its :415 names `start.sh`,
  `preview.sh` and `deploy.sh` as the callers of `seed.sh`.
- `./scripts/seed.sh --help` agrees: "It fills two lists from golden-set/seed/, each on its own
  condition".
- `CLAUDE.md`:159-160, rewritten this stage: "leave both lists empty; by default an empty guest
  book or to-do list is filled".

The other scripts still describe one:
- `./scripts/start.sh --help` prints "--no-seed leave the guest book empty. By default a guest book
  that has no entries is filled from golden-set/seed/ … a book that already has entries is never
  touched."
- `./scripts/help.sh` prints "seed.sh Fill an environment's guest book from golden-set/seed/ … for
  a book that is empty".
- The comments do too: `scripts/start.sh`:106, :113-115 and :170; `scripts/deploy.sh`:620-622
  ("skips a guest book that already has entries, so on every deploy after the first this is a
  single GET"); and `scripts/preview.sh`:198-201, which says the same.

`git diff main --stat -- scripts/` lists `seed.sh` and `seed_golden_set.py` and nothing else.

**Why they cannot both be true.** `--no-seed` skips `seed.sh` altogether (`scripts/start.sh`:172),
so it leaves both lists empty, and the help names one. The deploy and preview comments count one
`GET`, and the architecture counts one per list. `--help` is the human interface (Article XII).
reconcile-docs and reconcile-ops both found this, and neither may write `scripts/`. Graded minor:
the behaviour is right and the words are wrong.

**What settles it.** `spec/constitution.md` § Article I. Code contradicting `spec/` is a defect in
the code, as in COH-implement-9.

**Resolution.** Text only, made by the author whose write set holds `scripts/*.sh`.
reconcile-ops names build-platform.

Ready patch:
- `scripts/start.sh`:48-51. Replace with "--no-seed leave both lists empty. By default a guest book
  with no entries and a to-do list with no task are each filled from golden-set/seed/ once the
  application answers, so a fresh clone opens on screens worth looking at; a list that already
  holds something is never touched."
- `scripts/start.sh`:106 becomes "#: Fill each empty list from `golden-set/seed/` once the
  application answers." At :113-114, "skips a guest book that already has entries" becomes "skips a
  list that already holds something". At :115 and :170, "an empty guest book" becomes "an empty
  list".
- `scripts/help.sh`:89-91. Replace with "Fill an environment's guest book and to-do list from
  golden-set/seed/, each on its own condition, through the API. start.sh does this on its own for
  a list that is empty; …".
- `scripts/deploy.sh`:620-622 and `scripts/preview.sh`:198-201. Replace with "A new environment
  with an empty list is a screen nobody can judge. `seed.sh` refuses production and skips a list
  that already holds something, so on every deploy after the first this is one GET per list and a
  printed line for each."

**What was ambiguous.** In `spec/design/architecture.md` § The files, the scripts row (:637) gives
build-backend `seed_golden_set.py` and `seed.sh`, "and saying so in `--help`". That is `seed.sh`'s
own help. Meanwhile § What a new environment starts with names three callers whose help and
comments describe the seeding, and no row placed their text.

**What was not found.** The behaviour holds: the seeder and `seed.sh --help` work list by list, and
`CLAUDE.md` already follows them.

### COH-spec_sync-6 — Does a restore from backup bring back the to-do list alone, or the whole application?

- **kind:** contradiction
- **severity:** minor
- **decision_mode:** HITL
- **auto_basis:**
- **ambiguity_source:** docs/runbooks/restore-the-database.md § When to use this
- **artifacts:** reconcile/user-guide-todo-list.md, docs/runbooks/restore-the-database.md

**What each says.** The user guide, § Deleting a task (:69-71): "A restore from backup is the only
way back, and it returns the whole application, the guest book included, to an earlier moment
rather than bringing back one task."

The runbook, step 3, option B (:67-71), edited by reconcile-ops this stage: "it is the only option
when only *part* of the data is wrong, because you can copy the rows you need instead of the whole
database. The two lists are two tables with no key between them, so when only one list is wrong,
B can copy that table alone and leave the other list as it is now." Then, at :73: "B is the
default." `docs/backup-and-recovery.md` § The shape of a restore agrees with B.

**Why they cannot both be true.** Under B, the default, the guest book is not rewound, and the rows
copied can be one task's. The guide says a restore always rewinds the guest book and never returns
one task. A person who reads the guide would not ask for what the operator can do. An operator who
reads it would promise less than the runbook allows. Graded minor: nothing is stored wrong, and the
guide is not yet placed (COH-spec_sync-7).

**What settles it.** Nothing ranked above both. Both are documentation, which binds nothing
(`spec/design/conventions.md` § Documentation — where a document goes).
`spec/contexts/todo_list.md` § `BR-13` ("no bin, no undo, no recovery") and the non-goal "Undo and
restore" speak of what the product offers a person. They do not say what an operator can copy
from a backup.

**Resolution.** Recommended (A): the guide follows the runbook. Replace the guide's sentence with
"There is no undo and no bin. Whoever operates the environment can bring the list back from a
backup as it was at an earlier moment, within the backup window, and that takes tens of minutes;
whatever was changed on the list since that moment is lost." Also, the runbook's lead (:17-20) and
its two restatements (`docs/runbooks/incident-first-response.md`:46-48,
`docs/runbooks/README.md`:41-42) say what B allows: "a restore brings back what it copies as it
was at a moment in the past — the whole database under A, one list or the rows you need under B —
and every write since that moment to what it brings back is lost."

(B): B stops offering one table or chosen rows, so a restore is always whole. That also means
editing `docs/backup-and-recovery.md`, which calls the export "the only option when only part of
the data is wrong".

**What was ambiguous.** The runbook has said two things since before this change. Its § When to use
this says a restore returns "the whole book", and its option B says "copy the rows you need". The
guestbook's guide took the first ("returns the whole book to a moment in the past, not one entry",
`docs/user-guide.md`:60-62), and the to-do guide copied that. This stage sharpened both: "the
*whole database*, both lists" at :17-18, and "that table alone" at :71.

**What was not found.** The recovery time agrees. The guestbook guide's "tens of minutes" and
`docs/backup-and-recovery.md`'s 20–45 minutes do not disagree.

### COH-spec_sync-7 — Where does the to-do list's user guide live, and who puts it there?

- **kind:** gap
- **severity:** minor
- **decision_mode:** HITL
- **auto_basis:**
- **ambiguity_source:** spec/design/conventions.md § Documentation — where a document goes
- **artifacts:** reconcile/delta/docs.md, reconcile/delta/ops.md, reconcile/user-guide-todo-list.md

**What each says.**
- `reconcile/delta/docs.md`:21: "this template keeps a screen's user guide in `docs/`
  (`docs/user-guide.md` for the guest book), and `docs/` is outside this member's write set. So the
  page is written here, whole, for placement at `docs/user-guide-todo-list.md` with a row in
  `docs/README.md`."
- The page's own note (:8-11): "Where this page belongs. Beside `docs/user-guide.md` … Delete this
  note when the page moves."
- `reconcile/delta/ops.md` F-2 (:66-69): "A guide for the person using `/todo-list` is not
  operations documentation, so it is not written here, and no other `spec_sync` member's write set
  names `docs/`. Whether it should exist is the orchestrator's call."
- `docs/README.md`:25 lists `user-guide.md`, "the guest book, for the person using it", and
  nothing for the to-do list.

No change document planned a guide. `grep -i 'user guide'` over `requirements.md`, `tasks.md`,
`impact.md`, `brainstorm.md`, `design/delta/*.md` and `uat.md` finds nothing.

**Why it is a gap.** reconcile-ops, the one member whose tree is `docs/`, reads a user guide as
outside that tree. reconcile-docs, the member who wrote the guide, reads `docs/` as its home and
cannot write there. Merged as it stands, the change ships a page whose first paragraph says it is
in the wrong place. The page sits under `spec/changes/`, where `docs/README.md` does not lead.
Graded minor: the screen works, the guide exists, and placing it is one move and one row.

**What settles it.** Nothing ranked above both. `spec/design/conventions.md` § Documentation —
where a document goes (:281) gives `docs/` "the system: how to set it up, run it, configure it,
watch it, back it up and repair it", for "whoever operates or takes delivery of the application".
It names no home for a guide addressed to the person using a screen, although `docs/` held one
before this change.

**Resolution.** Recommended (A):
- The page moves to `docs/user-guide-todo-list.md`, without its placement note and with
  COH-spec_sync-6 applied.
- `docs/README.md` gains the row "the to-do list, for the person using it".
- The `docs/` row of `spec/design/conventions.md` § Documentation names the person using a screen
  among its readers.
- The orchestrator chooses who writes `docs/`, for example reconcile-ops re-dispatched with the
  move.

(B): the guide stays in the change record as its history, and `docs/` gets none. Its note then says
so rather than naming a destination.

**What was ambiguous.** The `docs/` row names the system's operation as the tree's subject, while
the tree has held a screen's user guide since before this change. So one member read the row and
the other read the precedent.

**What was not found.** Apart from the restore sentence (COH-spec_sync-6), the page agrees with the
specification, as the next section records.

### What was checked and agrees

- **The fragments against the commit.** Every edit a fragment claims is in `00c97dc`. Every edit
  under `spec/` in `00c97dc` is claimed by a fragment. The exceptions are `spec/ADR/index.md` and
  `spec/changes/INDEX.md`, which reconcile-design says `sdd-engine gen_indexes` regenerated. The
  fourteen pages in reconcile-ops' table are the fourteen `docs/` files in the diff.
  reconcile-docs' `README.md` and `CLAUDE.md` edits match its table.
- **reconcile-design's corrections hold.**
  - The revision is `5c58af1f8e8a`, with parent `a1b2c3d4e5f6`
    (`alembic/versions/5c58af1f8e8a_create_todo_tasks_table.py`:43-44).
  - `scenarios.md` § Test data lists eighteen task-text rows. `golden-set/fixtures/todo-task-text.json`
    holds 19 cases, counted with `python3 -c 'json.load…'`.
  - `_MAY_READ_ONE_CORPUS_FILE` names two readers (`tests/fitness/test_golden_set.py`:188-191).
  - `test_the_line_breaks_equal_their_browser_copy` is at `tests/fitness/test_length_constants.py`:194.
  - `test_this_schema_holds_exactly_two_tables` is at `tests/unit/test_guestbook_entry_model.py`:67.
  - `frontend/src/contexts/guestbook/lib/entryText.ts` is gone, and `frontend/src/lib/text.ts`
    exists.
  - After the last deletion, the focus goes to the empty frame (`TodoListPage.tsx`:78, :168-169).
- **`BR-13`'s new paragraph.**
  - It agrees with `api.md`'s order, step 4 (:392-393), and with `change_todo_task`, which judges
    the text before its one `UPDATE`.
  - It agrees with the row's editor, which refuses before `onSave` (`TodoTaskRow.tsx`:279-284).
  - The cited tests exist: `test_todo_tasks_router.py`:415 carries `req("CR-2609-823a/R-8")`.
  - `requirements.md` § R-8 clause 1, read literally, gives the other reason for this corner.
    `spec/design/api.md` ranks above the change's requirements and settles it, and the fragment
    cites it. Not raised.
- **One `PATCH` operation, or a correction and a marking?** Both fragments hold.
  `correct_todo_task` and `mark_todo_task` are one-line forms over `change_todo_task` (service
  :240-265), and the router calls `change_todo_task` (router :195).
- **The user guide against the screen.**
  - Its refusal and failure sentences match `todo-list.md` § Copy, the router and
    `lib/todoTask.ts` word for word. A `grep -c -F` of each found every one.
  - Its editing, focus, tick and wake-up claims match `todo-list.md` and `docs/troubleshooting.md`.
  - Its example tasks match the seed file, which holds 5 tasks with 1 done.
- **The frame's footer.** `architecture.md`:632 and `docs.md` entry 16 put "the not-found page
  passes none" beside "`GuestbookPage.tsx` passes none of its own". Read the second way, the
  not-found page would take the default footer. The code passes `footer={null}`
  (`StatusPages.tsx`:21, `PageFrame.tsx`:123), as `system-states.md` wants. Read as "passes no
  footer", the documents agree, so this is not raised. Writing "passes `null`" would leave one
  reading.
- **ops F-1's `CLAUDE.md` half** was closed in the same wave: reconcile-docs rewrote
  `CLAUDE.md`:159-160. The rest of F-1 is COH-spec_sync-5.
- **reconcile-docs' candidates for others.**
  - The rejected optimistic update. The rule stands in `architecture.md` (the `useTodoTasks.ts`
    row, "the cache written only from answers"). The rejection stands in the hook's module comment,
    where Article IX puts intent. No document contradicts it.
  - The `PROC-46` troubleshooting entry is unwritten. That is routing, not a disagreement.
- **Drift that predates this change.** Both authors reported it and left it: `number.ts` in
  conventions, the `EmptyState` section, the log line in `operations.md`, and "seven steps" in
  `deployment.md`. It is on `main` already. `git show main:docs/deployment.md` has "seven steps" at
  :35, and `git show main:spec/design/ui/system-states.md | grep -c EmptyState` printed `1`.
- **Each author's assumptions** match what the neighbour wrote:
  - reconcile-design: the glossary and README are COH-spec_sync-2, and the invariant is
    COH-spec_sync-1.
  - reconcile-docs: the guide is COH-spec_sync-7, the scripts are COH-spec_sync-5, and the
    optimistic update is above.
  - reconcile-ops: F-1 is COH-spec_sync-5, F-2 is COH-spec_sync-7, and F-3 predates the change.
  - reconcile-spec: `api.md` describes the request-shape refusals (:385-393), and the guide does
    not restate `BR-13`'s corner.
- **Glossary and invariants.** No identifier this wave added uses a bare `task`, and `D-01` to
  `D-03` hold.

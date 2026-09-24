# Requirements — the to-do list: add tasks and mark them done

**Change:** CR-2609-823a
**Source:** request.md, impact.md, brainstorm.md (answers `Q-1`…`Q-9`), and the answers
`Q-10`…`Q-12` recorded in the change record on 2026-09-24

## Goal

Anybody who opens the application can reach a second screen, a shared to-do list, add a task
of one line, tick it done and back, correct it and delete it, while the guestbook stays where
it is and keeps working as it does today.

Words used below, none of which is in `spec/glossary.md` yet (giving them a home is the design
stage's job): a **task** is one line of text somebody put on the list; **the to-do list** is the
one list of tasks every visitor shares; **done** and **not done** are the one state a task has,
switched both ways; **the moment of adding** is when the system stored a task. It orders the
list and never changes.

## Success criteria

| Id | Criterion | Baseline | How measured after delivery |
|---|---|---|---|
| **SC-1** | A person who has never seen the to-do list reaches it from the guestbook, adds a task and finds it at the top of the list, with no instruction. | None. Nobody can add a task today: no to-do concept exists in the specification or in the code (`impact.md` § What is missing). | The requester follows the `uat.md` script on the delivered branch before merging and records pass or fail per step. That is the one look after delivery this template schedules. |
| **SC-2** | Two people looking at the list after a reload see the same tasks, in the same order, with the same done marks. | None. The guestbook is the only thing people share today, and it has no state anybody marks. | The requester checks it at UAT with two browser windows (`uat.md`). The scenarios tagged `CR-2609-823a/R-3` and `CR-2609-823a/R-9` re-check it on every CI run of the branch. |
| **SC-3** | A task ticked done by mistake goes back to not done in one action, and neither action moves it in the list. | None. Nothing the application stores has a state that can be switched (`spec/contexts/guestbook.md` § `P-01`: "An entry either exists or it does not"). | A `uat.md` step at UAT, plus the scenarios tagged `CR-2609-823a/R-4` on every CI run. |
| **SC-4** | A reviewer who opens a freshly created environment sees example tasks on the list without typing any. | A freshly created environment opens today with the guestbook's welcome entries (`golden-set/seed/entries-welcome.json`) and nothing else. | The reviewer opens the first preview of this branch (Actions → Preview), or runs `./scripts/start.sh` on a fresh clone, and counts the example tasks. This is manual because the black box starts with `--no-seed` (`R-11`). |
| **SC-5** | A guest who knows the guestbook finds it where it was: the main address still opens it and everything it did before still works. | The main address redirects to the guestbook (`spec/design/ui/system-states.md` § Interactions). The 22 scenarios in `e2e/suite/features/guestbook.feature` pass. | The 22 scenarios of `e2e/suite/features/guestbook.feature` run unchanged on every CI run of this branch. The UI smoke's guestbook tests keep asserting what they assert today; a locator that names the lockup or a navigation link may follow the names the user approves in the mock-up (§ Open questions; Self-check 14; assumed: `A-4`, § Named assumptions). The requester checks at UAT. |

## Requirements

### R-1: Adding a task — **P1**
**Objective:** As anybody who opens the to-do list, I want to add a task by typing one line, so
that it joins the shared list of things to do.
**Why this priority:** Without it there is no list. Every other requirement acts on a task this
one creates.
**Independent test:** Add one task to an empty list and read the list back.

1. The system SHALL present one screen holding one field for a new task's text, with the list of
   tasks below that field (`request.md`: "a simple view with a field for adding tasks and a list";
   `Q-6`: "right under the field").
2. The system SHALL let anybody who opens the to-do list add a task, with no account and no
   sign-in.
3. WHEN a person submits a text for a new task, the system SHALL store one task holding that
   text as `R-2` shapes it, record it as not done, and record its moment of adding.
4. WHEN a task has been added, the system SHALL show it first in the list without the person
   reloading the screen.
5. WHEN a person submits a text identical to the text of a task already on the list, the system
   SHALL store a second, separate task (`Q-9`).

**Acceptance**
- **R-1.1** GIVEN an empty to-do list, WHEN a person adds the task "Water the plants", THEN the
  list holds exactly one task, its text is "Water the plants", and it is shown as not done.
- **R-1.2** GIVEN a list holding the task "Buy bread", WHEN a person adds "Buy bread" again,
  THEN the list holds two tasks with that text, and marking one of them done leaves the other
  not done.
- **R-1.3** GIVEN a list of two tasks, WHEN a person adds a third, THEN the third is shown first
  without the page being reloaded.
- **R-1.4** GIVEN a request to add a task that arrives already claiming to be done, WHEN it is
  stored, THEN the new task is not done.

### R-2: What is not a task is refused — **P1**
**Objective:** As a reader of the list, I want empty and over-long texts kept out, so that the
list never shows a row with nothing in it.
**Why this priority:** It is the other half of `R-1`. Shipping `R-1` without it stores empty
rows on the first day.
**Independent test:** Submit a text of three spaces and confirm the list is unchanged.

1. The system SHALL normalize a task's text to Unicode NFC and trim both of its ends of the
   written 30-code-point whitespace set, before it measures the text. This is the rule the
   system already applies to every text field it accepts (`spec/design/conventions.md` § Backend,
   on `app/platform/schemas/text.py`; the set is defined in `spec/contexts/guestbook.md` § `BR-01`).
2. IF a task's text is empty after trimming, THEN the system SHALL refuse it, store nothing, and
   tell the person that a task needs text.
3. IF a task's text is longer than 200 code points after normalizing and trimming, THEN the
   system SHALL refuse it, store nothing, and tell the person that the text is too long.
4. WHERE a text, once clause 1 has trimmed it, still carries whitespace other than a line break,
   the system SHALL keep that whitespace unchanged.
5. The system SHALL accept on the screen exactly the texts the service accepts. The field
   SHALL NOT block, cut short or silently stop taking a text the service would store, and the
   screen SHALL NOT let through a text the service would refuse.
6. IF a task's text, once clause 1 has trimmed it, still carries a line break, THEN the
   system SHALL refuse it, store nothing, and tell the person, with a reason of its own, that a
   task is one line (`Q-11`: "Refuse it, with its own message"). A line break is any of U+000A,
   U+000B, U+000C, U+000D, U+0085, U+2028 and U+2029: one written set that the screen and the
   service both read, never either language's default (assumed: `A-1`, § Named assumptions).
   Every one of them is in clause 1's trim set, so a line break at either end is removed by
   clause 1 and is not refused. A character that shows nothing but is not in the trim set, such
   as U+200B, is content, so a line break beside it is inside the text (assumed: `A-3`, § Named
   assumptions).

**Acceptance**
- **R-2.1** GIVEN the text "   " (three spaces), WHEN it is submitted as a new task, THEN it is
  refused, the person is told why, and the list is unchanged. The same holds for the empty text.
- **R-2.2** GIVEN a text of exactly 200 code points, WHEN it is submitted, THEN it is accepted
  and stored whole. GIVEN one of 201 code points, THEN it is refused and the list is unchanged.
- **R-2.3** GIVEN a text of 200 × U+1F600 (200 code points, 400 UTF-16 code units), WHEN it is
  typed or pasted into the field and submitted, THEN the screen takes every character and the
  service stores the task. GIVEN 201 of them, THEN the screen and the service both refuse it,
  for the same reason.
- **R-2.4** GIVEN a text of 200 letters, each written as U+0065 followed by U+0301 (400 code
  points before normalizing, 200 after), WHEN it is submitted, THEN it is accepted and stored as
  200 code points.
- **R-2.5** GIVEN a text of 200 code points with two spaces before it and two after (204 as
  typed), WHEN it is submitted, THEN it is accepted and stored as the 200 code points without
  the spaces. GIVEN a text of 205 spaces, THEN it is refused as empty, not as too long.
- **R-2.6** GIVEN the text "Buy  two   lamps", WHEN it is submitted, THEN it is stored with its
  inner spaces exactly as typed.
- **R-2.7** GIVEN the text "Buy bread", a line feed, then "and milk", WHEN it is submitted as a
  new task, THEN it is refused with the one-line reason, not as empty or too long, and the list
  is unchanged. GIVEN "Buy bread" followed by one line feed, THEN it is accepted and stored as
  "Buy bread".

### R-3: One shared list, in one order — **P1**
**Objective:** As anybody who opens the to-do list, I want every task on one list in the order
the tasks were added, newest first, so that everybody reads the same list the same way.
**Why this priority:** The list is what a person looks at. Without a settled order two people
see two different lists, and a task just added gets lost among the others.
**Independent test:** Add three tasks, then read the list from a second browser.

1. WHEN the to-do list is opened, the system SHALL show every stored task, done and not done
   alike, on one list, with no division into pages and no filter (`Q-9`).
2. The system SHALL order the list by moment of adding, newest first (`Q-6`).
3. WHERE two tasks share a moment of adding, the system SHALL show them in the same relative
   order every time the list is read, so that the order is total.
4. WHEN a task is marked done or not done, or its text is edited, the system SHALL keep it in
   the same position in the list (`Q-4`, `Q-6`).
5. WHEN the list is opened or reloaded, the system SHALL show the tasks exactly as they are
   stored at that moment, including tasks other people have added, marked, edited or deleted.
6. WHEN the list holds no task, the system SHALL say that it is empty, with a sentence about what
   to do, and SHALL NOT present it as an error (`spec/design/ui/system-states.md` § Components and their states:
   "Emptiness always carries a sentence about what to do").

**Acceptance**
- **R-3.1** GIVEN the tasks "First", "Second" and "Third", added in that order, WHEN the list is
  opened, THEN it shows "Third", "Second", "First".
- **R-3.2** GIVEN two tasks with the same moment of adding, WHEN the list is read twice, THEN both
  reads show them in the same relative order.
- **R-3.3** GIVEN 101 stored tasks, WHEN the list is opened, THEN all 101 are shown on one list,
  with nothing to press to see more. (101 is one more than the largest piece the guestbook's read
  hands out, and more than its default piece of 20.)
- **R-3.4** GIVEN the list "Third", "Second", "First" with "Second" not done, WHEN "Second" is
  marked done, THEN the list still reads "Third", "Second", "First". The order is also unchanged
  after the text of "Second" is edited.
- **R-3.5** GIVEN person A has the list open, WHEN person B adds a task and A reloads the list,
  THEN A sees B's task first.
- **R-3.6** GIVEN no stored task, WHEN the list is opened, THEN the screen says the list is empty,
  with a sentence about what to do, and shows no error.

### R-4: Marking a task done and not done — **P1**
**Objective:** As anybody, I want to tick a task done, and tick it back if I ticked it by
mistake, so that the list says what is left to do.
**Why this priority:** It is the point of the request: "mark that a task is done" (`request.md`).
**Independent test:** Tick one task done, reload, tick it back, reload.

1. WHEN a person marks a not-done task as done, the system SHALL record it as done.
2. WHEN a person marks a done task as not done, the system SHALL record it as not done (`Q-2`).
3. WHEN a person marks a task, the system SHALL record the state the person chose, whatever
   state was stored at that moment: marking done a task already done leaves it done, and marking
   not done a task already not done leaves it not done.
4. WHEN a task is marked done or not done, the system SHALL leave its text unchanged.
5. The system SHALL show, for every task in the list, whether it is done, and SHALL show a done
   task differently from a not-done one (`Q-4`).
6. WHILE a task is shown as done, the system SHALL keep its text at or above the contrast floor
   every text on screen clears, 4.5:1 against the surface it is painted on
   (`spec/design/ui/system-states.md` § Tokens).

**Acceptance**
- **R-4.1** GIVEN the not-done task "Buy bread", WHEN a person marks it done and reloads the
  list, THEN "Buy bread" is shown as done, with the same text, in the same position.
- **R-4.2** GIVEN the done task "Buy bread", WHEN a person marks it not done and reloads the list,
  THEN it is shown as not done.
- **R-4.3** GIVEN "Buy bread" is already done, because another person marked it, while this
  person's screen still shows it not done, WHEN this person marks it done, THEN it stays done and
  is not switched back to not done.
- **R-4.4** GIVEN a list holding one done task and one not-done task, WHEN it is shown, THEN the
  two are shown differently, and the done task's text measures at least 4.5:1 against the surface
  behind it.

### R-5: Two screens and the way between them — **P1**
**Objective:** As somebody using the application, I want to move between the guestbook and the
to-do list, so that I can find the list without knowing its address while the guestbook stays
where it was.
**Why this priority:** A to-do list at an address nobody is shown is a list nobody uses.
`spec/design/ui/system-states.md` § One column says a second screen "must add navigation here".
**Independent test:** From the guestbook, reach the to-do list and come back without typing an
address.

1. The system SHALL give the to-do list an address of its own, and entering that address
   directly SHALL open the list (`Q-5`).
2. WHILE a person is on the guestbook screen or on the to-do list screen, the system SHALL offer
   a way to reach the other screen without typing an address (`Q-1`).
3. WHEN a person opens the application's main address, the system SHALL show the guestbook, as it
   does today (`Q-5`).
4. The system SHALL NOT say anywhere on its screens that the application has one screen (`Q-1`:
   that copy "stops being true").

**Acceptance**
- **R-5.1** GIVEN the to-do list's own address, WHEN a person enters it in the browser, THEN the
  to-do list opens.
- **R-5.2** GIVEN the guestbook screen, WHEN a person uses the way to the other screen, THEN the
  to-do list opens with no address typed. GIVEN the to-do list screen, the same way leads back
  to the guestbook.
- **R-5.3** GIVEN the application's main address, WHEN it is opened, THEN the guestbook is shown.
- **R-5.4** GIVEN an address the application does not know, WHEN it is opened, THEN the page that
  says nothing is there does not claim the application has one screen.

### R-6: Editing a task's text — **P2**
**Objective:** As anybody, I want to correct a task's text, so that a typo or a changed plan does
not mean deleting the task and adding it again.
**Why this priority:** The list works without it, because delete and re-add is a workaround, but
the user put it in scope (`Q-3`).
**Independent test:** Edit one task's text and read it back.

1. WHEN a person changes a task's text, the system SHALL store the new text and show it in the
   task's place.
2. WHEN a task's text is edited, the system SHALL leave the task's state as it is stored at that
   moment and leave its moment of adding unchanged (`Q-9`: "Editing changes the text only, never
   done or not done").
3. WHERE a task is done, the system SHALL let a person edit its text exactly as it does for a
   not-done task (`Q-9`).
4. IF an edited text is empty after trimming, is longer than 200 code points after normalizing
   and trimming, or, once trimmed, still carries a line break, THEN the system SHALL refuse the
   edit, keep the task's previous text, and tell the person why (`R-2`).

**Acceptance**
- **R-6.1** GIVEN the not-done task "Buy bred", WHEN it is edited to "Buy bread", THEN the list
  shows "Buy bread", not done, in the same position.
- **R-6.2** GIVEN the done task "Call the plumber", WHEN it is edited to "Call the plumber again",
  THEN it is still done and in the same position.
- **R-6.3** GIVEN the task "Buy bread", WHEN it is edited to "   ", THEN the edit is refused and the
  task still reads "Buy bread". An edit to a text of 201 code points is refused the same way. An
  edit to a text with a line break between two words is refused the same way.

### R-7: Deleting a task — **P2**
**Objective:** As anybody, I want to remove a task, with one question before it goes, so that a
list does not fill with things nobody will do and a slip of the mouse deletes nothing.
**Why this priority:** Useful and independent of every other operation, and in scope (`Q-3`).
**Independent test:** Delete one task out of three and confirm the other two remain.

1. WHEN a person asks to delete a task, the system SHALL ask them to confirm before it deletes
   anything (`Q-9`).
2. WHEN the person confirms, the system SHALL delete the task permanently, with no bin, no undo
   and no recovery (`Q-9`).
3. IF the person does not confirm, THEN the system SHALL leave the task as it was.
4. WHEN a task is deleted, the system SHALL leave every other task unchanged.

**Acceptance**
- **R-7.1** GIVEN the tasks "Alpha", "Beta" and "Gamma", WHEN a person deletes "Beta" and
  confirms, THEN the list holds "Alpha" and "Gamma", and "Beta" does not come back after a reload.
- **R-7.2** GIVEN the task "Beta", WHEN a person asks to delete it and then cancels, THEN "Beta"
  is still on the list, unchanged.

### R-8: A task that no longer exists — **P2**
**Objective:** As somebody whose screen is out of date, I want to be told clearly when the task I
am acting on has been deleted, so that I never believe I changed something that is gone.
**Why this priority:** Without identity anybody can delete any task, so this happens as soon as
two people use the list. The user asked for "a clear message" (`Q-9`).
**Independent test:** Delete a task through one browser, then try to mark it done through
another.

1. IF a person edits, marks or deletes a task that has already been deleted, THEN the system
   SHALL change nothing, create no task, and tell the person the task no longer exists.
2. IF the same task is deleted a second time, THEN the system SHALL refuse and tell the person it
   no longer exists, rather than report a deletion it did not perform.

**Acceptance**
- **R-8.1** GIVEN person A's screen shows "Buy bread" and person B has deleted it, WHEN A marks it
  done, THEN A is told the task no longer exists, and after a reload no "Buy bread" is on the list.
- **R-8.2** GIVEN the same situation, WHEN A saves an edit of "Buy bread" to "Buy rye bread", THEN
  A is told the task no longer exists, and no task "Buy rye bread" appears.
- **R-8.3** GIVEN a task already deleted, WHEN it is deleted again, THEN the person is told it no
  longer exists.

### R-9: Two people changing one task at once — **P2**
**Objective:** As one of several people sharing the list, I want changes made at the same moment
to settle predictably, so that my tick is never silently undone by somebody else's edit.
**Why this priority:** It applies only when two people act on one task at once, but when that
happens and this requirement is missing, a change is lost with nothing on screen to show it.
**Independent test:** Send an edit and a mark for one task before either one is answered.

1. WHEN two people change the text of the same task at the same moment, the system SHALL keep
   the text from the change applied later (`Q-9`: "the later change wins").
2. WHEN one person edits a task's text while another marks the same task at the same moment, the
   system SHALL keep both changes, the edited text and the chosen state, in whichever order they
   are applied.
3. WHEN two people mark the same task at the same moment, the system SHALL end with the state
   chosen in the change applied later.

"At the same moment" means that both changes are sent before either one is answered.

**Acceptance**
- **R-9.1** GIVEN the not-done task "Buy bread", WHEN A edits it to "Buy rye bread" and B marks it
  done, both before either is answered, THEN the task reads "Buy rye bread" and is done, whichever
  change was applied first.
- **R-9.2** GIVEN the task "Buy bread", WHEN A edits it to "Buy rye bread" and B edits it to "Buy
  white bread", and B's change is applied later, THEN the task reads "Buy white bread".
- **R-9.3** GIVEN the not-done task "Buy bread", WHEN A and B both mark it done, both before either
  is answered, THEN it is done.

### R-10: A change that did not go through is not shown as made — **P2**
**Objective:** As somebody on a poor connection, I want to know when my change did not go
through, so that I never believe a task was added, ticked, edited or deleted when it was not.
**Why this priority:** The list belongs to the application, not to the browser (`brainstorm.md`
§ What was settled). A screen showing a change the application never stored lies about the one
thing the list is for.
**Independent test:** Cut the service off, tick a task, and read the screen.

1. IF adding, marking, editing or deleting a task is not stored, because the service cannot be
   reached or refuses the change, THEN the system SHALL tell the person the change was not made.
2. IF a change was not stored, THEN the system SHALL NOT show it in the list as made.
3. IF the list cannot be read, THEN the system SHALL say that the list failed to load and SHALL NOT
   say that the list is empty.

**Acceptance**
- **R-10.1** GIVEN the service cannot be reached, WHEN a person marks "Buy bread" done, THEN the
  screen says the change was not made and "Buy bread" is shown as not done.
- **R-10.2** GIVEN the service cannot be reached, WHEN a person adds a task, THEN the screen says
  the task was not added and no new task appears in the list.
- **R-10.3** GIVEN the service cannot be reached, WHEN the to-do list is opened, THEN the screen
  says the list failed to load, and does not show the empty-list sentence of `R-3.6`.

### R-11: Example tasks in a new environment — **P3**
**Objective:** As a reviewer opening a freshly created environment, I want a few example tasks
already on the list, so that I can judge the screen without typing.
**Why this priority:** The list works without it. A preview with an empty list gives nobody
anything to judge (`Q-8`).
**Independent test:** Bring up a freshly created environment and open the to-do list.
**Verified-by:** manual — the seeder is proved by `tests/tooling/` and the seed corpus by `tests/fitness/`, neither of which carries a requirement citation by rule (`spec/design/testing.md` § The UI smoke is not a traceability surface), and the black box starts the application with `--no-seed`; a person opens a freshly created environment and counts the example tasks.

1. WHEN an environment whose to-do list holds no task is filled with example data, whatever the
   guestbook holds, the system SHALL put at least three example tasks on the to-do list (`Q-10`:
   "Yes, each list is filled on its own").
2. The system SHALL hold every example task to the text rules of `R-2`, and SHALL keep every
   example task under 150 code points (the seed corpus is looked at, not a boundary file).
3. IF the environment is production, THEN the system SHALL add no example task
   (`spec/design/architecture.md` § What a new environment starts with).
4. IF the to-do list already holds at least one task, THEN the system SHALL add no example task,
   so that filling an environment again never duplicates them.
5. WHEN an environment is filled with example data, the system SHALL decide whether to give the
   guestbook its welcome entries by what the guestbook holds alone, whatever the to-do list holds
   (`Q-10`).
6. WHEN the example tasks have been put on the to-do list, the system SHALL mark at least one of
   them done (`Q-12`: "Yes, at least one is done"). It is added not done and then marked, because
   a new task is never born done (`R-1` clause 3).

**Acceptance**
- **R-11.1** GIVEN a freshly created environment, WHEN it has been filled with example data, THEN
  the to-do list shows at least three tasks.
- **R-11.2** GIVEN an environment whose to-do list holds one task, WHEN it is filled with example
  data again, THEN the list still holds exactly that one task.
- **R-11.3** GIVEN a production environment, WHEN filling it with example data is attempted, THEN
  no task is added.
- **R-11.4** GIVEN the example tasks, WHEN each is measured by the rules of `R-2`, THEN each is
  accepted and none reaches 150 code points.
- **R-11.5** GIVEN an environment whose guestbook holds its welcome entries and whose to-do list is
  empty, WHEN it is filled, THEN the list shows the example tasks and the guestbook holds exactly
  the entries it held before.
- **R-11.6** GIVEN a to-do list holding one task and an empty guestbook, WHEN it is filled, THEN
  the guestbook gets its welcome entries and the list still holds exactly that one task.
- **R-11.7** GIVEN a to-do list just filled with example tasks, WHEN it is shown, THEN at least one
  example task is shown as done.

## Edge cases

### Defects that have already happened once

| Source | What it was | Can this change bring it back? | Evidence |
|---|---|---|---|
| `contracts/invariants/guestbook.md` § `D-04`; `spec/design/data-model.md` § `guestbook_entries` | The browser counted UTF-16 code units and every other layer counted code points. All four literals read 80, so a signature of 41 emoji was refused by the screen and stored by the API with a 201. | **Yes.** A new text field with a new bound and a new browser copy is exactly where it happened. `tests/fitness/test_length_constants.py` compares numbers only and holds the three existing bounds, not a fourth. Answered by `R-2` clause 5 and `R-2.3`. | "a signature of 41 emoji was refused by the screen and stored by the API with a `201`" (`data-model.md`) |
| `spec/design/ui/guestbook.md`, the decision of 2026-09-17 | The field's `maxLength` counted UTF-16 units, so the signature field silently stopped taking characters after 40 emoji. "The guest loses what they typed with no sentence anywhere saying why." | **Yes.** A one-line field with a bound of 200 is the natural place to add that attribute again. Answered by `R-2` clause 5 and `R-2.3`. | `spec/design/ui/guestbook.md`, "No field stops accepting input at its bound" |
| `spec/design/api.md` § Collection read parameters | The bound was measured before the trim: 205 spaces in the phrase earned a "too long" refusal while 205 spaces in a signature was "empty". | **Yes**, for the new field. Answered by `R-2` clause 1 and `R-2.5`. | "two hundred and five spaces earned a `422`" (`api.md`) |
| `spec/design/api.md`, the preamble | A `404` refusal was raised without being declared, so no generated artefact knew it and the frontend normalised it by hand. | **Yes.** "The task no longer exists" (`R-8`) is a new refusal. `R-8` states the behaviour; declaring the refusal in the contract is `spec/design/api.md` § Refusals' standing rule, for the design stage. | `api.md`: "the `404` … existed in no generated artefact" |
| `spec/design/ui/system-states.md` § Tokens, the decision of 2026-09-16 | Quiet text (`--color-faint`) measured 2.92:1 on a card and 2.54:1 on a medium surface, below the 4.5:1 floor. | **Yes, and it is the likeliest one.** "Shown as done" invites greyed-out text. Answered by `R-4` clause 6 and `R-4.4`. | `system-states.md` § Tokens, first rejected alternative |
| `spec/design/ui/system-states.md` § One palette | The token `--color-base` collided with the scale's `text-base` class, and every entry's body rendered white on white. | Only if a new token is named for the done state. It stays held by `tests/fitness/test_design_tokens.py`, and the requirements add nothing. | "the whole body of every entry was white on white" |
| `spec/design/ui/guestbook.md` § in-place editing | Opening a second card mid-save moved the editor out from under the save, and a second editing session showed the first entry's content. | **Yes**, if tasks are edited in place. That is a screen decision the requirements leave to the design stage (`R-6` states only the outcome). | "Without that, opening a second card mid-save moved the editor out from under the save" |
| `spec/design/architecture.md` § What a new environment starts with; `golden-set/README.md` | One corpus served two jobs. An entry added to enrich a preview weakened a paging test, and a boundary case put an 80-character signature on screen. | **Yes**, when example tasks are added. Answered by `R-11` clause 2 (under 150 code points). The standing rule `tests/fitness/test_golden_set.py::test_no_suite_reads_the_seed_corpus` keeps suites off the seed half. | `golden-set/README.md`, "The halves were one directory, and the seam leaked" |
| `spec/invariants.md` § Deliberate non-goals (Paging and search) | A non-goal was lifted in code while `spec/invariants.md` still said the opposite, and no gate caught it. | **Yes, the other way round.** The authentication and retention non-goals are worded in the guestbook's noun ("any entry", "An entry lives until somebody deletes it"), so the file that binds every change says nothing about tasks unless the convergence round rewords it. Reported, not fixed (§ Impact analysis). | `spec/invariants.md`, "The lifting was incomplete for one turn" |
| `spec/invariants.md` § Deliberate non-goals (CSRF) | A layer echoed a token header nobody set or checked. It protected nothing and looked like protection. | No. There are still no sessions, and the to-do list adds none. | `spec/invariants.md`, CSRF item |
| `tests/_golden_set.py` history (`golden-set/README.md` § How it is read) | A hand-copied twin of the corpus locator diverged in return type and exception type. | Only if the task seed file gets a locator of its own. It stays held by `tests/fitness/test_golden_set.py::test_the_corpus_has_exactly_one_locator`. | `golden-set/README.md`, "A second locator for the second half would be that defect returning" |

`BR-01`'s "measuring before trimming" and `BR-04`'s "no tie-break" never occurred here. The guestbook's own record says so (`spec/changes/CR-2609-9b1e-guestbook/requirements.md` § Defects). They appear under Attacks below.

### Attacks
- **E-1: empty, often.** The text "" or "   " is submitted. It costs a row with nothing in it.
  The requirements say `R-2` clause 2, `R-2.1`.
- **E-2: empty, sometimes.** The list holds no task, either on first open or after the last task
  is deleted. It costs a blank area that reads like a failure. The requirements say `R-3`
  clause 6, `R-3.6`.
- **E-3: empty, sometimes.** Every task is done. It costs nothing if the list simply shows them
  all as done, and there is no special state. The requirements say `R-3` clause 1, `R-4` clause 5.
- **E-4: boundary, sometimes.** Exactly 200 code points, then 201. It costs the screen and the
  service disagreeing about what can be stored. The requirements say `R-2.2`.
- **E-5: boundary, sometimes.** 200 × U+1F600 (400 UTF-16 units). It costs a field that stops at
  100 characters and silently loses what was typed. The requirements say `R-2` clause 5, `R-2.3`.
- **E-6: boundary, rarely.** 200 decomposed letters (U+0065 U+0301). It costs a text accepted or
  refused depending on which keyboard typed it. The requirements say `R-2.4`.
- **E-7: boundary, rarely.** 205 spaces, or 200 code points padded to 204. It costs "too long"
  shown for an empty text, or a valid text refused. The requirements say `R-2.5`.
- **E-8: boundary, rarely.** 101 or more tasks on a list with no pages. It costs tasks past a
  default piece of 20 or a largest piece of 100 silently missing. The requirements say `R-3.3`.
  No upper limit on the number of tasks is stated (§ With no defined behaviour).
- **E-9: malformed, rarely.** A text with a line break inside it. A line feed or a carriage
  return arrives only through the API, because a one-line field strips those two. The other five
  characters of `R-2` clause 6's set (`A-1`) paste into the field, so the screen meets them and
  refuses them for the same reason the service does (`R-2` clause 5). It costs a task that
  renders on several lines, or a text the screen lets through and the service refuses. The
  requirements say `R-2` clause 6, `R-2.7` (`Q-11`).
- **E-10: malformed, rarely (API).** No text at all, or a value that is not text (a number,
  null). It costs a stored task with no words in it. The requirements say `R-2` clause 2 for a
  missing text. A value of the wrong type falls under the contract's standing validation
  convention (`spec/design/api.md` § Refusals).
- **E-11: malformed, rarely (API).** A new task sent already marked done. It costs a list that
  starts with finished work nobody did. The requirements say `R-1` clause 3, `R-1.4`.
- **E-12: malformed, rarely (API).** A task named by something that is not an identifier. The
  requirements do not restate it: `spec/design/api.md` § Conventions already makes "not an
  identifier" a different refusal from "no such task".
- **E-13: permission, sometimes on a public deployment.** A stranger with the link edits or
  deletes every task. It costs the whole list, with no recovery (`R-7` clause 2). The
  requirements say this is a standing non-goal (§ Non-Goals, authentication and moderation).
- **E-14: permission, sometimes.** Somebody types personal data into a task, such as a telephone
  number. It costs that value being shown to every visitor and kept until somebody deletes it.
  The requirements say this is a standing non-goal (retention policy; for tasks, `A-2`). Constitution article XI
  adds no new field here.
- **E-15: concurrent, sometimes.** An edit and a mark on one task at the same moment. It costs a
  tick silently undone by an edit, or an edit silently undone by a tick. The requirements say
  `R-9` clause 2, `R-9.1` (race `W-1`).
- **E-16: concurrent, sometimes.** Two marks from screens that are out of date. It costs a task
  flipped back although both people chose done. The requirements say `R-4` clause 3, `R-9`
  clause 3 (race `W-2`).
- **E-17: concurrent, sometimes.** An edit or a mark on a task another person has just deleted.
  It costs a deleted task coming back. The requirements say `R-8` clause 1 (race `W-3`).
- **E-18: concurrent, rarely.** Two tasks added in the same instant. It costs two readers seeing
  them in different orders. The requirements say `R-3` clause 3, `R-3.2` (race `W-4`).
- **E-19: partial failure, sometimes.** The service cannot be reached during a write. It costs a
  person who believes a change was made. The requirements say `R-10`.
- **E-20: partial failure, rarely.** The task is stored but the answer is lost on the way back.
  The screen reports a failure (`R-10`), and a retry by hand stores a second identical task. It
  costs a duplicate the person has to delete. The requirements say `R-1` clause 5 accepts the
  duplicate by decision, and no rule asks the system to detect it.
- **E-21: partial failure, rarely.** Filling a new environment stops after the first of three
  example tasks. The next run sees a list that is not empty and adds nothing, so the environment
  keeps one example task. The requirements say `R-11` clause 4. The guestbook's filling behaves
  the same way today. The same holds when filling stops after the example tasks are added and
  before one is marked done (`R-11` clause 6): the next run adds nothing and marks nothing.
- **E-22: partial failure.** The database goes away in the middle of a write. Every operation
  here touches one task, and no operation touches several ("clear all done" is a non-goal), so
  nothing can be half-applied. Clean.
- **E-23: repeated, often.** Enter pressed twice, or "add" clicked twice, before the first answer
  arrives. It costs two identical tasks nobody meant. The requirements do not say (§ With no
  defined behaviour).
- **E-24: repeated, sometimes.** The same task is deleted twice, for example by a double click on
  the confirmation. The second delete is refused with "no longer exists" (`R-8` clause 2). It
  costs a person who did delete the task reading that it no longer exists.
- **E-25: repeated, sometimes.** The same text is added twice on purpose. It costs nothing,
  because that makes two tasks (`R-1` clause 5, `R-1.2`).
- **E-26: repeated, often (every deploy).** Filling an environment runs again. It costs example
  tasks multiplying on every deploy. The requirements say `R-11` clause 4, `R-11.2`.
- **E-27: slow network, sometimes.** A write takes 30 s to answer. It costs a person who does not
  know whether to wait, retry or carry on. The requirements do not say what the screen shows
  meanwhile (§ With no defined behaviour).
- **E-28: offline, sometimes.** A task is typed with no network. The requirements say `R-10.2`
  (the failure is reported). Whether the typed text is still in the field afterwards is not
  said (§ With no defined behaviour).
- **E-29: offline, sometimes.** The list is opened with no network. It costs an unreachable
  service that reads as an empty list. The requirements say `R-10` clause 3, `R-10.3`.
- **E-30: ordering, rarely.** The moment of adding comes from a clock that runs behind another
  instance's clock. A task added later then sorts below an earlier one. The requirements say
  `R-3` clause 2: the order is by the moment the system recorded. The guestbook has the same
  exposure (`BR-04`).

### Races
- **W-1: an edit against a mark on one task.** The read-then-write: the edit reads the stored
  task (text and state), replaces the text and writes the whole task back. Between that read and
  that write the mark has stored "done". What the database holds at that moment is "done", and
  the edit's write-back replaces it with the "not done" it read. `R-9` clause 2 and `R-6`
  clause 2 forbid that outcome. The only update path in the codebase today overwrites with no
  version check (`impact.md`, `app/contexts/guestbook/services/guestbook_entries.py:206`), so
  nothing in the store holds this rule yet (constitution, article VI). Only a concurrent test can
  tell the two apart (`spec/design/testing.md` § Choosing what proves what).
- **W-2: two marks from screens that are out of date.** The read-then-write happens if a mark is
  built as "read the state, store its opposite". A reads not done and stores done. B, who saw not
  done on the screen, reads done and stores not done. The database ends "not done", although both
  people chose done. `R-4` clause 3 (record the chosen state) removes the read.
- **W-3: an edit or a mark against a delete.** The read-then-write: the edit reads the task (it
  exists), the delete removes it, then the edit writes. What the database holds at that moment is
  no task. A write that creates on absence brings the task back. `R-8` clause 1 ("create no task")
  forbids it.
- **W-4: two adds in the same instant.** There is no read. Both tasks are stored with the same
  moment of adding, and only a tie-break makes the order total (`R-3` clause 3).
- **W-5: filling a new environment against a person adding.** The read-then-write: filling reads
  "the to-do list is empty", a person adds a task, then filling posts the example tasks. The
  database ends with the person's task plus the examples. No constraint stands behind the check.
  The guestbook's filling has the same exposure today. It is rare, because it needs a person to
  add a task in the seconds between that read and those posts, during a deploy to an environment
  whose to-do list is empty (`R-11` clause 1, `Q-10`).
- **W-6: two fillings of one environment.** Deploy and preview both run on one environment.
  Both read "empty" and both post, so the examples appear twice. This is rare, and the guestbook
  has the same exposure today.

### With no defined behaviour
- When a person presses "add" a second time before the first add is answered, does the second
  press add a second task, or is it held off until the first is answered?
- After an add fails, does the field keep what was typed? After an add succeeds, is the field
  emptied?
- What does the screen show while a write waits 30 s for its answer, and can the person act on
  other tasks meanwhile?
- Is there a largest number of tasks the list holds or shows? With no pages (`Q-9`), every task
  is read at once, and nothing bounds how many there are.
- After "the task no longer exists" (`R-8`), does the list drop that task at once or on the next
  reload?

## Impact analysis

- **Collisions with invariants:** none requires anything to bend. Each source was checked:
  - `spec/invariants.md` § Deliberate non-goals. Authentication: consistent, since anybody adds,
    marks, edits and deletes any task (`R-1` clause 2). CSRF: consistent, since there are no
    sessions. Moderation: consistent. A mobile version: consistent, since the new screen is not
    designed for a phone. A data retention policy: consistent, since a task lives until somebody
    deletes it (assumed: `A-2`). A second database engine: consistent. Paging and search, lifted for the
    guestbook alone as `BR-05`: consistent, since the to-do list has neither (`Q-9`).
    **Finding, not a collision:** the authentication and retention items are worded for entries
    ("anybody may add, amend and delete any entry"; "An entry lives until somebody deletes it"),
    so their wording no longer covers everything the system stores. Only the convergence round
    edits this file (its own § Deliberate non-goals), so this is reported and not fixed.
    Converged by COH-requirements-5: the authentication item now names any to-do task (`Q-9`),
    and, since the user approved this document with `A-2` standing, the retention item names
    tasks too (`design/delta/converge.md`).
  - `contracts/invariants/guestbook.md`. `D-01`: consistent. A done task stays one record in
    its place (`Q-4`, `R-3.4`). A design that moved done tasks into a second store would breach
    it, and `tests/fitness/test_data_invariants.py::test_no_table_is_shaped_like_an_archive`
    sweeps every table. `D-02`: consistent, since a task points at nothing and copies nothing.
    `D-03`: consistent, since nothing here asks for an identifier a person reads. `D-04`:
    consistent, since `R-2` holds a task's text to the same normalization, trim set and unit. As
    written, `D-04` names the guestbook's two text fields, so it does not by itself cover a task.
    Whether an invariant of the task's own domain carries it is the design stage's call.
  - Constitution. Article VI: no uniqueness rule exists here (duplicates are allowed, `R-1`
    clause 5), so no index is asked for. What has to hold under concurrency is `R-9` clause 2
    (race `W-1`). Article XI: no new personal-data field. The example tasks follow the corpus rule
    "unambiguously artificial" (`golden-set/README.md`). Article XIII: nothing outside the
    allowed stack.
- **Decisions that already settle this:** `spec/ADR/index.md`, read whole, records no ADR, and
  its `Supersedes` and `Aliases` columns are empty. The rulings that settle parts of this change
  live in normative documents, per `spec/design/conventions.md` § When a decision is an ADR:
  - `spec/design/conventions.md` § Backend makes `app/platform/schemas/text.py` "a fact about
    EVERY text field this API accepts". That settles how the 200 is counted (`R-2`). Consistent.
  - `spec/design/api.md` § Collection read parameters, decision of 2026-09-17: "Every bound in
    this document is in CODE POINTS". Consistent.
  - `spec/design/ui/system-states.md` § One column: a second screen "must add navigation here".
    Consistent: `R-5` is that navigation. § Out of scope ("Navigation. One screen, so there is
    nothing to switch between") stops being true, which is a design edit.
  - `spec/design/ui/system-states.md` § Interactions: the main address redirects to the
    guestbook, and "The browser stores nothing". Both consistent (`R-5` clause 3; `R-3` clause 5).
  - `spec/design/ui/system-states.md` § Tokens, decision of 2026-09-16: the 4.5:1 floor.
    Consistent (`R-4` clause 6).
  - `spec/design/ui/guestbook.md`, decision of 2026-09-17: no field stops at its bound. This is
    the guestbook screen's decision. `R-2` clause 5 asks the same observable of the new field.
    Consistent.
  - `spec/design/architecture.md` § What a new environment starts with, decision of 2026-09-05:
    filling goes through the application, never into production, never into a guest book that
    already has entries, and it treats "an environment nobody has written in yet" as one
    condition. `Q-10` → A fills each list on its own. The seeder gains a refusal per list beside
    "It will not seed a guest book that already has entries", which is a design edit to that
    section.
  - `spec/design/conventions.md` § Language: English. Consistent (`Q-7`).
  - `spec/design/data-model.md` § Identifiers, decision of 2026-08-30. Consistent.
- **Dependencies:**
  - Exist: the page frame, the shared text rule (`app/platform/schemas/text.py`), the
    environment filler, and the toast and error primitives (`impact.md` § What the code does).
  - Do not exist, and none blocks: navigation between screens, which `R-5` asks for. A
    checkbox or toggle primitive (`impact.md` § What is missing): conventions add a primitive
    with its first caller. A browser-side text rule outside the guestbook's own folder:
    `frontend/src/contexts/guestbook/lib/entryText.ts` sits inside the guestbook context, and
    `tests/fitness/test_context_boundaries.py::test_no_screen_reaches_into_another_contexts_folder`
    refuses a second context that reaches it. Where the rule goes depends on which context owns
    a task.
  - `spec/contexts/guestbook.md` § Deliberate non-goals (authentication, moderation, search
    relevance, CSRF): nothing here depends on any of them being built.
  - Inherited disagreements (`impact.md` § Where these disagree), none of which blocks the
    requirements. First, `spec/design/conventions.md` § Layers says a router translates in a
    `match` block and names the guestbook router as the worked example, while that router uses
    `try`/`except`, and it is the file a new resource is told to copy. Second,
    `spec/design/ui/system-states.md` lists an empty-state primitive that the code removed, and
    `R-3.6` needs an empty-list sentence.
  - `R-11` reaches `scripts/seed_golden_set.py` and the seed half of the corpus. `impact.md`
    recorded `tooling_touched` as absent, on the condition that `Q-8` has since met
    (`brainstorm.md` § Open).
- **Frozen rules** (`spec/contexts/guestbook.md`):
  - `BR-01`: consistent. `R-2` borrows its trim set, NFC and unit and departs from none of them.
    The 200 is a new bound, not an edit of 80 or 1000.
  - `BR-02`: written about an entry's two moments, so it does not apply as written. `R-6`
    clause 2 keeps the moment of adding fixed in the same spirit.
  - `BR-03`: consistent. `R-7` clause 2 and `R-8` clause 2 mirror it for tasks.
  - `BR-04`: consistent. `R-3` clause 3 asks for the same totality. The to-do list is read in
    one direction only.
  - `BR-05`: does not apply, since the to-do list has no search and no pieces.
  - `P-01`: "There are no intermediate states, no lifecycle" describes entries. If the design
    places tasks inside the guestbook context, that sentence stops describing the whole context.
  - No departure from any of them, so no ADR with `supersedes` is needed.
- **Tests that would fail:**
  - `tests/unit/test_guestbook_entry_model.py::test_this_schema_holds_exactly_one_table` asserts
    `set(Base.metadata.tables) == {"guestbook_entries"}`. It goes red on any stored task.
  - `tests/fitness/test_golden_set.py::test_every_corpus_file_is_named_by_the_locator` goes red
    until a task seed file is registered in `tests/_golden_set.py`. Once the file is registered
    in `SEED_FILES`, these go red:
    - `::test_every_entry_carries_the_keys_an_entry_has`, which demands the two guestbook keys;
    - `::test_every_entry_meant_to_pass_really_passes` and
      `::test_no_seed_entry_stands_near_a_published_limit`, which index `author` and `message`;
    - `::test_the_corpus_exercises_a_message_with_line_breaks`, which demands a line break in
      every sequence file. Under `Q-11` no task file may carry an inner line break, so that rule
      has to be scoped to guest book entries.

    `::test_the_corpus_exercises_characters_outside_ascii` stays green only if an example task
    carries a character above U+007F.
  - `tests/tooling/test_seed_golden_set.py::test_an_empty_environment_gets_the_whole_seed_corpus`
    derives its expectation from `SEED_FILES` and reads `author` from every item.
    `::test_a_guest_book_with_entries_is_left_alone` expects nothing posted to an environment
    whose guestbook holds entries, and **goes red, because `Q-10` chose option A**: tasks are now
    posted where the guestbook holds entries.
  - `e2e/ui/test_smoke.py::test_the_built_spa_boots_and_a_deep_link_resolves` and
    `::test_an_unknown_address_says_so` look up the link named exactly "Guestbook" and call it
    "the only navigation this application has". A navigation link with that same name would make
    the lookup ambiguous. Whether that happens depends on the name the design chooses.
    `::test_the_root_redirects_to_the_one_screen` stays green (`Q-5`), though its name stops
    being true.
  - `tests/fitness/test_golden_set.py::test_the_frontend_reads_no_corpus_file` names one
    frontend module as the only reader of `golden-set/fixtures/text-measurement.json`. It goes
    red if the to-do screen's own text-rule test reads that file from somewhere else.
  - `tests/fitness/test_context_boundaries.py::test_no_screen_reaches_into_another_contexts_folder`
    goes red if a to-do screen in its own context imports the guestbook's browser text rule.
  - `tests/fitness/test_length_constants.py` does not go red. It holds three bounds and their
    one browser copy, so a fourth bound and its copy would stand unheld unless the test is
    extended.
  - `tests/integration/test_migrations.py::test_the_models_and_the_migrations_describe_the_same_schema`
    stays green only if the new model and the new revision agree. The guestbook-specific tests
    in that file are unaffected.
  - `tests/fitness/test_context_declarations.py` and `tests/fitness/test_data_invariants.py`
    stop being vacuously true once there is a second context or table, and go red on an
    incomplete declaration.
  - `e2e/suite/features/guestbook.feature` (22 scenarios, `CR-2609-9b1e/R-1`…`R-7`) is
    unaffected, because nothing here changes the guestbook.
- **Other changes in flight:**
  - `CR-2609-8ef9` (draft, chore). Its request names `spec/design/testing.md` § What only CI can
    answer and `scripts/test.sh`. This change's design stage will edit `spec/design/testing.md`
    too (other sections) and reaches `scripts/seed_golden_set.py` through `R-11`. That is the
    same document but a different section, and different scripts.
  - `CR-2609-9b1e` is merged. Its requirements are cited by `guestbook.feature`, and nothing here
    renumbers or edits them.

## Non-Goals
- **Removing or changing the guestbook.** The user chose to keep it beside the list (`Q-1`), and
  every guestbook behaviour and suite stays as it is (`SC-5`).
- **A Polish screen or any translation.** The screen is English, like the rest (`Q-7`,
  `spec/design/conventions.md` § Language).
- **Search, pages, filters (for example "only open tasks") and a "clear all done" action.**
  Everything is on one list (`Q-9`). `BR-05` stays the guestbook's.
- **Due dates, priorities, assigned people, categories and more than one list.** It is one shared
  list of one-line tasks (`Q-9`).
- **Live updates.** Other people's changes appear when the list is reloaded (`Q-9`, `R-3`
  clause 5). Nothing pushes them to an open screen.
- **Accounts, sign-in, "my tasks", and recording who added or ticked a task.** This is the
  standing non-goal (`spec/invariants.md` § Deliberate non-goals): anybody adds, marks, edits and
  deletes any task.
- **Moderation.** The same standing non-goal: no reports, no hiding.
- **Warning a person that somebody else's change overwrote theirs.** "The later change wins"
  (`Q-9`), and nobody is told their change was replaced (`R-9`).
- **A bin, undo, or restoring a deleted task.** "Gone for good" (`Q-9`, `R-7` clause 2).
- **Moving done tasks to the bottom or into a separate section.** Ticking never moves a task
  (`Q-4`, `R-3` clause 4).
- **Reordering tasks by hand.** The order is the moment of adding, newest first (`Q-6`), and
  nothing else sets it.
- **A mobile design of the new screen.** This is the standing non-goal (`spec/invariants.md`
  § Deliberate non-goals, "A mobile version").
- **A retention policy for tasks.** A task lives until somebody deletes it, as an entry does
  under the standing non-goal. For tasks this was assumption `A-2` (§ Named assumptions),
  confirmed at this document's approval.
- **Detecting a duplicate caused by a retried add.** The same text twice is two tasks by
  decision (`Q-9`, `R-1` clause 5), so `E-20` leaves a duplicate for a person to delete.

## Bounds

| Quantity | Value | Where it comes from |
|---|---|---|
| Task text, maximum | 200 code points, after NFC normalization and trimming | `Q-9` ("up to 200 characters"). The unit is the one every text field is measured in (`spec/design/conventions.md` § Backend on `text.py`; `spec/design/api.md` § Collection read parameters) |
| Task text, minimum | 1 code point after trimming | `Q-9` ("An empty task, or one made only of spaces, is refused") |
| Trim set | the written 30-code-point set | `spec/contexts/guestbook.md` § `BR-01`, `app/platform/schemas/text.py` |
| Line break inside a task | refused; the set is U+000A, U+000B, U+000C, U+000D, U+0085, U+2028, U+2029 | `Q-11` for the refusal; the set is assumption `A-1` (§ Named assumptions) |
| Emoji boundary value | 200 × U+1F600 = 200 code points = 400 UTF-16 code units; 201 refused | `R-2.3`, from the `D-04` incident |
| Decomposed boundary value | 200 × (U+0065 U+0301) = 400 code points before NFC, 200 after | `R-2.4`, from `BR-01`'s normalization |
| Padding boundary value | 2 + 200 + 2 = 204 as typed, accepted; 205 spaces, refused as empty | `R-2.5`, from the `api.md` trim-order incident |
| Tasks shown per read | all of them, with no pages | `Q-9` |
| List size that proves "no pages" | 101 tasks | one more than 100, the guestbook's largest piece (`spec/design/api.md` § Collection read parameters), and more than its default of 20 |
| Example tasks, minimum | 3 | `Q-8` ("a few"), with the seed-half rule that a list is at least three items (`tests/fitness/test_golden_set.py::test_the_seed_half_shows_a_list_rather_than_an_entry`) |
| Example tasks done, minimum | 1 | `Q-12` |
| Example task, maximum length | under 150 code points (0.75 × 200) | the seed-half margin in `tests/fitness/test_golden_set.py::test_no_seed_entry_stands_near_a_published_limit` |
| Contrast of a done task's text | at least 4.5:1 against the surface behind it | `spec/design/ui/system-states.md` § Tokens (WCAG 2.1, 1.4.3) |
| "At the same moment" | both changes sent before either is answered | `R-9` |

The search phrase's bound is also 200 code points (`QUERY_MAX_LENGTH`). That is two rules
sharing a number, and a test that reads the phrase's constant to prove the task's bound proves
the wrong rule.

## Open questions
- **`D1`: answered.** `Q-10` → A, each list is filled on its own (`R-11` clause 1).
- **`D2`: answered.** `Q-11` → A, refuse it with its own message (`R-2` clause 6).
- **`D3`: answered.** `Q-12` → A, at least one example is done (`R-11` clause 6).
- **Double add while the first is in flight, what the field holds after an add, the screen while
  a write waits, the list after "no longer exists", and a largest number of tasks.** None of
  these blocks the requirements. They are for the design stage: the screen specification and the
  mock-up the user approves. A product rule the design needs from them goes back to the user,
  not into a design document.
- **The frame's words with two screens: the lockup name, the footer about "entries", the header
  fact, and where the not-found page leads.** These block nothing here. `brainstorm.md` § Open
  gives them to the mock-up, for the user to approve there. `R-5` clause 4 is the only
  constraint on them in this document.

## Named assumptions

*This stage's question budget is spent: `sdd-engine loop ask --raise` refused a thirteenth
question. What no answer decides is written here as an assumption, in the form "Assumed: …, say
so if not". No item below is a human decision yet. The user confirms or overrules each one
at the approval of this document, which ends the stage.*

- **`A-1`: which characters are a line break (`R-2` clause 6, `R-6` clause 4).** Assumed: a line
  break is any of U+000A (line feed), U+000B (line tabulation), U+000C (form feed), U+000D
  (carriage return), U+0085 (next line), U+2028 (line separator) and U+2029 (paragraph
  separator): one written set that the screen and the service both read, so a pasted text is
  refused the same way on both sides. Say so if not. The other reading is U+000A and U+000D
  alone, which keeps the other five as content inside a task, the way a guestbook signature keeps
  U+0085 (`text-measurement.json` case `next_line_inside_is_kept`). The set is written down
  because the two languages' own line-break defaults disagree, among others about U+000B, U+000C
  and U+0085 (COH-requirements-4 in `review/coherence.md`), and `R-2` clause 5 fails if each side
  takes its own. **Status:** assumed, awaiting the user.
- **`A-2`: a task lives until somebody deletes it (§ Non-Goals).** Assumed: nothing removes a
  task except a person deleting it, with no expiry and no retention policy, as for a guestbook
  entry (`spec/invariants.md` § Deliberate non-goals, "A data retention policy"). Say so if not.
  `Q-9` settled that anybody may delete any task and that a deleted task is gone for good. It did
  not settle whether a task can go without anybody deleting it. **Status:** confirmed at this
  document's approval; `spec/invariants.md` § Deliberate non-goals names tasks since.
- **`A-3`: where the inside of a task's text ends (`R-2` clauses 4 and 6, `R-6` clause 4).**
  Assumed: the line-break rule reads the text as `R-2` clause 1 has trimmed it, so a line break
  the trim leaves in the text is refused wherever it sits. A character that shows nothing but is
  not in the trim set, such as U+200B (zero width space) or U+180E (Mongolian vowel separator), is
  content: "Buy bread", a line feed, then U+200B is refused, because clause 1 removes neither the
  U+200B nor the line feed before it. Say so if not. The other reading is "between the first and
  last visible character", the phrase the first draft used as a gloss on "inside": it lets that
  line feed through and stores it, and it needs a written definition of "visible" that the screen
  and the service both read, which no document has. The trim reading is the one `scenarios.md`
  S-9 already holds ("the line break rule runs before trimming" fails it) and the one
  `spec/contexts/guestbook.md` § `BR-01` uses for entries ("Whitespace *inside* a value is
  content and is kept; only the ends go") (COH-requirements-8 in `review/coherence.md`).
  **Status:** assumed, awaiting the user.
- **`A-4`: what "the guestbook suites run unchanged" promises (`SC-5`).** Assumed: the 22
  scenarios of `e2e/suite/features/guestbook.feature` run unedited, and the UI smoke's guestbook
  tests keep asserting what they assert today, while a locator in `e2e/ui/test_smoke.py` that
  names the lockup or a navigation link may follow the names the user approves in the mock-up.
  Say so if not. The other reading keeps the smoke unedited too, and so decides in advance a copy
  question § Open questions gives to the mock-up: the lockup stays "Guestbook", and no navigation
  link takes that exact name. The smoke finds the lockup link by that exact name
  (`e2e/ui/test_smoke.py`:40, :93, :373; `frontend/src/components/shell/PageFrame.tsx`:24), so
  under that reading a renamed lockup, or a second link named "Guestbook", turns it red
  (COH-requirements-9 in `review/coherence.md`). **Status:** assumed, awaiting the user.

## Self-check

1. [Completeness] [§ R-1] Does the moment of adding need to be visible to anybody, or does it
   serve only the order? If a person has to see it, the screen needs a requirement and the
   mock-up a place for it. As written, it serves `R-3` alone.
2. [Coherence] [§ R-1] Is "a new task is recorded not done, whatever the request claims" a rule
   the user stated, or one inferred from "a to-do list"? If a reviewer calls it invented, it goes
   to the user. The rejected reading is that a client can add a task already done.
3. [Clarity] [§ R-2] Can a second implementer find "the written 30-code-point set" without
   reading guestbook code? It points at `BR-01` and `text.py`. If tasks land in another context,
   the set has to be shared rather than copied, or two copies drift.
4. [Completeness] [§ R-2] What happens to a line break inside a text? It is refused with a reason
   of its own (`Q-11`, `R-2` clause 6, `R-2.7`). Which characters are a line break is assumption
   `A-1`, for the user to confirm at this document's approval.
5. [Measurability] [§ R-2] Can "the screen takes every character" in `R-2.3` be observed in a
   suite that owns citations? It can over the rule the screen applies, in vitest. The typing and
   pasting half only the UI smoke sees, and the smoke owns no citation. If design finds no vitest
   seam, that half loses its automated proof.
6. [Compliance] [§ R-2] Does `tests/fitness/test_length_constants.py` hold the new 200 and its
   browser copy? No, it names three bounds. Unless it is extended, the new copy stands unheld, as
   the signature's unit did before `D-04`.
7. [Clarity] [§ R-3] Does "newest first" still mean "by moment of adding" after an edit? Yes, by
   clause 4. A reader who takes "newest" as "most recently changed" makes edited tasks jump, and
   `R-3.4` pins the intended reading.
8. [Completeness] [§ R-3] Is there a number of tasks beyond which "every task on one list" stops
   being acceptable? None is stated. If the design needs a ceiling, that is a product question for
   the user, not a design choice.
9. [Measurability] [§ R-3] Can `R-3.2` be observed without control of the clock? Only if a test
   can store two tasks with an equal moment of adding. Otherwise the tie-break passes by luck.
10. [Clarity] [§ R-4] Is "mark done" setting a chosen state, or flipping the stored one? It is
    written as setting (clause 3). A flip built by the design fails `R-4.3` and `R-9.3` under
    screens that are out of date.
11. [Coherence] [§ R-4] Does clause 6 restate a rule that already has a home
    (`spec/design/ui/system-states.md` § Tokens)? Yes, on purpose, as the observable form of the
    defect this screen invites. If the frame's floor moves, this clause follows it rather than
    competing with it.
12. [Measurability] [§ R-4] Can "shown differently" be judged without a person? Only through what
    a test can read, such as the done state as the page exposes it. The visual form belongs to the
    mock-up.
13. [Completeness] [§ R-5] Where does the not-found page lead when there are two screens? That is
    not stated. If it leads only to the guestbook, a visitor who wanted the to-do list is one step
    further away, which `R-5` does not forbid.
14. [Compliance] [§ R-5] Would a navigation link named exactly "Guestbook" break the exact lookups
    in `e2e/ui/test_smoke.py`? Yes: two links with one name. The design either names the link
    differently, or the smoke's locator changes in the same change.
15. [Coherence] [§ R-6] Does "leave the task's state as it is stored at that moment" contradict
    "the later change wins"? Only if "later wins" is read as applying to the whole task. It is
    read per aspect (text, state). If the user meant the whole task, `R-9` clause 2 is the
    sentence to take back to them.
16. [Completeness] [§ R-7] Does the confirmation have to name the task? That is not stated. The
    guestbook's dialog does name the entry (`spec/design/ui/guestbook.md` § The delete dialog), so
    the mock-up will likely copy it. It is not a requirement here.
17. [Clarity] [§ R-8] Does "tell the person the task no longer exists" require the list to drop
    that task at once? No, and it is open. If the design leaves it on screen, a second attempt
    meets the same message.
18. [Clarity] [§ R-9] Is "the change applied later" well defined when two requests overlap? It
    means the one whose write the store applied last. If a reviewer needs arrival order instead, a
    mechanism beyond the store's own ordering is needed.
19. [Measurability] [§ R-9] Can `R-9.1` be proved by a sequential test? No. An edit followed by a
    mark passes over a whole-task write-back too. Only concurrent requests tell the two apart
    (constitution, article VI).
20. [Completeness] [§ R-10] Is the typed text still in the field after a failed add? That is open.
    If it is not, the person retypes it, and nothing here says whether that is acceptable.
21. [Completeness] [§ R-11] What happens in an environment that existed before this change and
    whose to-do list is empty? That is `D1`, answered by `Q-10` → A (`R-11` clause 1). Option A
    turns `tests/tooling/test_seed_golden_set.py::test_a_guest_book_with_entries_is_left_alone`
    red.
22. [Compliance] [§ R-11] Is `**Verified-by:** manual` honest here, or does a citation-owning
    suite exist that proves it? `tests/tooling/` and `tests/fitness/` own no citation, and the black box runs
    with `--no-seed`. If design-testing finds a surface, the marker has to be removed, not left
    standing beside a test.
23. [Coherence] [Gap] Do the non-goals in `spec/invariants.md`, worded for entries, bind the to-do
    list? By intent yes, by wording no. Only the convergence round edits that file, so the finding
    goes there. It went there as COH-requirements-5: authentication now covers tasks, and
    retention covers them too since the user approved this document with `A-2` standing.
24. [Compliance] [Gap] Which bounded context owns a task? That is not a requirement: it is
    design-domain's call. If tasks live inside the guestbook context, the closing sentence of
    `P-01` ("An entry either exists or it does not") stops describing that context.

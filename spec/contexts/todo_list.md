---
context: todo_list
classification: supporting
owns: [todo_tasks]
neighbours: [guestbook:peer:shared-kernel]
processes: [P-02]
screens: [spec/design/ui/todo-list.md]
features: [e2e/suite/features/todo_list.feature]
---

# To-do list

One list of things to do, shared by everybody who opens the application. Anybody adds a task
of one line, ticks it done and back, corrects its text and deletes it; everybody reads the same
list, in the same order, with the same done marks. The list belongs to the application and not
to a browser: what one person changes, the next person to open the list sees.

This context owns the task and every rule about it. It does not own the way between screens,
how a new environment is filled, or how a screen shows a failure (§ Neighbours, what no context
owns). The shapes on the wire are in [`spec/design/api.md`](../design/api.md); what is stored
is in [`spec/design/data-model.md`](../design/data-model.md). This document is the rules.

**The header claims a screen once its document exists, and the black-box file at the end of
design, before the file exists.** `screens` and `features` name files. No author who writes
one of those files writes this document, so the design stage's convergence round writes both
claims. The screen's document is written in design, so it is claimed in the same stage. The
black-box file is written only in implementation, where no author writes `spec/contexts/`. So
it is listed at the end of design, as the user decided in `CR-2609-823a` (`Q-19`): "List it
now, at the end of design". The header is read, not admired, so that early claim is a named
red and not a silent one: `test_every_screen_and_feature_a_context_names_is_on_disk` was red from
the design close, accepted by name at that boundary (`CR-2609-823a`, `Q-24`), and went green when
the first implementation wave wrote the file.

## Strategic classification

**Supporting.** The list is specific to this application — one list every visitor shares,
with no accounts, under the same text rule and the same frame as the guestbook — so it is not
something to buy: a vendor's to-do product brings the accounts this system refuses
([`spec/invariants.md`](../invariants.md) § Deliberate non-goals) and a second place to go. It
is not what the application competes on either: its rules are deliberately few (one line, one
state, one order, no dates, priorities, owners or second list), and it earns the modelling of
one stored thing and the handful of rules below, not the apparatus a core domain gets
([`spec/design/architecture.md`](../design/architecture.md) § When a context deserves tactical
modelling).

## Language

| Term | What it means here |
|---|---|
| **To-do list** | The one list of tasks. There is exactly one, and everybody shares it. |
| **Task** | One line of text somebody put on the to-do list. It has a text, a state and a moment of adding, and nothing else: no author, no due date, no owner. |
| **Done / not done** | The one state a task has, switched both ways by a person. A new task is not done. |
| **Marking** | Setting a task done or not done. It records the state the person chose, never the opposite of what was stored. |
| **Moment of adding** | When the system stored the task. It orders the list and never changes. |
| **Line break** | Any of seven code points: U+000A, U+000B, U+000C, U+000D, U+0085, U+2028 and U+2029. A task holds none inside its text (`BR-07`). In the guestbook the same characters are content — a message keeps its line breaks — and that difference is one reason these are two contexts. |

A task is not an entry. It has no signature, no moment of amendment and no "edited" fact, and
an entry has no state. Neither word is used for the other thing.

## Neighbours

| Neighbour | Role | Pattern | What crosses, and what happens when they change it |
|---|---|---|---|
| **Guestbook** | `peer` | `shared-kernel` | **One rule crosses, and nothing else: how a text is trimmed and measured** — normalized to Unicode NFC, trimmed at both ends of the one written set of thirty code points, then counted in code points, in that order. Its words are written once, in [`guestbook.md`](guestbook.md) § `BR-01`, and this document references them and restates none of them. **The guestbook keeps** entries, signatures, messages, the edited fact, its bounds of 80 and 1000, its order in both directions, its search and its pieces. **This context keeps** tasks, done and not done, the bound of 200, the one-line rule and its set of line breaks, and its own order. No record on one side refers to a record on the other, neither reads the other's list, and neither screen shows the other's data. **When the text rule changes, both contexts change with it**, because both are held to it — so it changes only with both sets of rules in view. When the guestbook changes anything else, nothing here moves. **If the guestbook is removed, the text rule moves into this document first**, because this context is then its only holder; a citation of `BR-01` from here that points nowhere is what the specification gates catch if that is forgotten. |

**Why a shared kernel rather than an upstream.** The guestbook supplies nothing this context
consumes at run time, and nothing it could change on its own without changing this context too.
The text rule is a fact about every text this system accepts rather than a fact about entries —
[`spec/design/api.md`](../design/api.md) § Collection read parameters says so for every bound
in the contract — and its words sit in the guestbook's document only because that was the one
context when they were written. Both sides are held to it; neither translates it.

**What no context owns, and this one therefore does not either:**

- **The way between the screens.** Reaching the to-do list from the guestbook and back, which
  screen the main address opens, and what the page for an unknown address says belong to the
  frame every screen renders inside ([`spec/design/ui/system-states.md`](../design/ui/system-states.md)).
- **How a new environment is filled.** Example tasks, when they are added and when they are
  not, are the environment's starting state
  ([`spec/design/architecture.md`](../design/architecture.md) § What a new environment starts
  with). They are bound by the rules below like any other task.
- **How a screen shows a failure.** That a change the application did not store is never shown
  as made, and that a list which could not be read is not an empty list, is how the screen
  behaves; its specification says how each looks.

## `P-02` — keeping the to-do list

One flow in five steps, each of which works on its own:

1. **Adding.** A person types one line and adds it. The system stores the task, not done, and
   records its moment of adding. It appears first in the list without the person reloading.
2. **Reading.** Anybody sees every task on one list, newest first, done and not done alike, as
   the tasks are stored at the moment the list is read. Other people's changes appear on the
   next reading; nothing pushes them to an open screen. A list with no task on it is empty, not
   broken, and says what to do.
3. **Marking.** A person ticks a task done, or ticks it back to not done. The task stays where it
   is.
4. **Correcting.** A person changes a task's text. The state and the place stay as they are.
5. **Deleting.** A person asks to delete a task and is asked once to confirm. On confirmation the
   task is gone for good; without it, nothing changes.

The one state a task has is switched freely in both directions. There is no other state, no
order of states to police, and nothing a task has to pass through.

## Business rules

### `BR-06` — a task needs text, and no more than 200 code points of it

A task's text is held to the text rule this context shares with the guestbook (§ Neighbours):
normalized, trimmed at both ends, and only then measured. A text that is empty once trimmed is
refused, nothing is stored, and the person is told that a task needs text. A text longer than
200 code points once normalized and trimmed is refused the same way, and the person is told it
is too long.

The order is what makes the bound honest. Two hundred and five spaces are an empty text, not a
text that is too long; two hundred code points with spaces around them are accepted and stored
without the spaces. Whitespace inside the text is content and is kept exactly as typed.

**The 200 is this context's own number.** It shares its unit with the guestbook's bounds and
nothing else. The guestbook's search phrase is also bounded at 200: that is two rules sharing a
number, and moving one moves nothing on the other side.

**The screen accepts exactly the texts the application accepts.** It never stops taking a text
the application would store — two hundred emoji are two hundred code points however the browser
counts them — and it never lets through a text the application would refuse.

### `BR-07` — a task is one line

A text that, once trimmed, still carries a line break (§ Language) is refused, nothing is
stored, and the person is told that a task is one line — a reason of its own, never "empty" or
"too long", so the person knows what to change.

**A text that is also too long is refused as more than one line.** A text over 200 code points
with a line break inside it breaks `BR-06` and this rule at once, and the person is told one
reason for it — that a task is one line — on the screen and by the application alike. A pasted
line break such as U+2028 is often invisible in a one-line field, while a text's length is there
to be seen, so the reason the person cannot find for themselves is the one they are given;
`BR-06`'s "too long" is the reason for a text of one line.

The rule reads the text after the trim. Every one of the seven characters is also in the trim
set, so a line break at either end is removed like a space and is not refused; only a line break
left inside the text is. A character that shows nothing but is not in the trim set, such as a
zero width space, is content — so a line break beside it is inside the text.

**The seven are one written set that the screen and the application both read**, never each
language's own idea of a line break: the two languages this system is built in disagree about
some of them, and a pasted text would then be refused on one side and stored on the other.

### `BR-08` — a task is born not done, and keeps its moment of adding

Whatever a request to add a task claims, the new task is not done. A list does not start with
finished work nobody did. Its moment of adding is recorded when it is stored and never changes
afterwards — not by marking, not by correcting. Example tasks in a new environment follow this
rule too: one that is to be shown done is added not done and then marked.

### `BR-09` — marking records the state the person chose

Marking sets a task done or not done; it does not flip whatever is stored. Marking done a task
that is already done leaves it done, and marking not done a task that is already not done leaves
it not done. That is what keeps two people whose screens are out of date from undoing each
other: both chose done, and the task ends done.

Marking never changes the text. Every task in the list shows whether it is done, a done task
looks different from a not-done one, and a done task's text stays as readable as any other text
on the screen — the floor it clears is the screen specification's.

### `BR-10` — the text and the state are two things, changed separately

Correcting a task changes its text and nothing else: never its state, never its moment of
adding. A done task can be corrected exactly as a not-done one can.

**A correction is held to `BR-06` and `BR-07` exactly as an addition is.** A corrected text
either of them refuses changes nothing — the task keeps the text it had — and the person is told
why, with the reason an addition of that text would get.

When two changes to one task meet — both sent before either is answered — **the later change to
the same thing wins, and a change to one thing never undoes the other**. Two corrections: the
text from the one applied later. Two markings: the state chosen in the one applied later. A
correction and a marking: both are kept, whichever was applied first. Nobody is told their
change was replaced (§ Deliberate non-goals).

This has to hold under concurrency and not only in sequence. A correction that writes back the
whole task it read would restore the state it read and silently undo a marking made in between —
which passes every test that sends one change after another. No check made before the write can
hold it; the data model names the mechanism that does
([`spec/design/data-model.md`](../design/data-model.md)).

### `BR-11` — the list has one order, and a task keeps its place

Every task is on one list — done and not done alike, with no pages and no filter — ordered by
moment of adding, newest first. Two tasks with the same moment of adding come back in the same
relative order every time the list is read, so **the order is total**; without that, two people
could read two different lists from the same stored tasks.

Marking and correcting never move a task. "Newest" means the moment of adding, never the moment
of the last change: a list reordered by its last change makes a task jump every time somebody
ticks it. The list is read in this one direction only.

### `BR-12` — the same text twice is two tasks

Adding a text identical to a task already on the list stores a second, separate task, and each
is marked, corrected and deleted on its own. There is deliberately no uniqueness rule here, so
nothing is asked of the store to hold one.

The consequence is accepted rather than overlooked: an add whose answer was lost on the way back,
and which a person then repeats, leaves two tasks, and a person deletes the one they did not
mean. Nothing detects it.

### `BR-13` — deletion is permanent, and a task that is gone stays gone

A deleted task stops existing: no bin, no undo, no recovery. Every other task is left as it was.
Deleting somebody else's task is possible, because without accounts there is no such thing as
"my task".

**A change aimed at a task that no longer exists changes nothing, creates nothing, and tells the
person the task no longer exists** — a marking, a correction and a second deletion alike. A write
that created the task again on finding it absent would bring back what somebody deleted, and
reporting success for a deletion that was not performed is what makes a person believe they
deleted twice.

**A correction whose text is refused is told about its text first.** When a corrected text that
`BR-06` or `BR-07` refuses is aimed at a task that no longer exists, the person is told the
text's reason — on the screen and by the application alike, because the screen refuses such a
text before anything is sent and cannot know the task is gone. Only a change that could
otherwise be made learns that its task no longer exists.

## Deliberate non-goals

Named, so that an absence does not read as an oversight. The system-wide ones — no accounts, no
moderation, no retention policy, no mobile design — are in
[`spec/invariants.md`](../invariants.md) § Deliberate non-goals and are not restated here.

- **More than one list, and anything on a task but its text and its state.** No due dates,
  priorities, assigned people, categories or notes.
- **Search, pages, filters and "clear all done".** Everything is on one list.
- **Reordering.** Neither by hand nor by state: a done task is not moved to the bottom or into a
  section of its own.
- **Live updates.** Other people's changes appear when the list is read again.
- **Telling a person that somebody else's change replaced theirs.** The later change wins
  (`BR-10`), silently.
- **Recording who added, marked or corrected a task.** There is nobody to record.
- **Detecting a duplicate.** The same text twice is two tasks (`BR-12`).
- **Undo and restore.** A deleted task is gone (`BR-13`).

## Open questions

- **Is there a largest number of tasks the list holds?** None is set, and with no pages every
  task is read at once. A ceiling is a product decision for a person to take, not one a design
  document may introduce.

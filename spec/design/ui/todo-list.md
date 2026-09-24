---
screen: todo-list
route: /todo-list
info_ref: S-02
requirements: [CR-2609-823a/R-1, CR-2609-823a/R-2, CR-2609-823a/R-3, CR-2609-823a/R-4, CR-2609-823a/R-5, CR-2609-823a/R-6, CR-2609-823a/R-7, CR-2609-823a/R-8, CR-2609-823a/R-9, CR-2609-823a/R-10]
mockup: spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/ui/index.html
---

# To-do list

The screen of the one shared to-do list. Anybody who opens it adds a task of one line, ticks it
done and back, corrects its text and deletes it, and reads the same list, newest first, as
everybody else — with no sign-in, because there is no identity here
([`../../contexts/todo_list.md`](../../contexts/todo_list.md) § `P-02`).

The screen renders inside the page frame ([`system-states.md`](system-states.md)). The frame owns
the lockup, the navigation between the screens, the layout of the header and the not-found page;
this document owns what the to-do list puts into that frame. The mock-up in the front matter was
drafted by the process and approved as drafted by the person who asked for the change; it holds
the pixels, and this document is the specification ([`README.md`](README.md)).

A requirement written `R-n` below is `CR-2609-823a/R-n`.

## Regions

Top to bottom, inside the page frame:

1. **Header** — the frame's lockup and navigation, with "To-do list" marked as the screen on
   show, and on the right the number of tasks (R-5, R-3).
2. **Title and introductory sentence** — "Things to do", and one sentence on what the list is
   for and what using it costs (R-1).
3. **The add field** — one line and "Add task", in a white card (R-1, R-2).
4. **The list** — directly under the add field: every task, newest first, done and not done
   alike. In its place while it loads, rows in outline; when there is no task, the empty
   sentence; when it could not be read, the failure sentence and the error card (R-3, R-4,
   R-10).
5. **Footer** — one sentence about who sees this.
6. **The delete question** — above the screen, only while a deletion is being asked (R-7).
7. **Notices** — the frame's toasts, bottom right: what went through, and what did not (R-8,
   R-10).

## Components and their states

### The task count in the header

| State | What the user sees |
|---|---|
| default | `6 tasks`, `1 task` — how many tasks the list holds, as last read |
| empty | `0 tasks` |
| loading | no number at all: none is shown before the list has been read |
| error | no number at all: a list that could not be read has no count |

States omitted: hover, focus, active, disabled — it is a fact in text, not a control.

### The add field (R-1, R-2)

| State | What the user sees |
|---|---|
| default | a white card holding one borderless field, with the placeholder "What needs doing?", and "Add task" on its right. The field has no visible label and is named "New task" for assistive technology. It takes every character typed or pasted: nothing stops input at a length, and there is no character counter |
| focus | the screen's focus ring on the field; nothing moves |
| hover | "Add task", while it is open, lightens slightly; the field does not change |
| disabled | "Add task" is closed while the field holds no text, or holds a text the screen's rule refuses. Why: once the field has been left or Enter pressed, the rule's sentence stands under the field (`error`); before that, the empty field and its placeholder say what it is waiting for. Field and button are both locked while an add travels, and "Adding…" says why (`loading`) |
| error | the sentence for the one reason the text is refused, under the field, in the danger colour, announced as an alert, with the field marked invalid. Nothing is sent and the list does not change. It appears after the field is left or on Enter, never while typing, and goes as soon as the text passes |
| loading | "Adding…" on the button; the field and the button locked, the typed text still in the field; no row appears until the answer |

States omitted: active — no pressed look of its own: a press shows as the state it starts,
`loading` or `error`; empty — the field's emptiness is its `default` state, and the empty list
is the list's own state, below.

**The screen's rule is the service's rule, applied before sending** (`BR-06`, `BR-07`). The text
is normalized and trimmed exactly as the service will do it, then judged, in this order: empty,
then more than one line, then longer than 200 code points — so a text that is both too long and
more than one line gets the one-line sentence. The screen accepts exactly the texts the service
accepts: two hundred emoji are taken whole and "Add task" opens, two hundred and one are refused
as too long. A line feed or a carriage return never reaches the field, because a one-line field
drops them; the other five line breaks can be pasted, often invisibly, and are refused with the
one-line sentence.

### The list (R-3, R-4, R-10)

| State | What the user sees |
|---|---|
| loading | four rows in outline inside the list's card, with the height reserved and no spinner; read aloud as "Loading tasks". The add field is usable meanwhile |
| empty | "No tasks yet. Add the first one above." in a dashed frame where the list would be. Nothing reads as an error, and the header says `0 tasks` |
| default | every stored task in one white card, one row per task, the rows parted by hairlines, newest first, done and not done alike. Nothing to press to see more, however many tasks there are: the footer follows the last task. A list whose every task is done is this state, not `empty` |
| error | "The tasks could not be loaded." above the shared error card ([`system-states.md`](system-states.md) § Components and their states), whose title says what went wrong — "Could not reach the service" when nothing answered — with the detail it was given and "Try again". The empty sentence is not shown, the header shows no count, and the add field stays usable |

States omitted: hover, focus, active, disabled — the list is not a control; the controls are in
its rows, below.

**The list shows the tasks in the order they arrive and sorts nothing** (`BR-11`). A tick and a
correction never move a task.

### A task's row (R-4, R-6, R-7, R-8, R-9, R-10)

| State | What the user sees |
|---|---|
| default | an empty box, the task's text beside it, and the quiet text buttons "Edit" and "Delete" on the right, always visible. The text is the box's label, so pressing the text ticks the box too. A long text wraps inside the row, and an unbroken run breaks anywhere rather than widening the page |
| done | the box filled with the accent colour and ticked; the text struck through in the muted text colour and exactly as readable as any other text; the row stays where it was |
| hover | over the box and its text the pointer says they can be pressed; "Edit" turns the accent colour and "Delete" the danger colour; a locked control does not change |
| focus | the screen's focus ring around the box (the checkbox itself is not drawn), and around "Edit" and "Delete" |
| loading | a tick travelling: the box locked and still showing the state that is stored, with "Saving…" beside it. The row's "Edit" and "Delete" and every other row stay usable |
| editing | the text replaced, in place, by a bordered field holding the stored text, with the focus in it, and "Save" and "Cancel" under it; "Edit" reads "Editing". The box stays usable; "Delete" stays usable. At most one row is ever editing, and the list does not move |
| saving | "Saving…" on "Save"; the edit field, "Save" and "Cancel" locked; "Edit" locked on every row until the answer |
| deleting | behind the open question: "Deleting…" in place of "Delete", and "Edit" locked |
| disabled | "Edit" is closed on the row being edited, where it reads "Editing" because the editor is already open, and on every row while a correction travels, where the "Saving…" on the row being saved says why. "Delete" is closed only while its own deletion travels, and reads "Deleting…". The box is closed only while its own tick travels, with "Saving…" beside it |
| error | a correction the screen's rule refuses: the sentence under the edit field, announced as an alert, the field marked invalid, and "Save" closed until the text passes; "Cancel" brings back the stored text. A change that did not go through leaves the row showing what is stored — the box as it was, the text as it was — and a notice says why; a correction that did not go through keeps the editor open with what was typed, so it can be sent again or cancelled |

States omitted: active — no pressed look of its own: a press shows as the state it starts;
empty — a row exists only for a stored task, and a stored task always has text (`BR-06`).

**A task shows done in three ways at once** — the tick, the strike-through and the checked state
assistive technology reads — so colour is never the only carrier (`BR-09`). The done text is
`--color-muted`, which measures 7.09:1 on the card; it is never greyed with `--color-disabled` or
with opacity, which is the defect recorded in [`system-states.md`](system-states.md) § Tokens.

**Editing happens in the row, one row at a time, and the words stay where they were read** —
the guestbook card's editing ([`guestbook.md`](guestbook.md) § The entry card), with the same
lock: while a correction travels, no editor opens anywhere, so the answer can only close the
editor that sent it. Opening "Edit" on another row closes the open editor, and what was typed
there is dropped. Ticking the box of a row being edited leaves the editor open with what was
typed. Escape does nothing in the editor: a stray key must not lose an edit. A done task is
corrected exactly as a not-done one, and its box stays ticked throughout (`BR-10`).

### The delete question (R-7, R-8)

| State | What the user sees |
|---|---|
| default | over the dimmed screen: "Delete this task?", the task's text quoted, "This cannot be undone.", then "Cancel", which has the focus, and "Delete task". The task is still on the list behind it |
| hover | "Cancel" takes the medium surface and ink text; "Delete task" lightens slightly |
| focus | the focus ring; the focus starts on "Cancel", and Tab stays inside the question in both directions |
| active | the shared buttons' own pressed look: each shrinks slightly while pressed |
| loading | "Deleting…" on "Delete task"; both buttons locked; Escape and a press on the backdrop do nothing; the focus rests on the question itself |
| disabled | both buttons, only while a deletion travels, and "Deleting…" says why |

States omitted: empty — the question opens only for a task on the list, and quotes it; error — a
deletion that did not go through closes the question and is told by a notice (§ Interactions).

**The question quotes the task it is about**, and the focus starts on "Cancel", so an Enter
pressed out of habit deletes nothing — the guestbook's delete dialog, and its focus rules, as
they are ([`guestbook.md`](guestbook.md) § The delete dialog).

### Notices (R-8, R-10)

| State | What the user sees |
|---|---|
| success | a dark notice at the bottom right, with a tick: "Task added.", "Task updated." or "Task deleted."; it goes by itself after a few seconds. A tick gets no notice: the box is its own confirmation |
| error | a dark notice with the error glyph, saying what was not done (§ Copy); it stays until it is dismissed with its "×". The screen under it is unchanged, so the lasting fact is on the screen and not only in the notice |
| hover | the "×" brightens |
| focus | the focus ring around the "×" |

States omitted: active, disabled, loading, empty — a notice exists only while it has something
to say, carries nothing to wait for, and its one button is always usable and has no pressed look
of its own.

## Copy

English, like the rest of this repository ([`../conventions.md`](../conventions.md) § Language).

| Key | Copy |
|---|---|
| screen title | `Things to do` |
| introductory sentence | `No account, no sign-in, one list for everybody. Add what needs doing and tick it off when it is done. Anyone can edit or delete any task.` |
| task count | `0 tasks` · `1 task` · `6 tasks` |
| add field placeholder | `What needs doing?` |
| add button | `Add task` |
| add button in flight | `Adding…` |
| empty list | `No tasks yet. Add the first one above.` |
| list failed to load | `The tasks could not be loaded.` — above the shared error card, whose copy is [`system-states.md`](system-states.md) § Copy |
| row actions | `Edit` · `Delete` |
| row being edited | `Editing` |
| editor | `Save` · `Saving…` · `Cancel` |
| tick in flight | `Saving…` |
| deletion in flight | `Deleting…` — on the row and on the question |
| question — title | `Delete this task?` |
| question — quotation | the task's text, as stored |
| question — consequence | `This cannot be undone.` |
| question — buttons | `Cancel` · `Delete task` · `Deleting…` |
| notice after adding | `Task added.` |
| notice after correcting | `Task updated.` |
| notice after deleting | `Task deleted.` |
| an add not stored, nothing answered | `The task was not added: the service could not be reached.` |
| a tick, correction or deletion not stored, nothing answered | `The change was not made: the service could not be reached.` |
| an add not stored, the service answered with an error of no sentence of its own | `The task was not added: the service answered with an error.` |
| a tick, correction or deletion not stored, the service answered with an error of no sentence of its own | `The change was not made: the service answered with an error.` |
| footer | `Tasks are public and editable by anyone with this link.` |

The sentence says "the service could not be reached" only when no answer came at all, and "the
service answered with an error" when an answer came that carries no sentence of its own — no
refusal `message` (§ Data), a server error for instance. An answer that does carry one shows that
sentence instead (§ The refusals this screen can show).

### The refusals this screen can show

The words live beside the endpoint that produces them, in
[`../api.md`](../api.md) § The to-do list's refusals, and this screen shows them as they are
written there, from the refusal's `message`:

| Code | Where it is shown |
|---|---|
| `todo_task_text_empty` | under the add field or the edit field |
| `todo_task_text_multiline` | under the add field or the edit field |
| `todo_task_text_too_long` | under the add field or the edit field |
| `todo_task_not_found` | in an error notice, after a tick, a correction or a deletion; nothing else on the screen changes |

**The screen's own verdict before sending uses the same three text sentences, word for word**, so
one text is refused on the screen and by the service for the same reason in the same words
(`BR-06`). If the service refuses a text the screen let through, its sentence stands in the same
place under the field and the text stays as typed.

Never shown, because this screen never provokes them: `todo_task_empty_patch` (every change it
sends carries a text or a done mark) and the standard validation refusal (it never sends a
malformed request).

### Accessibility labels

Text nobody sees and assistive technology reads. Here for the same reason as the rest: a test
and the smoke find elements by it.

| Text | Where |
|---|---|
| `New task` | the add field |
| `Edit task` | the edit field |
| `Tasks` | the list |
| `Loading tasks` | the list while it loads, a status region |
| the task's text | each box: the visible text is its label; while the row is editing, the stored text names it |
| `Edit “<text>”` · `Delete “<text>”` | each row's buttons: the visible word followed by that task's text in quotation marks |
| `Dismiss notification` | the "×" on a notice (the shared toast) |

## Data

Bound to the live contract, [`../api.md`](../api.md). One hook reads and writes the resource; no
screen element calls the client itself.

| Element | Source | Fields |
|---|---|---|
| the task count | `GET /api/todo-tasks` through `useTodoTasks()` | `total` |
| the rows, in the order they arrive | `GET /api/todo-tasks` through `useTodoTasks()` | `items[].id`, `items[].text`, `items[].done` |
| the empty state | `GET /api/todo-tasks` through `useTodoTasks()` | `items` empty, `total` 0 |
| adding | `POST /api/todo-tasks` through the add mutation of `useTodoTasks.ts` | sends `text` as the shared rule leaves it — normalized and trimmed, the text the screen judged; answered by one `TodoTaskRead` |
| ticking | `PATCH /api/todo-tasks/{todo_task_id}` through its mark mutation | sends `done` alone — `true` or `false`, the state the person chose; `todo_task_id` is the row's `id` |
| correcting | `PATCH /api/todo-tasks/{todo_task_id}` through its correction mutation | sends `text` alone |
| deleting | `DELETE /api/todo-tasks/{todo_task_id}` through its delete mutation | sends nothing; answered `204` |
| the sentence of a refusal | the body of any refused write above | `detail.code` decides where it is shown, `detail.message` is the words |

**A tick sends the state chosen, never "the opposite of what is stored"**, and it sends `done`
alone; a correction sends `text` alone. That is the screen's half of `BR-09` and `BR-10`: two
people ticking the same task done both end with it done, and a tick and a correction sent at the
same moment are both kept.

**A change is shown as made only once the answer says it was stored** — no row, tick or text
appears ahead of the answer — and the list is read again after every change that went through,
which is also when other people's changes arrive
([`../architecture.md`](../architecture.md) § The to-do list — where each rule lives).
`created_at` is not shown: it orders the list, and the order is the answer's.

## Interactions

- **Typing in the add field** → nothing is judged while typing; "Add task" opens the moment the
  screen's rule accepts the text.
- **Leaving the add field, or Enter, with no text or a refused text** → the rule's sentence under
  the field; nothing is sent.
- **"Add task", or Enter, with an accepted text** → the task is sent; meanwhile "Adding…", the
  field and the button locked, no row. On success the task appears first in the list with the
  frame's one entry animation, the count follows, the field is emptied and a notice says
  "Task added.". If nothing answered: the notice "The task was not added: the service could not
  be reached.", no row, and the text stays in the field for a retry. If the service answered with
  an error of no sentence of its own: the same, with the notice "The task was not added: the
  service answered with an error.". If the service refused the text: its sentence under the
  field, and the text stays.
- **Pressing the box or its text, or Space on the box** → the chosen state is sent; meanwhile the
  box is locked on the stored state with "Saving…" beside it. On success the box and the text
  show the stored state and the row stays in its place; no notice. If the task no longer exists:
  the `todo_task_not_found` sentence in a notice, the box as it was, and the row stays until the
  list is read again. If nothing answered: "The change was not made: the service could not be
  reached.", and the box as it was. If the service answered with an error of no sentence of its
  own: "The change was not made: the service answered with an error.", and the box as it was.
- **"Edit"** → the row's editor opens with this task's stored text and the focus in the field;
  an editor open on another row closes.
- **"Edit" while a correction travels** → nothing: it is locked on every row until the answer.
- **Leaving the edit field, or Enter, with a refused text** → the rule's sentence under the field;
  nothing is sent.
- **"Save", or Enter in the edit field, with an accepted text** → the text is sent; meanwhile the
  `saving` state. On success the editor closes, the new text stands in the task's place, its done
  state as it was, and a notice says "Task updated.". If the task no longer exists: the
  `todo_task_not_found` sentence in a notice; the editor stays open with what was typed and no
  task with the new text appears. If nothing answered: "The change was not made: the service
  could not be reached.", and the editor stays open with what was typed. If the service answered
  with an error of no sentence of its own: "The change was not made: the service answered with an
  error.", and the editor stays open with what was typed. In all three, the stored text is
  unchanged and comes back on "Cancel". If the service refused the text: its sentence under the
  edit field.
- **"Cancel" in the editor** → the editor closes and the stored text shows; nothing is sent.
- **"Delete"** → the question opens over the screen; nothing is sent.
- **"Cancel", Escape, or a press on the backdrop** → the question closes and the task is as it
  was.
- **"Delete task"** → the deletion is sent; meanwhile the question's `loading` state and the row's
  `deleting` state. On success the question closes, the row goes, every other row is untouched,
  and a notice says "Task deleted."; there is no undo anywhere. Deleting the last task brings back
  the empty sentence. If the task no longer exists: the question closes and the
  `todo_task_not_found` sentence stands in a notice; the row stays until the list is read again.
  If nothing answered: the question closes, "The change was not made: the service could not be
  reached.", and the row stays. If the service answered with an error of no sentence of its own:
  the question closes, "The change was not made: the service answered with an error.", and the
  row stays. A deletion of the row being edited closes its editor with it.
- **"Try again" on a list that could not be read** → the list is read again; the error card stays
  until the answer, then the list, the empty sentence or the card again.
- **"×" on a notice** → the notice goes.
- **Opening the to-do list's own address, or reloading it** → the list is read and shown as it is
  stored at that moment, including what other people added, ticked, corrected or deleted. Nothing
  pushes their changes to an open screen.
- **The navigation, the lockup and the main address** → the frame's
  ([`system-states.md`](system-states.md) § Interactions).

Keyboard: every action above works without a mouse — see the next section.

## Keyboard and accessibility

- **The Tab order** is the frame's lockup and navigation, the add field, "Add task" when it is
  open, then row by row from the top: the box, "Edit", "Delete"; in a row being edited, the box,
  the edit field, "Save", "Cancel", "Delete". A locked control is skipped.
- **Enter in the add field** adds an accepted text or shows the rule's sentence. **Space on a
  box** ticks it or unticks it. **Enter in the edit field** saves an accepted text or shows the
  sentence. **Escape** does nothing in the editor and closes the question, except while a
  deletion travels.
- **The focus goes back where the person was.** While a write travels its control is locked, and
  a locked control lets go of the focus; when the answer comes, the focus is put back, never left
  at the page's start:
  - **after a tick settles, either way**, on that row's box;
  - **after any add, whether it went through or not**, in the add field — so after a successful
    add the next task can be typed at once, and after a failed one the text that stayed can be
    sent again;
  - **after a correction that did not go through** — refused by the service, the task no longer
    existing, nothing answered, or an error of no sentence of its own — in the edit field, which
    stays open with what was typed;
  - **when the editor closes on "Save" or "Cancel"**, on that row's "Edit".

  Each applies when the focus was on the control that was locked or closed — the add field or
  "Add task"; the box; the edit field, "Save" or "Cancel" — and a person who has put the focus
  somewhere else meanwhile keeps it where they put it.
- **The question takes the focus on "Cancel"**, keeps Tab inside itself, and on closing hands the
  focus back to the "Delete" that opened it — or, when that row is gone, to the list, never to
  the page's start.
- **The focus ring is the screen's**, in the accent colour, on everything that can take the focus:
  the add field, each box (drawn around the box), "Edit", "Delete", the edit field, "Save",
  "Cancel", the question's buttons and a notice's "×". No component removes it
  ([`guestbook.md`](guestbook.md) § The composer card).
- **Refusal sentences are announced** as alerts and the field they belong to is marked invalid.
  Success notices are announced politely and error notices at once, by the shared toast.
- **Contrast.** Every text clears 4.5:1 on the surface behind it: the task text in ink, the done
  text in `--color-muted` (7.09:1 on the card), the placeholder, "Edit", "Delete" and "Saving…"
  in `--color-faint` (5.40:1 on the card). An unticked box's edge is `--color-faint` too, which
  clears the 3:1 a control's edge needs to be seen; `--color-line` would not. A locked control's
  text is exempt, as `--color-disabled` is ([`system-states.md`](system-states.md) § Tokens).
- **Reduced motion.** The entry animation of a new row is not played when the person asks for
  reduced motion.

## Tokens

Colour and typeface from `frontend/src/styles/theme.css`, and nothing else. Spacing, sizes and
radii outside the named ones come from Tailwind's own scale — never a bracketed value and never a
raw hex.

| Use | Token |
|---|---|
| the add field's card, the list's card, a row's box when unticked, the edit field, the question | `--color-card` |
| the edges of those cards, the rows' separators, the edit field's edge, "Cancel"'s edge | `--color-hairline` |
| the dashed frame of the empty list | `--color-line` |
| the task text, the typed text | `--color-ink` |
| done text, struck through; the empty sentence; the failure sentence; "Cancel"'s text | `--color-muted` |
| the placeholder; "Edit", "Delete" and "Saving…"; an unticked box's edge | `--color-faint` |
| "Add task", "Save"; a ticked box's fill and edge; "Edit" on hover; the focus ring | `--color-accent` |
| the text on "Add task" and "Save"; the tick | `--color-inverse` |
| a refusal sentence under a field; "Delete" on hover | `--color-danger` |
| "Cancel" on hover; the outline rows while loading | `--color-surface-medium` |
| the quotation in the question; a locked edit field | `--color-surface` |
| the cards | `--radius-card` |
| "Add task" | `--radius-control` |
| the edit field, "Save", "Cancel" | `--radius-control-tight` |
| the question | `--radius-modal` |
| "Edit", "Delete", "Saving…", "Save", "Cancel", the failure sentence | `--text-meta` |
| the empty sentence | `--text-body` |
| the title | `--font-serif`; everything else `--font-sans` |
| a new row arriving | `--animate-rise` |
| a closed "Add task" or "Save" | the scale's `opacity-35`, as on the guestbook; a locked box or row button `opacity-50` |
| "Add task" and "Save" on hover | the scale's `brightness-112`, as the guestbook's post button |

The frame's own tokens — the column's width, the header, the footer, the navigation — are
[`system-states.md`](system-states.md)'s, and the notices, the question's backdrop and the error
card are the shared primitives', unchanged by this screen.

## States with no defined behaviour

None. The two the mock-up and the requirements left open were answered by the person who asked
for the change: the words of a failed change when the service answered with an error of no
sentence of its own stand in § Copy and § Interactions, and where the focus goes when a control it
was on is locked for a write and then unlocked, or removed, stands in § Keyboard and
accessibility.

## Out of scope for this screen

- **Anything to do with identity.** No sign-in, no "my tasks", no record of who added, ticked or
  corrected a task.
- **Showing the moment of adding.** It orders the list and is not shown.
- **Search, filters, pages, "clear all done", reordering, due dates, owners.** The context's
  non-goals ([`../../contexts/todo_list.md`](../../contexts/todo_list.md) § Deliberate non-goals).
- **Live updates.** Other people's changes appear when the list is read again.
- **Telling somebody their change was replaced.** The later change wins, silently (`BR-10`).
- **Undo and restore.** A deleted task is gone (`BR-13`).
- **A special state for "every task done".** Such a list is simply a list of done tasks.
- **A character counter.** The field takes every character, and the sentence under it is the
  bound.
- **Other window shapes.** This stack declares no window classes, so the screen is one layout: the
  column narrows with the window, and a phone layout is a named non-goal
  ([`../../invariants.md`](../../invariants.md) § Deliberate non-goals).
- **Other languages and a dark theme.** English only; one palette
  ([`system-states.md`](system-states.md) § One palette).

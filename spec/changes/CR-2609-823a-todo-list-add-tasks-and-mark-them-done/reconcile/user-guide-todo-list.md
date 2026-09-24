# Using the to-do list

**For:** the person using the screen.
**Normative source:** `spec/contexts/todo_list.md` for the rules, `spec/design/ui/todo-list.md`
for every state of the screen, `spec/design/api.md` § The to-do list's refusals for the words of
every refusal.

> **Where this page belongs.** Beside `docs/user-guide.md`, the guest book's guide, as
> `docs/user-guide-todo-list.md`, with a row in the table of `docs/README.md`. It was written
> inside the change record because the step that wrote it may not write under `docs/`. Delete this
> note when the page moves.

## What it is

One list of things to do, shared by everybody who opens the application. You reach it with the
link **To-do list** in the header, beside **Guestbook**. The screen is titled "Things to do". The
application's main address still opens the guest book.

**There is no sign-in.** Everybody sees the same list, in the same order, with the same ticks.
Anybody can add a task, tick it, correct it or delete it, including a task somebody else added.
The list cannot show you "your" tasks, because it does not know who you are.

## Adding a task

Type one line into the field that says "What needs doing?" and press **Add task**, or Enter. The
task appears at the top of the list, not done, and the notice "Task added." confirms it. The field
empties itself for the next task.

- **A task is one line of at most 200 characters.** Spaces at either end are trimmed away. Spaces
  inside the text are kept exactly as you typed them.
- **The field never stops you typing, and there is no counter.** When you leave the field or press
  Enter, it tells you if the text cannot be added, and **Add task** stays closed until the text is
  fixed. The sentence goes away as soon as the text is acceptable.
- **Accented letters and most emoji count as one character each.** A few emoji are built from
  several parts, such as a flag, a family or a skin tone, and each part counts.
- **The same text twice is two tasks.** Nothing warns you about a duplicate. Each copy is ticked,
  corrected and deleted on its own.
- **While a task is being saved** the button reads "Adding…", and the field and button are locked
  until the answer comes.

## Ticking a task done

Press the box beside a task, or the task's text. The box fills with a tick and the text is struck
through. Press it again to make the task not done. A tick by mistake is undone in one press.

**A tick never moves the task.** The list is always in the order the tasks were added, newest
first, and a done task stays where it was. There is no notice for a tick, because the box is its
own confirmation. While a tick is being saved, "Saving…" shows beside the box.

## Correcting a task

Press **Edit**, change the text, and press **Save**, or Enter. The notice "Task updated." confirms
it.

- **Correcting changes the words and nothing else.** A done task stays done, and the task keeps its
  place in the list.
- **The same limits apply as for a new task.** One line, at most 200 characters, not empty.
- **Escape does nothing in the editor**, so a stray key cannot lose your edit. **Cancel** brings
  the text back as it was.
- **One task is edited at a time.** Pressing **Edit** on another task closes the first editor, and
  what you typed there is dropped.

## Deleting a task

Press **Delete**. A question opens: "Delete this task?", with the task quoted, and "This cannot
be undone." **Cancel** is selected first, so an Enter pressed out of habit deletes nothing.
**Delete task** deletes it, and the notice "Task deleted." confirms it.

**Deletion is permanent.** There is no undo and no bin. A restore from backup is the only way back,
and it returns the whole application, the guest book included, to an earlier moment rather than
bringing back one task.

## Other people on the same list

**Other people's changes appear when you open the list or reload the page.** Nothing updates a
screen that is already open. Opening the list reads it afresh every time, whether you use the
header link, its address or a reload. For a moment you may see the list as you last saw it, until
the fresh copy arrives.

**When two people change the same task at the same moment**, a tick and a correction are both
kept. Of two corrections, or two ticks, the one saved later wins. Nobody is told that their change
was replaced.

## Example tasks in a new environment

A newly created environment opens with **five example tasks, one of them already done**. That
includes a preview, a fresh copy on a laptop, and a stage nobody has used yet. They are ordinary
tasks: tick them, correct them, delete them. **Production never gets them.**

They are added only to an **empty** list. Once the list holds any task, nothing is added. So
outside production, a list somebody has emptied gets the five example tasks back the next time that
environment is deployed, or on a laptop the next time the application is started.

## When something goes wrong

The sentences under the field go away once the text is fixed. The notices that report a failure
stay until you dismiss them with **×**. The notices that confirm a success go away by themselves.

| What you see | What happened | What to do |
|---|---|---|
| "A task needs text. Type what there is to do." | the text is empty, or nothing but spaces | type the task |
| "A task can be at most 200 characters. Shorten it and try again." | the text is over 200 characters once the spaces at its ends are trimmed | shorten it |
| "A task is one line, and this text has a line break inside it, which may not be visible. Remove the line break and try again." | the text you pasted carries a line break. It is often invisible: a line copied out of a word processor or another document can carry one. This reason is the one you get even when the text is also too long | delete the text and type it again, or paste it a line at a time |
| "This task no longer exists. Somebody may have deleted it, and nothing was changed." | somebody else deleted the task while your screen still showed it. Your tick, correction or deletion was not applied, and the task was not brought back | reload the page; the task will be gone |
| "The task was not added: the service could not be reached." | no answer came, and nothing was stored | your text is still in the field; press **Add task** again once the connection is back |
| "The change was not made: the service could not be reached." | a tick, a correction or a deletion was not stored; the task shows what is stored | try again. After a failed correction the editor stays open with what you typed, so press **Save** again |
| "The task was not added: the service answered with an error." or "The change was not made: the service answered with an error." | the service failed on its side, and nothing was stored | try again; if it keeps happening, whoever operates the environment should read `docs/troubleshooting.md` |
| "The tasks could not be loaded.", with "Could not reach the service" and **Try again** | the list could not be read. This is not an empty list | press **Try again**. You can still add a task meanwhile |
| "No tasks yet. Add the first one above." | the list is empty. This is not an error | add a task |
| A task appears twice after a reload, although you were told it was not added | your first attempt did reach the list, but its answer was lost on the way back, and you added it again | delete the copy you do not want |
| The very first load of the day is slow | outside production the database sleeps when nothing uses it, and takes ten to fifteen seconds to wake | wait, once |

## What changed on the guest book

- **The header.** The name at the top left is now a placeholder, "Product name" with the letter
  "P", and it still leads to the guest book. Beside it are two links, **Guestbook** and
  **To-do list**, with the screen you are on marked.
- **A page that does not exist** now says "There is nothing at this address." It used to say that
  the guest book was the only screen.
- **Nothing else.** The guest book has the same address, the same entries, the same limits and the
  same sentence at its foot.

## What the list cannot do

Written down because each is a decision rather than a gap:

- no accounts, no "my tasks", and no record of who added or ticked a task;
- no due dates, priorities, assigned people, categories or notes, and only one list;
- no search, filters, pages or "clear all done";
- no reordering, and a done task is never moved to the bottom;
- no live updates;
- no undo, and no way to restore one deleted task;
- no warning when somebody else's change replaced yours;
- no duplicate detection.

No largest number of tasks has been set: the whole list is shown at once. Adding any of these
starts with `spec/contexts/todo_list.md`, not with the screen.

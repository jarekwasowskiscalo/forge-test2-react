# Findings

*The brainstorm for CR-2609-823a — a to-do list. Nine questions in three rounds, asked and
answered on 2026-09-24. Every answer below is the user's choice, recorded as `Q-1`…`Q-9` in the
change record.*

**Is this one change?** Yes. One to-do list and one screen: adding a task, ticking it done,
editing it and deleting it all live in one place. The one part that could have been a change of
its own was removing the guestbook, and the user chose to keep it (Q-1).

## What was settled

Already settled by the request or by the specification, and therefore not asked:

- **Anybody can add a task.** "chce by kazdy mogl dodac nowe zadanie" (`request.md`, line 5) —
  it agrees with the standing non-goal: no accounts, sessions or roles
  (`spec/invariants.md` § Deliberate non-goals).
- **One simple view:** one field to add a task, and the list of the tasks added below it
  (`request.md`, line 5).
- **Each task in the list has a way to mark it done** (`request.md`, line 5).
- **The list is kept by the application, not by the browser.** Everybody sees the same list;
  "the browser stores nothing" (`spec/design/ui/system-states.md`, lines 156-157).

Round 1:

- **Q-1 — Beside the guestbook, or replacing it?** → **Beside it; the guestbook stays.**
  - The application gets a second screen, and people need a way to switch between the two.
    The frame promises exactly that: a second screen "must add navigation here"
    (`spec/design/ui/system-states.md` § One column).
  - Copy that says the application has one screen stops being true: the 404 sentence "There
    is one screen in this application: the guestbook." (`system-states.md`, line 134).
  - Removing the guestbook is **not** part of this change.
- **Q-2 — Can a done task be switched back to not done?** → **Yes, it can be switched back.**
  - Done is a two-way switch: ticking marks the task done, and ticking again marks it not done.
    This settles the reading of "odznaczenia" in the request as a toggle.
- **Q-3 — Which of "ew usuniecie lub edycja" belong in this change?** → **Both delete and
  edit.**
  - "ew." is settled as *and also*, not as *maybe later*. Every task can have its text changed
    and can be removed.
- **Q-4 — What happens to a task once it is marked done?** → **It stays in its place, shown as
  done.**
  - Ticking never moves a task. Done tasks are shown differently from open ones (for example
    ticked or crossed out).

Round 2:

- **Q-5 — With two screens, which one opens at the main address?** → **The guestbook, as
  today.**
  - `/` keeps going to the guestbook (`frontend/src/router.tsx:29`), and the smoke test that
    pins it (`e2e/ui/test_smoke.py::test_the_root_redirects_to_the_one_screen`) keeps its
    meaning. Only its name, "the one screen", stops being true.
  - The to-do list gets an address of its own and is reached through the navigation.
- **Q-6 — In what order are the tasks listed?** → **Newest at the top.**
  - A task just added appears first, right under the field. Together with Q-4, the order is
    by when a task was added, and ticking done never changes it.
  - Two tasks added at the same instant still need a fixed order, which the guestbook gets
    from a tie-break (`spec/contexts/guestbook.md` § `BR-04`). See § Open.
- **Q-7 — Which language does the to-do screen use?** → **English, like the rest.**
  - Copy follows `spec/design/conventions.md` § Language. No rule is lifted. The request was
    written in Polish; the screen is not.
- **Q-8 — Does a fresh copy of the app start with example tasks?** → **Yes, a few example
  tasks.**
  - The seed half of the corpus (`golden-set/seed/`) gets example tasks, and the seeder has to
    post them. Today it knows `/guestbook-entries` alone and refuses a guest book that already
    has entries (`scripts/seed_golden_set.py:70`; `spec/design/architecture.md` § What a new
    environment starts with).
  - **This reaches `scripts/`.** `impact.md` recorded `tooling_touched` as absent on exactly
    this condition: "reached only if the requirements give the list seed data" (§ What I
    could not determine; § Tier signals). The condition is now met. See § Open.

Round 3, the read-back:

- **Q-9 — Is the summary right, including the assumptions for the smaller details?** →
  **Looks right, go ahead.** The summary was read back in plain words, together with the eight
  assumptions below, and the user confirmed all of them. They are settled, not assumed:
  - **A task is one line of text, up to 200 characters.** An empty task, or one made only of
    spaces, is refused. (The guestbook's trimming and counting rule, `BR-01`, is the nearest
    precedent. How the 200 is counted is the requirements author's to state.)
  - **Deleting asks "are you sure?" first,** as deleting a guestbook entry does, and a deleted
    task is gone for good (no bin, no undo).
  - **Editing changes the text only, never done or not done.** A done task can be edited too.
  - **The same text can be added twice**, and that makes two separate tasks.
  - **All tasks are on one list:** no search, no pages, no filters such as "only open", and no
    "clear all done" button.
  - **No due dates, priorities, assigned people, categories or multiple lists.** It is one
    shared list.
  - **When two people change the same task at the same moment, the later change wins.** A
    task somebody else has already deleted gives a clear message that it no longer exists.
  - **The list does not update live** while somebody looks at it. They see other people's
    changes when the list reloads.

## What the user said and the system does differently

- *Nothing.* Every answer stays inside what the specification allows. Q-1 keeps the guestbook,
  which `spec/contexts/guestbook.md` (lines 17-19) calls the example the first real feature
  replaces. That is a choice the specification leaves open, not a conflict with it.

## Rules no document carried

- **A task's "done" can be undone** (Q-2). Today no stored thing in this system has a state:
  a guestbook entry "either exists or it does not" (`spec/contexts/guestbook.md` § `P-01`).
  The to-do list brings in the first stored state, and it is reversible.
- **Ticking done never moves a task** (Q-4, Q-6). The list has one order, newest first, and
  done or not done plays no part in it.
- **Editing a task leaves its done-ness alone** (Q-9). The text and the state are two separate
  things, changed separately.

## Deliberately out of scope

- **Removing or changing the guestbook** — the user chose to keep it (Q-1).
- **A Polish screen** — the screen is English, like the rest (Q-7).
- **Search, paging, filters and "clear all done"** — one list, everything on it (Q-9). The
  guestbook's `BR-05` stays the guestbook's.
- **Due dates, priorities, assigned people, categories and more than one list** — one shared
  list of one-line tasks (Q-9).
- **Live updates** — the list shows other people's changes when it reloads (Q-9).
- **Accounts, logins and "my tasks"** — the standing non-goal (`spec/invariants.md`
  § Deliberate non-goals) holds for the to-do list as it does for the guestbook: anybody may
  add, tick, edit and delete any task.

## Open

Nothing here blocks the requirements. Each item has a named owner:

- **For the orchestrator — the recorded tier signals are out of date.** Q-8 lights
  `tooling_touched`, which `impact.md` recorded as absent on the condition Q-8 has now met. The
  tier does not move (`new_context` alone gives p3). The record should say what the change
  reaches before the design stage reads it.
- **For the requirements author — the tie-break.** Newest first (Q-6) needs a rule for two
  tasks added at the same instant, the way `BR-04` gives the guestbook one. It is a detail of
  the order, not a new product choice.
- **For the design stage — the words and the frame.** The user asked for no particular address
  for the list, no particular form of navigation and no particular copy (only that it is
  English, Q-7). The lockup's product name "Guestbook", the footer about entries and the 404
  sentence all describe a one-screen guestbook application
  (`frontend/src/components/shell/PageFrame.tsx:24`, `:72`; `system-states.md`, line 134).
  What they say with two screens is the mock-up's decision, for the user to approve there.

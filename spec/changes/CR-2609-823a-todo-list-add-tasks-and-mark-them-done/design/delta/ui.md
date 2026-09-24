# Delta fragment — `design-ui`

*The to-do screen derived from the mock-up the user approved as drafted (`Q-14` → A, the 19
panels and the choices C-1…C-24 of `design/ui/index.html`), plus what the frame and the guestbook's
document had to say differently once the application has two screens. The screen document is
written into the live tree; this fragment says what moved and why. The two questions the mock-up
left open went to the person who asked for the change and are applied as answered (`Q-15` → A,
`Q-16` → A; § The two questions, answered).*

- `ADDED` `spec/design/ui/todo-list.md`
  **Why:** The requirements add a screen (`R-1` clause 1: one field for a new task with the list below it) and the mock-up that records what was agreed about it cannot be diffed, merged or made to cite a requirement (`spec/design/ui/README.md`). The document gives the builder and the frontend test author one source: the regions top to bottom, every component with the states it has on the built screen and the reason for each state it lacks, starting with `empty`; every string verbatim; each element bound to a field of `spec/design/api.md` through the resource's one hook; the interactions with what the person sees while a write travels and after it fails; the keyboard paths; and the tokens by name. It takes the frozen screen id `S-02` (the next free one after the guestbook's `S-01`) and the route `/todo-list` (C-3), which is the value `spec/design/architecture.md` leaves to the screen specification for the route constant. Two points neither the mock-up nor the requirements fixed were decided by the person who asked for the change and are written in as answered: the words of a change the service answered with an error of no sentence of its own (`Q-15` → A, § Copy and § Interactions), and where the focus goes back once a write's control is unlocked or removed (`Q-16` → A, § Keyboard and accessibility); the document's § States with no defined behaviour now says none remain.
  **ADR:** none — a screen document applies the rules already in force (`spec/design/ui/README.md`, the template, `spec/design/conventions.md` § Frontend and § Language); every choice in it was approved in the mock-up, and each is reversed by an edit to this document and the screen's own files.
  **Requirements:** CR-2609-823a/R-1, CR-2609-823a/R-2, CR-2609-823a/R-3, CR-2609-823a/R-4,
  CR-2609-823a/R-5, CR-2609-823a/R-6, CR-2609-823a/R-7, CR-2609-823a/R-8, CR-2609-823a/R-9,
  CR-2609-823a/R-10

- `MODIFIED` `spec/design/ui/system-states.md` — the front matter's `requirements`; § One column
  (both paragraphs); § Regions (the header, content and footer items, the not-found item, the
  lockup paragraph, one sentence added to the lockup-link paragraph); § Components and their
  states (§ The navigation between the screens added; the paragraph under § `Toast`); § Copy
  (the product name, two navigation rows and the product initial added, the footer row removed,
  the 404 sentence, one paragraph added); § Data (the header sentence); § Interactions (two rows
  added); § Out of scope (the Navigation item)
  **Was:** "The application has one screen, and a module switcher with one entry was furniture";
  "a product that adds a second screen **must add navigation here**"; the header holding "the
  number of entries in the guestbook"; "Content — variable; today one built screen"; "Footer —
  one sentence about who sees this", with the footer's words in this document's copy table; the
  lockup named "Guestbook"; the 404 sentence "There is one screen in this application: the
  guestbook."; a toast that "disappears on its own"; out of scope, "Navigation. One screen, so
  there is nothing to switch between"; `requirements: []`.
  **Now:** two screens and the way between them as two text links after the lockup, named
  "Screens", the current one marked, on every screen including the not-found page, with a state
  table of its own; the header's fact supplied by each screen; the footer each screen's own,
  written in that screen's document, and none on the not-found page; the lockup "Product name"
  with the initial "P", still leading to the guestbook; the 404 sentence "There is nothing at
  this address."; a success or warning toast that goes by itself and an error toast that stays
  until dismissed; out of scope, a navigation bar, switcher or side panel;
  `requirements: [CR-2609-823a/R-5, CR-2609-823a/R-10]`.
  **Why:** `R-5` clause 2 asks for a way between the two screens without typing an address, and this document had already named where it goes — "a product that adds a second screen must add navigation here" — so the navigation is written here and not in either screen's document (`spec/contexts/todo_list.md` § Neighbours: the way between the screens belongs to no context). Text links were approved over a pill switcher (it would read as a filter, like the guestbook's Newest/Oldest), the lockup as the only way back (one direction only), and a top bar or side panel (withdrawn by § One column) (C-2). The lockup's name had to change because it carried one screen's name and would have stood beside a navigation link of the same name — two identical links — and the approved placeholder keeps the template's rule that the mark must look like a placeholder (C-1). `R-5` clause 4 makes the 404 sentence false, and the approved replacement counts no screens so the next screen cannot make it false again (C-22). The footer became per screen because "Entries are public…" is untrue on the to-do screen and the guestbook keeps every word it has (C-6); one fact, one home, so each screen's document holds its own sentence. The toast paragraph contradicted the code (`frontend/src/components/ui/Toast.tsx` keeps an error toast until it is dismissed) and decides how long `R-10`'s message stays; the mock-up drew the failure notices with their dismiss button, as the code behaves, and asked the screen specification to settle it, and the approval settled it that way.
  **ADR:** none — the navigation's shape, the placeholder's two strings, the 404 sentence and the footer's home are each reversed by an edit to the frame's one file and this document (`spec/design/ui/system-states.md` § One column names that seam); the toast sentence now describes the primitive as it already behaves.
  **Requirements:** CR-2609-823a/R-5, CR-2609-823a/R-10

- `MODIFIED` `spec/design/ui/guestbook.md` — the opening sentence; § Regions, item 1; § Copy (the
  footer row added)
  **Was:** "The only screen of this application."; the header region as "the lockup, the number of
  entries…"; no footer row, because the footer's words stood in `system-states.md` § Copy.
  **Now:** "One of the application's two screens, and the one its main address opens; the other is
  the to-do list"; the header region names the frame's navigation with "Guestbook" marked; the
  footer row `Entries are public and editable by anyone with this link.`, word for word as before.
  **Why:** The document's first sentence became false the moment a second screen exists, and `R-5` clause 3 keeps the guestbook as what the main address opens, which the sentence now says. The header region gains the navigation because the frame draws it on this screen too (`R-5` clause 2, from the guestbook to the list). The footer row is the guestbook's own sentence moving to the guestbook's own document, because the frame no longer holds one footer for every screen; nothing a guest sees changes (`SC-5`).
  **ADR:** none — two sentences corrected to the new count of screens and one copy row moved to its home; no behaviour of the guestbook changes.
  **Requirements:** CR-2609-823a/R-5

## The mock-up's choices, and where each one landed

| Choice | Landed in |
|---|---|
| C-1 lockup "Product name" / "P" | `system-states.md` § Regions, § Copy |
| C-2 two text links, "Screens", current marked | `system-states.md` § One column, § The navigation between the screens |
| C-3 `/todo-list` | `todo-list.md` front matter; `system-states.md` § Interactions |
| C-4 title and sentence; C-5 the task count | `todo-list.md` § Copy; § The task count in the header |
| C-6 footer per screen | `system-states.md` § Regions; `todo-list.md` and `guestbook.md` § Copy |
| C-7, C-8, C-9, C-10 the add field, when a refusal shows, the field after an add, the in-flight lock | `todo-list.md` § The add field, § Interactions |
| C-11, C-12, C-13 the row, how done looks, rows in one card | `todo-list.md` § A task's row, § Tokens, § Keyboard and accessibility |
| C-14 editing in place; C-15 a tick in flight | `todo-list.md` § A task's row, § Interactions |
| C-16 the delete question | `todo-list.md` § The delete question |
| C-17 success notices; C-18 failure words | `todo-list.md` § Notices, § Copy |
| C-19 the row stays after "no longer exists" | `todo-list.md` § Interactions |
| C-20 empty; C-21 failed to load; C-24 loading | `todo-list.md` § The list |
| C-22 not-found page | `system-states.md` § Copy |
| C-23 long texts wrap | `todo-list.md` § A task's row |

## Where the derivation read the mock-up, and the reading rejected

- **A correction that did not go through keeps the editor open with what was typed.** Panel P7
  says so for "no longer exists" ("the editor stays open with what was typed, as on the
  guestbook"); panel P11 says of a failed correction that "the old text … stays as it was". Both
  hold at once: the stored text is unchanged (the box keeps it as its name, "Cancel" brings it
  back, the new text appears nowhere in the list) while the editor keeps what was typed. The
  rejected reading closes the editor on failure, which throws away what the person typed and
  departs from the guestbook's editor, which C-14 copies.
- **A text the service refuses on an add shows under the field**, where the screen's own verdict
  stands, and the text stays. P5 says so for a correction; C-18's "a refusal with a sentence of
  its own shows that sentence" says what is shown, not where, and a notice for a text refusal
  would put the same three sentences in two places depending on which side caught the text.
- **A tick travelling locks only its own box.** C-15 names the box alone; P10 draws "Edit"
  locked on the ticking row because a correction was travelling in the same frame, which locks
  "Edit" on every row.
- **"An error of no sentence of its own" is an answer that carries no refusal sentence.** `Q-15`
  was asked with "for example an internal server error"; the document draws the line where the
  screen already reads the words — § Data: a refusal's `detail.message` is the words — so any
  answer that came and carries no such sentence gets "…the service answered with an error.",
  and one that carries it shows it (C-18). The rejected reading keys the words to a status code
  (every `5xx`), which leaves an answer outside `5xx` that carries no sentence with no words at
  all.
- **The focus goes back only when it was on the control that was locked or closed.** `Q-16` was
  asked as "while a change is being saved, its control is locked; where does the keyboard focus
  go when that control is unlocked again, or removed?", which presumes the focus was on it; the
  document says so, and says that a person who put the focus somewhere else while the write
  travelled keeps it there. The rejected reading moves the focus back on every answer, which
  pulls a keyboard user off the row they tabbed to while a slow tick was still travelling —
  "back where the person was" read against where the person now is. The add counts "Add task"
  as its control as well as the field (both are locked while an add travels), so a pointer
  press on "Add task" also brings the focus back to the field, as the answer's "after any add"
  says.

## The two questions, answered

The first attempt returned these two as `NEEDS_DECISION`; the person who asked for the change
answered both on 2026-09-24, and each answer is written into `spec/design/ui/todo-list.md` as
given; the two readings the writing-in needed are the last two items of § Where the derivation
read the mock-up, and the reading rejected. No state of the screen is left without defined
behaviour.

| Question | Answer | Landed in |
|---|---|---|
| `Q-15` — the words when a write fails and the service answered with an error of no sentence of its own (a server error, rather than a coded refusal or no answer) | A — `The task was not added: the service answered with an error.` for an add; `The change was not made: the service answered with an error.` for a tick, a correction and a deletion | § Copy (two rows, and the paragraph saying which sentence answers which case); § Interactions (the new failure branch on adding, ticking, correcting and deleting) |
| `Q-16` — where the focus goes when a control it was on is locked for a write and then unlocked, or removed | A — back where the person was: on the row's box after a tick settles, in the add field after any add, in the edit field after a correction that did not go through, and on the row's "Edit" when the editor closes on "Save" or "Cancel" | § Keyboard and accessibility (the bullet "The focus goes back where the person was", which replaces the sentence pointing at the open question) |

Rejected with those answers, as the options put them: for `Q-15`, the "could not be reached"
sentence for every failure with no sentence of its own (untrue when the service did answer), and
the bare sentence followed by the error's title as the browser names it; for `Q-16`, leaving the
focus to the browser as the guestbook does today (it can drop the focus to the page's start), and
giving the row's box the focus when the editor closes.

## Traceability — every requirement to where the screens carry it

| Requirement | Carried by |
|---|---|
| R-1 | `todo-list.md` § Regions 3–4, § The add field, § Interactions (adding), § Data (adding), § Keyboard and accessibility (the focus back in the add field after any add) |
| R-2 | `todo-list.md` § The add field (the screen's rule, no bound on input), § A task's row (`error`), § The refusals this screen can show |
| R-3 | `todo-list.md` § The list (every state; order as it arrives; no pieces), § The task count in the header |
| R-4 | `todo-list.md` § A task's row (`done`, `loading`), § Tokens (done text at 7.09:1), § Data (ticking), § Keyboard and accessibility (the focus back on the box after a tick settles) |
| R-5 | `system-states.md` § One column, § The navigation between the screens, § Copy (404), § Interactions; `todo-list.md` front matter (its own address); `guestbook.md` opening sentence |
| R-6 | `todo-list.md` § A task's row (`editing`, `saving`, `error`), § Interactions (correcting), § Keyboard and accessibility (the focus in the edit field after a failed correction, on "Edit" when the editor closes) |
| R-7 | `todo-list.md` § The delete question, § Interactions (deleting) |
| R-8 | `todo-list.md` § The refusals this screen can show (`todo_task_not_found`), § Interactions |
| R-9 | `todo-list.md` § Data: a tick sends `done` alone and the chosen state, a correction sends `text` alone; no screen state, since nobody is told |
| R-10 | `todo-list.md` § The list (`error` is not `empty`), § Notices, § Copy (the four failure sentences: nothing answered, or an error of no sentence of its own), § Interactions (each write's failure branches), § Data (nothing shown before the answer); `system-states.md` § `Toast` (an error stays until dismissed) |
| R-11 | no state of its own: example tasks are tasks like any other on this screen; the person who checks it by hand does so here. The seeder is `spec/design/architecture.md` § What a new environment starts with |

## Found outside this write set — for the orchestrator

1. **`spec/contexts/todo_list.md` front matter says `screens: []`.** With `spec/design/ui/todo-list.md`
   carrying `info_ref: S-02`,
   `tests/fitness/test_context_declarations.py::test_every_registered_screen_is_claimed_by_exactly_one_context`
   is red until the context claims it: `screens: [spec/design/ui/todo-list.md]`. That document's own
   rule ("the header claims a screen only once it exists") is now met. `spec/contexts/` is not in
   this skill's write set.
2. **`e2e/ui/test_smoke.py` names the lockup "Guestbook" and calls it "the only navigation this
   application has".** With the lockup renamed, the exact lookup of the link "Guestbook" finds the
   navigation link alone and still leads to `/guestbook`, so the assertions can hold; the comment and
   the constant's name are build-tests-e2e's.
3. **Pre-existing, not caused by this change, and left as they are:** `system-states.md` § Tokens
   still allows sizes off the Tailwind scale, which `spec/design/conventions.md` § Frontend
   forbids; `system-states.md` § Components still describes an `EmptyState` the code removed; the
   toast glyphs and the dialog backdrop in the shared primitives use colours outside
   `frontend/src/styles/theme.css`; field edges in `--color-hairline` sit below the 3:1 a control's
   edge needs, on both screens (the new box alone is given `--color-faint`). Each belongs to a
   change of its own or to reconcile-design.
4. **Code that still says "one screen"**: the docstrings of `frontend/src/components/shell/PageFrame.tsx`
   and the sentence in `frontend/src/pages/StatusPages.tsx` — build-frontend's, in its write set.

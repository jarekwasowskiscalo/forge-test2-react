# Delta fragment — `reconcile-design`

*The technical documents the design stage wrote into `spec/design/`, read against what the
branch built. The API register held word for word against the router and the schemas, and so
did `spec/design/ui/system-states.md` and `spec/design/ui/guestbook.md` against the frame and the
not-found page: no edit. Where the code departed from the design, or the design's own count was
wrong, the specification now follows the code, and each departure is an entry below. The two ADR
drafts of `design/adr/` are promoted as the first two numbers of `spec/ADR/`; the index is
regenerated, not edited.*

- `ADDED` `spec/ADR/ADR-0001-todo-list-is-its-own-bounded-context.md`
  **Was:** the unnumbered draft `design/adr/todo-list-is-its-own-bounded-context.md`.
  **Now:** `ADR-0001`, status `Proposed`, the body as drafted; every test it names as its
  enforcement exists on the branch.
  **Why:** The decision that the to-do list is a context of its own is cross-cutting and expensive to reverse — folding it back moves a table, a contract, a screen and a test tree — so it needs a number against the trunk before the change merges, and the index had none allocated, which made this the first. It stays `Proposed` because the change is not yet merging.
  **ADR:** this entry is the ADR.
  **Requirements:** CR-2609-823a/R-1, CR-2609-823a/R-2, CR-2609-823a/R-3, CR-2609-823a/R-4, CR-2609-823a/R-6, CR-2609-823a/R-7, CR-2609-823a/R-8, CR-2609-823a/R-9

- `ADDED` `spec/ADR/ADR-0002-task-text-refusals-are-coded-not-schema-constraints.md`
  **Was:** the unnumbered draft `design/adr/task-text-refusals-are-coded-not-schema-constraints.md`.
  **Now:** `ADR-0002`, status `Proposed`, the body as drafted; the router holds the five codes as
  literals, the schemas carry `text` as a bare `StrictStr`, and every test the ADR names exists.
  **Why:** Refusing a task's text with three coded reasons outside Pydantic's field constraints departs from the guestbook's convention and freezes three codes in a contract, so reversing it is a breaking contract change; it takes the next number after `ADR-0001`, whose context it depends on. It stays `Proposed` until the change merges.
  **ADR:** this entry is the ADR.
  **Requirements:** CR-2609-823a/R-2, CR-2609-823a/R-6

- `MODIFIED` `spec/design/data-model.md` — § Migrations (the second row of the table); § The revision that creates `todo_tasks` (its first sentence); § Compatibility mode (the history line of the second revision)
  **Was:** the revision was "issued by `./scripts/db.sh revision`", with "the head at the time of implementation" as its parent, in all three places.
  **Now:** it is `5c58af1f8e8a`, whose parent is `a1b2c3d4e5f6`.
  **Why:** The design could not know the identifier `./scripts/db.sh revision` would issue, and the migrations table exists so that a reader can match a row to a file and a parent to a chain; a placeholder where the identifier belongs would stay wrong for ever once the revision is released and never edited again. The ordered operations were checked against the file and held.
  **ADR:** none — it records two identifiers the implementation issued; no column, type or operation moves.
  **Requirements:** CR-2609-823a/R-1, CR-2609-823a/R-3, CR-2609-823a/R-4

- `MODIFIED` `spec/design/architecture.md` — § The to-do list — where each rule lives › The files (the rows for `todo_list/services/todo_tasks.py`, `contexts/todo_list/lib/todoTask.ts` and `components/shell/PageFrame.tsx`); › What holds the boundaries (the row for `test_the_frontend_reads_no_corpus_file`)
  **Was:** the service held "add, read, correct, mark and delete"; the browser rule gave its verdict "in the order `BR-07` then `BR-06`"; the frame held "the way between the two screens, and the frame's words for two of them"; the corpus row refused "a second module in `frontend/src/`" reading the text-measurement corpus.
  **Now:** the service holds add, read, change and delete, a `PATCH` reaching one operation, `change_todo_task`, that writes exactly the columns the body carried in one statement, with the correction and the marking as its one-field forms; the browser verdict runs in the service's order, empty, then more than one line, then too long; the frame also holds the guestbook's footer sentence as the default of its `footer`, since `GuestbookPage.tsx` passes none; and the corpus row refuses any module other than the one reader each context has for its own file, or either reader reaching for the other's.
  **Why:** Four departures of the built code from the placement the builders were handed. One `PATCH` operation writing the given columns is still the statement shape `data-model.md` § Two writers on one task requires, but a reader looking for a separate correction and marking behind the router would not find them. "`BR-07` then `BR-06`" misreads the order `lib/todoTask.ts` and the service both apply. The guestbook's footer sits in the frame because the guestbook's page was frozen but for imports and one docstring line, so a reader of "the footer belongs to the screen" needs to know where that sentence is. And `_MAY_READ_ONE_CORPUS_FILE` now allows two readers, each of its own context's file.
  **ADR:** none — each row records where a file already holds a rule the design placed; no boundary and no decision moves.
  **Requirements:** CR-2609-823a/R-2, CR-2609-823a/R-4, CR-2609-823a/R-5, CR-2609-823a/R-6, CR-2609-823a/R-9

- `MODIFIED` `spec/design/testing.md` — § Fitness functions (the `test_length_constants.py` row); § CR-2609-823a, the to-do list (the lead paragraph's sentence on bold paths; the edits-of-existing-tests bullet; the `StatusPages.test.tsx` bullet; the `todo-task-text.json` bullet of the fixture half)
  **Was:** the length-constants row named four bounds and no line breaks; bold named "a file the test wave will create", which "does not exist until then"; the one-table case was to be "renamed for the two tables it expects"; the not-found case was "red today"; the task's text corpus held "the nineteen `scenarios.md` lists … and one more".
  **Now:** the row adds `LINE_BREAKS` beside `TodoTask`, held equal to its browser copy as a set of code points; bold names a file the test wave created, because the map was written before it existed; the renamed case is `test_this_schema_holds_exactly_two_tables`; the not-found case was red before the implementation; the corpus holds the eighteen cases `scenarios.md` lists and the one `BR-07` added, nineteen in all.
  **Why:** The fitness row understated what `test_the_line_breaks_equal_their_browser_copy` holds, and a testing document that misdescribes a detector is how the detector gets deleted. `scenarios.md` § Test data lists eighteen task-text cases and `golden-set/fixtures/todo-task-text.json` holds those eighteen plus the precedence case, so "nineteen and one more" miscounted the design's own source. The other three sentences were written in the future tense before the tests existed, and each is now false as it reads.
  **ADR:** none — which suite proves what did not move; the entries correct a count, a name and three tenses.
  **Requirements:** CR-2609-823a/R-1, CR-2609-823a/R-2, CR-2609-823a/R-5

- `MODIFIED` `spec/design/conventions.md` — § Frontend — where a file goes (the item on the shared `lib/`: the list of a context's rule files, and the sentence on the text rule's browser half); § When a decision is an ADR (the paragraph on the state of `spec/ADR/`)
  **Was:** the list of context rule files named `contexts/guestbook/lib/entryText.ts`, and "`entryText.ts` is the case worth naming … this one stays in the context because the browser has exactly one"; and "The state of `spec/ADR/`: empty, until the first change carried out through `/sdd`".
  **Now:** the list names `contexts/todo_list/lib/todoTask.ts` in its place, and the sentence names `text.ts`: the browser half of the shared text rule, paired by name with `app/platform/schemas/text.py`, which moved up from the guestbook's `lib/entryText.ts` when the to-do list became its second caller (`CR-2609-823a`); and `spec/ADR/` holds the decisions of changes carried out through `/sdd`, the first two from `CR-2609-823a`, empty until then.
  **Why:** `frontend/src/contexts/guestbook/lib/entryText.ts` no longer exists — build-frontend moved it to `frontend/src/lib/text.ts`, as this very item prescribes for the day a second context needs a rule — so the item's example named a missing file and argued the old placement as current; the design's architecture fragment reported it for this stage. And promoting `ADR-0001` and `ADR-0002` made "empty" false in the one paragraph that says what the directory holds.
  **ADR:** none — the placement rule itself is unchanged; the edit records that the case it anticipated has arrived, and that the directory now holds what it was reserved for.
  **Requirements:** CR-2609-823a/R-2

- `MODIFIED` `spec/design/ui/todo-list.md` — § Keyboard and accessibility (the bullet on the question's focus)
  **Was:** on closing, the question hands the focus back to "Delete" "or, when that row is gone, to the list, never to the page's start".
  **Now:** "…to the list, and to the empty sentence when it was the last task; never to the page's start."
  **Why:** Deleting the last task removes the list itself, so there is no list to hold the focus; `TodoListPage.tsx` puts it on the empty-list frame instead, which is focusable for exactly that case. The screen document said nothing about the one deletion where "the list" names nothing, and the built screen answers it.
  **ADR:** none — one focus target on one screen, reversed by an edit to the page and this bullet.
  **Requirements:** CR-2609-823a/R-7

## What held, and was not edited

- `spec/design/api.md` — every route, shape, cardinality, refusal code, sentence and the order of
  the refusals match `app/contexts/todo_list/routers/todo_tasks.py` and
  `app/contexts/todo_list/schemas/todo_tasks.py` word for word, `StrictStr` and `StrictBool`
  included.
- `spec/design/data-model.md` § `todo_tasks` and § Two writers on one task — the columns, the
  index and the statement shape match the model, the revision and the service.
- `spec/design/ui/system-states.md` and `spec/design/ui/guestbook.md` — the navigation, the
  lockup, the not-found sentence, the toast rule and the fresh read on opening match `PageFrame.tsx`,
  `StatusPages.tsx`, `Toast.tsx` and `useTodoTasks.ts`.
- `spec/design/ui/todo-list.md` apart from the one bullet above — every state, string, label and
  token checked against the page, the row, the composer, the dialog and the checkbox.
- `spec/design/testing.md` § CR-2609-823a apart from the entries above — every pytest function,
  vitest name and Gherkin scenario title it cites exists on the branch.

`spec/ADR/index.md` and `spec/changes/INDEX.md` were regenerated by `sdd-engine gen_indexes`.

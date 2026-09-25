# The specification delta

*One entry per file changed under `spec/`, and nothing that is not an entry. That is this
document's whole size — it carries no line budget because it does not need one. The set of
entries and the set of edits have to be equal: gate `delta-coverage` compares them.*

*What an earlier pass said about a file, and everything else the fragments carry, is in
[`delta-history.md`](delta-history.md).*

<!-- ASSEMBLED FROM FRAGMENTS -- do not edit below; the source: design/delta/, reconcile/delta/ -->

## The reconciliation phase -- what reality corrected in the design

<!-- z spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/reconcile/delta/converge.md -->
- `ADDED` `contracts/invariants/todo_list.md` § `D-05`
  **Was:** no file. `spec/design/data-model.md` § `todo_tasks` called, in the present tense, for "a data invariant of the to-do list's own under `contracts/invariants/`, the counterpart of `D-04`", and `contracts/invariants/` held `guestbook.md` alone.
  **Now:** `contract: invariants`, `domain: todo_list`, `version: 1`, and one entry: "`D-05` — a stored task's text is normalized, one line, and within its bound in code points". Every `text` in `todo_tasks` is NFC, carries no member of the written trim set at either end, holds none of the seven code points of `LINE_BREAKS`, and is 1 to `TODO_TASK_TEXT_MAX_LENGTH` (200) code points long (`BR-06`, `BR-07`). Its three witnesses are the ones `spec/design/testing.md` § CR-2609-823a, the to-do list names, and each exists: the service round trip, the corpus case and the generator. The ready patch landed as written, with the browser's corpus reader named by path, as `D-04` names its own.
  **Why:** COH-spec_sync-1. `spec/invariants.md` § Data invariants gives an invariant decided in design, whose witnesses the implementation stage writes, to the first convergence round after they exist, the `spec_sync` stage's; `testing.md` named that round, and the user decided it at `Q-21` (6): "stated in the data model now and written into the data-rules folder at the reconciliation stage, once its tests exist." None of the four `spec_sync` members writes `contracts/`, and each said so, so without this round the data model would have merged citing a contract that did not exist. `D-05` is the next free identifier: nothing in `contracts/` or `spec/` used it.
  **ADR:** none — it writes down, where data invariants live, a rule the data model already stated and the user already placed.
  **Requirements:** CR-2609-823a/R-2, CR-2609-823a/R-6

- `MODIFIED` `contracts/invariants/README.md` — the **Contracts:** line
  **Was:** "`guestbook.md` — `D-01`…`D-03`, each with a witness and a kind of evidence."
  **Now:** "`guestbook.md` — `D-01`…`D-04`; `todo_list.md` — `D-05`; each with a witness and a kind of evidence."
  **Why:** COH-spec_sync-1, the second half of its ready patch. The line is the directory's list of its contracts, and a new contract that the list does not name is found only by listing the directory. The count also corrects `D-03` to `D-04`: `guestbook.md` has held `D-04` since before this change, and the line never caught up.
  **ADR:** none — an index line brought level with the files it indexes.
  **Requirements:** CR-2609-823a/R-2, CR-2609-823a/R-6

- `MODIFIED` `spec/invariants.md` § Data invariants: one paragraph added after "Which stage's convergence round writes a new data invariant is settled by its witnesses"
  **Was:** the section named "the first convergence round after they exist — the `spec_sync` stage's" as the writer, and did not say what makes that round run.
  **Now:** "What makes that round run is its stage's coherence pass." No member of the `spec_sync` stage writes `contracts/`, so an invariant a design document calls for, whose witnesses exist and which `contracts/invariants/` does not yet hold, is a finding of that pass in its own right; a pass that finds nothing else still records it, or the stage closes with the invariant unwritten.
  **Why:** COH-spec_sync-1, its ambiguity source. A convergence round is sent only for what a coherence pass records, and nothing obliged the pass to record an invariant it owed. Every `spec_sync` member left the invariant to "the round", and a clean pass would have closed the stage with no round at all. Settled automatically by the section itself, whose route this sentence completes.
  **ADR:** none — it says what triggers an existing route, and no rule about the data moves.
  **Requirements:** CR-2609-823a/R-2

- `MODIFIED` `spec/glossary.md` § Identifiers and their spaces — the `ADR-xxxx` row
  **Was:** "`spec/ADR/` (empty today — `design/conventions.md` § When a decision is an ADR)".
  **Now:** "`spec/ADR/` (what it holds: `design/conventions.md` § When a decision is an ADR)", the link kept.
  **Why:** COH-spec_sync-2, its ambiguity source. This stage promoted `ADR-0001` and `ADR-0002`, and `conventions.md` § When a decision is an ADR, the paragraph the row cites as its authority, now says the directory holds them. The row restated the directory's state instead of only pointing at its home, so the promotion edited the home and left the copy false. Settled automatically by the constitution, Article IV: the edit describing a fact this change creates lands in its pull request.
  **ADR:** none — a pointer that stops restating what it points at.
  **Requirements:** CR-2609-823a/R-1

- `MODIFIED` `spec/README.md` — the `spec/ADR/**` bullet, its last sentence
  **Was:** "The directory is empty today: the template's decisions, taken without a change record, stand as "decision of <date>" paragraphs in the normative documents, and the first ADR will come out of the first change through `/forge:sdd`".
  **Now:** "The template's decisions taken without a change record stand as "decision of <date>" paragraphs in the normative documents. The ADRs here come out of changes carried out through `/forge:sdd`, the first two from `CR-2609-823a`", the link to `conventions.md` kept.
  **Why:** COH-spec_sync-2, the second of the two sentences its ready patch names. It said the directory holds nothing, while `spec/ADR/index.md` lists two ADRs. It is edited with the glossary row because the finding's resolution is one: both copies stop stating the directory's state. Settled automatically by the constitution, Article IV.
  **ADR:** none — a fact this change made true, and no rule moves.
  **Requirements:** CR-2609-823a/R-1

- `MODIFIED` `spec/ADR/ADR-0001-todo-list-is-its-own-bounded-context.md` § Consequences — the bullet "Deleting the guestbook is no longer the deletion of one unit", one sentence
  **Was:** "That edit is outside every write set of this change and was reported by `design-spec`, and nothing enforces it."
  **Now:** "`design-spec` reported that the list was silent, `reconcile-docs` wrote the paragraph in the `spec_sync` stage of this change, and nothing enforces it."
  **Why:** COH-spec_sync-3. The draft said "this change" and meant the stages its author could see, design and implement. In the same wave that promoted the ADR, reconcile-docs wrote the paragraph into `CLAUDE.md` § What is an example ("One thing moves before the guestbook goes"), so the sentence became false. Once accepted, an ADR is never edited (`spec/design/conventions.md` § When a decision is an ADR); it is still `Proposed`, so this is the last moment the sentence can be corrected. Settled automatically by the constitution, Article IV.
  **ADR:** this entry edits the ADR itself, before acceptance; the decision is unchanged.
  **Requirements:** CR-2609-823a/R-1

- `MODIFIED` `spec/design/architecture.md` § What a new environment starts with — the second paragraph, its last clause
  **Was:** "because "an environment nobody has written in yet" is one condition and not two."
  **Now:** "because "a list that holds nothing yet" is one condition, asked of each list, whatever kind of environment holds it."
  **Why:** COH-spec_sync-4. Six lines apart the section said "Each list is filled on its own" and named "an environment nobody has written in yet" as the condition. An environment with a guest book entry and no task gets its example tasks, so the seeder (`scripts/seed_golden_set.py`) is not asking the second question, and `reconcile/delta/docs.md` names that phrase as the alternative `Q-10` rejected. `requirements.md` § Impact analysis read it as the fill condition; the design read "one condition" as clone against preview and kept it. Settled automatically by the constitution, Article IV.
  **ADR:** none — the sentence now says what the paragraph above it and the user's `Q-10` already decided.
  **Requirements:** CR-2609-823a/R-11

- `MODIFIED` `spec/design/architecture.md` § The to-do list — where each rule lives › The files — one row added after the `scripts/` row
  **Was:** the one `scripts/` row gave build-backend `seed_golden_set.py` and `seed.sh`, "filling each list on its own, and saying so in `--help`": `seed.sh`'s own help. § What a new environment starts with names `start.sh`, `preview.sh` and `deploy.sh` as the callers of `seed.sh`, and no row placed what their help and comments say about seeding.
  **Now:** a row for `start.sh`, `help.sh`, `deploy.sh` and `preview.sh`, written by build-backend: "text only: each calls or lists `seed.sh`, so every `--help` line and comment of theirs that describes the seeding says what `seed.sh` does — each list filled on its own when it holds nothing, a list that already holds something never touched, one `GET` per list on every run after the first; nothing they do moves".
  **Why:** COH-spec_sync-5, its ambiguity source. `./scripts/start.sh --help` still says `--no-seed` leaves "the guest book" empty, `./scripts/help.sh` says `seed.sh` fills "an environment's guest book", and the comments in `start.sh`, `deploy.sh` and `preview.sh` count one `GET`, while this document counts one per list and `--no-seed` skips `seed.sh` altogether. `--help` is the human interface (constitution, Article XII), and code contradicting `spec/` is a defect in the code (Article I). The writer is build-backend because § Who writes what gives it `scripts/`, as does `.specconf/stack.json`, which names `scripts/` as deliberately not build-platform's.
  **ADR:** none — who writes which file in this change, and reversing it edits one table row.
  **Requirements:** CR-2609-823a/R-11

- `MODIFIED` `spec/design/conventions.md` § Documentation — where a document goes: the `docs/` row of the table, and one paragraph added after the table
  **Was:** the `docs/` row gave the tree "the system: how to set it up, run it, configure it, watch it, back it up and repair it", for "whoever operates or takes delivery of the application". It named no home for a guide addressed to the person using a screen, although `docs/user-guide.md`, the guest book's, stood there before this change.
  **Now:** the subject adds "and how each of its screens is used", and the reader adds "and the person using one of its screens". The paragraph: "A screen's user guide is therefore `docs/`'s, one per screen beside `user-guide.md`, the guest book's: it describes the running system to the person using it, and binds nothing either." The user's words close it.
  **Why:** COH-spec_sync-7. reconcile-ops, the member whose tree is `docs/`, read the row and left the to-do list's guide out as not operations documentation. reconcile-docs read the precedent, took `docs/` for the guide's home, and could not write there, so the page sat in the change record with a note saying it was in the wrong place. The user decided `Q-31` = A: "Move it to docs/ with the other guide."
  **ADR:** none — a placement rule, in the document where placement rules live (constitution, Article IX).
  **Requirements:** CR-2609-823a/R-5

- `MODIFIED` `spec/design/architecture.md` § The to-do list — where each rule lives › The files — the row for `start.sh`, `help.sh`, `deploy.sh` and `preview.sh`, its "Written by" cell
  **Was:** "build-backend", which pass 10's round wrote for `COH-spec_sync-5`: the four scripts' seeding text corrected in this change.
  **Now:** "not this change: a text-only pull request with a changelog entry corrects them right after it merges, because build-backend does not run in the stage that found the text stale. The user decided it in `CR-2609-823a` (`Q-32`) in these words: "Follow-up fix right after merge."" The "Holds" cell is unchanged. It still says what the four scripts' help and comments must say.
  **Why:** COH-spec_sync-8. The row named a writer, and nobody was dispatched to write it. `git diff main --stat -- scripts/` touches only `seed.sh` and `seed_golden_set.py`, and `./scripts/start.sh --help` still says `--no-seed` leaves "the guest book" empty. Only build-backend may write `scripts/`, and it does not run in `spec_sync`. The user chose at `Q-32` not to send the change back: "This change goes on to delivery now; the stale help text is recorded as a known item and fixed in a small separate pull request with a changelog entry." The row now says who corrects the text and when, as § Who writes what already does for `golden-set/README.md` (`Q-26`).
  **ADR:** none. It says who writes four files and when; reversing it edits one cell.
  **Requirements:** CR-2609-823a/R-11

- `MODIFIED` `spec/invariants.md` § Data invariants: one paragraph added after the three one-sentence summaries of `D-01`…`D-03`
  **Was:** the section moved `D-01`…`D-03` into `contracts/invariants/guestbook.md` and stated them of every entity and every primary key. It did not say that the file bearing the guestbook's name holds every table's rules, or what happens to them when the guestbook is deleted.
  **Now:** "They are every table's, although the file that holds them is named for the guestbook, the example a reader may delete." `D-01`…`D-03` hold for `todo_tasks` as for every table, and `D-05` is written as `D-04` for a task. So `D-01`…`D-04` move first into `contracts/invariants/todo_list.md`, keeping their identifiers, and `guestbook.md` goes after them. It closes with the user's words at `Q-33`: "Move the four data rules too."
  **Why:** COH-spec_sync-11, its ambiguity source. The file's name says the rules are the guestbook's, and its content says they are every table's. The deletion lists in `CLAUDE.md` and `spec/README.md` followed the name: "One thing moves before the guestbook goes: the words of the text rule". `contracts/invariants/todo_list.md` followed the content: "`D-01`…`D-04` stand in `guestbook.md`". Deleting the guestbook as the lists said would turn three checks red. `tests/fitness/test_invariant_witnesses.py` asserts `{"D-01", "D-02", "D-03"} <= found`, `frozen-ids` fails on every citation of `D-04`, and `links` fails on `todo_list.md`:10. The user decided at `Q-33` that the lists name the move.
  **ADR:** none. It says where four existing invariants go when their file's context is deleted. No invariant's body changes, and neither does the rule for their identifiers.
  **Requirements:** CR-2609-823a/R-1, CR-2609-823a/R-2

- `MODIFIED` `spec/README.md` § This directory describes a template — one sentence added after the deletion list
  **Was:** the list deleted `contracts/invariants/guestbook.md` with the example and named nothing that moves out first.
  **Now:** "Two things move out first, because the to-do list stays and is held to both: the words of the text rule, `BR-01`, into `contexts/todo_list.md` (its § Neighbours), and the data invariants `D-01`…`D-04`, into `contracts/invariants/todo_list.md`, keeping their identifiers (`invariants.md` § Data invariants)."
  **Why:** COH-spec_sync-11. The finding names this list beside `CLAUDE.md`'s, and `Q-33` names this file: "CLAUDE.md, spec/README.md and ADR-0001 say D-01 to D-04 move into the to-do list's rules file first, keeping their identifiers, before the guestbook's file is deleted". The sentence names `BR-01` too. Without it this list would name one move where `CLAUDE.md` names two, which is how the finding arose.
  **ADR:** none. It is a deletion list, brought level with `CLAUDE.md`'s.
  **Requirements:** CR-2609-823a/R-1

- `MODIFIED` `spec/ADR/ADR-0001-todo-list-is-its-own-bounded-context.md` § Consequences — the bullet "Deleting the guestbook is no longer the deletion of one unit", one sentence added after the `BR-01` sentence
  **Was:** the bullet named the words of `BR-01` as the one thing that moves before the guestbook is deleted.
  **Now:** "The same holds for `D-01`…`D-04`, which `contracts/invariants/todo_list.md` builds on: they move into it first, keeping their identifiers, before `contracts/invariants/guestbook.md` is deleted (`spec/invariants.md` § Data invariants)."
  **Why:** COH-spec_sync-11. `Q-33` names ADR-0001 as one of the three texts that say it. The ADR is still `Proposed`, so it can be edited now and not after acceptance (`spec/design/conventions.md` § When a decision is an ADR). The same bullet already explains why `contracts/openapi/todo_list.yaml` does not `$ref` into `guestbook.yaml`. The invariants contract written in this stage points into `guestbook.md`, which is the same trap.
  **ADR:** this entry edits the ADR itself, before acceptance. The decision is unchanged.
  **Requirements:** CR-2609-823a/R-1

<!-- z spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/reconcile/delta/design.md -->
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

<!-- z spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/reconcile/delta/spec.md -->
- `MODIFIED` `spec/contexts/todo_list.md` — § `BR-13` (one paragraph added after its second
  paragraph; every other paragraph byte-identical)
  **Was:** `BR-13` said that a change aimed at a task that no longer exists "tells the person the
  task no longer exists — a marking, a correction and a second deletion alike". `BR-10` said
  that a corrected text `BR-06` or `BR-07` refuses is refused "with the reason an addition of that
  text would get". Neither said which reason a person gets when both apply at once: a corrected
  text the rules refuse, aimed at a task somebody has deleted.
  **Now:** `BR-13` states that such a correction is told the text's reason, on the screen and by
  the application alike, because the screen refuses the text before anything is sent. Only a
  change that could otherwise be made learns that its task no longer exists.
  **Why:** As written, the bold sentence of `BR-13` was false for one case the build handles on purpose. The service judges a correction's text before it writes, and the lookup is the write itself, so a refused text is refused for its text whatever task it names (`judge_todo_task_text` runs before the one `UPDATE` in `change_todo_task`). The contract publishes that order as "the lookup last" (`spec/design/api.md` § The to-do list's refusals), and `test_a_request_is_refused_for_what_it_is_whatever_its_identifier_names` holds it under `CR-2609-823a/R-8`. The screen cannot behave any other way: `BR-06` forbids it to let through a text the application would refuse, so the editor refuses that text before sending anything, and a person there never learns that the task is gone. `R-6` clause 4 and `R-8` clause 1 both apply to this case and name different reasons. The design-spec pass settled the matching overlap of `BR-06` and `BR-07` inside `BR-07`, for the same reason: one text, one verdict, on both sides. This one was left for the contract and the screen to settle separately. They agree, and the context document now says what they agree on. This is the design being vague, not the build drifting. The edit adds no rule the code does not hold.
  **ADR:** none. The order was decided in design and is published in `spec/design/api.md`. It is reversible by one line of the service, with no migration and no rewritten contract shape, and this entry adds no decision of its own.
  **Requirements:** CR-2609-823a/R-6, CR-2609-823a/R-8

## Superseded by a later pass

*40 entries about a file a later phase spoke about again, kept in full in [`delta-history.md`](delta-history.md). This brief carries the current statement about each path and nothing else.*

- `MODIFIED` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/api.md`
- `ADDED` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/api.md`
- `MODIFIED` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/api.md`
- `MODIFIED` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/architecture.md`
- `MODIFIED` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `MODIFIED` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `MODIFIED` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `MODIFIED` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `MODIFIED` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `MODIFIED` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `MODIFIED` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `MODIFIED` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `MODIFIED` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `MODIFIED` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `MODIFIED` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `MODIFIED` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `MODIFIED` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `MODIFIED` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `MODIFIED` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `MODIFIED` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `MODIFIED` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `MODIFIED` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `MODIFIED` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `MODIFIED` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `MODIFIED` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `MODIFIED` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `MODIFIED` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `MODIFIED` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `MODIFIED` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `MODIFIED` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `MODIFIED` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `MODIFIED` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/data-model.md`
- `ADDED` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/domain.md`
- `MODIFIED` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/domain.md`
- `MODIFIED` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/spec.md`
- `MODIFIED` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/spec.md`
- `MODIFIED` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/testing.md`
- `ADDED` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/ui.md`
- `MODIFIED` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/ui.md`
- `MODIFIED` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/ui.md`

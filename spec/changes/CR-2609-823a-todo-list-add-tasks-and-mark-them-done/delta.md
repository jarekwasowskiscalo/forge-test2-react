# The specification delta

*One entry per file changed under `spec/`, and nothing that is not an entry. That is this
document's whole size — it carries no line budget because it does not need one. The set of
entries and the set of edits have to be equal: gate `delta-coverage` compares them.*

*What an earlier pass said about a file, and everything else the fragments carry, is in
[`delta-history.md`](delta-history.md).*

<!-- ASSEMBLED FROM FRAGMENTS -- do not edit below; the source: design/delta/, reconcile/delta/ -->

## The design phase -- what the change wrote into the specification

<!-- z spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/api.md -->
- MODIFIED `spec/design/api.md` — the opening sentence; § Routes and their contexts (two rows); § Shapes (`TodoTaskRead`, `TodoTaskList`, `TodoTaskCreate`, `TodoTaskUpdate`, added after the guestbook's four); § Endpoints (four rows, and the subsection "The to-do list's endpoints"); § Refusals (the subsection "The to-do list's refusals", after the guestbook's body example). Every other paragraph is byte-identical.
  **Was:** the register described one context: its opening named `spec/contexts/guestbook.md` as where the rules are, the route table had three rows, and every shape, endpoint and refusal code was the guestbook's or the health probe's.
  **Now:** the opening names both context documents; `/api/todo-tasks` (`GET`, `POST`) and `/api/todo-tasks/{todo_task_id}` (`PATCH`, `DELETE`) are registered to `todo_list`; four shapes are stated field by field, with read and write kept apart; four endpoints with their cardinality; and five stable refusal codes — `todo_task_not_found` (404), `todo_task_empty_patch`, `todo_task_text_empty`, `todo_task_text_multiline`, `todo_task_text_too_long` (422) — each with its finished sentence, whether it carries `id`, and the one order in which a request earns exactly one of them.
  **Why:** Two implementers build this boundary at the same time without talking, so every question they could answer differently is answered here once: that marking and correcting are one `PATCH` whose absent fields are never written, which is what lets a correction and a marking sent at the same moment both stick (`BR-10`, race `W-1`) and makes a marking set the chosen state instead of flipping the stored one (`BR-09`, race `W-2`); that a missing task answers `404` and is never created again (`BR-13`, race `W-3`); that the list is one envelope holding every task in one total order with no parameters (`BR-11`); and that a task's text is refused with one of three codes a caller can branch on, in the order `BR-07` fixes, because the requirements demand a reason of its own for a line break (`R-2` clause 6, `Q-11`) and the scenarios tell "no text", "too long" and "more than one line" apart (`S-6`, `S-8`, `S-33`), which the integration corpus test proves on the wire and which FastAPI's list of Pydantic errors cannot do in words this contract owns. The standing rule of § Refusals — a stable code, a finished sentence, a status code with two shapes published as two — is applied to the new resource rather than restated.
  **ADR:** required — design-adr drafts it. Decision: every refusal of a task's text is a coded refusal in the `Refusal` envelope, decided outside Pydantic's field constraints (the published `TodoTaskCreate.text` is a required string with no `minLength` or `maxLength`), which departs from the guestbook's convention of answering an empty or over-long field with FastAPI's list. Rejected: (1) the guestbook's convention, bounds as `Field(min_length, max_length)` — no code this contract owns, only Pydantic's own type strings, and the length constraint answers before any later check sees the text, so a 201-code-point text with a line break would be called too long, the opposite of `BR-07`; (2) custom Pydantic error types raised from a schema validator — a code we own, but inside the list shape, which `frontend/src/api/problem.ts` reduces to its `msg` so the screen could not branch on it, and outside every router module, where the contract gate looks for each `x-refusals` literal, so the codes would be frozen by nothing; (3) a handler in `app/core/errors.py` that turns Pydantic errors into coded refusals — domain knowledge in the framework module that by rule knows nothing about the domain. This is not the router re-validation the guestbook's 2026-09-16 decision rejected: the rule is the context's (`BR-06`, `BR-07`), it is decided where business rules are decided, and the router only translates, which is `spec/design/conventions.md` § Layers as written; and the three codes exist because a requirement asks for three reasons, not to make a declaration come true. Cross-cutting (router, service, frontend adapter, black-box steps) and expensive to reverse (removing a stable code is a breaking change and a major version of the contract). Also taken here, none of them an ADR because each follows a convention in force or reverses in one file: one `PATCH` with optional fields rather than two sub-resources (`PUT …/done`, `PUT …/text`) — the guestbook's `PATCH` is the shape in force, and a future field is then an optional addition rather than a new endpoint, while a toggle endpoint was never open because `BR-09` forbids a flip; no read of one task, because no requirement reads one; `created_at` on the wire, rejected alternative leaving it off, because `BR-08` and `BR-11` make two promises about it that nobody could check otherwise; `{items, total}` although the list has no pieces, rejected alternative a bare array, because adding the count later breaks every caller.
  **Requirements:** CR-2609-823a/R-1, CR-2609-823a/R-2, CR-2609-823a/R-3, CR-2609-823a/R-4, CR-2609-823a/R-6, CR-2609-823a/R-7, CR-2609-823a/R-8, CR-2609-823a/R-9, CR-2609-823a/R-10, CR-2609-823a/R-11

- ADDED `contracts/openapi/todo_list.yaml`
  **Why:** Article VI of the constitution makes the contract the authority at a boundary and the code the thing validated against it, and `contracts/README.md` makes every `/api/*` path the application serves fall under a prefix some contract claims — so the moment `/api/todo-tasks` is served without this file, `./scripts/contracts.sh` goes red on an unclaimed boundary, and the frontend's generated types would describe whatever the Pydantic dump happened to say. The file freezes the two paths, the four operations with every status each answers, the four shapes (with `TodoTaskUpdate`'s optional fields frozen by existence only, as the guestbook's are), and the five codes under `x-refusals`, which is the only place a code is held still because FastAPI never puts one in `openapi.json`. It defines `Refusal`, `RefusalDetail`, `HTTPValidationError` and `ValidationError` again instead of referencing `guestbook.yaml`, because the guestbook is deleted as a unit and a contract that cannot be read without it would break on that day; the dump has one schema of each name, so the gate holds both copies to one definition.
  **ADR:** required — the same decision as the entry above (the text's refusals as codes rather than schema constraints), which is why no `minLength` or `maxLength` is frozen on `text`; the rest follows `contracts/openapi/README.md` as written.
  **Requirements:** CR-2609-823a/R-1, CR-2609-823a/R-2, CR-2609-823a/R-3, CR-2609-823a/R-4, CR-2609-823a/R-6, CR-2609-823a/R-7, CR-2609-823a/R-8, CR-2609-823a/R-9

- MODIFIED `contracts/openapi/README.md` — the **Contracts:** line
  **Was:** "`guestbook.yaml` (guestbook entries, `/api/guestbook-entries`) and `health.yaml` (the `/api/health` probe). Compatibility mode of both: **Backward**".
  **Now:** it names `todo_list.yaml` (the to-do list's tasks, `/api/todo-tasks`) between the two, and says the compatibility mode of all three is **Backward**.
  **Why:** The README is where a contract directory says what it holds and which compatibility mode each contract carries, and a reader deciding whether the to-do contract may be deployed before the code or after it looks there first. A third file that the line does not name reads as a file nobody declared, and "both" would then be a false count in the one sentence the directory uses to introduce itself.
  **ADR:** none — the line records a contract this change adds and repeats the mode the new file declares in its own header; no rule moves.
  **Requirements:** CR-2609-823a/R-1, CR-2609-823a/R-3

<!-- z spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md -->
- MODIFIED `spec/design/ui/guestbook.md` § Data: one paragraph added after the table
  **Was:** the table named the posting and amending hooks and not what they send. The rule lived only in the code, in `frontend/src/contexts/guestbook/components/EntryComposer.tsx` ("what is sent should be what the browser measured") and `frontend/src/contexts/guestbook/components/EntryCard.tsx`.
  **Now:** "What is posted and amended is the text the screen judged, not the text as typed." Each field is sent as the shared text rule leaves it, normalized and trimmed, so the browser and the service measure the same value.
  **Why:** COH-design-11. The worked example said nothing about its payload. design-ui wrote the to-do screen's add as "sends `text` as typed", and design-testing gave the composer the case "sends the text as the shared rule leaves it". build-frontend would have met a test its builder may not edit. The user decided `Q-21` (2) = A: "Adding a task sends the text cleaned up the same way the screen checked it, as the guestbook does, instead of exactly as typed".
  **ADR:** none. It writes down what the worked example already does.
  **Requirements:** CR-2609-823a/R-1

- MODIFIED `contracts/README.md` § Why a contract is written rather than generated
  **Was:** "for this template that is three paths, six operations and eight schemas".
  **Now:** "for this template that is five paths, ten operations and twelve schemas".
  **Why:** COH-design-18. `contracts/openapi/todo_list.yaml` adds two paths, four operations and four schemas (`TodoTaskCreate`, `TodoTaskUpdate`, `TodoTaskRead`, `TodoTaskList`), counted on the old figure's own convention. `./scripts/contracts.sh` prints "3 contracts, 5 paths, 10 operations". Settled automatically by the constitution, Article IV.
  **ADR:** none. It is a count this change makes true.
  **Requirements:** CR-2609-823a/R-1, CR-2609-823a/R-3

- MODIFIED `spec/design/ui/system-states.md` § Interactions: one paragraph added after the table
  **Was:** the table said the header links navigate "without a reload" and did not say whether the screen they open reads its list again. Only `spec/design/ui/todo-list.md` § Interactions spoke of reading ("Opening the to-do list's own address, or reloading it → the list is read"), and the 30 seconds a cached list is shown lived in a comment in `frontend/src/main.tsx` alone.
  **Now:** "Opening the to-do list reads its list, every time — the header link included." The screen shows the tasks as stored at that moment, never a copy it read earlier, with the user's words. The guestbook is unchanged: opened by a link within 30 seconds of its last read, it shows that read, and a reload or a change made on it reads it afresh.
  **Why:** COH-implement-1. `requirements.md` § R-3 clause 5 and `todo-list.md` promise what is stored "at that moment", and `uat.md` step 14 expects a header link to show a seeding done seconds before. The to-do query inherits `staleTime: 30_000` from `main.tsx`, and TanStack Query refetches on mount only stale data, so a header link opened within 30 seconds shows the old read. The requirement and the UAT author both read "opening" as "reading" because this section, which owns the header links, was silent. The user decided `Q-25` = A: "Always fetch the latest."
  **ADR:** none. It states what one screen does when it is opened; reversing it edits one query option and this paragraph.
  **Requirements:** CR-2609-823a/R-3

- MODIFIED `spec/design/ui/system-states.md` § Interactions: the paragraph on opening the to-do list, its second sentence reworded and three sentences added
  **Was:** "the screen shows the tasks as they are stored at that moment, other people's changes of the last few seconds included, and never a copy it read earlier". Nothing said what is drawn while the read made on opening is under way.
  **Now:** "the screen reads its list afresh and shows the tasks as they are stored at that moment, other people's changes of the last few seconds included." Then: "A list it read earlier in the same tab stays on screen only until that read answers, and is then replaced; it is not swapped for the loading outline meanwhile." The user's words follow, and a reload and an entered address are named as having no earlier list to show.
  **Why:** COH-implement-7. The paragraph promised "never a copy it read earlier". The code written for it (`useTodoTasks.ts`, `staleTime: 0` alone) keeps a cached list for TanStack Query's default five minutes and draws it, as a success, until the fresh read answers. So a to-do list left and reopened by its header link first shows the list it read before. `requirements.md` § R-3 clause 5, "SHALL show the tasks exactly as they are stored at that moment", said what is shown once the list is read, not while the read is under way: the convergence round of pass 7 read it as "nothing else is ever shown", build-frontend as "a read is always made". The user decided `Q-28` = A: "Briefly showing it is fine." The code stays as it is.
  **ADR:** none. It states what one screen draws for the length of one read; reversing it is one query option (`gcTime: 0`) and this paragraph.
  **Requirements:** CR-2609-823a/R-3

<!-- z spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/spec.md -->
- MODIFIED `spec/contexts/guestbook.md` — the front matter's `neighbours`, the opening sentence,
  § `BR-01` (one paragraph added) and § Boundaries (its first paragraph, and the lead-in of its
  second)
  **Was:** "The only bounded context of this system and the only feature it has";
  `neighbours: []`, with § Boundaries saying the context borders on nothing and "this one shows
  what the document looks like when there is nothing to draw", and a paragraph headed "What the
  second context will have to write"; `BR-01` said nothing about any text but an entry's.
  **Now:** the opening names the guestbook as a bounded context sharing one rule with the to-do
  list; `neighbours: [todo_list:peer:shared-kernel]`; § Boundaries carries the one neighbour row,
  whose account points at the to-do list's § Neighbours instead of restating it, and the second
  paragraph is headed "How a neighbour is declared" with its body unchanged; `BR-01` gains one
  paragraph saying a task's text is held to the same normalization, trim set and unit, with each
  context keeping its own bounds, and that a change to the rule changes both contexts.
  **Why:** The to-do list declares a shared kernel with the guestbook over the text rule of `BR-01`, and from that moment three sentences of the guestbook's own document were false: it called itself the only context, declared that it borders on nothing, and described its boundary as the empty example. A shared kernel is a peer relation held by both sides, so a header saying `[]` on one side and `shared-kernel` on the other is a boundary drawn in two different ways. The paragraph in `BR-01` is the one that matters most: the to-do list's § Neighbours says the rule "changes only with both sets of rules in view", and the person who changes it reads `BR-01`, not the to-do list — without a sentence there, the rule's home would be silent about its second holder. The rule itself is not touched: its normalization, its thirty code points, its unit and its bounds of 80 and 1000 read as they did.
  **ADR:** none — the decision behind this edit (a to-do list context of its own, joined to the guestbook by a shared kernel that is the text rule alone) is the ADR `design/delta/domain.md` marks as required for `design-adr`; this entry records the guestbook's side of that boundary and changes no rule.
  **Requirements:** CR-2609-823a/R-1, CR-2609-823a/R-2

<!-- z spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/ui.md -->
- MODIFIED `spec/design/ui/system-states.md` — the front matter's `requirements`; § One column
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

- MODIFIED `spec/design/ui/guestbook.md` — the opening sentence; § Regions, item 1; § Copy (the
  footer row added)
  **Was:** "The only screen of this application."; the header region as "the lockup, the number of
  entries…"; no footer row, because the footer's words stood in `system-states.md` § Copy.
  **Now:** "One of the application's two screens, and the one its main address opens; the other is
  the to-do list"; the header region names the frame's navigation with "Guestbook" marked; the
  footer row `Entries are public and editable by anyone with this link.`, word for word as before.
  **Why:** The document's first sentence became false the moment a second screen exists, and `R-5` clause 3 keeps the guestbook as what the main address opens, which the sentence now says. The header region gains the navigation because the frame draws it on this screen too (`R-5` clause 2, from the guestbook to the list). The footer row is the guestbook's own sentence moving to the guestbook's own document, because the frame no longer holds one footer for every screen; nothing a guest sees changes (`SC-5`).
  **ADR:** none — two sentences corrected to the new count of screens and one copy row moved to its home; no behaviour of the guestbook changes.
  **Requirements:** CR-2609-823a/R-5

## The reconciliation phase -- what reality corrected in the design

<!-- z spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/reconcile/delta/converge.md -->
- ADDED `contracts/invariants/todo_list.md` § `D-05`
  **Was:** no file. `spec/design/data-model.md` § `todo_tasks` called, in the present tense, for "a data invariant of the to-do list's own under `contracts/invariants/`, the counterpart of `D-04`", and `contracts/invariants/` held `guestbook.md` alone.
  **Now:** `contract: invariants`, `domain: todo_list`, `version: 1`, and one entry: "`D-05` — a stored task's text is normalized, one line, and within its bound in code points". Every `text` in `todo_tasks` is NFC, carries no member of the written trim set at either end, holds none of the seven code points of `LINE_BREAKS`, and is 1 to `TODO_TASK_TEXT_MAX_LENGTH` (200) code points long (`BR-06`, `BR-07`). Its three witnesses are the ones `spec/design/testing.md` § CR-2609-823a, the to-do list names, and each exists: the service round trip, the corpus case and the generator. The ready patch landed as written, with the browser's corpus reader named by path, as `D-04` names its own.
  **Why:** COH-spec_sync-1. `spec/invariants.md` § Data invariants gives an invariant decided in design, whose witnesses the implementation stage writes, to the first convergence round after they exist, the `spec_sync` stage's; `testing.md` named that round, and the user decided it at `Q-21` (6): "stated in the data model now and written into the data-rules folder at the reconciliation stage, once its tests exist." None of the four `spec_sync` members writes `contracts/`, and each said so, so without this round the data model would have merged citing a contract that did not exist. `D-05` is the next free identifier: nothing in `contracts/` or `spec/` used it.
  **ADR:** none — it writes down, where data invariants live, a rule the data model already stated and the user already placed.
  **Requirements:** CR-2609-823a/R-2, CR-2609-823a/R-6

- MODIFIED `contracts/invariants/README.md` — the **Contracts:** line
  **Was:** "`guestbook.md` — `D-01`…`D-03`, each with a witness and a kind of evidence."
  **Now:** "`guestbook.md` — `D-01`…`D-04`; `todo_list.md` — `D-05`; each with a witness and a kind of evidence."
  **Why:** COH-spec_sync-1, the second half of its ready patch. The line is the directory's list of its contracts, and a new contract that the list does not name is found only by listing the directory. The count also corrects `D-03` to `D-04`: `guestbook.md` has held `D-04` since before this change, and the line never caught up.
  **ADR:** none — an index line brought level with the files it indexes.
  **Requirements:** CR-2609-823a/R-2, CR-2609-823a/R-6

- MODIFIED `spec/invariants.md` § Data invariants: one paragraph added after "Which stage's convergence round writes a new data invariant is settled by its witnesses"
  **Was:** the section named "the first convergence round after they exist — the `spec_sync` stage's" as the writer, and did not say what makes that round run.
  **Now:** "What makes that round run is its stage's coherence pass." No member of the `spec_sync` stage writes `contracts/`, so an invariant a design document calls for, whose witnesses exist and which `contracts/invariants/` does not yet hold, is a finding of that pass in its own right; a pass that finds nothing else still records it, or the stage closes with the invariant unwritten.
  **Why:** COH-spec_sync-1, its ambiguity source. A convergence round is sent only for what a coherence pass records, and nothing obliged the pass to record an invariant it owed. Every `spec_sync` member left the invariant to "the round", and a clean pass would have closed the stage with no round at all. Settled automatically by the section itself, whose route this sentence completes.
  **ADR:** none — it says what triggers an existing route, and no rule about the data moves.
  **Requirements:** CR-2609-823a/R-2

- MODIFIED `spec/glossary.md` § Identifiers and their spaces — the `ADR-xxxx` row
  **Was:** "`spec/ADR/` (empty today — `design/conventions.md` § When a decision is an ADR)".
  **Now:** "`spec/ADR/` (what it holds: `design/conventions.md` § When a decision is an ADR)", the link kept.
  **Why:** COH-spec_sync-2, its ambiguity source. This stage promoted `ADR-0001` and `ADR-0002`, and `conventions.md` § When a decision is an ADR, the paragraph the row cites as its authority, now says the directory holds them. The row restated the directory's state instead of only pointing at its home, so the promotion edited the home and left the copy false. Settled automatically by the constitution, Article IV: the edit describing a fact this change creates lands in its pull request.
  **ADR:** none — a pointer that stops restating what it points at.
  **Requirements:** CR-2609-823a/R-1

- MODIFIED `spec/README.md` — the `spec/ADR/**` bullet, its last sentence
  **Was:** "The directory is empty today: the template's decisions, taken without a change record, stand as "decision of <date>" paragraphs in the normative documents, and the first ADR will come out of the first change through `/forge:sdd`".
  **Now:** "The template's decisions taken without a change record stand as "decision of <date>" paragraphs in the normative documents. The ADRs here come out of changes carried out through `/forge:sdd`, the first two from `CR-2609-823a`", the link to `conventions.md` kept.
  **Why:** COH-spec_sync-2, the second of the two sentences its ready patch names. It said the directory holds nothing, while `spec/ADR/index.md` lists two ADRs. It is edited with the glossary row because the finding's resolution is one: both copies stop stating the directory's state. Settled automatically by the constitution, Article IV.
  **ADR:** none — a fact this change made true, and no rule moves.
  **Requirements:** CR-2609-823a/R-1

- MODIFIED `spec/ADR/ADR-0001-todo-list-is-its-own-bounded-context.md` § Consequences — the bullet "Deleting the guestbook is no longer the deletion of one unit", one sentence
  **Was:** "That edit is outside every write set of this change and was reported by `design-spec`, and nothing enforces it."
  **Now:** "`design-spec` reported that the list was silent, `reconcile-docs` wrote the paragraph in the `spec_sync` stage of this change, and nothing enforces it."
  **Why:** COH-spec_sync-3. The draft said "this change" and meant the stages its author could see, design and implement. In the same wave that promoted the ADR, reconcile-docs wrote the paragraph into `CLAUDE.md` § What is an example ("One thing moves before the guestbook goes"), so the sentence became false. Once accepted, an ADR is never edited (`spec/design/conventions.md` § When a decision is an ADR); it is still `Proposed`, so this is the last moment the sentence can be corrected. Settled automatically by the constitution, Article IV.
  **ADR:** this entry edits the ADR itself, before acceptance; the decision is unchanged.
  **Requirements:** CR-2609-823a/R-1

- MODIFIED `spec/design/architecture.md` § What a new environment starts with — the second paragraph, its last clause
  **Was:** "because "an environment nobody has written in yet" is one condition and not two."
  **Now:** "because "a list that holds nothing yet" is one condition, asked of each list, whatever kind of environment holds it."
  **Why:** COH-spec_sync-4. Six lines apart the section said "Each list is filled on its own" and named "an environment nobody has written in yet" as the condition. An environment with a guest book entry and no task gets its example tasks, so the seeder (`scripts/seed_golden_set.py`) is not asking the second question, and `reconcile/delta/docs.md` names that phrase as the alternative `Q-10` rejected. `requirements.md` § Impact analysis read it as the fill condition; the design read "one condition" as clone against preview and kept it. Settled automatically by the constitution, Article IV.
  **ADR:** none — the sentence now says what the paragraph above it and the user's `Q-10` already decided.
  **Requirements:** CR-2609-823a/R-11

- MODIFIED `spec/design/architecture.md` § The to-do list — where each rule lives › The files — one row added after the `scripts/` row
  **Was:** the one `scripts/` row gave build-backend `seed_golden_set.py` and `seed.sh`, "filling each list on its own, and saying so in `--help`": `seed.sh`'s own help. § What a new environment starts with names `start.sh`, `preview.sh` and `deploy.sh` as the callers of `seed.sh`, and no row placed what their help and comments say about seeding.
  **Now:** a row for `start.sh`, `help.sh`, `deploy.sh` and `preview.sh`, written by build-backend: "text only: each calls or lists `seed.sh`, so every `--help` line and comment of theirs that describes the seeding says what `seed.sh` does — each list filled on its own when it holds nothing, a list that already holds something never touched, one `GET` per list on every run after the first; nothing they do moves".
  **Why:** COH-spec_sync-5, its ambiguity source. `./scripts/start.sh --help` still says `--no-seed` leaves "the guest book" empty, `./scripts/help.sh` says `seed.sh` fills "an environment's guest book", and the comments in `start.sh`, `deploy.sh` and `preview.sh` count one `GET`, while this document counts one per list and `--no-seed` skips `seed.sh` altogether. `--help` is the human interface (constitution, Article XII), and code contradicting `spec/` is a defect in the code (Article I). The writer is build-backend because § Who writes what gives it `scripts/`, as does `.specconf/stack.json`, which names `scripts/` as deliberately not build-platform's.
  **ADR:** none — who writes which file in this change, and reversing it edits one table row.
  **Requirements:** CR-2609-823a/R-11

- MODIFIED `spec/design/conventions.md` § Documentation — where a document goes: the `docs/` row of the table, and one paragraph added after the table
  **Was:** the `docs/` row gave the tree "the system: how to set it up, run it, configure it, watch it, back it up and repair it", for "whoever operates or takes delivery of the application". It named no home for a guide addressed to the person using a screen, although `docs/user-guide.md`, the guest book's, stood there before this change.
  **Now:** the subject adds "and how each of its screens is used", and the reader adds "and the person using one of its screens". The paragraph: "A screen's user guide is therefore `docs/`'s, one per screen beside `user-guide.md`, the guest book's: it describes the running system to the person using it, and binds nothing either." The user's words close it.
  **Why:** COH-spec_sync-7. reconcile-ops, the member whose tree is `docs/`, read the row and left the to-do list's guide out as not operations documentation. reconcile-docs read the precedent, took `docs/` for the guide's home, and could not write there, so the page sat in the change record with a note saying it was in the wrong place. The user decided `Q-31` = A: "Move it to docs/ with the other guide."
  **ADR:** none — a placement rule, in the document where placement rules live (constitution, Article IX).
  **Requirements:** CR-2609-823a/R-5

- MODIFIED `spec/design/architecture.md` § The to-do list — where each rule lives › The files — the row for `start.sh`, `help.sh`, `deploy.sh` and `preview.sh`, its "Written by" cell
  **Was:** "build-backend", which pass 10's round wrote for `COH-spec_sync-5`: the four scripts' seeding text corrected in this change.
  **Now:** "not this change: a text-only pull request with a changelog entry corrects them right after it merges, because build-backend does not run in the stage that found the text stale. The user decided it in `CR-2609-823a` (`Q-32`) in these words: "Follow-up fix right after merge."" The "Holds" cell is unchanged. It still says what the four scripts' help and comments must say.
  **Why:** COH-spec_sync-8. The row named a writer, and nobody was dispatched to write it. `git diff main --stat -- scripts/` touches only `seed.sh` and `seed_golden_set.py`, and `./scripts/start.sh --help` still says `--no-seed` leaves "the guest book" empty. Only build-backend may write `scripts/`, and it does not run in `spec_sync`. The user chose at `Q-32` not to send the change back: "This change goes on to delivery now; the stale help text is recorded as a known item and fixed in a small separate pull request with a changelog entry." The row now says who corrects the text and when, as § Who writes what already does for `golden-set/README.md` (`Q-26`).
  **ADR:** none. It says who writes four files and when; reversing it edits one cell.
  **Requirements:** CR-2609-823a/R-11

- MODIFIED `spec/invariants.md` § Data invariants: one paragraph added after the three one-sentence summaries of `D-01`…`D-03`
  **Was:** the section moved `D-01`…`D-03` into `contracts/invariants/guestbook.md` and stated them of every entity and every primary key. It did not say that the file bearing the guestbook's name holds every table's rules, or what happens to them when the guestbook is deleted.
  **Now:** "They are every table's, although the file that holds them is named for the guestbook, the example a reader may delete." `D-01`…`D-03` hold for `todo_tasks` as for every table, and `D-05` is written as `D-04` for a task. So `D-01`…`D-04` move first into `contracts/invariants/todo_list.md`, keeping their identifiers, and `guestbook.md` goes after them. It closes with the user's words at `Q-33`: "Move the four data rules too."
  **Why:** COH-spec_sync-11, its ambiguity source. The file's name says the rules are the guestbook's, and its content says they are every table's. The deletion lists in `CLAUDE.md` and `spec/README.md` followed the name: "One thing moves before the guestbook goes: the words of the text rule". `contracts/invariants/todo_list.md` followed the content: "`D-01`…`D-04` stand in `guestbook.md`". Deleting the guestbook as the lists said would turn three checks red. `tests/fitness/test_invariant_witnesses.py` asserts `{"D-01", "D-02", "D-03"} <= found`, `frozen-ids` fails on every citation of `D-04`, and `links` fails on `todo_list.md`:10. The user decided at `Q-33` that the lists name the move.
  **ADR:** none. It says where four existing invariants go when their file's context is deleted. No invariant's body changes, and neither does the rule for their identifiers.
  **Requirements:** CR-2609-823a/R-1, CR-2609-823a/R-2

- MODIFIED `spec/README.md` § This directory describes a template — one sentence added after the deletion list
  **Was:** the list deleted `contracts/invariants/guestbook.md` with the example and named nothing that moves out first.
  **Now:** "Two things move out first, because the to-do list stays and is held to both: the words of the text rule, `BR-01`, into `contexts/todo_list.md` (its § Neighbours), and the data invariants `D-01`…`D-04`, into `contracts/invariants/todo_list.md`, keeping their identifiers (`invariants.md` § Data invariants)."
  **Why:** COH-spec_sync-11. The finding names this list beside `CLAUDE.md`'s, and `Q-33` names this file: "CLAUDE.md, spec/README.md and ADR-0001 say D-01 to D-04 move into the to-do list's rules file first, keeping their identifiers, before the guestbook's file is deleted". The sentence names `BR-01` too. Without it this list would name one move where `CLAUDE.md` names two, which is how the finding arose.
  **ADR:** none. It is a deletion list, brought level with `CLAUDE.md`'s.
  **Requirements:** CR-2609-823a/R-1

- MODIFIED `spec/ADR/ADR-0001-todo-list-is-its-own-bounded-context.md` § Consequences — the bullet "Deleting the guestbook is no longer the deletion of one unit", one sentence added after the `BR-01` sentence
  **Was:** the bullet named the words of `BR-01` as the one thing that moves before the guestbook is deleted.
  **Now:** "The same holds for `D-01`…`D-04`, which `contracts/invariants/todo_list.md` builds on: they move into it first, keeping their identifiers, before `contracts/invariants/guestbook.md` is deleted (`spec/invariants.md` § Data invariants)."
  **Why:** COH-spec_sync-11. `Q-33` names ADR-0001 as one of the three texts that say it. The ADR is still `Proposed`, so it can be edited now and not after acceptance (`spec/design/conventions.md` § When a decision is an ADR). The same bullet already explains why `contracts/openapi/todo_list.yaml` does not `$ref` into `guestbook.yaml`. The invariants contract written in this stage points into `guestbook.md`, which is the same trap.
  **ADR:** this entry edits the ADR itself, before acceptance. The decision is unchanged.
  **Requirements:** CR-2609-823a/R-1

<!-- z spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/reconcile/delta/design.md -->
- ADDED `spec/ADR/ADR-0001-todo-list-is-its-own-bounded-context.md`
  **Was:** the unnumbered draft `design/adr/todo-list-is-its-own-bounded-context.md`.
  **Now:** `ADR-0001`, status `Proposed`, the body as drafted; every test it names as its
  enforcement exists on the branch.
  **Why:** The decision that the to-do list is a context of its own is cross-cutting and expensive to reverse — folding it back moves a table, a contract, a screen and a test tree — so it needs a number against the trunk before the change merges, and the index had none allocated, which made this the first. It stays `Proposed` because the change is not yet merging.
  **ADR:** this entry is the ADR.
  **Requirements:** CR-2609-823a/R-1, CR-2609-823a/R-2, CR-2609-823a/R-3, CR-2609-823a/R-4, CR-2609-823a/R-6, CR-2609-823a/R-7, CR-2609-823a/R-8, CR-2609-823a/R-9

- ADDED `spec/ADR/ADR-0002-task-text-refusals-are-coded-not-schema-constraints.md`
  **Was:** the unnumbered draft `design/adr/task-text-refusals-are-coded-not-schema-constraints.md`.
  **Now:** `ADR-0002`, status `Proposed`, the body as drafted; the router holds the five codes as
  literals, the schemas carry `text` as a bare `StrictStr`, and every test the ADR names exists.
  **Why:** Refusing a task's text with three coded reasons outside Pydantic's field constraints departs from the guestbook's convention and freezes three codes in a contract, so reversing it is a breaking contract change; it takes the next number after `ADR-0001`, whose context it depends on. It stays `Proposed` until the change merges.
  **ADR:** this entry is the ADR.
  **Requirements:** CR-2609-823a/R-2, CR-2609-823a/R-6

- MODIFIED `spec/design/data-model.md` — § Migrations (the second row of the table); § The revision that creates `todo_tasks` (its first sentence); § Compatibility mode (the history line of the second revision)
  **Was:** the revision was "issued by `./scripts/db.sh revision`", with "the head at the time of implementation" as its parent, in all three places.
  **Now:** it is `5c58af1f8e8a`, whose parent is `a1b2c3d4e5f6`.
  **Why:** The design could not know the identifier `./scripts/db.sh revision` would issue, and the migrations table exists so that a reader can match a row to a file and a parent to a chain; a placeholder where the identifier belongs would stay wrong for ever once the revision is released and never edited again. The ordered operations were checked against the file and held.
  **ADR:** none — it records two identifiers the implementation issued; no column, type or operation moves.
  **Requirements:** CR-2609-823a/R-1, CR-2609-823a/R-3, CR-2609-823a/R-4

- MODIFIED `spec/design/architecture.md` — § The to-do list — where each rule lives › The files (the rows for `todo_list/services/todo_tasks.py`, `contexts/todo_list/lib/todoTask.ts` and `components/shell/PageFrame.tsx`); › What holds the boundaries (the row for `test_the_frontend_reads_no_corpus_file`)
  **Was:** the service held "add, read, correct, mark and delete"; the browser rule gave its verdict "in the order `BR-07` then `BR-06`"; the frame held "the way between the two screens, and the frame's words for two of them"; the corpus row refused "a second module in `frontend/src/`" reading the text-measurement corpus.
  **Now:** the service holds add, read, change and delete, a `PATCH` reaching one operation, `change_todo_task`, that writes exactly the columns the body carried in one statement, with the correction and the marking as its one-field forms; the browser verdict runs in the service's order, empty, then more than one line, then too long; the frame also holds the guestbook's footer sentence as the default of its `footer`, since `GuestbookPage.tsx` passes none; and the corpus row refuses any module other than the one reader each context has for its own file, or either reader reaching for the other's.
  **Why:** Four departures of the built code from the placement the builders were handed. One `PATCH` operation writing the given columns is still the statement shape `data-model.md` § Two writers on one task requires, but a reader looking for a separate correction and marking behind the router would not find them. "`BR-07` then `BR-06`" misreads the order `lib/todoTask.ts` and the service both apply. The guestbook's footer sits in the frame because the guestbook's page was frozen but for imports and one docstring line, so a reader of "the footer belongs to the screen" needs to know where that sentence is. And `_MAY_READ_ONE_CORPUS_FILE` now allows two readers, each of its own context's file.
  **ADR:** none — each row records where a file already holds a rule the design placed; no boundary and no decision moves.
  **Requirements:** CR-2609-823a/R-2, CR-2609-823a/R-4, CR-2609-823a/R-5, CR-2609-823a/R-6, CR-2609-823a/R-9

- MODIFIED `spec/design/testing.md` — § Fitness functions (the `test_length_constants.py` row); § CR-2609-823a, the to-do list (the lead paragraph's sentence on bold paths; the edits-of-existing-tests bullet; the `StatusPages.test.tsx` bullet; the `todo-task-text.json` bullet of the fixture half)
  **Was:** the length-constants row named four bounds and no line breaks; bold named "a file the test wave will create", which "does not exist until then"; the one-table case was to be "renamed for the two tables it expects"; the not-found case was "red today"; the task's text corpus held "the nineteen `scenarios.md` lists … and one more".
  **Now:** the row adds `LINE_BREAKS` beside `TodoTask`, held equal to its browser copy as a set of code points; bold names a file the test wave created, because the map was written before it existed; the renamed case is `test_this_schema_holds_exactly_two_tables`; the not-found case was red before the implementation; the corpus holds the eighteen cases `scenarios.md` lists and the one `BR-07` added, nineteen in all.
  **Why:** The fitness row understated what `test_the_line_breaks_equal_their_browser_copy` holds, and a testing document that misdescribes a detector is how the detector gets deleted. `scenarios.md` § Test data lists eighteen task-text cases and `golden-set/fixtures/todo-task-text.json` holds those eighteen plus the precedence case, so "nineteen and one more" miscounted the design's own source. The other three sentences were written in the future tense before the tests existed, and each is now false as it reads.
  **ADR:** none — which suite proves what did not move; the entries correct a count, a name and three tenses.
  **Requirements:** CR-2609-823a/R-1, CR-2609-823a/R-2, CR-2609-823a/R-5

- MODIFIED `spec/design/conventions.md` — § Frontend — where a file goes (the item on the shared `lib/`: the list of a context's rule files, and the sentence on the text rule's browser half); § When a decision is an ADR (the paragraph on the state of `spec/ADR/`)
  **Was:** the list of context rule files named `contexts/guestbook/lib/entryText.ts`, and "`entryText.ts` is the case worth naming … this one stays in the context because the browser has exactly one"; and "The state of `spec/ADR/`: empty, until the first change carried out through `/sdd`".
  **Now:** the list names `contexts/todo_list/lib/todoTask.ts` in its place, and the sentence names `text.ts`: the browser half of the shared text rule, paired by name with `app/platform/schemas/text.py`, which moved up from the guestbook's `lib/entryText.ts` when the to-do list became its second caller (`CR-2609-823a`); and `spec/ADR/` holds the decisions of changes carried out through `/sdd`, the first two from `CR-2609-823a`, empty until then.
  **Why:** `frontend/src/contexts/guestbook/lib/entryText.ts` no longer exists — build-frontend moved it to `frontend/src/lib/text.ts`, as this very item prescribes for the day a second context needs a rule — so the item's example named a missing file and argued the old placement as current; the design's architecture fragment reported it for this stage. And promoting `ADR-0001` and `ADR-0002` made "empty" false in the one paragraph that says what the directory holds.
  **ADR:** none — the placement rule itself is unchanged; the edit records that the case it anticipated has arrived, and that the directory now holds what it was reserved for.
  **Requirements:** CR-2609-823a/R-2

- MODIFIED `spec/design/ui/todo-list.md` — § Keyboard and accessibility (the bullet on the question's focus)
  **Was:** on closing, the question hands the focus back to "Delete" "or, when that row is gone, to the list, never to the page's start".
  **Now:** "…to the list, and to the empty sentence when it was the last task; never to the page's start."
  **Why:** Deleting the last task removes the list itself, so there is no list to hold the focus; `TodoListPage.tsx` puts it on the empty-list frame instead, which is focusable for exactly that case. The screen document said nothing about the one deletion where "the list" names nothing, and the built screen answers it.
  **ADR:** none — one focus target on one screen, reversed by an edit to the page and this bullet.
  **Requirements:** CR-2609-823a/R-7

<!-- z spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/reconcile/delta/spec.md -->
- MODIFIED `spec/contexts/todo_list.md` — § `BR-13` (one paragraph added after its second
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

*30 entries about a file a later phase spoke about again, kept in full in [`delta-history.md`](delta-history.md). This brief carries the current statement about each path and nothing else.*

- `spec/design/architecture.md` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/architecture.md`
- `spec/invariants.md` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `spec/design/conventions.md` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `spec/design/conventions.md` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `spec/design/conventions.md` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `spec/README.md` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `spec/design/architecture.md` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `spec/contexts/todo_list.md` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `spec/design/testing.md` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `spec/design/testing.md` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `spec/design/testing.md` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `spec/design/ui/todo-list.md` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `spec/design/conventions.md` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `spec/design/architecture.md` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `spec/design/data-model.md` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `spec/invariants.md` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `spec/design/architecture.md` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `spec/README.md` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `spec/design/testing.md` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `spec/design/architecture.md` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `spec/design/testing.md` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `spec/contexts/todo_list.md` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `spec/design/testing.md` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `spec/design/testing.md` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md`
- `spec/design/data-model.md` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/data-model.md`
- `spec/contexts/todo_list.md` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/domain.md`
- `spec/glossary.md` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/domain.md`
- `spec/contexts/todo_list.md` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/spec.md`
- `spec/design/testing.md` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/testing.md`
- `spec/design/ui/todo-list.md` — the design phase, `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/ui.md`

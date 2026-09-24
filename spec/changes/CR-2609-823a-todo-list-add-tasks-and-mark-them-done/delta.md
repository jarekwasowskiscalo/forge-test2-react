# The specification delta

*One entry per file changed under `spec/`, and nothing that is not an entry. That is this
document's whole size — it carries no line budget because it does not need one. The set of
entries and the set of edits have to be equal: gate `delta-coverage` compares them.*

*What an earlier pass said about a file, and everything else the fragments carry, is in
[`delta-history.md`](delta-history.md).*

<!-- ASSEMBLED FROM FRAGMENTS -- do not edit below; the source: design/delta/, reconcile/delta/ -->

## The design phase -- what the change wrote into the specification

<!-- z spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/api.md -->
- `MODIFIED` `spec/design/api.md` — the opening sentence; § Routes and their contexts (two rows); § Shapes (`TodoTaskRead`, `TodoTaskList`, `TodoTaskCreate`, `TodoTaskUpdate`, added after the guestbook's four); § Endpoints (four rows, and the subsection "The to-do list's endpoints"); § Refusals (the subsection "The to-do list's refusals", after the guestbook's body example). Every other paragraph is byte-identical.
  **Was:** the register described one context: its opening named `spec/contexts/guestbook.md` as where the rules are, the route table had three rows, and every shape, endpoint and refusal code was the guestbook's or the health probe's.
  **Now:** the opening names both context documents; `/api/todo-tasks` (`GET`, `POST`) and `/api/todo-tasks/{todo_task_id}` (`PATCH`, `DELETE`) are registered to `todo_list`; four shapes are stated field by field, with read and write kept apart; four endpoints with their cardinality; and five stable refusal codes — `todo_task_not_found` (404), `todo_task_empty_patch`, `todo_task_text_empty`, `todo_task_text_multiline`, `todo_task_text_too_long` (422) — each with its finished sentence, whether it carries `id`, and the one order in which a request earns exactly one of them.
  **Why:** Two implementers build this boundary at the same time without talking, so every question they could answer differently is answered here once: that marking and correcting are one `PATCH` whose absent fields are never written, which is what lets a correction and a marking sent at the same moment both stick (`BR-10`, race `W-1`) and makes a marking set the chosen state instead of flipping the stored one (`BR-09`, race `W-2`); that a missing task answers `404` and is never created again (`BR-13`, race `W-3`); that the list is one envelope holding every task in one total order with no parameters (`BR-11`); and that a task's text is refused with one of three codes a caller can branch on, in the order `BR-07` fixes, because the requirements demand a reason of its own for a line break (`R-2` clause 6, `Q-11`) and the scenarios tell "no text", "too long" and "more than one line" apart (`S-6`, `S-8`, `S-33`), which the integration corpus test proves on the wire and which FastAPI's list of Pydantic errors cannot do in words this contract owns. The standing rule of § Refusals — a stable code, a finished sentence, a status code with two shapes published as two — is applied to the new resource rather than restated.
  **ADR:** required — design-adr drafts it. Decision: every refusal of a task's text is a coded refusal in the `Refusal` envelope, decided outside Pydantic's field constraints (the published `TodoTaskCreate.text` is a required string with no `minLength` or `maxLength`), which departs from the guestbook's convention of answering an empty or over-long field with FastAPI's list. Rejected: (1) the guestbook's convention, bounds as `Field(min_length, max_length)` — no code this contract owns, only Pydantic's own type strings, and the length constraint answers before any later check sees the text, so a 201-code-point text with a line break would be called too long, the opposite of `BR-07`; (2) custom Pydantic error types raised from a schema validator — a code we own, but inside the list shape, which `frontend/src/api/problem.ts` reduces to its `msg` so the screen could not branch on it, and outside every router module, where the contract gate looks for each `x-refusals` literal, so the codes would be frozen by nothing; (3) a handler in `app/core/errors.py` that turns Pydantic errors into coded refusals — domain knowledge in the framework module that by rule knows nothing about the domain. This is not the router re-validation the guestbook's 2026-09-16 decision rejected: the rule is the context's (`BR-06`, `BR-07`), it is decided where business rules are decided, and the router only translates, which is `spec/design/conventions.md` § Layers as written; and the three codes exist because a requirement asks for three reasons, not to make a declaration come true. Cross-cutting (router, service, frontend adapter, black-box steps) and expensive to reverse (removing a stable code is a breaking change and a major version of the contract). Also taken here, none of them an ADR because each follows a convention in force or reverses in one file: one `PATCH` with optional fields rather than two sub-resources (`PUT …/done`, `PUT …/text`) — the guestbook's `PATCH` is the shape in force, and a future field is then an optional addition rather than a new endpoint, while a toggle endpoint was never open because `BR-09` forbids a flip; no read of one task, because no requirement reads one; `created_at` on the wire, rejected alternative leaving it off, because `BR-08` and `BR-11` make two promises about it that nobody could check otherwise; `{items, total}` although the list has no pieces, rejected alternative a bare array, because adding the count later breaks every caller.
  **Requirements:** CR-2609-823a/R-1, CR-2609-823a/R-2, CR-2609-823a/R-3, CR-2609-823a/R-4, CR-2609-823a/R-6, CR-2609-823a/R-7, CR-2609-823a/R-8, CR-2609-823a/R-9, CR-2609-823a/R-10, CR-2609-823a/R-11

- `ADDED` `contracts/openapi/todo_list.yaml`
  **Why:** Article VI of the constitution makes the contract the authority at a boundary and the code the thing validated against it, and `contracts/README.md` makes every `/api/*` path the application serves fall under a prefix some contract claims — so the moment `/api/todo-tasks` is served without this file, `./scripts/contracts.sh` goes red on an unclaimed boundary, and the frontend's generated types would describe whatever the Pydantic dump happened to say. The file freezes the two paths, the four operations with every status each answers, the four shapes (with `TodoTaskUpdate`'s optional fields frozen by existence only, as the guestbook's are), and the five codes under `x-refusals`, which is the only place a code is held still because FastAPI never puts one in `openapi.json`. It defines `Refusal`, `RefusalDetail`, `HTTPValidationError` and `ValidationError` again instead of referencing `guestbook.yaml`, because the guestbook is deleted as a unit and a contract that cannot be read without it would break on that day; the dump has one schema of each name, so the gate holds both copies to one definition.
  **ADR:** required — the same decision as the entry above (the text's refusals as codes rather than schema constraints), which is why no `minLength` or `maxLength` is frozen on `text`; the rest follows `contracts/openapi/README.md` as written.
  **Requirements:** CR-2609-823a/R-1, CR-2609-823a/R-2, CR-2609-823a/R-3, CR-2609-823a/R-4, CR-2609-823a/R-6, CR-2609-823a/R-7, CR-2609-823a/R-8, CR-2609-823a/R-9

- `MODIFIED` `contracts/openapi/README.md` — the **Contracts:** line
  **Was:** "`guestbook.yaml` (guestbook entries, `/api/guestbook-entries`) and `health.yaml` (the `/api/health` probe). Compatibility mode of both: **Backward**".
  **Now:** it names `todo_list.yaml` (the to-do list's tasks, `/api/todo-tasks`) between the two, and says the compatibility mode of all three is **Backward**.
  **Why:** The README is where a contract directory says what it holds and which compatibility mode each contract carries, and a reader deciding whether the to-do contract may be deployed before the code or after it looks there first. A third file that the line does not name reads as a file nobody declared, and "both" would then be a false count in the one sentence the directory uses to introduce itself.
  **ADR:** none — the line records a contract this change adds and repeats the mode the new file declares in its own header; no rule moves.
  **Requirements:** CR-2609-823a/R-1, CR-2609-823a/R-3

<!-- z spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/architecture.md -->
- `MODIFIED` `spec/design/architecture.md` — § What this is, and for whom (one paragraph
  added); § Contexts and their boundaries (the lead sentence, one table row, the diagram);
  § Rules between contexts (the lead-in paragraph, two bullets extended by one clause each);
  § What a new environment starts with (three paragraphs); § What a new feature adds (the
  Screen row, the paragraph on a second context); § The to-do list — where each rule lives
  (added, with four subsections)
  **Was:** "one deliberately trivial example feature: a guestbook"; "One domain context and one
  supporting technical slice", one row, one context node; "One domain context has nothing to
  border on, so today this section only says where the boundary **will** be"; a new environment
  filled when "the guest book" is empty, and "It will not seed a guest book that already has
  entries … one `GET`"; "the only files two contexts share are `app/api.py`,
  `app/contexts/__init__.py` and `frontend/src/router.tsx` … three places"; no placement for a
  second context anywhere.
  **Now:** the to-do list stands beside the example and survives its deletion; two contexts in
  the table and the diagram, both joined to Platform by the shared kernel; the boundary exists
  and its code belongs to neither context (`app/platform/schemas/text.py`, `frontend/src/lib/`);
  each list is filled on its own, a task added and then marked, one `GET` per list; four shared
  files with one appended line each, plus the frame and the seeder when a context has a screen or
  seed data; and a section giving the layer per rule for `BR-06`…`BR-13` and the three
  requirements no context owns, every file with its tree and its writer, the builders' pairwise
  intersections written out and empty, the three data edges that cross them, and the fitness
  tests that hold each boundary.
  **Why:** The to-do list is the second bounded context, and four sentences of this document became false the moment `spec/contexts/todo_list.md` was written: the system has two features, two contexts, a boundary with a declared pattern, and more than three shared files. The placement section is what lets the two implement waves run in parallel — design-plan turns its rows into tasks and the builders' allowlists are checked against it — and it has to exist before any code does, because a builder deciding its own layout is how a rule lands in a router or a second copy of the text rule appears in a context's folder. The seeding paragraphs record `Q-10` (each list filled on its own) and `Q-12` (at least one example done, reached by marking) where the filling rule already lives, instead of in a second home.
  **ADR:** none — every placement applies a rule this repository already holds: one file per layer under the context (`conventions.md` § Backend and § Frontend), the bound and the set beside the model (§ Rules between contexts), the browser text rule moving up to `frontend/src/lib/` on the day a second context needs it (`conventions.md` § Frontend, in those words), navigation in the frame (`ui/system-states.md` § One column), seeding through the API (§ What a new environment starts with, decision of 2026-09-05). The decision this layout follows — a to-do list context of its own, joined by a shared kernel — is the ADR `design/delta/domain.md` marks as required. The individual choices and their rejected alternatives are under § Decisions below.
  **Requirements:** CR-2609-823a/R-1, CR-2609-823a/R-2, CR-2609-823a/R-3, CR-2609-823a/R-4,
  CR-2609-823a/R-5, CR-2609-823a/R-6, CR-2609-823a/R-7, CR-2609-823a/R-8, CR-2609-823a/R-9,
  CR-2609-823a/R-10, CR-2609-823a/R-11

<!-- z spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md -->
- `MODIFIED` `spec/invariants.md` § Deliberate non-goals, "Authentication and authorisation" and
  "A data retention policy"
  **Was:** "anybody may add, amend and delete any entry", and "An entry lives until somebody
  deletes it." Both were the guestbook's noun, written when an entry was the only thing the
  system stored.
  **Now:** "anybody may add, amend and delete anything the system stores: any guestbook entry and
  any to-do task.", and "An entry, like a to-do task, lives until somebody deletes it."
  **Why:** COH-requirements-5. `requirements.md` § Non-Goals cited both standing non-goals as
  covering tasks while their wording covered entries alone ("by intent yes, by wording no",
  Self-check 23). The authentication half: the user confirmed the intent at the `Q-9` read-back
  (`brainstorm.md` § Deliberately out of scope: the standing non-goal "holds for the to-do list as
  it does for the guestbook: anybody may add, tick, edit and delete any task"). The retention
  half: the first convergence round left it worded for entries, because no user decision then
  extended it to tasks and `requirements.md` carried it as assumption `A-2` ("nothing removes a
  task except a person deleting it, with no expiry and no retention policy, as for a guestbook
  entry"). The user approved `requirements.md` at the stage gate on 2026-09-24, and that document
  says of its named assumptions that "the user confirms or overrules each one at the approval of
  this document"; none was overruled, so `A-2` is a human decision and the retention item now
  names tasks too. Neither rewording lifts anything, so neither gains a "lifted by" line.
  **ADR:** none — it rewords two standing non-goals so that they name what the system now stores,
  and it lifts nothing and adds no rule.
  **Requirements:** CR-2609-823a/R-1, CR-2609-823a/R-4, CR-2609-823a/R-6, CR-2609-823a/R-7

- `MODIFIED` `spec/design/conventions.md` § Layers: one paragraph added after the paragraph on how a router translates a domain exception
  **Was:** § Layers put "business rules" in `services/` and "Pydantic request and response contracts" in `schemas/`. § Backend named the guestbook the worked example through every layer, and the guestbook holds its `BR-01` bounds as schema constraints. Nothing said which of the two a bound that is also a business rule follows.
  **Now:** "A rule whose refusal carries a code of its own is judged in `services/`, and `schemas/` holds no part of it." The request shapes carry the field with no bound. The service raises one domain exception per verdict, and the router translates each one into its coded refusal. The guestbook is the worked example of a bound refused with no code, not of every bound. A to-do task's text is named as such a rule, with the user's words.
  **Why:** COH-design-1 and COH-design-2. design-api followed the sentence: it made the task's three text refusals coded and decided outside the schema. design-architecture followed the worked example: it held `BR-06` and `BR-07` in the schema's text type, where FastAPI's list answers with no code. So the frozen contract, the screen's per-code messages and the router tests contradicted the placement build-backend was handed. testing.md also declared a red-first case, `test_the_create_and_update_shapes_give_every_case_the_same_verdict`, that only a rejected design could turn green. The user decided `Q-17` = A: "The service checks it, with a coded reason".
  **ADR:** none. The decision is carried by design-adr's draft `task-text-refusals-are-coded-not-schema-constraints.md`. This paragraph states the placement rule that follows from it, in the document where placement rules live (constitution, Article IX).
  **Requirements:** CR-2609-823a/R-2, CR-2609-823a/R-6

- `MODIFIED` `spec/design/conventions.md` § Frontend — where a file goes: the item on the shared `lib/`, three sentences added
  **Was:** a context's rule "moves up here the day a second context needs it". Nothing was said about the rule's test, whose cases carry one context's bounds.
  **Now:** "Only the rule moves up." A test that proves the rule through one context's bounds stays beside that context's modules and changes one import. The corpus reader `frontend/src/contexts/guestbook/lib/entryText.test.ts` is one such test. The reason is that nothing in the shared `lib/` imports from `contexts/`.
  **Why:** COH-design-3. The architecture fragment moved `entryText.test.ts` up with the rule, to a `text.test.ts` beside `text.ts`. testing.md kept it in the guestbook's folder with one import line changed. The reader needs the guestbook's `AUTHOR_MAX_LENGTH`, `MESSAGE_MAX_LENGTH` and `QUERY_MAX_LENGTH`, and `tests/fitness/test_context_boundaries.py` refuses that import from a module outside every context. Settled automatically by this same section's rule that nothing in the shared `lib/` imports from `contexts/`.
  **ADR:** none. It states a consequence of a placement rule already in force, beside the rule.
  **Requirements:** CR-2609-823a/R-2

- `MODIFIED` `spec/design/conventions.md` § Backend — where a file goes: the item on a context's routers
  **Was:** "`guestbook` is the **only** domain context of this template and at the same time its worked example through every layer: copy it, and when your own context replaces it, delete it."
  **Now:** "`guestbook` is this template's worked example through every layer: copy it, and when your own context replaces it, delete it. The to-do list (`todo_list`) is a second domain context and is not an example."
  **Why:** COH-design-8. With `spec/contexts/todo_list.md` there are two domain contexts, and `spec/design/architecture.md` § Contexts and their boundaries already says so. This sentence and `spec/README.md` still counted one. The count sat inside a sentence about where routers go, so a new context made it false without touching routers, and no design author's write set held it. Settled automatically by the constitution, Article IV: a specification edit lands in the same pull request as the change it describes.
  **ADR:** none. It states a count this change makes true, and no rule moves.
  **Requirements:** CR-2609-823a/R-1

- `MODIFIED` `spec/README.md` § This directory describes a template: its first paragraph
  **Was:** "The only domain context is the **guestbook**, and it is deliberately trivial: four operations, one table, one screen. It exists so that …"
  **Now:** "The example domain context is the **guestbook**, and it is deliberately trivial: four operations, one table, one screen. The to-do list beside it is not an example and stays when the guestbook is deleted. The guestbook exists so that …" The pronoun became a name so that it keeps pointing at the guestbook.
  **Why:** COH-design-8, the second of its two sentences. Once the to-do list exists, "the only domain context" is false. `spec/contexts/todo_list.md` § Neighbours already says the to-do list stays when the guestbook is removed and takes the text rule with it. Settled automatically by the constitution, Article IV.
  **ADR:** none. It states a count this change makes true, and no rule moves.
  **Requirements:** CR-2609-823a/R-1

- `MODIFIED` `spec/design/architecture.md` § Who writes what, and where the sets meet: one paragraph added after the test authors' sets
  **Was:** the test authors' sets were described by tree and by shape ("the vitest files"). Nothing said which document decides a test author's files, or that the change's boundary has to name each of them.
  **Now:** testing.md decides which files a test author writes. The change's § This change owns covers each of them, by path or by a row that holds it, even when both documents are written in one wave. The paragraph names **frontend/src/router.test.tsx** as build-tests-frontend's, with the user's words.
  **Why:** COH-design-4. testing.md gave build-tests-frontend **frontend/src/router.test.tsx** as the only citing proof of `R-5` clauses 1 and 3. The architecture fragment's write set left it out, and so did its § This change owns, from which `set-boundary --from-design` records the boundary. That fragment wrote the test rows from a guess ("if testing.md puts R-5's proof there"). So the implement gate would refuse the file, or its author would drop it. The user decided `Q-18` = A: "Add the file to the change's list".
  **ADR:** none. It says who writes which file in this change, and reversing it edits one table.
  **Requirements:** CR-2609-823a/R-5

- `MODIFIED` `spec/contexts/todo_list.md`: the front matter's `screens` and `features`, and the paragraph on when the header claims them
  **Was:** `screens: []` and `features: []`, under "The header claims a screen and a black-box file only once they exist". That sentence said when a file is claimed, and not who claims it.
  **Now:** `screens: [spec/design/ui/todo-list.md]` and a `features` line that names the to-do list's Gherkin file under `e2e/suite/features/`. The paragraph says the design stage's convergence round writes both claims: the screen as soon as its document exists, and the black-box file at the end of design, before it exists. The plan declares `test_every_screen_and_feature_a_context_names_is_on_disk` red on the task that writes the file. The declaration expires when that task writes it in the first implementation wave.
  **Why:** COH-design-5 and COH-design-6. design-ui wrote the screen document (`S-02`) in this stage while the header claimed no screen, so `test_every_registered_screen_is_claimed_by_exactly_one_context` went red. Nothing declared that red, and no implement author could clear it. It was settled automatically by the constitution, Article X: a stage never ends red, except for a declared failure of a test written before its implementation. For the black-box file, testing.md left the timing unresolved. No implement author writes `spec/contexts/`, and every option leaves a structural red at a stage boundary. The user decided `Q-19` = A: "List it now, at the end of design".
  **ADR:** none. It is a claim in a context header and when it is written; reversing it edits two front-matter lines.
  **Requirements:** CR-2609-823a/R-1, CR-2609-823a/R-2, CR-2609-823a/R-3, CR-2609-823a/R-4, CR-2609-823a/R-5, CR-2609-823a/R-6, CR-2609-823a/R-7, CR-2609-823a/R-8, CR-2609-823a/R-9, CR-2609-823a/R-10

- `MODIFIED` `spec/design/testing.md` § CR-2609-823a, the to-do list, "Existing detectors that go red on the way": the third bullet replaced, and a last bullet added
  **Was:** the third bullet declared `test_every_feature_file_is_claimed_by_exactly_one_context` red "from the test wave, when **e2e/suite/features/todo_list.feature** appears, until `spec/contexts/todo_list.md` claims it", and ended "**Unresolved, and handed to the coherence gate.**" The list was scoped to "structural cases" and said nothing of the contract gate.
  **Now:** the third bullet names `test_every_screen_and_feature_a_context_names_is_on_disk`. It is red since the convergence round claimed the feature file before the file exists (`Q-19`), and it is declared on build-tests-e2e's task in the first implementation wave. The two claim cases stay green, because the header claims both files. A last bullet names `./scripts/contracts.sh`, a gate of `./scripts/check.sh`. It is red since `contracts/openapi/todo_list.yaml` exists, with 11 findings, and green when build-backend's schemas and routers exist. No `**Must be red:**` line can name a gate, so the design boundary and each implementation boundary before build-backend's wave accept `check` red on that gate alone, with that bullet as the reason. The user's words close it.
  **Why:** COH-design-9 and COH-design-10. The claim case walks the feature files on disk and finds each one claimed once, so it cannot go red when the file appears. The on-disk case is the one `./scripts/test.sh fitness` shows red now. A plan built from the old bullet would have declared a red that never occurs, which the gate refuses, and left the real one undeclared. That half was settled automatically by the constitution, Article X: a deliberate red is declared before the run that shows it and must be proved to have occurred. The contract gate's red was recorded only in design-api's fragment, which nothing reads when the reds are planned, and the engine accepts a declared red only as a junit case, which no contract finding is. The user decided `Q-21` (1) = A: "record that in the test plan and sign it off by name at each stage end until the backend exists".
  **ADR:** none. Which cases are declared red, and when, is testing.md's to hold (constitution, Article IX).
  **Requirements:** CR-2609-823a/R-1, CR-2609-823a/R-2, CR-2609-823a/R-3, CR-2609-823a/R-4, CR-2609-823a/R-6, CR-2609-823a/R-7, CR-2609-823a/R-8, CR-2609-823a/R-9

- `MODIFIED` `spec/design/testing.md` § CR-2609-823a, the to-do list, "The witness for a task's text": its first sentence
  **Was:** "`data-model.md` calls for a data invariant of the to-do list's own … and the convergence round writes it." `data-model.md` carried no such call. The round that had run neither wrote the invariant nor mentioned it.
  **Now:** it cites `spec/design/data-model.md` § `todo_tasks`, which now carries the call. It names the convergence round of the `spec_sync` stage as the writer, the first round after the witnesses exist, since `tests/fitness/test_invariant_witnesses.py` refuses a witness that does not.
  **Why:** COH-design-16. The witnesses are test files the implementation stage writes, so no design-stage round could write the invariant green, and no implementation author writes `contracts/`. The user decided `Q-21` (6) = A: "stated in the data model now and written into the data-rules folder at the reconciliation stage, once its tests exist."
  **ADR:** none. It names when an existing route runs.
  **Requirements:** CR-2609-823a/R-2, CR-2609-823a/R-6

- `MODIFIED` `spec/design/testing.md` § Fitness functions, the row `test_migration_safety.py`
  **Was:** "the one revision creates its table and its index together".
  **Now:** "each of the two revisions creates its table and its index together".
  **Why:** COH-design-17. `spec/design/data-model.md` § Migrations counts two revisions once `todo_tasks` has its own. The two rules stay vacuous, and the count was false. Settled automatically by the constitution, Article IV: the specification edit lands with the change that makes it true.
  **ADR:** none. It is a count this change makes true.
  **Requirements:** CR-2609-823a/R-1

- `MODIFIED` `spec/design/ui/guestbook.md` § Data: one paragraph added after the table
  **Was:** the table named the posting and amending hooks and not what they send. The rule lived only in the code, in `frontend/src/contexts/guestbook/components/EntryComposer.tsx` ("what is sent should be what the browser measured") and `frontend/src/contexts/guestbook/components/EntryCard.tsx`.
  **Now:** "What is posted and amended is the text the screen judged, not the text as typed." Each field is sent as the shared text rule leaves it, normalized and trimmed, so the browser and the service measure the same value.
  **Why:** COH-design-11. The worked example said nothing about its payload. design-ui wrote the to-do screen's add as "sends `text` as typed", and design-testing gave the composer the case "sends the text as the shared rule leaves it". build-frontend would have met a test its builder may not edit. The user decided `Q-21` (2) = A: "Adding a task sends the text cleaned up the same way the screen checked it, as the guestbook does, instead of exactly as typed".
  **ADR:** none. It writes down what the worked example already does.
  **Requirements:** CR-2609-823a/R-1

- `MODIFIED` `spec/design/ui/todo-list.md` § Data, the adding row
  **Was:** "sends `text` as typed".
  **Now:** "sends `text` as the shared rule leaves it — normalized and trimmed, the text the screen judged".
  **Why:** COH-design-11, the artefact half of the entry above, from the ready patch under the finding.
  **ADR:** none.
  **Requirements:** CR-2609-823a/R-1

- `MODIFIED` `spec/design/conventions.md` § Layers: the paragraph on a rule whose refusal carries a code of its own
  **Was:** "A rule whose refusal carries a code of its own is judged in `services/`, and `schemas/` holds no part of it." It did not say whether a refusal about the request as a whole is such a rule. Nor did it say whether importing the bound or the kernel counts as holding part of the rule.
  **Now:** the sentence speaks of "a rule about a field's value". A refusal about the request as a whole, a `PATCH` that sets no field, is decided beside the endpoint before the service is called (`spec/design/api.md` § Shapes, `GuestbookEntryUpdate`). "Holding no part of the rule means importing none of it": the service's judgement imports the bound and the kernel's `normalize` and `length`, and `schemas/` imports neither. The user's words for both edges close the paragraph.
  **Why:** COH-design-12 and COH-design-13. Read literally, the sentence pulled `todo_task_empty_patch` into the service, while `spec/design/architecture.md` left it to the router, as the guestbook's router decides its own empty patch. And `spec/design/data-model.md` and the architecture fragment had the to-do schemas import the bound and the kernel. That can come true only through a use the paragraph forbids, or through a use nothing needs, and ruff's `F` rule removes an unused import. The user decided `Q-21` (3) and (4) = A.
  **ADR:** none. It narrows a placement rule to the case it was written for, in the document where placement rules live (constitution, Article IX).
  **Requirements:** CR-2609-823a/R-2, CR-2609-823a/R-6

- `MODIFIED` `spec/design/architecture.md` § The to-do list — where each rule lives, "The layer per rule": one sentence appended to the router paragraph
  **Was:** the router translated "the not-found refusal and the three about a task's text". Nothing placed `todo_task_empty_patch`.
  **Now:** "It answers `todo_task_empty_patch` itself, before it calls the service, as the guestbook's router answers its empty patch."
  **Why:** COH-design-12, the artefact half of the entry above, from the ready patch under the finding.
  **ADR:** none.
  **Requirements:** CR-2609-823a/R-4, CR-2609-823a/R-6

- `MODIFIED` `spec/design/data-model.md` § `todo_tasks`: one paragraph added after the column table, and one clause changed in "The bound, beside the model"
  **Was:** the section called for no data invariant on a task's text, and said "the column is declared from it and the schemas import it".
  **Now:** "Every `text` in this table is NFC, trimmed at both ends, 1 to 200 code points and one line: a data invariant of the to-do list's own under `contracts/invariants/`, the counterpart of `D-04`", with its witnesses named in testing.md. And "the column is declared from it and the service's judgement of a text imports it; the schemas do not".
  **Why:** COH-design-16: testing.md cited a call this document did not carry, and the user decided `Q-21` (6) = A. COH-design-13: the import contradicted § Layers, and the user decided `Q-21` (4) = A: "The request formats import no part of the text rule; the service does."
  **ADR:** none.
  **Requirements:** CR-2609-823a/R-2, CR-2609-823a/R-6

- `MODIFIED` `spec/invariants.md` § Data invariants: one paragraph added after "The editing route has not changed"
  **Was:** the section gave every edit to `contracts/` within a change to the convergence round, and did not say which stage's round.
  **Now:** "Which stage's convergence round writes a new data invariant is settled by its witnesses." An invariant decided in design, whose witnesses the implementation stage writes, is written by the first convergence round after they exist, which is the `spec_sync` stage's. Until then the design document that decided it states the call, and `spec/design/testing.md` names its witnesses and that round. The user's words close it.
  **Why:** COH-design-16, its ambiguity source. testing.md said "the convergence round writes it", and design-data assumed the same. The design round that ran did not write it, and could not have: `tests/fitness/test_invariant_witnesses.py` refuses a witness that does not exist, and the witnesses are written in implementation. The user decided `Q-21` (6) = A.
  **ADR:** none. It states when an existing route runs, and no rule about the data moves.
  **Requirements:** CR-2609-823a/R-2

- `MODIFIED` `contracts/README.md` § Why a contract is written rather than generated
  **Was:** "for this template that is three paths, six operations and eight schemas".
  **Now:** "for this template that is five paths, ten operations and twelve schemas".
  **Why:** COH-design-18. `contracts/openapi/todo_list.yaml` adds two paths, four operations and four schemas (`TodoTaskCreate`, `TodoTaskUpdate`, `TodoTaskRead`, `TodoTaskList`), counted on the old figure's own convention. `./scripts/contracts.sh` prints "3 contracts, 5 paths, 10 operations". Settled automatically by the constitution, Article IV.
  **ADR:** none. It is a count this change makes true.
  **Requirements:** CR-2609-823a/R-1, CR-2609-823a/R-3

- `MODIFIED` `spec/design/ui/system-states.md` § Interactions: one paragraph added after the table
  **Was:** the table said the header links navigate "without a reload" and did not say whether the screen they open reads its list again. Only `spec/design/ui/todo-list.md` § Interactions spoke of reading ("Opening the to-do list's own address, or reloading it → the list is read"), and the 30 seconds a cached list is shown lived in a comment in `frontend/src/main.tsx` alone.
  **Now:** "Opening the to-do list reads its list, every time — the header link included." The screen shows the tasks as stored at that moment, never a copy it read earlier, with the user's words. The guestbook is unchanged: opened by a link within 30 seconds of its last read, it shows that read, and a reload or a change made on it reads it afresh.
  **Why:** COH-implement-1. `requirements.md` § R-3 clause 5 and `todo-list.md` promise what is stored "at that moment", and `uat.md` step 14 expects a header link to show a seeding done seconds before. The to-do query inherits `staleTime: 30_000` from `main.tsx`, and TanStack Query refetches on mount only stale data, so a header link opened within 30 seconds shows the old read. The requirement and the UAT author both read "opening" as "reading" because this section, which owns the header links, was silent. The user decided `Q-25` = A: "Always fetch the latest."
  **ADR:** none. It states what one screen does when it is opened; reversing it edits one query option and this paragraph.
  **Requirements:** CR-2609-823a/R-3

- `MODIFIED` `spec/design/architecture.md` § Who writes what, and where the sets meet: one paragraph added after the paragraph on the test authors' files
  **Was:** the corpus was handed out by directory, `golden-set/seed/` to build-backend and `golden-set/fixtures/` to the integration test author. Nothing said who writes `golden-set/README.md`, the document beside them, or what a change does when its corpus files make that document false.
  **Now:** "`golden-set/README.md`, the corpus's rules document, is in no member's set." A change whose corpus files make a sentence of it false names each such sentence in its pull request, and a documentation-only pull request corrects them after it. The paragraph names the five sentences the to-do list's files made false, cites template issue #92, and closes with the user's words.
  **Why:** COH-implement-2. This stage wrote four fixtures, `golden-set/seed/todo-tasks-example.json` and a second browser reader, and five claims of `golden-set/README.md` became false. `testing.md` cites that README as what every corpus file owes, yet no member of this change may write it: the design fragment found it ownerless, `tasks.md` left it open, and the fix needs a stack-profile change this change cannot make (`PROC-18`, filed as template issue #92). The user decided `Q-26` = A: "Fix it in a follow-up."
  **ADR:** none. It records who writes one file and when; the lasting fix is the template's (issue #92).
  **Requirements:** CR-2609-823a/R-2, CR-2609-823a/R-11

- `MODIFIED` `spec/README.md` § This directory describes a template: the deletion list
  **Was:** "Deleting the example deletes with it: … both halves of the corpus `golden-set/`". `CLAUDE.md` § What is an example, and what is the template carried the same list.
  **Now:** "the guestbook's files in both halves of the corpus `golden-set/` (never the to-do list's `todo-task-text.json` and `todo-tasks-*.json`)". `CLAUDE.md` received the same replacement; it lies outside `spec/` and `contracts/`, so it needs no entry of its own, and it is named here so that the two lists are read as one edit. The ready patch set the exception off with a dash; it stands in parentheses, because a dash inside a comma-separated list would leave where the list resumes unclear.
  **Why:** COH-implement-3. This stage put five of the to-do list's files in `golden-set/`: four fixtures and the example tasks. Followed as written, both lists deleted them with the guestbook, and three to-do suites would lose the files they read. The same section already says the to-do list stays when the guestbook is deleted, and `scripts/seed_golden_set.py` and `./scripts/seed.sh --help` say its example tasks stay. The lists named a directory, which was accurate only while every corpus file was the guestbook's. Settled automatically by the constitution, Article IV: the specification edit that describes a fact this change creates lands in the same pull request.
  **ADR:** none. It narrows a deletion list to the files that are the example's.
  **Requirements:** CR-2609-823a/R-2, CR-2609-823a/R-11

- `MODIFIED` `spec/design/testing.md` § Four file sets, disjoint: one paragraph added after the rule that every path stands in one set, and two cells of the to-do list's table extended
  **Was:** the rule named every path the architecture creates or modifies, and the table listed each edit a test author makes to an existing test. Neither said whether a test whose docstring the change makes false is such an edit when no assertion moves, and the table named none of the five files concerned.
  **Now:** "An existing test whose prose the change makes false stands here too, even when no assertion moves." Such a docstring is edited, text only, by the author whose tree holds the file. build-tests-unit's cell names the docstrings of `test_context_declarations.py`, `test_context_boundaries.py`, `test_data_invariants.py` and `test_migration_safety.py`. build-tests-integration's cell adds the docstring of `test_migrations.py` that called the guestbook's screen the only one.
  **Why:** COH-implement-4. § Fitness functions, in the same document, was corrected at design: the context sweeps "were vacuously true while there was one context", `todo_tasks` made the data-invariant sweeps real, and the migration-safety row counts "each of the two revisions" (COH-design-17). The five tests' docstrings still said the opposite in the present tense, because no write set carried the move into their prose. Article IX keeps a check's intent in its docstring, so a reader would take a real red for a synthetic one. Settled automatically by the constitution, Article I: code contradicting `spec/` is a defect in the code.
  **ADR:** none. Which author edits which test is testing.md's to hold (constitution, Article IX).
  **Requirements:** CR-2609-823a/R-1

- `MODIFIED` `spec/design/architecture.md` § The files: one row added after the row for the three guestbook modules
  **Was:** the row for the three guestbook modules ended "nothing else about the guestbook moves", which froze the guestbook's frontend for its behaviour and made no exception for prose the second screen made false.
  **Now:** a row for `contexts/guestbook/pages/GuestbookPage.tsx`, written by build-frontend: "the one exception to 'nothing else moves', and prose alone". The line of its module docstring that called `S-01` the only screen names it one of two; nothing the screen does moves.
  **Why:** COH-implement-5. `GuestbookPage.tsx`:30 says "`S-01` -- the only screen in this application", while `spec/design/ui/system-states.md` § One column says the application has two screens. T-22 corrected the frame's docstrings, but the freeze kept this file out of every task. Article IX makes module docstrings cite the specification. Settled automatically by the constitution, Article I.
  **ADR:** none. It is one line of prose in one file, and nothing on screen changes.
  **Requirements:** CR-2609-823a/R-5

- `MODIFIED` `spec/design/testing.md` § CR-2609-823a, the to-do list, "Existing detectors that go red on the way": the lead sentence and the third bullet
  **Was:** "each is declared on the task whose product closes it", and the on-disk case "declared on build-tests-e2e's task, whose product is the file, in the first implementation wave".
  **Now:** each "was declared red on the task that turned it red or, when it already stood at the design close, accepted by name at that boundary (`CR-2609-823a`, `Q-24`) and carried as a baseline red". The task whose product closes it names it under **Turns green:** in `tasks.md`. The on-disk case was "accepted by name at the design close (`Q-24`), and turned green by build-tests-e2e's feature file in the first implementation wave".
  **Why:** COH-implement-6. `tasks.md` carried the on-disk case (T-11) and the context-boundaries case (T-14) as baseline reds, accepted by name when the design stage closed (`Q-24`, recorded in the session trace as the reds accepted at the design boundary). The seed-file cases were declared on T-10 and T-4, the tasks that turned them red. This section described a red that starts inside the design stage as if it started inside implementation, although a red standing at the design close cannot be declared on a task of a plan not yet written (constitution, Article X). Its fourth bullet already said so for `./scripts/contracts.sh`; the fitness cases had no such sentence. The user decided `Q-27` = A: "Yes, record what happened."
  **ADR:** none. It records how two reds were carried; the mechanism is the engine's.
  **Requirements:** CR-2609-823a/R-1, CR-2609-823a/R-2, CR-2609-823a/R-3, CR-2609-823a/R-4, CR-2609-823a/R-6, CR-2609-823a/R-7, CR-2609-823a/R-8, CR-2609-823a/R-9, CR-2609-823a/R-10

- `MODIFIED` `spec/contexts/todo_list.md`: the paragraph on when the header claims a screen and a black-box file, its last two sentences
  **Was:** "so that early claim is a declared red and not a silent one: the plan declares `test_every_screen_and_feature_a_context_names_is_on_disk` red on the task that writes the file. The declaration expires when that task writes the file in the first implementation wave."
  **Now:** "so that early claim is a named red and not a silent one: `test_every_screen_and_feature_a_context_names_is_on_disk` was red from the design close, accepted by name at that boundary (`CR-2609-823a`, `Q-24`), and went green when the first implementation wave wrote the file." The ready patch landed as written; "declared" became "named" in the clause before it, because this repository keeps "declared" for a red named on a task before the run that shows it (constitution, Article X), which is the reading this finding corrects.
  **Why:** COH-implement-6, the second of the two documents its decision names. The paragraph said the plan declared the red on a task, while `tasks.md` T-11 says "It is not declared" and carries it as a baseline red accepted at the design close. The user decided `Q-27` = A: "Yes, record what happened."
  **ADR:** none. It records how one red was carried.
  **Requirements:** CR-2609-823a/R-1, CR-2609-823a/R-2, CR-2609-823a/R-3, CR-2609-823a/R-4, CR-2609-823a/R-5, CR-2609-823a/R-6, CR-2609-823a/R-7, CR-2609-823a/R-8, CR-2609-823a/R-9, CR-2609-823a/R-10

- `MODIFIED` `spec/design/ui/system-states.md` § Interactions: the paragraph on opening the to-do list, its second sentence reworded and three sentences added
  **Was:** "the screen shows the tasks as they are stored at that moment, other people's changes of the last few seconds included, and never a copy it read earlier". Nothing said what is drawn while the read made on opening is under way.
  **Now:** "the screen reads its list afresh and shows the tasks as they are stored at that moment, other people's changes of the last few seconds included." Then: "A list it read earlier in the same tab stays on screen only until that read answers, and is then replaced; it is not swapped for the loading outline meanwhile." The user's words follow, and a reload and an entered address are named as having no earlier list to show.
  **Why:** COH-implement-7. The paragraph promised "never a copy it read earlier". The code written for it (`useTodoTasks.ts`, `staleTime: 0` alone) keeps a cached list for TanStack Query's default five minutes and draws it, as a success, until the fresh read answers. So a to-do list left and reopened by its header link first shows the list it read before. `requirements.md` § R-3 clause 5, "SHALL show the tasks exactly as they are stored at that moment", said what is shown once the list is read, not while the read is under way: the convergence round of pass 7 read it as "nothing else is ever shown", build-frontend as "a read is always made". The user decided `Q-28` = A: "Briefly showing it is fine." The code stays as it is.
  **ADR:** none. It states what one screen draws for the length of one read; reversing it is one query option (`gcTime: 0`) and this paragraph.
  **Requirements:** CR-2609-823a/R-3

- `MODIFIED` `spec/design/testing.md` § CR-2609-823a, the to-do list: the `CR-2609-823a/R-3` row, one proof added after the `TodoListPage.test.tsx` entry
  **Was:** the row proved clause 5 only through "A task somebody else added appears after a reload", and named no case for the header link that `Q-25` made read the list again.
  **Now:** "**frontend/src/router.test.tsx** (the to-do list opened a second time by its header link is read again and shows what is stored then, under a query client with `frontend/src/main.tsx`'s defaults, so that the case fails if the list inherits their 30 seconds …)", closed by the user's words.
  **Why:** COH-implement-8. The convergence round of pass 7 wrote `Q-25` into `system-states.md` and sent the code to build-frontend and the UAT line to build-tests-uat, and sent nothing to a test author. Every query client the tests build takes TanStack's default `staleTime` of 0, the UI smoke asserts headings and addresses, and UAT step 15 shows the same task whether or not the list is read again. So the one line that carries `Q-25` could be deleted with every suite green, while `uat.md` says the suites prove all of `R-1` to `R-10`. The user decided `Q-29` = A: "Add an automated test". The case is build-tests-frontend's to write afterwards, in a file already in its cell.
  **ADR:** none. Which suite proves a decision is testing.md's to hold (constitution, Article IX).
  **Requirements:** CR-2609-823a/R-3

- `MODIFIED` `spec/design/testing.md` § Four file sets, disjoint: three cells of the to-do list's table
  **Was:** the cells named the five files of COH-implement-4 whose docstrings counted one. build-tests-unit's cell gave `tests/unit/test_guestbook_entry_model.py` for its assertion alone ("the schema holds two tables"), and `tests/integration/test_e2e_reset.py` and `e2e/suite/steps/guestbook_steps.py` stood in no cell.
  **Now:** build-tests-unit's cell reads "(the schema holds two tables, in an assertion and in the docstring that counted one)". build-tests-integration's cell adds "`tests/integration/test_e2e_reset.py` (text only: the comment on `REQUIRED` that counted one table)". build-tests-e2e's cell adds "text only, `e2e/suite/steps/guestbook_steps.py` (the comment on `ENTRIES` that counted one resource)". Two joins became commas, so that each list keeps a single "and".
  **Why:** COH-implement-9. The rule this section gained in pass 7 names a class of prose, a docstring that states a count the change alters, while its cells named a closed list drawn from COH-implement-4's grep over `tests/fitness/` and `tests/integration/test_migrations.py` alone. Three more comments still counted one: "The template's schema is one table and no edges", "The one table in this application's schema that holds a scenario's state" and "The one resource this suite drives". `spec/design/data-model.md` and `spec/design/api.md` say two tables and two resources. Settled automatically by the constitution, Article I: code contradicting `spec/` is a defect in the code. `guestbook_steps.py` lies outside the recorded boundary and under the architecture fragment's freeze of the guestbook's steps, so this round also adds its row to § This change owns below and states the one-comment exception where that freeze lives. The three edits are their authors' to make afterwards.
  **ADR:** none. Which author edits which test is testing.md's to hold (constitution, Article IX).
  **Requirements:** CR-2609-823a/R-1

<!-- z spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/data-model.md -->
- `MODIFIED` `spec/design/data-model.md` — the opening paragraph; § `guestbook_entries` (its first line); § `todo_tasks` (new, with its subsection Two writers on one task); § Indexes and uniqueness (one row, two paragraphs, one phrase); § Migrations (one row, the sentence naming the head, and the new subsection The revision that creates `todo_tasks`); § Compatibility mode (one paragraph after the history)
  **Was:** One table, `guestbook_entries`, called "The only table", with the context rules cited from `spec/contexts/guestbook.md` alone; one index; "One revision, and it is the head"; an unindexed order described as a full sort "every time the only screen is opened"; the compatibility history naming only the initial revision.
  **Now:** A second table, `todo_tasks` — `id` `Uuid` primary key issued by the application, `text` `String(200)`, `done` `Boolean`, `created_at` `DateTime(timezone=True)`, all `NOT NULL`, no server default, no relation to anything — with what is deliberately not a column, why the text is `String(200)` and the state a boolean (each with its rejected alternatives), the constant `TODO_TASK_TEXT_MAX_LENGTH = 200` beside the model, the statement shape through which the store holds `BR-10` (column-scoped single-statement writes under the row lock at `READ COMMITTED`, each naming only the columns the person changed, no read before them, no upsert) with the three read-then-writes it protects, and the one rule the store does not hold (filling an empty list); the index `ix_todo_tasks_created_at_id` on (`created_at`, `id`) serving `ORDER BY created_at DESC, id DESC`; no uniqueness constraint, on purpose (`BR-12`); the revision as ordered `upgrade()` and `downgrade()` operations with its parent the head at the time of implementation; its mode declared `backward compatible`. The guestbook's first line and the intro name two tables and two context documents; "the only screen" became "the screen that reads it".
  **Why:** The to-do list stores something no table holds — a task with a text, a state switched both ways and a moment of adding (`R-1`, `R-3`, `R-4`, `R-6`) — and `spec/contexts/todo_list.md` declares `owns: [todo_tasks]`, which `tests/fitness/test_context_declarations.py::test_every_table_a_context_owns_is_declared_by_the_data_model` refuses until this register carries a `## todo_tasks` heading. The concurrency half is the part that matters most: `R-9` clause 2 and race `W-1` say an edit and a mark on one task must both stick, `BR-10` says "No check made before the write can hold it; the data model names the mechanism that does", and the only update path in the codebase today reads the row first (`app/contexts/guestbook/services/guestbook_entries.py`, `update_entry`). Without a named statement shape two implementers would each pick one, and a whole-row write-back passes every sequential test. No "at most one" rule exists — `BR-12` makes the same text twice two tasks — so the preflight's mechanism (a unique constraint or a partial unique index) has nothing to hold, and the document now says so rather than staying silent. Four existing sentences became false the moment a second table exists ("The only table", the context citation, "One revision, and it is the head", "the only screen"), and each is corrected in the fewest words that make it true again.
  **ADR:** none — five decisions are taken here and none is both cross-cutting and expensive to reverse, so each is recorded with its rejected alternatives in `spec/design/data-model.md`, the home `spec/design/conventions.md` § When a decision is an ADR gives a column, a type and a constraint. (1) `text` is `String(200)`, rejecting `Text` with the bound in the schemas alone and rejecting `CHECK` constraints for the empty text and the line break; reversing it is one revision widening one column. (2) `done` is a boolean, rejecting a `status` column over a set of values and a nullable `done_at`; it follows from `P-02`'s one state with two values. (3) `BR-10` is held by column-scoped single-statement writes, rejecting a version column (it refuses the second writer, which `R-9` and the context's non-goal "Telling a person that somebody else's change replaced theirs" rule out — so the one alternative that would cost a migration and a contract is excluded by the requirements, not by this choice), a locking read and the ORM's load-modify-flush; reversing it is an edit to one service. (4) No uniqueness constraint, which is `BR-12` restated as a schema fact. (5) The filling race is left to the seeder's check, which requirements races `W-5` and `W-6` already accept and the guestbook already carries. The one cross-cutting decision underneath all of this — the to-do list is a context of its own — is the ADR `design/delta/domain.md` marks as required.
  **Requirements:** CR-2609-823a/R-1, CR-2609-823a/R-2, CR-2609-823a/R-3, CR-2609-823a/R-4, CR-2609-823a/R-6, CR-2609-823a/R-7, CR-2609-823a/R-8, CR-2609-823a/R-9, CR-2609-823a/R-11

<!-- z spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/domain.md -->
- `ADDED` `spec/contexts/todo_list.md`
  **Why:** The requirements bring a stored thing no context describes — a task with a state that
  is switched both ways — and every rule about it (`R-1`…`R-4`, `R-6`…`R-9`) needs one owner.
  The guestbook cannot be that owner: its flow `P-01` states that an entry "either exists or it
  does not", its words (entry, author, edited) describe nothing a task has, no rule in the
  requirements relates a task to an entry, and it is the template's example, declared deletable
  as a unit — a list the user chose to keep beside it would be deleted with it. So the task gets
  a context of its own, which shares exactly one rule with the guestbook, the text rule of
  `BR-01`, as a declared shared kernel, and owns `P-02` and `BR-06`…`BR-13` exclusively.
  **ADR:** required — design-adr drafts it. Decision: the to-do list is a bounded context of its
  own (`todo_list`, classified `supporting`), a peer of the guestbook joined by a shared kernel
  that is the text rule alone. Rejected: (1) placing tasks inside the guestbook context — it
  would make `P-01`'s "no states" false for its own context, put a second vocabulary under one
  owner, and tie a feature the user kept to an example the template tells its reader to delete;
  (2) placing them in Platform — Platform holds no domain rules by definition
  (`spec/design/architecture.md` § Platform); (3) `guestbook:upstream:conformist` — true of the
  prose's location and false of the rule, which is a fact about every text field this API accepts
  and lives in neither context's code; (4) `separate-ways` — false, because both contexts are
  held to one rule and a change to it changes both; (5) classifying it `core` — nothing about it
  is what the application competes on, and the non-goals strip out everything that would make a
  to-do list distinctive; (6) `generic` — a bought to-do product brings the accounts
  `spec/invariants.md` refuses and a second place to go. Cross-cutting and expensive to reverse:
  undoing the context moves a table, a contract, a screen and a test tree.
  **Requirements:** CR-2609-823a/R-1, CR-2609-823a/R-2, CR-2609-823a/R-3, CR-2609-823a/R-4,
  CR-2609-823a/R-6, CR-2609-823a/R-7, CR-2609-823a/R-8, CR-2609-823a/R-9

- `MODIFIED` `spec/glossary.md` — the opening paragraph, the rows **Guestbook**, **To-do list**
  and **Task**, and the process row **Task (process)**
  **Was:** "today there is one context, so the split is an exercise for the future"; Guestbook
  "The only bounded context of this system"; no row for the to-do list, the task or the process
  word *task*.
  **Now:** the split is real and says when a word earns a row here; Guestbook is "a bounded
  context" that shares the text rule with the to-do list and nothing else; To-do list (source
  form `todo_list`) and Task (source form `TodoTask`, table `todo_tasks`) point to the context's
  § Language; Task (process) names the collision with `tasks.md` and the scripts.
  **Why:** A second context makes two of the glossary's sentences false the moment it exists,
  and the new words need a home before anybody writes them anywhere else, or the next author
  invents a second name and both survive. *Task* is also a process word in this repository
  (`tasks.md`, `T-n`, "every task is a script"), which is the `Session` trap the glossary already
  names; qualifying the identifier as `todo_task` is what keeps a search for one from finding
  the other.
  **ADR:** none — the entry records the words the new context brings and corrects two sentences
  its arrival makes untrue; the decision it follows from is the ADR marked on the entry above.
  **Requirements:** CR-2609-823a/R-1, CR-2609-823a/R-4

<!-- z spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/spec.md -->
- `MODIFIED` `spec/contexts/guestbook.md` — the front matter's `neighbours`, the opening sentence,
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

- `MODIFIED` `spec/contexts/todo_list.md` — § `BR-07` (one paragraph added) and § `BR-10` (one
  paragraph added)
  **Was:** `BR-06` refused a text over 200 code points as too long and `BR-07` refused a text with
  an inner line break as more than one line, "never 'empty' or 'too long'", and neither said
  which reason a text breaking both gets. `BR-10` said a correction changes the text and nothing
  else, and nothing said in words that a correction is held to `BR-06` and `BR-07`.
  **Now:** `BR-07` states that a text both too long and more than one line is refused as more
  than one line, on the screen and by the application alike, and why that order. `BR-10` states
  that a correction is held to `BR-06` and `BR-07` exactly as an addition is, that a refused
  correction leaves the task with the text it had, and that the person is told the reason an
  addition of that text would get.
  **Why:** Two gaps, each of which would have been settled twice by two authors who never talk. First, for a text over 200 code points with a line break inside it, `BR-06` and `BR-07` both applied and named different reasons — a contradiction between two rules, left to the contract and the screen to resolve separately, while `R-2` clause 5 demands that the screen and the application give one verdict for one text (`scenarios.md` § Bounds the requirements did not give, item 1, recorded it as unsettled). The order chosen is the one `BR-07`'s own words already read as ("never 'too long'") and the one `R-2.7` uses ("refused with the one-line reason, not as empty or too long"), with its reason stated: a pasted line break can be invisible in a one-line field, a length never is. Second, `R-6` clause 4 — a refused correction keeps the previous text and says why — was carried only by inference from `BR-06`'s "nothing is stored", in words written for adding; `S-33` fails exactly on "an edit is held to weaker rules than an add", so the rule is now said where corrections live.
  **ADR:** none — the first paragraph resolves an overlap between two rules of this same change in the direction `BR-07` and `R-2.7` already read, and one sentence reverses it with no migration and no rewritten contract; the second says for corrections what `BR-06` and `BR-07` already require, and adds no rule.
  **Requirements:** CR-2609-823a/R-2, CR-2609-823a/R-6

<!-- z spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/testing.md -->
- `MODIFIED` `spec/design/testing.md` — § Fitness functions (the rows for
  `test_context_boundaries.py`, `test_context_declarations.py`, `test_golden_set.py`,
  `test_data_invariants.py` and `test_length_constants.py`); § The fixture half (the lead-in
  sentence, four table rows, the sentence on browser readers, one paragraph and one rejected-
  alternatives block added, one sentence added to each of "Bounds are computed" and "The order
  in `entries-ordinary.json`"); § Evidence map (the paragraph "In the template this map is
  empty"); § CR-2609-823a, the to-do list (added); § Four file sets, disjoint (the change's
  table and one paragraph added)
  **Was:** the fitness rows called the context, declaration and data-invariant sweeps vacuously
  true "today — one context", "one table", and held "the three length bounds"; the fixture half
  was "Three files" read by the browser through "the only one"; the evidence map was "empty, and
  that is correct", with the guestbook as its only filling.
  **Now:** the sweeps are described as real since the second context and the second table; the
  length rule holds four bounds and the to-do list's seven line breaks; the fixture half lists the
  to-do list's four files, two of them read by the browser, each by one module of its own
  context, with the decision why the task's text cases are a file of their own; the map has a
  subsection for `CR-2609-823a` — an owner, a proof and fixtures per requirement, a test per
  refusal code, how two writers are interleaved, the witnesses of the task-text invariant, which
  seeds the black box binds, the green-by-design and red-first lists, the detectors that go red on
  the way, the files with no test of their own — and its four authors' disjoint file sets.
  **Why:** The implementation stage's test authors write only what this document assigns, in parallel and without talking, so every requirement needs its owner, its citation form and its fixture named before any of them starts — a requirement assigned to nobody is written by nobody, and a proof put in the wrong suite either costs the black box's run time forever or cannot see the rule at all (a race proved by two calls in sequence, a contrast floor asked of jsdom). The red-first list has to exist before the run that shows the failures, or "expected red" becomes a name for whatever broke, and a declared red the runner cannot collect fails the gate; the detectors that the specification and the locator redden on purpose have to be named for the same reason. The fitness rows are edited because this change makes their "vacuously true today" false, and a testing document that misdescribes what its detectors see is how a detector gets deleted.
  **ADR:** none — the suite, fixture and marker choices here are recorded where the constitution (article IX) puts them, in `spec/design/testing.md`; the one decision with rejected alternatives, the to-do list's own text corpus, is reversed by moving test data between two files, with no migration, contract or CI change.
  **Requirements:** CR-2609-823a/R-1, CR-2609-823a/R-2, CR-2609-823a/R-3, CR-2609-823a/R-4,
  CR-2609-823a/R-5, CR-2609-823a/R-6, CR-2609-823a/R-7, CR-2609-823a/R-8, CR-2609-823a/R-9,
  CR-2609-823a/R-10, CR-2609-823a/R-11

<!-- z spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/ui.md -->
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

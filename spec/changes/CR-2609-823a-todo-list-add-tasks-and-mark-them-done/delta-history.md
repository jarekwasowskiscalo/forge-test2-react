# The specification delta — what the earlier passes said

*The evidence behind [`delta.md`](delta.md), assembled from the same fragments: the entries a
later phase superseded, and everything in a fragment that is not a delta entry. Together the
two documents carry every line the fragments hold — this one is what the brief does not need
in front of a reviewer, not what the change stopped saying.*

<!-- ASSEMBLED FROM FRAGMENTS -- do not edit below; the source: design/delta/, reconcile/delta/ -->

## Superseded by a later pass

### The design phase -- what the change wrote into the specification

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

## What else the fragments carry

*Everything in a delta fragment that is not a delta entry — each author's own prose and the `## This change owns` table `set-boundary --from-design` reads out of the fragments. It sits here because the brief is entries; the fragment remains the source.*

### The design phase -- what the change wrote into the specification

<!-- z spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/api.md -->
# Delta fragment — `design-api`

*The contract half of the to-do list, in its two documents: the prose in `spec/design/api.md`,
which freezes at the end of this stage and which the backend and the frontend build against
without talking, and the machine-comparable half in `contracts/openapi/todo_list.yaml`, which
`./scripts/contracts.sh` holds the running application to from now on. Neither is generated
from the other; they say the same thing and the traceability table below is how to check it.*




## Traceability — every endpoint, field and refusal to its requirement

| Contract element | Rule | Requirements |
|---|---|---|
| `GET /api/todo-tasks` → `TodoTaskList`, no parameters, every task, one total order | `BR-11`, `P-02` step 2 | R-3 (clauses 1–3, 5, 6) |
| `TodoTaskList.items` | `BR-11` | R-3 clause 1 |
| `TodoTaskList.total` | `BR-11` | R-3 clause 1; R-11 clause 4 (whether the list is empty) |
| `POST /api/todo-tasks` → `201 TodoTaskRead` | `BR-08`, `BR-12`, `P-02` step 1 | R-1 (clauses 2–5); R-11 clauses 1, 6 (the filling adds through it) |
| `TodoTaskCreate.text` | `BR-06`, `BR-07` | R-1 clause 3; R-2 |
| no `done` in `TodoTaskCreate`, an extra `done` ignored | `BR-08` | R-1 clause 3, R-1.4 |
| `PATCH /api/todo-tasks/{todo_task_id}` → `200 TodoTaskRead` | `BR-09`, `BR-10`, `P-02` steps 3–4 | R-4; R-6; R-11 clause 6 (the filling marks through it) |
| `TodoTaskUpdate.done` — the chosen state, never a flip | `BR-09` | R-4 clauses 1–3 |
| `TodoTaskUpdate.text` — held to the same three refusals | `BR-10` | R-6 clauses 1, 4 |
| absent fields never written; no version, no `If-Match` | `BR-10` | R-9 clauses 1–3; R-4 clause 4; R-6 clause 2 |
| `DELETE /api/todo-tasks/{todo_task_id}` → `204` | `BR-13`, `P-02` step 5 | R-7 clauses 2, 4 |
| `TodoTaskRead.id` | `D-03` | R-1 clause 5 (two tasks with one text are two identities) |
| `TodoTaskRead.text` | `BR-06`, `BR-07` | R-1 clause 3; R-2 |
| `TodoTaskRead.done` | `BR-08`, `BR-09` | R-4 clause 5 |
| `TodoTaskRead.created_at` | `BR-08`, `BR-11` | R-1 clause 3; R-3 clause 2; R-6 clause 2 |
| `todo_task_not_found` (404) | `BR-13` | R-8 clauses 1–2 |
| `todo_task_empty_patch` (422) | the shape of `TodoTaskUpdate` | R-4, R-6 (a `PATCH` that asks for no change is not a success) |
| `todo_task_text_empty` (422) | `BR-06` | R-2 clause 2; R-6 clause 4 |
| `todo_task_text_multiline` (422), winning over too long | `BR-07` | R-2 clause 6; R-6 clause 4 |
| `todo_task_text_too_long` (422) | `BR-06` | R-2 clause 3; R-6 clause 4 |
| the order of refusals; a refusal stores nothing; only `2xx` is "made" | `BR-07`, `BR-13` | R-2 clause 5; R-10 clauses 1–2 |

**`R-5` has no contract surface, and that is stated rather than implied.** The way between the
two screens, the main address and the not-found page are the frame's
(`spec/contexts/todo_list.md` § Neighbours, what no context owns); no endpoint serves them, and
the SPA's own routes are not API routes. `R-7` clauses 1 and 3 (the confirmation) and `R-10`
clause 3 (a list that failed to load) are likewise the screen's; the contract's part of them is
that nothing is deleted before a `DELETE` arrives and that a failed read is never a `200`.

## Generated contracts — what moves, and who regenerates

- `openapi.json` (gitignored) and `frontend/src/api/schema.d.ts` (committed) **both move** once
  the backend's routers exist: two new paths and four new schemas, `TodoTaskCreate`,
  `TodoTaskUpdate`, `TodoTaskRead` and `TodoTaskList`. `Refusal`, `RefusalDetail`,
  `HTTPValidationError` and `ValidationError` keep their names and shapes, and every guestbook
  path and schema is untouched.
- The frontend implementer runs `./scripts/generate.sh` after the backend's routers are in
  place and commits the new `schema.d.ts`; `./scripts/generate.sh --check` at convergence is
  the proof the two sides met.
- Names the implementers have to use for the gate to agree, because the contract freezes them:
  the path parameter `todo_task_id`; the component names above, which are the Pydantic class
  names; `responses=` on `POST` and `PATCH` declaring the `422` as an `anyOf` over `Refusal`
  and `HTTPValidationError` (the guestbook's `PATCH` is the worked example), and the `404` on
  `PATCH` and `DELETE`; `total` declared with a lower bound of zero; and the five codes written
  as string literals in the to-do list's router module. One thing the machine contract cannot
  freeze and the prose does: `done` is read strictly, a JSON boolean and nothing that merely
  reads as one, because Pydantic's lax reading would take `"true"` or `1`.

## What the contract gate says today

`./scripts/contracts.sh` exits 1 on this tree with 11 findings, every one in
`contracts/openapi/todo_list.yaml` and every one of two kinds: the dump has no such path or
schema yet (six), and no router module holds the code yet (five). `guestbook.yaml` and
`health.yaml` raise nothing. They are findings about code the implement stage has not written,
not about the contract — the scale line reads 3 contracts, 5 paths, 10 operations, 7 refusals —
and they close when the backend's routers and schemas exist. Until then `./scripts/check.sh`,
which runs this gate, is red on it.

## Found outside this write set, left for the members who own it

- `contracts/README.md` § Why a contract is written rather than generated says the contracts
  are "three paths, six operations and eight schemas" for this template; after this change the
  gate's own scale line counts five paths and ten operations. That file is outside this
  member's allowlist.
- `spec/design/data-model.md` (being written by `design-data` in this wave) says the schemas
  import `TODO_TASK_TEXT_MAX_LENGTH`. An import is fine; a `max_length` constraint built from it
  on the request schema is not — it would answer an over-long text with FastAPI's list and no
  code, before the one-line rule could win (§ Refusals). A point for the coherence pass if the
  architecture places the bound in the schema.
- The five sentences are product text, as § Refusals says of every sentence. If the mock-up the
  user approves words a reason differently, the sentence here follows it and the code does not
  move.

<!-- z spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/architecture.md -->
# Delta fragment — `design-architecture`

*Where the to-do list lives, which layer holds each of its rules, which files are created,
modified or removed, and which implementer writes each of them. The live document is
`spec/design/architecture.md` § The to-do list — where each rule lives; this fragment carries
what belongs to the change alone: the requirement per file, the nine write sets written out,
what the change leaves alone, what nobody in this composition can write, and the boundary.*


## Decisions

1. **The to-do list is one file per layer in its own directory in every tree** —
   `app/contexts/todo_list/`, `frontend/src/contexts/todo_list/` — named after the concept:
   `todo_task.py` singular, `todo_tasks.py` plural, `TodoTask*` in TypeScript. The glossary
   qualifies the identifier (`todo_task`, never a bare `task`) because *task* is also a process
   word. **ADR:** none — `conventions.md` § Backend and § Frontend applied; the context itself is
   `design-domain`'s ADR.
2. **`BR-06` and `BR-07` are judged in the service, before any write, as one sequence —
   normalize, then empty, then one line, then measure — with one domain exception per verdict,
   which the router translates into its coded refusal; the request shapes carry `text` with no
   bound.** Rejected: one text type in the schema — a constraint there answers before the route
   runs, with FastAPI's list and no code, while `spec/design/api.md` § Shapes gives each of the
   three text refusals a code; a validator in the schema — it answers inside the same list.
   **ADR:** none — the decision is design-adr's draft
   `task-text-refusals-are-coded-not-schema-constraints.md`, taken by the user (`Q-17`: "The
   service checks it, with a coded reason"); `conventions.md` § Layers states the placement rule
   that follows from it.
3. **`LINE_BREAKS` lives beside `TodoTask`, not in `app/platform/schemas/text.py`.** Rejected:
   Platform — the guestbook keeps line breaks as content, so the set is one context's fact
   (`spec/contexts/todo_list.md` § Neighbours keeps it on the to-do side), and the test for a
   Platform file is "a fact about every one of these". **ADR:** none — `conventions.md`
   § Backend's own test, applied.
4. **The browser text rule moves from `frontend/src/contexts/guestbook/lib/entryText.ts` to
   `frontend/src/lib/text.ts`.** Its corpus-reading test, `entryText.test.ts`, stays in the
   guestbook's folder and changes one import line, because it needs the guestbook's bounds and
   `frontend/src/lib/` imports no context (`conventions.md` § Frontend). Rejected: a copy in
   the to-do context (a rule with two homes, the `D-04` defect's shape); importing the
   guestbook's folder (refused by `test_no_screen_reaches_into_another_contexts_folder`);
   `textMeasurement.ts` (names the corpus rather than the rule). `text.ts` pairs by name with
   `app/platform/schemas/text.py`, its other half. **ADR:** none — `conventions.md` § Frontend:
   a context's rule "moves up here the day a second context needs it — never before".
5. **The done control is a design-system primitive, `frontend/src/components/ui/Checkbox.tsx`,
   with its first caller.** A checkbox by semantics, so the done state is exposed to assistive
   technology and to a test (requirements Self-check 12). No `EmptyState` primitive returns — the
   to-do list says "empty" in its own words, as the guestbook does — and no theme token is added:
   every text token already clears 4.5:1 (`ui/system-states.md` § Tokens). **ADR:** none —
   `conventions.md` § Frontend.
6. **The query hook writes its cache only from the server's answer.** Rejected: an optimistic
   update with rollback — it shows a change as made before it is stored, which `R-10` clause 2
   forbids even for a moment. **ADR:** none — one hook's behaviour.
7. **The seeder fills each list on its own, through the API; an example task is added, then
   marked.** **ADR:** none — the rule is the user's (`Q-10`, `Q-12`); the placement is the
   decision of 2026-09-05 in § What a new environment starts with, extended by one list.

## The layer per requirement

| Requirement | Layer | Why that one |
|---|---|---|
| R-1 (add) | schemas (create shape) → service (text judgement, insert, `done` false, clock) → router (binding); screen: composer + hook | the service owns the write and the clock; `R-1.4` holds because nothing the caller sends reaches `done` |
| R-2 (text refused) | service's judgement over `app/platform/schemas/text.py`, one domain exception per verdict, each translated by the router into its coded refusal; browser: `lib/todoTask.ts` over `frontend/src/lib/text.ts` | one sequence, normalize → empty → one line → measure, on each side of the wire (Decision 2) |
| R-3 (one list, one order) | service's read (`created_at DESC, id DESC`, no pages); index in model + revision; screen: page | the order is a rule meeting the store |
| R-4 (mark) | service: one `UPDATE` naming `done` alone with the chosen value; screen: row + `Checkbox` | the store holds `R-4` clause 3 through the statement's shape (`data-model.md` § Two writers on one task) |
| R-5 (two screens) | frame `PageFrame.tsx`, `routes.ts`, `router.tsx`, `StatusPages.tsx` | no context owns it; the frame is the one file that learns about a second screen |
| R-6 (correct) | service: one `UPDATE` naming `text` alone; the same judgement as the add | a correction held to `R-2` by construction |
| R-7 (delete) | service: one `DELETE … RETURNING`; screen: row + dialog | the confirmation is the screen's; the deletion the service's |
| R-8 (gone) | service raises `TodoTaskNotFoundError` on no row returned; router translates to the not-found refusal; hook reports it | a service never names a status code |
| R-9 (concurrent) | service, by the statement shape `data-model.md` names — no read before any write | only the store can hold it; no router or screen can |
| R-10 (not stored, not shown) | hook (no optimistic write), page (failed load ≠ empty) | the hook is the one place the cache is written |
| R-11 (example tasks) | `scripts/seed_golden_set.py` + `golden-set/seed/todo-tasks-example.json` | § What a new environment starts with |

## Files — created, modified, removed

| Path | Change | Holds | Requirements | Writer |
|---|---|---|---|---|
| `app/contexts/todo_list/__init__.py` | created | the public API; registers `todo_tasks` on `Base` | R-1, R-3 | build-backend |
| `app/contexts/todo_list/models/__init__.py` | created | the layer's docstring | R-1 | build-backend |
| `app/contexts/todo_list/models/todo_task.py` | created | `TodoTask`, `TODO_TASK_TEXT_MAX_LENGTH`, `LINE_BREAKS`, the ordering index | R-1, R-2, R-3, R-4 | build-backend |
| `app/contexts/todo_list/schemas/__init__.py` | created | the layer's docstring | R-1 | build-backend |
| `app/contexts/todo_list/schemas/todo_tasks.py` | created | the shapes `api.md` names, with no text rule | R-1, R-2, R-4, R-6 | build-backend |
| `app/contexts/todo_list/services/__init__.py` | created | the layer's docstring | R-1 | build-backend |
| `app/contexts/todo_list/services/todo_tasks.py` | created | add, read, correct, mark, delete; `TodoTaskNotFoundError`; the text's judgement and its three domain exceptions | R-1, R-2, R-3, R-4, R-6, R-7, R-8, R-9 | build-backend |
| `app/contexts/todo_list/routers/__init__.py` | created | the layer's docstring | R-1 | build-backend |
| `app/contexts/todo_list/routers/todo_tasks.py` | created | the HTTP binding, the declared refusals, the sentences | R-1, R-2, R-3, R-4, R-6, R-7, R-8 | build-backend |
| `app/contexts/__init__.py` | modified | one appended registration | R-1, R-3 | build-backend |
| `app/api.py` | modified | one appended `include_router` | R-1, R-3, R-4, R-6, R-7 | build-backend |
| `alembic/versions/<issued by db.sh revision>_create_todo_tasks_table.py` | created | the table and its index, in `data-model.md`'s order | R-1, R-3, R-4 | build-migration |
| `frontend/src/contexts/todo_list/pages/TodoListPage.tsx` | created | the screen and its states | R-1, R-3, R-10 | build-frontend |
| `frontend/src/contexts/todo_list/components/TodoTaskComposer.tsx` | created | the field and its verdict before sending | R-1, R-2 | build-frontend |
| `frontend/src/contexts/todo_list/components/TodoTaskRow.tsx` | created | the done control, the text drawn done, the correction, the delete trigger | R-4, R-6, R-7 | build-frontend |
| `frontend/src/contexts/todo_list/components/DeleteTodoTaskDialog.tsx` | created | the confirmation | R-7 | build-frontend |
| `frontend/src/contexts/todo_list/hooks/useTodoTasks.ts` | created | query, four mutations, `todoTaskKeys`, answer-only cache | R-1, R-3, R-4, R-6, R-7, R-8, R-10 | build-frontend |
| `frontend/src/contexts/todo_list/lib/todoTask.ts` | created | the type, the two browser copies, the verdict, the sentences | R-2, R-4, R-6 | build-frontend |
| `frontend/src/lib/text.ts` | created (moved) | the shared text rule's browser half | R-2 | build-frontend |
| `frontend/src/contexts/guestbook/lib/entryText.ts` | removed (moved) | — | R-2 | build-frontend |
| `frontend/src/contexts/guestbook/lib/guestbookEntry.ts` | modified | one import path | R-2 | build-frontend |
| `frontend/src/contexts/guestbook/components/EntryComposer.tsx` | modified | one import path | R-2 | build-frontend |
| `frontend/src/contexts/guestbook/hooks/useEntryQueryParams.ts` | modified | one import path | R-2 | build-frontend |
| `frontend/src/components/ui/Checkbox.tsx` | created | the done control primitive | R-4 | build-frontend |
| `frontend/src/components/shell/PageFrame.tsx` | modified | the way between screens; the frame's words for two screens | R-5 | build-frontend |
| `frontend/src/pages/StatusPages.tsx` | modified | the not-found copy | R-5 | build-frontend |
| `frontend/src/routes.ts` | modified | `TODO_LIST_ROUTE` (its value is the screen specification's) | R-5 | build-frontend |
| `frontend/src/router.tsx` | modified | one appended route; `/` unchanged | R-5 | build-frontend |
| `frontend/src/api/schema.d.ts` | regenerated | the to-do shapes, from `./scripts/generate.sh` | R-1, R-4, R-6, R-7, R-8 | build-frontend |
| `golden-set/seed/todo-tasks-example.json` | created | at least three example tasks, under 150 code points, one above U+007F, at least one done | R-11 | build-backend |
| `scripts/seed_golden_set.py` | modified | a per-list emptiness check, the task posts, the marking | R-11 | build-backend |
| `scripts/seed.sh` | modified | its header and `--help` name both lists | R-11 | build-backend |
| `.github/CODEOWNERS` | modified | the to-do list's rows in the per-context pattern, naming the owner the catch-all already names (no other owner is recorded anywhere) | — no requirement asks for it; `spec/design/architecture.md` § What a new feature adds, Ownership, for the context `R-1`…`R-9` opened | build-platform |

## The write sets — one per implementer, and their intersection

| Member | Its set for this change |
|---|---|
| build-tests-integration | `tests/integration/` (new to-do files), `tests/tooling/test_seed_golden_set.py`, `tests/_golden_set.py`, `golden-set/fixtures/` (new to-do files) |
| build-tests-unit | `tests/unit/` (new to-do files; `test_guestbook_entry_model.py`, `test_entry_text_rules.py`), `tests/fitness/test_golden_set.py`, `tests/fitness/test_length_constants.py` |
| build-tests-frontend | `frontend/src/contexts/guestbook/lib/entryText.test.ts` (one import line), `frontend/src/contexts/todo_list/**/*.test.ts(x)`, `frontend/src/components/shell/PageFrame.test.tsx`, `frontend/src/pages/StatusPages.test.tsx`, `frontend/src/router.test.tsx` |
| build-tests-e2e | `e2e/suite/features/todo_list.feature`, `e2e/suite/steps/todo_list_steps.py`, `e2e/suite/test_scenarios.py`, `e2e/ui/` |
| build-tests-uat | this record's `uat.md` |
| build-backend | every `app/` row above, `golden-set/seed/todo-tasks-example.json`, `scripts/seed_golden_set.py`, `scripts/seed.sh` |
| build-migration | the one new file under `alembic/versions/` |
| build-frontend | every `frontend/src/` row above — modules only, no `*.test.*` |
| build-platform | `.github/CODEOWNERS` |

**The intersection, written out.** Two sets can meet only where they hold the same top-level
tree. Three pairs do, and a fourth describes one table from two trees; every other pair of the
nine holds disjoint trees, so its intersection is empty without looking further.

- build-frontend ∩ build-tests-frontend, in `frontend/src/`: the first set has no path matching
  `*.test.ts` or `*.test.tsx`, the second has nothing else — **∅**.
- build-tests-unit ∩ build-tests-integration, in `tests/`: `tests/unit/` and `tests/fitness/`
  against `tests/integration/`, `tests/tooling/` and `tests/_golden_set.py` — **∅**.
- build-backend ∩ build-tests-integration, in `golden-set/`: `golden-set/seed/` against
  `golden-set/fixtures/` — **∅**.
- build-backend ∩ build-migration, around the table: `app/contexts/todo_list/models/todo_task.py`
  against the new file under `alembic/versions/` — **∅**.

**Every pairwise intersection is empty, and so is the intersection of all nine.** No test file is
in any builder's set: build-backend, build-frontend, build-migration and build-platform hold no
path under `tests/` or `e2e/`, and build-frontend holds no `*.test.*` file.

**Three data edges cross the sets, and none is a shared file** (live document, § Who writes what):
`frontend/src/api/schema.d.ts` is generated from build-backend's schemas and routers, so
build-frontend's regeneration waits for build-backend — design-plan orders that task after the
backend's; `scripts/seed_golden_set.py` imports `tests/_golden_set.py`, already ordered by the test
wave coming first; the revision and the model agree through `data-model.md`, and
`tests/integration/test_migrations.py` compares them.

## Boundaries

What may not import what, and the fitness test that refuses it, is the live document's table
(`spec/design/architecture.md` § What holds the boundaries): neither context imports the other on
either side of the wire (`tests/fitness/test_context_boundaries.py`); only `app/api.py` reaches
`routers/todo_tasks.py`; `services/`, `models/` and `schemas/` import no web framework and no
router reaches the session (`tests/fitness/test_layering.py`); the context is registered in both
aggregates and has both a document and code; the two browser copies equal their homes
(`tests/fitness/test_length_constants.py`, which build-tests-unit extends to the 200 and to
`LINE_BREAKS`); one frontend module reads the text-measurement corpus and no suite reads the seed
half (`tests/fitness/test_golden_set.py`).

## What this change does not move

- **The guestbook's backend, whole** — `app/contexts/guestbook/` in every layer, its revision
  `alembic/versions/a1b2c3d4e5f6_create_guestbook_entries_table.py`, its contract, its welcome
  entries, `e2e/suite/features/guestbook.feature` and its steps (`SC-5`), save one comment in
  `e2e/suite/steps/guestbook_steps.py`, on `ENTRIES`, that counted one resource
  (`spec/design/testing.md` § Four file sets, disjoint, COH-implement-9): prose alone, and no step
  text or binding moves. Its frontend changes by three import paths and one line of
  `GuestbookPage.tsx`'s module docstring (`spec/design/architecture.md` § The files,
  COH-implement-5), and nothing else.
- **`app/platform/schemas/text.py`** — the kernel's server half is imported by the to-do service's
  judgement as it stands; `app/platform/schemas/refusals.py` is reused as the envelope.
- **`app/main.py`, `app/core/`, `app/db/`, `alembic/env.py`** — the aggregate and the context
  registry are the only composition points, and `alembic/env.py` already imports every context.
- **`frontend/src/api/client.ts` and `frontend/src/api/problem.ts`** — both are resource-agnostic.
- **`frontend/src/components/ui/` beyond `Checkbox.tsx`** — `Button`, `Modal`, `Toast` and
  `Feedback` are reused; no `EmptyState` returns.
- **`frontend/src/styles/theme.css`** — every text token already clears 4.5:1, so the done state
  is drawn with tokens that exist.
- **`infra/`, `Dockerfile`, `docker-compose.yml`, `.github/workflows/`** — `infra_touched` is
  absent, and no workflow names a context.
- **`e2e/harness/`** — the reset is table-agnostic and `todo_tasks` is scenario state.
- **`pyproject.toml`, `uv.lock`, `frontend/package.json`** — no dependency is added.
- **`http/`** — no request file for the to-do list: no member of this composition writes `http/`,
  and § What a new feature adds does not list one.

## Found outside every write set — for the orchestrator

1. **`golden-set/README.md` has no author in this composition, and this change needs it
   edited.** Its § `seed/` says "One file: `entries-welcome.json`", which `R-11` makes false.
   build-tests-integration
   holds `golden-set/fixtures/`, build-backend `golden-set/seed/`, and reconcile-docs the root
   `README.md` only. It is left out of § This change owns because `set-boundary --from-design`
   refuses a row with no author. Proposed owner: build-tests-integration, which owns the locator
   the README describes, by adding the path to its `writes` in `.specconf/stack.json` § `skills`.
2. **`e2e/suite/golden_set.py` has no author either.** It is the black box's one crossing into
   the corpus, and it re-exports only the guestbook's fixture files. If `spec/design/testing.md`
   gives the to-do scenarios fixture files, the re-export has to grow there. Proposed owner:
   build-tests-e2e.
3. **One document still keeps the browser's text rule in the guestbook.**
   `spec/design/conventions.md` § Frontend lines 188–190 says `entryText.ts` "stays in the
   context because the browser has exactly one" caller, which the move makes false —
   reconcile-design's, since this skill does not write `conventions.md`.
4. **The to-do list's front matter against three fitness tests.**
   `tests/fitness/test_context_boundaries.py::test_every_context_document_has_code_and_every_context_directory_has_a_document`
   is red from the moment `spec/contexts/todo_list.md` exists until build-backend creates
   `app/contexts/todo_list/`. Both claims are in `spec/contexts/todo_list.md` since the
   convergence round (COH-design-5, COH-design-6); the on-disk case is red until build-tests-e2e
   writes the feature file.

## This change owns

| Path | Why |
|---|---|
| `app/contexts/todo_list/` | the to-do list's backend, whole: model, schemas, service, router and the public API (build-backend) |
| `app/contexts/__init__.py` | one appended line registering the context, so its table reaches `Base.metadata` (build-backend) |
| `app/api.py` | one appended line mounting the to-do router under `/api` (build-backend) |
| `alembic/versions/` | the one revision that creates `todo_tasks` and its ordering index (build-migration) |
| `frontend/src/contexts/todo_list/` | the to-do screen, whole: page, components, hook, lib, and the vitest files beside them (build-frontend, build-tests-frontend) |
| `frontend/src/lib/text.ts` | the shared text rule's browser half, moved up because a second context needs it (build-frontend) |
| `frontend/src/contexts/guestbook/lib/entryText.ts` | removed: the rule's old home inside the guestbook (build-frontend) |
| `frontend/src/contexts/guestbook/lib/entryText.test.ts` | one import line, to the rule's new home (build-tests-frontend) |
| `frontend/src/contexts/guestbook/lib/guestbookEntry.ts` | one import path, to the rule's new home (build-frontend) |
| `frontend/src/contexts/guestbook/components/EntryComposer.tsx` | one import path, to the rule's new home (build-frontend) |
| `frontend/src/contexts/guestbook/hooks/useEntryQueryParams.ts` | one import path, to the rule's new home (build-frontend) |
| `frontend/src/components/ui/Checkbox.tsx` | the done control, a design-system primitive with its first caller (build-frontend) |
| `frontend/src/components/shell/PageFrame.tsx` | the way between the two screens and the frame's words for two of them (build-frontend) |
| `frontend/src/components/shell/PageFrame.test.tsx` | the vitest cases for the way between screens (build-tests-frontend) |
| `frontend/src/pages/StatusPages.tsx` | a not-found page that no longer says there is one screen (build-frontend) |
| `frontend/src/pages/StatusPages.test.tsx` | the vitest case for the not-found copy (build-tests-frontend) |
| `frontend/src/routes.ts` | the to-do list's route constant (build-frontend) |
| `frontend/src/router.tsx` | one appended route binding the constant to the screen (build-frontend) |
| `frontend/src/router.test.tsx` | the vitest cases for the to-do list's own address, the main address and an unknown address (`R-5`) (build-tests-frontend) |
| `frontend/src/api/schema.d.ts` | regenerated from the backend's schemas, never edited (build-frontend) |
| `golden-set/seed/todo-tasks-example.json` | the example tasks a new environment opens with (build-backend) |
| `scripts/seed_golden_set.py` | filling each list on its own, adding then marking an example task (build-backend) |
| `scripts/seed.sh` | its header and `--help`, which name the guest book alone today (build-backend) |
| `.github/CODEOWNERS` | the to-do list's rows in the per-context pattern the file states (build-platform) |
| `tests/unit/` | the text rule and the model's constants, and the one-table assertion a second table turns red (build-tests-unit) |
| `tests/fitness/` | the corpus rules scoped to entries and the two new browser copies (build-tests-unit) |
| `tests/integration/` | the service, router, contract, concurrency and corpus tests of the to-do list (build-tests-integration) |
| `tests/tooling/` | the seeder's per-list filling (build-tests-integration) |
| `tests/_golden_set.py` | registers the example-task file and any to-do fixture file (build-tests-integration) |
| `golden-set/fixtures/` | the to-do list's ordinary, boundary and refused texts (build-tests-integration) |
| `e2e/suite/features/todo_list.feature` | the to-do list's Gherkin scenarios (build-tests-e2e) |
| `e2e/suite/steps/todo_list_steps.py` | the steps that bind them (build-tests-e2e) |
| `e2e/suite/test_scenarios.py` | the import that makes the new step module exist for the runner (build-tests-e2e) |
| `e2e/ui/` | the UI smoke: the to-do screen boots, and locators follow the approved names (`A-4`) (build-tests-e2e) |

<!-- z spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/converge.md -->
# Delta fragment — `review-converge`

*Written by the convergence round of coherence pass 1, `requirements` stage. The requirements
stage has no fragment directory of its own, and `close_stage` assembles `delta.md` from
`design/delta/` and `reconcile/delta/` alone, so this entry sits in the first of them. The
edits this round made to `requirements.md` and `impact.md` are inside the change record and
need no entry.*


*Written by the convergence round of coherence pass 4, `design` stage, for the eight findings
`COH-design-1` to `COH-design-8`. Each entry below is an edit to the earliest document a finding
names as its `ambiguity_source` (constitution, Article VIII). The artefact-level patches under
each finding in `review/coherence.md` belong to the authors the convergence round sends again,
and they are not declared here. This round's edits to `requirements.md` (`COH-design-7`) are
inside the change record and need no entry.*


*Written by the convergence round of coherence pass 5, `design` stage, for the ten findings
`COH-design-9` to `COH-design-18`. Every decision was taken before this round, automatically from
the document a finding's `auto_basis` names or by the user at `Q-21`, and this round records it.
Each finding's edit lands in the earliest document it names as its `ambiguity_source`. Where the
dispatch also handed this round the ready patch under a finding, that patch landed too, in the
artefact that carried the contradiction. Both kinds are declared below when they land under
`spec/` or `contracts/`. This round's edits inside the change record need no entry: the
requirements (`COH-design-14`), the scenarios (`COH-design-15`), the ADR draft on coded text
refusals (`COH-design-15`), and the api and architecture fragments (`COH-design-15`,
`COH-design-9`, `COH-design-13`).*


*Written by the convergence round of coherence pass 7, `implement` stage, for the six findings
`COH-implement-1` to `COH-implement-6`. The implement stage has no fragment directory of its own,
so these entries sit here, as the requirements stage's did. Each edit lands in the earliest
document a finding names as its `ambiguity_source`; for `COH-implement-3` and `COH-implement-6`
the ready patch under the finding names that document itself, and it landed with the small
adjustments the entries below name. The
artefact-level patches that fall outside this round's write set — `useTodoTasks.ts`
(`staleTime: 0`), `GuestbookPage.tsx`:30, `uat.md` step 14 and the five test docstrings of
`COH-implement-4` — belong to their authors in the convergence round that follows, and they are
not declared here as made.*


*Written by the convergence round of coherence pass 8, `implement` stage, for the four findings
`COH-implement-7` to `COH-implement-10`, each with the ready patch under it. `COH-implement-7`
names `requirements.md` § R-3 clause 5 as its `ambiguity_source`; its patch and the user's
decision (`Q-28`) land in `spec/design/ui/system-states.md` § Interactions, which ranks above the
change's requirements (constitution, Article VIII) and now decides what is shown while the read is
under way, so the approved requirements are left as they are. `COH-implement-10`'s edits
(`design/delta/architecture.md` § What this change does not move, `tasks.md` T-22 and § Outside
every task, item 6), `COH-implement-9`'s exception in that same fragment bullet, and the
`guestbook_steps.py` row of § This change owns below are inside the change record and need no
entry. The three comment edits of `COH-implement-9` and the `frontend/src/router.test.tsx` case of
`COH-implement-8` belong to their authors afterwards, and they are not declared here as made.*


## This change owns

| Path | Why |
|---|---|
| `frontend/src/contexts/guestbook/pages/GuestbookPage.tsx` | one line of its module docstring, which called the guestbook the only screen; now one of two (COH-implement-5); nothing the screen does moves (build-frontend) |
| `e2e/suite/steps/guestbook_steps.py` | one comment, on `ENTRIES`, that counted one resource (COH-implement-9); no step text or binding moves (build-tests-e2e) |

<!-- z spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/data-model.md -->
# Delta fragment — `design-data`

*The schema half of the to-do list: one new table, `todo_tasks`, owned by the `todo_list`
context that `design-domain` opened (`design/delta/domain.md`), one index, no uniqueness
constraint, and one revision in `backward compatible` mode. The mechanism `BR-10` delegates to
the data model ("the data model names the mechanism that does") is written into
§ `todo_tasks` › Two writers on one task. One file is edited, so there is one entry.*


## Traceability — every table, column, index and operation to its requirement

| What | Where in `spec/design/data-model.md` | Requirements |
|---|---|---|
| table `todo_tasks`, one row per task, no list row | § `todo_tasks` | R-1 (clause 3), R-3 (clause 1) |
| `id` — `Uuid`, primary key, `default=uuid.uuid4` | § `todo_tasks`, the table | R-4, R-6, R-7, R-8 (a task is addressed by it); `D-03` |
| `text` — `String(200)`, `NOT NULL` | § `todo_tasks`, the table and "Why `String(200)`" | R-1 (clause 3), R-2 (clauses 1-3 and 6), R-6 (clauses 1 and 4) |
| `done` — `Boolean`, `NOT NULL`, `false` on every insert | § `todo_tasks`, the table and "Why a boolean" | R-1 (clause 3, R-1.4), R-4 (clauses 1-3), R-6 (clause 2) |
| `created_at` — `DateTime(timezone=True)`, `NOT NULL`, set once | § `todo_tasks`, the table | R-1 (clause 3), R-3 (clauses 2-4), R-6 (clause 2) |
| no `updated_at`, no `deleted_at`, no position, nobody | § `todo_tasks`, "What is deliberately not a column" | R-3 (clauses 2 and 4), R-7 (clause 2); the non-goals of `requirements.md` |
| `TODO_TASK_TEXT_MAX_LENGTH = 200` beside the model | § `todo_tasks`, "The bound, beside the model" | R-2 (clauses 3 and 5) |
| column-scoped correction, chosen-state marking, single-statement deletion, no upsert | § `todo_tasks` › Two writers on one task | R-4 (clause 3), R-6 (clause 2), R-8 (clauses 1-2), R-9 (clauses 1-3); races `W-1`, `W-2`, `W-3` |
| no row in the revision; the filling race left to the seeder | § `todo_tasks`, the last two paragraphs | R-11 (clauses 1 and 4); races `W-5`, `W-6` |
| `ix_todo_tasks_created_at_id` on (`created_at`, `id`) | § Indexes and uniqueness | R-3 (clauses 2-3) |
| no unique constraint on `todo_tasks` | § Indexes and uniqueness | R-1 (clause 5) |
| the revision: `create_table`, `create_index`; down: `drop_index`, `drop_table` | § Migrations › The revision that creates `todo_tasks` | every row above |
| mode `backward compatible` | § Compatibility mode | every row above |

`R-5` (the way between screens) and `R-10` (a change that did not go through) store nothing and
have no row here. No column holds an amount of money or an account identifier.

## The fixtures of `scenarios.md` § Test data, against this schema

| Fixture | Verdict |
|---|---|
| `tasks-ordinary.json` (six tasks, one text twice, two marked done after adding) | accepted: every text is under 80 code points, the repeated "Buy bread" meets no unique constraint, `done` is written by a marking after the insert |
| `tasks-boundary.json` (five cases on the bound) | accepted: each is at most 200 code points once normalized and trimmed, and `varchar(200)` counts code points, so 200 × U+1F600 fits (200 characters, 400 UTF-16 units) and 200 × (U+0065 U+0301) is stored as 200 × U+00E9 |
| `tasks-refused.json` (nine cases) | refused by the service and never reach the column; were a 201-code-point value to arrive by a route that skipped the rule, the column would refuse it too |
| the additions to `text-measurement.json` | a pure rule, no row |
| 101 tasks for S-14 | accepted: nothing bounds the number of rows |
| two tasks with one moment of adding (`R-3.2`) | accepted: nothing is unique on `created_at`, and `id` breaks the tie |
| `golden-set/seed/tasks-welcome.json` (five tasks, one marked done) | accepted: the longest is 112 code points; posted through the API, never by the revision |
| every inline value | accepted: all are short, one-line texts |

## Checked against the invariants

`D-01`: a done task stays the same row in the same place, and a deletion is a `DELETE`, so no
table is shaped like an archive. `D-02`: no foreign key, no column copied — the columns
`todo_tasks` shares by name and type with `guestbook_entries` are `id` and `created_at`, which the
sweep in `tests/fitness/test_data_invariants.py` treats as universal, and `text` and `done` sit on
no other table. The same test fails if the word for a deliberately copied historical value
appears anywhere in `spec/design/data-model.md`, and the edit avoids it. `D-03`: `id` is a UUID
issued by the application. `spec/invariants.md`: no accounts (nobody is recorded), a task lives
until it is deleted (no expiry column), one engine (Postgres alone, no `batch_alter_table`).

## Found outside this write set, left for the members who own it

- **The data invariant for a task's text — the call is made here, the file is not mine.**
  `design/delta/domain.md` and `design/delta/spec.md` both left to this step whether a task's text
  gets an invariant of its own, because `D-04` names only `author` and `message`. The call: it
  does. Every `text` in `todo_tasks` is NFC, carries no member of the trim set at either end, is 1
  to 200 code points and carries no line break inside — the same kind of fact as `D-04`, about a
  different domain, so it belongs in the to-do list's own file under `contracts/invariants/`,
  with a witness from both sides of the shared rule. `contracts/` is written by the convergence
  round in a change cycle (`spec/invariants.md` § Data invariants, "The editing route"), not by a
  fan-out author, so it is reported for that round rather than written.
- **For `design-testing`:** the statement shape in § Two writers on one task is proved only by
  two writers interleaved on one row, the second waiting on the first's lock
  (`requirements.md` § Self-check 19); `R-3.2` needs two tasks stored with one `created_at`,
  through the service's clock seam. `tests/integration/test_migrations.py` keeps a hand-written
  mirror of the guestbook's columns and will need one for `todo_tasks`, and
  `tests/unit/test_guestbook_entry_model.py::test_this_schema_holds_exactly_one_table` goes red
  on the new table (`requirements.md` § Impact analysis).
- **For `design-architecture`:** the model is `TodoTask` in
  `app.contexts.todo_list.models.todo_task`, with `TODO_TASK_TEXT_MAX_LENGTH` beside it, and the
  context has to be imported by `app/contexts/__init__.py` for `alembic/env.py` to see the table
  (§ What Alembic sees). Where the browser keeps its copy of the constant is that member's call.

<!-- z spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/domain.md -->
# Delta fragment — `design-domain`

*A new bounded context, the to-do list, opened only after placing the requirements in the one
context that exists was tried and failed. The evidence for both is below the entries.*



## The concept is absent — the search

Run from the repository root on 2026-09-24, before any edit:

| Search | Where | Found |
|---|---|---|
| `grep -niE "to-do\|todo\|\btasks?\b\|\bdone\b\|tick" spec/glossary.md` | the glossary | nothing |
| the same, `-r` | `spec/contexts/` (one document, `guestbook.md`) | nothing |
| `grep -rniEl "to-do\|todo" spec --exclude-dir=changes` | the whole specification | `spec/invariants.md` lines 124 and 162 — "any to-do task", "like a to-do task", written by this change's own convergence round (COH-requirements-5, `design/delta/converge.md`); `spec/rationale/AUDIT-2026-09-01.md` — "TODO/FIXME" markers, not the concept |
| `grep -rciE "\btasks?\b"` over `spec/` outside `spec/changes/` | the whole specification | only the process word: "every task is a script" (constitution art. XII, conventions § Scripts), the `tasks` gate (conventions § Naming) |
| `grep -rnwI todo` over `app/ frontend/src e2e golden-set alembic contracts` | the code and the corpus | nothing (0 lines), and no `TODO` marker in first-party source |
| `grep -rhoE "\bBR-[0-9]{2}\b\|\bP-[0-9]{2}\b"` over `spec/ contracts/ CLAUDE.md` | the frozen spaces | `BR-01`…`BR-05`, `P-01` declared; `BR-14` appears only as an illustration in `spec/ADR/index.md`, which the `frozen-ids` gate does not hold. So `P-02` and `BR-06`…`BR-13` are fresh |

`impact.md` § What is missing ran the wider search (`todo|to-do|todos|task|tasks|done|complete|completed|zadani|checkbox|checked`
over twelve trees) and found the same. The term is not in the glossary after all, so the
`new_context` signal stands.

## The alternative that was tried — placing the requirements in the guestbook

| Test | Guestbook | Result |
|---|---|---|
| Does its language cover a task? | Entry, Author, Message, Edited. A task has no signature, no moment of amendment, no "edited"; an entry has no state. | fails |
| Does its flow hold a state? | `P-01`: "There are no intermediate states, no lifecycle … An entry either exists or it does not." Tasks would make that sentence false for its own context (requirements Self-check 24). | fails |
| Is any rule shared? | Only the text rule of `BR-01` (NFC, the trim set, code points). `BR-03` and `BR-04` are the same *shape* of rule about a different thing, and each side can change its own without the other (the list is read one way; the guestbook both ways). | one rule, handled as a kernel |
| Does a flow cross? | No step of either flow reads or writes the other's records; `Q-10` fills each list on its own. | nothing crosses |
| Can one owner hold both? | The guestbook is the template's example, deleted as a unit (`CLAUDE.md` § What is an example; `spec/contexts/guestbook.md`, "it can be deleted when your first real feature replaces it"). The user kept it beside the list (`Q-1`), so the list must survive its deletion. | fails |
| Could Platform hold it? | Platform has no domain rules (`spec/design/architecture.md` § Platform). | fails |

## Traceability — every rule to its requirement

| Rule | Requirements |
|---|---|
| `P-02` step 1, `BR-08` | R-1 (clauses 1-5; R-1.4) |
| `BR-06` | R-2 clauses 1-3, 4, 5; R-6 clause 4 |
| `BR-07` | R-2 clause 6 (assumption `A-1` set, `A-3` reading); R-6 clause 4 |
| `BR-11`, `P-02` step 2 | R-3 clauses 1-5 |
| `BR-09` | R-4 clauses 1-5; R-4 clause 6 by reference to the screen's floor |
| `BR-10` | R-6 clauses 1-3; R-9 clauses 1-3 |
| `BR-12` | R-1 clause 5 |
| `BR-13`, `P-02` step 5 | R-7 clauses 1-4; R-8 clauses 1-2 |

**Handed over, not owned by this context:** R-5 (the way between screens, the main address, the
404 copy) to the frame, `spec/design/ui/system-states.md`; R-3 clause 6 and R-10 (how an empty,
unreadable or failed state looks) to the screen specification; R-11 (example tasks in a new
environment) to `spec/design/architecture.md` § What a new environment starts with — bound by
`BR-06`…`BR-08` like any task.

## Checked against `spec/invariants.md` and `contracts/invariants/`

Authentication: consistent — anybody adds, marks, corrects and deletes any task, and the
non-goal already names tasks. CSRF, moderation, mobile, one engine: consistent. Paging and
search, lifted for the guestbook alone: consistent — the list has neither. Retention: consistent
— a task lives until deleted, and the non-goal names tasks. `D-01`: a done task stays one record
in its place, never moved to an archive. `D-02`, `D-03`: nothing here conflicts. `D-04` names
the guestbook's two fields; whether the task's text gets an invariant of its own is design-data's
call. No rule here contradicts an invariant.

<!-- z spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/spec.md -->
# Delta fragment — `design-spec`

*The to-do list's context document was opened by `design-domain` in the wave before this one
(`design/delta/domain.md`), with `P-02` and `BR-06`…`BR-13`. This pass read it whole against
every requirement, brought the guestbook's document level with the new boundary, and closed two
gaps in the rules. No rule identifier is minted: the highest in use is `BR-13`, and every edit
below amends a section that already has one.*



## Traceability — every requirement to where the live specification carries it

| Requirement | Carried by | This pass |
|---|---|---|
| R-1 | `P-02` step 1, `BR-08`, `BR-12` | read, no edit needed |
| R-2 | `BR-06`, `BR-07`; the shared text rule in the guestbook's `BR-01` | `BR-07` amended (two reasons meeting); `BR-01` names its second holder |
| R-3 | `P-02` step 2, `BR-11` | read, no edit needed |
| R-4 | `BR-09` (clause 6 by reference to the screen's floor) | read, no edit needed |
| R-5 | the frame every screen renders inside — owned by no context (todo_list § Neighbours, what no context owns) | no edit here; the guestbook's "only bounded context and only feature" sentence is corrected |
| R-6 | `P-02` step 4, `BR-10` | `BR-10` amended (a correction held to `BR-06` and `BR-07`) |
| R-7 | `P-02` step 5, `BR-13` | read, no edit needed |
| R-8 | `BR-13` | read, no edit needed |
| R-9 | `BR-10` | read, no edit needed |
| R-10 | how a screen shows a failure — owned by no context (todo_list § Neighbours) | no edit here |
| R-11 | a new environment's starting state — owned by no context; `BR-08` binds example tasks | no edit here |

## Checked against the invariants

Authentication and retention: consistent — the non-goals name tasks, and a correction or a
refusal needs no identity. `D-01`: a refused correction leaves one record as it was. `D-02`,
`D-03`: untouched. `D-04` names the guestbook's two fields; the sentence added to `BR-01` says a
task's text is held to the same rule and leaves to design-data whether the task's own domain
gets a data invariant for it. No edit here contradicts an invariant.

## Found outside this write set, left for the members who own it

Four documents still say there is one context, and none of them is a context document: the
specification's README (the row "What the guestbook does" and "The only domain context is the
guestbook"), architecture § the opening line and § Rules between contexts ("One domain context
has nothing to border on"), and testing's fitness table ("vacuously true with one context", on
the boundaries and declarations rows). The project's CLAUDE.md lists what deleting the guestbook
deletes; since this change it also has to say that the text rule's words move into the to-do
list first.

<!-- z spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/testing.md -->
# Delta fragment — `design-testing`

*How anyone will know the to-do list works: the cheapest suite per requirement, the citation, the
fixtures, which tests must be seen red first and which are green by design. Written into the live
`spec/design/testing.md`. This fragment carries the entry and what belongs to the change alone:
the owner per requirement, where this design departs from `scenarios.md` and from a neighbour's
fragment, and what nobody in the composition can write.*


## Traceability — every requirement to its owner

| Requirement | Owner (the deciding claim) | Supplementary | Citation surfaces |
|---|---|---|---|
| R-1 | `tests/integration/` — service and router | unit model, vitest page and hook, e2e (3 scenarios) | marker, tag, in-name |
| R-2 | `tests/unit/` — the text rule over `todo-task-text.json`, and a generator | integration corpus/service/router, vitest rule and composer, e2e (2); fitness and smoke without citation | marker, tag, in-name |
| R-3 | `tests/integration/` — order, tie on `id`, 101 in one read | router envelope, corpus reversal, vitest page, e2e (5) | marker, tag, in-name |
| R-4 | `tests/integration/` — chosen state for all four pairs | router, vitest row, e2e (4); clause 6 by the smoke, the token fitness and `uat.md` (no citation) | marker, tag, in-name |
| R-5 | `frontend` — router, frame, not-found page | `test_spa_fallback.py` already covers the server half; the smoke | in-name |
| R-6 | `tests/integration/` — service and corpus on `PATCH` | router, vitest row, e2e (2) | marker, tag, in-name |
| R-7 | `tests/integration/` — the row gone, the rest untouched | vitest row (the confirmation, its only proof), e2e (1) | marker, tag, in-name |
| R-8 | `tests/integration/` — service and the deletion race | router `404`, e2e (3) | marker, tag |
| R-9 | `tests/integration/` — two writers interleaved behind a held row lock | e2e (2, overlapping sends, supplementary) | marker, tag |
| R-10 | `frontend` — page and hook with a failing client | — | in-name |
| R-11 | **manual**, as the requirement already states | tooling seeder tests and the corpus fitness, neither citing | — (`uat.md`) |

Refusal codes from `spec/design/api.md` § The to-do list's refusals: `todo_task_not_found`,
`todo_task_empty_patch`, `todo_task_text_empty`, `todo_task_text_multiline`,
`todo_task_text_too_long` — five codes, five router tests, plus the standard validation `422`, the
order of the refusals, and the contract test over every shape.

Characterisation (green by design): `frontend/src/router.test.tsx` "opens the guestbook at the
main address", pinning `spec/design/ui/system-states.md` § Interactions. Also green on the first
run: the new corpus-shape rules in `tests/fitness/test_golden_set.py`, pinning
`golden-set/README.md`, because their subject is test data written earlier in the same wave.

## Where this departs from `scenarios.md`

1. **The task's text cases are a file of their own, `todo-task-text.json`, not additions to
   `text-measurement.json`.** Adding a field its readers do not know turns guestbook cases red on
   both sides in the commit that adds it, while the frontend author runs beside the fixture author
   and must stop on an existing red; the fitness sweeps would import a bound that does not exist
   until implementation; and `text-measurement.json` is deleted with the guestbook. The values are
   the ones S-8's note and the additions table give, plus one case for `BR-07`'s precedence, which
   design-spec added after the scenarios were written.
2. **The fixture files are `todo-tasks-*.json`, not `tasks-*.json`**, for glossary § Task
   (process); the seed file is `todo-tasks-example.json`, design-architecture's name, not
   `tasks-welcome.json`. Every value stands.
3. **The black box does not bind S-5, S-6, S-8, S-13 or S-33.** Each looks a text up in a to-do
   fixture file by its sentence; the deciding claim is a rule over a corpus, which
   `tests/integration/test_todo_tasks_corpus.py` reads directly, and the black box reaches the
   corpus only through `e2e/suite/golden_set.py`, which no author may write. S-18, S-41 and S-43
   (store-ordered) are proved in integration only, as the scenarios already said.
4. **`refusal` in `todo-tasks-refused.json` holds the contract's code**, not the guestbook's
   mechanism word, because every to-do refusal has a stable code.

## Where this departs from `design/delta/architecture.md` — for the coherence gate

**Decision 4's second half does not hold: the corpus-reading test cannot move to
`frontend/src/lib/text.test.ts`.** `frontend/src/contexts/guestbook/lib/entryText.test.ts` asserts
the guestbook's verdicts, and they need `AUTHOR_MAX_LENGTH`, `MESSAGE_MAX_LENGTH` and
`QUERY_MAX_LENGTH` from `./guestbookEntry`. From `frontend/src/lib/` that import is refused by
`tests/fitness/test_context_boundaries.py::test_no_screen_reaches_into_another_contexts_folder`
(`_web_context_of` returns `guestbook` for a module outside every context, and only
`frontend/src/router.tsx` is exempt), and transcribing the bounds instead is what
§ Choosing what proves what forbids. So the reader stays where it is and changes one import line;
the moved `frontend/src/lib/text.ts` has no test file of its own, with the reason written in the
live document. Consequences, all simplifications: the fitness allow-list for
`text-measurement.json`, `D-04`'s witness path in `contracts/invariants/guestbook.md`, and
`golden-set/README.md`'s two mentions of the reader stay true, so items 3 and the reader half of
item 1 in that fragment's "Found outside every write set" disappear. The edit to
`entryText.test.ts` is inside the boundary as it stands.

**Resolved as COH-design-3** (AUTO, on `spec/design/conventions.md` § Frontend — where a file
goes, which now says "Only the rule moves up"): the reader stays, and the architecture fragment
follows this reading. The live document cites that rule where it keeps the reader in place, and
§ Four file sets names `frontend/src/lib/text.ts` as the import's target.

The architecture's build-tests-unit set also lists `tests/unit/test_entry_text_rules.py`; with the
separate corpus file it needs no edit.

## Found outside this write set — for the orchestrator

- **`e2e/suite/golden_set.py` has no author in `.specconf/stack.json` § `skills`**, and it is the
  black box's only permitted crossing into the corpus (`tests/fitness/test_e2e_isolation.py`,
  `PERMITTED_CROSSING`). This design routes around it (departure 3), but any change whose Gherkin
  must read a new fixture file cannot be built today. A template fault: the profile's write sets.
- **The feature file's claim.** `tests/fitness/test_context_declarations.py::test_every_feature_file_is_claimed_by_exactly_one_context`
  goes red when build-tests-e2e writes `e2e/suite/features/todo_list.feature` (wave 1), and only
  `spec/contexts/todo_list.md`'s `features` clears it — a path no implement author holds. A claim
  written earlier turns `test_every_screen_and_feature_a_context_names_is_on_disk` red instead.
  Options for the coherence gate: (A) the convergence round claims the file at design close and the
  on-disk case is declared red until wave 1; (B) the implement stage ends with the claim case
  declared red and reconcile-spec claims it; (C) the profile lets one implement member write the
  context header's `features` line. The same timing holds, one stage earlier, for the screen
  document design-ui writes and `test_every_registered_screen_is_claimed_by_exactly_one_context`.
- **`golden-set/README.md` has no author**, and this change makes two of its sentences false: its
  § `seed/` names one file, and its exception names one browser reader of the corpus where there
  are now two, each of its own context's file.
- **A same-wave read.** `frontend/src/contexts/todo_list/lib/todoTask.test.ts` reads
  `golden-set/fixtures/todo-task-text.json` with `readFileSync`, and build-tests-frontend runs
  beside build-tests-integration, which writes that file. `readFileSync` is not an import, so
  `tests/fitness/test_wave_dependencies.py` sees no edge and would refuse an `after` that nothing
  justifies. The file's declared reds are to be observed after the whole test wave; design-plan
  should say so on the frontend task, whose author may otherwise see a missing-file failure first.

## Checked against the invariants

`D-01`–`D-03`: no new witness — the fitness sweeps reach `todo_tasks` through `Base.metadata`.
The task-text invariant design-data calls for (the convergence round writes it): witnesses named in
the live document — a round trip, a corpus read by both sides, and a generator. `spec/invariants.md`:
no test asks for an identity, and nothing assumes a retention policy.

<!-- z spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/design/delta/ui.md -->
# Delta fragment — `design-ui`

*The to-do screen derived from the mock-up the user approved as drafted (`Q-14` → A, the 19
panels and the choices C-1…C-24 of `design/ui/index.html`), plus what the frame and the guestbook's
document had to say differently once the application has two screens. The screen document is
written into the live tree; this fragment says what moved and why. The two questions the mock-up
left open went to the person who asked for the change and are applied as answered (`Q-15` → A,
`Q-16` → A; § The two questions, answered).*




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

### The reconciliation phase -- what reality corrected in the design

<!-- z spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/reconcile/delta/converge.md -->
# Delta fragment — `review-converge`

*Written by the convergence round of coherence pass 10, `spec_sync` stage, for the seven findings
`COH-spec_sync-1` to `COH-spec_sync-7`. Findings 1 to 5 were settled automatically from the
document each one's `auto_basis` names; 6 and 7 by the user, at `Q-30` and `Q-31`. Each entry below
is an edit to the earliest document a finding names as its `ambiguity_source`, or the ready patch
under a finding where that patch lands in `spec/` or `contracts/`. `COH-spec_sync-6` has no entry:
its `ambiguity_source`, `docs/runbooks/restore-the-database.md` § When to use this, is under
`docs/`, which binds nothing and is outside the set Article IV makes a delta declare, and no
document in `spec/` or `contracts/` let the two readings in. The artefact repairs outside this
round's write set belong to their authors afterwards and are not declared here as made: the
`docs/` edits of `COH-spec_sync-6` and `COH-spec_sync-7`, the move of
`reconcile/user-guide-todo-list.md`, and the `--help` and comment text of `COH-spec_sync-5` in
`scripts/start.sh`, `scripts/help.sh`, `scripts/deploy.sh` and `scripts/preview.sh`.*


*Written by the convergence round of coherence pass 11, `spec_sync` stage, for the five findings
`COH-spec_sync-8` to `COH-spec_sync-12`. Three were settled by the user: `COH-spec_sync-8` at
`Q-32`, `COH-spec_sync-9` and `COH-spec_sync-10` at `Q-30`, `COH-spec_sync-11` at `Q-33`.
`COH-spec_sync-12` was settled automatically from `spec/design/architecture.md` § Who writes what,
and where the sets meet. Three of the five have no entry here. `COH-spec_sync-9` and
`COH-spec_sync-10` are about `docs/`, which binds nothing, and no document in `spec/` or
`contracts/` states what a restore brings back. `COH-spec_sync-12` is about `reconcile/delta/ops.md`
F-1, another member's fragment. Their ambiguity sources, the runbook and pass 10's resolutions in
`review/coherence.md`, are outside this round's write set. Their repairs are reconcile-ops' and are
not declared here as made: `docs/user-guide-todo-list.md` § Deleting a task, `docs/user-guide.md`
§ Deleting an entry, and `reconcile/delta/ops.md` (§ Confirmed correct and left alone, § The
convergence round, F-1). `CLAUDE.md` § What is an example took `COH-spec_sync-11`'s ready patch,
with a pointer to `spec/invariants.md` in place of its "Superseded by" clause. It lies outside
`spec/` and `contracts/` and needs no entry. No script is edited in this change (`Q-32`).*


## This change owns

No path. Pass 10's round listed `scripts/start.sh`, `scripts/help.sh`, `scripts/deploy.sh` and
`scripts/preview.sh` here, text only and build-backend's, for `COH-spec_sync-5`. The user then
decided at `Q-32`: "Follow-up fix right after merge". So this change edits none of the four, and
the pull request after it that corrects them carries its own changelog entry.

<!-- z spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/reconcile/delta/design.md -->
# Delta fragment — `reconcile-design`

*The technical documents the design stage wrote into `spec/design/`, read against what the
branch built. The API register held word for word against the router and the schemas, and so
did `spec/design/ui/system-states.md` and `spec/design/ui/guestbook.md` against the frame and the
not-found page: no edit. Where the code departed from the design, or the design's own count was
wrong, the specification now follows the code, and each departure is an entry below. The two ADR
drafts of `design/adr/` are promoted as the first two numbers of `spec/ADR/`; the index is
regenerated, not edited.*








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

<!-- z spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/reconcile/delta/docs.md -->
# Delta fragment — `reconcile-docs`

*The documentation half of the reconcile fan-out, in two documents for two readers. This
fragment is the intent note, written for whoever changes the to-do list in six months: why each
part has the shape it has, what lost, and what would have to change for the loser to win. The
user documentation is a separate page for the person using the screen:
`docs/user-guide-todo-list.md`.*

*This member edited nothing under `spec/` outside this change record, so the fragment carries no
entry for `delta.md`. The two files it edited outside the record, `README.md` and `CLAUDE.md`,
lie outside `spec/` and `contracts/` and need no entry. That is the rule
`design/delta/converge.md` applied to `CLAUDE.md` in the implement stage. Everything below is
carried by `close_stage` into `delta-history.md`.*

## The documentation written for the other reader

| File | What changed | Why |
|---|---|---|
| `README.md` | the opening paragraph: "The one feature is an example: a guest book" becomes two features, one of them an example; § Start here: the application opens with the guest book's entries and five example tasks, one of them done | both sentences became false with this change, and the first is the first thing a person taking the template reads |
| `CLAUDE.md` | the opening line names the to-do list beside the example; § What is an example gains a paragraph: the words of `BR-01` move into `spec/contexts/todo_list.md` before the guestbook is deleted, and the rule's code and the seeder's task half stay; "Everything else … stays" names the to-do list; the `--no-seed` comment names both lists | ADR-0001 § Consequences and `design/delta/spec.md` § Found outside this write set both reported that the deletion list was silent about `BR-01`. Nothing enforces it, and no design or implement author could write it. This stage's write set is the first to hold `CLAUDE.md`. The `--no-seed` comment described one list, and the seeder now fills two |
| `reconcile/user-guide-todo-list.md` | added, then removed in the convergence round: the to-do list for the person using it. It covers adding, ticking, correcting and deleting, other people on the same list, the example tasks, every refusal and failure sentence with what to do about it, what changed on the guest book, and what the list cannot do. The page now stands at `docs/user-guide-todo-list.md` | `docs/` is outside this member's write set, so the page was first written here with a note naming its destination. COH-spec_sync-7 settled the home (`Q-31`: "Move it to docs/ with the other guide."), and `spec/design/conventions.md` § Documentation now gives `docs/` a screen's user guide. The move and the row in `docs/README.md` are `reconcile-ops`'s; this member removed the copy here |

**The clean room found nothing to correct.** `evidence/cleanroom.md` is GREEN on all four steps
(setup, migrate, generate, check), so no first-run instruction was proved wrong. Its one warning
(an uncommitted file at the time of the run) is about what the run proved, not about any
instruction.

**The acceptance script needed no translation.** Every step of `uat.md` names what a person does
and sees in words the screen uses.

## Why this shape

Each entry gives what was chosen, what lost and why, what would have to change for the loser to
win, and the source. A source is always a durable document. Where a reason is an implementer's, it
is the one that implementer wrote into its module docstring or into the `ASSUMPTIONS` it
returned, which were banked at `loop back`. The `INTENT` paragraphs themselves did not reach this
step (§ What we do not know).

### 1. The to-do list is a bounded context of its own

- **Chosen:** `todo_list` sits beside the guestbook in every tree. The two share one rule, the
  text rule of `BR-01`, as a declared shared kernel.
- **Lost:**
  - *Tasks inside the guestbook.* Its `P-01` says an entry "either exists or it does not". Worse,
    the list would be deleted with the example the template tells its reader to delete.
  - *Tasks in Platform.* Platform holds no domain rules.
  - *The guestbook upstream and the to-do list conformist.* That describes where the rule's words
    sit, not whose rule it is.
  - *Separate ways, each context with its own copy of the rule.* Two copies is the shape of the
    `D-04` defect.
  - *A bought to-do product.* It brings the accounts the non-goals refuse.
- **Would flip it:** a rule that relates a task to an entry, or the guestbook no longer being
  deletable. Reversing costs a data migration and a rewritten contract (ADR-0001 § Consequences).
- **Source:** `spec/ADR/ADR-0001-todo-list-is-its-own-bounded-context.md`;
  `design/delta/domain.md` § The alternative that was tried.

### 2. A task's text is refused with a code, judged in the service, never by a schema constraint

- **Chosen:** three coded refusals, `todo_task_text_empty`, `todo_task_text_multiline` and
  `todo_task_text_too_long`, judged by the service. The request shapes carry `text` with no bound
  and import no part of the rule.
- **Lost:**
  - *The guestbook's convention, `Field(min_length, max_length)` answered with FastAPI's list.* It
    gives no code the screen can branch on. And a length constraint answers before anything else
    looks, so a long text with a line break inside would be called too long.
  - *A custom Pydantic error raised from a validator.* The code would sit inside the list that the
    frontend reduces to its message. It would also sit outside the router module, which is where
    the contract gate looks for each code.
  - *A handler in `app/core/errors.py`.* That puts domain knowledge into the framework module.
- **Would flip it:** a screen that no longer tells three reasons apart, together with `BR-07`'s
  precedence being dropped. Then the guestbook's convention would be enough. Until then one API
  has two regimes on purpose, and neither is to be "harmonised" toward the other (ADR-0002
  § Consequences).
- **How it broke first:** design-architecture followed the guestbook as the worked example and
  put the rule in the schema. design-api put it in the service, with codes. The user settled it
  (`Q-17`: "The service checks it, with a coded reason"). `spec/design/conventions.md` § Layers
  now says that a rule whose refusal carries a code is judged in `services/` (COH-design-1,
  COH-design-2).
- **Source:** `spec/ADR/ADR-0002-task-text-refusals-are-coded-not-schema-constraints.md`;
  `design/delta/converge.md`, pass 4; the module docstring of
  `app/contexts/todo_list/schemas/todo_tasks.py`.

### 3. One judgement for adding and correcting, in the order empty, one line, length

- **Chosen:** the shared kernel normalizes and trims the text first. Then an empty text is
  refused, then a line break left inside, then a text over 200 code points. A correction goes
  through the same function as an addition, and the browser applies the same order.
- **Lost:**
  - *Measuring before the line-break check*, which is what a schema length constraint would do.
    A pasted line break is often invisible in a one-line field, while a length is always visible.
    So the reason a person cannot find for themselves is the one they are given (`BR-07`).
  - *A separate check for corrections.* It could drift from the check for additions (`BR-10`).
- **Would flip it:** a field that shows line breaks. Then a person could see both reasons, and the
  order would stop hiding anything.
- **Source:** build-backend, the module docstring of
  `app/contexts/todo_list/services/todo_tasks.py`; `design/delta/spec.md`, the `BR-07` entry.

### 4. Two writers on one task are held by the shape of each statement

- **Chosen:** every write is one statement. It names only the columns the person changed, reads
  nothing first, never upserts, and runs at `READ COMMITTED`. `RETURNING` hands back the row as the
  statement left it. A tick writes the state chosen, never a flip.
- **Lost:**
  - *A version column.* It refuses the second writer, which is the opposite of `BR-10`, and
    telling a person their change lost is a named non-goal.
  - *A locking read.* It is correct, but it holds only while every path remembers to take the lock.
  - *The ORM's load, modify and flush.* A deletion that lands between the load and the flush
    surfaces as a stale-data error instead of "no longer exists".
  - *`REPEATABLE READ`.* The waiting statement fails with a serialization error instead of
    re-reading the row.
- **Would flip it:** lifting the non-goal "Telling a person that somebody else's change replaced
  theirs" (`spec/contexts/todo_list.md` § Deliberate non-goals). Then the version column wins, at
  the cost of a column, a refusal in the contract and a screen state.
- **The warning left in the code:** the service's docstring names each of the losing shapes, so
  that nobody "simplifies" the service into one of them. No sequential test tells them apart. Only
  `tests/integration/test_todo_tasks_concurrency.py` can, because it interleaves two writers on one
  row lock.
- **Source:** `spec/design/data-model.md` § `todo_tasks` › Two writers on one task;
  `design/delta/data-model.md`, decision (3); the service's module docstring.

### 5. `total` is the length of the one read, not a second count

- **Chosen:** `total = len(items)`.
- **Lost:** a `COUNT(*)` in a second statement, as the guestbook has. At `READ COMMITTED` the
  second statement sees its own snapshot. It can disagree with the rows beside it when somebody
  adds a task between the two. The guestbook needs its count because its read is one page.
- **Would flip it:** pages on the to-do list, which are a non-goal today. A page cannot imply how
  many tasks there are, so the count would have to come from the database.
- **Source:** build-backend, the docstring of `list_todo_tasks` in
  `app/contexts/todo_list/services/todo_tasks.py`.

### 6. `text` is `String(200)`, the rest of the rule is no `CHECK`, and the revision writes the literal

- **Chosen:**
  - a `varchar(200)` column: the last layer's refusal of a value that skipped the rule, and
    Postgres counts code points, which is the rule's unit;
  - no `CHECK` for an empty text or a line break;
  - `200` written as a literal in the revision;
  - no server default on any column.
- **Lost:**
  - *`Text`.* It leaves no last line of defence.
  - *`CHECK` constraints.* They would be a second hand-written copy of the thirty-code-point trim
    set and the seven line breaks, in SQL.
  - *The constant in the revision.* A released revision would change whenever the constant moved.
  - *A server default.* It would be drift, which the next autogeneration drafts away.
- **Would flip it:** moving the bound takes a new revision that widens the column, plus the
  constant, its browser copy and the boundary fixtures. `tests/integration/test_migrations.py` goes
  red on the day the constant moves without one. The 200 itself is the requester's number (`Q-9`,
  "up to 200 characters").
- **Source:** `spec/design/data-model.md` § `todo_tasks`; the module docstrings of
  `app/contexts/todo_list/models/todo_task.py` and
  `alembic/versions/5c58af1f8e8a_create_todo_tasks_table.py`; build-migration's `ASSUMPTIONS`.

### 7. The seven line breaks are one written set beside the model

- **Chosen:** `LINE_BREAKS`, seven code points written as numbers beside `TodoTask`. Its one
  browser copy is held equal to it by `tests/fitness/test_length_constants.py`.
- **Lost:**
  - *Each language's own idea of a line break.* Python's `str.splitlines` also breaks on the four
    C0 separators. JavaScript's line terminators leave out U+000B, U+000C and U+0085. A pasted
    text would then be refused on one side and stored on the other.
  - *U+000A and U+000D alone*, the other reading of `A-1`.
  - *Platform.* The guestbook keeps these characters as content, so the set is a fact about one
    context.
- **Would flip it:** the guestbook refusing line breaks too. Then the set is a fact about every
  text, and it moves to `app/platform/schemas/text.py`.
- **Source:** the model's module docstring; `design/delta/architecture.md`, decision 3;
  `requirements.md` § Named assumptions, `A-1`.

### 8. The browser's text rule moved out of the guestbook, and its test stayed behind

- **Chosen:** the rule moved unchanged from `frontend/src/contexts/guestbook/lib/entryText.ts` to
  `frontend/src/lib/text.ts`. The guestbook's corpus reader, `entryText.test.ts`, stays in the
  guestbook's folder with one import changed.
- **Lost:**
  - *A copy in the to-do context.* A rule with two homes is the shape of the `D-04` defect.
  - *Importing the guestbook's folder.* `test_no_screen_reaches_into_another_contexts_folder`
    refuses it.
  - *Moving the test up too.* It needs the guestbook's bounds, and nothing in the shared `lib/`
    imports a context.
- **Would flip it:** nothing in sight. This is where `spec/design/conventions.md` § Frontend puts
  a rule a second context needs ("Only the rule moves up"). One consequence: when the guestbook is
  deleted, its reader goes with it. What is left exercising the shared rule in the browser is the
  to-do list's `todoTask.test.ts`, which reaches `text.ts` through the to-do verdict.
- **Source:** `design/delta/architecture.md`, decision 4; COH-design-3; `design/delta/testing.md`
  § Where this departs from `design/delta/architecture.md`.

### 9. The screen shows a change only once the service has stored it

- **Chosen:** the query hook writes its cache only from the service's answer. It reads the whole
  list again after every change that went through, and it waits for that read inside the change.
  So the notice "Task added." and the new row arrive together.
- **Lost:** an optimistic update, rolled back on failure. It shows a change as made before it is
  stored, which `R-10` clause 2 forbids even for a moment. In the hook's words: "An optimistic tick
  rolled back on failure is still a tick the person saw made."
- **Would flip it:** relaxing `R-10` clause 2. The screen would feel faster on a slow connection,
  at the price of briefly lying on the one list whose point is to say what is done.
- **Source:** `design/delta/architecture.md`, decision 6; the module comment of
  `frontend/src/contexts/todo_list/hooks/useTodoTasks.ts`. The rejected alternative has no
  paragraph in `spec/design/`; `spec/design/architecture.md` states only the rule (§ Candidates for
  `spec/rationale/`).

### 10. The list is read afresh every time it is opened, and an earlier copy may show for a moment

- **Chosen:** `staleTime: 0` on the to-do query. The header link, the address and a reload all read
  the list. A copy read earlier in the same tab stays on screen until that read answers.
- **Lost:**
  - *Inheriting the 30 seconds of `frontend/src/main.tsx`.* A header link opened within 30 s
    showed the old read. The UAT would have failed a working system at step 14 (COH-implement-1).
  - *`gcTime: 0`*, which draws a loading outline instead of the earlier copy. The user decided:
    "Briefly showing it is fine." (`Q-28`).
- **The guestbook keeps its 30 s**, because this change froze the guestbook's behaviour (`SC-5`,
  and the architecture's freeze on its hook).
- **Would flip it:** people confused by the earlier copy changing into the fresh one. Then
  `gcTime: 0` is the change, plus one paragraph in `spec/design/ui/system-states.md`
  § Interactions.
- **Source:** `Q-25`, `Q-28`, `Q-29`; COH-implement-1, COH-implement-7, COH-implement-8;
  `design/delta/converge.md`, passes 7 and 8.

### 11. The add field never stops input, judges when it is left, and sends what it judged

- **Chosen:**
  - no `maxLength` and no counter;
  - the verdict and its sentence appear when the field is left or Enter is pressed;
  - Enter is handled on the key, because a form does not submit through a closed button, and
    Enter on a refused text has to say why;
  - the text is sent normalized and trimmed;
  - a failed add keeps the text in the field.
- **Lost:**
  - *`maxLength`.* It counts UTF-16 units, so a text of emoji stops at half the bound. That is the
    guestbook's `D-04` defect, one context over.
  - *Sending the text as typed.* The browser and the service would then measure different strings
    (`Q-21`, item 2; COH-design-11).
  - *Emptying the field on failure.* "Retrying otherwise means typing it again."
- **Would flip it:** a change to the unit the rule counts in. That is a change to `BR-01`, for
  both contexts.
- **Source:** build-frontend, the module comment of
  `frontend/src/contexts/todo_list/components/TodoTaskComposer.tsx`;
  `spec/design/ui/todo-list.md` § The add field; COH-design-11.

### 12. Each list is filled on its own condition, and an example task is added, then ticked

- **Chosen:** the seeder asks the guest book whether it has entries and the to-do list whether its
  `total` is zero, each whatever the other holds. Every example task is posted with its text alone,
  and the done one is then marked through the marking route.
- **Lost:**
  - *One condition for the whole environment*, "nobody has written in it yet". An environment
    that existed before the to-do list, such as stage or an open preview, would never get its
    example tasks (`Q-10`).
  - *An example born done.* The create shape has no `done`, and a task is never born done (`BR-08`,
    `Q-12`).
  - *A guarantee in the store.* "Only while empty" is a statement about the absence of every row,
    and no key or index can state that.
- **Accepted as the price:** a person who adds a task in the seconds between the read and the
  posts, or two fillings at once, leaves the examples beside that task or twice over. And outside
  production, a list emptied by hand is filled again at the next deploy, because every deploy runs
  the seeder. The user guide says so.
- **Would flip it:** environments that never outlive the arrival of a new list. Then one condition
  per environment would do. While stage and open previews outlive it, one condition cannot.
- **Source:** the module docstring of `scripts/seed_golden_set.py`; `spec/design/architecture.md`
  § What a new environment starts with, whose condition is "a list that holds nothing yet", asked
  of each list (COH-spec_sync-4); `spec/design/data-model.md` § `todo_tasks`, its last
  paragraphs.

### 13. The contract: one `PATCH`, an envelope with a count, and the moment of adding on the wire

- **Chosen:**
  - marking and correcting are one `PATCH`, and its absent fields are never written;
  - the list is `{items, total}`, although it has no pages;
  - `created_at` is published, although the screen does not show it;
  - there is no read of one task.
- **Lost:**
  - *Two sub-resources, `PUT …/done` and `PUT …/text`.* The guestbook's `PATCH` is the shape in
    force, and with it a future field is an optional addition. A toggle endpoint was never open,
    because `BR-09` forbids a flip.
  - *A bare array.* Adding the count later would break every caller.
  - *Leaving `created_at` off.* `BR-08` and `BR-11` make promises about it that nobody could check.
- **Would flip it:** a requirement to read one task. That adds an endpoint and changes none of
  these.
- **Source:** `design/delta/api.md`, the `spec/design/api.md` entry, "Also taken here".

### 14. The frame: two text links, and a name that is plainly a placeholder

- **Chosen:**
  - "Guestbook" and "To-do list" are text links after the lockup, with the current one marked,
    grouped as "Screens";
  - the lockup is the placeholder "Product name" with the initial "P", and it still leads to the
    guestbook;
  - the not-found sentence, "There is nothing at this address.", counts no screens.
- **Lost:**
  - *A pill switcher.* It reads as a filter, like the guestbook's Newest and Oldest.
  - *The lockup as the only way back.* It leads in one direction only.
  - *A top bar or a side panel.* § One column withdrew both.
  - *Keeping "Guestbook" as the lockup.* It would stand beside a navigation link of the same name,
    and it named the product after one of its screens.
- **Would flip it:** nothing named. A third screen adds a link in `PageFrame.tsx`. The not-found
  sentence was chosen so that the next screen cannot make it false.
- **Source:** `design/delta/ui.md`, choices C-1, C-2 and C-22; the module comment of
  `frontend/src/components/shell/PageFrame.tsx`.

### 15. A done task is shown three ways, and never faded

- **Chosen:** the tick, the strike-through and the checked state together. The text is in
  `--color-muted`, which measures 7.09:1 on the card.
- **Lost:** greying the text with `--color-disabled` or with opacity. That defect has happened
  once already: quiet text measured 2.92:1 on a card, below the 4.5:1 floor (`R-4` clause 6).
- **Would flip it:** a token that looks quieter and still clears 4.5:1. The rule is the floor,
  not the colour.
- **Source:** `spec/design/ui/todo-list.md` § A task's row; `requirements.md` § Defects that have
  already happened once.

### 16. Two temporary shapes, each with its exit named

- **The guestbook's footer lives in the frame, as a default.** The footer is each screen's own.
  But `GuestbookPage.tsx` was frozen for this change, so `PageFrame`'s `footer` defaults to the
  guestbook's sentence, and the not-found page passes none. **Exit:** the guestbook screen passes
  its own sentence, and the constant goes. **Source:** build-frontend's `ASSUMPTIONS`; the comment
  on the constant in `PageFrame.tsx`.
- **The done-text contrast check lives in `e2e/ui/test_smoke.py`**, not beside the style helpers in
  `e2e/ui/styles.py`, because T-12's file list left `styles.py` out. **Exit:** a change whose write
  set holds `styles.py` can move it. **Source:** build-tests-e2e's `ASSUMPTIONS`.

### 17. The to-do list's ownership rows come last in `.github/CODEOWNERS`

- **Chosen:** five per-context rows at the end of the file, naming the owner the catch-all names.
- **Lost:**
  - *Placing them earlier.* GitHub applies the last matching rule, so a row above the catch-all
    would be overridden.
  - *Rows for the guestbook.* It is the example that gets replaced.
- **Would flip it:** a real owner for the to-do list, recorded somewhere. Today none is (T-24).
- **Source:** build-platform's `ASSUMPTIONS`; `tasks.md` T-24.

## How we know

| Kind of source | Entries |
|---|---|
| An ADR, promoted in this stage | 1, 2 |
| A user decision recorded in the change | 2 (`Q-17`), 6 (`Q-9`), 10 (`Q-25`, `Q-28`, `Q-29`), 11 (`Q-21`), 12 (`Q-10`, `Q-12`) |
| A design fragment's recorded decision and its rejected alternatives | 3, 4, 7, 8, 9, 13, 14 |
| A normative document under `spec/design/` | 4, 6, 8, 11, 12, 15 |
| A resolved coherence finding | 2, 8, 10, 11, 12, and § What broke along the way |
| An implementer's module docstring (build-backend, build-migration, build-frontend) | 3, 4, 5, 6, 7, 9, 11, 12, 14 |
| An implementer's `ASSUMPTIONS`, banked at `loop back` | 6 (build-migration), 16 (build-frontend, build-tests-e2e), 17 (build-platform), and § What broke along the way |

## What we do not know

1. **The implementers' `INTENT` paragraphs.** The dispatch to this step carried none. The
   session-history tools return a sub-agent's hand-back cut to a few hundred characters, and the
   raw transcripts are not to be read directly. So the why of every implementation choice above
   rests on the module docstrings and the banked `ASSUMPTIONS`. Whatever an implementer weighed and
   rejected without writing it into either is lost. This concerns all nine members of the implement
   stage: build-backend, build-frontend, build-migration and build-platform, and the five test
   authors.
2. **Three values build-tests-integration chose that no document fixes.** They are the letter `a`
   as "an ASCII letter" in the boundary cases, every second task of the 101-task case marked done,
   and the descriptions in `todo-task-text.json`. Its report says so and gives no reason. None is
   needed for correctness, and each can change without touching a rule.
3. **Why 200.** The number is the requester's (`Q-9`). No reason beyond that choice was asked for
   or recorded. Moving it is a product decision, and entry 6 says what it costs.
4. **Not decided: the largest number of tasks.** No ceiling is set, and the whole list is read and
   drawn at once (`spec/contexts/todo_list.md` § Open questions). This is a decision for a person,
   not a gap in anybody's reasoning.
5. **Two seams nothing guards.** Both are known and named in the ADRs, and neither is guarded
   because nobody built the guard, not because somebody decided against one. No test refuses a
   foreign key from `todo_tasks` to `guestbook_entries` (ADR-0001). The five refusal sentences have
   two copies, one in the router and one in `spec/design/api.md`, and nothing compares them
   (ADR-0002).

## What broke along the way

No debug stage ran, and nothing needed `build-debug`. This is what broke, and why:

1. **A migration landed in another project's database.** build-migration's first
   `./scripts/db.sh migrate` applied this change's revision to a different project's Postgres. That
   project's container held `0.0.0.0:5432`, this repository's default database URL names
   `localhost:5432`, and the scripts check only that compose lists `db` as running. The user
   approved a revert. The other container was stopped, and this repository's database went back to
   `127.0.0.1:5432`. The template's scripts still cannot tell the two databases apart (banked as
   `PROC-46`). **Source:** build-migration's `ASSUMPTIONS`; `sessions/76720804-…/summary.md`, S5,
   W9 and W10.
2. **The black box could not run between the test waves.** So its 22 scenarios and 4 smoke cases
   were collected but never seen failing. `./scripts/test.sh e2e` builds the SPA first, and that
   build type-checks all of `frontend/src`. That includes the first wave's vitest files, which
   import modules only the second wave writes (`PROC-41`). The suite's green is evidence of
   behaviour. It is not a red-first proof. **Source:** build-tests-e2e's `ASSUMPTIONS` (status
   CONTENTION); `sessions/76720804-…/summary.md` § What was not done.
3. **A defect in a first-wave test surfaced only in the second wave.** The test wrote
   `await act(() => mutation.mutate(...))`, which awaits the `void` that TanStack's `mutate`
   returns. `@typescript-eslint/await-thenable` needs types, and while the imported modules did not
   exist, their types were `any`. build-frontend returned `TEST_DISPUTED`, and the test author fixed
   the test (TD-3). **Source:** build-frontend's `ASSUMPTIONS`; `PROC-45`.
4. **The missing routes answered 405, not 404.** While no to-do route existed, `POST`, `PATCH` and
   `DELETE` got 405 because a GET-only route matched those paths. The plan had predicted a JSON 404.
   This is worth knowing when reading the red-first failures of a new resource. **Source:**
   build-tests-integration's `ASSUMPTIONS`.
5. **The header link showed an old list.** Entry 10 covers it.
6. **Documents were left false by the new corpus files.**
   - The deletion lists in `spec/README.md` and `CLAUDE.md` would have deleted the to-do list's
     fixtures with the guestbook (COH-implement-3). Fixed.
   - Five test docstrings and three comments still counted one table, one context or one resource
     (COH-implement-4, COH-implement-9). Fixed.
   - Five sentences of `golden-set/README.md` are still false, because no member may write that
     file. They go to a follow-up pull request (`Q-26`) and template issue #92.

   **Source:** `review/coherence.md`, passes 7 and 8; `design/delta/converge.md`.

## Candidates for `spec/rationale/`

**None was written, on purpose.** `spec/rationale/README.md` sends a rejected alternative to its
ADR or to the decision paragraph of a normative document, "never here", and a rule that holds to
`spec/design/`. Every durable reason in § Why this shape already has such a home:

- ADR-0001 and ADR-0002 (entries 1 and 2);
- `spec/design/data-model.md` § `todo_tasks` (entries 4 and 6);
- `spec/design/conventions.md` § Layers and § Frontend (entries 2 and 8);
- `spec/design/ui/system-states.md` § Interactions (entry 10);
- `spec/design/api.md` § The to-do list's refusals (entries 2, 3 and 13);
- `spec/design/ui/todo-list.md` (entries 11 and 15).

The implementation-level reasons are in module docstrings, which is where the constitution
(article IX) puts intent. A note under `spec/rationale/` would be a second home for each of them.

**One reason has no normative home.** The rejection of an optimistic update (entry 9) lives in
the change record and in the hook's module comment, and `spec/design/architecture.md` states the
rule without it. If it is to bind, its home is a decision paragraph in that document, which is
`reconcile-design`'s, not this tree.

## Candidates for operator documents and runbooks

These are for `reconcile-ops`, whose tree is `docs/`, and for the orchestrator:

- **`docs/user-guide-todo-list.md`**, moved from `reconcile/user-guide-todo-list.md`, with a row in
  `docs/README.md`'s table. Decided at `Q-31` (COH-spec_sync-7), and `reconcile-ops`'s to make.
- **`docs/troubleshooting.md`: migrations or tests reaching another project's database.** Symptom,
  cause (another container holds `0.0.0.0:5432`), and fix (find it with `docker ps`, then stop it
  or move one project's port). It is needed until `PROC-46` lands.
- **`docs/operations.md`: an emptied list is filled again at the next deploy** outside production,
  for the to-do list exactly as for the guest book.
- **Script help and comments that still describe one list.** build-backend reported some of them,
  and each was confirmed here:
  - `scripts/start.sh`: `--help` ("--no-seed leave the guest book empty") and the comment on
    `seed_when_up`;
  - `scripts/deploy.sh`: the comment above the seed step, line 621;
  - `scripts/preview.sh`: the comment at line 199;
  - `scripts/help.sh`: the `seed.sh` row, line 89.

  Scripts belong to no reconcile member, so this item is the orchestrator's.

<!-- z spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/reconcile/delta/ops.md -->
# Delta fragment — `reconcile-ops`

*The operator's documentation under `docs/`, read against what the branch does to running the
system. Every edit this member made is under `docs/`, which binds nothing and is not part of the
`spec/` set Article IV makes a delta declare. So this fragment carries **no `ADDED` / `MODIFIED` /
`REMOVED` entry** and no boundary table. It records what changed operationally, which page took
each change, what was confirmed correct and left alone, the one runbook the change earned, and the
findings that belong to somebody else.*

## What changed about running the system

Read from `git diff main...HEAD` over the operational trees `.specconf/stack.json` declares
(`infra/`, `.github/workflows/`, `scripts/*.sh`, `alembic/versions/`, `Dockerfile`,
`docker-compose.yml`), the schema tree, and every environment read.

| # | What changed | Where it is in the code | Pages that took it |
|---|---|---|---|
| 1 | Revision `5c58af1f8e8a` (parent `a1b2c3d4e5f6`) creates `todo_tasks` (`id`, `text` `String(200)`, `done`, `created_at`) and `ix_todo_tasks_created_at_id`. Backward compatible, no data, a plain index build on a table created one step earlier, no manual step: it runs as deployment step 3 | `alembic/versions/5c58af1f8e8a_create_todo_tasks_table.py` | `docs/backup-and-recovery.md` (what cannot be rebuilt now names both tables); `docs/runbooks/restore-the-database.md` (both lists rewind together, count both tables, a restore to a moment before the to-do list has no `todo_tasks`, and option B can copy one table alone); `docs/runbooks/roll-back-a-release.md` (the table and its tasks survive a rollback) |
| 2 | A new HTTP surface, `GET`/`POST /api/todo-tasks` and `PATCH`/`DELETE /api/todo-tasks/{todo_task_id}`, and a second screen at `/todo-list`. The post-deploy smoke now asks `GET /api/todo-tasks` too, derived from `contracts/openapi/todo_list.yaml` with no script edit. The collection read takes no parameters and returns every task | `app/contexts/todo_list/`, `contracts/openapi/todo_list.yaml`, `scripts/smoke_contract.py` (unchanged, reads the new contract), `frontend/src/router.tsx` | `docs/solution-overview.md` (two screens, two tables, the to-do list not an example); `docs/security.md` (anybody may add, correct, tick and delete any task); `docs/operations.md` § Capacity (the unpaged whole-list read and the absence of any ceiling); `docs/runbooks/roll-back-a-release.md` (past the first to-do release, the rollback smoke gets a 404 on `/api/todo-tasks` and the unreverted shell shows "The tasks could not be loaded."); `docs/runbooks/release-to-production.md` (check `/todo-list` too, and an empty production list is correct); `docs/troubleshooting.md` (new symptom: the to-do list fails to load while the guest book works, told apart by `404` or `500`) |
| 3 | The seeder fills two lists, each on its own condition: welcome entries while the guest book holds none, example tasks while the to-do list's `total` is zero. Tasks are added not done and the done one is marked afterwards. It prints one line per list, costs one `GET` per list on a later run, refuses production before reading either list, and gives an environment that existed before the to-do list its examples on the next run. A part-way or simultaneous fill is a state it never repairs | `scripts/seed.sh`, `scripts/seed_golden_set.py`, `golden-set/seed/todo-tasks-example.json` | `docs/operations.md` § Filling an environment; `docs/deployment.md` (the seed line after the steps, and § A new environment is not empty); `docs/runbooks/preview-environment.md` and `docs/aws-account-setup.md` § 11 (what a raised preview shows); `docs/troubleshooting.md` (new symptom: too few example tasks, none done, or each twice); `docs/runbooks/refill-the-example-data.md` (new); `docs/runbooks/README.md` (the index row) |
| 4 | Restore and incident wording that said "the whole book" and "entries" now covers both lists | follows from 1 | `docs/runbooks/incident-first-response.md` step 4; `docs/runbooks/README.md` |
| 5 | The vitest suite reads a second corpus file, `golden-set/fixtures/todo-task-text.json`, which is one more reason `golden-set/` routes the frontend CI job | `frontend/src/contexts/todo_list/lib/todoTask.test.ts` | `docs/troubleshooting.md` § A CI job I expected to run was skipped |
| 6 | **No environment read added or removed.** `git diff main...HEAD -- app frontend/src scripts alembic` holds no `os.environ`, `getenv`, `import.meta.env` or `process.env` line on either side, and no Terraform, workflow, Dockerfile or compose file changed | — | none. `docs/configuration.md` confirmed as it stands |

## Confirmed correct and left alone

- `docs/configuration.md`: no variable, no Terraform value, no environment number moved.
  `APP_ENV` still "is what stops the seeder writing to production", word for word what the seeder
  does.
- `docs/deployment.md` § The order the steps happen in: the migrate step and the smoke are
  described generically ("every read-only endpoint `contracts/openapi/` declares"), which is true
  of the new route with no edit.
- `docs/runbooks/run-a-migration.md`: generic and true. The new revision builds its index on an
  empty table it has just created, so "a table lock on a large table" does not apply to it, and the
  300-second timeout is not approached.
- `docs/monitoring.md`: nothing new is observable or monitored. The to-do list's modules write no
  log line of their own (no logger anywhere under `app/contexts/`).
- `docs/runbooks/rotate-database-credentials.md`: untouched by this change.
- `docs/user-guide.md`: it is the guestbook's page (`CLAUDE.md` deletes it with the example) and
  true of the guestbook now that its restore sentence follows `Q-30` (COH-spec_sync-10).

## The convergence round — `COH-spec_sync-6` and `COH-spec_sync-7`

Applied as the user decided them, with the smallest edit each allows. No other section moved.

| Finding | Decision | Page | Edit |
|---|---|---|---|
| `COH-spec_sync-7` | `Q-31` = A: "Move it to docs/ with the other guide." | `docs/user-guide-todo-list.md` (new) | the page `reconcile-docs` wrote at `reconcile/user-guide-todo-list.md`, moved here without its placement note. Its sentences are unchanged apart from the one `COH-spec_sync-6` names. The paths it gave in backticks are now links, relative to `docs/`: its **Normative source:** line, the troubleshooting cell and the last paragraph. `reconcile-docs` removes the copy in the change record (its fragment says so) |
| `COH-spec_sync-7` | the same | `docs/README.md` § The documents | one row after `user-guide.md`: "`user-guide-todo-list.md` — the to-do list, for the person using it" |
| `COH-spec_sync-6` | `Q-30` = A: the guide follows the runbook | `docs/user-guide-todo-list.md` § Deleting a task | "A restore from backup is the only way back, and it returns the whole application, the guest book included, …" becomes "Whoever operates the environment can bring the list back from a backup as it was at an earlier moment, within the backup window, and that takes tens of minutes; whatever was changed on the list since that moment is lost." |
| `COH-spec_sync-6` | the same | `docs/runbooks/restore-the-database.md` § When to use this | "a restore returns the *whole database*, both lists, …" becomes "a restore brings back what it copies as it was at a moment in the past — the whole database under A, one list or the rows you need under B (step 3) — and every write since that moment to what it brings back is lost." |
| `COH-spec_sync-6` | the same | `docs/runbooks/incident-first-response.md` step 4 and `docs/runbooks/README.md`, the closing paragraph | both restatements now say what option B allows, in the runbook's words |

Left alone because no finding named them: `docs/user-guide.md` § Deleting an entry says a restore
"returns the whole book to a moment in the past, not one entry". That sentence was there before
this change and is what the to-do guide first copied. Under option B it is not true. A one-line
repair on the same lines as `Q-30` would fix it, and COH-spec_sync-10 names it. Also left alone: the runbook candidate `reconcile/delta/docs.md`
lists for `docs/troubleshooting.md` (another project's container holding port 5432, until `PROC-46`).

## The convergence round of pass 11 — `COH-spec_sync-9`, `COH-spec_sync-10` and `COH-spec_sync-12`

The ready patches of `review/coherence.md` § Pass 11, applied with the smallest edit each allows.

| Finding | Decision | Page | Edit |
|---|---|---|---|
| `COH-spec_sync-9` | `Q-30` = A: "one list, or chosen tasks" | `docs/user-guide-todo-list.md` § Deleting a task | "can bring the list back from a backup as it was at an earlier moment, …; whatever was changed on the list since that moment is lost." becomes "can bring back from a backup the whole list or only the tasks you name, as they were at an earlier moment within the backup window, and that takes tens of minutes. What comes back replaces what is there now, so any change made since that moment to what is brought back is lost." |
| `COH-spec_sync-10` | `Q-30` = A, covering the guest book's guide too | `docs/user-guide.md` § Deleting an entry | "the only way back — which takes tens of minutes and returns the whole book to a moment in the past, not one entry." becomes "the only way back. Whoever operates the environment can bring back the whole book or only the entries you name, as they were at an earlier moment within the backup window, and that takes tens of minutes; any change made since that moment to what is brought back is lost." |
| `COH-spec_sync-10` | the same | this fragment, § Confirmed correct and left alone and § The convergence round | the guest book's guide is no longer called true in one section and untrue in the other |
| `COH-spec_sync-12` | AUTO: `spec/design/architecture.md` § Who writes what, and where the sets meet | this fragment, F-1 | routes `scripts/*.sh` to `build-backend`, records the user's deferral at `Q-32`, and no longer cites the `CLAUDE.md` line `reconcile-docs` rewrote |

## The runbook this change earned

`docs/runbooks/refill-the-example-data.md`. With this change the seeder has two independent
conditions and a two-phase add-then-mark for tasks. A fill that stopped part way leaves five
tasks with none done, or fewer than five; two fills at once leave the examples twice. The seeder
never repairs either, because it fills only an empty list (`spec/design/data-model.md` § Two writers
on one task, "Filling an empty list is the one rule here the store does not hold"; requirements
edge `E-21`, races `W-5` and `W-6`). The repair is a person's to make on a live preview or stage:
confirm the environment is not `prod`, empty the one list on its screen, run
`./scripts/seed.sh --base-url`, and read the header counts. The page says at the top that the procedure **has not been
performed on a deployed environment**, and names the only thing that proves it
(`tests/tooling/test_seed_golden_set.py`, against a faked API).

## Findings — outside this member's write set

- **F-1. The seeder's two lists are not yet in the scripts' own help and comments.**
  `./scripts/start.sh --help` still says `--no-seed` will "leave the guest book empty. By default a
  guest book that has no entries is filled from golden-set/seed/…" (`scripts/start.sh` lines
  48-51). The comments at `scripts/start.sh` lines 106, 113-114 and 170, `scripts/deploy.sh` lines
  620-622 and `scripts/preview.sh` lines 199-201 still describe one list. `CLAUDE.md` said the
  same, and `reconcile-docs` rewrote that line in this stage (§ Running and developing). The
  behaviour is two lists, each on its own condition. `--help` is what an operator reads, and
  `scripts/` is outside `docs/`, so it is reported rather than edited: `scripts/*.sh` to a
  `build-backend` repair (`spec/design/architecture.md` § Who writes what, and where the sets meet;
  COH-spec_sync-5, COH-spec_sync-8). The user deferred that repair to a text-only pull request with
  a changelog entry right after this change merges (`Q-32` = A: "Follow-up fix right after
  merge."), so no script is edited in this change (`spec/design/architecture.md` § The files).
- **F-2. Resolved: the to-do screen's user guide.** It became `COH-spec_sync-7`. The user decided
  `Q-31` = A, and `spec/design/conventions.md` § Documentation now gives `docs/` one guide per
  screen. The page stands at `docs/user-guide-todo-list.md` (§ The convergence round above).
- **F-3. Present before this change, left alone because the edits are differential.**
  `docs/operations.md` § The logs gives `app.services.guestbook_entries: entry amended id=…` as the
  application's line format, but no module under `app/contexts/` logs anything. `docs/deployment.md`
  says "seven steps" and lists eight.
- **F-4. No rule without a home.** Every behaviour these pages describe cites where it is
  specified: `spec/design/architecture.md` § What a new environment starts with,
  `spec/design/data-model.md` § Two writers on one task, `spec/contexts/todo_list.md` § Open
  questions, `spec/design/ui/todo-list.md` § Copy. Nothing here needs a decision.

<!-- z spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/reconcile/delta/spec.md -->
# Delta fragment — `reconcile-spec`

*The design wrote `spec/contexts/` before any code existed (`design/delta/domain.md`,
`design/delta/spec.md`). This pass set every claim in those two fragments against the built
branch: the service, schemas, router and model of the to-do list, the screen's rule, hooks, page,
row, composer and delete question, the seeder and its corpus, and what the tests assert. The
design held, with one gap. Two rules the design left side by side (`BR-10` and `BR-13`) name
different reasons for one corner case. The build settles it, deliberately and under test, and
the context document now says so in one paragraph. No rule identifier is minted, and no
behaviour was found wrong.*


## Every claim of the design baseline against the built branch

| Claim (where the design put it) | What the branch does | Verdict |
|---|---|---|
| `P-02` step 1, `BR-08`: a new task is stored not done with its moment of adding, whatever the request claims, and appears first without a reload | the create shape has no `done` and a sent one is ignored; the service writes `done` false and the moment from its own clock; the screen reads the whole list again after every add that went through | holds |
| `BR-06`: normalized and trimmed by the shared rule, then empty, then over 200 code points; 205 spaces are empty; inner whitespace kept | `normalize` then the three verdicts in the service and in the browser's rule; corpus `todo-task-text.json` read by both suites | holds |
| `BR-06`: the screen accepts exactly what the application accepts and never stops at a length | no length limit on either field; the same verdict function gates add and correction; the two bounds and the two sets of line breaks are held equal by `test_length_constants.py` | holds |
| `BR-07` (design-domain): one written set of seven line breaks, read after the trim | `LINE_BREAKS` in the model and its browser copy, both applied to the trimmed text | holds |
| `BR-07` (design-spec paragraph): too long and more than one line is refused as more than one line, on the screen and by the application alike | the line-break check comes before the length check on both sides; `test_a_text_too_long_and_on_two_lines_is_refused_as_multiline` | holds |
| `BR-08`: an example task shown done is added not done and then marked | the seeder adds all five examples, then marks the done one | holds |
| `BR-09`: marking records the state chosen, leaves the text alone, and a done task stays readable | a marking sends `done` alone and the service writes it as sent; done is shown by the box, a strike-through and the checked state, never by fading | holds |
| `BR-10` (design-domain): a correction changes the text alone; later wins per aspect; a correction never undoes a marking under concurrency | one `UPDATE` naming only the columns given, no read before it; `test_todo_tasks_concurrency.py` interleaves two writers | holds |
| `BR-10` (design-spec paragraph): a correction is held to `BR-06` and `BR-07`, a refused one keeps the old text, and the person gets the addition's reason | one judgement serves both writes; the editor uses the add field's verdict and sentences; `test_a_refused_correction_keeps_the_text_it_had` | holds |
| `BR-11`: one list, newest first, total order, never moved by marking or correcting, one direction | ordered by moment of adding then identifier, both descending, with no parameters; the screen never sorts again | holds |
| `BR-12`: the same text twice is two tasks | no uniqueness anywhere; the scenario marks one of two "Buy bread" | holds |
| `BR-13`: deletion is permanent; a change to a gone task changes and creates nothing and says so; a second deletion is refused | single-statement update and delete with no upsert; not found when no row matched | holds, with the gap recorded in the entry above |
| § Neighbours: one shared rule, nothing else crosses | the browser's text rule moved out of the guestbook's folder into the frame's shared `lib/text.ts`; the guestbook's own diff is import lines only; no record, read or screen crosses | holds |
| § Open questions: no ceiling on the number of tasks | none in the service, the schema or the screen | holds |
| guestbook.md `BR-01` paragraph (design-spec): a task's text follows the same normalization, trim set and unit, with bounds of its own | both contexts call the one `normalize` and `length`; the guestbook's bounds of 80 and 1000 are untouched | holds |
| guestbook.md opening, § Boundaries, `neighbours`: the guestbook is one of two contexts joined by a shared kernel | the guestbook's behaviour is unchanged (its diff is imports and one comment line), and the declaration is read by `test_context_declarations.py` | holds |

## Every requirement accounted for in the built behaviour

| Requirement | Where the build carries it | In a context document |
|---|---|---|
| R-1 | service `add_todo_task`, create shape without `done`, page refetch after add | `P-02` step 1, `BR-08`, `BR-12` |
| R-2 | `judge_todo_task_text` and `todoTaskTextVerdict`, the shared text rule | `BR-06`, `BR-07` |
| R-3 | `list_todo_tasks` order, `staleTime: 0`, the page's empty sentence | `P-02` step 2, `BR-11` |
| R-4 | `mark_todo_task`, the row's box and done styling | `BR-09` |
| R-5 | the router and the frame's navigation | none, the frame's by design (§ Neighbours) |
| R-6 | `correct_todo_task`, the row's editor | `BR-10`, and now the corner in `BR-13` |
| R-7 | `delete_todo_task`, the delete question | `P-02` step 5, `BR-13` |
| R-8 | not found on no row matched; the refusal order | `BR-13` |
| R-9 | single-statement column-scoped writes | `BR-10` |
| R-10 | cache written only from answers; `todoTaskFailure` | none, the screen's by design (§ Neighbours) |
| R-11 | the seeder and `todo-tasks-example.json` | none, the environment's by design; `BR-08` binds the examples |

No requirement is unaccounted for. No built behaviour was classified as a defect.

## Divergences left to other members

- **Technical, for `reconcile-design`, and already carried there:** a request that changes both
  the text and the state at once, the refusal of a request that sets neither, and the standard
  validation answer for a body of the wrong shape. The screen never sends any of them, they
  are about the shape of a request rather than a person's action, and `spec/design/api.md`
  already describes each. No context document mentions them, and none should.

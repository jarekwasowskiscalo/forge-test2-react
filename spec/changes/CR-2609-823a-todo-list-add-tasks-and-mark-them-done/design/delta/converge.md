# Delta fragment — `review-converge`

*Written by the convergence round of coherence pass 1, `requirements` stage. The requirements
stage has no fragment directory of its own, and `close_stage` assembles `delta.md` from
`design/delta/` and `reconcile/delta/` alone, so this entry sits in the first of them. The
edits this round made to `requirements.md` and `impact.md` are inside the change record and
need no entry.*

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

*Written by the convergence round of coherence pass 4, `design` stage, for the eight findings
`COH-design-1` to `COH-design-8`. Each entry below is an edit to the earliest document a finding
names as its `ambiguity_source` (constitution, Article VIII). The artefact-level patches under
each finding in `review/coherence.md` belong to the authors the convergence round sends again,
and they are not declared here. This round's edits to `requirements.md` (`COH-design-7`) are
inside the change record and need no entry.*

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

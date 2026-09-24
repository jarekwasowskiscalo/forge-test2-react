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

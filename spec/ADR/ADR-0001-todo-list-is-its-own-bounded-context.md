---
id: ADR-0001
title: The to-do list is a bounded context of its own, sharing only the text rule with the guestbook
status: Proposed
date: 2026-09-24
cr: CR-2609-823a
supersedes: []
superseded_by: null
aliases: []
---

# ADR-0001 — The to-do list is a bounded context of its own, sharing only the text rule with the guestbook

## Context

Before this change the system had one bounded context, the guestbook. It declared
`neighbours: []`, and every context sweep in `tests/fitness/` was vacuously true. The
requirements of `CR-2609-823a` bring something no context described: a **task**, which has a
text, a state switched both ways (done and not done) and a moment of adding (`R-1`, `R-3`,
`R-4`, `R-6`). Every rule about it (`R-1`…`R-4`, `R-6`…`R-9`) needs one owner. The search that
found the concept absent is in `design/delta/domain.md` § The concept is absent.

These constraints forced the choice:

- **The guestbook's flow rules out a state.** `P-01` says: "There are no intermediate states,
  no lifecycle … An entry either exists or it does not." Tasks placed there would make that
  sentence false for its own context (requirements Self-check 24).
- **No word, rule or flow crosses.** The guestbook's words (entry, author, message, edited)
  describe nothing a task has, and no requirement relates a task to an entry. `Q-10` fills each
  list on its own. The same seven characters mean opposite things on the two sides: a message
  keeps its line breaks, while a task refuses them (`Q-11`, `BR-07`).
- **The guestbook is deletable, and the list has to survive that.** The guestbook is the
  template's example, "deleted as a unit" (`CLAUDE.md` § What is an example;
  `spec/contexts/guestbook.md`). The user chose to keep the to-do list beside it (`Q-1`).
- **One rule really is shared.** Both contexts use the text rule of `BR-01`: NFC, the written
  30-code-point trim set, then a count in code points. Its code was already outside the
  guestbook, in `app/platform/schemas/text.py`, which `spec/design/conventions.md` § Backend
  calls "a fact about EVERY text field this API accepts".
- **Platform holds no domain rules** by definition (`spec/design/architecture.md` § Platform).

## Decision

The to-do list is a bounded context of its own, `todo_list`, and it sits beside the guestbook
in every tree: `spec/contexts/todo_list.md`, `app/contexts/todo_list/`,
`frontend/src/contexts/todo_list/`, the table `todo_tasks`, the contract
`contracts/openapi/todo_list.yaml` and the feature file `e2e/suite/features/todo_list.feature`.
It owns `P-02` and `BR-06`…`BR-13`, and nothing of the guestbook's. The two contexts are peers
that share exactly one rule, how a text is normalized, trimmed and measured, and the words of
that rule stay in `spec/contexts/guestbook.md` § `BR-01`. They share nothing else. No record on
one side refers to a record on the other. Neither reads the other's list. Neither imports the
other's code, on the server or in the browser.

## Rejected alternatives

- **Tasks inside the guestbook context.** `P-01`'s "no states" would become false for its own
  context, and two vocabularies would sit under one owner. Worst, the list the user kept would
  be tied to an example the template tells its reader to delete: removing the guestbook would
  remove the list.
- **Tasks in Platform.** Platform holds no domain rules by definition, and `BR-06`…`BR-13` are
  nothing but domain rules.
- **The guestbook as upstream, the to-do list as conformist.** That describes where the words of
  the text rule happen to be written, not whose rule it is. The rule is a fact about every text
  field the API accepts, and its code lives in neither context.
- **Separate ways, with each context keeping its own copy of the text rule.** Both contexts are
  held to one rule, and a change to it changes both. Two copies are how the browser and the
  service once came to disagree about one number (`contracts/invariants/guestbook.md` § `D-04`).
- **Buying it, by integrating a vendor's to-do product as a generic context.** It would bring
  the accounts that `spec/invariants.md` § Deliberate non-goals refuses, and a second place for
  people to go.

The designer also recorded two choices that are routed elsewhere rather than put here. The
classification `supporting` rather than `core` is recorded in `spec/contexts/todo_list.md`
§ Strategic classification, and reversing it is a front-matter edit. The declared pattern
`guestbook:peer:shared-kernel` is argued in the same document under § Neighbours, "Why a
shared kernel rather than an upstream".

## Consequences

- **The context is registered once in each composition point.** Those points are
  `app/contexts/__init__.py`, `app/api.py` and `frontend/src/router.tsx`, and the front matter
  of `spec/contexts/todo_list.md` declares the table, the screen and the feature file. These
  are held by `test_every_context_directory_is_registered_and_every_registration_exists`,
  `test_every_context_document_has_code_and_every_context_directory_has_a_document`,
  `test_every_table_a_context_owns_is_declared_by_the_data_model`,
  `test_every_context_the_api_register_names_is_a_declared_context`, the two claim sweeps for
  screens and feature files, and
  `test_every_neighbour_names_a_context_and_a_pairing_the_rules_allow`. The context sweeps that
  were vacuously true now see a second context (`spec/design/testing.md` § Fitness functions).
- **The shared rule's code lives in neither context's folder.** The server half stays in
  `app/platform/schemas/text.py`. The browser half moves out of the guestbook, from
  `frontend/src/contexts/guestbook/lib/entryText.ts` to `frontend/src/lib/text.ts`, and three
  guestbook imports point at the new home. `spec/design/conventions.md` § Frontend prescribes
  that move "the day a second context needs it". The boundary is held by
  `test_no_context_imports_another_contexts_internals` and
  `test_no_screen_reaches_into_another_contexts_folder`.
- **Each side keeps what is its own.** The guestbook keeps its bounds of 80 and 1000 and keeps
  line breaks as content. The to-do list keeps its bound of 200 and `LINE_BREAKS`, which sit
  beside `TodoTask` and not in Platform, because the guestbook keeps those characters. Each
  constant is held equal to its one browser copy by `tests/fitness/test_length_constants.py`.
- **A change to the text rule changes both contexts.** `spec/contexts/guestbook.md` § `BR-01`
  now names its second holder. The rule has two sets of corpus tests: the guestbook's in
  `tests/unit/test_entry_text_rules.py`, over `text-measurement.json`, and the to-do list's in
  `tests/unit/test_todo_task_text_rules.py`, over `todo-task-text.json`, which the implement
  stage writes. A change that breaks either side turns that side red. Nothing makes the person
  changing the rule read the to-do list's rules first; the paragraph in `BR-01` is the only
  prompt.
- **Deleting the guestbook is no longer the deletion of one unit.** The words of `BR-01` have to
  move into `spec/contexts/todo_list.md` first (§ Neighbours), and the gate `frozen-ids` goes red
  on a citation of `BR-01` that resolves nowhere. The list in `CLAUDE.md` § What is an example
  also has to say this. `design-spec` reported that the list was silent, `reconcile-docs` wrote
  the paragraph in the `spec_sync` stage of this change, and nothing enforces it.
  `contracts/openapi/todo_list.yaml` writes out
  `Refusal`, `RefusalDetail`, `HTTPValidationError` and `ValidationError` itself, rather than
  using a `$ref` into `guestbook.yaml`, so it stays readable when the guestbook is deleted.
  `./scripts/contracts.sh` holds both copies to the dump's one definition.
- **The frame belongs to no context.** The way between the two screens, the main address and the
  not-found page live in `frontend/src/components/shell/`, `frontend/src/pages/` and the
  composition root. They are held by `test_no_screen_reaches_into_another_contexts_folder`, from
  which only `frontend/src/router.tsx` is exempt.
- **No record refers across.** `todo_tasks` has no foreign key and copies no column
  (`spec/design/data-model.md` § `todo_tasks`).
  `tests/fitness/test_data_invariants.py::test_no_column_is_a_copy_of_another_tables_column`
  refuses a copied column. **Nothing refuses a foreign key from `todo_tasks` to
  `guestbook_entries`**: one declared by table name needs no import, so no boundary test sees
  it, and only review stands in the way.
- **The context can have an owner of its own.** `.github/CODEOWNERS` gains the per-context
  rows the file already describes. No test reads `CODEOWNERS`, so this rests on the file's own
  comment.
- **Reversing this is expensive.** Folding the list back into another context needs a data
  migration for `todo_tasks` and a rewritten contract (the paths under `/api/todo-tasks`, the
  `todo_task_*` codes and the schema names), and it moves a screen, a feature file and a test
  tree. This describes a cost, not a rule, so no check applies to it.

## Enforced by

- `tests/fitness/test_context_boundaries.py` — `test_no_context_imports_another_contexts_internals`
  and `test_no_screen_reaches_into_another_contexts_folder` catch either context importing the
  other on either side of the wire, including a to-do module that reaches for the guestbook's
  `lib/`. `test_every_context_directory_is_registered_and_every_registration_exists` and
  `test_every_context_document_has_code_and_every_context_directory_has_a_document` catch a
  context with a document and no code, or code that is registered in one aggregate only.
- `tests/fitness/test_context_declarations.py` catches three things. The first is a table the
  context owns that `spec/design/data-model.md` does not declare. The second is a screen or
  feature file claimed by no context, or by two. The third is an illegal neighbour pairing.
- `tests/fitness/test_length_constants.py` catches a browser copy of the 200 or of
  `LINE_BREAKS` that drifts from its home beside `TodoTask`.
- `tests/fitness/test_data_invariants.py` — `test_no_column_is_a_copy_of_another_tables_column`
  catches a guestbook fact transcribed into `todo_tasks`.
- Gate `frozen-ids` catches a citation of `BR-01` left pointing nowhere after the guestbook is
  deleted.

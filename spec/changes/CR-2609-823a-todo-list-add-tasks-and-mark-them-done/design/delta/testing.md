# Delta fragment — `design-testing`

*How anyone will know the to-do list works: the cheapest suite per requirement, the citation, the
fixtures, which tests must be seen red first and which are green by design. Written into the live
`spec/design/testing.md`. This fragment carries the entry and what belongs to the change alone:
the owner per requirement, where this design departs from `scenarios.md` and from a neighbour's
fragment, and what nobody in the composition can write.*

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
item 1 in that fragment's "Found outside every write set" disappear. `frontend/src/lib/text.test.ts`
is in the recorded boundary and is simply never written; the edit to `entryText.test.ts` is
inside the boundary as it stands.

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

# Tasks — the to-do list: add tasks and mark them done

**Change:** CR-2609-823a. **From:** `spec/design/architecture.md` § The to-do list — where each
rule lives (the files and their writers), `spec/design/testing.md` § CR-2609-823a, the to-do list
and § Four file sets, disjoint (the tests, their cases and their authors),
`spec/design/data-model.md` § The revision that creates `todo_tasks`, `spec/design/api.md` § The
to-do list's endpoints and § The to-do list's refusals, `spec/design/ui/todo-list.md` and
`spec/design/ui/system-states.md`. A requirement written `R-n` below is `CR-2609-823a/R-n`.

## Reading this plan

**The waves are the profile's, derived by `sdd-engine skill_gate --list` from each member's
`after` in `.specconf/stack.json`.** Wave 1a is `build-tests-integration`, `build-tests-frontend`
and `build-tests-uat`. Wave 1b is `build-tests-unit` and `build-tests-e2e`, which the profile
orders after `build-tests-integration` because both import the corpus locator it writes. The RED
proof stands between wave 1 and wave 2. Wave 2 is `build-backend`, `build-migration`,
`build-frontend` and `build-platform`, which the profile orders after every test author. Each
member receives every task it owns, and does them in the order its `Depends on:` fields give.

**The fields.** `Files:` is the write allowlist of the task, and `Scope:` is the boundary row it
sits under (`set-boundary --from-design` recorded the boundary from the architecture fragment's
§ This change owns). `Depends on:` names only the tasks whose output this one reads or builds on.
`Parallel:` says what the task runs beside. `Must be red:` lists every case the task leaves
failing, and each is declared before the RED proof. `Green by design:` lists a planned case that
is already green, and correctly so, with the reason `green-by-design` records. `Turns green:`
lists a case that is red before the task starts and that the task's product turns green.
`Verification:` is the command, and what a pass looks like.

**How a declared case is spelled.** Every id below is `classname::name`, the form the junit
carries and the only one `declare-red` accepts.

- **pytest.** The classname is the module's dotted path, for example
  `tests.integration.test_todo_tasks_service`. A function listed with a bracket
  (`…::test_x[ascii_at_maximum]`) is parametrized, and its ids are the corpus's `case` field, or
  the ids this plan lists for the contract test. A function listed without a bracket is one
  collected case. Its variants (the four pairs of a marking, both orders of two writers, a
  marking, a correction and a deletion) live inside it and never in parameters, or its id would
  never be collected.
- **pytest-bdd.** All scenarios are collected in `e2e/suite/test_scenarios.py`, so the classname
  is `e2e.suite.test_scenarios`. The runner names a scenario `test_` followed by its title in
  lower case, with spaces as underscores and every other non-word character dropped. The titles
  are the ones `scenarios.md` gives, verbatim.
- **vitest.** The classname is the file's path relative to `frontend/`, the vitest root. The
  name is the test's own title, `[req:…]` included. A declared case stands at the top level of
  its file, because an enclosing `describe` prefixes the title with its own name and ` > `. It
  is one `it`, never an `it.each` whose title expands per row. A file vitest cannot load reports
  one case, `<path>::<path>`, and every case inside it goes uncollected.

**Red as itself.** A test author reaches a module wave 2 writes from inside the test or a
fixture, never at the top of the module: a failed top-level import un-collects every case in the
file, and a declared case the runner does not collect fails the gate (`spec/design/testing.md`
§ CR-2609-823a, "Red first"). No existing test is edited except where a task below names it.

## Wave 1 — tests

### T-1 · build-tests-integration · R-2, R-3, R-6
**Wave:** 1a
**Files:** `golden-set/fixtures/todo-tasks-ordinary.json`, `golden-set/fixtures/todo-tasks-boundary.json`,
`golden-set/fixtures/todo-tasks-refused.json`, `golden-set/fixtures/todo-task-text.json`,
`tests/_golden_set.py`, `tests/integration/test_todo_tasks_corpus.py`
**Scope:** `golden-set/fixtures/`, `tests/_golden_set.py`, `tests/integration/`
**Does:** Writes the to-do list's fixture half to the keys and codes of `spec/design/testing.md`
§ CR-2609-823a, "The fixture half this change adds", with every value from `scenarios.md`
§ Test data. It registers the four files and the example-task file in the locator as
`TODO_TASKS_ORDINARY`, `TODO_TASKS_BOUNDARY`, `TODO_TASKS_REFUSED` and `TODO_TASK_TEXT` in
`FIXTURE_FILES`, and `TODO_TASKS_EXAMPLE` (`golden-set/seed/todo-tasks-example.json`, which T-17
writes) in `SEED_FILES`. It adds a reader `tasks_of(path)` for the `tasks` key beside
`entries_of`. It then writes the corpus test, parametrized with `ids` from each case's `case`
field. That test adds the ordinary tasks in file order, marks the done ones after all six are
added, and asserts the reversal of the file with its marks. It posts every boundary case and
reads back its `stored` text. It sends every refused case as an addition, and again as a
correction of an existing task, and expects its `refusal` code with nothing stored and the
corrected task keeping its text. `todo-task-text.json` holds exactly these nineteen cases, each
input written in escapes. They are the eighteen of `scenarios.md` § New fixtures, "Additions to
`text-measurement.json`", with the six-character row counted as six, and the precedence case
`BR-07` added:

| `case` | input | `verdict` | `length` |
|---|---|---|---|
| `ascii_at_maximum` | 200 ASCII letters | `accepted` | 200 |
| `ascii_one_past_maximum` | 201 ASCII letters | `too_long` | — |
| `emoji_at_maximum` | 200 × U+1F600 | `accepted` | 200 |
| `emoji_one_past_maximum` | 201 × U+1F600 | `too_long` | — |
| `emoji_under_the_bound_but_over_it_in_utf16` | 101 × U+1F600 (202 UTF-16 units) | `accepted` | 101 |
| `decomposed_at_maximum` | 200 × (U+0065 U+0301) | `accepted` | 200 |
| `decomposed_one_past_maximum` | 201 × (U+0065 U+0301) | `too_long` | — |
| `ascii_padded_to_maximum` | 2 × U+0020, 200 ASCII letters, 2 × U+0020 | `accepted` | 200 |
| `spaces_past_the_maximum` | 205 × U+0020 | `empty` | — |
| `line_feed_inside` | "Buy bread", U+000A, "and milk" | `multiline` | — |
| `carriage_return_inside` | "Buy bread", U+000D, "and milk" | `multiline` | — |
| `line_tabulation_inside` | "Buy bread", U+000B, "and milk" | `multiline` | — |
| `form_feed_inside` | "Buy bread", U+000C, "and milk" | `multiline` | — |
| `next_line_inside` | "Buy bread", U+0085, "and milk" | `multiline` | — |
| `line_separator_inside` | "Buy bread", U+2028, "and milk" | `multiline` | — |
| `paragraph_separator_inside` | "Buy bread", U+2029, "and milk" | `multiline` | — |
| `tab_inside_is_kept` | "Buy", U+0009, "bread" | `accepted` | 9 |
| `line_feed_at_the_end_is_trimmed` | "Buy bread", U+000A | `accepted` | 9 |
| `too_long_and_on_two_lines_is_multiline` | 100 ASCII letters, U+000A, 101 ASCII letters | `multiline` | — |

**Depends on:** —
**Parallel:** yes. It runs beside T-5…T-8, which belong to other members. It is its member's
first task, because T-3's corpus-shaped cases and T-4's seeder cases read the locator it writes.
**Must be red:** `tests.integration.test_todo_tasks_corpus::test_every_boundary_task_is_accepted_and_stored_as_the_file_states[text_at_maximum]`,
`tests.integration.test_todo_tasks_corpus::test_every_boundary_task_is_accepted_and_stored_as_the_file_states[text_at_maximum_in_emoji]`,
`tests.integration.test_todo_tasks_corpus::test_every_boundary_task_is_accepted_and_stored_as_the_file_states[text_at_maximum_decomposed]`,
`tests.integration.test_todo_tasks_corpus::test_every_boundary_task_is_accepted_and_stored_as_the_file_states[text_padded_to_maximum]`,
`tests.integration.test_todo_tasks_corpus::test_every_boundary_task_is_accepted_and_stored_as_the_file_states[text_at_minimum]`,
`tests.integration.test_todo_tasks_corpus::test_every_refused_task_is_refused_with_its_code_and_stores_nothing[text_absent]`,
`tests.integration.test_todo_tasks_corpus::test_every_refused_task_is_refused_with_its_code_and_stores_nothing[text_three_spaces]`,
`tests.integration.test_todo_tasks_corpus::test_every_refused_task_is_refused_with_its_code_and_stores_nothing[text_all_whitespace]`,
`tests.integration.test_todo_tasks_corpus::test_every_refused_task_is_refused_with_its_code_and_stores_nothing[text_spaces_past_maximum]`,
`tests.integration.test_todo_tasks_corpus::test_every_refused_task_is_refused_with_its_code_and_stores_nothing[text_one_past_maximum]`,
`tests.integration.test_todo_tasks_corpus::test_every_refused_task_is_refused_with_its_code_and_stores_nothing[text_one_past_maximum_in_emoji]`,
`tests.integration.test_todo_tasks_corpus::test_every_refused_task_is_refused_with_its_code_and_stores_nothing[text_one_past_maximum_decomposed]`,
`tests.integration.test_todo_tasks_corpus::test_every_refused_task_is_refused_with_its_code_and_stores_nothing[text_padded_one_past_maximum]`,
`tests.integration.test_todo_tasks_corpus::test_every_refused_task_is_refused_with_its_code_and_stores_nothing[text_line_break_inside]`,
`tests.integration.test_todo_tasks_corpus::test_every_refused_text_is_refused_as_a_correction_and_the_task_keeps_its_text[text_absent]`,
`tests.integration.test_todo_tasks_corpus::test_every_refused_text_is_refused_as_a_correction_and_the_task_keeps_its_text[text_three_spaces]`,
`tests.integration.test_todo_tasks_corpus::test_every_refused_text_is_refused_as_a_correction_and_the_task_keeps_its_text[text_all_whitespace]`,
`tests.integration.test_todo_tasks_corpus::test_every_refused_text_is_refused_as_a_correction_and_the_task_keeps_its_text[text_spaces_past_maximum]`,
`tests.integration.test_todo_tasks_corpus::test_every_refused_text_is_refused_as_a_correction_and_the_task_keeps_its_text[text_one_past_maximum]`,
`tests.integration.test_todo_tasks_corpus::test_every_refused_text_is_refused_as_a_correction_and_the_task_keeps_its_text[text_one_past_maximum_in_emoji]`,
`tests.integration.test_todo_tasks_corpus::test_every_refused_text_is_refused_as_a_correction_and_the_task_keeps_its_text[text_one_past_maximum_decomposed]`,
`tests.integration.test_todo_tasks_corpus::test_every_refused_text_is_refused_as_a_correction_and_the_task_keeps_its_text[text_padded_one_past_maximum]`,
`tests.integration.test_todo_tasks_corpus::test_every_refused_text_is_refused_as_a_correction_and_the_task_keeps_its_text[text_line_break_inside]`,
`tests.integration.test_todo_tasks_corpus::test_the_ordinary_tasks_read_back_as_the_reversal_of_the_file_with_their_marks`
**Verification:** `./scripts/test.sh integration` shows every case named above failing because no
to-do route answers (the application's JSON 404 under `/api/`), none as a collection error.
`./scripts/test.sh fitness` shows the corpus rules red that T-10 rescopes, and the seed-file cases
T-10 lists. That is expected until wave 1b, and they are named in this task's closing block.

### T-2 · build-tests-integration · R-1, R-2, R-3, R-4, R-6, R-7, R-8, R-9
**Wave:** 1a
**Files:** `tests/integration/test_todo_tasks_service.py`, `tests/integration/test_todo_tasks_concurrency.py`
**Scope:** `tests/integration/`
**Does:** Writes the service's claims over real storage as the evidence map's rows for `R-1`,
`R-2`, `R-3`, `R-4`, `R-6`, `R-7` and `R-8` give them. An equal `created_at` is arranged through
the service's clock or rows written directly, never hoped for from two quick calls. It writes
the four concurrency cases exactly as "How two writers are interleaved" prescribes: a third
connection holds the row lock, `pg_stat_activity` shows each waiter queued, every wait is bounded
at a few seconds and fails with its own message. Each case carries
`@pytest.mark.req("CR-2609-823a/R-n")`. It imports from `app.contexts.todo_list.services.todo_tasks`
the operations it calls, `TodoTaskNotFoundError` (the name `spec/design/architecture.md` gives it)
and one domain exception per text verdict. The names it gives those three exceptions are the ones
T-9 then imports and T-15 implements.
**Depends on:** —
**Parallel:** yes, beside T-1, T-3 and T-4 in its member's dispatch, and beside T-5…T-8.
**Must be red:** `tests.integration.test_todo_tasks_service::test_an_added_task_is_stored_not_done_with_its_moment_of_adding`,
`tests.integration.test_todo_tasks_service::test_the_same_text_added_twice_is_two_tasks_marked_apart`,
`tests.integration.test_todo_tasks_service::test_a_stored_text_is_normalized_one_line_and_within_the_bound_in_code_points`,
`tests.integration.test_todo_tasks_service::test_inner_whitespace_is_stored_as_typed`,
`tests.integration.test_todo_tasks_service::test_the_list_comes_back_newest_first`,
`tests.integration.test_todo_tasks_service::test_tasks_sharing_a_moment_of_adding_still_have_a_total_order`,
`tests.integration.test_todo_tasks_service::test_every_task_is_read_at_once_done_and_not_done`,
`tests.integration.test_todo_tasks_service::test_marking_and_correcting_leave_a_task_in_its_place`,
`tests.integration.test_todo_tasks_service::test_marking_records_the_state_chosen_whatever_is_stored`,
`tests.integration.test_todo_tasks_service::test_marking_leaves_the_text_and_the_moment_of_adding_alone`,
`tests.integration.test_todo_tasks_service::test_a_correction_changes_the_text_and_nothing_else`,
`tests.integration.test_todo_tasks_service::test_a_done_task_is_corrected_as_a_not_done_one_is`,
`tests.integration.test_todo_tasks_service::test_a_refused_correction_keeps_the_text_it_had`,
`tests.integration.test_todo_tasks_service::test_deleting_removes_the_row_and_leaves_every_other_task`,
`tests.integration.test_todo_tasks_service::test_a_change_to_a_deleted_task_changes_nothing_and_creates_nothing`,
`tests.integration.test_todo_tasks_concurrency::test_a_correction_and_a_marking_queued_on_one_task_are_both_kept`,
`tests.integration.test_todo_tasks_concurrency::test_of_two_queued_corrections_the_one_applied_later_wins`,
`tests.integration.test_todo_tasks_concurrency::test_of_two_queued_markings_the_one_applied_later_wins`,
`tests.integration.test_todo_tasks_concurrency::test_a_change_queued_behind_a_deletion_creates_nothing`
**Verification:** `./scripts/test.sh integration` shows every case named above failing inside the
test on the missing `app.contexts.todo_list` package, none as a collection error and none hanging.

### T-3 · build-tests-integration · R-1, R-2, R-3, R-4, R-6, R-7, R-8
**Wave:** 1a
**Files:** `tests/integration/test_todo_tasks_router.py`, `tests/integration/test_todo_tasks_contract.py`
**Scope:** `tests/integration/`
**Does:** Writes the router cases of the evidence map and its refusal table. They cover each route's
status and body, the five codes with the sentences of `spec/design/api.md` § The to-do list's
refusals, the standard validation `422`, and the order in which one request earns one refusal.
Each router case named here is one collected case, with its variants (`POST` and `PATCH`, the
several malformed bodies) inside it. It writes the contract test, which validates every real
answer against the schema `app.openapi()` publishes for its operation and status. That test is
parametrized with exactly the thirteen ids below: `list_answers`, `create_succeeds`,
`create_refuses_an_empty_text`, `create_refuses_a_text_that_is_not_a_string`, `patch_marks`,
`patch_corrects`, `patch_refuses_an_empty_patch`, `patch_refuses_a_text_on_two_lines`,
`patch_refuses_a_done_that_is_not_a_boolean`, `patch_task_is_absent`, `patch_id_is_not_a_uuid`,
`delete_succeeds`, `delete_is_absent`.
**Depends on:** —
**Parallel:** yes, beside T-1, T-2 and T-4 in its member's dispatch, and beside T-5…T-8.
**Must be red:** `tests.integration.test_todo_tasks_router::test_adding_answers_201_with_the_task_as_stored`,
`tests.integration.test_todo_tasks_router::test_a_done_sent_with_a_new_task_is_ignored`,
`tests.integration.test_todo_tasks_router::test_the_list_is_one_envelope_with_every_task_and_its_count`,
`tests.integration.test_todo_tasks_router::test_a_patch_carrying_done_alone_writes_done_alone`,
`tests.integration.test_todo_tasks_router::test_a_patch_carrying_text_alone_writes_text_alone`,
`tests.integration.test_todo_tasks_router::test_a_refused_text_in_a_patch_that_also_carries_done_writes_neither`,
`tests.integration.test_todo_tasks_router::test_deleting_answers_204_with_no_body`,
`tests.integration.test_todo_tasks_router::test_a_change_to_a_missing_task_answers_404_with_its_code`,
`tests.integration.test_todo_tasks_router::test_a_patch_setting_neither_field_is_refused`,
`tests.integration.test_todo_tasks_router::test_each_text_refusal_answers_with_its_own_code`,
`tests.integration.test_todo_tasks_router::test_a_text_too_long_and_on_two_lines_is_refused_as_multiline`,
`tests.integration.test_todo_tasks_router::test_a_body_of_the_wrong_shape_gets_the_standard_validation_refusal`,
`tests.integration.test_todo_tasks_router::test_a_request_is_refused_for_what_it_is_whatever_its_identifier_names`,
`tests.integration.test_todo_tasks_contract::test_the_body_matches_the_schema_published_for_the_status_it_returned[list_answers]`,
`tests.integration.test_todo_tasks_contract::test_the_body_matches_the_schema_published_for_the_status_it_returned[create_succeeds]`,
`tests.integration.test_todo_tasks_contract::test_the_body_matches_the_schema_published_for_the_status_it_returned[create_refuses_an_empty_text]`,
`tests.integration.test_todo_tasks_contract::test_the_body_matches_the_schema_published_for_the_status_it_returned[create_refuses_a_text_that_is_not_a_string]`,
`tests.integration.test_todo_tasks_contract::test_the_body_matches_the_schema_published_for_the_status_it_returned[patch_marks]`,
`tests.integration.test_todo_tasks_contract::test_the_body_matches_the_schema_published_for_the_status_it_returned[patch_corrects]`,
`tests.integration.test_todo_tasks_contract::test_the_body_matches_the_schema_published_for_the_status_it_returned[patch_refuses_an_empty_patch]`,
`tests.integration.test_todo_tasks_contract::test_the_body_matches_the_schema_published_for_the_status_it_returned[patch_refuses_a_text_on_two_lines]`,
`tests.integration.test_todo_tasks_contract::test_the_body_matches_the_schema_published_for_the_status_it_returned[patch_refuses_a_done_that_is_not_a_boolean]`,
`tests.integration.test_todo_tasks_contract::test_the_body_matches_the_schema_published_for_the_status_it_returned[patch_task_is_absent]`,
`tests.integration.test_todo_tasks_contract::test_the_body_matches_the_schema_published_for_the_status_it_returned[patch_id_is_not_a_uuid]`,
`tests.integration.test_todo_tasks_contract::test_the_body_matches_the_schema_published_for_the_status_it_returned[delete_succeeds]`,
`tests.integration.test_todo_tasks_contract::test_the_body_matches_the_schema_published_for_the_status_it_returned[delete_is_absent]`
**Verification:** `./scripts/test.sh integration` shows every case named above failing because no
to-do route is served and no to-do operation is published, none as a collection error.

### T-4 · build-tests-integration · R-1, R-3, R-4, R-11
**Wave:** 1a
**Files:** `tests/integration/test_migrations.py`, `tests/tooling/test_seed_golden_set.py`
**Scope:** `tests/integration/`, `tests/tooling/`
**Does:** Adds a hand-written mirror of the `todo_tasks` columns to the migration tests, and two
cases: the table has exactly the four columns of `spec/design/data-model.md` § `todo_tasks`, and
its ordering index exists. In the seeder's tests, the fake learns the to-do list's `GET`, `POST`
and `PATCH` beside the guest book's. `test_a_guest_book_with_entries_is_left_alone` is rewritten
under `Q-10`: its entries are left alone and the empty to-do list still gets its examples.
`test_an_empty_environment_gets_the_whole_seed_corpus` expects both lists filled and the done
example marked, with the expectation still derived from `SEED_FILES` and never from the example
values (`test_no_suite_reads_the_seed_corpus`). Two cases are added:
`test_a_to_do_list_holding_a_task_is_left_alone` and `test_the_done_example_is_added_then_marked`.
The design's "a list filled whatever the guestbook holds" is covered by
`test_a_guest_book_with_entries_is_left_alone` (entries present) and
`test_an_empty_environment_gets_the_whole_seed_corpus` (no entries) together, and adds no case of
its own. `test_production_is_refused` keeps
asserting that nothing is posted, which now covers both lists.
**Depends on:** T-1
**Parallel:** yes, beside T-5…T-8. Within its member it follows T-1, whose `SEED_FILES` it reads.
**Must be red:** `tests.integration.test_migrations::test_upgrade_head_creates_the_todo_tasks_table_with_exactly_these_columns`,
`tests.integration.test_migrations::test_the_todo_list_order_has_an_index_behind_it`,
`tests.tooling.test_seed_golden_set::test_a_guest_book_with_entries_is_left_alone`,
`tests.tooling.test_seed_golden_set::test_an_empty_environment_gets_the_whole_seed_corpus`,
`tests.tooling.test_seed_golden_set::test_a_to_do_list_holding_a_task_is_left_alone`,
`tests.tooling.test_seed_golden_set::test_the_done_example_is_added_then_marked`,
`tests.tooling.test_seed_golden_set::test_the_boundary_corpus_is_opt_in`,
`tests.tooling.test_seed_golden_set::test_a_trailing_slash_on_the_base_url_is_tolerated`.
The last two are unedited cases. They go red because T-1's `SEED_FILES` names a file the seeder
cannot read until T-17 writes it and teaches the seeder the `tasks` key. Any other tooling case
red for that reason alone is named in this task's closing block, so it is declared before the RED
proof.
**Green by design:** `tests.tooling.test_seed_golden_set::test_production_is_refused`. The seeder
refuses production before it reads either list, so no task can be posted there today. The case
pins that the refusal still covers the second list once the seeder asks two.
**Verification:** `./scripts/test.sh integration` shows the two migration cases failing because
there is no `todo_tasks` table. `./scripts/test.sh tooling` shows the six tooling cases failing on
the missing seed file or the missing to-do filling. Every other case passes.

### T-5 · build-tests-frontend · R-1, R-2
**Wave:** 1a
**Files:** `frontend/src/contexts/todo_list/lib/todoTask.test.ts`,
`frontend/src/contexts/todo_list/components/TodoTaskComposer.test.tsx`,
`frontend/src/contexts/guestbook/lib/entryText.test.ts`
**Scope:** `frontend/src/contexts/todo_list/`, `frontend/src/contexts/guestbook/lib/entryText.test.ts`
**Does:** Writes the browser rule's reader of `golden-set/fixtures/todo-task-text.json`, which
asserts the same bytes, verdicts and lengths T-9 asserts on the server. It is the one module T-10
allows to read that file. It reads the file and imports `./todoTask` inside each test, so a
missing file or module fails as that test. It writes the composer's cases from
`spec/design/ui/todo-list.md` § The add field: no `maxLength`; 200 pasted emoji held and addable;
201 held, the too-long sentence, nothing sent; a pasted U+2028 between two words gets the one-line
sentence and sends nothing; what is sent is the text as the shared rule leaves it. It changes the
one import line of `entryText.test.ts` from `./entryText` to `@/lib/text`, and nothing else in
that file.
**Depends on:** —
**Parallel:** yes, beside T-1…T-4 and T-8. It reads T-1's `todo-task-text.json` at run time with
`readFileSync`, which is not an import, so the profile orders nothing between the two members. Its
first run may fail on the missing file while T-1 is still writing, and its declared cases are
observed after the whole test wave, never on that first run.
**Must be red:** `src/contexts/todo_list/lib/todoTask.test.ts::gives each case of the task's corpus the verdict it states [req:CR-2609-823a/R-2]`,
`src/contexts/todo_list/lib/todoTask.test.ts::measures each accepted case in code points, as the server does [req:CR-2609-823a/R-2]`,
`src/contexts/todo_list/lib/todoTask.test.ts::refuses a text both too long and on two lines as one line [req:CR-2609-823a/R-2]`,
`src/contexts/todo_list/components/TodoTaskComposer.test.tsx::takes 200 pasted emoji whole and lets the task be added [req:CR-2609-823a/R-2]`,
`src/contexts/todo_list/components/TodoTaskComposer.test.tsx::holds 201 emoji, says the text is too long and sends nothing [req:CR-2609-823a/R-2]`,
`src/contexts/todo_list/components/TodoTaskComposer.test.tsx::says a text with a line break inside is one line and sends nothing [req:CR-2609-823a/R-2]`,
`src/contexts/todo_list/components/TodoTaskComposer.test.tsx::sends the text as the shared rule leaves it [req:CR-2609-823a/R-1]`,
`src/contexts/guestbook/lib/entryText.test.ts::src/contexts/guestbook/lib/entryText.test.ts`.
The last is the guestbook's corpus reader failing to load on `@/lib/text`, which T-18 moves the
rule to. The design declared no such red, and this plan declares it so the RED proof does not read
an old test gone red as a regression.
**Verification:** `./scripts/test.sh frontend` shows the seven to-do cases failing as themselves on
the module they reach, and `entryText.test.ts` failing to load. Every other guestbook case passes.

### T-6 · build-tests-frontend · R-1, R-3, R-4, R-6, R-7, R-8, R-10
**Wave:** 1a
**Files:** `frontend/src/contexts/todo_list/components/TodoTaskRow.test.tsx`,
`frontend/src/contexts/todo_list/hooks/useTodoTasks.test.tsx`,
`frontend/src/contexts/todo_list/pages/TodoListPage.test.tsx`
**Scope:** `frontend/src/contexts/todo_list/`
**Does:** Writes the screen's cases from the evidence map's rows for `R-4`, `R-6`, `R-7` and `R-10`
and the page's rows for `R-1` and `R-3`. The row covers: a done task drawn differently (its
checkbox checked and its text carrying the done style); a tick sends the chosen state; a correction
is shown in place; a refused correction keeps the old text and says why; a delete asks first, a
cancel sends nothing, a confirm sends the one deletion. The hook writes nothing into the cached list
before the answer or after a failure, and refetches after a change that went through. The page
covers: an added task first with no reload; the order as it arrives; the empty sentence with no
error; an all-done list not called empty; each failure sentence of `spec/design/ui/todo-list.md`
§ Copy, `Q-15`'s words included; a failed load that is not called empty; a refusal with
`todo_task_not_found` that says the task no longer exists and does not show it done. Every string
is quoted from `todo-list.md` § Copy, component data is synthetic and written in the test, and no
corpus file is read.
**Depends on:** —
**Parallel:** yes, beside T-1…T-4 and T-8.
**Must be red:** `src/contexts/todo_list/components/TodoTaskRow.test.tsx::shows a done task differently from a not-done one [req:CR-2609-823a/R-4]`,
`src/contexts/todo_list/components/TodoTaskRow.test.tsx::sends the state the person chose [req:CR-2609-823a/R-4]`,
`src/contexts/todo_list/components/TodoTaskRow.test.tsx::shows a corrected text in the task's place [req:CR-2609-823a/R-6]`,
`src/contexts/todo_list/components/TodoTaskRow.test.tsx::keeps the old text and says why when a correction is refused [req:CR-2609-823a/R-6]`,
`src/contexts/todo_list/components/TodoTaskRow.test.tsx::asks before deleting and sends nothing until confirmed [req:CR-2609-823a/R-7]`,
`src/contexts/todo_list/components/TodoTaskRow.test.tsx::leaves the task as it was when the deletion is cancelled [req:CR-2609-823a/R-7]`,
`src/contexts/todo_list/hooks/useTodoTasks.test.tsx::writes nothing into the list before the application answers [req:CR-2609-823a/R-10]`,
`src/contexts/todo_list/hooks/useTodoTasks.test.tsx::refetches the list after a change that went through [req:CR-2609-823a/R-1]`,
`src/contexts/todo_list/pages/TodoListPage.test.tsx::shows an added task first without a reload [req:CR-2609-823a/R-1]`,
`src/contexts/todo_list/pages/TodoListPage.test.tsx::shows the tasks in the order they arrive [req:CR-2609-823a/R-3]`,
`src/contexts/todo_list/pages/TodoListPage.test.tsx::says the list is empty and how to begin, with no error [req:CR-2609-823a/R-3]`,
`src/contexts/todo_list/pages/TodoListPage.test.tsx::shows a list whose tasks are all done and does not call it empty [req:CR-2609-823a/R-3]`,
`src/contexts/todo_list/pages/TodoListPage.test.tsx::says a marking that did not go through was not made [req:CR-2609-823a/R-10]`,
`src/contexts/todo_list/pages/TodoListPage.test.tsx::says a task that did not go through was not added [req:CR-2609-823a/R-10]`,
`src/contexts/todo_list/pages/TodoListPage.test.tsx::says a correction or a deletion that did not go through was not made [req:CR-2609-823a/R-10]`,
`src/contexts/todo_list/pages/TodoListPage.test.tsx::says the list failed to load, not that it is empty [req:CR-2609-823a/R-10]`,
`src/contexts/todo_list/pages/TodoListPage.test.tsx::says a task refused as gone no longer exists and does not show it done [req:CR-2609-823a/R-10]`
**Verification:** `./scripts/test.sh frontend` shows the seventeen cases failing as themselves on
the modules they reach. Every other case passes, except T-5's `entryText.test.ts`.

### T-7 · build-tests-frontend · R-5
**Wave:** 1a
**Files:** `frontend/src/router.test.tsx`, `frontend/src/components/shell/PageFrame.test.tsx`,
`frontend/src/pages/StatusPages.test.tsx`
**Scope:** `frontend/src/router.test.tsx`, `frontend/src/components/shell/PageFrame.test.tsx`,
`frontend/src/pages/StatusPages.test.tsx`
**Does:** Writes the composition root's cases against `frontend/src/router.tsx`. The to-do list's
own address, `/todo-list`, opens the to-do screen. The main address opens the guestbook. An
unknown address gets the page whose sentence is `There is nothing at this address.`
(`spec/design/ui/system-states.md` § Copy). The frame case checks that each screen offers the
link to the other one, `Guestbook` and `To-do list`, in the group named `Screens`. The not-found
case checks that the page does not say the application has one screen.
**Depends on:** —
**Parallel:** yes, beside T-1…T-4 and T-8.
**Must be red:** `src/router.test.tsx::opens the to-do list at its own address [req:CR-2609-823a/R-5]`,
`src/router.test.tsx::answers an unknown address with the page that says nothing is there [req:CR-2609-823a/R-5]`,
`src/components/shell/PageFrame.test.tsx::offers the way to the other screen on each screen [req:CR-2609-823a/R-5]`,
`src/pages/StatusPages.test.tsx::does not say the application has one screen [req:CR-2609-823a/R-5]`
**Green by design:** `src/router.test.tsx::opens the guestbook at the main address [req:CR-2609-823a/R-5]`.
The redirect from `/` to `/guestbook` already stands in `frontend/src/router.tsx`. This
characterisation case pins `spec/design/ui/system-states.md` § Interactions, which `R-5` clause 3
restates.
**Verification:** `./scripts/test.sh frontend` shows the four cases failing, because today the page
says "There is one screen in this application: the guestbook." and no route or link to the to-do
list exists. The characterisation case passes.

### T-8 · build-tests-uat · R-1, R-3, R-4, R-5, R-9, R-11
**Wave:** 1a
**Files:** `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/uat.md`
**Scope:** `spec/changes/CR-2609-823a-todo-list-add-tasks-and-mark-them-done/uat.md`
**Does:** Writes the script a person walks after delivery. It has a step for each of the seeds
`S-49`…`S-53` of `R-11`, which is `**Verified-by:** manual`: a fresh environment shows at least
three example tasks with one done; filling again adds nothing to a list that holds a task;
production gets none; a guestbook with its welcome entries and an empty list gets the tasks and
keeps its entries; a list with a task and an empty guestbook gets only the welcome entries. It has
the look at a done task's contrast (`R-4` clause 6), and the steps `SC-1`…`SC-5` of
`requirements.md` measure, two browser windows for `SC-2` included.
**Depends on:** —
**Parallel:** yes, beside T-1…T-7. It reads `requirements.md` and `scenarios.md` alone.
**Verification:** `sdd-skill build-tests-uat verify` exits 0.

### T-9 · build-tests-unit · R-1, R-2, R-3, R-4
**Wave:** 1b
**Files:** `tests/unit/test_todo_task_text_rules.py`, `tests/unit/test_todo_task_model.py`,
`tests/unit/test_guestbook_entry_model.py`
**Scope:** `tests/unit/`
**Does:** Writes the text rule's cases over `TODO_TASK_TEXT` (T-1's `todo-task-text.json`): a
verdict per case and a length per accepted case, parametrized with `ids` from `case`, through the
service's judgement of a text. The judgement's function name is this task's to choose, and the
three exceptions carry the names T-2 imports. It writes one case holding that every case, refused
ones included, builds a valid create and update shape. It writes one case for the precedence of
`BR-07` over `BR-06`, one reading the bound from `TODO_TASK_TEXT_MAX_LENGTH` from both sides (never
`QUERY_MAX_LENGTH`), one holding `LINE_BREAKS` to the seven written code points, all inside the
trim set, and one `hypothesis` generator as "Red first" describes it. It writes the model's four
declarations of `spec/design/data-model.md` § `todo_tasks`. It renames
`test_this_schema_holds_exactly_one_table` to `test_this_schema_holds_exactly_two_tables`, which
expects `guestbook_entries` and `todo_tasks`. Each case carries `@pytest.mark.req("CR-2609-823a/R-n")`.
**Depends on:** T-1, T-2
**Parallel:** yes, beside T-11 and T-12. It goes out once wave 1a has returned, since it reads
T-1's corpus through the locator and T-2's exception names.
**Must be red:** `tests.unit.test_todo_task_text_rules::test_every_case_gets_the_verdict_the_corpus_states[ascii_at_maximum]`,
`tests.unit.test_todo_task_text_rules::test_every_case_gets_the_verdict_the_corpus_states[ascii_one_past_maximum]`,
`tests.unit.test_todo_task_text_rules::test_every_case_gets_the_verdict_the_corpus_states[emoji_at_maximum]`,
`tests.unit.test_todo_task_text_rules::test_every_case_gets_the_verdict_the_corpus_states[emoji_one_past_maximum]`,
`tests.unit.test_todo_task_text_rules::test_every_case_gets_the_verdict_the_corpus_states[emoji_under_the_bound_but_over_it_in_utf16]`,
`tests.unit.test_todo_task_text_rules::test_every_case_gets_the_verdict_the_corpus_states[decomposed_at_maximum]`,
`tests.unit.test_todo_task_text_rules::test_every_case_gets_the_verdict_the_corpus_states[decomposed_one_past_maximum]`,
`tests.unit.test_todo_task_text_rules::test_every_case_gets_the_verdict_the_corpus_states[ascii_padded_to_maximum]`,
`tests.unit.test_todo_task_text_rules::test_every_case_gets_the_verdict_the_corpus_states[spaces_past_the_maximum]`,
`tests.unit.test_todo_task_text_rules::test_every_case_gets_the_verdict_the_corpus_states[line_feed_inside]`,
`tests.unit.test_todo_task_text_rules::test_every_case_gets_the_verdict_the_corpus_states[carriage_return_inside]`,
`tests.unit.test_todo_task_text_rules::test_every_case_gets_the_verdict_the_corpus_states[line_tabulation_inside]`,
`tests.unit.test_todo_task_text_rules::test_every_case_gets_the_verdict_the_corpus_states[form_feed_inside]`,
`tests.unit.test_todo_task_text_rules::test_every_case_gets_the_verdict_the_corpus_states[next_line_inside]`,
`tests.unit.test_todo_task_text_rules::test_every_case_gets_the_verdict_the_corpus_states[line_separator_inside]`,
`tests.unit.test_todo_task_text_rules::test_every_case_gets_the_verdict_the_corpus_states[paragraph_separator_inside]`,
`tests.unit.test_todo_task_text_rules::test_every_case_gets_the_verdict_the_corpus_states[tab_inside_is_kept]`,
`tests.unit.test_todo_task_text_rules::test_every_case_gets_the_verdict_the_corpus_states[line_feed_at_the_end_is_trimmed]`,
`tests.unit.test_todo_task_text_rules::test_every_case_gets_the_verdict_the_corpus_states[too_long_and_on_two_lines_is_multiline]`,
`tests.unit.test_todo_task_text_rules::test_every_accepted_case_has_the_length_the_corpus_states[ascii_at_maximum]`,
`tests.unit.test_todo_task_text_rules::test_every_accepted_case_has_the_length_the_corpus_states[emoji_at_maximum]`,
`tests.unit.test_todo_task_text_rules::test_every_accepted_case_has_the_length_the_corpus_states[emoji_under_the_bound_but_over_it_in_utf16]`,
`tests.unit.test_todo_task_text_rules::test_every_accepted_case_has_the_length_the_corpus_states[decomposed_at_maximum]`,
`tests.unit.test_todo_task_text_rules::test_every_accepted_case_has_the_length_the_corpus_states[ascii_padded_to_maximum]`,
`tests.unit.test_todo_task_text_rules::test_every_accepted_case_has_the_length_the_corpus_states[tab_inside_is_kept]`,
`tests.unit.test_todo_task_text_rules::test_every_accepted_case_has_the_length_the_corpus_states[line_feed_at_the_end_is_trimmed]`,
`tests.unit.test_todo_task_text_rules::test_the_create_and_update_shapes_carry_no_bound`,
`tests.unit.test_todo_task_text_rules::test_a_text_too_long_and_on_two_lines_is_refused_as_multiline`,
`tests.unit.test_todo_task_text_rules::test_the_bound_stands_where_the_constant_says`,
`tests.unit.test_todo_task_text_rules::test_the_line_breaks_are_the_seven_written_code_points_and_all_are_trimmed`,
`tests.unit.test_todo_task_text_rules::test_any_text_is_either_refused_or_kept_normalized_one_line_and_within_the_bound`,
`tests.unit.test_todo_task_model::test_the_text_column_is_as_long_as_the_bound`,
`tests.unit.test_todo_task_model::test_a_new_task_is_not_done_by_the_models_default`,
`tests.unit.test_todo_task_model::test_the_moment_of_adding_is_stored_with_its_zone`,
`tests.unit.test_todo_task_model::test_the_order_has_an_index_the_model_declares`,
`tests.unit.test_guestbook_entry_model::test_this_schema_holds_exactly_two_tables`
**Verification:** `./scripts/test.sh unit` shows every case named above failing inside the test on
the missing `app.contexts.todo_list` package, none as a collection error. Every other unit case
passes.

### T-10 · build-tests-unit · R-2, R-11
**Wave:** 1b
**Files:** `tests/fitness/test_golden_set.py`, `tests/fitness/test_length_constants.py`
**Scope:** `tests/fitness/`
**Does:** Teaches the corpus rules the to-do files, as `spec/design/testing.md` § Fitness functions
describes `test_golden_set.py` since this change. A third key, `tasks`, is added for sequences of
`{text, done}` with no line break anywhere. The rules that index `author` and `message` are scoped
to the guestbook's entry files, and the rule demanding a line break in every sequence file becomes
the guestbook's alone. `todo-task-text.json` is held to rules of its own: a closed set of four
verdicts, a length exactly when `accepted`, inputs in escapes, all seven line breaks present, and
the 101-emoji case. Two new cases hold the boundary tasks exactly on `TODO_TASK_TEXT_MAX_LENGTH` and
the tasks refused as too long over it by exactly one.
`test_no_seed_entry_stands_near_a_published_limit` is extended to hold an example task under three
quarters of that bound. One new case holds the example file to at least one done task and every
text accepted by `BR-06` and `BR-07`, through the shared kernel and the model's constants.
`test_the_frontend_reads_no_corpus_file` names two readers, each allowed its own context's file
alone: the guestbook's `entryText.test.ts` for `text-measurement.json`, and T-5's `todoTask.test.ts`
for `todo-task-text.json`. The seed-half detector learns the name `TODO_TASKS_EXAMPLE`. In
`test_length_constants.py`, two new cases hold `TODO_TASK_TEXT_MAX_LENGTH` and `LINE_BREAKS` beside
`TodoTask` equal to their browser copies of the same names in
`frontend/src/contexts/todo_list/lib/todoTask.ts`, read as text. The literal shape each side is
parsed in is written down in the test's docstring for T-14 and T-19. These cases cite no requirement.
**Depends on:** T-1
**Parallel:** yes, beside T-9, T-11 and T-12. On arrival the rules T-1's registration broke are
red, and this task's edits turn them green.
**Must be red:** `tests.fitness.test_golden_set::test_every_corpus_file_is_named_by_the_locator`,
`tests.fitness.test_golden_set::test_each_half_agrees_with_the_locator_about_what_is_in_it`,
`tests.fitness.test_golden_set::test_every_file_says_which_story_it_is_and_what_it_demonstrates`,
`tests.fitness.test_golden_set::test_every_file_is_utf8_json_and_ends_with_a_newline`,
`tests.fitness.test_golden_set::test_the_seed_half_shows_a_list_rather_than_an_entry`,
`tests.fitness.test_golden_set::test_no_seed_entry_stands_near_a_published_limit`,
`tests.fitness.test_golden_set::test_every_boundary_task_sits_exactly_on_the_task_bound`,
`tests.fitness.test_golden_set::test_every_task_refused_as_too_long_is_over_the_bound_by_exactly_one`,
`tests.fitness.test_golden_set::test_the_example_tasks_show_one_done_and_every_one_is_accepted`,
`tests.fitness.test_length_constants::test_the_task_bound_equals_its_browser_copy`,
`tests.fitness.test_length_constants::test_the_line_breaks_equal_their_browser_copy`.
The first six are red because the locator names `golden-set/seed/todo-tasks-example.json` before
T-17 writes it, and the sixth also waits on the bound T-14 declares. The rest are red because `TODO_TASK_TEXT_MAX_LENGTH`, `LINE_BREAKS` or their browser
copies do not exist yet. A case of `tests/fitness/` may be left red for one of those two reasons
and no other. Every further case red for one of them is named in this task's closing block with its
reason, so it is declared before the RED proof.
**Green by design:** every new rule that reads only the four to-do fixture files — the `tasks` key's
shape, case names and sentences given once, the verdict set, lengths, escapes, the seven line breaks,
the 101-emoji case. They are green on their first run because T-1 wrote those files before this task
runs and their subject is test data, not code. Each is listed by id in the closing block for
`green-by-design`.
**Verification:** `./scripts/test.sh fitness` shows only the cases named above, and the ones this
task's closing block adds, failing, each for its stated reason. `test_the_frontend_reads_no_corpus_file`,
`test_no_suite_reads_the_seed_corpus` and every entry rule pass.

### T-11 · build-tests-e2e · R-1, R-2, R-3, R-4, R-6, R-7, R-8, R-9
**Wave:** 1b
**Files:** `e2e/suite/features/todo_list.feature`, `e2e/suite/steps/todo_list_steps.py`,
`e2e/suite/test_scenarios.py`
**Scope:** `e2e/suite/features/todo_list.feature`, `e2e/suite/steps/todo_list_steps.py`,
`e2e/suite/test_scenarios.py`
**Does:** Turns into Gherkin the twenty-two seeds the evidence map binds in the black box, with the
titles of `scenarios.md` verbatim, each tagged `@req:CR-2609-823a/R-n`, in business language with no
path, status or column. The values are the inline ones of `scenarios.md` § Inline values, or produced
by a rule ("Task 001" to "Task 101"). No fixture file is read, because `e2e/suite/golden_set.py`
re-exports the guestbook's files alone and no author may write it. "Deletes and confirms" binds to one
deletion. The two `R-9` scenarios send both requests before either is answered. No step text the
guestbook's steps already define is defined again, because a second definition brought in by a star
import replaces the first for every scenario. `e2e/suite/test_scenarios.py` gains one star import of
the new step module and nothing else.
**Depends on:** —
**Parallel:** yes, beside T-9 and T-10. Its member goes out once wave 1a has returned. The profile
orders it after `build-tests-integration` for the locator the guestbook's steps import, and none of
its tasks reads a to-do fixture.
**Must be red:** `e2e.suite.test_scenarios::test_adding_the_first_task`,
`e2e.suite.test_scenarios::test_the_same_text_added_twice_makes_two_separate_tasks`,
`e2e.suite.test_scenarios::test_a_task_sent_as_already_done_is_still_saved_as_not_done`,
`e2e.suite.test_scenarios::test_spaces_between_the_words_of_a_task_are_kept_as_typed`,
`e2e.suite.test_scenarios::test_a_line_break_after_the_last_word_is_trimmed_not_refused`,
`e2e.suite.test_scenarios::test_the_list_shows_the_newest_task_at_the_top`,
`e2e.suite.test_scenarios::test_a_hundred_and_one_tasks_are_all_shown_on_one_list`,
`e2e.suite.test_scenarios::test_marking_a_task_done_leaves_it_where_it_was`,
`e2e.suite.test_scenarios::test_correcting_a_tasks_text_leaves_it_where_it_was`,
`e2e.suite.test_scenarios::test_a_task_somebody_else_added_appears_after_a_reload`,
`e2e.suite.test_scenarios::test_a_task_marked_done_stays_done_after_a_reload`,
`e2e.suite.test_scenarios::test_a_task_marked_done_by_mistake_goes_back_to_not_done`,
`e2e.suite.test_scenarios::test_marking_done_a_task_that_is_already_done_leaves_it_done`,
`e2e.suite.test_scenarios::test_marking_not_done_a_task_that_is_already_not_done_leaves_it_not_done`,
`e2e.suite.test_scenarios::test_correcting_a_typo_in_a_task`,
`e2e.suite.test_scenarios::test_editing_a_done_task_keeps_it_done_and_where_it_was`,
`e2e.suite.test_scenarios::test_deleting_one_task_leaves_the_others_and_does_not_come_back`,
`e2e.suite.test_scenarios::test_marking_done_a_task_that_somebody_else_deleted`,
`e2e.suite.test_scenarios::test_editing_a_task_that_somebody_else_deleted_creates_nothing`,
`e2e.suite.test_scenarios::test_deleting_the_same_task_twice`,
`e2e.suite.test_scenarios::test_an_edit_and_a_tick_sent_at_the_same_moment_are_both_kept`,
`e2e.suite.test_scenarios::test_two_people_marking_the_same_task_done_at_the_same_moment_leave_it_done`
**Turns green:** `tests.fitness.test_context_declarations::test_every_screen_and_feature_a_context_names_is_on_disk`.
It has been red since the design's convergence round claimed this feature file before it existed
(`Q-19`, signed off at the design close, `Q-24`), and the implement baseline carries it. This task's
feature file closes it in wave 1. It is not declared, since the RED proof finds it green.
**Verification:** `./scripts/test.sh e2e --collect-only` shows every step bound and the twenty-two
scenarios collected. `./scripts/test.sh e2e` shows each named scenario failing against an application
that serves no to-do route, while the twenty-two guestbook scenarios pass unedited.
`./scripts/test.sh fitness` shows the on-disk case passing.

### T-12 · build-tests-e2e · R-2, R-4, R-5
**Wave:** 1b
**Files:** `e2e/ui/test_smoke.py`
**Scope:** `e2e/ui/`
**Does:** Adds four smoke cases against the built bundle. The to-do address opens its screen
directly. The way between the screens leads both ways. 200 emoji typed into the add field are held
and added, and 201 are refused with the too-long sentence. A done task's text measures at least 4.5:1
against the surface it is painted on, opacity included, through `e2e/ui/styles.py`. Data is seeded
through the harness's API client, never the screen. The comment on `_LOCKUP` is corrected, because the
exact link "Guestbook" is now the frame's navigation link rather than the lockup (`A-4`). No existing
case is renamed and no existing assertion changes. The smoke cites no requirement.
**Depends on:** —
**Parallel:** yes, beside T-9 and T-10. Within its member it runs with T-11 in any order.
**Must be red:** `e2e.ui.test_smoke::test_the_todo_list_opens_at_its_own_address`,
`e2e.ui.test_smoke::test_the_way_between_the_screens_leads_both_ways`,
`e2e.ui.test_smoke::test_a_task_of_emoji_is_bounded_in_the_unit_the_server_uses`,
`e2e.ui.test_smoke::test_a_done_tasks_text_clears_the_contrast_floor_where_it_is_painted`
**Verification:** `./scripts/test.sh ui` shows the four new cases failing, because the built bundle has
no to-do screen. Every existing smoke case passes as before.

## Wave 2 — implementation

### T-13 · build-migration · R-1, R-3, R-4
**Wave:** 2
**Files:** `alembic/versions/*_create_todo_tasks_table.py`
**Scope:** `alembic/versions/`
**Does:** Writes the one revision, issued by `./scripts/db.sh revision`, with its parent the head
`./scripts/db.sh status` reports (today `a1b2c3d4e5f6`). Its `upgrade()` and `downgrade()` are exactly
the ordered operations of `spec/design/data-model.md` § The revision that creates `todo_tasks`, with the
literal `200` and never the constant, no server default, no data and no backfill. Its mode is
`backward compatible`.
**Depends on:** T-4
**Parallel:** yes, beside every `build-backend` task. Neither imports the other and both build from the
same frozen document, so a service or router case red for the missing table mid-wave is expected.
**Turns green:** T-4's two migration cases.
**Verification:** `./scripts/db.sh migrate` applies it forwards from the current head.
`./scripts/test.sh integration` shows T-4's migration cases passing, and
`test_the_models_and_the_migrations_describe_the_same_schema` passing once T-14's model exists.

### T-14 · build-backend · R-1, R-2, R-3, R-4
**Wave:** 2
**Files:** `app/contexts/todo_list/__init__.py`, `app/contexts/todo_list/models/__init__.py`,
`app/contexts/todo_list/models/todo_task.py`, `app/contexts/__init__.py`
**Scope:** `app/contexts/todo_list/`, `app/contexts/__init__.py`
**Does:** Declares `TodoTask` with the four columns of `spec/design/data-model.md` § `todo_tasks` and
`ix_todo_tasks_created_at_id` in `__table_args__`. Beside it go `TODO_TASK_TEXT_MAX_LENGTH = 200` and
`LINE_BREAKS`, the seven code points of `A-1` written as numbers the way the trim set is, in the shape
T-10's docstring parses. The context's public API names the three, the layer's `__init__.py` carries
its docstring, and one registration line is appended to `app/contexts/__init__.py`.
**Depends on:** T-9, T-10
**Parallel:** its member's first to-do task, since T-15 imports the model. It runs beside T-13, T-17
and every other member.
**Turns green:** T-9's four model cases and `test_this_schema_holds_exactly_two_tables`;
`tests.fitness.test_context_boundaries::test_every_context_document_has_code_and_every_context_directory_has_a_document`,
red since `spec/contexts/todo_list.md` was written, where `frontend/src/contexts/todo_list/` exists
from wave 1 and this directory is the last missing half; and T-10's constant cases, the two length
cases together with T-19.
**Verification:** `./scripts/test.sh unit` shows T-9's model cases passing. `./scripts/test.sh fitness`
shows the document-and-code case passing. `test_every_context_directory_is_registered_and_every_registration_exists`
is red from this task until T-16 appends `app/api.py`'s line, inside the same dispatch.

### T-15 · build-backend · R-1, R-2, R-3, R-4, R-6, R-7, R-8, R-9
**Wave:** 2
**Files:** `app/contexts/todo_list/schemas/__init__.py`, `app/contexts/todo_list/schemas/todo_tasks.py`,
`app/contexts/todo_list/services/__init__.py`, `app/contexts/todo_list/services/todo_tasks.py`
**Scope:** `app/contexts/todo_list/`
**Does:** Writes the four shapes of `spec/design/api.md` § Shapes. They carry no bound and import no
part of the text rule. The create shape has no `done`, and the update shape has two optional fields
with `done` read strictly as a boolean. It writes the service's add, read, correct, mark and delete
with the statement shapes of `spec/design/data-model.md` § Two writers on one task: no read before a
write, no upsert, `created_at` from the service's clock on insert only, and the list by `created_at`
then `id`, both descending. The text's judgement runs normalize, empty, one line, measure, over
`app/platform/schemas/text.py` and the model's constants, and raises one domain exception per verdict.
`TodoTaskNotFoundError` is raised when a statement returns no row. The names are those T-2 and T-9
import.
**Depends on:** T-2, T-9, T-14
**Parallel:** after T-14 in its member, and beside T-13.
**Verification:** `./scripts/test.sh unit` shows T-9's rule cases passing. `./scripts/test.sh integration`
shows T-2's nineteen cases passing once T-13's revision is in.

### T-16 · build-backend · R-1, R-2, R-3, R-4, R-6, R-7, R-8
**Wave:** 2
**Files:** `app/contexts/todo_list/routers/__init__.py`, `app/contexts/todo_list/routers/todo_tasks.py`,
`app/api.py`
**Scope:** `app/contexts/todo_list/`, `app/api.py`
**Does:** Binds the four routes of `spec/design/api.md` § Endpoints, with the path parameter
`todo_task_id`. `responses=` declares the `422` as an `anyOf` over `Refusal` and `HTTPValidationError`
on `POST` and `PATCH`, and the `404` on `PATCH` and `DELETE`; `total` is declared with a lower bound of
zero. The five codes are written as string literals with the sentences of § The to-do list's refusals.
`todo_task_empty_patch` is decided beside the endpoint before the service is called, and each domain
exception is translated explicitly in a `match` block. One `include_router` line is appended to
`app/api.py`. This task does not write `frontend/src/api/schema.d.ts`, which is T-23's.
**Depends on:** T-3, T-15
**Parallel:** after T-15 in its member, and beside T-13.
**Turns green:** `./scripts/contracts.sh`, a gate of `./scripts/check.sh` and no case, whose eleven
findings have been accepted by name at each stage end since the design (`Q-21`); T-3's twenty-six
cases; and, with T-13, T-11's twenty-two scenarios.
**Verification:** `./scripts/contracts.sh` exits 0. `./scripts/test.sh integration` shows T-3's cases
passing. `./scripts/test.sh e2e` shows the twenty-two to-do scenarios passing, and T-12's four smoke
cases still red until T-22.

### T-17 · build-backend · R-11
**Wave:** 2
**Files:** `golden-set/seed/todo-tasks-example.json`, `scripts/seed_golden_set.py`, `scripts/seed.sh`
**Scope:** `golden-set/seed/todo-tasks-example.json`, `scripts/seed_golden_set.py`, `scripts/seed.sh`
**Does:** Writes the five example tasks of `scenarios.md` § Seed data under the key `tasks`, as
`{text, done}` with a `story` and a `demonstrates` line, with number 3 done. The seeder asks each list
on its own whether it is empty: the guest book by its entries as today, the to-do list by the `total`
of `GET /api/todo-tasks`. It posts every example task through `POST` and then marks the done one
through `PATCH`, never in production, and leaves the guest book's condition and file as they are. The
header and `--help` of `seed.sh` name both lists.
**Depends on:** T-1, T-4, T-10
**Parallel:** yes, independent of T-14…T-16. It speaks HTTP, and its tests fake the answers.
**Turns green:** T-4's six tooling cases and T-10's six seed-file cases, the last of them together
with T-14.
**Verification:** `./scripts/test.sh tooling` shows every seeder case passing. `./scripts/test.sh fitness`
shows the seed-file cases passing. `./scripts/seed.sh --help` names the guest book and the to-do list.

### T-18 · build-frontend · R-2
**Wave:** 2
**Files:** `frontend/src/lib/text.ts`, `frontend/src/contexts/guestbook/lib/entryText.ts`,
`frontend/src/contexts/guestbook/lib/guestbookEntry.ts`,
`frontend/src/contexts/guestbook/components/EntryComposer.tsx`,
`frontend/src/contexts/guestbook/hooks/useEntryQueryParams.ts`
**Scope:** `frontend/src/lib/text.ts`, `frontend/src/contexts/guestbook/lib/entryText.ts`,
`frontend/src/contexts/guestbook/lib/guestbookEntry.ts`,
`frontend/src/contexts/guestbook/components/EntryComposer.tsx`,
`frontend/src/contexts/guestbook/hooks/useEntryQueryParams.ts`
**Does:** Moves the shared text rule, unchanged, from the guestbook's `lib/entryText.ts` to
`frontend/src/lib/text.ts`, removes the old file, and points the guestbook's three importers at
`@/lib/text`. The move and the three imports are one sitting, so the tree compiles at both ends of it.
**Depends on:** T-5
**Parallel:** its member's first task, since T-19 imports `@/lib/text`.
**Turns green:** `src/contexts/guestbook/lib/entryText.test.ts::src/contexts/guestbook/lib/entryText.test.ts`,
the load failure T-5 declared. The file loads again and every one of its cases passes.
**Verification:** `./scripts/test.sh frontend` shows every guestbook case passing.
`./scripts/test.sh fitness` shows `test_no_screen_reaches_into_another_contexts_folder` passing.

### T-19 · build-frontend · R-2, R-4, R-6
**Wave:** 2
**Files:** `frontend/src/contexts/todo_list/lib/todoTask.ts`
**Scope:** `frontend/src/contexts/todo_list/`
**Does:** Writes the `TodoTask` type, aliased from the generated contract as
`components['schemas']['TodoTaskRead']`. It writes `export const TODO_TASK_TEXT_MAX_LENGTH = 200` and
`LINE_BREAKS` in the shape T-10's docstring parses, and the verdict in the order `BR-07` then `BR-06`
over `@/lib/text`, with the sentences of `spec/design/ui/todo-list.md` § The refusals this screen can
show.
**Depends on:** T-5, T-10, T-18
**Parallel:** after T-18 in its member, and beside every other member.
**Turns green:** T-5's three rule cases, and T-10's two length cases together with T-14.
**Verification:** `./scripts/test.sh frontend` shows T-5's `todoTask.test.ts` cases passing.
`./scripts/test.sh fitness` shows the two length cases passing once T-14 is in.

### T-20 · build-frontend · R-4, R-6, R-7
**Wave:** 2
**Files:** `frontend/src/components/ui/Checkbox.tsx`,
`frontend/src/contexts/todo_list/components/TodoTaskRow.tsx`,
`frontend/src/contexts/todo_list/components/DeleteTodoTaskDialog.tsx`
**Scope:** `frontend/src/components/ui/Checkbox.tsx`, `frontend/src/contexts/todo_list/`
**Does:** Writes the done control as a design-system primitive with checkbox semantics, exporting the
component and its props interface and drawn with existing tokens only. It writes one task's row as
`spec/design/ui/todo-list.md` § A task's row gives it (every state, correction in place, the focus
rule of `Q-16`), and the delete question over `Modal` as § The delete question gives it.
**Depends on:** T-6, T-19
**Parallel:** after T-19 in its member.
**Turns green:** T-6's six row cases.
**Verification:** `./scripts/test.sh frontend` shows T-6's `TodoTaskRow.test.tsx` cases passing.

### T-21 · build-frontend · R-1, R-2, R-3, R-8, R-10
**Wave:** 2
**Files:** `frontend/src/contexts/todo_list/hooks/useTodoTasks.ts`,
`frontend/src/contexts/todo_list/components/TodoTaskComposer.tsx`,
`frontend/src/contexts/todo_list/pages/TodoListPage.tsx`
**Scope:** `frontend/src/contexts/todo_list/`
**Does:** Writes the resource's query and its four mutations with `todoTaskKeys`. The cache is written
only from the application's answer, and the list is refetched after a change that went through. It
writes the add field, which has no attribute that stops input at a bound, applies the verdict before
sending, sends the text as the shared rule leaves it, and shows a refusal under the field. It writes
the screen with its regions, its loading, empty, failed and default states, and its notices with the
words of `spec/design/ui/todo-list.md` § Copy (`Q-15`), keyboard behaviour as § Keyboard and
accessibility gives it (`Q-16`), and its own footer sentence.
**Depends on:** T-5, T-6, T-19, T-20
**Parallel:** after T-20 in its member.
**Turns green:** T-5's four composer cases, and T-6's two hook cases and nine page cases.
**Verification:** `./scripts/test.sh frontend` shows every to-do vitest case passing.

### T-22 · build-frontend · R-5
**Wave:** 2
**Files:** `frontend/src/components/shell/PageFrame.tsx`, `frontend/src/pages/StatusPages.tsx`,
`frontend/src/routes.ts`, `frontend/src/router.tsx`
**Scope:** `frontend/src/components/shell/PageFrame.tsx`, `frontend/src/pages/StatusPages.tsx`,
`frontend/src/routes.ts`, `frontend/src/router.tsx`
**Does:** Gives the frame the lockup "Product name" and "P", still leading to the guestbook, and the
navigation group `Screens` with `Guestbook` and `To-do list`, the current one marked, as
`spec/design/ui/system-states.md` § The navigation between the screens gives it. Each screen gets its
own footer, and the not-found page none. `frontend/src/contexts/guestbook/pages/GuestbookPage.tsx` is
outside this change, because the guestbook's frontend changes by three import paths and nothing else
(`design/delta/architecture.md` § What this change does not move). So the guestbook's own sentence
reaches its screen without an edit there, and a way the frame cannot provide is reported rather than
taken by editing that file. The not-found page's sentence becomes `There is nothing at this address.`.
`TODO_LIST_ROUTE = '/todo-list'` is added, with one route binding it to `TodoListPage`. `/` still
redirects to the guestbook. The frame's docstrings stop saying there is one screen.
**Depends on:** T-7, T-21
**Parallel:** after T-21 in its member, since the route binds the page.
**Turns green:** T-7's four cases, and T-12's four smoke cases.
**Verification:** `./scripts/test.sh frontend` shows T-7's cases passing. `./scripts/test.sh ui` shows
T-12's four cases passing, and every existing smoke case, the focus-ring walk over the new links
included, still passing.

### T-23 · build-frontend · R-1, R-4, R-6, R-7, R-8
**Wave:** 2
**Files:** `frontend/src/api/schema.d.ts`
**Scope:** `frontend/src/api/schema.d.ts`
**Does:** Regenerates the contract's types with `./scripts/generate.sh` once T-16's schemas and routers
exist. It gains two paths and the schemas `TodoTaskCreate`, `TodoTaskUpdate`, `TodoTaskRead` and
`TodoTaskList`. It is never edited by hand.
**Depends on:** T-16
**Parallel:** this is the one edge between two builders of wave 2 (`spec/design/architecture.md`
§ Who writes what, "Disjoint is not independent", edge 1). Every other `build-frontend` task runs beside
`build-backend`. If `build-frontend` returns before T-16 exists, the `./scripts/generate.sh` the
orchestrator runs when wave 2 has returned (implement table, row 33) produces this file, and this task
is met by that run. Until then the `tsc` step of `./scripts/lint.sh` is red on the to-do aliases, and
vitest is not.
**Verification:** `./scripts/generate.sh --check` exits 0, and `./scripts/lint.sh` exits 0.

### T-24 · build-platform · —
**Wave:** 2
**Files:** `.github/CODEOWNERS`
**Scope:** `.github/CODEOWNERS`
**Does:** Adds the to-do list's five rows in the file's own per-context pattern:
`/spec/contexts/todo_list.md`, `/contracts/openapi/todo_list.yaml`, `/app/contexts/todo_list/`,
`/frontend/src/contexts/todo_list/` and `/e2e/suite/features/todo_list.feature`. Each names
`@jarekwas`, the owner the catch-all rules name, since no other owner is recorded anywhere. The file's
comment stops saying there is one context. No requirement asks for this. It is the Ownership row of
`spec/design/architecture.md` § What a new feature adds, for the context `R-1`…`R-9` opened.
**Depends on:** —
**Parallel:** yes, beside every task of wave 2.
**Verification:** `grep -nE '^/[^ ]*todo_list' .github/CODEOWNERS` prints exactly the five rows. No
suite reads the file (`spec/design/testing.md` § CR-2609-823a, "No test file of their own"), and
GitHub reads it once the branch is pushed.

## Scope against the design

The union of the tasks' `Scope:` fields against the boundary the design recorded (the preflight's
`boundary`). No task writes outside it. The rows no task touches belong to the `spec_sync` stage,
whose members write documentation and the live specification rather than code.

| Path from the boundary | Tasks that touch it |
|---|---|
| `.github/CODEOWNERS` | T-24 |
| `CLAUDE.md` | none in `implement` (spec_sync) |
| `README.md` | none in `implement` (spec_sync) |
| `alembic/versions/` | T-13 |
| `app/api.py` | T-16 |
| `app/contexts/__init__.py` | T-14 |
| `app/contexts/todo_list/` | T-14, T-15, T-16 |
| `docs/` | none in `implement` (spec_sync) |
| `e2e/suite/features/todo_list.feature` | T-11 |
| `e2e/suite/steps/todo_list_steps.py` | T-11 |
| `e2e/suite/test_scenarios.py` | T-11 |
| `e2e/ui/` | T-12 |
| `frontend/src/api/schema.d.ts` | T-23 |
| `frontend/src/components/shell/PageFrame.test.tsx` | T-7 |
| `frontend/src/components/shell/PageFrame.tsx` | T-22 |
| `frontend/src/components/ui/Checkbox.tsx` | T-20 |
| `frontend/src/contexts/guestbook/components/EntryComposer.tsx` | T-18 |
| `frontend/src/contexts/guestbook/hooks/useEntryQueryParams.ts` | T-18 |
| `frontend/src/contexts/guestbook/lib/entryText.test.ts` | T-5 |
| `frontend/src/contexts/guestbook/lib/entryText.ts` | T-18 |
| `frontend/src/contexts/guestbook/lib/guestbookEntry.ts` | T-18 |
| `frontend/src/contexts/todo_list/` | T-5, T-6, T-19, T-20, T-21 |
| `frontend/src/lib/text.ts` | T-18 |
| `frontend/src/pages/StatusPages.test.tsx` | T-7 |
| `frontend/src/pages/StatusPages.tsx` | T-22 |
| `frontend/src/router.test.tsx` | T-7 |
| `frontend/src/router.tsx` | T-22 |
| `frontend/src/routes.ts` | T-22 |
| `golden-set/fixtures/` | T-1 |
| `golden-set/seed/todo-tasks-example.json` | T-17 |
| `scripts/seed.sh` | T-17 |
| `scripts/seed_golden_set.py` | T-17 |
| `spec/ADR/` | none in `implement` (spec_sync) |
| `spec/contexts/` | none in `implement` (spec_sync) |
| `spec/design/` | none in `implement` (spec_sync) |
| `spec/glossary.md` | none in `implement` (spec_sync) |
| `spec/rationale/` | none in `implement` (spec_sync) |
| `tests/_golden_set.py` | T-1 |
| `tests/fitness/` | T-10 |
| `tests/integration/` | T-1, T-2, T-3, T-4 |
| `tests/tooling/` | T-4 |
| `tests/unit/` | T-9 |

T-8's `uat.md` lies inside this change record, which is not a boundary path.

## Disjointness

**Wave 1**, by task:
T-1 {`golden-set/fixtures/todo-tasks-ordinary.json`, `golden-set/fixtures/todo-tasks-boundary.json`,
`golden-set/fixtures/todo-tasks-refused.json`, `golden-set/fixtures/todo-task-text.json`,
`tests/_golden_set.py`, `tests/integration/test_todo_tasks_corpus.py`};
T-2 {`tests/integration/test_todo_tasks_service.py`, `tests/integration/test_todo_tasks_concurrency.py`};
T-3 {`tests/integration/test_todo_tasks_router.py`, `tests/integration/test_todo_tasks_contract.py`};
T-4 {`tests/integration/test_migrations.py`, `tests/tooling/test_seed_golden_set.py`};
T-5 {`frontend/src/contexts/todo_list/lib/todoTask.test.ts`,
`frontend/src/contexts/todo_list/components/TodoTaskComposer.test.tsx`,
`frontend/src/contexts/guestbook/lib/entryText.test.ts`};
T-6 {`frontend/src/contexts/todo_list/components/TodoTaskRow.test.tsx`,
`frontend/src/contexts/todo_list/hooks/useTodoTasks.test.tsx`,
`frontend/src/contexts/todo_list/pages/TodoListPage.test.tsx`};
T-7 {`frontend/src/router.test.tsx`, `frontend/src/components/shell/PageFrame.test.tsx`,
`frontend/src/pages/StatusPages.test.tsx`};
T-8 {this record's `uat.md`};
T-9 {`tests/unit/test_todo_task_text_rules.py`, `tests/unit/test_todo_task_model.py`,
`tests/unit/test_guestbook_entry_model.py`};
T-10 {`tests/fitness/test_golden_set.py`, `tests/fitness/test_length_constants.py`};
T-11 {`e2e/suite/features/todo_list.feature`, `e2e/suite/steps/todo_list_steps.py`,
`e2e/suite/test_scenarios.py`};
T-12 {`e2e/ui/test_smoke.py`}.
**Intersection: empty.** No path stands in two sets, and by member the sets fall in the four trees
`spec/design/testing.md` § Four file sets gives: `tests/unit/` with `tests/fitness/`;
`tests/integration/`, `tests/tooling/`, `golden-set/fixtures/` and `tests/_golden_set.py`; the vitest
files; `e2e/`. Every wave-1 path is a test, test data or the locator. None is a module wave 2 writes.

**Wave 2**, by task:
T-13 {the one new file under `alembic/versions/`};
T-14 {`app/contexts/todo_list/__init__.py`, `app/contexts/todo_list/models/__init__.py`,
`app/contexts/todo_list/models/todo_task.py`, `app/contexts/__init__.py`};
T-15 {`app/contexts/todo_list/schemas/__init__.py`, `app/contexts/todo_list/schemas/todo_tasks.py`,
`app/contexts/todo_list/services/__init__.py`, `app/contexts/todo_list/services/todo_tasks.py`};
T-16 {`app/contexts/todo_list/routers/__init__.py`, `app/contexts/todo_list/routers/todo_tasks.py`,
`app/api.py`};
T-17 {`golden-set/seed/todo-tasks-example.json`, `scripts/seed_golden_set.py`, `scripts/seed.sh`};
T-18 {`frontend/src/lib/text.ts`, `frontend/src/contexts/guestbook/lib/entryText.ts`,
`frontend/src/contexts/guestbook/lib/guestbookEntry.ts`,
`frontend/src/contexts/guestbook/components/EntryComposer.tsx`,
`frontend/src/contexts/guestbook/hooks/useEntryQueryParams.ts`};
T-19 {`frontend/src/contexts/todo_list/lib/todoTask.ts`};
T-20 {`frontend/src/components/ui/Checkbox.tsx`,
`frontend/src/contexts/todo_list/components/TodoTaskRow.tsx`,
`frontend/src/contexts/todo_list/components/DeleteTodoTaskDialog.tsx`};
T-21 {`frontend/src/contexts/todo_list/hooks/useTodoTasks.ts`,
`frontend/src/contexts/todo_list/components/TodoTaskComposer.tsx`,
`frontend/src/contexts/todo_list/pages/TodoListPage.tsx`};
T-22 {`frontend/src/components/shell/PageFrame.tsx`, `frontend/src/pages/StatusPages.tsx`,
`frontend/src/routes.ts`, `frontend/src/router.tsx`};
T-23 {`frontend/src/api/schema.d.ts`};
T-24 {`.github/CODEOWNERS`}.
**Intersection: empty.** By member it is the pairwise check of `spec/design/architecture.md` § Who
writes what: backend ∩ frontend, backend ∩ migration, backend ∩ platform, frontend ∩ migration,
frontend ∩ platform and migration ∩ platform are all ∅. No wave-2 path is a test file. Every
`build-frontend` path is a module, and every `build-tests-frontend` path in the same tree is a
`*.test.ts` or `*.test.tsx`. The schema's two trees meet only as data: `todo_task.py` (T-14) and the
revision (T-13) describe one table and neither imports the other, and `tests/integration/test_migrations.py`
compares them.

## Requirement coverage

| R-n | Tasks |
|---|---|
| R-1 | T-2, T-3, T-4, T-5, T-6, T-8, T-9, T-11, T-13, T-14, T-15, T-16, T-21, T-23 |
| R-2 | T-1, T-2, T-3, T-5, T-9, T-10, T-11, T-12, T-14, T-15, T-16, T-18, T-19, T-21 |
| R-3 | T-1, T-2, T-3, T-4, T-6, T-8, T-9, T-11, T-13, T-14, T-15, T-16, T-21 |
| R-4 | T-2, T-3, T-4, T-6, T-8, T-9, T-11, T-12, T-13, T-14, T-15, T-16, T-19, T-20, T-23 |
| R-5 | T-7, T-8, T-12, T-22 |
| R-6 | T-1, T-2, T-3, T-6, T-11, T-15, T-16, T-19, T-20, T-23 |
| R-7 | T-2, T-3, T-6, T-11, T-15, T-16, T-20, T-23 |
| R-8 | T-2, T-3, T-6, T-11, T-15, T-16, T-21, T-23 |
| R-9 | T-2, T-8, T-11, T-15 |
| R-10 | T-6, T-21 |
| R-11 | T-4, T-8, T-10, T-17 |

Every requirement has a task, and every task but T-24 cites one. T-24 serves none and says so in
its heading. No task is finished by changing an assertion. Wave 2 writes no test, and every case a
builder turns green was written, and seen red, in wave 1.

## What can go in parallel

- **Wave 1a, in one message:** `build-tests-integration` (T-1, then T-2, T-3 and T-4, with T-4 after
  T-1), `build-tests-frontend` (T-5, T-6, T-7 in any order) and `build-tests-uat` (T-8). Nothing
  orders the three members. T-5 reads T-1's `todo-task-text.json` at run time, and its reds are
  observed after the wave.
- **Wave 1b, in one message, once wave 1a has returned:** `build-tests-unit` (T-9 and T-10 in any
  order) and `build-tests-e2e` (T-11 and T-12 in any order). The profile orders both after
  `build-tests-integration` alone. T-9 reads T-1's corpus and T-2's exception names, and T-10 reads
  T-1's locator.
- **The RED proof, between the waves.** Declare every `Must be red:` id above and every id the
  closing blocks of T-1, T-4 and T-10 add. Run the proof, observe, and file each `Green by design:`
  entry. The `Turns green:` cases carried from the design close (T-11's on-disk case, T-14's
  context-boundaries case) are baseline reds, not declarations. `./scripts/lint.sh` may be red between
  the waves on imports of modules wave 2 writes. It is not a case a runner collects, and it clears
  with wave 2.
- **Wave 2, in one message:** `build-backend` (T-14, T-15, T-16 in that order; T-17 at any point),
  `build-migration` (T-13), `build-frontend` (T-18, T-19, T-20, T-21, T-22 in that order; T-23 last
  and only once T-16 exists) and `build-platform` (T-24).
- **The orders that bind:** T-15 after T-14 (it imports the model), T-16 after T-15 (it binds the
  service), T-19 after T-18 (it imports `@/lib/text`), T-20 after T-19, T-21 after T-20 (the page
  renders the row), T-22 after T-21 (the route binds the page), and **T-23 after T-16**, the one edge
  that crosses two builders.
- **The orders that do not bind:** migration against backend (neither imports the other, and a case
  red for the missing table mid-wave is expected); frontend against backend except T-23 (the modules
  are built against the frozen contract in `spec/design/api.md`, and vitest does not type-check);
  T-17 against T-14…T-16; T-24 against everything. None of these is to be serialised out of caution.

## Outside every task — for the orchestrator

1. **An undeclared red in the design.** T-5's one-line import edit makes
   `frontend/src/contexts/guestbook/lib/entryText.test.ts` fail to load from wave 1 until T-18 moves
   the rule. `spec/design/testing.md` names no such red. This plan declares it on T-5, and T-18 closes it.
2. **A count in the design.** `spec/design/testing.md` § CR-2609-823a, "The fixture half this change
   adds", says `todo-task-text.json` holds "the nineteen `scenarios.md` lists … and one more".
   `scenarios.md`'s table holds eighteen cases, the six-character row counted as six, and T-1 writes
   those plus `BR-07`'s precedence case, nineteen in all. No value exists for a twentieth. For
   reconcile-design.
3. **`golden-set/README.md` has no author and is outside the boundary.** Two of its sentences become
   false: § `seed/` ("One file: `entries-welcome.json`") and its exception naming one browser reader
   of the corpus. This is the architecture fragment's "Found outside every write set", item 1, still open.
4. **`spec/design/conventions.md` § Frontend** still says `entryText.ts` stays in the guestbook's
   folder because the browser has one caller. For reconcile-design.
5. **The task-text data invariant** under `contracts/invariants/` is written by the `spec_sync`
   stage's convergence round, once T-2's and T-9's witnesses exist (`Q-21`, item 6).
6. **The guestbook's footer.** `spec/design/ui/system-states.md` makes the footer each screen's own,
   while the architecture keeps `GuestbookPage.tsx` untouched. T-22 is told to satisfy both, and to
   report rather than edit that file if the frame cannot.
7. **Production and the seeder.** `spec/design/testing.md` lists "production refused for tasks too"
   as red until the seeder changes. It is green by design (T-4), because the seeder refuses production
   before it reads either list.

## Lessons from the implementation

*Appended by the implementers during a wave, one line per lesson. The orchestrator pastes this
section into the next wave's prompts, so the second wave does not discover what the first already
knows, and `reconcile-docs` reads it at the end instead of guessing why something has the shape it
has.*

*Not "I did X". A lesson is something that surprised you: an assumption that turned out false, a test
that does not catch what it was meant to, or a place where the code does not work the way it looks.*

*Nothing yet.*

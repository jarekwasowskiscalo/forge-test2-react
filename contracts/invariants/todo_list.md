---
contract: invariants
domain: todo_list
version: 1
---

# Data invariants — to-do list

Things that must always be true of the to-do list's data. `D-01`…`D-04` stand in
[`guestbook.md`](guestbook.md), and the first three hold for `todo_tasks` as for every table; the
format of every entry and the rules of the `D-xx` space: [`README.md`](README.md).

---

## `D-05` — a stored task's text is normalized, one line, and within its bound in code points

Every `text` in `todo_tasks` is in **Unicode NFC**, carries no member of the written trim set at
either end, holds none of the seven code points of `LINE_BREAKS`, and is between 1 and
`TODO_TASK_TEXT_MAX_LENGTH` (200) **code points** long (`BR-06`, `BR-07`). It is `D-04` for the
to-do list's one field, plus the one-line rule the guestbook does not have: a message keeps its
line breaks as content, and a task refuses them.

**Witness:** `tests/integration/test_todo_tasks_service.py::test_a_stored_text_is_normalized_one_line_and_within_the_bound_in_code_points`, `tests/unit/test_todo_task_text_rules.py::test_every_case_gets_the_verdict_the_corpus_states` and `tests/unit/test_todo_task_text_rules.py::test_any_text_is_either_refused_or_kept_normalized_one_line_and_within_the_bound`
**Kind of evidence:** three, because the invariant is about a value, about agreement, and about
every text. The round trip is an invocation only a database can answer. The corpus is read by the
browser's rule test too (`frontend/src/contexts/todo_list/lib/todoTask.test.ts`). The generator
draws from every text rather than the listed ones.

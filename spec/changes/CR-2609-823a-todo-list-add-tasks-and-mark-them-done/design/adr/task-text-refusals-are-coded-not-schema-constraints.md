---
id: ADR-NNNN
title: A task's text is refused with a stable code, never by a constraint in the published schema
status: Proposed
date: 2026-09-24
cr: CR-2609-823a
supersedes: []
superseded_by: null
aliases: []
---

# ADR-NNNN — A task's text is refused with a stable code, never by a constraint in the published schema

## Context

The requirements ask for three reasons, and the person must be told which one applies. A text
that is empty once trimmed is refused as empty (`R-2` clause 2). A text over 200 code points is
refused as too long (clause 3). A text that still carries a line break is refused "with a reason
of its own" (clause 6, `Q-11`). `BR-07` settles the overlap: a text that is both too long and on
two lines is refused as more than one line, "on the screen and by the application alike". The
scenarios tell the three reasons apart (`S-6`, `S-8`, `S-33`), and the integration corpus test
proves each on the wire (`spec/design/testing.md` § CR-2609-823a). The screen chooses where
to show a refusal by its `detail.code` (`spec/design/ui/todo-list.md` § The refusals this screen
can show).

**The convention in force answers differently.** Every text bound in this API was a schema
constraint, `Field(min_length, max_length)` over `NormalizedText`. An empty or over-long
`author` or `message` is answered with FastAPI's list of `{loc, msg, type}`
(`spec/design/api.md` § Refusals). `frontend/src/api/problem.ts` reduces that list to its `msg`.

**Two facts about the machinery forced the choice:**

- **A Pydantic length constraint runs before anything else can look at the text.** A
  201-code-point text with a line break inside would therefore be refused as too long, which is
  the opposite of what `BR-07` requires.
- **FastAPI never puts a refusal code in `openapi.json`.** A code is held still only by
  `x-refusals` in `contracts/openapi/*.yaml`, and `scripts/openapi_contract.py` looks for each
  code there as a string literal in a router module under `app/`. A code raised anywhere else is
  frozen by nothing.

**This does not supersede a recorded decision.** The decision of 2026-09-16 in
`spec/design/api.md` § Refusals rejected making "the router raise a coded refusal for the
Pydantic cases too". For the guestbook, that would have meant re-validating each field by hand
in the router, and minting codes whose only purpose was to make an over-narrow declaration come
true. That decision still holds for the guestbook's fields. This one concerns a new resource and
differs on three points: its rule belongs to the context (`BR-06`, `BR-07`); it is decided where
business rules are decided; and its three codes exist because a requirement asks for three
reasons. `spec/ADR/index.md` records no ADR that this contradicts.

## Decision

Every refusal of a task's text answers `422` with a stable code and a finished sentence in the
`Refusal` envelope, never with FastAPI's list of `{loc, msg, type}`. This holds for adding
(`POST`) and correcting (`PATCH`) alike. The codes are `todo_task_text_empty`,
`todo_task_text_multiline` and `todo_task_text_too_long`, decided in that order, so a text earns
exactly one of them. The text rule is not a field constraint: the published `text` of
`TodoTaskCreate` and `TodoTaskUpdate` is a string with no `minLength` or `maxLength`. The bounds
are stated in `spec/design/api.md` § The to-do list's refusals and under `x-refusals` in
`contracts/openapi/todo_list.yaml`. The verdict is decided outside Pydantic's field constraints,
where the context's rules are decided, and the router only translates it. The codes and their
sentences are literals in `app/contexts/todo_list/routers/todo_tasks.py`. The guestbook keeps
its own convention, so its fields still answer with FastAPI's list.

## Rejected alternatives

- **The guestbook's convention: bounds as `Field(min_length, max_length)`, answered with
  FastAPI's list.** It gives no code this contract owns, only Pydantic's type strings. Its
  length constraint also answers before any later check sees the text, so a text too long and on
  two lines would be refused as too long, against `BR-07`.
- **Custom Pydantic error types raised from a schema validator.** The code would be ours, but it
  would sit inside the list shape, which `frontend/src/api/problem.ts` reduces to its `msg`, so
  the screen could not branch on it. The code would also sit outside every router module, where
  the contract gate looks for each `x-refusals` literal, so nothing would hold it still.
- **A handler in `app/core/errors.py` that turns Pydantic errors into coded refusals.** It would
  put domain knowledge into the framework module, which by rule knows nothing about the domain.

## Consequences

- **One API now has two regimes for refusing a text.** The guestbook's fields answer with
  FastAPI's list, and a task's text answers with a code. `spec/design/api.md` § The to-do list's
  refusals states the difference, so that neither side is later "harmonised" toward the other.
  Each side is held by a test that sends real requests and checks each answer against the schema
  published for its status: `tests/integration/test_guestbook_entries_contract.py` for the
  guestbook, and `tests/integration/test_todo_tasks_contract.py`, which the implement stage
  writes, for the to-do list.
- **The three codes are part of the contract.** Removing or renaming one is a breaking change and
  a major version of `todo_list.yaml` (`contracts/README.md` § Compatibility mode).
  `./scripts/contracts.sh` goes red when a frozen code is missing as a literal from every router
  module.
- **The contract gate cannot see a length constraint added to the request schema later.** The
  comparison checks a subset, so the dump may carry more than the contract, and a `max_length`
  would pass the gate. Such a constraint would quietly bring back FastAPI's list for an over-long
  text and break `BR-07`. The tests that catch it are in
  `tests/integration/test_todo_tasks_router.py`: `test_each_text_refusal_answers_with_its_own_code`,
  on `POST` and on `PATCH`, and `test_a_text_too_long_and_on_two_lines_is_refused_as_multiline`.
  Both are written in the implement stage (`spec/design/testing.md` § CR-2609-823a).
- **`422` has two shapes on `POST` and `PATCH`, and both are published** as an `anyOf` over
  `Refusal` and `HTTPValidationError`, following the rule of 2026-09-16. A malformed body keeps
  FastAPI's list: a missing `text`, a `text` that is not a string, a `done` that is not a
  boolean, or an identifier that is not a UUID. This is held by
  `test_a_body_of_the_wrong_shape_gets_the_standard_validation_refusal` and by the contract test.
- **Refusals are decided before the task is looked up.** A request that could never succeed is
  refused for what it is, and never with `404`. This is held by
  `test_a_request_is_refused_for_what_it_is_whatever_its_identifier_names`.
- **The browser gives the same verdict in the same order** before it sends anything
  (`frontend/src/contexts/todo_list/lib/todoTask.ts`). It is held by
  `frontend/src/contexts/todo_list/lib/todoTask.test.ts`, which reads the same
  `todo-task-text.json` as the service's tests, and by `tests/fitness/test_length_constants.py`
  for the copies of the 200 and of `LINE_BREAKS`.
- **The store still refuses an over-long text.** The column is `String(200)`
  (`spec/design/data-model.md` § `todo_tasks`), which is a last line of defence and not the
  refusal path. It is held by `tests/unit/test_todo_task_model.py`.
- **The five sentences have two copies, and nothing compares them.** They are product text in
  the router module and are copied word for word into `spec/design/api.md`. The guestbook's two
  sentences rest on the same hope.

## Enforced by

- `scripts/openapi_contract.py`, run by `./scripts/contracts.sh` (gate `contracts`), catches a
  code under `x-refusals` in `contracts/openapi/todo_list.yaml` that no router module under
  `app/` holds as a literal.
- `tests/integration/test_todo_tasks_router.py` (implement stage):
  - `test_each_text_refusal_answers_with_its_own_code` catches an empty, over-long or multi-line
    text answered with FastAPI's list or with the wrong code.
  - `test_a_text_too_long_and_on_two_lines_is_refused_as_multiline` catches the length being
    decided first.
  - `test_a_request_is_refused_for_what_it_is_whatever_its_identifier_names` catches the lookup
    running before the refusal.
- `tests/integration/test_todo_tasks_contract.py` (implement stage) catches an answer whose body
  does not match the schema published for its status, both shapes of `422` included.
- `tests/integration/test_todo_tasks_corpus.py` (implement stage) catches a case of
  `todo-tasks-refused.json` refused with a code other than the one the file states.
- `frontend/src/contexts/todo_list/lib/todoTask.test.ts` (implement stage) catches the browser's
  verdict drifting from the corpus the service is held to.

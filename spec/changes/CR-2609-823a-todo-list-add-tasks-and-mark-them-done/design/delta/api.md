# Delta fragment — `design-api`

*The contract half of the to-do list, in its two documents: the prose in `spec/design/api.md`,
which freezes at the end of this stage and which the backend and the frontend build against
without talking, and the machine-comparable half in `contracts/openapi/todo_list.yaml`, which
`./scripts/contracts.sh` holds the running application to from now on. Neither is generated
from the other; they say the same thing and the traceability table below is how to check it.*

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

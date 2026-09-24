# API contract

The shapes on the wire. The rules behind them are in the document of the context that answers
each route — [`spec/contexts/guestbook.md`](../contexts/guestbook.md) and
[`spec/contexts/todo_list.md`](../contexts/todo_list.md); the columns in
[`data-model.md`](data-model.md). This document never explains a rule — it states a field, a
code and a sentence.

**The contract is the authority and the code is validated against it** — constitution,
article VI, settled in [`contracts/README.md`](../../contracts/README.md). The shapes in a form
a machine can compare against the running application stand in `contracts/openapi/`: written
by hand, committed, versioned by `info.version`. This document says the same thing in prose —
field, code and sentence — and the two are to agree.

The Pydantic dump (`openapi.json`) is an **artefact, not a source**: gitignored, rebuilt on
every run and compared against the contract by `./scripts/contracts.sh`.
`frontend/src/api/schema.d.ts` is generated from it and committed. **Neither of those two files
is edited by hand** — `./scripts/generate.sh` recreates them and CI compares.

The opposite sentence stood here until 2026-09-02: "one source of truth about shapes: the
Pydantic schemas". It contradicted article VI, which stands above this document in the
hierarchy of article VIII, and because of that contradiction the `404` described below in
§ Refusals existed in no generated artefact — the routers raised it without declaring
`responses=`.

## Conventions

- **The `/api` prefix is applied in one place** — `app/api.py` — and nowhere else.
  A router registered outside the aggregate lands outside the prefix and is swallowed by the
  SPA catch-all, which answers `index.html` with status 200. The symptom is not a 404 but a
  frontend breaking on `JSON.parse("<!doctype ...")`.
- **Paths and identifiers are in English**, as is everything else in this repository
  ([`conventions.md`](conventions.md) § Language).
- **An identifier in a path is a UUID** ([`data-model.md`](data-model.md) § Identifiers). A
  value that is not a UUID gets a `422`, not a `404`: "this is not an identifier" and "there is
  no such entry" are different facts, and only the first is fixed by correcting the request.
- **Moments are ISO-8601 with an offset.** The column is `timestamptz`, so the zone is part of
  the value rather than of the formatting — the list's order rests on this (`BR-04`), and it
  has to settle correctly across an offset change too.
- **There is no authentication.** No route requires a session and none returns `401` or `403`.
  This is a named non-goal, not an oversight — [`guestbook.md`](../contexts/guestbook.md)
  § Deliberate non-goals.

## Routes and their contexts

Which bounded context answers each route. The context is declared in
[`../contexts/`](../contexts/), not here — this column cites it, and
`tests/fitness/test_context_declarations.py` holds the citation to a context that
exists. A route answered by no context is the Platform slice
([`architecture.md`](architecture.md) § Platform), which owns no domain rules.

| Route | Methods | Context | Session |
|---|---|---|---|
| `/api/health` | `GET` | — | no |
| `/api/guestbook-entries` | `GET` (with `q`, `sort`, `limit`, `offset`), `POST` | `guestbook` | no |
| `/api/guestbook-entries/{entry_id}` | `GET`, `PATCH`, `DELETE` | `guestbook` | no |
| `/api/todo-tasks` | `GET`, `POST` | `todo_list` | no |
| `/api/todo-tasks/{todo_task_id}` | `PATCH`, `DELETE` | `todo_list` | no |

Rejected (decision of 2026-09-07, `cr: historical` — the column and its heading were renamed
from "Module" to "Context", and a register naming a thing is a rule about that thing's name;
specification-shape changes are made on the trunk and carry no `delta.md`):

- **Keep "Module".** The system has one word for this and it is *bounded context* — it is what
  `spec/contexts/` is called, what `spec/glossary.md` defines and what the front matter
  declares. A second word for one concept is the homograph ISO 10241-1 exists to forbid, and it
  costs a reader the question "is a module the same thing as a context" every time.
- **Call the section "Context map".** In DDD that names the map of relationships *between*
  contexts, which this table is not — it maps a route to the context that answers it. Reusing
  the term would put a second meaning on a word this repository has just given one meaning to.
- **Drop the column and let `spec/contexts/` be the only home.** It is the stricter reading of
  "one fact, one home", and it takes something away: the register is what somebody reads when
  they hold a route and want to know whose rules apply. The column stays as a **citation**, and
  `tests/fitness/test_context_declarations.py` is what makes it a link rather than a repetition.

## Shapes

### `GuestbookEntryRead` — the response

| Field | Type | Notes |
|---|---|---|
| `id` | `uuid` | issued by the application at write time |
| `author` | `string` | trimmed of whitespace |
| `message` | `string` | trimmed of whitespace |
| `created_at` | `date-time` | the moment of writing; never changes (`BR-02`) |
| `updated_at` | `date-time` | the moment of last amendment; equal to `created_at` on an entry never amended |

### `GuestbookEntryCreate` — the `POST` body

| Field | Type | Required | Bounds |
|---|---|---|---|
| `author` | `string` | yes | 1–80 **code points**, after normalizing and trimming |
| `message` | `string` | yes | 1–1000 **code points**, after normalizing and trimming |

### `GuestbookEntryPage` — the collection `GET` response

| Field | Type | Notes |
|---|---|---|
| `items` | `GuestbookEntryRead[]` | this piece, in `sort` order |
| `total` | `integer` | how many entries match `q`; **the whole population, not the length of `items`** |
| `total_all` | `integer` | how many entries the guestbook has; `q` does not affect it |

An envelope rather than a bare array, and that is the only reason it exists: **a piece cannot
say how many it came from**. The screen shows both numbers at once — the heading speaks about
the guestbook, the sentence under the search bar about the result — and deriving either from
`items.length` gives a number that looks plausible and is therefore unnoticeably wrong.

Without `q` both numbers are equal and the service counts once.

### `GuestbookEntryUpdate` — the `PATCH` body

| Field | Type | Required | Bounds |
|---|---|---|---|
| `author` | `string` | no | 1–80 code points, after normalizing and trimming |
| `message` | `string` | no | 1–1000 code points, after normalizing and trimming |

**An absent field means "do not touch", never "clear".** A field present and empty is a
refusal: "clear the message" is not an operation an entry supports (`BR-01`).

A body that sets **no** field is rejected — see § Refusals. The shape is valid, the refusal is
about the request, and that is why it lives beside the endpoint rather than in the schema.

### `TodoTaskRead` — the response

| Field | Type | Notes |
|---|---|---|
| `id` | `uuid` | issued by the application at write time |
| `text` | `string` | the task's one line as stored: normalized and trimmed, 1–200 code points, no line break inside (`BR-06`, `BR-07`) |
| `done` | `boolean` | `true` is done, `false` is not done; `false` on every new task (`BR-08`), and changed only by a `PATCH` that carries `done` (`BR-09`) |
| `created_at` | `date-time` | the moment of adding; set once and never changed — not by a marking, not by a correction (`BR-08`). The list is ordered by it (`BR-11`) |

A task has these four and nothing else: no `updated_at`, no author, no position
([`../contexts/todo_list.md`](../contexts/todo_list.md) § Language). `created_at` is on the wire
although no screen shows it, because two promises are made about it — the order, and that it
never moves — and a promise about a value nobody can read is a promise nobody can check.

### `TodoTaskList` — the collection `GET` response

| Field | Type | Notes |
|---|---|---|
| `items` | `TodoTaskRead[]` | every stored task, done and not done alike, in the list's order (§ Endpoints) |
| `total` | `integer` | how many tasks the list holds; equal to the length of `items`, because the list is read whole (`BR-11`) |

An envelope rather than a bare array although the list has no pieces. A caller that needs only
to know whether the list is empty — the filling of a new environment is one — reads `total`;
and the day the list is read in pieces, `items` shortens and `total` keeps its meaning, which a
bare array could only achieve by breaking every caller.

### `TodoTaskCreate` — the `POST` body

| Field | Type | Required | Bounds |
|---|---|---|---|
| `text` | `string` | yes | 1–200 **code points** and one line, after normalizing and trimming (`BR-06`, `BR-07`) |

**There is no `done` in this shape.** A task is born not done (`BR-08`). A `done` sent anyway is
ignored like every key the shape does not have — keys it does not have are ignored, never
refused — and the task is stored not done, with a `201`: the request asked for a task and it
gets one.

**The bounds are refusals with a code, not schema constraints.** A text outside them is refused
with one of the three `todo_task_text_*` codes of § Refusals, never with FastAPI's list of
`{loc, msg, type}`. The person has to be told which of three reasons applies, and when a text
breaks two rules the one-line reason is the one given (`BR-07`) — a length constraint in the
schema answers before anything else can look at the text, so it would call "too long" a text
whose trouble is a line break, and it would name the reason with a type string this contract
does not own. The published schema therefore carries `text` as a required `string` with no
`minLength` or `maxLength`; the bounds are stated here, in § Refusals and under `x-refusals` in
`contracts/openapi/todo_list.yaml`.

A body without `text`, or with a `text` that is not a string (`null`, a number), is a malformed
request rather than a text anybody typed, and gets the standing validation `422` (§ Refusals).

### `TodoTaskUpdate` — the `PATCH` body

| Field | Type | Required | Bounds |
|---|---|---|---|
| `text` | `string` | no | as in `TodoTaskCreate`, with the same three refusals (`BR-10`) |
| `done` | `boolean` | no | `true` marks the task done, `false` marks it not done — the state chosen, whatever is stored (`BR-09`). A JSON `true` or `false` and nothing that merely reads as one: `"true"` or `1` gets the standing validation `422` |

**An absent field means "do not touch".** A field sent as `null` reads as absent. A correction
sends `text` alone and a marking sends `done` alone; a body carrying both applies both in one
write, and a refused `text` writes nothing, `done` included. A body that sets neither is
refused — see § Refusals.

**A `PATCH` writes the fields it carries and no other.** A field absent from the body is never
written — not even back with the value the server read — so a correction and a marking of one
task sent at the same moment are both kept, and of two changes to the same field the one
applied later wins (`BR-10`). There is no version, no `ETag` and no `If-Match`, and no change is
refused for resting on an older reading: the later change wins, and nobody is told
([`../contexts/todo_list.md`](../contexts/todo_list.md) § Deliberate non-goals). How the store
holds this is [`data-model.md`](data-model.md)'s.

## Collection read parameters

`GET /api/guestbook-entries` takes four query parameters, all optional. FastAPI holds the
bounds, so a value outside them is an ordinary Pydantic `422` — with no separate refusal code.

| Parameter | Type | Default | Bounds | Meaning |
|---|---|---|---|---|
| `q` | `string` | none | ≤ 200 code points, after normalizing and trimming | narrow to entries containing this phrase — in the signature **or** in the message, regardless of case |
| `sort` | `newest` \| `oldest` | `newest` | a closed set | which end of the guestbook to read from (`BR-04`) |
| `limit` | `integer` | 20 | 1–100 | how many entries in this piece |
| `offset` | `integer` | 0 | ≥ 0 | which entry to start from |

**A value outside the set is a refusal, not a silent fall back to the default.** A client that
got `sort` wrong would get newest first while its screen said otherwise — and nothing anywhere
would say so.

**The phrase is trimmed before it is measured**, exactly as an entry's values are (`BR-01`): a
phrase of nothing but spaces is not a phrase — including a phrase of more spaces than the bound
allows, which is no phrase and not a refusal. That sentence was here before the code obeyed it:
the bound lived on the raw query string while an entry's bounds lived after the trim, so two
hundred and five spaces earned a `422` and two hundred and five spaces in a signature was
simply empty. One document, two orders, and a caller met the undocumented one.

The characters `%` and `_` are matched literally — without that a guest searching for `100%`
would hit the whole guestbook, silently and looking like a successful search.

**Every bound in this document is in CODE POINTS, and a value is normalized to Unicode NFC
and trimmed of a written 30-code-point set before it is counted.** The unit is stated because
it is the thing the two sides of this contract once disagreed about while both reading the
same number: JSON Schema's `maxLength` is code points, a Postgres `varchar(n)` is code points,
Pydantic counts code points — and the browser's `String.prototype.length` counts UTF-16 code
units, so a signature of 41 emoji was 41 to the server and 82 to the screen. A bound published
without its unit is a bound each reader completes for itself. The set, and why it is a union
of what the two languages removed by default, is in `app/platform/schemas/text.py`;
[`../contexts/guestbook.md`](../contexts/guestbook.md) § `BR-01` carries the rule.

Rejected (decision of 2026-09-17, `cr: historical` — the unit was published here and the
phrase's bound was moved behind its trim, on GitHub issue #28, outside `/forge:sdd`):

- **State the unit only in the context document and leave this register saying "characters".**
  This register is what an independent client builds against; a bound published without its unit
  is a bound each reader completes for itself, which is precisely how one of this system's own
  four layers came to complete it differently.
- **Freeze `q`'s `maxLength` in `contracts/openapi/guestbook.yaml` while touching it.** Rejected
  against a standing decision recorded in that file: the read parameters' bounds are numbers this
  register owns, not a set a caller can enumerate, and `sort` is frozen there because its set is
  closed. Nothing about this change made that argument weaker.
- **Change this document to match the code instead — measure the phrase before trimming it.** The
  document was the correct half. A bound applied to the raw query string refuses a phrase that is
  empty once trimmed, so a guest who held down the space bar got a `422` where a guest who did the
  same in a signature got "this is empty".

**Case folding is Unicode**, because that is what Postgres does — and Postgres is this
application's only engine ([`architecture.md`](architecture.md) § One engine). `Å` finds `å`,
and that is a plain sentence rather than a conditional one: while there was a second engine it
cost one marker and one explanation in the service code.

## Endpoints

| Method | Path | Success | Response | Cardinality |
|---|---|---|---|---|
| `GET` | `/api/guestbook-entries` | `200` | `GuestbookEntryPage` | 0..`limit` entries in an envelope, in `sort` order (`BR-04`) |
| `POST` | `/api/guestbook-entries` | `201` | `GuestbookEntryRead` | exactly 1 |
| `GET` | `/api/guestbook-entries/{entry_id}` | `200` | `GuestbookEntryRead` | exactly 1 |
| `PATCH` | `/api/guestbook-entries/{entry_id}` | `200` | `GuestbookEntryRead` | exactly 1 |
| `DELETE` | `/api/guestbook-entries/{entry_id}` | `204` | no body | — |
| `GET` | `/api/todo-tasks` | `200` | `TodoTaskList` | every stored task, 0..n, with no ceiling and no pieces (`BR-11`) |
| `POST` | `/api/todo-tasks` | `201` | `TodoTaskRead` | exactly 1, not done (`BR-08`) |
| `PATCH` | `/api/todo-tasks/{todo_task_id}` | `200` | `TodoTaskRead` | exactly 1, as stored once this change is applied |
| `DELETE` | `/api/todo-tasks/{todo_task_id}` | `204` | no body | — |

**An empty guestbook is a `200` with an empty `items`, never a `404`.** "There are no entries"
is a successful answer to "list the entries"; a `404` would make an empty guestbook
indistinguishable from a broken route. A search that found nothing has the same form — and then
`total` is zero while `total_all` is not, which is the only way the screen tells those two
sentences apart.

### The to-do list's endpoints

**The collection `GET` takes no parameters and answers with the whole list.** There is nothing to
narrow, one direction to read in and no pieces (`BR-11`) — so no `q`, `sort`, `limit` or
`offset`. A query parameter it does not take is ignored, and the answer is still every task.

**The order is the answer's.** `items` come newest `created_at` first, and a tie on `created_at`
is settled by `id` in the same direction, so the order is total (`BR-11`). A client shows
`items` in the order they arrive and sorts nothing again. Marking and correcting never move a
task, because neither touches `created_at`.

**An empty list is a `200` with an empty `items` and a `total` of zero, never a `404`** — for the
reason given for the guestbook above.

**There is no read of one task.** No requirement reads a task on its own: the screen reads the
list, and so does the filling of a new environment, which adds its example tasks with `POST`
and marks the done one with `PATCH` — no door exists for it that a person does not have.

**The same text twice is two tasks.** `POST` never refuses a text for matching another task's:
there is no duplicate refusal and never a `409` (`BR-12`).

**`PATCH` and `DELETE` never create a task.** An identifier no task has answers `404` and writes
nothing — a marking, a correction and a second deletion alike (`BR-13`).

## Refusals

Every refusal carries a **stable code** and a **finished sentence**. The code is a contract the
screen branches on, and it never changes. The sentence is product text and may be reworded.

The sentence lives **beside the endpoint that produced it** —
`app/contexts/guestbook/routers/guestbook_entries.py` — rather than in a shared table one edit away from telling
somebody the wrong field to correct (`spec/design/conventions.md` § Layers).

| Code | Status | When | Sentence |
|---|---|---|---|
| `guestbook_entry_not_found` | `404` | the identifier is valid, the entry is not there — also on a second deletion of the same entry (`BR-03`) | "There is no such entry. Somebody else may have deleted it." |
| `guestbook_entry_empty_patch` | `422` | `PATCH` sets no field | "No field was given to change. The entry is unchanged." |

Both sentences are copied here from `app/contexts/guestbook/routers/guestbook_entries.py` verbatim. A sentence
changed there and not here is exactly the divergence this document exists to prevent.

Validation refusals (`422`) from an empty or over-long `author`/`message`, from a wrong type, or
from an unreadable identifier in the path are produced by Pydantic and carry FastAPI's standard
shape — a list of `{loc, msg, type}` in `detail`. The frontend normalises both shapes in
`frontend/src/api/problem.ts`; **that normalisation is the only place** where four shapes of
backend error become one.

**The published document says so too, and that is not a restatement of this paragraph.** `PATCH
/api/guestbook-entries/{entry_id}` is the one operation that can answer `422` with either shape,
and it declares both: an `anyOf` over `Refusal` and `HTTPValidationError`, frozen in
`contracts/openapi/guestbook.yaml` from version `1.2.0` and generated into
`frontend/src/api/schema.d.ts`. It used to declare `Refusal` alone — which was the *rarer* of the
two, and which additionally suppressed the `HTTPValidationError` FastAPI adds by default, so the
shape a caller meets most often could not be described by a type at all. A status code with two
shapes is stated as two, or it is not stated.

Nothing compares a body against that declaration by reading two documents;
`tests/integration/test_guestbook_entries_contract.py` does it by sending the request and
validating what came back against the schema published for the status code that came back.

Rejected (decision of 2026-09-16, `cr: historical` — how a status code carrying two shapes is
published is a rule about this contract and every one after it, so it lives here; the repair was
made on the trunk and carries no `delta.md`):

- **Leave the `422` declared as `Refusal` alone.** It is what the router already said, and the
  bodies on the wire are correct either way, so nothing a user can see is wrong. What is wrong is
  the generated type: it describes one in six of the responses and, because an explicit `422`
  suppresses the one FastAPI generates, it leaves the other five describable by nothing at all. A
  contract that is silent about a shape is better than a contract that names the wrong one.
- **Unify the two bodies into one error shape (RFC 9457 `problem+json`).** This is the stated
  destination of `frontend/src/api/problem.ts`, and it is the right end state: one shape means no
  union to publish and no discrimination to write. It also changes every `422` body, which under
  the BACKWARD mode `contracts/openapi/README.md` declares is a breaking change and a major
  version — plus `problem.ts`, the e2e steps and every assertion on `detail`. That is a design
  change with its own requirements, not a repair to a document that describes the wrong thing.
- **Make the router raise a coded refusal for the Pydantic cases too**, so `Refusal` becomes true.
  It would mean re-validating each field by hand before Pydantic sees it, in the router, which is
  precisely where `spec/design/conventions.md` § Layers says a bound does not belong — and it
  would mint five refusal codes whose only reason to exist is to make an over-narrow declaration
  come true.
- **Teach `scripts/openapi_contract.py` to demand `content` on every declared response.** It is
  the gate that let this through, so it looks like the place to fix it. Its subset design is
  argued in its own docstring and the full comparison was rejected there with a measured reason;
  and it would still not have caught this, because it reads two documents and never sends a
  request. The missing capability is a test on real responses, which is what was added.

The body of a refusal with a code has the shape:

```json
{ "detail": { "code": "guestbook_entry_not_found", "message": "…", "id": "…" } }
```

### The to-do list's refusals

**Every refusal about a task carries a code and a sentence, the three about its text included**
— unlike the guestbook, whose empty and over-long fields answer with FastAPI's list (above).
The reason is in § Shapes, `TodoTaskCreate`. The sentences live beside the to-do list's
endpoints, in its router module, exactly as written here; a sentence reworded there and not
here is the divergence this document exists to prevent. `id` is present only on the refusal
that is about one identified task.

| Code | Status | When | `id` | Sentence |
|---|---|---|---|---|
| `todo_task_not_found` | `404` | the identifier is valid and no task has it — on a marking, a correction, and a second deletion of the same task (`BR-13`) | the identifier from the path | "This task no longer exists. Somebody may have deleted it, and nothing was changed." |
| `todo_task_empty_patch` | `422` | a `PATCH` sets neither `text` nor `done` | absent | "No change was given. The task is unchanged." |
| `todo_task_text_empty` | `422` | `text` is empty once normalized and trimmed, on `POST` and on `PATCH` (`BR-06`) | absent | "A task needs text. Type what there is to do." |
| `todo_task_text_multiline` | `422` | `text`, once trimmed, still holds a line break — also when it is longer than 200 code points (`BR-07`) | absent | "A task is one line, and this text has a line break inside it, which may not be visible. Remove the line break and try again." |
| `todo_task_text_too_long` | `422` | `text` is one line and longer than 200 code points once normalized and trimmed (`BR-06`) | absent | "A task can be at most 200 characters. Shorten it and try again." |

The last sentence says "characters" because that is the word a person uses; the rule counts code
points, and so does every bound in this document (§ Collection read parameters).

**One refusal per request, decided in this order:**

1. An identifier that is not a UUID, or a body of the wrong shape — no `text` on a `POST`, a
   `text` that is not a string, a `done` that is not a boolean — gets the standing validation
   `422`, FastAPI's list, before anything below is asked.
2. `todo_task_empty_patch`.
3. `todo_task_text_empty`, then `todo_task_text_multiline`, then `todo_task_text_too_long`. An
   empty text cannot hold a line break, since every line break is trimmed from the ends, and a
   text with a line break inside is never refused as too long (`BR-07`) — so a text earns
   exactly one of the three.
4. Only then is the task looked up, and `todo_task_not_found` is the last answer: a request
   that could never succeed is refused for what it is, whatever its identifier names.

**A refusal stores nothing, and only a `2xx` answer reports a change as made.** Every operation
touches one task, so a refused request leaves the list exactly as it found it.

**`422` has two shapes on `POST` and on `PATCH`, and both are published** — an `anyOf` over
`Refusal` and `HTTPValidationError`, the rule this section set for the guestbook's `PATCH`.
`DELETE` has no coded `422`; its only one is FastAPI's own for an unreadable identifier, and it
is not declared.

```json
{ "detail": { "code": "todo_task_text_multiline", "message": "A task is one line, and …" } }
```

## After a contract change

```bash
./scripts/generate.sh
```

Commit what it changed. `openapi.json` is gitignored — an intermediate artefact sets in git —
and `schema.d.ts` is committed, regenerated by CI and compared.

**First, though, the contract changes**, because the contract is the authority:

```bash
./scripts/contracts.sh
```

It compares `contracts/openapi/` against the application and goes red on a difference. A
divergence is closed on **one** side — either the contract was wrong and its `info.version`
rises, or the code was wrong and the context's `schemas/` or `routers/` changes. Never by copying the
dump into the contract: the `contracts` gate refuses a file with a generator banner.


## The gates were renamed

Every gate this document names is called after what it checks — `traceability`,
`e2e-scenario`, `english`. They were numbered `G1` to `G20` until 2026-09-06.

Rejected (decision of 2026-09-06, `cr: historical` — the naming rule and the rejected
alternatives live in one place, and this is a pointer to it rather than a second copy;
framework changes are made on the trunk and carry no `delta.md`): recording the argument again
here. See [`conventions.md`](conventions.md) § A gate is named, not numbered, and
[the process's `spec_gates.py`](https://github.com/Scalo-Sales-Engineering-Consulting/claude-marketplace/blob/main/plugins/forge/skills/_shared/sdd/spec_gates.py), where every gate declares the numeric
code it carried, for the mapping from every retired code.

## The manual this document cites has moved

The reference tables it points at travel with the process now — the gate register with its retired codes is [the process's `spec_gates.py`](https://github.com/Scalo-Sales-Engineering-Consulting/claude-marketplace/blob/main/plugins/forge/skills/_shared/sdd/spec_gates.py) — and not in `docs/`. `docs/` holds
the documentation of the **system** — setting up the AWS account, deploying, configuring,
operating it — and the manual for the **change process** moved beside the framework it
describes.

Rejected (decision of 2026-09-10, `cr: historical` — the forge plugin deleted its `docs/` tree
on 2026-09-10 and kept only what the process runs on, so `sdd-reference.md` and its table of
old numeric codes exist nowhere; the mapping from a retired code to a gate's name lives in the
gate register itself, `spec_gates.py`, where every gate declares the code it carried, and the
links here name that. Framework changes are made on the trunk and carry no `delta.md`): leaving
links that return 404, or copying the mapping into this document — the second home this section
argues against.

Rejected (decision of 2026-09-09, `cr: historical` — the change process left this repository
on 2026-09-09 for a plugin, `forge@scalo`, so the relative link this section used
named a path under the process's old home here, which exists in no clone of this template;
a link that 404s in a document about where facts live is worse than no link. It is now the URL
of the document in the repository that ships it. Framework changes are made on the trunk and
carry no `delta.md`): keeping a relative path and vendoring a copy of the reference here. That
would put the manual's tables in two repositories, which is the second home this whole document
exists to argue against.

Rejected (decision of 2026-09-06, `cr: historical` — the rule and its rejected alternatives
live in one place, and this is a pointer to it rather than a second copy; framework changes are
made on the trunk and carry no `delta.md`): recording the argument again here. See
[`conventions.md`](conventions.md) § Documentation — where a document goes.

Rejected (decision of 2026-09-10, `cr: historical` — the marketplace that ships the
process moved organisation and is named `scalo` there. Every absolute link in this
document still pointed into the organisation this repository was forked out of, so the plugin
it names installed from a marketplace this template's readers may have no access to at all.
Framework changes are made on the trunk and carry no `delta.md`): leaving the old URLs because
the repository they name still resolves for whoever happens to have access to it. A citation
whose permission depends on which organisation the reader belongs to is the same failure as the
relative path the block above rejects — it works for the author and 404s for the team.

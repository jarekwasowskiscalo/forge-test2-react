"""To-do task request and response shapes -- the four `spec/design/api.md` § Shapes names.

Read and write shapes are separate classes, per `spec/design/conventions.md`, so a
response that grows a field never silently starts accepting it on a request. These
models import only from `pydantic`: no coupling to FastAPI, to routers, or to the
model beside them.

**The request shapes hold no part of the text rule, and importing none of it is how
that is kept** (`spec/design/conventions.md` § Layers; the user's words in
`CR-2609-823a`, `Q-21`: "The request formats import no part of the text rule; the
service does."). A task's text is refused with one of three CODED reasons --
empty, more than one line, too long -- and when a text breaks two rules the one-line
reason wins (`BR-07`). A `min_length`, `max_length`, pattern or validator here would
answer before the service could look, with FastAPI's list of `{loc, msg, type}` and
no code, and would call "too long" a text whose trouble is a line break. So `text` is
a plain string, published with no bound, and kept **exactly as it was sent**: not
even normalized, because normalizing is the first step of the judgement and the
judgement is the service's (`app/contexts/todo_list/services/todo_tasks.py`).
`tests/unit/test_todo_task_text_rules.py` builds both shapes from every case of the
corpus, the refused ones included, and holds them to that.

**Strict types, and only for what is malformed.** `StrictStr` and `StrictBool`
refuse a `text` of `42` and a `done` of `"true"` or `1` with the standing validation
`422`: those are not texts anybody typed or choices anybody made, they are requests
of the wrong shape (`spec/design/api.md` § The to-do list's refusals, step 1).
Pydantic's lax mode would read `"true"` and `1` as `True` and mark a task done on a
value that merely resembles a choice. Strictness constrains the TYPE and publishes
no `minLength`, `maxLength` or `pattern`, so the contract's bare `string` holds.
"""

import datetime
import uuid

from pydantic import BaseModel, Field, StrictBool, StrictStr


class TodoTaskCreate(BaseModel):
    """Request contract for `POST /api/todo-tasks`.

    **There is no `done` here**, and that is `BR-08` rather than an omission: a task
    is born not done. A `done` sent anyway is ignored like every key this shape does
    not have -- Pydantic's default `extra="ignore"` -- and the task is stored not done
    with a `201`, because the request asked for a task and gets one.
    """

    #: Required, a string, and nothing more: the bounds are the service's coded
    #: refusals, never a constraint here (module docstring).
    text: StrictStr


class TodoTaskUpdate(BaseModel):
    """Request contract for `PATCH /api/todo-tasks/{todo_task_id}`.

    Both fields optional, and an absent field means "do not touch", never "clear". A
    field sent as `null` reads as absent -- it lands on the same `None` -- so a body of
    two nulls is the same request as `{}`. A body that sets neither is refused by the
    router, not here: "no change given" is a fact about the request as a whole, and it
    is decided beside the endpoint before the service is called (`Q-21`, item 3).

    A correction carries `text` alone, a marking `done` alone, and a body carrying
    both is one change applied in one statement -- or refused whole, when its text is.
    """

    #: As in `TodoTaskCreate`: no bound, kept as sent, judged by the service.
    text: StrictStr | None = None
    #: The state the person chose -- `true` done, `false` not done -- written as
    #: chosen whatever is stored (`BR-09`). A JSON boolean and nothing that merely
    #: reads as one.
    done: StrictBool | None = None


class TodoTaskRead(BaseModel):
    """Response contract for one task: these four fields and nothing else.

    No `updated_at`, no author, no position (`spec/contexts/todo_list.md`
    § Language). `created_at` is on the wire although no screen shows it, because two
    promises are made about it -- the order, and that it never moves -- and a promise
    about a value nobody can read is a promise nobody can check.
    """

    id: uuid.UUID
    #: As stored: normalized, trimmed, one line, 1 to 200 code points.
    text: str
    done: bool
    #: The moment of adding, with its offset; set once and never moved (`BR-08`).
    created_at: datetime.datetime


class TodoTaskList(BaseModel):
    """Response contract for `GET /api/todo-tasks`: the whole list and its count.

    An envelope rather than a bare array although the list has no pieces. A caller
    that needs only to know whether the list is empty -- the filling of a new
    environment is one -- reads `total`; and the day the list is read in pieces,
    `items` shortens and `total` keeps its meaning, which a bare array could only
    achieve by breaking every caller.
    """

    #: Every stored task, done and not done alike, newest `created_at` first, a tie
    #: settled by `id` in the same direction (`BR-11`).
    items: list[TodoTaskRead]
    #: How many tasks the list holds. Equal to `len(items)` because the list is read
    #: whole (`BR-11`) -- the one envelope in this API where that is true.
    total: int = Field(ge=0)

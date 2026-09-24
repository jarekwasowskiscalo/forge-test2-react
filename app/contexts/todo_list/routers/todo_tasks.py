"""To-do tasks -- the HTTP binding of the to-do list.

Mounted at `/api/todo-tasks` by `app/api.py`, the one place the prefix is applied.
HTTP binding and nothing else: it reads the path and the body, calls
`app.contexts.todo_list.services.todo_tasks`, and translates that module's domain
exceptions into coded refusals in an explicit `match`. No rule about a task is
decided here (`spec/design/conventions.md` § Layers) -- with the one exception the
conventions name: a `PATCH` that sets neither field is a refusal about the request as
a whole, answered beside the endpoint before the service is called, exactly as the
guestbook's router answers its empty patch (`CR-2609-823a`, `Q-21`, item 3).

**Every refusal carries a stable code and a finished English sentence, the three
about a task's text included** -- unlike the guestbook, whose empty and over-long
fields answer with FastAPI's list. The code is what the screen branches on and never
changes; the sentence is what a person reads. The sentences below are the ones
`spec/design/api.md` § The to-do list's refusals publishes, written here exactly as
written there: a sentence reworded here and not there is the divergence that register
exists to prevent. The codes are string literals because `./scripts/contracts.sh`
looks for each code of `contracts/openapi/todo_list.yaml`'s `x-refusals` as a literal
in a `routers/` module.

**One refusal per request, in the contract's order**, and the order falls out of where
each question is asked rather than out of code that sequences it: a body of the wrong
shape or an identifier that is not a UUID is FastAPI's `422` before this module runs;
the empty patch is asked here, first; the text is judged by the service before it
writes; and "no such task" is what the write itself answers, so it is always last.

The service is imported as a module rather than name by name: its operations and this
module's handlers answer to the same words -- a handler is the operation bound to a
route -- and `service.delete_todo_task` reads as what it is.
"""

import uuid
from typing import Any, Final, assert_never

from fastapi import APIRouter, HTTPException

from app.contexts.todo_list.schemas.todo_tasks import (
    TodoTaskCreate,
    TodoTaskList,
    TodoTaskRead,
    TodoTaskUpdate,
)
from app.contexts.todo_list.services import todo_tasks as service
from app.platform.schemas.refusals import Refusal

router = APIRouter()

#: The sentence of `todo_task_not_found`: the identifier is valid and no task has it --
#: a marking, a correction, a second deletion (`BR-13`).
_NOT_FOUND: Final = (
    "This task no longer exists. Somebody may have deleted it, and nothing was changed."
)

#: The sentence of `todo_task_empty_patch`: a `PATCH` that sets neither field is a
#: request that cannot be carried out rather than one that succeeds by doing nothing.
_EMPTY_PATCH: Final = "No change was given. The task is unchanged."

#: The sentences of the three refusals of a task's text (`BR-06`, `BR-07`). The last
#: says "characters" because that is the word a person uses; the rule counts code
#: points, and so does every bound in `spec/design/api.md`.
_TEXT_EMPTY: Final = "A task needs text. Type what there is to do."
_TEXT_MULTILINE: Final = (
    "A task is one line, and this text has a line break inside it, which may not be "
    "visible. Remove the line break and try again."
)
_TEXT_TOO_LONG: Final = "A task can be at most 200 characters. Shorten it and try again."

#: What `PATCH` and `DELETE` answer when the identifier resolves to no task.
#:
#: Declared rather than merely raised: FastAPI builds `openapi.json` from the
#: decorator, never from the body of a raised exception, so a `404` raised without
#: this reaches neither the published document nor `frontend/src/api/schema.d.ts`.
_NOT_FOUND_RESPONSE: Final[dict[int | str, dict[str, Any]]] = {
    404: {"model": Refusal, "description": "No task has that identifier."}
}

#: The `422` on `POST` and `PATCH`, which is genuinely two shapes and is published as two
#: (`spec/design/api.md` § Refusals, the rule set for the guestbook's `PATCH`).
#:
#: A coded `Refusal` for a text the rules refuse or a patch that sets nothing, and
#: FastAPI's `HTTPValidationError` for a body of the wrong shape or an identifier that
#: is not a UUID. Declaring `Refusal` alone would describe half the answers and, since
#: an explicit `422` REPLACES the one FastAPI generates, leave the other half
#: describable by nothing in the generated types. Raw `$ref`s, because
#: `HTTPValidationError` is not an importable model -- FastAPI injects it into
#: `components/schemas` itself -- and because this form keeps the component names the
#: generated types already know.
#:
#: A copy of the guestbook router's declaration rather than an import of it: a context
#: never imports another context's internals (`tests/fitness/test_context_boundaries.py`),
#: and the guestbook is an example deleted as a unit, which must not take this with it.
_EITHER_REFUSAL_OR_VALIDATION: Final[dict[str, Any]] = {
    "description": "A coded refusal -- a text the rules refuse, or a patch that sets no "
    "field -- or FastAPI's validation error for a request of the wrong shape.",
    "content": {
        "application/json": {
            "schema": {
                "anyOf": [
                    {"$ref": "#/components/schemas/Refusal"},
                    {"$ref": "#/components/schemas/HTTPValidationError"},
                ]
            }
        }
    },
}

#: The domain exceptions a text can earn, and the four the router ever translates.
_TextRefused = (
    service.TodoTaskTextEmptyError
    | service.TodoTaskTextMultilineError
    | service.TodoTaskTextTooLongError
)
_Refused = service.TodoTaskNotFoundError | _TextRefused


def _unprocessable(code: str, message: str) -> HTTPException:
    """A coded `422` about the request or its text: no `id`, because it names no task."""
    return HTTPException(status_code=422, detail={"code": code, "message": message})


def _refusal(error: _Refused) -> HTTPException:
    """The coded refusal for each domain exception the service raises -- explicitly.

    A `match` over the classes rather than a lookup table, so a fifth exception added
    to the service without a branch here is a type error (`assert_never`) instead of an
    unhandled `500`.
    """
    match error:
        case service.TodoTaskNotFoundError(todo_task_id=missing):
            return HTTPException(
                status_code=404,
                detail={"code": "todo_task_not_found", "message": _NOT_FOUND, "id": str(missing)},
            )
        case service.TodoTaskTextEmptyError():
            return _unprocessable("todo_task_text_empty", _TEXT_EMPTY)
        case service.TodoTaskTextMultilineError():
            return _unprocessable("todo_task_text_multiline", _TEXT_MULTILINE)
        case service.TodoTaskTextTooLongError():
            return _unprocessable("todo_task_text_too_long", _TEXT_TOO_LONG)
        case _:
            assert_never(error)


@router.get("/todo-tasks", response_model=TodoTaskList)
def list_todo_tasks() -> TodoTaskList:
    """The whole list, newest first, and how many tasks it holds.

    No parameters -- nothing to narrow, one direction, no pieces (`BR-11`) -- so a
    query parameter this does not take is ignored and the answer is still every task.
    An empty list is a `200` with an empty `items`, never a `404`.
    """
    return service.list_todo_tasks()


@router.post(
    "/todo-tasks",
    response_model=TodoTaskRead,
    status_code=201,
    responses={422: _EITHER_REFUSAL_OR_VALIDATION},
)
def add_todo_task(data: TodoTaskCreate) -> TodoTaskRead:
    """Add a task, not done. A `done` in the body is ignored, never refused (`BR-08`).

    Raises:
        HTTPException: 422 with `todo_task_text_empty`, `todo_task_text_multiline` or
            `todo_task_text_too_long` when the text is refused.
    """
    try:
        return service.add_todo_task(text=data.text)
    except (
        service.TodoTaskTextEmptyError,
        service.TodoTaskTextMultilineError,
        service.TodoTaskTextTooLongError,
    ) as error:
        raise _refusal(error) from error


@router.patch(
    "/todo-tasks/{todo_task_id}",
    response_model=TodoTaskRead,
    responses={**_NOT_FOUND_RESPONSE, 422: _EITHER_REFUSAL_OR_VALIDATION},
)
def change_todo_task(todo_task_id: uuid.UUID, data: TodoTaskUpdate) -> TodoTaskRead:
    """Mark a task, correct its text, or both -- writing the fields the body carries.

    Raises:
        HTTPException: 422 with `todo_task_empty_patch` when the body sets neither
            field; 422 with a `todo_task_text_*` code when the text is refused; 404 with
            `todo_task_not_found` when no task has `todo_task_id`.
    """
    if data.text is None and data.done is None:
        raise _unprocessable("todo_task_empty_patch", _EMPTY_PATCH)
    try:
        return service.change_todo_task(todo_task_id, text=data.text, done=data.done)
    except (
        service.TodoTaskNotFoundError,
        service.TodoTaskTextEmptyError,
        service.TodoTaskTextMultilineError,
        service.TodoTaskTextTooLongError,
    ) as error:
        raise _refusal(error) from error


@router.delete("/todo-tasks/{todo_task_id}", status_code=204, responses=_NOT_FOUND_RESPONSE)
def delete_todo_task(todo_task_id: uuid.UUID) -> None:
    """Delete a task for good.

    Raises:
        HTTPException: 404 with `todo_task_not_found` when no task has `todo_task_id`
            -- a second deletion of the same task included, so a deletion that did not
            happen is never reported as one.
    """
    try:
        service.delete_todo_task(todo_task_id)
    except service.TodoTaskNotFoundError as error:
        raise _refusal(error) from error

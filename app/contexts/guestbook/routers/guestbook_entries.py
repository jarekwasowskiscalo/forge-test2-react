"""Guestbook entries -- the one resource this template ships with.

Mounted at `/api/guestbook-entries`. HTTP binding and nothing else: it reads
the path and the body, calls `app.contexts.guestbook.services.guestbook_entries`, and translates
that module's domain exceptions into status codes in an explicit `match`. No
rule about entries is decided here (spec/design/conventions.md § Layers).

**Refusals carry a stable code and a finished English sentence.** The code is
what the screen branches on and never changes; the sentence is what a person
reads and may be reworded. Keeping the sentence beside the endpoint that
produced it -- rather than in a shared table one edit away from telling somebody
to fix the wrong field -- is the rule spec/design/api.md § Refusals states and
this module follows.

This is the resource to copy when you add your own, and the resource to delete
once yours has replaced it as the template's worked example.
"""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Query

from app.contexts.guestbook.schemas.guestbook_entries import (
    PAGE_SIZE_DEFAULT,
    PAGE_SIZE_MAX,
    QUERY_MAX_LENGTH,
    GuestbookEntryCreate,
    GuestbookEntryPage,
    GuestbookEntryRead,
    GuestbookEntrySort,
    GuestbookEntryUpdate,
)
from app.contexts.guestbook.services.guestbook_entries import (
    GuestbookEntryNotFoundError,
    create_entry,
    delete_entry,
    get_entry,
    list_entries,
    update_entry,
)
from app.platform.schemas.refusals import Refusal
from app.platform.schemas.text import NormalizedText

router = APIRouter()

#: What every route taking an id answers when the id does not resolve.
#:
#: Declared rather than merely raised, and the difference is the whole point:
#: FastAPI builds `openapi.json` from the decorator, never from the bodies of
#: raised exceptions, so a 404 that only ever appears inside `_not_found` below
#: reaches no document and no generated type. `spec/design/api.md` promised this
#: refusal all along and `frontend/src/api/schema.d.ts` had no shape for it.
_NOT_FOUND_RESPONSE: dict[int | str, dict[str, Any]] = {
    404: {"model": Refusal, "description": "There is no entry with that identifier."}
}

#: The 422 on PATCH, which is genuinely two shapes and must be published as two.
#:
#: This route is the only one that can refuse with a *coded* 422 -- the body
#: that sets no field (`guestbook_entry_empty_patch`). Every other way to earn a
#: 422 here is Pydantic's: an empty or over-long field, a wrong type, an
#: unreadable id in the path. Those answer with FastAPI's standard
#: `HTTPValidationError`, a LIST under `detail`, through
#: `app/core/errors.py`.
#:
#: Declaring `{"model": Refusal}` said the first was the only one. Worse, an
#: explicit 422 REPLACES the `HTTPValidationError` FastAPI would have generated
#: (`fastapi/openapi/utils.py` adds its own only when the operation declares
#: none), so the shape a caller meets most often vanished from the document and
#: from `frontend/src/api/schema.d.ts` -- leaving a consumer of the generated
#: types no way to describe it at all. `frontend/src/api/problem.ts` has always
#: handled both; it was the published contract that knew about one.
#:
#: Written as raw `$ref`s rather than `model=Refusal | HTTPValidationError`
#: because `HTTPValidationError` is not an importable Pydantic model -- FastAPI
#: injects it into `components/schemas` as a plain dict. This form is also the
#: only one that keeps the component NAMES `schema.d.ts` already knows: renaming
#: a component is itself a breaking change, whatever the shape underneath.
_EITHER_REFUSAL_OR_VALIDATION: dict[str, Any] = {
    "description": "The body sets no field at all, or a field is outside its bounds. "
    "Two different shapes under one status code: a coded refusal for the first, "
    "FastAPI's validation error for the rest.",
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

#: The sentence an operator reads when the id does not resolve. One constant
#: rather than four copies: this is the same fact on every route that takes an
#: id, and four copies drift.
_NOT_FOUND = "There is no such entry. Somebody else may have deleted it."

#: Refused before anything is read, because a PATCH that sets no field is a
#: request that cannot be carried out rather than one that succeeds by doing
#: nothing -- a client that meant to change something would otherwise get 200
#: and never learn its body was empty.
_EMPTY_PATCH = "No field was given to change. The entry is unchanged."


def _not_found(entry_id: uuid.UUID) -> HTTPException:
    return HTTPException(
        status_code=404,
        detail={"code": "guestbook_entry_not_found", "message": _NOT_FOUND, "id": str(entry_id)},
    )


@router.get("/guestbook-entries", response_model=GuestbookEntryPage)
def list_guestbook_entries(
    q: Annotated[
        str | None,
        # Ahead of `Query`, and that ordering is the fix rather than a detail.
        # `max_length` used to measure the phrase as it arrived, while an entry's
        # fields were measured after trimming -- so `spec/design/api.md` § Narrowing
        # ("the phrase is trimmed before it is measured") was true of the document
        # and of nothing else, and two hundred and five spaces earned a 422 instead
        # of being no phrase at all. `NormalizedText` is a `BeforeValidator`, so the
        # bound now applies to the same string the service will search with.
        NormalizedText,
        Query(max_length=QUERY_MAX_LENGTH, description="Narrow to entries containing this."),
    ] = None,
    sort: Annotated[
        GuestbookEntrySort, Query(description="Which end of the book to read from.")
    ] = GuestbookEntrySort.NEWEST,
    limit: Annotated[int, Query(ge=1, le=PAGE_SIZE_MAX)] = PAGE_SIZE_DEFAULT,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> GuestbookEntryPage:
    """One page of entries, with how many match and how many the book holds.

    The four parameters are bounded here rather than in the service, because
    every one of them is a fact about *this request* -- and FastAPI turns each
    bound into the standard 422 the frontend already normalises
    (`frontend/src/api/problem.ts`). A bad `sort` is therefore a refusal a
    caller can act on rather than a silent fall back to the default.
    """
    return list_entries(query=q, sort=sort, limit=limit, offset=offset)


@router.get(
    "/guestbook-entries/{entry_id}",
    response_model=GuestbookEntryRead,
    responses=_NOT_FOUND_RESPONSE,
)
def read_guestbook_entry(entry_id: uuid.UUID) -> GuestbookEntryRead:
    """One entry by id.

    Raises:
        HTTPException: 404 if no entry with `entry_id` exists.
    """
    try:
        return get_entry(entry_id)
    except GuestbookEntryNotFoundError as exc:
        raise _not_found(entry_id) from exc


@router.post("/guestbook-entries", response_model=GuestbookEntryRead, status_code=201)
def create_guestbook_entry(data: GuestbookEntryCreate) -> GuestbookEntryRead:
    """Add an entry. The length and emptiness rules refuse with 422 in Pydantic."""
    return create_entry(data)


@router.patch(
    "/guestbook-entries/{entry_id}",
    response_model=GuestbookEntryRead,
    responses={
        **_NOT_FOUND_RESPONSE,
        422: _EITHER_REFUSAL_OR_VALIDATION,
    },
)
def update_guestbook_entry(entry_id: uuid.UUID, data: GuestbookEntryUpdate) -> GuestbookEntryRead:
    """Change an entry's author, its message, or both.

    Raises:
        HTTPException: 422 if the body sets no field; 404 if no entry with
            `entry_id` exists.
    """
    if data.author is None and data.message is None:
        raise HTTPException(
            status_code=422,
            detail={"code": "guestbook_entry_empty_patch", "message": _EMPTY_PATCH},
        )
    try:
        return update_entry(entry_id, data)
    except GuestbookEntryNotFoundError as exc:
        raise _not_found(entry_id) from exc


@router.delete("/guestbook-entries/{entry_id}", status_code=204, responses=_NOT_FOUND_RESPONSE)
def delete_guestbook_entry(entry_id: uuid.UUID) -> None:
    """Remove an entry permanently.

    Raises:
        HTTPException: 404 if no entry with `entry_id` exists, so deleting the
            same id twice refuses the second time instead of reporting success.
    """
    try:
        delete_entry(entry_id)
    except GuestbookEntryNotFoundError as exc:
        raise _not_found(entry_id) from exc

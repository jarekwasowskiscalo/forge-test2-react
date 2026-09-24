"""Guestbook entry request/response data contracts.

Read and write shapes are separate classes even where they would be identical
today, per spec/design/conventions.md -- a response that grows a field must not
silently start accepting it on a request. These models import only from
`pydantic`: no coupling to FastAPI or to routers.

The length bounds are imported from the model rather than restated, because
restating them is how a schema and a column come to disagree about what fits.
`author` and `message` are stripped before they are measured, so a body of
spaces is refused as empty rather than stored as whitespace (`BR-01`).
"""

import datetime
import enum
import uuid
from typing import Annotated

from pydantic import BaseModel, Field

from app.contexts.guestbook.models.guestbook_entry import AUTHOR_MAX_LENGTH, MESSAGE_MAX_LENGTH
from app.platform.schemas.text import NormalizedText

#: The longest search phrase the list endpoint will consider. A ceiling rather
#: than no ceiling, because `q` reaches a `LIKE` pattern: an unbounded string is
#: an unbounded scan, and nobody searching a guest book types two hundred
#: characters on purpose.
QUERY_MAX_LENGTH = 200

#: How many entries one read may return. The screen asks for what it shows and
#: grows the number as somebody presses "Load more"; the ceiling is here so that
#: a caller which asks for everything is refused rather than served.
PAGE_SIZE_MAX = 100

#: What a caller gets when it names no page size. Big enough that a small book
#: comes back whole, small enough that a large one does not.
PAGE_SIZE_DEFAULT = 20

#: A signature, and a message, as the contract accepts them: normalized to NFC and
#: trimmed of the written whitespace set BEFORE the bound is applied, then measured
#: in code points.
#:
#: The order is what the two types exist to state. `NormalizedText` is a
#: `BeforeValidator`, so it runs ahead of the constraint -- which is why a signature
#: of nothing but spaces is *empty* rather than three characters long. This was
#: `ConfigDict(str_strip_whitespace=True)` until the unit of the bound became a
#: written rule rather than whatever each runtime happened to do:
#: `app/platform/schemas/text.py` says what changed and why, and
#: `golden-set/fixtures/text-measurement.json` is where both sides prove it.
Author = Annotated[str, NormalizedText, Field(min_length=1, max_length=AUTHOR_MAX_LENGTH)]
Message = Annotated[str, NormalizedText, Field(min_length=1, max_length=MESSAGE_MAX_LENGTH)]


class GuestbookEntrySort(enum.StrEnum):
    """The orders the list may be read in (`BR-04`).

    A closed set rather than a free string, so an unknown value is a refusal the
    caller can act on instead of a silent fall back to the default -- a client
    that misspells `oldest` should learn it, not get the newest first and
    quietly disagree with what its screen says.

    `StrEnum` so FastAPI renders the two values into the OpenAPI document as an
    enum of strings, which is what makes them reachable from the generated
    frontend types -- and so a member compares equal to its own wire value,
    which is what lets a step or a test say `"newest"` and mean the member.
    """

    NEWEST = "newest"
    OLDEST = "oldest"


class GuestbookEntryCreate(BaseModel):
    """Request contract for `POST /api/guestbook-entries`."""

    author: Author
    message: Message


class GuestbookEntryUpdate(BaseModel):
    """Request contract for `PATCH /api/guestbook-entries/{entry_id}`.

    Both fields are optional and a body that sets neither is refused by the
    router, not here: "no field given" is a fact about the request, and the
    sentence the operator reads about it belongs beside the endpoint that
    produced it (spec/design/conventions.md § Layers).
    """

    author: Author | None = None
    message: Message | None = None


class GuestbookEntryRead(BaseModel):
    """Response contract for a single guestbook entry."""

    id: uuid.UUID
    author: str
    message: str
    created_at: datetime.datetime
    updated_at: datetime.datetime


class GuestbookEntryPage(BaseModel):
    """Response contract for `GET /api/guestbook-entries`: one page and two counts.

    An envelope rather than a bare array, because a page cannot imply either
    number a paged screen has to state. `items` is what fits; `total` is how many
    entries answer the question that was asked; `total_all` is how big the book
    is regardless of the question.

    **The two counts are different facts and the screen shows both at once.** The
    header says how many entries exist; the line under the search box says how
    many the current search matched. Deriving either from `len(items)` is the
    defect `e2e/harness/list_response.py` was written about: 2 is a plausible
    number of rows, so a page of two would satisfy an assertion about a
    population of fifty.
    """

    items: list[GuestbookEntryRead]
    #: How many entries match `q`. Equal to `total_all` when no phrase was given.
    total: int = Field(ge=0)
    #: How many entries the book holds. Never affected by `q`, `limit` or `offset`.
    total_all: int = Field(ge=0)

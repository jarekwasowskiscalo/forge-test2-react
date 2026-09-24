"""The body of a refusal that carries a stable code.

`spec/design/api.md` section Refusals states this shape and calls the code "a
contract the screen branches on, and it never changes". Until this module existed
the sentence was true of the running application and of nothing else: the code is
raised inside `HTTPException(detail=...)`, FastAPI does not look into a raised
exception, so the shape reached neither `openapi.json` nor
`frontend/src/api/schema.d.ts`. The frontend normalised it by hand from an
untyped payload -- which is exactly the state Article VI of the constitution
forbids, one boundary over.

Declaring it here and naming it in each route's `responses=` is what carries the
shape into the generated types. `contracts/openapi/guestbook.yaml` freezes it
from the other side, and `./scripts/contracts.sh` holds the two together.

Not named after a resource, unlike its neighbours in this package, and that is
the rule rather than an exception to it: the refusal envelope is a fact about
every coded refusal this API makes, not about guest book entries. The *sentences*
stay beside the endpoint that produces them (`app/contexts/guestbook/routers/guestbook_entries.py`);
only the envelope is shared.
"""

from pydantic import BaseModel


class RefusalDetail(BaseModel):
    """The code, the sentence, and the identifier the refusal is about."""

    #: Stable, machine-readable, and never reworded. This is what a screen
    #: branches on.
    code: str
    #: A finished English sentence, written for the person reading it. May be reworded
    #: freely -- it is product text, not contract.
    message: str
    #: Present only when the refusal is about one identified thing. Absent on a
    #: refusal about the request as a whole, such as a PATCH that sets no field.
    id: str | None = None


class Refusal(BaseModel):
    """The envelope FastAPI puts a raised `HTTPException.detail` into."""

    detail: RefusalDetail

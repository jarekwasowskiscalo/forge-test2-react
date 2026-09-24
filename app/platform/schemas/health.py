"""The health probe's response shape.

One class rather than the read/write pair `spec/design/conventions.md` asks for,
because there is no write: nothing is ever sent to this endpoint. The convention
exists so a response that grows a field cannot silently start accepting it on a
request, and an endpoint with no request body has nothing to protect.

Imports only from `pydantic`, like every other module here: no FastAPI, no
routers, no services.
"""

from pydantic import BaseModel


class HealthRead(BaseModel):
    """What the probe answers with when the process is up.

    `status` is always `"ok"` and typed as a plain string rather than a literal
    on purpose: this endpoint's whole design is that answering at all IS the
    signal (`app/platform/routers/health.py`), so a second value would be a different
    endpoint. It is kept in the body because that is what every caller already
    keys on -- `scripts/app_status.py` among them.

    `environment` and `version` say WHICH copy answered. Without them a probe
    that returns 200 proves something is alive and nothing about what it is,
    which is the question actually asked after a release.
    """

    status: str
    environment: str
    version: str

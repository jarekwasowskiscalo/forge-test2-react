"""Health-check router.

Reports that the service process is up, and says which copy answered. Still zero
coupling to any service or persistence layer, so "the process answers" and "the
database is reachable" stay separate questions -- a health check that touches the
database turns a slow query into an outage. Naming the environment and the
release does not cross that line: both are strings read out of the process's own
environment (`app/core/build_info.py`), which cannot be slow and cannot fail.

They are here because a 200 alone proves something is alive and nothing about
what it is, and "what is on prod right now" is the question actually asked after
a release. `contracts/openapi/health.yaml` carries them as a promise.

Registered on `api_router` in `app/api.py`, so the route is
**`/api/health`**. Plain `/health` is matched by the SPA catch-all in
`app/main.py`: it answers 200 with the HTML shell wherever a frontend build
exists, and 404 where one does not, so it is never a liveness signal. Probes
and scripts must use the prefixed path.
"""

from fastapi import APIRouter

from app.core import build_info
from app.platform.schemas.health import HealthRead

router = APIRouter()


@router.get("/health")
def get_health() -> HealthRead:
    """Report that the service is running, and which release is running it."""
    return HealthRead(
        status="ok",
        environment=build_info.environment(),
        version=build_info.version(),
    )

"""Application entrypoint.

Creates the FastAPI app instance and wires together, in this exact order:

0. logging (`configure_logging`) and the request-id middleware -- so the very
   first record of the process is shaped and every later line carries the id.
1. `api_router` under `/api` -- every JSON endpoint.
2. `/assets` -- the Vite build's hashed, immutable bundles.
3. the SPA catch-all -- `index.html` for every remaining path.

**The order is load-bearing.** `/{full_path:path}` matches every path,
including `/api/...`, and Starlette matches routes in registration order
with first-match-wins. Registering the catch-all first would make every API
call return the HTML shell with status 200, and the frontend would then fail
on `JSON.parse("<!doctype ...")`. The catch-all additionally re-raises a
JSON 404 for unknown `api/` paths, so a typo'd endpoint never silently
returns HTML.

Intentionally does not configure a host/port or add a `uvicorn.run(...)`
block: `scripts/start.sh` decides the address (`:8080` by default, and the
container maps its `8000` onto it), so Uvicorn's own CLI default
(`uvicorn app.main:app`), not app-level code.
"""

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response

from app.api import api_router
from app.core import build_info
from app.core.errors import CatchAllMiddleware, register_error_handlers
from app.core.logging_config import configure_logging
from app.core.request_id import RequestIdMiddleware
from app.core.robots import UNLISTED_ENVIRONMENTS, NoIndexMiddleware

# At import, not in a lifespan: both entrypoints (the image's `uvicorn
# app.main:app` and scripts/run.py) import this module exactly once per worker,
# and configuring here means the first record of the process is already shaped.
configure_logging()

# Where Vite's build lands (`build.outDir` in frontend/vite.config.ts) and, in
# the image, where the Node stage's output is copied to. `FRONTEND_STATIC_DIR`
# overrides it, which is what lets tests point at a throwaway build instead of
# writing into -- and then deleting -- a developer's real one.
STATIC_DIR = Path(os.environ.get("FRONTEND_STATIC_DIR") or Path(__file__).parent / "static")
INDEX_HTML = STATIC_DIR / "index.html"

app = FastAPI(title="Guestbook API", version="0.1.0")

# FIRST, because `add_middleware` inserts at the front of the list and the front
# of that list is the OUTERMOST layer -- so the first one added here is the last
# one entered, and this has to be the innermost of the three. Starlette builds
# `ServerErrorMiddleware` outside all of them and answers through the raw
# `send`, so an unhandled exception caught only there left without the two
# headers below. Caught here instead, the 500 travels back out through both
# wrappers and is stamped like every other response (`app/core/errors.py`).
app.add_middleware(CatchAllMiddleware)

# The request id rides a contextvar, so it must be set before anything that
# logs -- pure ASGI, no response buffering.
app.add_middleware(RequestIdMiddleware)

# A preview answers on a public URL that nothing authenticates, so it says
# `noindex` on every response (`app/core/robots.py`). Added only where it applies:
# stage and production are indexable if somebody points a domain at them, and a
# middleware that always ran would be a decision hidden inside a condition.
if build_info.environment() in UNLISTED_ENVIRONMENTS:
    app.add_middleware(NoIndexMiddleware)

# 1. API first -- before anything that could shadow it.
app.include_router(api_router, prefix="/api")


class ImmutableStaticFiles(StaticFiles):
    """Serves Vite's build output with a one-year immutable cache.

    Safe only because every filename Vite emits under `assets/` carries a
    content hash: a changed file is a changed URL, so a cached response can
    never go stale. `index.html` is deliberately NOT served from here -- it
    keeps a stable URL and so must stay `no-cache` (see `spa` below).
    """

    def file_response(self, *args: Any, **kwargs: Any) -> Response:
        response = super().file_response(*args, **kwargs)
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return response


# 2. Built assets. Mounted only when a build exists: in dev the Vite server
# serves them from memory on :5173 and `app/static/` is empty, and
# StaticFiles raises at construction time if its directory is missing.
if (STATIC_DIR / "assets").is_dir():
    app.mount(
        "/assets",
        ImmutableStaticFiles(directory=STATIC_DIR / "assets"),
        name="assets",
    )


# 3. SPA fallback LAST. The server has no per-page HTML -- every non-API URL
# returns the identical shell and React Router decides what to render.
@app.get("/{full_path:path}", include_in_schema=False)
async def spa(full_path: str) -> FileResponse:
    """Return the SPA shell, or a JSON 404 for unknown `/api/*` paths."""
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")
    if not INDEX_HTML.is_file():
        raise HTTPException(
            status_code=404,
            detail="frontend build not found -- run `npm run build` in frontend/",
        )
    # Stable URL, so it must never be cached: a stale shell would reference
    # hashed bundles that the previous deploy deleted.
    return FileResponse(
        INDEX_HTML,
        media_type="text/html",
        headers={"Cache-Control": "no-cache"},
    )


register_error_handlers(app)

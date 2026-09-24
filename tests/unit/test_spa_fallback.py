"""Tests for the single-artifact serving wiring in app/main.py.

Three properties are load-bearing and each is easy to break silently:

1. **Registration order.** `/{full_path:path}` matches `/api/...` too, and
   Starlette matches in registration order. If the catch-all were registered
   before `api_router`, every API call would answer 200 with the HTML shell.
2. **The `api/` guard.** An unknown API path must be a JSON 404, not the
   shell -- otherwise a typo'd endpoint surfaces as a JSON parse error in the
   browser rather than a 404 the fetch wrapper can handle.
3. **Cache headers.** Hashed bundles under `/assets` are immutable;
   `index.html` keeps a stable URL and so must be `no-cache`. Reversed, a
   deploy leaves users on a cached shell pointing at deleted bundles.

The SPA shell is a build artifact that does not exist in a source checkout, so
these tests build a throwaway one in `tmp_path` and point `app.main` at it via
`FRONTEND_STATIC_DIR`. They must NOT write into the real `app/static/`: a
developer who has run `npm run build` would have their build deleted at
teardown.

`app.main` is reloaded because the directory is resolved -- and the `/assets`
mount decided -- at import time. StaticFiles raises in its constructor when
its directory is missing, so the mount cannot be conditional on anything later
than import.
"""

import importlib
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.main

INDEX_HTML = "<!doctype html><html><head></head><body><div id=root></div></body></html>"
BUNDLE_JS = "console.log('bundle')\n"
BUNDLE_NAME = "index-B4f9c0de.js"


def _reload_main() -> FastAPI:
    # `importlib.reload` returns `ModuleType`, so `.app` is `Any` and the declared
    # return type was a claim nothing checked.
    reloaded: FastAPI = importlib.reload(app.main).app
    return reloaded


@pytest.fixture
def built_app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[FastAPI]:
    """Yield an app instance serving a throwaway frontend build in `tmp_path`."""
    static_dir = tmp_path / "static"
    (static_dir / "assets").mkdir(parents=True)
    # `newline=""` alongside the encoding: `write_text` translates "\n" to
    # `os.linesep` by default, so on Windows the bundle would land on disk as
    # CRLF while the assertions below compare the served bytes against the LF
    # original. The point of these fixtures is to be byte-exact.
    (static_dir / "index.html").write_text(INDEX_HTML, encoding="utf-8", newline="")
    (static_dir / "assets" / BUNDLE_NAME).write_text(BUNDLE_JS, encoding="utf-8", newline="")

    monkeypatch.setenv("FRONTEND_STATIC_DIR", str(static_dir))
    yield _reload_main()

    # monkeypatch restores the env var, but app.main still holds the tmp_path
    # it was reloaded with -- reload again so later tests see the real module.
    monkeypatch.undo()
    _reload_main()


@pytest.fixture
def unbuilt_app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[FastAPI]:
    """Yield an app instance pointed at a static dir that does not exist."""
    monkeypatch.setenv("FRONTEND_STATIC_DIR", str(tmp_path / "never-built"))
    yield _reload_main()
    monkeypatch.undo()
    _reload_main()


def test_api_route_wins_over_the_catch_all(built_app: FastAPI) -> None:
    """`/api/health` reaches the API router, not the SPA shell."""
    with TestClient(built_app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    #: The status alone: what this test is about is which handler answered, and
    #: the rest of the body belongs to tests/unit/test_health.py.
    assert response.json()["status"] == "ok"


def test_unknown_api_path_returns_json_404_not_the_shell(built_app: FastAPI) -> None:
    with TestClient(built_app) as client:
        response = client.get("/api/nope")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/json")
    assert "<!doctype" not in response.text.lower()


def test_a_mistyped_api_path_stays_a_typo_and_never_becomes_a_refusal(
    built_app: FastAPI,
) -> None:
    """A typo in the address answers 404 and nothing else.

    This template has no access check, so today the assertion is cheap. It is
    kept because it is the one that decides *where* a check may live when a
    product adds one: a route dependency runs after a route has matched, so an
    unmatched `/api/...` path never reaches it. The same check written as
    middleware would run before routing and answer 401 here -- turning every
    mistyped endpoint into "your session expired", which sends the caller to log
    in again over a problem logging in does not solve. Asserted by absence: no
    401, no 403, and no cookie handed out on the way.
    """
    with TestClient(built_app) as client:
        response = client.get("/api/nope/at/all")

    assert response.status_code == 404, "an unknown path answered as an access decision"
    assert response.headers["content-type"].startswith("application/json")
    assert "set-cookie" not in response.headers


@pytest.mark.parametrize("path", ["/", "/guestbook", "/guestbook/anything", "/no-such-page"])
def test_every_app_route_returns_the_same_shell(built_app: FastAPI, path: str) -> None:
    """There is no per-page HTML -- React Router decides what to render."""
    with TestClient(built_app) as client:
        response = client.get(path)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert response.text == INDEX_HTML


def test_shell_is_not_cached(built_app: FastAPI) -> None:
    with TestClient(built_app) as client:
        response = client.get("/guestbook")

    assert response.headers["cache-control"] == "no-cache"


def test_hashed_bundle_is_served_immutable(built_app: FastAPI) -> None:
    with TestClient(built_app) as client:
        response = client.get(f"/assets/{BUNDLE_NAME}")

    assert response.status_code == 200
    assert response.text == BUNDLE_JS
    assert response.headers["cache-control"] == "public, max-age=31536000, immutable"


def test_missing_build_keeps_the_api_working(unbuilt_app: FastAPI) -> None:
    """A source checkout has no build -- the app must still boot and serve /api.

    Only the SPA route degrades, and it degrades to a JSON 404 that names the
    fix. That is what makes `uvicorn app.main:app --reload` usable next to the
    Vite dev server, which serves the shell itself on :5173.
    """
    with TestClient(unbuilt_app) as client:
        assert client.get("/api/health").status_code == 200

        response = client.get("/guestbook")

    assert response.status_code == 404
    assert "npm run build" in response.json()["detail"]

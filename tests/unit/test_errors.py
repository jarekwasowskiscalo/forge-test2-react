"""Tests for centralized JSON error handling (Boundary: ErrorHandlers).

Verifies `register_error_handlers` in isolation against a throwaway FastAPI()
app with minimal test-only routes, rather than via the real items endpoints,
so these tests do not depend on the resource routes being wired into
`app.main`. The contract held here: invalid input answers with a 4xx JSON
payload, and an unhandled error answers with a 5xx JSON payload that leaks
no internals.
"""

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel
from starlette.testclient import TestClient as StarletteTestClient

from app.core.errors import register_error_handlers

# A distinctive substring of the exception message raised by the 500 test
# route. Used to assert this text never leaks into the client response.
_SECRET_EXCEPTION_MESSAGE = "sql password hunter2 leaked-detail-88421"


class _Payload(BaseModel):
    name: str


def _build_test_app() -> FastAPI:
    """Build a throwaway app with error handlers and minimal test-only routes."""
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/boom-http")
    def boom_http() -> None:
        raise HTTPException(status_code=404, detail="not found here")

    @app.post("/boom-validation")
    def boom_validation(payload: _Payload) -> dict[str, str]:
        return {"name": payload.name}

    @app.get("/boom-generic")
    def boom_generic() -> None:
        raise ValueError(_SECRET_EXCEPTION_MESSAGE)

    return app


def _client() -> TestClient | StarletteTestClient:
    app = _build_test_app()
    return TestClient(app, raise_server_exceptions=False)


def test_http_exception_passes_through_unchanged() -> None:
    with _client() as client:
        response = client.get("/boom-http")

    assert response.status_code == 404
    assert response.json() == {"detail": "not found here"}


def test_request_validation_error_returns_structured_422() -> None:
    with _client() as client:
        # Missing the required "name" field triggers a validation failure.
        response = client.post("/boom-validation", json={})

    assert response.status_code == 422
    body = response.json()
    assert "detail" in body
    assert isinstance(body["detail"], list)
    assert any("name" in str(err.get("loc", [])) for err in body["detail"])


def test_unhandled_exception_returns_fixed_sanitized_500() -> None:
    with _client() as client:
        response = client.get("/boom-generic")

    assert response.status_code == 500
    assert response.json() == {"detail": "internal server error"}

    response_text = response.text
    assert _SECRET_EXCEPTION_MESSAGE not in response_text
    assert "ValueError" not in response_text
    assert "Traceback" not in response_text

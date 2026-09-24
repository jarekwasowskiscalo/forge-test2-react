"""The health-check endpoint (HealthRouter), exercised in isolation.

Mounts ONLY app.platform.routers.health onto a throwaway FastAPI() app, deliberately --
the point is the router's own contract (running status as JSON, a successful
status code on the defined path), not the wiring of `app.main`, which registers
every router under `/api` and is proved by tests/integration/test_app_integration.py.
This mirrors how the error tests exercise their handlers in isolation.

One fact is the exception to that isolation and is asserted on the real
aggregate instead: that the liveness check answers **with every database
connection refused**. That is a claim about the whole application, not about a
router, and an isolated mount is precisely where it cannot be false. It lives in
this suite because it is the one thing here that must hold with no database at
all, and a suite that needs one cannot state it.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core import build_info
from app.platform.routers.health import router as health_router


def _build_health_only_app() -> FastAPI:
    """Build a throwaway app exposing only the health router in isolation.

    Mounted with no prefix, so the paths below are unprefixed. The `/api`
    prefix is applied once, in `app.main`, and is not the router's own
    business -- asserting it here would test the wiring rather than the
    router. `tests/integration/test_app_integration.py` covers it on the real app.
    """
    app = FastAPI()
    app.include_router(health_router)
    return app


def test_health_endpoint_returns_ok_status_and_json_body() -> None:
    app = _build_health_only_app()
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    #: The keys rather than the values: `environment` and `version` are read from
    #: the process environment, so a suite that pinned them here would fail on the
    #: one machine that had APP_ENV set. What they are read from is asserted by
    #: test_health_reports_the_copy_that_answered below.
    assert response.json().keys() == {"status", "environment", "version"}
    assert response.json()["status"] == "ok"


def test_health_reports_the_copy_that_answered() -> None:
    """The probe names its environment and release, or the deployment is anonymous.

    This is the whole reason the body grew: a 200 proves something is alive and
    nothing about what it is, and "which release is on prod right now" is the
    question actually asked after a deploy. Terraform sets both variables on both
    functions (`infra/terraform/modules/api/main.tf`); here they are set by hand,
    so the assertion is about the wiring rather than about any one deployment.
    """
    app = _build_health_only_app()

    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("APP_ENV", "stage")
        patch.setenv("APP_VERSION", "v9.9.9")
        with TestClient(app) as client:
            body = client.get("/health").json()

    assert body == {"status": "ok", "environment": "stage", "version": "v9.9.9"}


def test_health_outside_a_deployment_says_so_rather_than_inventing_one() -> None:
    """With nothing set, the answer is `local` and the repository's own version.

    A probe that guessed an environment name would put a wrong word on a screen
    somebody trusts, so the fallback is a word no deployment uses.
    """
    app = _build_health_only_app()

    with pytest.MonkeyPatch.context() as patch:
        patch.delenv("APP_ENV", raising=False)
        patch.delenv("APP_VERSION", raising=False)
        with TestClient(app) as client:
            body = client.get("/health").json()

    assert body["environment"] == "local"
    assert body["version"] != ""


def test_the_repository_still_has_a_version_the_fallback_can_find() -> None:
    """The arrangement above is only useful while it points at the real file.

    `APP_VERSION` is how a deployment says which release answered, and since the
    release stopped writing a version into `pyproject.toml` that file is no longer
    kept in step with any tag. It is still the fallback for a checkout, though --
    the test above asserts the answer is not empty, and this says where the
    non-empty answer comes from. A `[project]` table that lost its `version` would
    make both of them report `0.0.0+unknown` and neither of them say why.
    """
    assert build_info._version_from_pyproject() is not None


def test_health_answers_on_the_whole_api_under_its_real_prefix() -> None:
    """The probe is reachable at the address a load balancer is configured with.

    Asserted on the real aggregate (`app.main`) rather than on the isolated
    router above, because `/api` is applied by `app/api.py` and an
    isolated mount is exactly where a lost prefix cannot be observed. It also
    hands back no cookie: a liveness probe has no identity and must not be
    given one, which stays true for whatever authentication a product grows on
    top of this template.
    """
    from app.main import app

    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "set-cookie" not in response.headers


def test_health_answers_while_every_database_connection_fails() -> None:
    """The production image serves this route in a container with no Postgres.

    The engine is made to refuse every connection, so anything the request touches
    below the router -- an eager dependency, a service reached by accident --
    turns into a failure here rather than into a 200 that happened to run next to a
    reachable database. It is patched on the engine rather than on `SessionLocal`,
    because the services bind that name at import time and rebinding the module
    attribute would leave them holding the original.
    """
    from app.db import session as db_session
    from app.main import app

    def _refuse(*args: object, **kwargs: object) -> None:
        raise AssertionError("the liveness check reached for a database connection")

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(db_session.engine, "connect", _refuse)
        with TestClient(app) as client:
            response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"

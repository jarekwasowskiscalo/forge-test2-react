"""A preview must not be indexable; nothing else may be quietly made unindexable.

A per-branch preview answers on a public, unauthenticated Function URL. That is a
deliberate trade -- `AWS_IAM` authorization would make it unopenable in a browser,
which is the one thing a preview is for -- and "short-lived and throwaway" answers
"who can reach it" without answering "what if a crawler finds it". An indexed page
outlives the branch by however long the index holds it.

The header form rather than a `robots.txt` or a meta tag, because it applies to
every response including the JSON ones, and because neither of the others can be
turned on for one environment and off for the others.

The second test is the one that will fail one day: the middleware is added by a
condition in `app/main.py`, and a condition is exactly the kind of thing that gets
loosened to `!= "prod"` by somebody in a hurry -- at which point stage silently
stops being indexable and nobody finds out from a test.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.robots import UNLISTED_ENVIRONMENTS, NoIndexMiddleware

HEADER = "x-robots-tag"


def _app_with_middleware() -> FastAPI:
    app = FastAPI()
    app.add_middleware(NoIndexMiddleware)

    @app.get("/thing")
    def thing() -> dict[str, str]:
        return {"ok": "yes"}

    return app


def test_every_response_carries_the_header() -> None:
    """Including the JSON ones, which is what a `robots.txt` could not reach."""
    with TestClient(_app_with_middleware()) as client:
        response = client.get("/thing")

    assert response.status_code == 200
    assert response.headers[HEADER] == "noindex, nofollow"


def test_a_response_that_is_not_a_success_carries_it_too() -> None:
    """A 404 renders a page too, and a crawler will happily index one."""
    with TestClient(_app_with_middleware()) as client:
        response = client.get("/nothing-here")

    assert response.status_code == 404
    assert response.headers[HEADER] == "noindex, nofollow"


def test_only_the_disposable_environments_are_hidden() -> None:
    """Named set, not `!= "prod"`.

    Stage exists to be production's rehearsal, and a rehearsal that differs from
    production in whether search engines can see it is a difference nobody chose.
    The set is asserted here so that widening it is a decision somebody makes on
    purpose rather than a comparison somebody loosens.
    """
    assert set(UNLISTED_ENVIRONMENTS) == {"preview"}


@pytest.mark.parametrize("environment", ["local", "stage", "prod"])
def test_the_real_application_adds_it_only_where_it_should(environment: str) -> None:
    """Asserted against `app.main`'s own condition rather than restating it.

    Reads the source, because the decision is taken at import: the module is
    already loaded by the time a test could set the variable, and re-importing it
    to find out would prove something about the reimport rather than about the app.
    """
    import pathlib

    main = (pathlib.Path(__file__).resolve().parents[2] / "app" / "main.py").read_text("utf-8")

    assert "build_info.environment() in UNLISTED_ENVIRONMENTS" in main, (
        "app/main.py no longer decides by the named set, so a widened comparison "
        "could hide stage or production from search engines with nothing to say so"
    )
    assert (environment in UNLISTED_ENVIRONMENTS) == (environment == "preview")

"""Fixtures and the artefact policy for the UI smoke suite.

The suite drives the *built* SPA in a real Chromium against the same running
application the HTTP scenarios use, so the wiring mirrors `e2e/suite/conftest.py`
on purpose: one health check per session that exits with a sentence, one database
reset per test through the harness, one coherence probe that asks the application
whether the reset it cannot see actually reached it. The probe is not written
here: it lives once, in `e2e/suite/conftest.py`, so this room inherits it rather
than copying it. What is new here is the browser -- and the policy around what
the browser is allowed to record.

**The artefact policy is this code, not a convention** (`spec/design/testing.md` § The UI smoke in a browser):

* No tracing and no video, ever. The launch and context calls below simply never
  pass `record_video_dir` or start tracing, and `tests/fitness/test_ui_suite.py`
  keeps the pytest-playwright plugin -- whose CLI can switch both on from the
  command line -- out of the tree.
* A screenshot is taken **only when a test fails**, and lands in
  `.sdd/ui-artifacts/` -- gitignored, never uploaded. Never `e2e/reports/`: that
  directory is a CI artefact, and a pixel-perfect picture of a screen full of
  real records is exactly the personal data Article XI keeps out of artefacts.
* Assertion messages in the tests name counts, roles and selectors, never a
  value read off the page -- the page's values *are* the data.

`UI_BASE_URL` is the API base with its `/api` suffix cut off: the application
serves the SPA and the API from one process, so the two agree by construction
and `TARGET_BASE_URL` keeps working for both suites.
"""

import os
import pathlib
from collections.abc import Generator, Iterator
from typing import Final

import pytest
from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from e2e.harness.client import BASE_URL, ApiClient
from e2e.harness.database import reset_target_database
from e2e.suite.conftest import (
    DATABASE_URL_VAR,
    HEALTH_PATH,
    REQUIRED_TABLES,
    the_application_agrees_its_world_is_empty,
)

UI_BASE_URL: Final[str] = BASE_URL.removesuffix("/api")

_REPO_ROOT: Final[pathlib.Path] = pathlib.Path(__file__).resolve().parents[2]

#: Failure screenshots only. Under `.sdd/` so it is gitignored and stays on the
#: machine that ran the suite; `e2e/reports/` is uploaded and must stay pixel-free.
ARTIFACTS_DIR: Final[pathlib.Path] = _REPO_ROOT / ".sdd" / "ui-artifacts"


@pytest.fixture(scope="session")
def _target_is_answering() -> None:
    """One sentence instead of seven identical connection errors.

    The API health route, not the SPA shell: the shell answers 200 HTML for any
    path whatever the application's state, which is the exact trap `/api/health`
    exists to avoid.
    """
    client = ApiClient()
    try:
        answer = client.get(HEALTH_PATH)
    except Exception as exc:
        pytest.exit(
            f"nothing answered {BASE_URL}{HEALTH_PATH} ({exc!r}). The UI smoke suite "
            "needs the application running with a built SPA: `./scripts/test.sh e2e` "
            "arranges both.",
            returncode=1,
        )
    finally:
        client.close()
    if answer.status != 200:
        pytest.exit(f"{BASE_URL}{HEALTH_PATH} answered {answer}.", returncode=1)


@pytest.fixture(scope="session")
def browser(_target_is_answering: None) -> Iterator[Browser]:
    """One Chromium per session. Launched plain: no tracing, nothing recorded."""
    playwright: Playwright = sync_playwright().start()
    launched = playwright.chromium.launch()
    try:
        yield launched
    finally:
        launched.close()
        playwright.stop()


@pytest.fixture
def page(browser: Browser) -> Iterator[Page]:
    """A fresh context per test -- no cookies, storage or history bleed between
    tests -- and deliberately no `record_video_dir`. See the module docstring."""
    context = browser.new_context()
    try:
        yield context.new_page()
    finally:
        context.close()


@pytest.fixture
def empty_application(_target_is_answering: None) -> Iterator[ApiClient]:
    """The reset the HTTP suite does, through the same harness.

    The coherence question is asked here, on a throwaway conversation: an
    application on :8080 pointed at a *different* database would otherwise pass
    an empty-screen assertion against a world this suite never emptied. The
    implementation lives in `e2e/suite/conftest.py` so both rooms get the check
    from one place instead of two that can drift.

    The yielded client is the seam for seeding through the API -- httpx stays in
    the harness, psycopg stays in `harness/database`, and this suite opens no
    connection of its own.

    The same disposability mark gates the reset here, in the same order and from
    the same place: `reset_target_database` refuses a database that is not this
    run's to empty before it composes a statement that deletes anything. Two
    rooms, one guard, because two copies of a guard is how one of them comes to
    be the weaker.
    """
    url = os.environ.get(DATABASE_URL_VAR)
    if not url:
        pytest.exit(
            f"{DATABASE_URL_VAR} is not set, so there is no database to empty between "
            "tests. `./scripts/test.sh e2e` sets it; a hand-run needs it exported.",
            returncode=1,
        )
    reset_target_database(url, required=REQUIRED_TABLES)

    probe = ApiClient()
    try:
        the_application_agrees_its_world_is_empty(probe)
    finally:
        probe.close()

    client = ApiClient()
    try:
        yield client
    finally:
        client.close()


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[None]
) -> Generator[None, pytest.TestReport, pytest.TestReport]:
    """Screenshot on failure, and only on failure -- the whole artefact policy.

    Wrapped so the report exists when the verdict is read. The screenshot is a
    courtesy for the person debugging locally; a failure to take it must never
    replace the test's own failure, hence the swallowed exception around it.
    """
    report = yield
    failed_with_a_page = report.when == "call" and report.failed
    page = getattr(item, "funcargs", {}).get("page") if failed_with_a_page else None
    if page is not None:
        try:
            ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
            safe = item.nodeid.replace("/", "_").replace("::", "-")
            page.screenshot(path=str(ARTIFACTS_DIR / f"{safe}.png"), full_page=True)
        except Exception:
            pass
    return report

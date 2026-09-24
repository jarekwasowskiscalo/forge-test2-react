"""Two fixtures: is the application there, and is its world empty.

This file sits in `suite/` rather than beside `harness/` because it is the half
that knows the application -- which port, which health route, which tables have
to exist, what an empty guest book answers. The harness knows none of that and
takes all four as arguments.

Neither fixture does anything at import time. This module is loaded by an editor
collecting the tree and by `pytest --collect-only`, neither of which should
start a container or open a socket.
"""

import os
from collections.abc import Iterator
from typing import Final

import pytest

from e2e.harness.client import BASE_URL, ApiClient
from e2e.harness.database import reset_target_database
from e2e.harness.list_response import rows
from e2e.suite.target import Target

#: The database the scenarios empty, and the same one the application is using.
#: `scripts/test.sh e2e` resolves it before starting anything and `start.sh`
#: inherits this exact value, so the suite and the application cannot disagree
#: about which database they mean. Deliberately not defaulted here: a second
#: copy of that connection string is precisely the drift `_lib.sh` was written
#: to stop.
DATABASE_URL_VAR: Final[str] = "DATABASE_URL"

#: Liveness only -- it touches no service and no persistence layer, which is why
#: an answer here is not evidence that the database is reachable.
HEALTH_PATH: Final[str] = "/health"

#: Discovery that cannot see this is not looking at this application's migrated
#: database, and emptying the wrong one produces wrong counts in business
#: assertions rather than one error about the database. The tables a product
#: adds later do not belong here -- they will be discovered because they exist.
#:
#: **This is a sanity check and never a permission**, and it used to be read as
#: though it were both. A shared staging database has `guestbook_entries` too:
#: the name proves the schema is this application's, not that the rows in it are
#: anybody's to delete. What decides that is the disposability mark the harness
#: reads off the database itself, before the truncate -- `e2e/harness/database.py`
#: § `assert_disposable`.
REQUIRED_TABLES: Final[frozenset[str]] = frozenset({"guestbook_entries"})

#: The list endpoint the coherence check below asks. The question is whether the
#: application sees an empty world, not what is in it.
ENTRIES: Final[str] = "/guestbook-entries"

#: The Gherkin tag that carries a requirement id, and the pytest marker it turns
#: into. `@req:CR-2608-a7f3/R-3` becomes `@pytest.mark.req("CR-2608-a7f3/R-3")`,
#: so one traceability reader works across the pytest suite and this one instead
#: of two that can disagree about what counts as a reference.
REQ_TAG_PREFIX: Final[str] = "req:"


def pytest_bdd_apply_tag(tag: str, function: object) -> bool | None:
    """Turn `@req:<id>` into the `req` marker; leave every other tag to pytest-bdd.

    Returning `None` means "not handled", which hands the tag back to the default
    behaviour -- so `@skip` and `@xfail` keep working. Returning `True` claims it.
    """
    if not tag.startswith(REQ_TAG_PREFIX):
        return None
    marker = pytest.mark.req(tag[len(REQ_TAG_PREFIX) :])
    marker(function)
    return True


@pytest.fixture(scope="session")
def _target_is_answering() -> None:
    """Fail once, with a sentence, rather than once per scenario with a stack.

    The suite this replaces had no health check at all, so a wrong base URL --
    or no application -- produced one identical connection error per scenario and
    no statement of the cause. `pytest.exit` rather than `pytest.fail` for the
    same reason: there is nothing to learn from the tenth failure.
    """
    client = ApiClient()
    try:
        answer = client.get(HEALTH_PATH)
    except Exception as exc:
        pytest.exit(
            f"nothing answered {BASE_URL}{HEALTH_PATH} ({exc!r}). Start one with "
            "`./scripts/start.sh`, or set TARGET_BASE_URL -- and keep the "
            "`/api` suffix on it: without the prefix every route is answered by the SPA "
            "catch-all in app/main.py, which returns the HTML shell with a 200.",
            returncode=1,
        )
    finally:
        client.close()

    if answer.status != 200:
        pytest.exit(
            f"{BASE_URL}{HEALTH_PATH} answered {answer}. A 405 or an HTML body here means "
            "the base URL is missing its `/api` prefix and the SPA catch-all is replying.",
            returncode=1,
        )


def the_application_agrees_its_world_is_empty(client: ApiClient) -> None:
    """Ask the application whether the reset it cannot see actually reached it.

    **This runs after the reset, and it is no longer the first thing that looks.**
    `reset_target_database` now settles the target before it deletes anything:
    it asks the server which database answered and whether that database carries
    this run's disposability mark, on the very connection the truncate will use.
    So the question below has stopped being the only one and has kept its job --
    the mark says the database is this run's to empty, and this says the
    application is reading the database that was emptied. Neither implies the
    other, which is why both are asked.

    This catches the failure that actually bites: `test.sh e2e` reuses an
    application already listening on :8080, and that application may be pointed
    at a different database than DATABASE_URL names. Emptying database A and
    asserting business counts against database B is exactly "a wrong count in a
    business assertion, which reads as an application defect and sends the reader
    to the wrong code" -- no comparison of connection strings can see it, and one
    question to the application can.

    **The client asking must not be the scenario's own.** The client handed to a
    scenario has made no request, and the scenario depends on that:
    `ApiClient.last` raises "no request has been made in this scenario" so that a
    `Then` reading a response no `When` produced fails with a sentence. Asking
    this question on that client quietly disables the check -- a scenario that
    lost its `When` but kept its `Then` would read *this* answer and pass.
    """
    remaining = rows(client.get(ENTRIES))

    if remaining:
        raise AssertionError(
            f"the database at {DATABASE_URL_VAR} was emptied, but the application still "
            f"reports guest book entries. It is reading a different database than this "
            f"suite just truncated -- most likely an application left running on :8080 "
            f"from an earlier session, with a different {DATABASE_URL_VAR}."
        )


@pytest.fixture(autouse=True)
def empty_world(_target_is_answering: None) -> None:
    """The world every scenario in this room starts from, emptied before it runs.

    Autouse, and a fixture of the *scenario* rather than of a client, because
    that says the true thing: emptying the world is a precondition of running
    one, and no step chooses it. Hanging it off a client fixture isolates only
    the scenarios that happen to request that client, which is not isolation --
    it is a coincidence that holds until a scenario talks to the application some
    other way.

    The reset is per scenario rather than per run: it costs milliseconds and
    per-scenario isolation removes every ordering dependency between scenarios,
    which is worth more than the time it saves.

    The coherence question -- does the reset reach the application the suite is
    talking to? -- is asked here too, on a throwaway conversation, because there
    is no session to wait for: every route this application has answers without
    one.

    `reset_target_database` refuses outright -- before it sends a statement that
    deletes anything -- when the database does not carry this run's disposability
    mark. `./scripts/test.sh e2e` is what puts the mark there, so a hand-run of
    pytest stops with a sentence naming the script rather than emptying whatever
    `DATABASE_URL` happens to be pointing at that afternoon.
    """
    url = os.environ.get(DATABASE_URL_VAR)
    if not url:
        pytest.exit(
            f"{DATABASE_URL_VAR} is not set, so there is no database to empty between "
            "scenarios and a run would be testing whatever the last one left behind. "
            "`./scripts/test.sh e2e` sets it; a hand-run needs it in the environment.",
            returncode=1,
        )
    reset_target_database(url, required=REQUIRED_TABLES)

    probe = ApiClient()
    try:
        the_application_agrees_its_world_is_empty(probe)
    finally:
        probe.close()


@pytest.fixture
def target(empty_world: None) -> Iterator[Target]:
    """The client the scenario will talk to the application with.

    The client handed over below has made **no request of its own**, and the
    scenario depends on that: it is what lets `ApiClient.last` tell a step that
    no `When` ran. See `the_application_agrees_its_world_is_empty` for what
    asking the coherence question on this client would cost.

    It depends on `empty_world` so the ordering is stated rather than assumed:
    the client must not exist before the reset, or a scenario could send its
    first request into a world that is about to be emptied under it.
    """
    client = ApiClient()
    try:
        yield Target(api=client)
    finally:
        client.close()

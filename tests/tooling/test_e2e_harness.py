"""Unit tests for `e2e/harness/` -- the parts that survive an API change.

These used to be six `unittest` modules inside the behave tree, run only by CI
and only by hand-enumerating their names across three working directories with
`../../../.venv/bin/python`. A newly added one ran nowhere, and `check.sh` --
documented as "if this passes, CI passes" -- ran none of them at all. Living
here they are inside `testpaths`, so `uv run pytest` collects them with no edit
to any workflow, and being `no_db` they run on the macOS leg too,
which is more coverage than they had rather than less.

**Nothing here may hand `reset_target_database` a real connection string.**
`tests/conftest.py` points `DATABASE_URL` at the session's own testcontainers
Postgres before any test module is imported, so a "harmless" reset in this file
would truncate the database the rest of the suite is using, and the failure
would surface in an unrelated test. Every database test below drives a fake
connection; `e2e/harness/database.py` takes its URL as an argument -- never from
the environment -- precisely so that this rule is easy to keep.

The environment does reach that module, and this docstring used to deny it. Two
variables now, and neither is the connection string. `E2E_ALLOW_REMOTE_RESET`
(`ALLOW_REMOTE_RESET_VAR`) is the deliberate override for a reset aimed at an
address that is not this host; `E2E_RUN_ID` (`RUN_ID_VAR`) is the run a
database's disposability mark has to name. Both widen or narrow what a reset
*does*; neither can tell it *where* to point, which is the property this file
relies on.

The negative cases below go one better than raising: each drives the real
`reset_target_database` through its `connect` seam and asserts the fake
connection was handed **no statements at all**. "It raised" and "it sent nothing"
are different claims, and only the second one is what a guard on a function that
deletes every row it can reach is actually promising.
"""

import contextlib
import json
import re
import secrets
from datetime import UTC, datetime
from typing import Any, Final

import httpx
import pytest

from e2e.harness.assertions import found, should_answer, should_be
from e2e.harness.client import TIMEOUT_SECONDS, Answer, ApiClient
from e2e.harness.database import (
    ALLOW_REMOTE_RESET_VAR,
    MARKER_MAX_AGE,
    NEVER_TRUNCATED,
    RUN_ID_VAR,
    connection_parameters,
    discover_tables,
    marker_for,
    reset_target_database,
    truncate_statement,
)
from e2e.harness.list_response import row_where, rows, total_of

BASE = "http://testserver/api"


def _client(handler, **kwargs) -> ApiClient:
    """An `ApiClient` wired to a `MockTransport`, so no server is involved."""
    return ApiClient(base_url=BASE, transport=httpx.MockTransport(handler), **kwargs)


def _json(payload, status=200):
    return lambda request: httpx.Response(status, json=payload)


def _answer(payload, status=200) -> Answer:
    """One `Answer` produced the way the client produces them."""
    return _client(_json(payload, status)).get("/anything")


# --- ApiClient -------------------------------------------------------------


def test_the_api_prefix_and_the_query_string_both_survive_the_base_url_merge():
    """The `/api` prefix is the single most load-bearing string in the suite.

       Without it every request is answered by the SPA catch-all in `app/main.py`
    -- 200 with the HTML shell for a GET, 405 for anything else -- and the whole
       suite fails at once on a status that names nothing.
    """
    seen: list[httpx.URL] = []

    def handler(request):
        seen.append(request.url)
        return httpx.Response(200, json=[])

    _client(handler).get("/entries", limit=5, offset=5)

    assert str(seen[0]) == "http://testserver/api/entries?limit=5&offset=5"


def test_the_timeout_reaches_the_wire():
    """A rule that is stated but not checked is not a rule.

    No request in the suite this replaces had a timeout at all, so a hung
    application hung the run until CI's twenty-minute kill.
    """
    seen: list[Any] = []

    def handler(request):
        seen.append(request.extensions.get("timeout"))
        return httpx.Response(200, json={})

    _client(handler).get("/health")

    assert seen[0] == dict.fromkeys(("connect", "read", "write", "pool"), TIMEOUT_SECONDS)


def test_send_puts_a_json_body_on_the_wire_with_the_method_it_was_given():
    """The verb is general -- the method is an argument -- so the next resource needs
    no new one, and every write a person authors is provable black-box with it.
    """
    seen: list[tuple[str, str, bytes]] = []

    def handler(request):
        seen.append((request.method, str(request.url), request.content))
        return httpx.Response(201, json={"id": 7})

    answer = _client(handler).send("post", "/tasks", body={"body": "call back"})

    assert seen[0][0] == "POST", "the method reaches the wire as given"
    assert seen[0][1] == "http://testserver/api/tasks", "the /api prefix survives"
    assert json.loads(seen[0][2]) == {"body": "call back"}
    assert answer.status == 201
    assert answer.payload == {"id": 7}


def test_send_refuses_a_method_it_does_not_make_rather_than_letting_the_spa_answer():
    """An unroutable verb is answered by the SPA catch-all with a 405 that names
    nothing -- the same class of failure the `/api` prefix already cost five days of
    diagnosis for. Refusing in the harness names the typo instead."""
    with pytest.raises(AssertionError, match="not a write this harness makes"):
        _client(_json({})).send("GTE", "/tasks", body={})


def test_the_client_remembers_its_own_last_answer():
    client = _client(_json({"id": "abc"}, 201))
    returned = client.send("post", "/x", body={})

    assert client.last is returned


def test_asking_for_the_last_answer_before_any_request_explains_the_missing_step():
    """The guard behind `Then` steps that read "the response".

    Reachable only because the `target` fixture hands the scenario a client that
    has made no request. It used to ask its "is the world empty" question on that
    very client, which populated `_last` before the first step ran and made this
    message unreachable in every scenario -- so a `Then` with no `When` read the
    fixture's own answer and passed. `e2e/suite/conftest.py` probes on a
    throwaway client now, and `tests/fitness/test_e2e_scenarios.py` refuses a scenario
    with no `When` statically.
    """
    client = _client(_json({}))

    with pytest.raises(AssertionError, match="no request has been made"):
        _ = client.last


def test_describe_last_never_raises_because_that_is_the_case_it_exists_for():
    """The diagnostic in the suite this replaces crashed in exactly this case.

    `_last_import_summary` asserted `context.last_import is not None` and built
    its message from `context.response.status_code` -- but when no upload had
    run, both were `None`, so the scenario reported `AttributeError: 'NoneType'
    object has no attribute 'status_code'` instead of the sentence explaining
    that a precondition step was missing.
    """
    assert _client(_json({})).describe_last() == "nothing has been sent yet"


def test_a_non_json_answer_is_described_rather_than_decoded():
    """The 405 from the SPA catch-all arrives as HTML; it must still be legible."""
    client = _client(lambda request: httpx.Response(405, text="<!doctype html><html></html>"))
    answer = client.get("/entries")

    assert answer.payload is None
    assert "not JSON" in answer.shape
    assert "405" in str(answer)


def test_an_answers_shape_names_keys_and_counts_but_never_a_value():
    """`shape` goes into failure messages, so it must not carry personal data."""
    assert _answer({"id": 1, "rows_total": 19}).shape == "object with keys: id, rows_total"
    assert _answer([{"full_name": "John Miller"}] * 19).shape == "array of 19"
    assert "Miller" not in _answer([{"full_name": "John Miller"}]).shape


def test_reading_a_record_off_a_list_answer_says_which_answer_surprised_it():
    with pytest.raises(AssertionError, match="expected a single object"):
        _answer([{"id": 1}]).record()


# --- list_response ---------------------------------------------------------


def test_rows_reads_both_wire_shapes_the_application_uses():
    """One collection endpoint answers an envelope; the others answer a bare array."""
    assert len(rows(_answer({"items": [{"id": i} for i in range(19)], "total": 19}))) == 19
    assert len(rows(_answer([{"id": i} for i in range(19)]))) == 19


def test_counting_an_envelope_cannot_silently_return_the_number_of_keys():
    """The defect this module exists for.

    `len(response.json())` over `{"items": [...], "total": 19}` is 2, and 2 is a
    plausible number of cases -- so `Then only 2 cases should be returned` could
    pass against a page of fifty.
    """
    page = {"items": [{"id": i} for i in range(50)], "total": 50}

    assert len(rows(_answer(page))) == 50


def test_the_population_count_is_read_off_the_envelope_and_not_from_the_page():
    """`total` is the one number on the envelope a page cannot imply.

    The queue screen states "N of M": N is the page, M is the book. A page of one
    out of nineteen has to answer 1 and 19, from the same response -- which is
    also the pair a regression collapses into "1 of 1".
    """
    page = _answer({"items": [{"id": 0}], "total": 19})

    assert len(rows(page)) == 1
    assert total_of(page) == 19
    assert total_of(_answer({"items": [], "total": 0})) == 0


def test_asking_a_bare_array_for_a_population_count_refuses_rather_than_guesses():
    """No fallback to the page length, deliberately.

    Answering `len(rows(answer))` when the field is absent would make the
    assertion that checks `total` pass against an endpoint that had stopped
    sending it -- the exact shape of silent-green this module exists to prevent.
    `GET /api/guestbook-entries` answers an envelope today, which is precisely why
    an envelope that arrives without its count has to raise: that is what the
    endpoint dropping the field would look like from here.
    """
    with pytest.raises(AssertionError, match="carrying a whole-population count"):
        total_of(_answer([{"author": "Anna"}]))

    with pytest.raises(AssertionError, match="carrying a whole-population count"):
        total_of(_answer({"items": [{"id": 0}]}))

    #: `bool` is an `int` in Python, so `{"total": true}` would otherwise read as
    #: a count of one.
    with pytest.raises(AssertionError, match="not a number"):
        total_of(_answer({"items": [], "total": True}))


def test_a_payload_that_is_not_a_list_at_all_raises_rather_than_reading_as_empty():
    with pytest.raises(AssertionError, match="expected a list of rows"):
        rows(_answer({"detail": "entry not found"}))


def test_row_where_matches_on_the_stringified_value_and_reports_a_miss_as_none():
    answer = _answer([{"entry_no": 101, "author": "Anna"}])

    assert row_where(answer, entry_no="101") is not None
    assert row_where(answer, entry_no="101", author="Brian") is None


# --- assertions ------------------------------------------------------------


def test_a_wrong_status_is_reported_in_the_words_of_the_rule_that_was_broken():
    answer = _answer({"detail": "nope"}, status=201)

    with pytest.raises(AssertionError, match="expected the write to be refused"):
        should_answer(answer, 409, meaning="the write to be refused")


def test_should_be_names_the_subject_so_the_message_stands_on_its_own():
    expected = re.escape("expected the signature to be 'Anna', got 'Brian'")

    with pytest.raises(AssertionError, match=expected):
        should_be("Brian", "Anna", subject="the signature")


def test_found_turns_a_missing_row_into_a_sentence_naming_the_answer():
    answer = _answer([])

    with pytest.raises(AssertionError, match="no entry signed Anna in the response"):
        found(None, subject="entry signed Anna", answer=answer)
    assert found({"id": 1}, subject="entry", answer=answer) == {"id": 1}


# --- database --------------------------------------------------------------


#: What the identity query answers for a database this run may empty. The fake
#: hands back exactly the six columns `target_identity` reads, in order, so a
#: column added to that query without a thought here fails rather than silently
#: reading `None`.
def _identity(marker: str | None, *, database: str = "app") -> tuple[Any, ...]:
    return (database, "app", "127.0.0.1", 5432, 4242, marker)


class _FakeCursor:
    def __init__(self, table_names, identity_row):
        self._table_names = table_names
        self._identity_row = identity_row
        self.executed: list[object] = []

    def execute(self, statement):
        self.executed.append(statement)

    def fetchone(self):
        return self._identity_row

    def fetchall(self):
        return [(name,) for name in self._table_names]


class _FakeConnection:
    """Mimics `with connection.cursor()`, and `with connection` around the reset.

    It records every statement it is handed, which is the whole point: the
    negative cases below assert that a refused target was sent no statement that
    deletes anything, and "it raised" alone would not have said that.
    """

    def __init__(self, table_names=(), identity_row=None):
        self.cursor_obj = _FakeCursor(table_names, identity_row)

    @contextlib.contextmanager
    def cursor(self):
        yield self.cursor_obj

    def __enter__(self):
        return self

    def __exit__(self, *_exc_info):
        return False


def _connector(connection):
    """A stand-in for `psycopg.connect` that records how it was called.

    `reset_target_database` takes this as its `connect` seam. A case that is
    refused before the connection opens leaves `calls` empty, which is a stronger
    statement than "no TRUNCATE was sent": nothing was even reached.
    """
    calls: list[dict[str, Any]] = []

    def connect(**kwargs):
        calls.append(kwargs)
        return connection

    connect.calls = calls  # type: ignore[attr-defined]
    return connect


#: Anything that removes rows or objects. Matched against every statement the
#: fake was handed, because the criterion this guard is written in is "no
#: instruction that deletes reached the server", not "an exception was raised".
_DESTRUCTIVE: Final[re.Pattern[str]] = re.compile(r"\b(truncate|delete|drop)\b", re.IGNORECASE)


def _deleting_statements(connection: _FakeConnection) -> list[str]:
    return [str(one) for one in connection.cursor_obj.executed if _DESTRUCTIVE.search(str(one))]


#: The seven ways a connection string can fail to say where it points, or point
#: somewhere this suite will not empty without being asked. Each one passes the
#: guard as it was written before this file's `reset_target_database` cases
#: existed -- weaknesses 1 to 3 of the four the audit found.
_TARGETS_THAT_ARE_NOT_PINNED_DOWN: Final[tuple[tuple[str, str, dict[str, str], str], ...]] = (
    (
        "hostaddr beside a local host",
        "postgresql://app:app@localhost:5432/app?hostaddr=203.0.113.9",
        {},
        "refusing to empty a database on 203.0.113.9",
    ),
    (
        "hostaddr and no host at all",
        "hostaddr=203.0.113.9 dbname=app user=app",
        {},
        "refusing to empty a database on 203.0.113.9",
    ),
    (
        "no address, with PGHOST in the environment",
        "dbname=app user=app",
        {"PGHOST": "db.example.com"},
        "does not locate",
    ),
    (
        "no address, with PGHOSTADDR in the environment",
        "dbname=app user=app",
        {"PGHOSTADDR": "203.0.113.9"},
        "does not locate",
    ),
    (
        "a service file this guard cannot read",
        "service=prod dbname=app",
        {},
        "named through a service file",
    ),
    (
        "a host list with one entry that is not this host",
        "host=localhost,db.example.com dbname=app",
        {},
        "refusing to empty a database on db.example.com",
    ),
    (
        "an opt-in somebody wrote as a disabler",
        "postgresql://app:app@db.example.com:5432/app",
        {ALLOW_REMOTE_RESET_VAR: "0"},
        "does not switch this guard off",
    ),
)


@pytest.mark.parametrize(
    ("dsn", "environment", "expected"),
    [case[1:] for case in _TARGETS_THAT_ARE_NOT_PINNED_DOWN],
    ids=[case[0] for case in _TARGETS_THAT_ARE_NOT_PINNED_DOWN],
)
def test_a_target_the_connection_string_does_not_pin_down_is_refused_before_any_sql(
    monkeypatch, dsn, environment, expected
):
    """Every one of these used to pass the guard and empty a database elsewhere.

    libpq ignores `host` when `hostaddr` is given, fills an absent address from
    `PGHOST` / `PGHOSTADDR`, and resolves `service=` out of a file this process
    never reads -- so reading `host` out of the string described a target that
    was not the one about to be truncated. And `not os.environ.get(...)` meant
    that `E2E_ALLOW_REMOTE_RESET=0`, written by somebody who wanted the guard ON,
    turned it off.

    The assertion is not only that it raised: the connection was never opened, so
    nothing at all reached a server.
    """
    monkeypatch.delenv(ALLOW_REMOTE_RESET_VAR, raising=False)
    for name in ("PGHOST", "PGHOSTADDR", "PGSERVICE"):
        monkeypatch.delenv(name, raising=False)
    for name, value in environment.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setenv(RUN_ID_VAR, "run-under-test")

    connection = _FakeConnection(["guestbook_entries"], _identity(marker_for("run-under-test")))
    connect = _connector(connection)

    with pytest.raises(RuntimeError, match=re.escape(expected)):
        reset_target_database(dsn, required=frozenset({"guestbook_entries"}), connect=connect)

    assert connect.calls == [], "a refused target must not even be connected to"
    assert _deleting_statements(connection) == []


#: The fourth weakness, and the one no amount of reading the connection string
#: could have caught: "local" is not "disposable". A tunnel to a shared database
#: answers on 127.0.0.1 and carries `guestbook_entries` just as a throwaway
#: container does.
_DATABASES_THAT_ARE_NOT_THIS_RUNS: Final[tuple[tuple[str, str | None, str], ...]] = (
    (
        "no mark at all, though the schema matches",
        None,
        "does not carry the mark of a disposable database",
    ),
    (
        "a mark left by another run",
        marker_for("some-earlier-run"),
        "marked disposable by a different run",
    ),
    (
        "a mark this run wrote, but long enough ago to be a shell profile's doing",
        marker_for("run-under-test", stamped_at=datetime.now(UTC) - MARKER_MAX_AGE * 2),
        "past the",
    ),
    (
        "something else's comment on the database",
        "the analytics replica -- do not point tests at this",
        "does not carry the mark of a disposable database",
    ),
)


@pytest.mark.parametrize(
    ("marker", "expected"),
    [case[1:] for case in _DATABASES_THAT_ARE_NOT_THIS_RUNS],
    ids=[case[0] for case in _DATABASES_THAT_ARE_NOT_THIS_RUNS],
)
def test_a_database_that_is_not_this_runs_to_empty_is_refused_before_any_sql(
    monkeypatch, marker, expected
):
    """The address is local, the schema is this application's, and it still refuses.

    That pair is exactly what a shared staging database behind a port-forward
    looks like, and `REQUIRED_TABLES` says yes to it. The mark is content of the
    database, so no connection string and no environment variable can produce
    one.
    """
    monkeypatch.delenv(ALLOW_REMOTE_RESET_VAR, raising=False)
    monkeypatch.setenv(RUN_ID_VAR, "run-under-test")

    connection = _FakeConnection(["guestbook_entries"], _identity(marker))
    connect = _connector(connection)

    with pytest.raises(RuntimeError, match=re.escape(expected)):
        reset_target_database(
            "postgresql+psycopg://app:app@localhost:5432/app",
            required=frozenset({"guestbook_entries"}),
            connect=connect,
        )

    assert _deleting_statements(connection) == [], (
        "the database was refused, so no instruction that removes anything may have been sent"
    )


def test_a_run_that_never_went_through_the_script_has_nothing_to_be_disposable_on(monkeypatch):
    """`E2E_RUN_ID` is minted by `./scripts/test.sh e2e`, which is also what stamps.

    A hand-run of pytest has neither, so it is told which command it skipped
    rather than emptying whatever `DATABASE_URL` points at that afternoon.
    """
    monkeypatch.delenv(RUN_ID_VAR, raising=False)
    connection = _FakeConnection(["guestbook_entries"], _identity(marker_for("anything")))
    connect = _connector(connection)

    with pytest.raises(RuntimeError, match=re.escape("scripts/test.sh e2e")):
        reset_target_database(
            "postgresql+psycopg://app:app@localhost:5432/app",
            required=frozenset({"guestbook_entries"}),
            connect=connect,
        )

    assert _deleting_statements(connection) == []


def test_a_refusal_names_the_database_the_server_said_it_was_on(monkeypatch):
    """The message has to describe the target that was REACHED, not the one typed.

    A connection string that reads as `localhost` at the end of a tunnel is the
    case this guard exists for, so a refusal quoting the string back would be
    pointing at the one piece of evidence already known to be misleading.
    """
    monkeypatch.setenv(RUN_ID_VAR, "run-under-test")
    connection = _FakeConnection(["guestbook_entries"], _identity(None, database="shared_staging"))

    with pytest.raises(RuntimeError, match="shared_staging"):
        reset_target_database(
            "postgresql+psycopg://app:app@localhost:5432/app",
            required=frozenset({"guestbook_entries"}),
            connect=_connector(connection),
        )


def test_a_marked_database_is_emptied_and_the_truncate_is_the_last_thing_sent(monkeypatch):
    """The positive control's unit half: the order this function promises.

    Every refusal happens before a statement that deletes is composed, so on the
    path where nothing refuses, the deleting statement is the last one -- after
    the identity read and after discovery. `tests/integration/test_e2e_reset.py`
    proves the same thing against a real Postgres.
    """
    monkeypatch.setenv(RUN_ID_VAR, "run-under-test")
    connection = _FakeConnection(
        ["guestbook_entries", "alembic_version"], _identity(marker_for("run-under-test"))
    )

    truncated = reset_target_database(
        "postgresql+psycopg://app:app@localhost:5432/app",
        required=frozenset({"guestbook_entries"}),
        connect=_connector(connection),
    )

    assert truncated == 1, "alembic_version is not a scenario's state"
    sent = [str(one) for one in connection.cursor_obj.executed]
    assert _DESTRUCTIVE.search(sent[-1]), "the deleting statement is the last one"
    assert len(_deleting_statements(connection)) == 1


def test_the_sqlalchemy_driver_tag_is_stripped_and_every_parameter_is_named(monkeypatch):
    """`psycopg.conninfo.conninfo_to_dict` raises on `postgresql+psycopg://`.

    The message it raises names neither the tag nor the fix, so a developer
    whose `DATABASE_URL` is the one every other script uses would be told their
    connection string is invalid.

    Explicit parameters rather than a string, and that is the second half of the
    fix: `connect(dsn)` lets libpq fill everything the string did not say from
    `PGHOST`, `PGHOSTADDR` and a service file, which is a way of aiming this
    function that no reading of the string can see.
    """
    monkeypatch.delenv(ALLOW_REMOTE_RESET_VAR, raising=False)

    assert connection_parameters("postgresql+psycopg://app:app@localhost:5432/app") == {
        "user": "app",
        "password": "app",
        "host": "localhost",
        "port": "5432",
        "dbname": "app",
    }


def test_the_timeouts_this_module_sets_are_never_taken_from_the_connection_string(monkeypatch):
    """Both exist to stop a stopped database hanging the run, so both must win.

    Forwarded, they would arrive at `connect()` as duplicate keywords and raise a
    `TypeError` from inside the call, naming neither the connection string nor
    the collision.
    """
    monkeypatch.delenv(ALLOW_REMOTE_RESET_VAR, raising=False)
    parameters = connection_parameters(
        "postgresql://app:app@localhost:5432/app?connect_timeout=600&options=-c%20lock_timeout%3D0"
    )

    assert "connect_timeout" not in parameters
    assert "options" not in parameters


def test_a_non_local_target_is_refused_unless_somebody_asked_for_it_by_name(monkeypatch):
    """This function deletes every row it can reach.

    Two accepted values, and the difference between them is the point: `1` is the
    unscoped escape the documentation has always named, and the database's own
    name is consent that does not carry over to the next target somebody aims
    this at.
    """
    remote = "postgresql://app:app@db.example.com:5432/app"

    monkeypatch.delenv(ALLOW_REMOTE_RESET_VAR, raising=False)
    with pytest.raises(RuntimeError, match="refusing to empty a database"):
        connection_parameters(remote)

    monkeypatch.setenv(ALLOW_REMOTE_RESET_VAR, "1")
    assert connection_parameters(remote)["host"] == "db.example.com"

    monkeypatch.setenv(ALLOW_REMOTE_RESET_VAR, "app")
    assert connection_parameters(remote)["dbname"] == "app"

    monkeypatch.setenv(ALLOW_REMOTE_RESET_VAR, "some_other_database")
    with pytest.raises(RuntimeError, match="does not switch this guard off"):
        connection_parameters(remote)


def test_discovery_finds_the_tables_and_leaves_alembics_bookkeeping_alone():
    """Truncating `alembic_version` makes the next upgrade replay every migration."""
    connection = _FakeConnection(["alfa", "beta", "gamma", *NEVER_TRUNCATED])

    discovered = discover_tables(connection, frozenset({"alfa", "beta"}))

    assert "alembic_version" not in discovered
    assert discovered == frozenset({"alfa", "beta", "gamma"})


def test_discovery_only_asks_for_base_tables():
    """A reporting view in `public` would make TRUNCATE raise and abort the run."""
    connection = _FakeConnection(["alfa", "beta"])
    discover_tables(connection, frozenset({"alfa"}))

    statement = str(connection.cursor_obj.executed[0])
    assert "table_type = 'BASE TABLE'" in statement
    assert "table_schema = 'public'" in statement


def test_a_database_that_is_missing_the_expected_tables_is_refused():
    """The replacement for a hand-maintained list of table names.

    Discovery that cannot see them is not looking at this application's
    database, and reporting a successful reset of the wrong one is how a whole
    run comes to fail for a reason none of its assertions mentions.
    """
    connection = _FakeConnection(["something_else"])

    with pytest.raises(RuntimeError, match=r"does not look like the application's database"):
        discover_tables(connection, frozenset({"alfa", "beta"}))


def test_the_truncate_is_one_statement_over_quoted_sorted_identifiers():
    statement = truncate_statement({"gamma", "alfa", "beta"}).as_string(None)

    assert statement == 'TRUNCATE TABLE "alfa", "beta", "gamma" RESTART IDENTITY CASCADE'


def test_truncating_nothing_is_refused_rather_than_reported_as_a_reset():
    with pytest.raises(RuntimeError, match="no tables to truncate"):
        truncate_statement([])


def test_the_body_of_a_write_is_never_printed_when_it_carries_a_credential(capsys):
    """A credential reaches no log, no report and no committed artefact.

    `_log` prints the request body for a human diagnosing a failure. That is harmless
    while no write carries a secret -- and the day a product built from this template
    adds a login, one does. Printed, it is captured by pytest, attached to the failing
    test, and lands in the JUnit report CI keeps for seven days; `CLAUDE.md` forbids
    reading that file into a session for exactly this class of reason. The redaction is
    tested now rather than the day it is needed, because that day nobody will think to
    look.

    The assertion names the field, not a value: it is the *presence* of the field's
    content in the output that is refused, and a message quoting the secret in order to
    complain about it would break the same rule in the same place. The password used here
    is generated for this run so that no literal enters the repository either.

    Note what this does NOT say: nothing here forbids printing the body of a write that
    carries no credential. The diagnostic is worth keeping; what has to change is that
    it stops being unconditional.
    """
    secret = secrets.token_urlsafe(16)
    client = _client(_json({"login": "qa-agent"}, 201))

    client.send("post", "/session", body={"login": "qa-agent", "password": secret})

    printed = capsys.readouterr().out
    # The comparison is reduced to a boolean before the assert, so neither the message
    # nor pytest's own rewriting of the expression can put the value into the report.
    # An assertion that quotes the secret in order to complain about it breaks the rule
    # in the very file the next person opens.
    leaked = secret in printed
    assert not leaked, (
        "the request body was printed with the credential in it -- redact the value "
        "before printing, or do not print the body of this write at all"
    )
    assert "password" not in printed, (
        "the printed body still names the credential field, so its value is one "
        "unredacted branch away"
    )
    # And the diagnostic still says something. A redaction that prints nothing at all
    # takes away the only view a human has of a failing exchange.
    assert "POST" in printed and "/session" in printed, (
        f"the exchange was not logged at all: {printed!r}"
    )


def test_an_answer_never_carries_the_session_identifier_it_was_given():
    """The identifier is opaque and stays out of every message the suite can print.

    `Answer` already refuses the response body; `shape` names keys, never values. This
    pins that for the one response whose body is about a session, because a `Set-Cookie`
    value repeated into a failure message is the same leak by another route.
    """
    session_id = secrets.token_urlsafe(16)
    client = _client(
        lambda request: httpx.Response(
            201,
            json={"login": "qa-agent", "role": "Agent"},
            headers={"set-cookie": f"app_session={session_id}; Path=/"},
        )
    )

    answer = client.send(
        "post", "/session", body={"login": "qa-agent", "password": secrets.token_urlsafe(8)}
    )

    # Booleans again, so no failure message can repeat the identifier it is refusing.
    in_str = session_id in str(answer)
    in_shape = session_id in answer.shape
    in_description = session_id in client.describe_last()

    assert not in_str, "str(Answer) repeats the session identifier"
    assert not in_shape, "Answer.shape repeats the session identifier"
    assert not in_description, "describe_last() repeats the session identifier"

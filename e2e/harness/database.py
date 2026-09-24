"""The target's database, emptied between scenarios.

Scenarios are isolated by truncating rather than by migrating or restarting:
`TRUNCATE` costs milliseconds, touches no schema, and removes every ordering
dependency between scenarios. A failure here **aborts the run**. It used to be
swallowed, on the reasoning that Docker might be unavailable -- but a scenario
that runs against somebody else's leftovers does not fail honestly, it fails
with a wrong count in a business assertion, which reads as an application defect
and sends the reader to the wrong code. Worse, when the leftovers happen to be
compatible it passes, and a green suite that tested nothing is the one outcome a
test tool must never produce.

The tables are **discovered**, not listed. The list used to be six names in a
string, hand-maintained against a schema the roadmap is still growing; the day
`Communication`, `PaymentPromise` or `WriteOffProposal` lands, a stale list does
not fail, it silently stops isolating. `required` is the guard that replaces it:
discovery that cannot see the tables the caller named is not looking at this
application's database, and one sentence beats twenty-one wrong counts.

Every discovered table is emptied wholesale. There is no row this reset has to
spare, because there is no account to sign in as -- this template has no
authentication. A product that grows one gets a table whose bootstrap row is
infrastructure rather than a scenario's state, and that is the point at which a
"preserve these rows" step belongs here; adding it in advance would be a branch
nothing exercises.

This module connects to Postgres directly. Its predecessor shelled out to
`docker compose exec -T db psql -U app -d app`, which hardcoded the compose
service name, the role and the database, and needed the repository root as its
working directory to find `docker-compose.yml`.

**Two gates stand before the first statement that deletes anything, and only the
second one is consent.** The first (`connection_parameters`) asks whether the
connection string says unambiguously where it points and whether that address is
allowed; the second (`assert_disposable`) asks the *server*, on the very
connection that will truncate, whether this database carries THIS run's
disposability marker. The first used to be the whole guard, and it could not be:
"the host reads as local" is a statement about a string, and an SSH tunnel or a
`kubectl port-forward` to a shared database is indistinguishable from the
compose container through it. Ownership is a fact about the database, so it is
read out of the database.

No test framework in the harness.
"""

import os
from collections.abc import Callable, Iterable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Final, Protocol

import psycopg
from psycopg import sql

#: Tables a reset must leave alone. Every other base table in `public` is
#: discovered and emptied, so a name here is a claim that the rows in it are not
#: any scenario's data.
#:
#: * `alembic_version` -- Alembic's own bookkeeping. Truncating it would make the
#:   next `alembic upgrade head` replay every migration into a populated database,
#:   and the truncation is not undone: one `./scripts/test.sh e2e` would leave the
#:   developer's own Postgres needing a re-migration from empty.
#:
#: Reference data seeded by a migration belongs here too, when a schema has any.
#: This one has none -- `guestbook_entries` is entirely scenario state.
#:
#: The disposability marker is deliberately NOT a row in a table of its own, so
#: it needs no entry here. See `MARKER_SENTINEL`.
NEVER_TRUNCATED: Final[frozenset[str]] = frozenset({"alembic_version"})

#: Addresses this module will reach without being asked twice. It deletes every
#: row it can reach, so pointing it at another machine has to be a thing somebody
#: typed on purpose.
#:
#: `""` is NOT in this set, and its absence is the fix for a real hole. It used to
#: be here, meaning "a unix socket, therefore this host" -- but `.get("host", "")`
#: cannot tell a socket from a DSN that names no host at all, and a DSN that names
#: no host lets libpq take the target from `PGHOST`, `PGHOSTADDR` or `PGSERVICE`.
#: A DSN with no address is refused outright now, which costs the socket form
#: nothing that matters here: every connection string this repository produces
#: carries an explicit host.
LOCAL_HOSTS: Final[frozenset[str]] = frozenset({"localhost", "127.0.0.1", "::1"})

#: Opt out of the address guard above, for a target that is deliberately not this
#: host. **Compared by equality, never for truthiness**, and that is the whole
#: point of it: `not os.environ.get(...)` used to mean that
#: `E2E_ALLOW_REMOTE_RESET=0` -- or `false`, or `no` -- switched the protection
#: OFF, while the refusal message asked for `=1`. A variable somebody once wrote
#: into a profile as a disabler worked as an enabler.
#:
#: Two accepted values, and they do different amounts of work:
#:
#: * `1` -- consent to a non-local address, unscoped. The form `docs/` and
#:   `spec/` already name.
#: * the target database's NAME -- consent to a non-local address, scoped to that
#:   one database, so it does not carry over to the next target somebody points
#:   this at. It is also the only form `scripts/test.sh` accepts as leave to
#:   stamp a database it did not create.
#:
#: Anything else is refused with a sentence of its own rather than ignored: an
#: inherited `=0` has to be loud, because silently treating it as "unset" would
#: leave the person who wrote it believing the guard was off.
ALLOW_REMOTE_RESET_VAR: Final[str] = "E2E_ALLOW_REMOTE_RESET"

#: The unscoped value of the variable above.
ALLOW_REMOTE_RESET_ANY: Final[str] = "1"

#: This run's identity, minted by `scripts/test.sh e2e` and read back out of the
#: marker. A reset is refused when it is unset, because a hand-run that never
#: went through the script has nothing that could have stamped the database.
RUN_ID_VAR: Final[str] = "E2E_RUN_ID"

#: What a disposable database says about itself, in `COMMENT ON DATABASE`.
#:
#: A comment rather than a marker table, and that is a decision with a reason:
#: `alembic/` is the schema's only owner (`spec/design/data-model.md` § Owner of
#: the schema), so a marker table would either be created behind Alembic's back
#: or ship in a revision -- and a revision would put an `e2e_disposable` table in
#: production, which is an invitation rather than a guard. A comment is still
#: content of the database, held in a shared catalogue no client-side
#: configuration can forge, and it costs no schema change at all.
MARKER_SENTINEL: Final[str] = "sdd-e2e-disposable"

#: How long a stamp stays good for. The `run_id` comparison already refuses
#: another run's marker, so this catches the one case it cannot: an `E2E_RUN_ID`
#: left in a shell profile, which would otherwise keep a three-week-old stamp
#: alive for ever.
MARKER_MAX_AGE: Final[timedelta] = timedelta(hours=12)

#: libpq reads these when a parameter was not given explicitly, so they are a
#: second way to say where a connection points -- one no amount of reading the
#: DSN can see. Emptied around the connect and restored afterwards; the explicit
#: parameters already win, but a parameter this module does not parse would
#: otherwise still resolve from here.
LIBPQ_ENVIRONMENT: Final[tuple[str, ...]] = (
    "PGHOST",
    "PGHOSTADDR",
    "PGPORT",
    "PGDATABASE",
    "PGUSER",
    "PGSERVICE",
    "PGSERVICEFILE",
)

#: A stopped database must fail in seconds rather than on the OS TCP timeout
#: (~75s on Linux), which across thirty executed scenarios (twenty-one declarations, two of them outlines) would overrun CI's
#: `timeout-minutes: 20` and report as a hang rather than as a database error.
CONNECT_TIMEOUT_SECONDS: Final[int] = 5

#: Bounds a `TRUNCATE` waiting for ACCESS EXCLUSIVE behind a request the HTTP
#: client already gave up on.
STATEMENT_TIMEOUT_MS: Final[int] = 5_000

#: SQLAlchemy spells the driver into the scheme; libpq does not accept it.
_DRIVER_TAG: Final[str] = "+psycopg"

#: Passed to `connect()` by `open_connection` and therefore never forwarded from
#: the connection string -- see the return of `connection_parameters`.
_PARAMETERS_THIS_MODULE_SETS: Final[frozenset[str]] = frozenset({"connect_timeout", "options"})

#: Identity and marker in one round trip, on the connection that will truncate.
#: Asking the server settles `host` / `hostaddr` / `service` / `PG*` at the source,
#: because the server is the thing answering; asking on a second connection would
#: describe a different target than the one about to be emptied.
_IDENTITY_QUERY: Final[str] = (
    "SELECT current_database(), current_user, inet_server_addr(), inet_server_port(), "
    "pg_backend_pid(), shobj_description(oid, 'pg_database') "
    "FROM pg_database WHERE datname = current_database()"
)


class _Connection(Protocol):
    """Just enough of `psycopg.Connection` for this module to be testable.

    Written as a Protocol so `tests/tooling/test_e2e_harness.py` can hand this module a
    fake and assert on the discovery and the refusal without a database -- and
    without ever holding a real connection string, which inside the pytest suite
    would be the session's own testcontainers instance.
    """

    def cursor(self) -> Any: ...


@dataclass(frozen=True)
class TargetIdentity:
    """Who answered, as the server describes itself. **Material, not criterion.**

    The address is here so a refusal can name the database it actually reached
    instead of the string somebody typed. It is deliberately not part of the
    consent test: a tunnel is still a tunnel, and `127.0.0.1` at the end of one
    is a shared database wearing this host's address.
    """

    database: str
    user: str
    address: str | None
    port: int | None
    backend_pid: int
    marker: str | None

    def __str__(self) -> str:
        """No password can reach this: every field came back from the server."""
        where = f"{self.address or 'this host'}:{self.port or '?'}"
        return f"{self.database!r} as {self.user!r} on {where} (backend {self.backend_pid})"


def _consent() -> str | None:
    """The opt-in's value, refusing anything that is neither accepted form.

    Returns `None` when the variable is unset or empty -- `E2E_ALLOW_REMOTE_RESET=`
    left in a profile means "unset", and treating it as a value would refuse every
    perfectly local run.
    """
    raw = os.environ.get(ALLOW_REMOTE_RESET_VAR)
    if raw is None or raw == "":
        return None
    return raw


def _addresses(parsed: dict[str, Any]) -> list[str]:
    """Every address the DSN names, `hostaddr` included.

    libpq's rule, and the hole this closes: "If both `host` and `hostaddr` are
    specified, the value for `hostaddr` gives the server network address. The
    value for `host` is ignored." Reading `host` alone let
    `…@localhost:5432/app?hostaddr=203.0.113.9` pass as local and connect to
    `203.0.113.9`. Both keys are comma-separated lists, and every entry has to
    clear the gate: one non-local name in `host=localhost,db.example.com` is one
    non-local target.
    """
    found: list[str] = []
    for key in ("host", "hostaddr"):
        value = parsed.get(key)
        if value is None:
            continue
        found.extend(part.strip() for part in str(value).split(","))
    return [address for address in found if address]


def connection_parameters(url: str) -> dict[str, str]:
    """A SQLAlchemy URL as EXPLICIT libpq parameters, refusing an unclear target.

    Explicit parameters rather than a DSN string, because `psycopg.connect(dsn)`
    leaves everything the string did not say to be filled in from `PGHOST`,
    `PGHOSTADDR`, `PGSERVICE` and the service file -- which is a second, invisible
    way of pointing this function at a database nobody meant. Handing libpq every
    parameter by name closes that, and `_libpq_environment_ignored` closes what is
    left.

    `postgresql+psycopg://` is SQLAlchemy's spelling; `psycopg.conninfo` raises
    `ProgrammingError` on it, and the resulting message names neither the tag
    nor the fix.

    This is the gate that used to be called `libpq_dsn`, and it refuses four
    shapes it used to accept -- see `LOCAL_HOSTS` and `ALLOW_REMOTE_RESET_VAR`
    for why each one was a hole rather than a nicety.
    """
    dsn = url.replace(_DRIVER_TAG, "", 1) if _DRIVER_TAG in url else url
    try:
        parsed = psycopg.conninfo.conninfo_to_dict(dsn)
    except psycopg.Error as exc:
        raise RuntimeError(f"{url!r} is not a connection string this suite can use: {exc}") from exc

    if parsed.get("service"):
        raise RuntimeError(
            "refusing to empty a database named through a service file: `service=` puts the "
            "target in `pg_service.conf`, which this guard cannot read, so nothing here can "
            "tell whether the database about to be emptied is disposable. Name the host, "
            "port and database in the connection string instead."
        )

    addresses = _addresses(parsed)
    if not addresses:
        raise RuntimeError(
            "refusing to empty a database the connection string does not locate: it names "
            "neither `host` nor `hostaddr`, so libpq would take the target from PGHOST, "
            "PGHOSTADDR or a service file and this guard would be checking a target nobody "
            "stated. Put the host in the connection string."
        )

    consent = _consent()
    remote = sorted({address for address in addresses if address not in LOCAL_HOSTS})
    if remote:
        database = str(parsed.get("dbname", "") or "")
        if consent is None:
            raise RuntimeError(
                f"refusing to empty a database on {', '.join(remote)}: this deletes every row "
                f"it can reach, and only a local target is assumed to be disposable. Set "
                f"{ALLOW_REMOTE_RESET_VAR}={database or ALLOW_REMOTE_RESET_ANY} if that is "
                f"genuinely what you want."
            )
        if consent not in (ALLOW_REMOTE_RESET_ANY, database):
            raise RuntimeError(
                f"{ALLOW_REMOTE_RESET_VAR}={consent!r} does not switch this guard off, and it "
                f"is not being read as though it did. Remove the variable, or set it to "
                f"{ALLOW_REMOTE_RESET_ANY!r} or to {database!r} -- the database you mean to "
                f"empty on {', '.join(remote)}."
            )

    #: Every key the connection string carried, by name. `conninfo_to_dict`
    #: returns only what was written, so nothing here invents a default -- and
    #: what it does return is exactly what `connect(**params)` must be told
    #: rather than left to work out.
    #:
    #: Minus the two this module sets itself: a DSN carrying `?connect_timeout=`
    #: or `?options=` would otherwise arrive at `connect()` as a duplicate
    #: keyword and raise `TypeError` from inside the call, naming neither the
    #: connection string nor the collision. This module's values win, and they
    #: have to: both exist to stop a stopped database hanging the run.
    return {
        key: str(value)
        for key, value in parsed.items()
        if value is not None and key not in _PARAMETERS_THIS_MODULE_SETS
    }


@contextmanager
def _libpq_environment_ignored() -> Iterator[None]:
    """`PG*` emptied for the length of one connect, and put back afterwards.

    Belt and braces over the explicit parameters: those already win for every key
    the connection string carried, and this covers the keys it did not. Restored
    in a `finally` because this process is a pytest session that goes on running
    other people's tests.
    """
    saved = {name: os.environ.pop(name) for name in LIBPQ_ENVIRONMENT if name in os.environ}
    try:
        yield
    finally:
        os.environ.update(saved)


def target_identity(connection: _Connection) -> TargetIdentity:
    """Who actually answered, and what the database says about itself.

    One round trip, on the connection the caller is about to truncate. Asking a
    second connection would describe a second target.
    """
    with connection.cursor() as cursor:
        cursor.execute(_IDENTITY_QUERY)
        row = cursor.fetchone()

    if row is None:
        raise RuntimeError(
            "the server did not answer the question of which database this connection is on, "
            "so nothing here can tell whether it is disposable."
        )
    return TargetIdentity(
        database=str(row[0]),
        user=str(row[1]),
        address=None if row[2] is None else str(row[2]),
        port=None if row[3] is None else int(row[3]),
        backend_pid=int(row[4]),
        marker=None if row[5] is None else str(row[5]),
    )


def marker_for(run_id: str, *, stamped_at: datetime | None = None) -> str:
    """The sentence a disposable database carries about itself.

    Flat text rather than JSON so that `\\l+` in psql, and the refusal messages
    below, read the same way a person would write it.
    """
    when = (stamped_at or datetime.now(UTC)).astimezone(UTC)
    return f"{MARKER_SENTINEL} run_id={run_id} stamped_at={when.isoformat()}"


def _marker_fields(marker: str) -> dict[str, str]:
    """`key=value` words out of the mark, ignoring the sentinel and any prose."""
    fields: dict[str, str] = {}
    for word in marker.split():
        key, separator, value = word.partition("=")
        if separator:
            fields[key] = value
    return fields


def assert_disposable(identity: TargetIdentity, *, run_id: str | None) -> None:
    """Refuse unless this database says it is THIS run's to empty.

    **This is the consent criterion**, and the address in `identity` is not: the
    marker is content of the database, so a tunnel, a port-forward or a
    hand-written DSN cannot produce one, while all three can produce an address
    that reads as local. `required` in `discover_tables` is not the criterion
    either -- it proves the schema is this application's, which a shared staging
    database satisfies just as well as a throwaway container does.

    Every refusal names the database the server said it was on, so the reader is
    told which target was reached rather than which string was typed.
    """
    if not run_id:
        raise RuntimeError(
            f"{RUN_ID_VAR} is not set, so there is no run for a database to be disposable ON. "
            f"`./scripts/test.sh e2e` mints one and stamps the database it resolved; a "
            f"hand-run of pytest against {identity} has skipped that step."
        )

    if identity.marker is None or not identity.marker.startswith(MARKER_SENTINEL):
        raise RuntimeError(
            f"refusing to empty {identity}: it does not carry the mark of a disposable "
            f"database. Emptying it would delete every row in it, and nothing here can tell "
            f"it apart from a shared one that happens to have the same schema. "
            f"`./scripts/test.sh e2e` stamps the database it provisions itself."
        )

    fields = _marker_fields(identity.marker)
    stamped_run = fields.get("run_id", "")
    if stamped_run != run_id:
        raise RuntimeError(
            f"refusing to empty {identity}: it is marked disposable by a different run "
            f"({stamped_run or 'no run id'}), not by this one ({run_id}). A marker left by an "
            f"earlier run is not consent for this one."
        )

    raw_stamped_at = fields.get("stamped_at", "")
    try:
        stamped_at = datetime.fromisoformat(raw_stamped_at)
    except ValueError:
        raise RuntimeError(
            f"refusing to empty {identity}: its disposability mark carries no readable time "
            f"({raw_stamped_at or 'nothing'}), so there is no telling how old the claim is."
        ) from None
    if stamped_at.tzinfo is None:
        stamped_at = stamped_at.replace(tzinfo=UTC)

    age = datetime.now(UTC) - stamped_at
    if age > MARKER_MAX_AGE:
        raise RuntimeError(
            f"refusing to empty {identity}: its disposability mark is {age} old, past the "
            f"{MARKER_MAX_AGE} this suite will honour. An {RUN_ID_VAR} left in a shell "
            f"profile keeps an old stamp matching for ever; re-stamp it by letting "
            f"`./scripts/test.sh e2e` resolve the database."
        )


def mark_disposable(connection: _Connection, *, run_id: str, database: str) -> str:
    """Say, in the database itself, that this run may empty it. Returns the mark.

    Called by `scripts/e2e_database.py` on behalf of `scripts/test.sh e2e`, and
    by nothing inside the suite: a reset that stamped its own target would be
    consenting on the operator's behalf, which is the whole thing this guard
    exists to stop. The caller is the one component that knows whether the
    database is disposable -- it either provisioned it, or was told so by name.

    `database` is passed rather than read from the connection so the identifier
    that ends up in the statement is one the caller stated.
    """
    mark = marker_for(run_id)
    with connection.cursor() as cursor:
        cursor.execute(
            sql.SQL("COMMENT ON DATABASE {} IS {}").format(
                sql.Identifier(database), sql.Literal(mark)
            )
        )
    return mark


def discover_tables(connection: _Connection, required: frozenset[str]) -> frozenset[str]:
    """Every base table in `public`, minus the ones that must survive.

    `table_type = 'BASE TABLE'` is not decoration: a reporting view in the same
    schema would come back from an unfiltered query and make `TRUNCATE` raise,
    which -- because a failed reset aborts the run -- would take all twenty-one
    scenarios down with a message about a view.

    **`required` is a sanity check, not a permission.** It says "this is an
    instance of this application's schema", which a shared environment satisfies.
    `assert_disposable` is what says the instance is this run's to empty.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
        )
        found = frozenset(str(row[0]) for row in cursor.fetchall())

    missing = required - found
    if missing:
        raise RuntimeError(
            f"this does not look like the application's database: {sorted(missing)} "
            f"{'is' if len(missing) == 1 else 'are'} missing. Found: {sorted(found) or '(no tables)'}. "
            "Has it been migrated, and is DATABASE_URL the one the application is using?"
        )
    return found - NEVER_TRUNCATED


def truncate_statement(tables: Iterable[str]) -> sql.Composed:
    """One `TRUNCATE` over every table, in one statement.

    One statement rather than one per table because `CASCADE` and the foreign
    keys between these tables make any partial order wrong, and `RESTART
    IDENTITY` so a scenario's ids do not depend on how many ran before it.
    Identifiers are quoted through `psycopg.sql` even though they came from
    `information_schema`: composing SQL by concatenation is a habit, not a
    judgement call about one call site.
    """
    names = sorted(tables)
    if not names:
        raise RuntimeError("no tables to truncate -- refusing to report a reset that did nothing")
    return sql.SQL("TRUNCATE TABLE {} RESTART IDENTITY CASCADE").format(
        sql.SQL(", ").join(sql.Identifier(name) for name in names)
    )


def open_connection(url: str, *, connect: Callable[..., Any] = psycopg.connect) -> Any:
    """A connection to `url`'s database, with the target settled before it opens.

    `connect` is a seam and only a seam: `tests/tooling/test_e2e_harness.py` passes
    a fake so it can drive `reset_target_database` end to end and assert that a
    refused target received **no statements at all** -- the claim the acceptance
    criterion for this guard is written in, and one no test could make while the
    only way in was `psycopg.connect` by name.
    """
    parameters = connection_parameters(url)
    with _libpq_environment_ignored():
        return connect(
            **parameters,
            connect_timeout=CONNECT_TIMEOUT_SECONDS,
            autocommit=True,
            options=f"-c statement_timeout={STATEMENT_TIMEOUT_MS}",
        )


def reset_target_database(
    url: str,
    *,
    required: frozenset[str],
    connect: Callable[..., Any] = psycopg.connect,
) -> int:
    """Empty `url`'s database of every scenario's state. Returns tables truncated.

    The count is returned rather than logged so the caller can assert on it:
    "the reset succeeded" and "the reset found something to do" are different
    claims, and only the second one is worth anything.

    The order below is the guarantee this function makes, and it is the reason
    the identity read is not folded in with discovery: **every refusal happens
    before a statement that deletes anything is composed, let alone sent.**
    """
    with open_connection(url, connect=connect) as connection:
        assert_disposable(target_identity(connection), run_id=os.environ.get(RUN_ID_VAR))
        tables = discover_tables(connection, required)
        with connection.cursor() as cursor:
            cursor.execute(truncate_statement(tables))
    return len(tables)

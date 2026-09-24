"""Stamp a database as this end-to-end run's to empty.

`scripts/test.sh e2e` calls this once, before it starts anything, against the
database `resolve_database_url` settled on. The harness refuses to truncate a
database that does not carry the stamp (`e2e/harness/database.py` §
`assert_disposable`), so this script is the single place where a human decision
-- "that database is disposable" -- becomes a fact the harness can read.

**It is deliberately not part of the suite.** A reset that stamped its own target
would be granting itself the permission it is supposed to be asking for. The
caller here is the one component that knows: it either provisioned the database
itself through compose, or was told the database's name by somebody who typed
`E2E_ALLOW_REMOTE_RESET=<name>`.

`--consent-required` is how the caller says which of those two it is. `test.sh`
passes it whenever `APP_DB_EXTERNAL=1` -- a `DATABASE_URL` somebody else set,
which the script did not create and cannot know is disposable. The connection
string is parsed here rather than in the shell because the database's name is in
it, and a shell that splits a URL on `/` gets a query string wrong the first time
anybody adds `?sslmode=require`.

The connection is opened through the harness rather than here, so `psycopg` keeps
the single door `tests/fitness/test_e2e_isolation.py` § GATEWAYS holds it to.
"""

import argparse
import os
import pathlib
import sys

#: `uv run python scripts/e2e_database.py` puts `scripts/` on the path, not the
#: repository root, so `e2e` would not resolve. The same two lines as
#: `scripts/dump_openapi.py`, for the same reason and in the same shape.
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from e2e.harness.database import (  # noqa: E402  (import needs the path set up above)
    ALLOW_REMOTE_RESET_VAR,
    connection_parameters,
    mark_disposable,
    open_connection,
)


def _consent_covers(database: str) -> bool:
    """Has somebody named THIS database as the one they mean to have emptied?

    The database's own name, never `1`: `1` is the unscoped opt-out of the
    address guard, and carrying it over to "you may stamp anything" would put
    the two decisions back into one variable with one value -- which is how
    consent to empty one database becomes consent to empty the next.
    """
    return os.environ.get(ALLOW_REMOTE_RESET_VAR) == database


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--url",
        required=True,
        help="the database to stamp, as DATABASE_URL spells it (the SQLAlchemy form is fine)",
    )
    parser.add_argument(
        "--run-id",
        required=True,
        help="this run's identity; the harness refuses a stamp carrying any other",
    )
    parser.add_argument(
        "--consent-required",
        action="store_true",
        help=(
            "this database was not provisioned by the caller, so refuse unless "
            f"{ALLOW_REMOTE_RESET_VAR} names it"
        ),
    )
    arguments = parser.parse_args(argv)

    #: Parsed before the connection is opened, because the database's NAME is what
    #: goes into the `COMMENT ON DATABASE` identifier and it has to be the one the
    #: caller stated rather than whatever the server happens to answer.
    database = connection_parameters(arguments.url).get("dbname", "")
    if not database:
        print(
            "the connection string does not name a database, so there is nothing to stamp",
            file=sys.stderr,
        )
        return 1

    if arguments.consent_required and not _consent_covers(database):
        print(
            f"refusing to mark {database!r} disposable: DATABASE_URL was already set in this "
            f"environment, so this script did not create that database and cannot tell whether "
            f"emptying it is safe -- and the end-to-end suite empties every row it can reach, "
            f"before every scenario.\n"
            f"\n"
            f"Two ways forward:\n"
            f"  * unset DATABASE_URL, and this script provisions a throwaway Postgres itself, or\n"
            f"  * set {ALLOW_REMOTE_RESET_VAR}={database} to say you have looked at that "
            f"database and it is yours to empty.\n"
            f"\n"
            f"The second is scoped on purpose: it names one database, so it does not carry over "
            f"to the next one you point this at.",
            file=sys.stderr,
        )
        return 1

    with open_connection(arguments.url) as connection:
        mark = mark_disposable(connection, run_id=arguments.run_id, database=database)
    print(f"{database}: {mark}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

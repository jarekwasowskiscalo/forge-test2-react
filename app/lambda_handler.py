"""How AWS enters this application. Two doors, one zip.

`app/main.py` is unchanged and unaware: it builds the same ASGI application it
builds for `uvicorn`, and Mangum translates one Lambda event into one HTTP
request against it. Nothing under `app/` branches on being in Lambda except the
connection pool in `app/db/session.py`, which is a property of the runtime and
not of the application.

**`handler` and `migrate` are two functions in one deployment package**, wired to
two Lambda functions with different roles, timeouts and triggers. One artefact
because they are the same code against the same schema -- a migration built from
a different commit than the code it prepares is the failure this arrangement
exists to make unrepresentable.

`app/static/` is deliberately absent from the zip stage and production receive:
the SPA is served from S3 through the same CloudFront distribution
(`spec/design/architecture.md` § Deployment), and `app/main.py` mounts static
files only when the directory exists. That is the whole difference between the
artefacts this project ships -- what is in them, not what the code does.

A per-branch preview is the one exception, and it is an exception in the PACKAGE
rather than in the code: `scripts/package.sh --preview` builds a second zip that
does carry `app/static`, because a preview has no CloudFront distribution to serve
a second copy from. `app/main.py` needs no branch for it -- it already mounts
whatever is there.

**A third handler, `preview_maintenance`, belongs to the shared preview layer
rather than to any branch**, for a reason of ordering: at teardown a branch's own
functions are being deleted by the very destroy that would have to call one.
"""

import logging
import os
import re
from typing import TYPE_CHECKING, Any

from mangum import Mangum

from app.main import app

if TYPE_CHECKING:  # pragma: no cover - types only, never imported at runtime
    from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

#: The database role the API function logs in as, when the deployment names one.
#:
#: Set by Terraform on the migration function and on nothing else. Its absence is
#: how a local run or a test of this module does nothing about roles at all.
IAM_USER_VAR = "DB_IAM_USER"

#: This branch's own database on the shared preview cluster.
#:
#: Set by Terraform on a preview's migration function and on nothing else. **Its
#: absence is what makes stage and production run exactly the code they ran before
#: previews existed** -- there is no environment name compared against a list, and
#: so no list to keep current.
PREVIEW_DATABASE_VAR = "PREVIEW_DATABASE"

#: What a per-branch preview database may be called.
#:
#: The name reaches `CREATE DATABASE "<name>"` and `DROP DATABASE "<name>"` as an
#: interpolated identifier, because identifiers cannot be bound as parameters.
#: The `preview_` prefix is inside the pattern rather than checked beside it, so
#: no accepted name can ever be the maintenance database: a caller that passed
#: `app` is refused by the same line that refuses a quote.
PREVIEW_DATABASE_PATTERN = re.compile(r"^preview_[a-z0-9_]{1,40}$")


def _checked_preview_database(name: object) -> str:
    """Return `name` if it can safely be interpolated into DDL, else raise.

    A branch name reaches this after `scripts/preview.sh` has reduced it to a
    slug, so in practice the value is machine-made. The guard is not about the
    person who pushes a branch -- they can edit this file -- but about the fact
    that a branch called `x"; DROP DATABASE app; --` would otherwise close the
    quoted identifier and mean something else entirely.
    """
    if not isinstance(name, str) or not PREVIEW_DATABASE_PATTERN.fullmatch(name):
        raise ValueError(
            f"{name!r} is not a preview database name. It becomes part of a CREATE or "
            "DROP DATABASE statement, which cannot be parameterised, so it must match "
            f"{PREVIEW_DATABASE_PATTERN.pattern}."
        )
    return name


#: The adapter, once it has been asked for. Built on first access rather than at
#: import -- see `__getattr__` below.
_adapter: Mangum | None = None


def __getattr__(name: str) -> Any:
    """Build the ASGI adapter the first time `handler` is read (PEP 562).

    **Importing an entry point must not construct a runtime**, and this module is
    imported far more often than it is invoked: `tests/conftest.py` discovers
    every module under `app/` by importing it, which is what makes the database
    rebinding work for a service added later without anybody listing it.

    Mangum's constructor calls `asyncio.get_event_loop()`, which on Python 3.12
    emits a DeprecationWarning when no loop is running -- and this project turns
    warnings into errors. So `handler = Mangum(app)` at module scope did not fail
    in Lambda; it failed in **eighty-one integration tests** that had nothing to
    do with Lambda, at fixture setup, with a message about an event loop.

    Lambda resolves its handler by importing this module and reading the
    attribute, so the adapter is built exactly when it is first needed and
    exactly once -- inside the function, where an event loop is what the runtime
    is there to provide.

    `lifespan="off"` because this application has no startup or shutdown work:
    logging is configured at import, the engine is built at import, and there is
    nothing to open or close per invocation. Left on, Mangum would run a lifespan
    protocol against an application that implements none, and pay for it on every
    cold start.
    """
    if name != "handler":
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    global _adapter
    if _adapter is None:
        _adapter = Mangum(app, lifespan="off")
    return _adapter


def migrate(event: dict[str, Any] | None = None, context: object = None) -> dict[str, Any]:
    """Apply every pending migration. The release step, invoked before the code rolls.

    **Not run on start-up**, and that is the same rule the image follows: a
    container that migrates as it boots races every other replica booting beside
    it, and two Alembic runs against one database is how a half-applied schema
    happens. Here the race would be worse -- Lambda can start a hundred execution
    environments in a second.

    So this is a separate function with a separate role, invoked once by
    `scripts/deploy.sh` and by the deployment workflow, and the code only rolls
    after it returns. The order matters in one direction: new code against an old
    schema asks for a column that does not exist, while old code against a new
    schema simply ignores it.

    It also **grants the API function its login**, when `DB_IAM_USER` names one.
    That is here rather than in a hand-run `psql` because there is no hand to run
    it with: the cluster has no public address, and this function is the only
    thing in the account that can both reach it and perform DDL. A step nobody
    can perform is a step that does not get performed.

    Returns what it did rather than only succeeding, so the caller can print a
    line worth reading in a deploy log. Raises on failure -- a migration that
    reported success it did not have would be the worst outcome available here.
    """
    # Imported inside the function, not at module scope: `handler` above is the
    # hot path and pays for every import in this module on a cold start, while
    # Alembic is only ever needed by the release step. The two share a zip; they
    # should not share a start-up cost.
    from alembic.config import Config
    from sqlalchemy import create_engine
    from sqlalchemy.engine import make_url
    from sqlalchemy.pool import NullPool

    from alembic import command
    from app.db.alembic_url import for_alembic_config
    from app.db.iam_auth import dsn_without_password
    from app.db.session import DATABASE_URL, engine

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config = Config(os.path.join(root, "alembic.ini"))
    # `script_location` is relative to `alembic.ini`'s own directory in the repo;
    # in the zip that directory is the package root and the same relative path
    # resolves. Set explicitly anyway, because a migration that cannot find its
    # revisions reports "target database is not up to date" -- a sentence about
    # the database, when the fault is the path.
    config.set_main_option("script_location", os.path.join(root, "alembic"))

    # A preview migrates its OWN database, which does not exist yet. Everything
    # else migrates the one its URL already names and takes neither branch below.
    preview = os.environ.get(PREVIEW_DATABASE_VAR)
    target_url = DATABASE_URL
    target_engine = engine
    created = False

    try:
        if preview:
            name = _checked_preview_database(preview)
            created = _create_database_if_absent(engine, name)
            # `render_as_string(hide_password=False)`, because `str(url)` masks the
            # password as `***` -- which would connect nowhere, slowly.
            target_url = (
                make_url(DATABASE_URL).set(database=name).render_as_string(hide_password=False)
            )
            # NullPool: this engine exists for one release step and is disposed of
            # below. A pool would hold connections open against a cluster whose
            # whole economy is falling back to zero capacity.
            target_engine = create_engine(target_url, poolclass=NullPool)
            # `alembic/env.py` prefers this over its own fallback, so setting it is
            # the whole of how the migration is pointed at the branch's database.
            # Escaped, because a deployed URL carries a percent-encoded password and
            # ConfigParser reads `%` as an interpolation (`app/db/alembic_url.py`).
            config.set_main_option("sqlalchemy.url", for_alembic_config(target_url))

        # Against the database being migrated, never against the one this function's
        # own URL names: the grants inside are per-database.
        granted = _ensure_iam_login(target_engine)

        logger.info("applying migrations to %s", dsn_without_password(target_url))
        command.upgrade(config, "head")
        logger.info("migrations applied")
        return {
            "status": "ok",
            "target": "head",
            "iam_user": granted,
            "database": preview or "",
            "created": created,
        }
    finally:
        if target_engine is not engine:
            target_engine.dispose()


def _create_database_if_absent(engine: Engine, name: str) -> bool:
    """Create a preview's database on the shared cluster. Returns whether it had to.

    Idempotent, because a preview is redeployed on every push to its branch and
    only the first of those finds nothing there.

    **AUTOCOMMIT, not `engine.begin()`.** `CREATE DATABASE` cannot run inside a
    transaction block and `begin()` opens one -- so the obvious spelling fails with
    a message about transactions, on the one path nobody can try locally.
    """
    from sqlalchemy import text

    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        exists = connection.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": name}
        ).scalar()
        if exists:
            return False
        logger.info("creating preview database %s", name)
        connection.execute(text(f'CREATE DATABASE "{name}"'))
    return True


def _ensure_iam_login(engine: Engine) -> str | None:
    """Make sure the API function's database role exists and may log in with a token.

    Returns the role's name, or `None` when the deployment named none.

    **The engine is a parameter rather than an import**, and that is not style. A
    Postgres role is cluster-wide, but `GRANT CONNECT ON DATABASE`, `GRANT USAGE
    ON SCHEMA` and `ALTER DEFAULT PRIVILEGES` are per-database and take effect on
    whichever database the connection is attached to. Issued over the wrong
    connection they succeed, grant nothing that matters, and leave the API
    function unable to read a single row -- which is exactly what a preview needs
    them not to do, since a preview's database is not the one this function's own
    `DATABASE_URL` names.

    **Idempotent by construction**, because it runs on every release: the role is
    created only if absent, and the grants are re-issued because `GRANT` of a
    privilege already held is a no-op. There is no "has this run before" flag to
    get wrong.

    The role owns nothing. It reads and writes rows in the existing schema and
    cannot create or drop a table -- so a defect in the API cannot reshape the
    database, whatever it does to the data. Schema changes come through Alembic,
    from this function, under the master user (still under `spec/design/data-model.md` § Owner of the schema).
    """
    from sqlalchemy import text

    user = os.environ.get(IAM_USER_VAR)
    if not user:
        return None

    # Identifiers cannot be bound as parameters, so the name is validated instead
    # of quoted-and-hoped. It comes from Terraform rather than from a request, so
    # this is a guard against a typo becoming a syntax error at the worst moment
    # -- not against an attacker, who has no way to set it.
    if not user.replace("_", "").isalnum():
        raise ValueError(
            f"{IAM_USER_VAR}={user!r} is not a plain identifier. It becomes part of a "
            "CREATE ROLE statement and cannot be parameterised."
        )

    with engine.begin() as connection:
        exists = connection.execute(
            text("SELECT 1 FROM pg_roles WHERE rolname = :name"), {"name": user}
        ).scalar()
        if not exists:
            logger.info("creating database role %s", user)
            connection.execute(text(f'CREATE ROLE "{user}" WITH LOGIN'))
        # `rds_iam` is what makes a signed token an acceptable password. Without
        # it the role exists, the token is valid, and the connection is refused
        # with "password authentication failed" -- which sends everybody looking
        # at the password there is not.
        connection.execute(text(f'GRANT rds_iam TO "{user}"'))
        connection.execute(
            text(f'GRANT CONNECT ON DATABASE "{connection.engine.url.database}" TO "{user}"')
        )
        connection.execute(text(f'GRANT USAGE ON SCHEMA public TO "{user}"'))
        connection.execute(
            text(f'GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO "{user}"')
        )
        # For the tables the migration below is about to create. Without this,
        # every release would grant the PREVIOUS release's tables and the new one
        # would be unreadable until the release after it.
        connection.execute(
            text(
                "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
                f'GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO "{user}"'
            )
        )
    logger.info("database role %s may log in with an IAM token", user)
    return user


def preview_maintenance(
    event: dict[str, Any] | None = None, context: object = None
) -> dict[str, Any]:
    """Drop a preview's database. The whole job of the shared preview layer's own function.

    **Why this is not the branch's own migration function.** At teardown the
    branch's functions are being deleted by the same `terraform destroy` that
    would have to call one of them, and an ordering that depends on a resource
    outliving its own deletion is an ordering that eventually does not. This
    function outlives every preview, so there is nothing to order -- and it is
    also the only way to reclaim a database whose stack somebody destroyed by
    hand, which the branch's own function by definition cannot do.

    It connects to the shared cluster's own database, never to a branch's: `DROP
    DATABASE` cannot be issued from inside the database it names. Idempotent, so
    a teardown that fires twice -- which is what a merge with auto-delete does,
    once for the closed pull request and once for the deleted branch -- succeeds
    both times.
    """
    from sqlalchemy import text

    from app.db.session import engine

    payload = event or {}
    action = payload.get("action")
    if action != "drop":
        raise ValueError(
            f"unknown action {action!r}. This function drops preview databases and "
            "does nothing else; anything it grew would run with the master password "
            "in a place nobody reviews as carefully as a migration."
        )
    name = _checked_preview_database(payload.get("database"))

    # AUTOCOMMIT, because `DROP DATABASE` cannot run inside a transaction block
    # and `engine.begin()` opens one. The failure is a clear enough message, but
    # only once somebody has run it -- which for a teardown path means once
    # somebody's preview would not go away.
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        # A database with a session still attached refuses to be dropped, and a
        # preview's last visitor is exactly the person who just closed the pull
        # request. `datname` is a value rather than an identifier, so unlike the
        # statement below it can be bound.
        connection.execute(
            text(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = :name AND pid <> pg_backend_pid()"
            ),
            {"name": name},
        )
        connection.execute(text(f'DROP DATABASE IF EXISTS "{name}"'))

    logger.info("dropped preview database %s", name)
    return {"status": "ok", "action": "drop", "database": name}

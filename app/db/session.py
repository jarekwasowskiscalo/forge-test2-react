"""Database engine and session-per-call factory.

Resolves `DATABASE_URL` once at import time and exposes a module-level
`Engine`/`SessionLocal`. Does not create or migrate any schema itself -
that is Alembic's job (see `alembic/`) - so a database's migration state
is always accurately reported.
Must not import anything from `fastapi`/`starlette`.

Resolves and honours `DATABASE_URL`; it decides nothing itself. The default
when nothing set it is the project's Postgres instance (see
docker-compose.yml). **Postgres is the only engine this application supports**
(`spec/design/architecture.md` § One engine): there is no second dialect to branch on here, and that is what
makes every test in the suite a test of the thing that runs in production.

Two facts about the runtime change how the pool is built, and both are read
from the environment rather than configured, because both are properties of
where the process happens to be running:

- `AWS_LAMBDA_FUNCTION_NAME` is set by Lambda itself. One execution
  environment serves one request at a time, so a pool larger than one holds
  connections nothing can use -- and connections are the scarce thing in front
  of a database that scales to zero.
- `DB_IAM_AUTH` asks for an IAM auth token instead of a password. The token is
  signed locally and costs no round trip, which is why the function can live in
  a VPC with no route to Secrets Manager and no NAT gateway behind it.
"""

import logging
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.iam_auth import install_iam_auth

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+psycopg://app:app@localhost:5432/app")

# The dialect, never the URL: the URL carries credentials and must not reach a
# log line at any level.
logging.getLogger(__name__).info(
    "database engine: dialect=%s", DATABASE_URL.split("://", 1)[0].split("+", 1)[0]
)

#: One request per execution environment, so one connection is the whole pool.
#: Anywhere else the default pool is right and this module has no opinion.
_IN_LAMBDA = bool(os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))
_pool_args: dict[str, int] = {"pool_size": 1, "max_overflow": 0} if _IN_LAMBDA else {}

engine = create_engine(
    DATABASE_URL,
    # Checks a pooled connection is still alive before handing it out, at the
    # cost of one round trip. Without it the first request after anything that
    # severs an idle connection -- a Postgres restart, a `docker compose
    # restart db`, a firewall idle timeout -- fails with an OperationalError
    # that the client sees as a 500, and only the *next* request recovers. The
    # daily import is exactly the kind of long-idle-then-suddenly-busy workload
    # where that happens.
    pool_pre_ping=True,
    # SURFACE REDUCTION, NOT THE RULE -- and the distinction is why this line is
    # commented rather than merely set. With it, a `StatementError` renders
    # `[SQL parameters hidden due to hide_parameters=True]` where it used to
    # render the values somebody typed. Without it there was no decision here at
    # all: the flag appeared nowhere in this repository, and `False` was
    # SQLAlchemy's default rather than anybody's choice -- ten lines above, the
    # same author had already recognised the risk for the URL.
    #
    # What it does NOT buy, so that nobody mistakes it for the guarantee:
    # `DBAPIError._message()` still returns `str(self.orig)`, so psycopg's own
    # `DETAIL: Key (author)=(...) already exists.` is untouched; the
    # `__cause__`/`__context__` chain is untouched; and an exception from
    # outside the engine -- Pydantic's `input_value='...'`, a `KeyError`'s key --
    # was never in its reach. The rule that holds article XI over a log record
    # is `ExceptionSummaryFilter` in `app/core/logging_config.py`, which sits on
    # every sink and reduces any exception to its type and its frames. This flag
    # shortens what that filter has to be right about.
    #
    # Scoped to the engine that serves requests. The migration engines
    # (`app/lambda_handler.py`, `alembic/env.py`) bind no user value -- they run
    # DDL under the master user -- so the flag would reduce nothing there.
    hide_parameters=True,
    **_pool_args,
)

# A no-op unless `DB_IAM_AUTH` asks for it, so the engine above is the same
# engine on a laptop, in the image and in the function.
install_iam_auth(engine)

SessionLocal = sessionmaker(bind=engine)

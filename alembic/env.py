from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

# Every context's models must be IMPORTED before `Base.metadata` is read, or the
# metadata Alembic compares the database against is empty and `--autogenerate`
# drafts dropping every table. `app.contexts` is the aggregate that imports every
# context (spec/design/data-model.md § Owner of the schema); `app.db.base` alone
# imports none, by design. `tests/fitness/test_alembic_env_metadata.py` replays
# this file's imports in a fresh interpreter and asks what the metadata knows.
import app.contexts  # noqa: F401
from alembic import context
from app.db.alembic_url import for_alembic_config
from app.db.base import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
#
# `disable_existing_loggers` defaults to True, which would switch off every
# logger already created and not named in alembic.ini -- root, sqlalchemy.engine
# and alembic are the only three it names. That costs nothing for a CLI run,
# where no application logger exists yet, but the test suite migrates a fresh
# database mid-session (`tests/conftest.py::fresh_database`), long after the
# service modules are imported: every `app.*` logger would go silent for the
# rest of the run, and a test asserting that a refusal logs its underlying
# library exception would see an empty log.
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

# Resolve the URL the same way the application does, unless the caller
# (CLI or a test) has already set an explicit sqlalchemy.url override.
# app.db.session is only imported lazily, as a fallback: it builds its
# Engine from DATABASE_URL at import time and caches itself in
# sys.modules, so importing it here unconditionally would freeze that
# Engine's target before a caller (e.g. a test fixture) gets a chance to
# set DATABASE_URL to its own isolated database.
db_url = config.get_main_option("sqlalchemy.url")
if not db_url:
    from app.db.session import DATABASE_URL

    db_url = DATABASE_URL
# Escaped on the way back in, because ConfigParser reads `%` as an interpolation
# and REFUSES the value outright. A deployed password is percent-encoded, so this
# line raised on every AWS environment and on no developer's machine
# (`app/db/alembic_url.py` has the whole story).
config.set_main_option("sqlalchemy.url", for_alembic_config(db_url))

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

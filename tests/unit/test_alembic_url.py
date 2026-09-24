"""A percent sign in a database URL used to stop every deployed migration.

The defect, in full: Alembic keeps its options in a `configparser.ConfigParser`,
which reads `%` as the start of an interpolation, and `Config.set_main_option`
hands the value straight to it. `alembic/env.py` sets `sqlalchemy.url` on every
run. The deployed migration function's URL carries the master password
percent-encoded -- `urlencode()` in `infra/terraform/modules/api/main.tf`, over a
password generated from `-_=+[]{}<>:?`, every one of which encodes to `%xx`.

So `env.py` raised `ValueError: invalid interpolation syntax` before applying a
single revision, on every AWS environment, with a message naming neither Alembic
nor a database. It never failed locally, because the local password is `app`.

These tests exercise the real `alembic.config.Config` rather than the one-line
helper alone: the helper is trivially correct and what actually needed proving is
that the round trip through ConfigParser gives the URL back unchanged.
"""

import pytest
from alembic.config import Config

from app.db.alembic_url import for_alembic_config
from tests._repo import REPO_ROOT

#: A URL shaped exactly like the deployed one: `=` and `[` percent-encoded, which
#: is what Terraform's urlencode() does to two of the characters the master
#: password is generated from.
DEPLOYED_SHAPE = "postgresql+psycopg://app_master:ab%3Dcd%5Bef@host.rds.amazonaws.com:5432/app"


def _config() -> Config:
    return Config(str(REPO_ROOT / "alembic.ini"))


def test_the_raw_url_is_refused_by_alembic_itself() -> None:
    """The failure this file exists for, kept executable rather than described.

    If a future Alembic or ConfigParser stops raising here, the escape below
    becomes unnecessary rather than wrong -- and this test is how anybody would
    find that out.
    """
    with pytest.raises(ValueError, match="interpolation"):
        _config().set_main_option("sqlalchemy.url", DEPLOYED_SHAPE)


def test_the_escaped_url_survives_the_round_trip() -> None:
    """What Alembic hands to SQLAlchemy has to be the URL that went in.

    Read back through `get_section`, which is what `alembic/env.py`'s
    `run_migrations_online` uses -- interpolation is applied on the way out, so an
    escape that was not exactly undone would connect somewhere else.
    """
    config = _config()
    config.set_main_option("sqlalchemy.url", for_alembic_config(DEPLOYED_SHAPE))

    section = config.get_section(config.config_ini_section, {})
    assert section["sqlalchemy.url"] == DEPLOYED_SHAPE
    assert config.get_main_option("sqlalchemy.url") == DEPLOYED_SHAPE


def test_a_url_with_no_percent_is_left_alone() -> None:
    """The local shape, which is why nobody saw the other one for so long."""
    plain = "postgresql+psycopg://app:app@localhost:5432/app"
    assert for_alembic_config(plain) == plain

    config = _config()
    config.set_main_option("sqlalchemy.url", for_alembic_config(plain))
    assert config.get_main_option("sqlalchemy.url") == plain

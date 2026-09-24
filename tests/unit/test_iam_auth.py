"""The passwordless connection seam, without an AWS account.

`app/db/iam_auth.py` runs in exactly one place -- a Lambda in a VPC -- and that
is the one place nobody can step through. So the whole of it is written to be
exercisable from here: the switch is an environment variable, the signer is
`boto3` imported inside the function, and the effect is a mutation of a plain
dictionary.

`boto3` is not a dependency of this project (it is provided by the Lambda
runtime), so these tests put a fake in `sys.modules` before the import runs.
That is not a workaround for a missing package -- it is the only way to assert
what the token is signed OVER, which is the part that goes wrong: a token signed
for the wrong host, port, user or region is refused as a bad password, and a bad
password is the least informative failure this code could have.

Why it matters that this is a unit test: the alternative is discovering the
region argument is missing during a deploy, from a connection error.
"""

import sys
from typing import Any

import pytest
from sqlalchemy import create_engine, event

from app.db import iam_auth

#: A URL with every part the signer reads spelled out, so a test can assert that
#: each one reached the token rather than a default that happened to match.
URL = "postgresql+psycopg://appuser@db.example.internal:6543/app"


class _FakeRdsClient:
    """Records what it was asked to sign, and hands back a recognisable token."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def generate_db_auth_token(self, **kwargs: Any) -> str:
        self.calls.append(kwargs)
        return "token-for-" + str(kwargs.get("DBHostname"))


class _FakeBoto3:
    def __init__(self, client: _FakeRdsClient) -> None:
        self._client = client
        self.regions: list[str | None] = []

    def client(self, service: str, region_name: str | None = None) -> _FakeRdsClient:
        assert service == "rds", f"signed a token with the {service!r} client"
        self.regions.append(region_name)
        return self._client


@pytest.fixture
def fake_boto3(monkeypatch: pytest.MonkeyPatch) -> _FakeBoto3:
    """`import boto3` inside `install_iam_auth` resolves to the fake."""
    client = _FakeRdsClient()
    module = _FakeBoto3(client)
    monkeypatch.setitem(sys.modules, "boto3", module)
    return module


@pytest.mark.parametrize("value", ["", "0", "false", "no"])
def test_it_does_nothing_at_all_unless_asked(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    """The path every laptop, every container and every test takes.

    `false` is in the set deliberately: a deployment that wrote `DB_IAM_AUTH=false`
    meaning "no" would otherwise get a token, and then fail on the connection
    rather than on the configuration.
    """
    monkeypatch.setenv(iam_auth.IAM_AUTH_VAR, value)
    # No `boto3` in `sys.modules` here, so a version that tried to import it
    # would fail rather than silently skip.
    monkeypatch.delitem(sys.modules, "boto3", raising=False)

    assert iam_auth.install_iam_auth(create_engine(URL)) is None


def test_the_token_is_signed_over_the_endpoint_the_url_names(
    monkeypatch: pytest.MonkeyPatch, fake_boto3: _FakeBoto3
) -> None:
    """Host, port, user and region, each taken from where it actually lives.

    The port is the interesting one: it is not 5432 here, and a signer that
    hardcoded the default would produce a token the database refuses without
    saying which of the four fields was wrong.
    """
    monkeypatch.setenv(iam_auth.IAM_AUTH_VAR, "1")
    monkeypatch.setenv(iam_auth.REGION_VAR, "eu-central-1")
    engine = create_engine(URL)

    signer = iam_auth.install_iam_auth(engine)
    assert signer is not None
    # Registered, not merely built: a signer nobody wired to the engine would
    # pass every assertion below and never run in production.
    assert event.contains(engine, "do_connect", signer)
    params: dict[str, Any] = {"password": "the password from the URL"}
    signer(engine.dialect, None, (), params)

    assert fake_boto3.regions == ["eu-central-1"]
    signed = fake_boto3._client.calls[-1]
    assert signed == {
        "DBHostname": "db.example.internal",
        "Port": 6543,
        "DBUsername": "appuser",
        "Region": "eu-central-1",
    }
    assert params["password"] == "token-for-db.example.internal"


def test_a_fresh_token_is_signed_for_every_connection(
    monkeypatch: pytest.MonkeyPatch, fake_boto3: _FakeBoto3
) -> None:
    """A token expires after about fifteen minutes; an execution environment does
    not. Signing once at import would work for the first connection and fail on
    the first reconnect after that -- intermittently, under load, and never on
    the machine of whoever wrote it."""
    monkeypatch.setenv(iam_auth.IAM_AUTH_VAR, "1")
    monkeypatch.setenv(iam_auth.REGION_VAR, "eu-central-1")
    engine = create_engine(URL)
    signer = iam_auth.install_iam_auth(engine)
    assert signer is not None

    for _ in range(3):
        signer(engine.dialect, None, (), {})

    assert len(fake_boto3._client.calls) == 3


def test_the_default_port_is_used_when_the_url_omits_one(
    monkeypatch: pytest.MonkeyPatch, fake_boto3: _FakeBoto3
) -> None:
    monkeypatch.setenv(iam_auth.IAM_AUTH_VAR, "1")
    monkeypatch.setenv(iam_auth.REGION_VAR, "eu-central-1")
    engine = create_engine("postgresql+psycopg://appuser@db.example.internal/app")

    signer = iam_auth.install_iam_auth(engine)
    assert signer is not None
    signer(engine.dialect, None, (), {})

    assert fake_boto3._client.calls[-1]["Port"] == 5432


def test_a_missing_region_refuses_at_setup_rather_than_at_connect(
    monkeypatch: pytest.MonkeyPatch, fake_boto3: _FakeBoto3
) -> None:
    """Loudly, at import of the engine, and not on the first request.

    A token signed for the wrong region is refused as a bad password. Failing
    here names the variable; failing there names nothing.
    """
    monkeypatch.setenv(iam_auth.IAM_AUTH_VAR, "1")
    monkeypatch.delenv(iam_auth.REGION_VAR, raising=False)

    with pytest.raises(RuntimeError, match=iam_auth.REGION_VAR):
        iam_auth.install_iam_auth(create_engine(URL))


def test_a_url_with_no_host_refuses_for_the_same_reason(
    monkeypatch: pytest.MonkeyPatch, fake_boto3: _FakeBoto3
) -> None:
    monkeypatch.setenv(iam_auth.IAM_AUTH_VAR, "1")
    monkeypatch.setenv(iam_auth.REGION_VAR, "eu-central-1")

    with pytest.raises(RuntimeError, match="no host"):
        iam_auth.install_iam_auth(create_engine("postgresql+psycopg://appuser@/app"))


def test_the_redacted_dsn_keeps_the_endpoint_and_drops_everything_else() -> None:
    """For a log line. Split on the URL's structure rather than by pattern,
    because a password may legally contain `@` -- and a regular expression that
    assumes otherwise leaks exactly the passwords that were chosen carefully."""
    redacted = iam_auth.dsn_without_password(
        "postgresql+psycopg://appuser:p%40ss@word@db.example.internal:6543/app"
    )

    assert redacted == "postgresql+psycopg://db.example.internal:6543/app"
    assert "ss" not in redacted.replace("psycopg", "")

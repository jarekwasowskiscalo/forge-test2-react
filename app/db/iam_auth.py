"""Passwordless connection to RDS, for the runtime that has no place to keep a password.

Off by default and off everywhere except AWS: a laptop, the Docker image and the
test suite all connect with the password in `DATABASE_URL` and never reach the
code below. `DB_IAM_AUTH=1` is what turns it on, and the deployment sets it.

**Why this exists rather than a secret in the environment.** The function runs in
a VPC with no route out -- no NAT gateway, no interface endpoint -- because it
needs to reach exactly one thing and that thing is inside the VPC. A password
fetched from Secrets Manager at runtime would need a route to Secrets Manager,
and that route costs money every hour whether or not anybody visits the guest
book. An IAM auth token is **signed locally**: it is a SigV4 signature over the
endpoint, the port and the user, computed from credentials the runtime already
holds. No round trip, no route, nothing to rotate.

**The token expires after fifteen minutes**, which is why this is a `do_connect`
event and not a URL built once at import. An execution environment outlives that
window comfortably, so a connection made from a URL stamped at import would fail
on the first reconnect after the token went stale -- intermittently, under load,
and never on the developer's machine.

Framework-agnostic like the rest of `app/db/`: it imports `sqlalchemy` and
`boto3` and nothing of this application's own.
"""

import logging
import os
from collections.abc import Callable
from typing import Any
from urllib.parse import urlsplit

from sqlalchemy import Engine, event

logger = logging.getLogger(__name__)

#: The switch. Present and truthy means "sign a token"; absent means "the URL
#: already carries what is needed", which is the case everywhere but AWS.
IAM_AUTH_VAR = "DB_IAM_AUTH"

#: Which region to sign for. Lambda sets `AWS_REGION` itself; the variable is
#: read rather than discovered so a mis-signed token fails with a message about
#: the region rather than about the password.
REGION_VAR = "AWS_REGION"

#: Default Postgres port, used when the URL does not spell one out.
_DEFAULT_PORT = 5432


def _wanted() -> bool:
    """Whether this deployment asked for IAM auth.

    Anything but the empty string and `0` counts as yes: the value is written by
    Terraform, and a deployment that set `DB_IAM_AUTH=false` meaning "no" would
    otherwise get a token and a confusing failure. `false` is not in the accepted
    set for exactly that reason.
    """
    value = os.environ.get(IAM_AUTH_VAR, "").strip().lower()
    return value not in ("", "0", "false", "no")


#: What a `do_connect` listener is, as far as this module is concerned: it is
#: handed the connection parameters and mutates them in place.
Signer = Callable[[Any, Any, Any, dict[str, Any]], None]


def install_iam_auth(engine: Engine) -> Signer | None:
    """Sign a fresh auth token before each connection, when asked to.

    Returns without doing anything when `DB_IAM_AUTH` is unset, which is the
    path every local run and every test takes -- so this module is dead weight
    on a laptop and cannot break one.

    **Returns the listener it registered**, or `None` when it registered none.
    Handing it back rather than keeping it private is what lets a test call it
    with a dictionary and assert what the token was signed over; the alternative
    is reaching into SQLAlchemy's dispatch internals, which couples the test to
    the shape of a library rather than to the behaviour of this module.
    """
    if not _wanted():
        return None

    url = engine.url
    host = url.host
    if host is None:
        raise RuntimeError(
            f"{IAM_AUTH_VAR} is set, but DATABASE_URL names no host to sign a token for. "
            "An IAM token is signed over the endpoint, the port and the user; without a "
            "host there is nothing to sign."
        )
    port = url.port or _DEFAULT_PORT
    user = url.username
    region = os.environ.get(REGION_VAR)
    if not region:
        raise RuntimeError(
            f"{IAM_AUTH_VAR} is set, but {REGION_VAR} is not. The token is signed for one "
            "region and a token signed for the wrong one is refused as a bad password, "
            "which is the least helpful way this could fail."
        )

    # Imported here, not at module scope: `boto3` ships with the Lambda runtime
    # and is not a dependency of this application anywhere else. A top-level
    # import would make every local run and every test pay for a package they
    # will never call.
    import boto3

    client = boto3.client("rds", region_name=region)

    @event.listens_for(engine, "do_connect")
    def _sign(_dialect: Any, _rec: Any, _args: Any, params: dict[str, Any]) -> None:
        """Replace the password with a token good for the next fifteen minutes.

        The token is returned by mutating `params` rather than by returning a
        connection: SQLAlchemy takes a `None` return as "carry on and connect
        normally", which is exactly what should happen once the password has
        been swapped.
        """
        params["password"] = client.generate_db_auth_token(
            DBHostname=host, Port=port, DBUsername=user, Region=region
        )

    logger.info("database auth: iam token, region=%s", region)
    return _sign


def dsn_without_password(url: str) -> str:
    """`url` with anything that could be a credential removed.

    For a log line or an error message. Split on the URL's own structure rather
    than by regular expression, because a password may legally contain `@` and
    a pattern that assumes otherwise leaks exactly the passwords that were
    chosen carefully.
    """
    parts = urlsplit(url)
    host = parts.hostname or ""
    port = f":{parts.port}" if parts.port else ""
    return f"{parts.scheme}://{host}{port}{parts.path}"

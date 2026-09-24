"""Where the development database answers, and who can reach it there.

Two rules about one mapping in `docker-compose.yml`, and they are separate
questions: WHICH port the database is published on, and WHICH ADDRESSES it
answers at. The file used to spell only the first, and a mapping that names no
address publishes on all of them.

## The port

`scripts/_lib.sh` derives the database URL from the port the process publishes.

The change process's clean room runs this template's cold steps inside a fresh clone,
against a Postgres published on a port the kernel just said was free -- and it tells
the clone which port by the one variable the stack profile declares
(`runtime.port_variable`, `POSTGRES_HOST_PORT`). Compose publishes on
`${POSTGRES_HOST_PORT:-5432}`; the URL the scripts connect with has to say the same,
or the clone's own scripts start a database on one port and connect to another.

It once hardcoded 5432 while compose published on the variable, a disagreement that
was invisible only because the sole caller that moved the port also supplied its own
URL -- and that URL made `ensure_db_running` file the database as external and start
nothing. This is the template's half of that repair; the process proves its own.

## The address

`- "${POSTGRES_HOST_PORT:-5432}:5432"` named no host address, and Docker publishes
such a mapping "to all host addresses (0.0.0.0 and [::])" -- its own words. The one
service carrying a credential (`app`/`app`, written into the compose file and into
docs/configuration.md) was therefore the one component on the LAN, while this repo's
own server binds 127.0.0.1 and says why. The scope is now its own variable, because
the scope and the port number are two decisions and one knob spelling both is how
moving the number silently moves the exposure.

Sources the real library in a bare shell; reads the compose file as text. No
database, no Docker.
"""

import ipaddress
import re
import subprocess
from typing import Final

from tests._repo import REPO_ROOT

PORT = 59214
"""The port from the run that exposed this: `connection refused` on 127.0.0.1:59214."""

#: The `db` service's published mapping, as `docker-compose.yml` spells it.
#:
#: Read as text rather than through a YAML parser on purpose: the defaults are
#: `${VAR:-default}` substitutions, and what this file has to prove is what the
#: WRITTEN default is. A parser would hand back whatever the environment running
#: the test happened to hold, which is the one answer that means nothing.
_DB_PUBLISH: Final = re.compile(r'^\s*- "(\$\{[^"]+)"\s*$', re.MULTILINE)


def _sourced_default_url(port: str | None) -> str:
    """`POSTGRES_URL_DEFAULT` as `scripts/_lib.sh` computes it at source time."""
    env = {"PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "HOME": str(REPO_ROOT)}
    if port is not None:
        env["POSTGRES_HOST_PORT"] = port
    done = subprocess.run(
        ["bash", "-c", '. scripts/_lib.sh >/dev/null 2>&1; printf "%s" "$POSTGRES_URL_DEFAULT"'],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    return done.stdout.strip()


def test_the_default_url_honours_the_published_port() -> None:
    """Compose publishes on `${POSTGRES_HOST_PORT:-5432}`; the URL must say the same."""
    assert _sourced_default_url(str(PORT)) == (f"postgresql+psycopg://app:app@localhost:{PORT}/app")


def test_the_default_url_is_unchanged_when_no_port_was_published() -> None:
    """Every existing caller sets nothing and must keep getting 5432."""
    assert _sourced_default_url(None) == "postgresql+psycopg://app:app@localhost:5432/app"


# --------------------------------------------------------------------------- #
# Who may reach that port -- a decision the port number does not carry
# --------------------------------------------------------------------------- #

#: `${NAME:-default}` -- the variable and the default it falls back to.
_DEFAULT: Final = re.compile(r"\$\{([A-Z_][A-Z0-9_]*):-([^}]*)\}")


def _db_published_mapping() -> str:
    """The one host mapping the `db` service publishes, exactly as written."""
    compose = (REPO_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    block = compose[compose.index("\n  db:") : compose.index("\n  app:")]
    published = _DB_PUBLISH.findall(block)
    assert len(published) == 1, f"expected one published mapping for `db`, found {published}"
    return published[0]


def _resolved(mapping: str) -> list[str]:
    """The mapping with every `${NAME:-default}` replaced by its default.

    Substituted before splitting, because `${VAR:-127.0.0.1}` contains a colon of
    its own and a naive split tears the variable in half rather than the mapping.
    """
    return _DEFAULT.sub(lambda match: match.group(2), mapping).split(":")


def _publishes_on_loopback(mapping: str) -> bool:
    """Does this mapping, at its defaults, reach no further than this machine?

    Two ways to answer no, and the first is the one that hid: a `host:container`
    mapping names no address at all, and Docker then publishes on every interface.
    A mapping that names one still has to name a loopback one.
    """
    parts = _resolved(mapping)
    if len(parts) != 3:
        return False
    try:
        return ipaddress.ip_address(parts[0]).is_loopback
    except ValueError:
        return False


def test_the_database_is_published_on_loopback_by_default() -> None:
    """A mapping with no host address publishes on every interface.

    Docker's own words: the daemon publishes "to all host addresses (0.0.0.0 and
    [::])" unless one is named. `db` is the only service carrying a credential --
    `app`/`app`, printed in the compose file and in docs/configuration.md -- so
    the absent address put the one component worth reaching on the LAN.
    """
    mapping = _db_published_mapping()
    assert _publishes_on_loopback(mapping), (
        f'`db` publishes as "{mapping}", which at its defaults resolves to '
        f"{':'.join(_resolved(mapping))} -- reachable from more than this machine."
    )


def test_the_address_and_the_port_are_two_variables() -> None:
    """One knob for both is how the scope moves when somebody moves the number.

    The clean room sets `POSTGRES_HOST_PORT` to a port it owns (`.specconf/stack.json`
    § `runtime.port_variable`). If that variable also spelled the address, every run
    that moved the port would decide the exposure too -- silently, and in passing.
    """
    declared = [name for name, _ in _DEFAULT.findall(_db_published_mapping())]
    assert declared == ["POSTGRES_HOST_BIND", "POSTGRES_HOST_PORT"], (
        f"the mapping is driven by {declared}; the address and the port each need one of "
        "their own, in that order"
    )


def test_the_loopback_check_shoots_at_the_shapes_that_are_wrong() -> None:
    """The detector comes with proof that it fires.

    A predicate that has only ever seen the repaired file cannot say whether it
    would have noticed the defect. The first case below is the mapping exactly as
    it was written before this repair.
    """
    assert not _publishes_on_loopback("${POSTGRES_HOST_PORT:-5432}:5432"), (
        "the pre-repair mapping named no address, and this check must call that reachable"
    )
    assert not _publishes_on_loopback("${POSTGRES_HOST_BIND:-0.0.0.0}:5432:5432")
    assert not _publishes_on_loopback("${POSTGRES_HOST_BIND:-192.168.1.4}:5432:5432")
    assert _publishes_on_loopback("${POSTGRES_HOST_BIND:-127.0.0.1}:5432:5432")
    assert _publishes_on_loopback("127.0.0.2:5432:5432"), "the whole 127/8 block is this machine"

"""What this running copy is, and where it is running.

Terraform has set ``APP_ENV`` on both functions since the stack was written, and
until now not one line of Python read it -- a variable that cost a deployment and
told nobody anything. It is read here, beside a new ``APP_VERSION``, so
`/api/health` can answer the two questions asked of any deployed copy: which
environment am I looking at, and which release is on it.

**Neither is a module constant.** They are read per call, so setting an
environment variable takes effect without reimporting anything. That is the trap
`app/db/session.py` documents about its own import-time engine -- avoided here
rather than repeated, because these two values are read by a probe that a test
wants to point at three different environments in three consecutive assertions.

The fallback ends at `pyproject.toml`, not at package metadata, and that is not a
preference: `scripts/package.sh` exports with ``--no-emit-project`` and the
`Dockerfile` syncs with ``--no-install-project``, so neither artefact contains
dist-info for this project and `importlib.metadata` would raise in exactly the
two places where the answer matters. In a checkout the file is there; in an
artefact ``APP_VERSION`` is set instead; and if both fail the answer says so out
loud rather than inventing a version number.
"""

import functools
import os
import pathlib
import tomllib

#: What an unset ``APP_ENV`` means. A developer's laptop, a test, a container
#: somebody started by hand -- everything that is not one of the deployed
#: environments Terraform names.
DEFAULT_ENVIRONMENT = "local"

#: What is reported when neither the environment nor the repository can say. The
#: `+unknown` is deliberate: it is a valid version string that no release will
#: ever carry, so it cannot be mistaken for one in a screenshot.
DEFAULT_VERSION = "0.0.0+unknown"

_ENVIRONMENT_VAR = "APP_ENV"
_VERSION_VAR = "APP_VERSION"


@functools.lru_cache(maxsize=1)
def _version_from_pyproject() -> str | None:
    """The version declared in the repository, or None when there is no repository.

    Cached, unlike the environment reads above: the file cannot change under a
    running process, and parsing it on every liveness probe would be a small
    cost paid forever for nothing.
    """
    path = pathlib.Path(__file__).resolve().parents[2] / "pyproject.toml"
    try:
        with path.open("rb") as handle:
            declared = tomllib.load(handle)["project"]["version"]
    except (OSError, KeyError, tomllib.TOMLDecodeError):
        return None
    return str(declared)


def environment() -> str:
    """Which deployment this is: what Terraform put in ``APP_ENV``, else `local`."""
    return os.environ.get(_ENVIRONMENT_VAR) or DEFAULT_ENVIRONMENT


def version() -> str:
    """Which release this is: ``APP_VERSION``, else the repository, else unknown."""
    return os.environ.get(_VERSION_VAR) or _version_from_pyproject() or DEFAULT_VERSION

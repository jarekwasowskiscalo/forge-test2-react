"""What goes into the deployment package, and what must not.

Two halves, split by what they cost. Resolving dependencies for another platform
needs the network and about twenty seconds, so that half is proved by CI
actually running `scripts/package.sh`. Everything else is a property of the
script's own text or of `scripts/zip_deterministically.py`, and both are checked
here in milliseconds.

**The `--no-default-groups` assertion is the one that has already been paid for
twice.** `uv export --no-dev` is an alias of `--no-group dev` and nothing more,
so with `default-groups = ["dev", "e2e"]` it leaves the end-to-end group in --
and the package built with it held playwright's browsers: 229 MB, thirty under a
limit that fails a deploy rather than a build. The Dockerfile carries a comment
about exactly this. A comment in one file did not stop the second file making
the same choice, which is why it is an assertion now.
"""

import asyncio
import os
import pathlib
import stat
import subprocess
import sys
import zipfile
from typing import Final

import pytest

from tests._repo import REPO_ROOT

PACKAGE_SH: Final[pathlib.Path] = REPO_ROOT / "scripts" / "package.sh"
ZIPPER: Final[pathlib.Path] = REPO_ROOT / "scripts" / "zip_deterministically.py"


@pytest.fixture(scope="module")
def package_text() -> str:
    return PACKAGE_SH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def package_commands(package_text: str) -> str:
    """The script with its comments taken out.

    The comment above the export names `--no-dev` in order to warn about it, and
    a rule that read the whole file would refuse the very sentence that keeps the
    mistake from coming back.
    """
    return "\n".join(
        line for line in package_text.splitlines() if not line.lstrip().startswith("#")
    )


def test_the_export_drops_every_default_group_not_only_dev(package_commands: str) -> None:
    assert "--no-default-groups" in package_commands, (
        "scripts/package.sh must export with --no-default-groups. `--no-dev` is an alias "
        "of `--no-group dev`, and this project's default-groups include `e2e` -- so "
        "`--no-dev` ships playwright to Lambda."
    )
    assert "--no-dev" not in package_commands, (
        "`--no-dev` is back in a command in scripts/package.sh. It looks like it drops "
        "the test dependencies and drops one group of them."
    )


def test_the_spa_is_excluded_from_the_function_package(package_commands: str) -> None:
    """`app/static` belongs on S3, not in the function (`spec/design/architecture.md` § Deployment).

    Not a size argument -- it is small. It is that two copies of the SPA behind
    one CloudFront distribution is two answers to what the browser gets, and the
    one nobody expects is served on whichever path routes to the function.

    Still asserted on the command rather than on the file's text, and now for a
    second reason: a preview package DOES carry the SPA, so this line is the one
    thing keeping that exception from becoming the rule.
    """
    assert "--exclude='app/static'" in package_commands


def test_the_preview_package_carries_the_spa(package_commands: str) -> None:
    """The one artefact where the two halves travel together, and the one that may.

    A per-branch preview has no CloudFront distribution, so there is no second copy
    for the function's copy to disagree with -- the function IS the distribution.
    The exception is a differently named file rather than a flag on the first one,
    so that an exception somebody can point at never quietly becomes a deleted rule.
    """
    assert "lambda-preview.zip" in package_commands
    assert 'cp -R "$WEB_DIR"/. "$LAMBDA_STAGE/app/static/"' in package_commands


def test_the_spa_reaches_the_stage_only_after_the_production_zip(
    package_commands: str,
) -> None:
    """Ordering, because the two artefacts are built from ONE stage directory.

    `lambda.zip` is written first and the SPA is copied in afterwards. Reverse
    that and the SPA is inside the artefact stage and production receive -- which
    no assertion above would catch, because both files would still exist and both
    would still be named correctly.
    """
    production = package_commands.index('zip_stage "$LAMBDA_ZIP"')
    copy = package_commands.index('cp -R "$WEB_DIR"/.')
    preview = package_commands.index('zip_stage "$LAMBDA_PREVIEW_ZIP"')

    assert production < copy < preview, (
        "the SPA is copied into the stage before the production package is zipped"
    )


def test_the_two_packages_keep_their_own_names(package_commands: str) -> None:
    """`deploy.sh` and `infra.sh` choose between them by name and nothing else.

    A rename that made the environments receive the preview artefact would deploy a
    working application -- serving a second copy of the SPA from behind CloudFront,
    which is the failure the exclusion above exists to prevent, arriving by the one
    route that skips it.
    """
    assert 'LAMBDA_ZIP="$BUILD_DIR/lambda.zip"' in package_commands
    assert 'LAMBDA_PREVIEW_ZIP="$BUILD_DIR/lambda-preview.zip"' in package_commands


def test_the_migration_handler_gets_what_it_reads(package_commands: str) -> None:
    """`app/lambda_handler.py:migrate` opens `alembic.ini` and walks `alembic/`.

    Left out, the release step fails with "target database is not up to date" --
    a sentence about the database, when the fault is a missing directory.
    """
    for needed in ("alembic", "alembic.ini"):
        assert needed in package_commands, f"{needed} is not put into the package"


def test_the_platform_is_the_functions_and_not_this_machines(package_commands: str) -> None:
    """A wheel resolved for macOS installs cleanly and cannot be imported by
    Lambda -- the failure surfaces on the first request, not in the build."""
    assert "aarch64-manylinux" in package_commands
    assert "--python-version" in package_commands


def _zip(stage: pathlib.Path, target: pathlib.Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ZIPPER)],
        env={
            **os.environ,
            "LAMBDA_STAGE": str(stage),
            "LAMBDA_ZIP": str(target),
            "ZIP_EPOCH": "1980-01-01T00:00:00",
        },
        capture_output=True,
        text=True,
        check=False,
    )


def test_two_zips_of_the_same_tree_are_byte_identical(tmp_path: pathlib.Path) -> None:
    """The whole reason the zipper exists.

    Without it a deploy cannot tell "already running this" from "something
    changed", so it uploads and rolls the function every time -- and the release
    that actually changed something looks exactly like the nine that did not.

    The two files are written with different mtimes on purpose: that is the thing
    that differs between two builds of identical content.
    """
    stage = tmp_path / "stage"
    (stage / "app").mkdir(parents=True)
    (stage / "app" / "main.py").write_text("x = 1\n", encoding="utf-8")
    (stage / "alembic.ini").write_text("[alembic]\n", encoding="utf-8")

    first = tmp_path / "one.zip"
    assert _zip(stage, first).returncode == 0
    os.utime(stage / "app" / "main.py", (0, 0))
    second = tmp_path / "two.zip"
    assert _zip(stage, second).returncode == 0

    assert first.read_bytes() == second.read_bytes()


def test_compiled_caches_never_reach_the_package(tmp_path: pathlib.Path) -> None:
    """A `.pyc` records the absolute path and the mtime of the source it came
    from -- the two things the zipper exists to normalise, smuggled in as bytes.
    """
    stage = tmp_path / "stage"
    (stage / "app" / "__pycache__").mkdir(parents=True)
    (stage / "app" / "main.py").write_text("x = 1\n", encoding="utf-8")
    (stage / "app" / "__pycache__" / "main.cpython-312.pyc").write_bytes(b"\x00\x01")

    target = tmp_path / "out.zip"
    assert _zip(stage, target).returncode == 0

    with zipfile.ZipFile(target) as archive:
        assert archive.namelist() == ["app/main.py"]


def test_entries_are_sorted_and_stamped_with_one_instant(tmp_path: pathlib.Path) -> None:
    stage = tmp_path / "stage"
    (stage / "b").mkdir(parents=True)
    (stage / "b" / "second.py").write_text("2\n", encoding="utf-8")
    (stage / "a.py").write_text("1\n", encoding="utf-8")

    target = tmp_path / "out.zip"
    assert _zip(stage, target).returncode == 0

    with zipfile.ZipFile(target) as archive:
        names = archive.namelist()
        assert names == sorted(names)
        assert {info.date_time for info in archive.infolist()} == {(1980, 1, 1, 0, 0, 0)}


def test_the_executable_bit_is_recorded_rather_than_inherited_from_umask(
    tmp_path: pathlib.Path,
) -> None:
    """Modes are part of a zip, and `umask` is part of a machine. Recording the
    source tree's own bit is what keeps the package the same on both."""
    stage = tmp_path / "stage"
    stage.mkdir()
    script = stage / "entry.sh"
    script.write_text("#!/bin/sh\n", encoding="utf-8")
    script.chmod(0o755)
    (stage / "plain.py").write_text("x = 1\n", encoding="utf-8")

    target = tmp_path / "out.zip"
    assert _zip(stage, target).returncode == 0

    with zipfile.ZipFile(target) as archive:
        modes = {info.filename: (info.external_attr >> 16) & 0o777 for info in archive.infolist()}
    assert modes["entry.sh"] & stat.S_IXUSR
    assert not modes["plain.py"] & stat.S_IXUSR


def test_an_empty_stage_refuses_rather_than_writing_an_empty_package(
    tmp_path: pathlib.Path,
) -> None:
    """An empty zip uploads and deploys perfectly, and the function cannot import
    its handler. Failing here names the cause."""
    stage = tmp_path / "stage"
    stage.mkdir()

    result = _zip(stage, tmp_path / "out.zip")

    assert result.returncode != 0
    assert "nothing to zip" in result.stderr


# --------------------------------------------------------------------------- #
# Importing the entry point must not construct a runtime
# --------------------------------------------------------------------------- #


def test_importing_the_entry_point_builds_nothing() -> None:
    """`tests/conftest.py` imports every module under `app/` by discovery, so an
    import-time side effect here is an import-time side effect in the whole suite.

    It already was one: `handler = Mangum(app)` at module scope calls
    `asyncio.get_event_loop()`, which on Python 3.12 warns when no loop is
    running -- and this project turns warnings into errors. Eighty-one
    integration tests failed at fixture setup with a message about an event loop
    and no connection to Lambda whatsoever.
    """
    import app.lambda_handler as entry_point

    assert entry_point._adapter is None, (
        "importing app.lambda_handler built the ASGI adapter. Lambda reads the "
        "attribute; nothing else should pay for it."
    )


def test_reading_the_handler_builds_it_once_and_keeps_it() -> None:
    """Lambda resolves `app.lambda_handler.handler` by importing the module and
    reading the attribute, so the lazy build has to be invisible from outside --
    and it has to be a build, not a rebuild per invocation."""
    import app.lambda_handler as entry_point

    # The loop is created and closed HERE, by the test that causes it. Mangum's
    # constructor reaches for `asyncio.get_event_loop()`, and given no current
    # loop that CREATES one and installs it as this thread's -- which nothing
    # then closes. The orphan stayed invisible for as long as nothing in this
    # suite cleared that reference; `tests/unit/test_error_response_envelope.py`
    # is the first test here to call `asyncio.run()`, and its teardown sets the
    # current loop back to None. The orphan is collected unclosed at that point,
    # and `filterwarnings = ["error"]` turns the ResourceWarning into a failure
    # of whatever happened to run last -- a failure with nothing to do with the
    # test that leaked. Installing a loop up front also means Mangum finds one
    # rather than making one, which is what Lambda's own runtime does.
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    entry_point._adapter = None
    try:
        first = entry_point.handler
        second = entry_point.handler
        assert first is second, "a second read built a second adapter"
        assert callable(first)
    finally:
        entry_point._adapter = None
        asyncio.set_event_loop(None)
        loop.close()


def test_any_other_attribute_still_raises() -> None:
    """A module-level `__getattr__` that returned something for every name would
    turn every typo into a silent success -- including `from app.lambda_handler
    import handlr`."""
    import app.lambda_handler as entry_point

    with pytest.raises(AttributeError, match="handlr"):
        _ = entry_point.handlr  # type: ignore[attr-defined]

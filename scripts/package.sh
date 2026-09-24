#!/usr/bin/env bash
# The two artefacts AWS gets: a Lambda deployment package and the built SPA.
#
# Neither is the Docker image, and that is the arrangement spec/design/architecture.md § Deployment chose. The
# image is what you run locally and in-house; these two are what a serverless
# deployment needs, and they are built from the same source and the same
# lockfile. What differs is only what ends up inside them.
#
# Both land under .sdd/build/, which is gitignored: a build output tracked in
# git is a build output that goes stale without saying so.
set -euo pipefail
# shellcheck source=scripts/_lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/_lib.sh"
cd "$REPO_ROOT"

usage() {
    cat <<'TEXT'
usage: package.sh [--lambda|--web|--preview]

  (no argument)  build both
  --lambda       the Lambda deployment package only (.sdd/build/lambda.zip)
  --web          the SPA only (.sdd/build/web/)
  --preview      both, PLUS a third artefact: .sdd/build/lambda-preview.zip,
                 which is the Lambda package with the SPA inside it

The Lambda package holds app/, alembic/, alembic.ini and the runtime
dependencies resolved FOR THE FUNCTION'S PLATFORM -- arm64 Linux, Python 3.14 --
not for this machine. It deliberately does NOT hold app/static: the SPA is
served from S3 through the same CloudFront distribution, and app/main.py mounts
static files only when the directory is there.

The preview package is the one exception, for the one environment that has no
CloudFront distribution to serve a second copy from: a per-branch preview is a
single function answering on a Function URL, so the screen has to be inside it.
It is a separate file rather than a flag on the first, so that stage and
production keep receiving exactly the artefact they received before previews
existed.

The zip is byte-identical for identical inputs: entries are sorted and every
timestamp is fixed. That is what lets a deploy say "this is already the running
version" instead of uploading and rolling for nothing.
TEXT
}

want_lambda=1
want_web=1
want_preview=0
case "${1:-}" in
    -h|--help) usage; exit 0 ;;
    --lambda) want_web=0 ;;
    --web) want_lambda=0 ;;
    --preview) want_preview=1 ;;
    "") ;;
    *) usage >&2; die "unknown option: $1" ;;
esac

#: Where both artefacts land. Under .sdd/ with the other machine-local outputs.
BUILD_DIR="$REPO_ROOT/.sdd/build"
LAMBDA_STAGE="$BUILD_DIR/lambda"
LAMBDA_ZIP="$BUILD_DIR/lambda.zip"
WEB_DIR="$BUILD_DIR/web"

#: The second function package, and the only artefact in this project where the
#: SPA and the backend travel together.
#:
#: A per-branch preview serves the screen from the function itself rather than
#: from S3 behind a CloudFront distribution -- a distribution is minutes to create
#: and longer to delete, and a bucket name is globally unique, which is the wrong
#: shape entirely for something created and destroyed per branch.
#:
#: It is a SECOND zip rather than one zip that always carries the SPA, and that is
#: deliberate. `spec/design/architecture.md` records the decision that the SPA does
#: not travel to Lambda, because two copies behind one distribution are two answers
#: to what the browser gets. A preview is an exception to that decision for one
#: environment; a second, differently named artefact is an exception somebody can
#: point at, where a quietly deleted `--exclude` would just be the rule gone. It
#: also means `lambda.zip` stays byte-for-byte what it was before previews
#: existed, so nothing added here can reach production.
LAMBDA_PREVIEW_ZIP="$BUILD_DIR/lambda-preview.zip"

#: What the function runs on. Both halves are stated rather than inherited: the
#: machine building this is very often macOS on arm64, and `psycopg[binary]`
#: resolved for macOS installs a wheel the function cannot load -- a failure that
#: surfaces as "no module named psycopg_binary" on the first request, long after
#: the build said OK.
#:
#: `_2_28` and not `2014`: Lambda's Python 3.14 runtime is Amazon Linux 2023,
#: whose glibc is far newer than manylinux2014 asks for -- and `psycopg-binary`
#: publishes no aarch64 wheel at that tag at all, so the older, "safer"-looking
#: value does not resolve rather than resolving to something worse.
LAMBDA_PLATFORM="aarch64-manylinux_2_28"
LAMBDA_PYTHON="3.14"

#: Fixed timestamp for every entry in the zip. The value is arbitrary and must
#: only be constant; 1980-01-01 is the earliest a zip can express.
ZIP_EPOCH="1980-01-01T00:00:00"

build_lambda() {
    require_uv
    step "Resolving runtime dependencies for $LAMBDA_PLATFORM (Python $LAMBDA_PYTHON)"
    rm -rf "$LAMBDA_STAGE" "$LAMBDA_ZIP"
    mkdir -p "$LAMBDA_STAGE"

    # From the lockfile, not from pyproject: the deployment package must hold
    # the versions this repository was tested with, and `--frozen` is what makes
    # this read the lockfile as it stands rather than quietly re-resolving it into
    # a different build.
    #
    # `--frozen` does NOT notice a drifted lockfile -- it means "do not update it",
    # and `--locked` is the flag that errors when the lock is out of date. The
    # comment here used to claim otherwise, which is part of why a release that
    # desynchronised `uv.lock` from `pyproject.toml` went unnoticed for so long.
    # The drift is caught by `uv sync --locked` in CI and by `release.sh` before it
    # tags anything -- never here.
    #
    # `--no-default-groups`, NOT `--no-dev`. The latter is an alias of
    # `--no-group dev` and nothing more, so with `default-groups = ["dev", "e2e"]`
    # in pyproject.toml it leaves the e2e group in -- and the package grew to
    # 229 MB with playwright's 144 MB of browsers inside it, thirty megabytes
    # under a limit that would have failed the deploy rather than the build.
    #
    # The Dockerfile already carries this warning in a comment, having paid for
    # it once. It was not enough: a warning in one file does not reach the second
    # place that makes the same choice, which is why `tests/tooling/` now asserts
    # what this package may contain.
    uv export --frozen --no-default-groups --no-emit-project --format requirements.txt \
        >"$BUILD_DIR/requirements.txt"

    # `--python-platform` makes this a cross-build: uv resolves wheels for the
    # function's architecture and refuses rather than falling back to a source
    # distribution it cannot compile for another platform.
    uv pip install \
        --requirements "$BUILD_DIR/requirements.txt" \
        --target "$LAMBDA_STAGE" \
        --python-platform "$LAMBDA_PLATFORM" \
        --python-version "$LAMBDA_PYTHON" \
        --no-installer-metadata \
        --no-compile-bytecode \
        --quiet

    step "Adding the application"
    # `app/static` is excluded, not forgotten -- see the usage text above.
    #
    # `alembic.ini` and `alembic/` come along because the migration handler in
    # app/lambda_handler.py reads them. One zip, two handlers: a migration built
    # from a different commit than the code it prepares is the thing this
    # arrangement makes unrepresentable.
    tar -cf - --exclude='app/static' --exclude='__pycache__' app alembic alembic.ini |
        tar -xf - -C "$LAMBDA_STAGE"

    zip_stage "$LAMBDA_ZIP"

    # The preview package, from the SAME stage plus the SPA. One dependency
    # resolution, one Vite build, two zips -- the second costs about a second.
    #
    # Strictly AFTER the production zip above, so that no refactor can leak
    # `app/static` into the artefact stage and production receive.
    if [ "$want_preview" -eq 1 ]; then
        [ -d "$WEB_DIR" ] ||
            die "no SPA build to put in the preview package. build_web runs first; it did not."
        step "Adding the SPA, for the preview package only"
        mkdir -p "$LAMBDA_STAGE/app/static"
        cp -R "$WEB_DIR"/. "$LAMBDA_STAGE/app/static/"
        zip_stage "$LAMBDA_PREVIEW_ZIP"
    fi
}

#: Zip whatever the stage currently holds, into the named artefact.
#:
#: Python's zipfile rather than the `zip` binary: `zip` is not installed
#: everywhere, its `-X` still records the current time, and sorting its input
#: portably is more shell than this deserves.
zip_stage() {
    local target="$1"
    step "Zipping, deterministically -> $(basename "$target")"
    LAMBDA_STAGE="$LAMBDA_STAGE" LAMBDA_ZIP="$target" ZIP_EPOCH="$ZIP_EPOCH" \
        uv run python "$REPO_ROOT/scripts/zip_deterministically.py"

    # Size and digest on one line, because both answer a question a deploy asks:
    # how much is being uploaded, and is it the same thing as last time.
    local report
    report=$(ZIP="$target" uv run python - <<'PY'
import hashlib
import os

path = os.environ["ZIP"]
digest = hashlib.sha256(open(path, "rb").read()).hexdigest()
print(f"{os.path.getsize(path) / 1e6:.1f} MB, sha256 {digest[:16]}")
PY
)
    ok "$target ($report)"
}

build_web() {
    ensure_frontend_deps
    step "Building the SPA for S3"
    rm -rf "$WEB_DIR"
    # `--outDir` overrides vite.config.ts's `../app/static`, which is where the
    # image and the local run want it. The same build, a different destination:
    # the SPA does not know or care which of the two is serving it, because the
    # API is same-origin either way (spec/design/architecture.md § Deployment).
    (cd frontend && npm run build -- --outDir "$WEB_DIR" --emptyOutDir)
    ok "$WEB_DIR"
}

mkdir -p "$BUILD_DIR"

# The SPA first, because the preview package puts it INSIDE the function package
# and cannot be built before it exists. For every other mode the order is
# immaterial: the two artefacts share no inputs.
if [ "$want_preview" -eq 1 ]; then
    want_lambda=1
    want_web=1
fi
if [ "$want_web" -eq 1 ]; then
    build_web
fi
if [ "$want_lambda" -eq 1 ]; then
    build_lambda
fi

summary "Package" 0

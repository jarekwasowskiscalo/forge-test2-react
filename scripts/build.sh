#!/usr/bin/env bash
# Compile the frontend into app/static, which is what the application serves.
set -euo pipefail
# shellcheck source=scripts/_lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/_lib.sh"
cd "$REPO_ROOT"

usage() {
    cat <<'TEXT'
usage: build.sh [--docker|--if-stale]

  (no argument)  type-check and compile the SPA into app/static
  --if-stale     compile only when app/static is missing, or older than one of the
                 sources it was built from; otherwise say what was compared and
                 do nothing. This is what test.sh runs before the UI smoke.
  --docker       ...and build the production image as sdd-app-template:local

app/static is generated and gitignored. The application serves whatever is
there; without a build, the API works and only the SPA routes 404 with a
message saying to run this.

What "stale" is measured against -- frontend/src, index.html, package.json, the
lockfile, tsconfig.json and vite.config.ts -- is declared once, in
scripts/spa_build_state.py, and read by test.sh and status.sh as well.
TEXT
}

docker_image=0
if_stale=0
case "${1:-}" in
    -h|--help) usage; exit 0 ;;
    --docker) docker_image=1 ;;
    --if-stale) if_stale=1 ;;
    "") ;;
    *) usage >&2; die "unknown option: $1" ;;
esac

# Before `ensure_frontend_deps`, not after it: the point of `--if-stale` is that a
# current bundle costs nothing, and asking for node -- possibly for an `npm ci` -- to
# decide that nothing needs doing would be most of the cost the flag exists to avoid.
if [ "$if_stale" -eq 1 ]; then
    verdict="$(spa_build_report --explain)"
    state="$(printf '%s\n' "$verdict" | sed -n '1p')"
    reason="$(printf '%s\n' "$verdict" | sed -n '2p')"
    if [ "$state" = "current" ]; then
        step "The SPA is already built"
        ok "$reason"
        summary "Build" 0
    fi
    step "Rebuilding the SPA"
    info "$reason"
fi

ensure_frontend_deps

step "Building the SPA (tsc --noEmit, then vite build)"
(cd frontend && npm run build)

# The claim is measured, not announced. This line used to read "app/static is current"
# unconditionally, which is a freshness claim nothing behind it had made -- and the
# neighbouring presence check in test.sh, which the line made look redundant, is exactly
# what served a stale bundle to the UI smoke. So the comparison runs again, over the
# bundle just written, and reports what it found.
verdict="$(spa_build_report --explain)"
state="$(printf '%s\n' "$verdict" | sed -n '1p')"
reason="$(printf '%s\n' "$verdict" | sed -n '2p')"
outcome=0
if [ "$state" = "current" ]; then
    ok "$reason"
else
    # Exit 4, not 1: `vite build` ran and wrote a bundle, so something WAS delivered --
    # it is just not a bundle of THESE sources, because somebody saved a file while the
    # compiler was running. That is precisely "did what it could and named a gap", and
    # `check.sh` files a 4 under "Not run" rather than red. Yellow goes with 4 here as it
    # does in `audit.sh`.
    outcome=4
    warn "$reason"
    info "a build input changed while the build was running -- run ./scripts/build.sh again"
fi

if [ "$docker_image" -eq 1 ]; then
    require_docker
    step "Building the production image (sdd-app-template:local)"
    # The image builds the frontend again in its own Node stage -- it must not
    # depend on the host having run the step above, or an image would ship
    # whatever happened to be in app/static.
    docker build -t sdd-app-template:local .
    ok "sdd-app-template:local"
    info "run it with: docker run --rm -p 8000:8000 sdd-app-template:local"
fi

summary "Build" "$outcome"

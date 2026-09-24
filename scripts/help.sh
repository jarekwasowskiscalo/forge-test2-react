#!/usr/bin/env bash
# Every script in this directory, and what it is for. Start here.
set -euo pipefail
# shellcheck source=scripts/_lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/_lib.sh"

cat <<'TEXT'
sdd-app-template

Every task has a script. Run it from anywhere; each one finds the repository
itself.

  FIRST RUN
    install.sh              Install uv and Docker if missing, then start the app.
                            The only script that installs anything on your machine.
    setup.sh                Install this project's dependencies only (Python,
                            frontend). Assumes uv, Docker and Node are there.
    preflight.sh            Check the machine and report. Changes nothing.
  RUNNING IT
    status.sh               What is true right now: the app on :8080 (and whether it
                            is THIS app), build freshness, Docker, the database, the
                            locks. --json for machines. Changes nothing.
    start.sh                Postgres, migrations, then the app on :8080.
    start.sh --development  ...and the Vite dev server with hot reload on :5173.
    start.sh --container    Everything in Docker: the image, its migration step and
                            Postgres. Needs no uv, no Node, no Python.
    stop.sh                 Stop the containers. Data is kept.

  TESTS
    test.sh                 Every suite: backend, frontend, e2e.
    test.sh backend         Python tests (starts its own throwaway database).
    test.sh unit            The pure rules. Seconds, no database.
    test.sh --no-db         Only the tests that need no database.
    test.sh frontend        Vitest.
    test.sh e2e             The black box: BDD scenarios plus the Playwright UI
                            smoke, one junit, against a running app. Starts one
                            if needed and builds the SPA if missing.
    test.sh ui              The UI smoke alone -- same prerequisites, faster loop.
    APP_TEST_DATABASE_URL=...  Point the backend suite at a Postgres you already
                            have. Full fidelity, no Docker, nothing skipped.

  BEFORE YOU COMMIT
    verify.sh               Verification in one place: --fast (the default), --boundary
                            (a stage boundary), --full (delivery and CI), --cold (from
                            nothing: a fresh clone, an empty toolchain, an empty
                            database), --explain. At most 40 lines of output; the detail
                            is in .sdd/reports/.
    check.sh                Every gate of this application that CI runs. CI runs more:
                            spec/design/testing.md, "What only CI can answer".
    check.sh --no-docker    Everything this machine can honestly run, and a named
                            list of what it could not. Exits 4 (INCOMPLETE).
    specs.sh                The specification gates on their own: requirements,
                            deltas, dead links, indexes, traceability.
    contracts.sh            Does the application honour the hand-written contract
                            in contracts/openapi/? Rebuilds the dump and compares.
                            Exits 4 when there is no contract to compare.
    lint.sh                 Static checks only: ruff, mypy, eslint, types.
    lint.sh --fix           ...and fix what can be fixed automatically.
    hygiene.sh              Repository hygiene only: --help, exec bits, shellcheck,
                            actionlint, nothing generated tracked in git.
    changelog.sh new "<t>"  The record of a change made OUTSIDE the SDD process:
                            one file per pull request under changelog/, saying what
                            changed and why. A change with a record in spec/changes/
                            needs none.
    changelog.sh check      The gate CI runs over it: this branch adds a well-formed
                            entry, or is exempt and prints which exemption.
    audit.sh                Known vulnerabilities, one section per ecosystem: npm
                            over frontend/package-lock.json (fails at high) and uv
                            over uv.lock (fails at any). The images, the Terraform
                            providers and the actions have no scanner and say so,
                            naming what pins them. Reads lockfiles, installs
                            nothing; exit 4 if a tool is absent.
    audit.sh --level moderate
                            ...and fail at moderate too.

  BUILDING
    build.sh                Compile the frontend into app/static.
    build.sh --if-stale     ...only when app/static is missing or older than a source.
    build.sh --docker       ...and build the production image.

  DATABASE
    db.sh migrate           Apply migrations (alembic upgrade head).
    db.sh status            Which migration is applied, and what is pending.
    db.sh revision "msg"    Create a new migration from the models.
    db.sh reset             Drop everything and migrate from scratch. Destructive.
    db.sh history           The full migration history, newest first (alembic history --verbose).
    db.sh downgrade <rev>   Step back to <rev>. Destructive for what the revisions above it added.
    db.sh shell             Open psql against the development database.
    seed.sh                 Fill an environment's guest book from golden-set/seed/,
                            through the API. start.sh does this on its own for a
                            book that is empty; this is the way to point it at a
                            preview, or to run it again by hand.

  DEPLOYMENT (AWS)
    package.sh              Build the two artefacts AWS gets: the Lambda zip and
                            the SPA. Neither is the Docker image.
    infra-check.sh          Format and type-check every Terraform root. No
                            credentials, no state -- what CI runs on every PR.
    infra.sh <env> plan     What an apply would change in stage or prod.
    infra.sh <env> apply    Make it so. Asks first, unless told --yes.
    infra.sh bootstrap ...  The one-time, per-account state bucket and roles.
    infra.sh preview-shared The network and cluster every preview borrows. Once
                            per account; it replaced dev.
    preview.sh up|down      One branch's own environment: a Lambda, a public URL
                            and a database on the shared preview cluster. Started
                            by a click in Actions, removed when the PR closes.
    deploy.sh <env>         The whole release: build, apply, MIGRATE, ROLL the
                            alias, publish the SPA, invalidate, smoke, seed. In
                            that order -- the schema goes before the code that
                            needs it, and the alias is what puts the new code
                            live. Runs from GitHub Actions; a workstation is
                            refused.

    release.sh <bump>       Cut a release: compute the next vX.Y.Z and tag the
                            trunk with it. No version is written down and no commit
                            is made -- the tag is the only record of a release, and
                            it is what asks production for a deployment.

  GENERATED CODE
    generate.sh             Regenerate the API types the frontend consumes.
                            Run after changing a Pydantic schema or the import
                            contract, and commit the result.

  HOUSEKEEPING
    clean.sh                Remove caches and build output.
    clean.sh --all          ...and the virtualenvs, node_modules and containers.
    help.sh                 This list.

The change process (SDD) is not in this list, by decision: it is independent of
these scripts and has commands of its own (sdd-specs, sdd-verify, sdd-engine,
sdd-retro, sdd-tests, sdd-lint, sdd-preview-mock -- each answers --help), a README
in the marketplace that ships it, and CI of its own. Nothing here calls it, imports it
or names its files; what it calls of these scripts is the script contract.

Add --help to any of them for its own options. Scripts whose name starts with
an underscore are internal (_lib.sh is sourced, _install-docker.sh is called by
install.sh) and are not called directly. The .py files beside them are helpers the
.sh scripts run and are not listed either: the glob hygiene.sh checks is scripts/*.sh.
TEXT

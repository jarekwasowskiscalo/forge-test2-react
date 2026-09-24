#!/usr/bin/env bash
# The development database: migrate it, inspect it, or throw it away.
#
# Alembic owns the schema. The application never calls create_all(), so what a
# database contains is always exactly what the migrations say.
set -euo pipefail
# shellcheck source=scripts/_lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/_lib.sh"
cd "$REPO_ROOT"

usage() {
    cat <<'TEXT'
usage: db.sh <command>

  migrate            Apply every pending migration (alembic upgrade head).
  status             Which revision is applied, which one is the target, and
                     whether anything is left to apply.
  history            The full migration history, newest first.
  revision "message" Autogenerate a migration from the models. Review it before
                     committing -- autogenerate is a first draft, not an answer.
  downgrade <rev>    Move back to a revision. Also takes -1 for one step.
  reset              Drop the database and migrate from scratch. DESTRUCTIVE.
  shell              Open a SQL prompt against the development database.

These target the development Postgres, starting it through docker compose if it
is not up. Postgres is the only engine (spec/design/architecture.md § One engine); with no usable Docker and no
DATABASE_URL of your own they stop and say what to do.

A DATABASE_URL already set in this environment is honoured as it stands -- and
then `reset` and `shell` refuse, because that database is not this script's to
destroy or to reach into through a container it did not start.
TEXT
}

command="${1:-}"
shift || true

case "$command" in
    -h|--help|"") usage; exit 0 ;;

    migrate)
        require_uv; ensure_db_ready
        step "Applying migrations (alembic upgrade head)"
        uv run alembic upgrade head
        summary "Migrate" 0
        ;;

    status)
        require_uv; ensure_db_ready
        step "Applied revision"
        uv run alembic current --verbose
        # `alembic heads` lists the head of alembic/versions -- where the database
        # is going, not what is left to get there. It used to be printed under a
        # "Pending" header, so a fully migrated database reported
        # "Pending: d3f81c07ae64 (head)" and the operator either ran `db.sh
        # migrate` for nothing or believed a revision was missing. The label now
        # says what the command actually answers, and the verdict below answers
        # the question that header was pretending to.
        step "Target revision (head of alembic/versions)"
        uv run alembic heads
        step "Outstanding"
        # Alembic prints "(head)" beside the applied revision when there is
        # nothing above it -- its own marker, rather than a revision id parsed out
        # of the line by this script. Asked through `lists_line`'s sibling so that
        # an alembic which could not reach the database is not reported as a
        # database that is behind -- advice to migrate a server that is not there.
        at_head=0
        lists_match '\(head\)' uv run alembic current 2>/dev/null || at_head=$?
        case "$at_head" in
            0) ok "nothing to apply -- the database is at head" ;;
            1) warn "the database is behind head -- run: db.sh migrate" ;;
            *) die "alembic could not read the applied revision, so nothing is known about what is left. Run: uv run alembic current" ;;
        esac
        ;;

    history)
        require_uv
        uv run alembic history --verbose
        ;;

    revision)
        [ $# -ge 1 ] || die 'a message is required: db.sh revision "add reports table"'
        require_uv; ensure_db_ready
        step "Autogenerating a migration"
        # --autogenerate diffs the models against the live database, so the
        # database has to be at head first or the diff describes the wrong gap.
        uv run alembic upgrade head
        uv run alembic revision --autogenerate -m "$1"
        warn "read the generated file before committing: autogenerate misses"
        warn "server defaults, index predicates and anything it cannot see in the models"
        ;;

    downgrade)
        [ $# -ge 1 ] || die "a target revision is required: db.sh downgrade -1"
        require_uv; ensure_db_ready
        step "Downgrading to $1"
        uv run alembic downgrade "$1"
        ;;

    reset)
        require_uv
        # Resolved before the warning, so the warning can name which of the two
        # databases is about to be destroyed. This command deletes data; being
        # told the target afterwards is no use.
        resolve_database_url
        [ "${APP_DB_EXTERNAL:-0}" = "1" ] &&
            die "DATABASE_URL names a database this script did not create, and reset
    destroys the volume behind it. Drop that database yourself, or unset
    DATABASE_URL to reset the project's own Postgres."
        warn "this deletes every row in $DATABASE_URL"
        step "Removing the database volume"
        docker compose down -v
        step "Starting a fresh Postgres"
        docker compose up -d --wait db
        step "Applying migrations"
        uv run alembic upgrade head
        summary "Reset" 0
        ;;

    shell)
        resolve_database_url
        [ "${APP_DB_EXTERNAL:-0}" = "1" ] &&
            die "DATABASE_URL names a database outside docker compose, so there is no
    container to open a prompt in. Reach it with your own client:
    psql \"\$DATABASE_URL\""
        ensure_db_running
        step "psql -- \\q to leave"
        docker compose exec db psql -U app -d app
        ;;

    *) usage >&2; die "unknown command: $command" ;;
esac

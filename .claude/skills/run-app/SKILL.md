---
name: run-app
description: Use when the user asks to start, run, restart or stop the sdd-app-template application - "start the application", "run the app", "start the server", "restart", "stop the application", "stop it", "from scratch", or asks for the development mode with hot reload. Runs the project's own scripts; do not assemble uv/docker/alembic commands by hand.
---

# Run the application

Every operation is a script in `scripts/`. Run the script; do not reconstruct what it does.
`scripts/help.sh` lists everything.

**Measured.** Every command you run under this skill is read by the session audit: this
conversation's own window is inside its scope, and a command assembled by hand instead of the
script that wraps it is counted there by name. What it counts, and what to do when the process
itself is the thing in your way:
[`${CLAUDE_PLUGIN_ROOT}/skills/_shared/process-failure.md`](https://github.com/Scalo-Sales-Engineering-Consulting/claude-marketplace/blob/main/plugins/forge/skills/_shared/process-failure.md).
This is the half of a session that can file, so a fault met here is filed when it is met rather
than at the end of the session — the `fault-report` skill does it.

## First: ask the machine, never your memory

```bash
./scripts/status.sh --json
```

Read-only; it reports what is installed, what is
running on the application's port **and whether it is this application** — `ours`, beside the
`pid`, `user`, `command` and `started` of whoever holds it — whether the served build is
stale, which database exists, and the locks. The port is `APP_PORT`, so it follows
`--port N` rather than always meaning 8080. Then follow `advice[]`, in order:

| `advice[].code` | What you do |
|---|---|
| `NOT_INSTALLED` | `./scripts/setup.sh` first. |
| `DOCKER_DOWN` | There is nothing to fall back to — the application runs on Postgres only. Report the script's own error verbatim; it names the two ways forward (start Docker, or point `DATABASE_URL` at a Postgres that exists). |
| `ALREADY_RUNNING_HEALTHY` | Nothing to start — say so. Restart (`./scripts/stop.sh`, then start) only when the user wants new code or the detail says the served build is stale. |
| `APP_STARTING` | This checkout's own application holds the port and has not answered `/api/health` yet. **Wait and keep polling** — a start still warming up looks exactly like a stranger on the port, and this is the report telling the two apart. Only if it never answers: `./scripts/stop.sh`, then start again. |
| `PORT_SQUATTER` | A process this checkout did not start holds the port — the JSON names it (`pid`, `user`, `command`, `started`) and says so in `ours`. Any result read off that port is about the wrong program. **Take the free port the advice offers** (`./scripts/start.sh --port N`): it costs nothing and touches nobody's work. To stop it instead, **ask the user** about *that named process* and quote what the JSON says about it — it may be their editor, their own database, or a colleague's session. Never end a process this report could not attribute, and never on `ours: null`, which means "could not tell" and not "probably mine". |
| `BUILD_MISSING` / `BUILD_STALE` | `./scripts/build.sh` before starting — or start with `--development`, which serves sources via Vite and needs no build. |
| `DB_FRESH_CHOICE` | Data exists. **Ask the user** when they said "from scratch"/"a fresh database": keep it (just start) or `./scripts/db.sh reset` — destructive, say so in the question. Never reset unasked. |
| `GATE_LOCK_HELD` / `GATE_LOCK_STALE` | A gate run owns the machine — wait; or clear the named stale lock after confirming nothing is alive. |

## Start it

```bash
./scripts/start.sh
```

Foreground process serving <http://127.0.0.1:8080>.
**Run it with `run_in_background: true`**, then poll `http://127.0.0.1:8080/api/health`
until it answers 200 before telling the user it is up.

Note the `/api` prefix. Plain `/health` is matched by the SPA catch-all, so it answers 200
from the HTML shell whether or not the API works, and 404 forever on a checkout with no
frontend build.

## Start it with hot reload

```bash
./scripts/start.sh --development
```

Backend on :8000 with `--reload`, Vite on :5173. The user develops against :5173; requests
are same-origin through Vite's proxy, which is why there is no CORS middleware anywhere in
this repository.

## Stop it

```bash
./scripts/stop.sh
```

Stops Postgres and keeps the data. `Ctrl+C` stops only the application process and leaves
the container running, which is usually what someone wants between runs.

## When it will not start

Read the script's own error first — it names the cause and the fix. Then read the log:
the application writes `.sdd/logs/app.log`; quote its last error to the user rather than
paraphrasing. The three failures that actually happen:

- **Docker is not running.** `start.sh` stops, and says so: the application runs on
  Postgres and only on Postgres (`spec/design/architecture.md` § One engine), so there is
  nothing to fall back to. Quote its message — it names both ways forward, starting Docker
  or pointing `DATABASE_URL` at a Postgres the machine already has.
- **Port 8080 is already in use.** `status.sh` already told you who holds it and whether
  it is this app — see `APP_STARTING` and `PORT_SQUATTER` above. The cheap answer is
  `./scripts/start.sh --port N` on the free port it offers; stopping somebody else's
  process is the expensive one and needs their say-so, not yours.

## Related

- Tests: skill `run-checks`, or `./scripts/test.sh`.
- The database on its own: `./scripts/db.sh migrate|status|reset|shell`.
- No Docker on the machine at all: point `DATABASE_URL` at a Postgres you already have
  (and `APP_TEST_DATABASE_URL` for the test suite). There is no second engine to fall back
  to — `spec/design/architecture.md` § One engine says why, and `./scripts/check.sh
  --no-docker` names what it therefore cannot answer rather than reporting green.

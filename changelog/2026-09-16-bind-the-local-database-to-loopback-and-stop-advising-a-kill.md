---
date: 2026-09-16
branch: fix/local-db-loopback-and-port-ownership
pr: 48
kind: fix
---

# Bind the local database to loopback, and stop advising a kill on a process nobody identified

Closes [#29](https://github.com/Scalo-Sales-Engineering-Consulting/forge_template_python_react/issues/29).

## What changed

- `docker-compose.yml` — the `db` service publishes
  `${POSTGRES_HOST_BIND:-127.0.0.1}:${POSTGRES_HOST_PORT:-5432}:5432`. The address is new; the
  port keeps its variable and its meaning. The comment above it says why the address is
  loopback, and that widening it is an act.
- `docs/configuration.md` — a `POSTGRES_HOST_BIND` row in "What the scripts read", and a
  paragraph in "The local stack" naming the scope and stating that container mode does not use
  the published port at all.
- `scripts/app_status.py` — `APP_PORT` is read from the environment; `_listener_pid` gains
  `_process_facts`, `_compose_app_is_running`, `_listener_owner`, `_free_port_above` and
  `_describe_holder`; `probe_app_port` reports `user`, `command`, `started`, `ours` and
  `free_port` beside the pid; `advise` splits the one squatter branch into `APP_STARTING` (ours)
  and a reworded `PORT_SQUATTER` (not ours, or unknown), and reads the port from the report
  rather than from the module constant.
- `.claude/skills/run-app/SKILL.md` — the `PORT_SQUATTER` row rewritten in the shape of
  `DB_FRESH_CHOICE`, a new `APP_STARTING` row, and the two paragraphs around them that still
  said ":8080" and "a stray process by its pid".
- `tests/tooling/test_database_port.py` — three tests and a `_publishes_on_loopback` predicate,
  on top of the two that were already there.
- `tests/tooling/test_app_status.py` — `test_the_squatter_advice_names_the_pid` replaced by ten
  tests, and a `_held()` helper whose defaults are a listener nothing could identify.

## Why

Two findings from the audit of 2026-09-15 (`claude-marketplace:
audits/2026-09-15-latest/03-aplikacja-python-react.md#A48` and `02-forge-proces-i-skille.md#A45`),
both about the local development machine.

**The database answered on every interface.** `- "${POSTGRES_HOST_PORT:-5432}:5432"` names no
host address, and Docker's own documentation says the daemon then publishes "to all host
addresses (0.0.0.0 and [::])". The `db` service is the only one carrying a credential —
`app`/`app`, printed in the compose file and again in `docs/configuration.md` — so the one
component worth reaching was the one on the network. This repository already applies the
opposite rule to its own server (`scripts/run.py:31` binds `127.0.0.1`, and `scripts/start.sh`
says in as many words that `0.0.0.0` "would just put the dev server on the LAN"): the database
was the exception to a convention that was otherwise enforced, and no document named the
exposure.

**No claim is made that any machine was reachable from the internet.** The real scope of a
published port depends on the host's firewall and the daemon's settings. This is a report about
the default configuration of an artefact, not about the state of anybody's laptop.

**The `run-app` skill told the model to end a process it could not name.** The `PORT_SQUATTER`
row said "`./scripts/stop.sh` for the compose container; a stray process by its pid. Only then
start." — no ownership, no consent. The row beneath it, `DB_FRESH_CHOICE`, has always demanded
both ("**Ask the user**", "Never reset unasked"), so the skill knew the pattern and did not
apply it here.

The identification underneath could not have supported that instruction anyway:

- `_listener_pid` ran `lsof -nP -ti` and returned an integer. No command, no user, no start
  time — nothing a person could weigh.
- Its own docstring recorded that `lsof` "refuses to name another user's process". In that case
  the pid was `None`, and the advice to end "a stray process by its pid" stood unchanged over a
  pid that was not there.
- `listening-not-answering` is reached after two seconds of silence on `/api/health` — which is
  also what **this checkout's own application still starting up** looks like. The advice then
  named the pid of the very application the reader was trying to start.
- `APP_PORT: Final = 8080` never read the environment, though `scripts/_lib.sh:248` defines it
  as `APP_PORT="${APP_PORT:-8080}"` and `start.sh --port N` sets it. After `--port 8090` the
  report probed 8080, found whatever was there, and advised about it with total confidence.

## From what, to what

**Before.** One mapping that named a port and no address. One probe that returned a number. One
advice branch that covered both a stranger and our own slow start, and recommended ending the
process in either case.

**After.** The address is a variable of its own, defaulting to loopback. The probe answers *who*
— pid, user, command, start time — and, separately, *whether it is ours*. The advice branches on
that answer: our own application gets "wait"; anything else gets a free port to move to, and a
requirement to ask about that specific process before stopping it.

`ours` is three-valued, and the third value is the point. `true` and `false` are findings;
`null` is "could not tell", which is what `lsof` returns for another user's process. `null` is
read as *not ours* — never as "probably mine", which is the assumption that let the old advice
reach a process nobody had identified.

## How it works now

A stranger on the port, measured on this machine:

```json
{
  "state": "listening-not-answering", "port": 8093, "pid": 92733,
  "user": "jaroslawwasowski", "command": "lonelyserver3",
  "started": "Wed Sep 16 21:09:29 2026", "ours": false, "free_port": 8094
}
```

```
[PORT_SQUATTER] lonelyserver3 run by jaroslawwasowski (pid 92733, started Wed Sep 16
    21:09:29 2026) holds :8093 and this checkout did not start it; any result read off
    that port is about the wrong program
    -> ./scripts/start.sh --port 8094 leaves it alone -- ask the user before stopping a
       process this checkout does not own
```

Ownership is decided on the command line, not on the pid: host mode runs
`.venv/bin/python3 scripts/run.py`, and that interpreter lives inside the checkout, so the
repository's own path in the process's `argv` is proof a pid could never be. Container mode
publishes through Docker's proxy, whose command line says nothing about this checkout — so the
second signal is whether this compose project's `app` service is running.

**The command line decides ownership and never reaches the report.** `probe_database` already
publishes the *scheme* of `DATABASE_URL` and not the URL, because the rest is a credential; a
stranger's arguments are the same hazard, and can carry a password. The report gets `user`,
`command` and `started`; `argv` stays inside the module. That is Article XI applied to a
neighbour's process rather than to our own logs.

The database now publishes where it is asked to:

```
$ lsof -nP -iTCP:5492 -sTCP:LISTEN
com.docke  89797  ...  TCP 127.0.0.1:5492 (LISTEN)     # this change
com.docke  89797  ...  TCP *:5432 (LISTEN)             # a worktree still on the old file
```

## What it means for the process

For anybody running `./scripts/start.sh`, `./scripts/db.sh` or the suites: **nothing moves.**
The port is unchanged, the URL is unchanged, and `localhost` still reaches the database — the
IPv4-only publish was tested rather than assumed (see below).

Two things change for a person or an agent:

- **Reaching the development database from another machine now needs saying so**:
  `POSTGRES_HOST_BIND=0.0.0.0`. That is the one deliberate behaviour change here, and it is the
  point of the change.
- **The `run-app` skill no longer authorises stopping an unidentified process.** Where it used
  to say "a stray process by its pid", it now offers `./scripts/start.sh --port N` and requires
  the user's answer about the named process. A slow start is reported as `APP_STARTING` and is
  waited on, not killed.

`APP_STARTING` is a new `advice[].code`. The existing codes, their order and the JSON's shape
are untouched — the new fields live inside the `app_port` check, so `checks` still has its eight
keys.

## What it does not change

- **`POSTGRES_HOST_PORT` keeps its meaning and its contract.** `.specconf/stack.json`
  § `runtime.port_variable` still names it, and the clean room still sets it to a port that run
  owns. The scope is a second variable precisely so the port keeps doing one job.
- **`app` and `frontend` still publish on every interface** (`${APP_PORT:-8080}:8000` and
  `5173:5173`). Left deliberately, not overlooked: neither carries a credential, and showing a
  containerised demo to somebody on the same network is a reasonable thing to want. The finding
  was about the service holding the data.
- **No application code, no schema, no migration, no screen.** The `app/` tree is untouched.
- **`scripts/start.sh`, `scripts/stop.sh` and `scripts/_lib.sh` are untouched.** `app_status.py`
  reports; it has never started or stopped anything, and still does not. Nothing here sends a
  signal to any process.
- **`GATE_LOCK_HELD` / `GATE_LOCK_STALE` are still emitted by nothing**, for the reason recorded
  at `scripts/app_status.py`'s tail: the gate lock is the process's file, not this tree's.
- **The two existing tests in `test_database_port.py` stay.** The issue says a test that checks
  only the port number does not satisfy its criterion — which is an argument for adding the
  address, not for deleting the rule about the port.

## How it was verified

- `./scripts/test.sh tooling` — 315 collected, all green; 34 in the two modules this touched.
- `./scripts/test.sh unit` — 129 passed. `./scripts/test.sh fitness` — 252 passed, including
  the documentation gate that refuses a documented variable nothing outside `docs/` reads.
- **The new database test was seen red.** With `docker-compose.yml` returned to
  `- "${POSTGRES_HOST_PORT:-5432}:5432"`, `test_the_database_is_published_on_loopback_by_default`
  and `test_the_address_and_the_port_are_two_variables` both fail. The detector comes with proof
  that it fires, and `test_the_loopback_check_shoots_at_the_shapes_that_are_wrong` keeps that
  proof in the suite.
- **On real Docker**, `POSTGRES_HOST_PORT=5492 APP_PORT=8092 ./scripts/start.sh`: the container
  is created with `{"5432/tcp":[{"HostIp":"127.0.0.1","HostPort":"5492"}]}`, the host listener
  is `TCP 127.0.0.1:5492 (LISTEN)` on IPv4 only, alembic ran `a1b2c3d4e5f6` against it and
  `/api/health` answered 200. **That last part is the answer to the one real risk**: the scripts
  connect to the name `localhost`, which can resolve to `::1` first while Docker publishes IPv4
  loopback only. It resolves and connects. Tested, not assumed.
- **Container mode with the database port not published at all** — the `ports:` block commented
  out — `./scripts/start.sh --container` built, migrated and answered
  `{"status":"ok","environment":"local","version":"0.1.0"}` on :8092, with the db container
  reporting `{"5432/tcp":null}` and nothing listening on 5492. The published port really is
  uninvolved there.
- **A synthetic stranger** on the application's port: the report named it
  (`lonelyserver3 run by jaroslawwasowski (pid 92733, started …)`), set `ours: false`, offered
  `--port 8094`, and **the process was still listening afterwards** — no signal was sent, by the
  advice or by anything that followed it. This checkout's own application on :8092 reported
  `ours: true`.
- **One defect was found and fixed by that run.** The first draft asked `ps` for `comm`, which
  macOS truncates to sixteen characters: the venv interpreter came back as `/Users/jaroslaww`
  and the report named the command `jaroslaww` — a slice of the user's own name, presented as
  the identity of a process. The command now comes from `args`, read with `-ww` so the path that
  decides ownership cannot be trimmed either.
  `test_a_long_executable_path_is_not_truncated_into_a_command_name` starts a real process under
  a long `argv[0]` and holds that.
- `./scripts/lint.sh` — ruff, ruff format, mypy --strict over 108 files, eslint and tsc clean.
- `POSTGRES_HOST_PORT=5522 APP_PORT=8092 ./scripts/check.sh` — **OK**, the whole local gate,
  including the production image build and 44 end-to-end tests (30 scenario items collected of
  30 declared, plus the 14-test Chromium smoke) run against a loopback-bound database. The ports
  were moved because other worktrees on this machine hold 5432 and 5492; nothing in the run
  depends on the numbers, and a first attempt on the defaults failed with Docker's
  `port is already allocated` before any test ran.
- **`APP_STARTING` was not observed on a live machine**: the window between the port opening and
  `/api/health` answering was shorter than a status call on every attempt. The branch is covered
  by `test_our_own_slow_start_is_not_called_a_squatter`, and the `ours: true` half of it was
  measured on the real process.

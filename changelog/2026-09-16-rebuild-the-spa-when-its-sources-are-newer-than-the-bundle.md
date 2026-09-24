---
date: 2026-09-16
branch: fix/spa-staleness-check
pr: 53
kind: fix
---

# Rebuild the SPA when its sources are newer than the bundle

## What changed

- `scripts/spa_build_state.py` is new: the one declaration of what the built SPA is
  judged against (`BUILD_INPUTS`) and the one comparison that judges it. Prints
  `missing`, `stale` or `current` on the first line of stdout and, with `--explain`, a
  sentence on the second saying what was compared against what. Exit code is 0 whatever
  the verdict -- a report, not a gate.
- `scripts/_lib.sh` gains `spa_build_report`, which runs that module under a bare
  `python3` (falling back to `uv run python`), so every script asks for the verdict the
  same way.
- `scripts/build.sh` gains `--if-stale`, which compiles only when the bundle is missing
  or older than an input, and its closing line no longer announces `app/static is
  current` on faith: the comparison runs again over the bundle just written and the line
  reports what it found. A bundle that is already stale on delivery exits 4, not 0.
- `scripts/test.sh` prepares the `e2e` and `ui` suites with `build.sh --if-stale`
  instead of a presence check on `app/static/index.html`.
- `scripts/app_status.py` no longer carries its own copy of the input list and the mtime
  comparison; it imports both from the new module, so `status.sh --json` and the two
  scripts cannot drift apart.
- `tests/tooling/test_spa_build_state.py` is new. `tests/fitness/test_scripts_syntax_floor.py`
  registers the new module as a bare-machine script. `scripts/help.sh` lists the flag.
- `docs/troubleshooting.md` gains the symptom this was found as -- "A UI test fails against
  code you have already fixed" -- with what the preparation step compares now, how to read
  `frontend_build` out of `./scripts/status.sh --json`, and the one case that stops a run
  on purpose.

## Why

`scripts/test.sh` asked only whether `app/static/index.html` **existed**, so the `e2e`
and `ui` suites ran against whatever bundle was lying in the working tree.

On 2026-09-16, while implementing issue #27, `./scripts/test.sh ui` reported three
failures against components that had already been fixed: it had reused the bundle built
from the previous sources, after edits to `frontend/src/styles/theme.css` and several
components. The mirror image is the one that matters -- a stale bundle still holding the
old, PASSING behaviour reports green for a screen nobody built -- and neither shape can
be told apart from the suite's own output.

CI never meets this: a clean checkout has no `app/static/`, so every CI run builds. It
is a hazard of the local loop alone, which is the loop whose verdict people act on
fastest, and a suite whose verdict is about the wrong code costs the credit of every
other verdict it gives.

`scripts/build.sh` made it harder to see. Its `ok "app/static is current"` printed
unconditionally after a build, which reads as a freshness claim -- and made the presence
check next door look like the belt to its braces rather than the only thing deciding.

## From what, to what

Before, in `scripts/test.sh`:

    if [ ! -f "$REPO_ROOT/app/static/index.html" ]; then
        info "no built SPA under app/static/ -- building one"
        "$REPO_ROOT/scripts/build.sh"
    fi

A bundle from any moment in the past satisfied that check. After:

    "$REPO_ROOT/scripts/build.sh" --if-stale

which rebuilds when the bundle is missing **or** older than `frontend/src`,
`frontend/index.html`, `frontend/package.json`, `frontend/package-lock.json`,
`frontend/tsconfig.json` or `frontend/vite.config.ts`.

Before, in `scripts/build.sh`, after every compile:

        OK app/static is current

After, the same line having actually compared:

        OK app/static was written at 22:31:19, after all 6 build inputs (frontend/src,
        frontend/index.html, frontend/package.json, frontend/package-lock.json,
        frontend/tsconfig.json, frontend/vite.config.ts) -- newest of them
        frontend/src/lib/datetime.ts at 22:22:24

and, when a rebuild is needed, the reason for it:

    ==> Rebuilding the SPA
        frontend/src/styles/theme.css changed at 22:31:33, after app/static was written
        at 22:31:27 -- the bundle is older than its sources

## How it works now

`scripts/spa_build_state.py` holds two facts and nothing else: the list of build inputs,
and the rule that the bundle is stale when the newest of them is newer than the newest
file under `app/static`. `package.json`, the lockfile and `tsconfig.json` are inputs
because a dependency bump, a change to the build script or a compiler option stales a
bundle exactly as an edit to a component does, and `npm run build` type-checks before it
compiles. `vitest.config.ts`, `eslint.config.js` and the rest are not, because
`vite build` never reads them and a check that fires at everything is a check people
switch off.

The comparison is mtimes and nothing else. A content hash would be exact and would also
mean reading every source on every `./scripts/test.sh ui`; the failure mode mtimes have
-- a clock moved backwards -- makes a build look stale, which costs a rebuild rather
than a false green. Ties count as current, so a coarse filesystem clock cannot make
`--if-stale` rebuild for ever.

Three callers read that one verdict: `./scripts/status.sh --json` reports it,
`./scripts/build.sh --if-stale` acts on it, and `./scripts/test.sh e2e|ui` delegates to
`build.sh`. `--if-stale` resolves the verdict **before** `ensure_frontend_deps`, so a
current bundle costs no `node` and no `npm ci` -- measured at 47 ms, against tens of
seconds for a build.

After every real compile, `build.sh` runs the comparison again over what it has just
written. Current, and it says so with the evidence. Still stale, and a source was saved
while the compiler was running: it warns, says to run the build again, and exits 4 --
"did what it could and named a gap", which `check.sh` files under "Not run" rather than
red, because a bundle *was* delivered, just not one of these sources.

## What it means for the process

Nothing. No stage, gate, skill or script contract moves, and no command anybody types
changes: `./scripts/test.sh ui` is still the whole instruction, and it now builds when
it has to. `--if-stale` is available to anything that wants a build only if one is due;
plain `./scripts/build.sh` still compiles unconditionally, which is what
`./scripts/check.sh` and CI use.

## What it does not change

- **CI is untouched**, and deliberately so. A clean checkout has no `app/static/`, so
  every CI build was already a build from these sources; `.github/workflows/ci.yml`
  keeps calling `./scripts/build.sh` with no flag.
- **Nothing about the production image.** It builds the frontend in its own Node stage
  and has never depended on the host's `app/static/`.
- **`app_status.py`'s verdict is unchanged in substance.** It gained two inputs --
  `frontend/package.json` and `frontend/tsconfig.json` -- and lost its private copy of
  the comparison; the rule it applies is the rule it already applied.
- **Not a content check.** Two different edits that leave a file's mtime alone (a
  checkout that restores timestamps, a build artefact copied in) are still invisible
  here.

## How it was verified

- `./scripts/test.sh tooling -k spa_build` -- 13 passed. The staleness detector fires
  for every declared input in turn, does not fire for a file the build never reads,
  reports `missing` rather than `stale` when there is no bundle, and treats an asset
  written after `index.html` as part of the same build. One test asserts that
  `app_status.py` and `spa_build_state.py` are the same objects, so a private copy
  growing back is a red test rather than a silent divergence.
- `./scripts/test.sh fitness` -- 255 passed, including the syntax floor now holding the
  new module to the oldest `python3` a bare machine may start it with.
- The real loop, by hand: `./scripts/build.sh` then `./scripts/build.sh --if-stale`
  skipped the build in 47 ms with the evidence printed; `touch
  frontend/src/styles/theme.css` then `./scripts/test.sh ui` printed "Rebuilding the
  SPA", named that file, and compiled before entering a single screen. This is the
  2026-09-16 incident reproduced and then not reproduced.
- The exit-4 path, by forcing the race it exists for -- a source touched in a loop while
  `./scripts/build.sh` ran. `build.sh` warned, said to run it again and exited 4
  (`Build: INCOMPLETE`); the same race under `./scripts/test.sh ui` stopped with "the
  SPA was not built from these sources ... Nothing was started and nothing was run", so
  no container and no application were started to smoke a bundle already known to be
  stale.
- CI on the pull request: every job green except `operations-doc`, the diff-scoped gate that
  refuses a change to `scripts/_lib.sh` with nothing under `docs/` -- correctly, since the
  local test loop is something an operator runs. The symptom index answers it.
- `./scripts/check.sh` -- OK, every gate, including the 49 end-to-end tests (30 BDD
  scenarios plus the 19 UI smokes) on a free Postgres port, and `./scripts/lint.sh` --
  OK. `sdd-specs` -- Specs: OK.

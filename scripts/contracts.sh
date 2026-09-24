#!/usr/bin/env bash
# Does the application honour the contract somebody wrote by hand?
#
# `contracts/openapi/` is authored, committed and versioned; `openapi.json` is a dump of
# the Pydantic schemas and is gitignored. The constitution (Article VI) says which of the
# two has authority -- the contract does, and the code is validated against it, never the
# other way around -- and until this gate existed nothing in the tree asked the question.
# `generate.sh --check` is its sibling and answers a different one: whether the generated
# TypeScript matches the dump. Both halves can agree while both disagree with the contract.
#
# The comparison is a SUBSET: every sentence the contract states must be true of the dump,
# and the dump may carry more. `scripts/openapi_contract.py` carries that argument in full.
#
# No contract to compare is a NAMED GAP (exit 4), never a pass: a gate that quietly did not
# run reads on a dashboard exactly like one that found nothing.
set -euo pipefail
# shellcheck source=scripts/_lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/_lib.sh"
cd "$REPO_ROOT"

usage() {
    cat <<'TEXT'
usage: contracts.sh [--json]

  (no argument)  compare, then say what disagrees and on which contract line
  --json         machine-readable findings and scale, for a summary step

Reads:
  contracts/openapi/*.yaml   the hand-written contract -- committed, versioned
  app/*/routers/*.py and app/*/*/routers/*.py
                             for the refusal codes the dump structurally cannot carry

Writes:
  openapi.json               the dump, rebuilt every run and gitignored on purpose

Exit codes:
  0  every sentence of the contract is true of the application
  1  they disagree, or a contract does not parse
  4  no contract to compare (a named gap, not a pass)
TEXT
}

json=()
case "${1:-}" in
    -h|--help) usage; exit 0 ;;
    --json) json=(--json) ;;
    "") ;;
    *) usage >&2; die "unknown option: $1" ;;
esac

# `uv` and nothing else: no database (dump_openapi.py points DATABASE_URL at a URL that
# is well formed and deliberately unreachable), no daemon, no Node, no network. That is
# why the gate spec carries an empty `needs` and runs in every profile.
#
# `require_uv` rather than the named gap `audit.sh` returns for a missing npm, and the
# asymmetry is deliberate: `preflight.py` treats uv as required and Docker as
# informational. A machine without uv cannot run most of this repository, so reporting
# "not checked" here would be reporting it about half the gates at once.
require_uv

step "Dumping the OpenAPI document from the Pydantic schemas"
uv run python scripts/dump_openapi.py

step "Checking the application against contracts/openapi/"
# The child's exit code IS the answer, including 4, so it must survive `set -e`.
rc=0
uv run python scripts/openapi_contract.py ${json[@]+"${json[@]}"} || rc=$?

summary "API contract is frozen" "$rc"

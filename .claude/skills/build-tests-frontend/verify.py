#!/usr/bin/env python3
"""Verify for `build-tests-frontend`: five statements, so there is nothing here to drift.

The contract, the write allowlist and the worktree check live once, in the engine's
`skill_gate.py`. What is per-skill is the brief this renders -- see the engine's
`skill_brief.py`.

Run it as `sdd-skill <name> preflight|verify`, from the repository root. Not directly: the
`sys.path` line below is the process's own layout, where `_shared` sits beside the skill.
The engine left with the plugin, so in THIS tree that path names nothing and the import
falls through to PYTHONPATH -- which `sdd-skill` sets and nothing else does. The line stays
because these files are the same five statements the plugin ships thirty-two of, and eight
shims per template drifting from those is the more expensive half of the trade.
`test_the_command_that_runs_a_skill_hands_the_engine_to_the_interpreter` is what keeps it
from being invisible.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "_shared"))

from sdd.skill_brief import main

raise SystemExit(main("build-tests-frontend", "verify"))

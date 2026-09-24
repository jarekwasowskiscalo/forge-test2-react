---
date: 2026-09-23
branch: chore/plugin-pin-rule
pr: 80
kind: chore
---

# Write the plugin pin rule down before this stack has a plugin to pin

## What changed

`.specconf/stack.json` § `plugins.$comment` keeps its statement that this template assumes no
vendor plugin. It gains the rule for the first one: an entry pins a `version` (one concrete
number, never a range, a branch or the name alone) and lists the `skills` and `mcp` servers that
version ships.

`tests/fitness/test_process_pin.py` gains three cases:

- the absence is still stated, and the rule is written beside it;
- every declared plugin carries one concrete version;
- a plugin that brings an MCP server is pinned with it.

The last two are vacuous today because the list is empty.

## Why

forge_template_python_react#58 / #66, audit ticket E5-06. The other template pinned
`dart-flutter` by name, and the 2026-09-20 audit found 1.0.3 and 1.0.5 of it side by side in a
vendor cache. 1.0.5 installed itself mid-session. 1.0.3 declares no MCP server at all, so the
name alone could not say which manifest the profile meant. `uv.lock` pins this project's
dependencies; the agent's toolchain was pinned by nothing. This stack would inherit the same gap
with its first plugin unless the rule is already written when that plugin arrives.

## From what, to what

Before: the list was empty and said so, with no rule for what an entry must carry.

After: the list is still empty and still says so. The rule is in the profile, and the fitness
suite fails the first entry that arrives without a version.

## How it works now

A future vendor plugin is declared with `install`, `version`, `skills` and `mcp`. The engine
installs nothing and refuses nothing on the strength of `version`. It banks what each dispatch
was actually handed and reports a divergence from the pin (claude-marketplace#209). The template
states what it meant; the engine records what the machine had.

## What it means for the process

Nothing about running or changing this repository moves.

## What it does not change

No plugin is added. The stated absence is not removed: it is the correct state today, and the
issue says so. `.claude/settings.json` and its `enabledPlugins` are untouched. `schema_version`
stays `1`: `stack.py` has accepted the optional `version` key since forge 0.1.117.

## How it was verified

- `sdd-engine stack --check` (forge 0.1.124): `OK .specconf/stack.json (fastapi-react-postgres:
  8 contract scripts, 3 suites, 11 skills)`.
- `./scripts/test.sh fitness`: 312 passed.
- Seen failing first: with the rule's `` `version` `` removed from the comment, the suite reported
  `1 failed, 311 passed` (`the profile carries no rule for the first plugin`), and was green again
  once the word was restored.
- Not run: the two per-entry cases against a real entry, because none exists.

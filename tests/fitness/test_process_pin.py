"""`.claude/settings.json` -- the one thing this template knows about the process.

The SDD process is a Claude Code plugin, `forge@scalo`, and this repository does
not carry it: it names it. Two keys do that, and Claude Code honours them in every
clone, so nobody has to remember an install command.

What this file mostly guards is an ABSENCE. The process registers its own hooks, in
the plugin's `hooks/hooks.json`. Hooks from a plugin and hooks from a project's
settings are not deduplicated -- both run. So a `hooks` section left here would run
the session brief and the PreToolUse guard twice on every single tool call, and
nothing would fail: it would just cost double and log double.

It also holds a rule for a plugin this template does not have yet. `.specconf/stack.json`
§ `plugins` is empty on purpose, and says so; the day it gains an entry, the entry pins a
version -- one number, not a range and not the name alone -- because the other template
found `dart-flutter` 1.0.3 and 1.0.5 side by side in a vendor cache, and 1.0.3 declares
no MCP server at all. A name resolves to either. The three assertions below are vacuous
today, and that is the point: they are written before the first entry, not after it.
Every one reads a file of this repository and nothing of the machine, because a CI runner
has no vendor cache (claude-marketplace#209).
"""

import json
import pathlib
import re
from typing import Final

REPO_ROOT: Final[pathlib.Path] = pathlib.Path(__file__).resolve().parents[2]
SETTINGS: Final[pathlib.Path] = REPO_ROOT / ".claude" / "settings.json"
STACK: Final[pathlib.Path] = REPO_ROOT / ".specconf" / "stack.json"

#: One concrete version: digits and dots, nothing a resolver could widen.
_ONE_VERSION: Final = re.compile(r"^\d+(\.\d+)*$")

#: The plugin and the marketplace it comes from, exactly as `enabledPlugins` spells
#: the pair. Written out rather than derived: this is the fact the file exists to
#: state, and deriving it from the file would make the test agree with anything.
PLUGIN: Final = "forge"
MARKETPLACE: Final = "scalo"


def _declared_plugins() -> dict[str, dict[str, object]]:
    """The vendor plugins the stack profile declares, without the prose."""
    plugins = json.loads(STACK.read_text(encoding="utf-8"))["plugins"]
    return {name: entry for name, entry in plugins.items() if name != "$comment"}


def _settings() -> dict[str, object]:
    loaded: dict[str, object] = json.loads(SETTINGS.read_text(encoding="utf-8"))
    return loaded


def test_the_settings_name_the_process_and_where_it_comes_from() -> None:
    enabled = _settings().get("enabledPlugins")
    assert isinstance(enabled, dict), "settings.json enables no plugin at all"
    assert enabled.get(f"{PLUGIN}@{MARKETPLACE}") is True, (
        f"the pin does not enable {PLUGIN}@{MARKETPLACE}. Without it a fresh clone has "
        "no /forge:sdd, no gates and no hooks -- and nothing says so."
    )

    known = _settings().get("extraKnownMarketplaces")
    assert isinstance(known, dict), "the marketplace the plugin comes from is not declared"
    entry = known.get(MARKETPLACE)
    assert isinstance(entry, dict), f"{MARKETPLACE} is enabled but never described"
    source = entry.get("source")
    assert isinstance(source, dict) and source.get("source") in {"github", "git"}, (
        f"{MARKETPLACE} has no resolvable source: {source!r}"
    )


def test_this_repository_registers_no_hook_of_the_process_s() -> None:
    """The absence this file is really about -- see the module docstring."""
    settings = _settings()
    assert "hooks" not in settings, (
        "settings.json registers hooks. The process's own come with the plugin, and a "
        "second identical set here is not deduplicated: every hook would run twice."
    )


def test_the_pin_is_all_there_is() -> None:
    """No third key creeps in. A template that starts configuring the process from
    here has stopped installing it and started forking it."""
    assert set(_settings()) == {"enabledPlugins", "extraKnownMarketplaces"}, sorted(_settings())


def test_the_empty_plugin_list_is_a_stated_absence_with_its_rule() -> None:
    """The absence stays, and it carries the rule for the first entry."""
    comment = " ".join(json.loads(STACK.read_text(encoding="utf-8"))["plugins"]["$comment"])
    assert "stated absence" in comment, "the profile no longer says the list is empty on purpose"
    assert "`version`" in comment, (
        "the profile carries no rule for the first plugin; it will be pinned by name alone"
    )


def test_every_plugin_the_stack_profile_declares_carries_one_version() -> None:
    for name, entry in _declared_plugins().items():
        version = entry.get("version")
        assert isinstance(version, str) and version, (
            f"{name} is pinned by name alone; the record of what the machine had has "
            "nothing to be read against"
        )
        assert _ONE_VERSION.match(version), (
            f"{name} pins {version!r}, which is a range or a branch -- it reads like a pin "
            "and resolves to whatever the client holds"
        )


def test_an_mcp_server_is_pinned_with_the_plugin_that_brings_it() -> None:
    for name, entry in _declared_plugins().items():
        if entry.get("mcp"):
            assert entry.get("version"), (
                f"{name} brings {entry['mcp']} and names no version; which manifest declares "
                "the server is then unanswerable"
            )

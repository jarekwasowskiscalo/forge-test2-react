"""Which version a rollback may go back to, and the four times it must refuse.

The defect being repaired chose by arithmetic -- the highest published version below
the alias -- and arithmetic cannot tell a release from an apply. So the rules that
matter here are the ones that say **no**: a register that guesses is the register that
was already there.

Every case is a hand-built document. `deploy.sh` does the transport; nothing in this
file needs an account, and that is the point -- a rule only exercisable against AWS is
a rule nobody exercises.
"""

import json
from typing import Any

import pytest
from release_manifest import (
    KEEP,
    LIMIT_BYTES,
    Refusal,
    append,
    dump,
    entry,
    load,
    rollback_target,
)


def _served(version: str, **extra: Any) -> dict[str, Any]:
    return {"version": version, "commit": "abc1234", "environment": "prod", **extra}


def test_the_target_is_the_entry_before_the_one_serving() -> None:
    entries = [_served("4"), _served("6")]
    assert rollback_target(entries, "6")["version"] == "4"


def test_a_published_version_that_never_served_is_not_a_target() -> None:
    """The whole finding, in one assertion. Version 5 exists on the account -- an apply
    published it and the migration then failed -- and it is not in the register, so it
    is not a candidate. The old rule picked exactly it."""
    entries = [_served("4"), _served("6")]
    assert rollback_target(entries, "6")["version"] != "5"


def test_a_second_rollback_does_not_walk_forward_into_the_rejected_release() -> None:
    """`[4, 6]`, rolled back to 4, then 7 deployed and rolled back again. "The newest
    entry below 7" would answer 6 -- the release the first rollback was called to
    escape. It is skipped because some entry names it as what it rolled away from."""
    entries = [
        _served("4"),
        _served("6"),
        _served("4", rolled_back_from="6"),
        _served("7"),
    ]
    assert rollback_target(entries, "7")["version"] == "4"


def test_an_empty_manifest_refuses() -> None:
    with pytest.raises(Refusal, match="no release manifest yet"):
        rollback_target([], "6")


def test_a_serving_version_the_manifest_never_recorded_refuses() -> None:
    """The commonest way to arrive here is a deploy that moved the alias and then
    failed its smoke, so the sentence names that case and names the last release --
    and still refuses, because "very likely" is not "it served"."""
    with pytest.raises(Refusal) as refusal:
        rollback_target([_served("4"), _served("6")], "9")
    assert "failed after moving the alias" in str(refusal.value)
    assert "version 6" in str(refusal.value)


def test_the_oldest_recorded_release_refuses() -> None:
    with pytest.raises(Refusal, match="oldest release"):
        rollback_target([_served("4")], "4")


def test_a_manifest_whose_earlier_releases_were_all_rejected_refuses() -> None:
    """Rather than returning the rejected one. Refusing here is what sends a person to
    the manual command with the history in front of them."""
    entries = [_served("4"), _served("6"), _served("4", rolled_back_from="6")]
    with pytest.raises(Refusal):
        rollback_target(entries, "4")


def test_the_newest_entry_for_the_serving_version_is_the_one_read() -> None:
    """A version can appear twice -- deployed, rolled away from, rolled back to. The
    position that matters is the latest one, because that is where the alias is now."""
    entries = [_served("4"), _served("6"), _served("4", rolled_back_from="6"), _served("2")]
    assert rollback_target(entries, "2") is entries[2]


def test_append_keeps_the_newest_and_drops_the_oldest() -> None:
    entries: list[dict[str, Any]] = []
    for number in range(KEEP + 5):
        entries = append(entries, _served(str(number)))
    assert len(entries) == KEEP
    assert entries[-1]["version"] == str(KEEP + 4)
    assert entries[0]["version"] == "5"


def test_append_trims_until_the_document_fits_a_standard_parameter() -> None:
    """The count is the readable bound; the byte budget is the real one. An entry is
    not a fixed size -- a commit sha, a digest, a long environment name -- so a manifest
    that fit yesterday can stop fitting, and being refused by the API at the last step
    of a deploy is the wrong place to find that out."""
    fat = {**_served("1"), "commit": "x" * 600}
    entries: list[dict[str, Any]] = []
    for _ in range(KEEP):
        entries = append(entries, dict(fat))
    assert len(dump(entries).encode("utf-8")) <= LIMIT_BYTES
    assert len(entries) < KEEP


def test_the_document_is_written_without_newlines_or_tabs() -> None:
    """`deploy.sh` reads it back through `aws ssm get-parameter --output text`, which
    is only safe for a value that occupies one line."""
    written = dump(append([], entry("7", "abc1234", "prod", digest="d" * 44)))
    assert "\n" not in written
    assert "\t" not in written


def test_an_entry_carries_the_digest_when_one_was_found_and_omits_it_otherwise() -> None:
    """An unknown digest is read as unknown, never as a mismatch: an account that could
    not be asked must not make a rollback refuse."""
    assert entry("7", "abc1234", "prod", digest="sha")["digest"] == "sha"
    assert "digest" not in entry("7", "abc1234", "prod")


def test_a_rollback_entry_names_what_it_rolled_away_from() -> None:
    assert entry("4", "abc1234", "prod", rolled_back_from="6")["rolled_back_from"] == "6"
    assert "rolled_back_from" not in entry("4", "abc1234", "prod")


def test_a_parameter_holding_something_else_reads_as_no_register() -> None:
    """The refusal a person then gets is about the manifest, which is the thing they can
    act on -- not about JSON, which is the thing they cannot see."""
    assert load("") == []
    assert load("not json at all") == []
    assert load(json.dumps({"version": "4"})) == []
    assert load(json.dumps(["4", {"version": "6"}])) == [{"version": "6"}]

"""What actually served, and what a rollback is therefore allowed to go back to.

**A published Lambda version is not a release.** `publish = true`
(`infra/terraform/modules/api/main.tf`) mints an immutable version on every apply,
and the alias is moved three steps later -- after the migration, and only if it
succeeded. So every apply that stopped in between leaves a version that is newer than
the one serving and that nothing ever routed to. `scripts/infra.sh <env> apply` leaves
one on its own, without any deploy at all.

`deploy.sh --rollback` used to choose by arithmetic alone: the highest published
version below the alias. That predicate cannot tell those two apart, and on a real
account the consequence is not a wrong log line -- it is production traffic moved onto
a version that was never live, reported as `Rollback: OK`.

**This module is the register that makes the question answerable.** A deploy appends
one entry after its smoke has passed, so an entry means "this version served this
environment and answered the contract". A rollback appends its own, naming what it
rolled away from -- and that name is what keeps the next rollback from walking
forward into the release somebody has just rejected.

Pure functions over a JSON document: no AWS, no network, no clock of its own. That is
deliberate. The rules are the part worth testing, the transport is `aws ssm
get-parameter` / `put-parameter` in `deploy.sh`, and a rule that needs an account to
exercise is a rule nobody exercises.

Usage:
    uv run python scripts/release_manifest.py target --current 6 < manifest.json
    uv run python scripts/release_manifest.py digest --version 7 < manifest.json
    uv run python scripts/release_manifest.py append --version 7 --commit abc123 \
        --environment prod [--digest SHA] [--rolled-back-from 8] < manifest.json
"""

import argparse
import datetime
import json
import sys
from typing import Any, Final

#: Entries kept, newest last. Twenty of them is about 3 KB, and an SSM parameter on
#: the Standard tier holds 4 KB -- so `LIMIT_BYTES` below is the real ceiling and this
#: is the readable one. Older entries are dropped rather than archived: this register
#: answers "what may a rollback go back to", and a version from thirty releases ago is
#: not an answer to it.
KEEP: Final = 20

#: The Standard tier's hard limit. Exceeding it is an API error, so the document is
#: trimmed until it fits rather than written and refused.
LIMIT_BYTES: Final = 4096


class Refusal(Exception):
    """No target could be named. The message is the sentence the operator reads."""


def load(text: str) -> list[dict[str, Any]]:
    """The manifest as a list, or empty. An unreadable register is an empty one.

    Not a raise: a parameter that holds something other than this document is a
    register that says nothing, and `target` below already refuses on an empty one --
    with a sentence about the manifest rather than about JSON.
    """
    try:
        document = json.loads(text)
    except ValueError:
        return []
    if not isinstance(document, list):
        return []
    return [entry for entry in document if isinstance(entry, dict)]


def dump(entries: list[dict[str, Any]]) -> str:
    """Compact, because every byte of this document is charged against 4 KB."""
    return json.dumps(entries, separators=(",", ":"))


def append(entries: list[dict[str, Any]], entry: dict[str, Any]) -> list[dict[str, Any]]:
    """`entries` with `entry` newest-last, trimmed to what a Standard parameter holds."""
    kept = [*entries, entry][-KEEP:]
    while len(kept) > 1 and len(dump(kept).encode("utf-8")) > LIMIT_BYTES:
        kept = kept[1:]
    return kept


def entry(
    version: str,
    commit: str,
    environment: str,
    digest: str = "",
    rolled_back_from: str | None = None,
    at: str | None = None,
) -> dict[str, Any]:
    """One release that served. `rolled_back_from` is set by a rollback and only by one.

    `digest` is the function version's `CodeSha256`. It is what makes a version number
    checkable rather than merely findable: replace the function and the numbering
    restarts at 1, so an entry saying "5" would name different code entirely. Empty
    when the account could not be asked, which is read as "unknown", never as "wrong".
    """
    written: dict[str, Any] = {
        "version": version,
        "commit": commit,
        "environment": environment,
        "at": at or datetime.datetime.now(tz=datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    if digest:
        written["digest"] = digest
    if rolled_back_from is not None:
        written["rolled_back_from"] = rolled_back_from
    return written


def rejected(entries: list[dict[str, Any]]) -> set[str]:
    """Every version some rollback has moved away from.

    A rejected version stays in the manifest -- it did serve, and deleting history to
    express an opinion about it would make the register lie -- but it is never a
    target again. Without this, the second rollback of an incident rolls FORWARD into
    the release the first one was called to escape.
    """
    return {
        str(one["rolled_back_from"]) for one in entries if one.get("rolled_back_from") is not None
    }


def rollback_target(entries: list[dict[str, Any]], current: str) -> dict[str, Any]:
    """The newest entry before `current` that served and has not been rejected.

    Raises `Refusal` rather than guessing, in all four cases where an answer would be
    invented: there is no register yet, the alias is somewhere the register never put
    it, `current` is the oldest thing recorded, or everything before it has already
    been rolled back.
    """
    if not entries:
        raise Refusal(
            "this environment has no release manifest yet, so there is no record of "
            "which version last served. It is written by the first deploy whose smoke "
            "passes. Refusing to guess from version numbers -- that is the defect this "
            "replaced."
        )

    serving = [index for index, one in enumerate(entries) if str(one.get("version")) == current]
    if not serving:
        last = str(entries[-1].get("version"))
        raise Refusal(
            f"the alias serves version {current}, and no green deploy recorded it. "
            "**This is what a deploy that failed after moving the alias leaves behind**, "
            "and it is the commonest way to arrive here -- the alias moved, the smoke "
            f"did not pass, nothing was written. The last release this manifest records "
            f"is version {last}. Rolling back to it is very likely what you want, and "
            "this refuses to do it on its own because 'very likely' is not the same "
            "sentence as 'it served'."
        )

    unusable = rejected(entries)
    for one in reversed(entries[: serving[-1]]):
        version = str(one.get("version"))
        if version == current or version in unusable:
            continue
        return one

    raise Refusal(
        f"version {current} is the oldest release this manifest still records that has "
        "not already been rolled back, so there is nothing to go back to. Forward is "
        "the only direction: fix it and deploy."
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="verb", required=True)

    asking = sub.add_parser("target", help="print the version a rollback should go to")
    asking.add_argument("--current", required=True, help="the version the alias serves now")

    checking = sub.add_parser("digest", help="print the CodeSha256 recorded for a version")
    checking.add_argument("--version", required=True)

    writing = sub.add_parser("append", help="print the manifest with one entry added")
    writing.add_argument("--version", required=True)
    writing.add_argument("--commit", default="unknown")
    writing.add_argument("--digest", default="")
    writing.add_argument("--environment", required=True)
    writing.add_argument("--rolled-back-from", default=None)
    writing.add_argument("--at", default=None, help="an ISO instant; the clock is used otherwise")

    arguments = parser.parse_args(argv)
    entries = load(sys.stdin.read())

    if arguments.verb == "digest":
        # The newest entry for that version wins, and nothing is printed when none of
        # them recorded one: an unknown digest is not a mismatch, and the caller reads
        # the empty line as "there is nothing to compare".
        for one in reversed(entries):
            if str(one.get("version")) == arguments.version:
                print(str(one.get("digest", "")))
                return 0
        print("")
        return 0

    if arguments.verb == "target":
        try:
            print(rollback_target(entries, arguments.current)["version"])
        except Refusal as refusal:
            print(str(refusal), file=sys.stderr)
            return 1
        return 0

    print(
        dump(
            append(
                entries,
                entry(
                    version=arguments.version,
                    commit=arguments.commit,
                    environment=arguments.environment,
                    digest=arguments.digest,
                    rolled_back_from=arguments.rolled_back_from,
                    at=arguments.at,
                ),
            )
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

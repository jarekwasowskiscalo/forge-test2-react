"""Fill a freshly created environment with the seed corpus, through its own API.

A preview with an empty guest book is a preview of a screen nobody can judge. This
fills one, from `golden-set/seed/` -- the half of the corpus that exists to be
LOOKED AT.

**It reads the seed half and not the fixture half, and that is the decision this
file now is.** It used to post `entries-ordinary.json`, on the argument that a
reviewer should see the very data the assertions are written about. The argument
did not survive contact: the fixture half is sized and shaped by what tests need
to prove, so an entry added to make a preview look richer weakened a paging test
that counted them, and a boundary case added to prove a rule put an eighty-
character signature on the screen. The two halves keep the properties that
matter to both -- characters outside ASCII, a message with line breaks -- and
each is now free to change for its own reason.

**Through the HTTP API, not through the database**, and that decision is older
than the split and survived it. A seeder that wrote rows directly would be a
second implementation of `BR-01`, would drift from the service the moment a rule
changed, and could plant data the application itself would have refused. Posting
means the corpus arrives the way a guest's entry arrives, or does not arrive at
all.

Two refusals keep it safe to wire into a deployment:

- **It will not seed production.** It asks `/api/health`, which reports the
  environment the deployment was given, and stops there. Test data in production
  is not a mistake anybody can undo by hand once a real visitor has replied to it.
- **It will not seed a guest book that already has entries.** So it is idempotent,
  and running it on every deploy touches only the environments that are new --
  which is the whole request it answers.

Not called directly. `scripts/seed.sh` is the interface, and every caller --
`start.sh`, `preview.sh`, `deploy.sh` -- goes through it, because a task is a
script (constitution, article XII):

    ./scripts/seed.sh                                  the app on this machine
    ./scripts/seed.sh --base-url https://.../api       a preview, a stage
    ./scripts/seed.sh --base-url ... --boundary        and the fixture extremes

Everything the guest book owns is an example and may be deleted (`CLAUDE.md`), and
this file goes with it: it is named after the corpus, and the corpus is the
guest book's. What stays is the mechanism -- a seed half, a script that posts it,
and the two refusals -- because a template whose environments come up empty is a
template that teaches the wrong first lesson.
"""

import argparse
import json
import pathlib
import sys
import urllib.error
import urllib.request
from typing import Any

#: The repository root, so `tests/_golden_set.py` can be imported. That module is
#: the ONLY place allowed to decide where the corpus lies
#: (`tests/fitness/test_golden_set.py`), it imports nothing but the standard
#: library, and joining `golden-set` to a root worked out here would be the twin
#: that file exists to refuse.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tests._golden_set import BOUNDARY, SEED_FILES, entries_of

#: Where test data must never go. Compared against what `/api/health` reports,
#: which is what Terraform put in `APP_ENV` -- so this is the deployment's own
#: answer rather than something inferred from a URL.
REFUSED_ENVIRONMENTS = frozenset({"prod"})

ENTRIES = "/guestbook-entries"
HEALTH = "/health"

TIMEOUT_SECONDS = 30


def _get(url: str) -> Any:
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        return json.loads(response.read())


def _post(url: str, body: dict[str, Any]) -> int:
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        return int(response.status)


def environment_of(base_url: str) -> str:
    """What the deployment says it is. `local` outside one."""
    body = _get(f"{base_url}{HEALTH}")
    return str(body.get("environment", "unknown"))


def is_empty(base_url: str) -> bool:
    """Whether the guest book has no entries yet."""
    body = _get(f"{base_url}{ENTRIES}?limit=1")
    return not body.get("items")


def seed(base_url: str, entries: list[dict[str, Any]]) -> int:
    """Post every entry. Returns how many were accepted; raises on the first refusal."""
    for index, entry in enumerate(entries, start=1):
        status = _post(
            f"{base_url}{ENTRIES}", {"author": entry["author"], "message": entry["message"]}
        )
        if status != 201:
            raise RuntimeError(f"entry {index} was answered with {status}, not 201")
    return len(entries)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        required=True,
        help="Where the API answers, including the /api prefix and no trailing slash.",
    )
    parser.add_argument(
        "--boundary",
        action="store_true",
        help="Also post the fixture entries that sit exactly on the published limits.",
    )
    arguments = parser.parse_args(argv)
    base_url = arguments.base_url.rstrip("/")

    try:
        environment = environment_of(base_url)
    except (urllib.error.URLError, OSError, ValueError) as error:
        print(
            f"error: could not ask {base_url}{HEALTH} which environment it is: {error}",
            file=sys.stderr,
        )
        return 1

    if environment in REFUSED_ENVIRONMENTS:
        print(f"refusing to seed {environment}: the corpus is test data", file=sys.stderr)
        return 1

    try:
        if not is_empty(base_url):
            print(f"{environment} already has entries; nothing seeded")
            return 0

        entries = [entry for path in SEED_FILES for entry in entries_of(path)]
        if arguments.boundary:
            # The one deliberate borrow from the fixture half, and it is opt-in
            # because it is a category error made on purpose: a person reviewing
            # the SCREEN rather than the flow wants to see what it does at the
            # limits, and the corpus that proves those limits is the one place
            # they are computed rather than transcribed. No deployment passes it.
            entries += entries_of(BOUNDARY)
        posted = seed(base_url, entries)
    except (urllib.error.URLError, OSError, ValueError, RuntimeError) as error:
        print(f"error: seeding {environment} failed: {error}", file=sys.stderr)
        return 1

    print(f"seeded {environment} with {posted} entries from the seed corpus")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

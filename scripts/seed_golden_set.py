"""Fill a freshly created environment with the seed corpus, through its own API.

A preview whose guest book or to-do list is empty is a preview of a screen nobody
can judge. This fills each of them from `golden-set/seed/` -- the half of the corpus
that exists to be LOOKED AT: the guest book's welcome entries and the to-do list's
example tasks.

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
second implementation of `BR-01` -- or of `BR-06`...`BR-08` for a task -- would
drift from the service the moment a rule changed, and could plant data the
application itself would have refused. Posting means the corpus arrives the way a
guest's entry or a person's task arrives, or does not arrive at all.

**A task arrives the way a person's does**: added with its text alone, and so not
done, and then -- once every example task is on the list -- marked through the
marking route when the corpus says it ends done. An example shown done got there
the way any task does, never born done (`BR-08`); the create shape has no `done` to
send, and the seeder does not try.

Two refusals keep it safe to wire into a deployment:

- **It will not seed production.** It asks `/api/health`, which reports the
  environment the deployment was given, and stops there -- before it reads either
  list. Test data in production is not a mistake anybody can undo by hand once a
  real visitor has replied to it.
- **It will not seed a list that already holds something, and it asks each list on
  its own.** The guest book gets its welcome entries when it holds none, whatever
  the to-do list holds, and the to-do list gets its example tasks when its `total`
  is zero, whatever the guest book holds (`spec/design/architecture.md` § What a new
  environment starts with). So it is idempotent, running it on every deploy touches
  only what is new, and an environment that existed before the to-do list -- stage,
  an open preview -- gets its example tasks on the next run without its welcome
  entries being posted a second time.

"Only while the list is empty" is a read and then posts, and nothing a key or an
index can state; the guarantee is this check and is weaker by choice -- a person
adding a task in the seconds between the read and the posts, or two fillings of one
environment at once, leaves the examples beside the task or twice over
(`spec/design/data-model.md` § Two writers on one task, the last paragraph).

Not called directly. `scripts/seed.sh` is the interface, and every caller --
`start.sh`, `preview.sh`, `deploy.sh` -- goes through it, because a task is a
script (constitution, article XII):

    ./scripts/seed.sh                                  the app on this machine
    ./scripts/seed.sh --base-url https://.../api       a preview, a stage
    ./scripts/seed.sh --base-url ... --boundary        and the fixture extremes

The welcome entries belong to the guest book, which is an example and may be
deleted (`CLAUDE.md`); the example tasks belong to the to-do list, which is not.
Deleting the guest book deletes `entries-welcome.json` and the half of this file
that posts entries, and leaves the mechanism -- a seed half, a script that posts it,
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

from tests._golden_set import BOUNDARY, SEED_FILES, entries_of, story_of

#: Where test data must never go. Compared against what `/api/health` reports,
#: which is what Terraform put in `APP_ENV` -- so this is the deployment's own
#: answer rather than something inferred from a URL.
REFUSED_ENVIRONMENTS = frozenset({"prod"})

ENTRIES = "/guestbook-entries"
TASKS = "/todo-tasks"
HEALTH = "/health"

TIMEOUT_SECONDS = 30


def _get(url: str) -> Any:
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        return json.loads(response.read())


def _send(method: str, url: str, body: dict[str, Any]) -> tuple[int, Any]:
    """Send one JSON body; return the status and the decoded answer.

    The answer is read because a task's is needed: the marking of a done example
    goes to the identifier its own addition was answered with.
    """
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method=method,
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        payload = response.read()
        return int(response.status), json.loads(payload) if payload else None


def _seed_half(key: str) -> list[dict[str, Any]]:
    """Every item the seed half holds under `key`, file by file in the locator's order.

    By the key a file lists rather than by file name, so each list is filled from
    whatever seed files hold its kind of item: `entries` for the guest book, `tasks`
    for the to-do list.
    """
    return [item for path in SEED_FILES for item in story_of(path).get(key, [])]


def environment_of(base_url: str) -> str:
    """What the deployment says it is. `local` outside one."""
    body = _get(f"{base_url}{HEALTH}")
    return str(body.get("environment", "unknown"))


def guest_book_is_empty(base_url: str) -> bool:
    """Whether the guest book has no entries yet."""
    body = _get(f"{base_url}{ENTRIES}?limit=1")
    return not body.get("items")


def to_do_list_is_empty(base_url: str) -> bool:
    """Whether the to-do list holds no task, by the `total` of its one read.

    `total` rather than `items`: it is the number the envelope exists to give a caller
    that wants to know only whether the list is empty (`spec/design/api.md`
    § `TodoTaskList`).
    """
    body = _get(f"{base_url}{TASKS}")
    return int(body.get("total", 0)) == 0


def seed(base_url: str, entries: list[dict[str, Any]]) -> int:
    """Post every entry. Returns how many were accepted; raises on the first refusal."""
    for index, entry in enumerate(entries, start=1):
        status, _ = _send(
            "POST",
            f"{base_url}{ENTRIES}",
            {"author": entry["author"], "message": entry["message"]},
        )
        if status != 201:
            raise RuntimeError(f"entry {index} was answered with {status}, not 201")
    return len(entries)


def seed_tasks(base_url: str, tasks: list[dict[str, Any]]) -> int:
    """Add every example task, then mark the done ones. Returns how many were added.

    All of them are added first, in file order, each as its text alone; only then is
    each done one marked, through the identifier its own addition was answered with.
    Newest first is decided by the moment of adding, so the order the marks are made
    in moves nothing. Raises on the first answer that is not the one a success gets.
    """
    added: list[tuple[str, dict[str, Any]]] = []
    for index, task in enumerate(tasks, start=1):
        status, answer = _send("POST", f"{base_url}{TASKS}", {"text": task["text"]})
        if status != 201:
            raise RuntimeError(f"example task {index} was answered with {status}, not 201")
        if not isinstance(answer, dict) or "id" not in answer:
            raise RuntimeError(f"example task {index} was added and its identifier not given")
        added.append((str(answer["id"]), task))
    for index, (todo_task_id, task) in enumerate(added, start=1):
        if task["done"] is not True:
            continue
        status, _ = _send("PATCH", f"{base_url}{TASKS}/{todo_task_id}", {"done": True})
        if status != 200:
            raise RuntimeError(f"example task {index} was marked with {status}, not 200")
    return len(added)


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
        # The guest book, on its own condition.
        if guest_book_is_empty(base_url):
            entries = _seed_half("entries")
            if arguments.boundary:
                # The one deliberate borrow from the fixture half, and it is opt-in
                # because it is a category error made on purpose: a person reviewing
                # the SCREEN rather than the flow wants to see what it does at the
                # limits, and the corpus that proves those limits is the one place
                # they are computed rather than transcribed. No deployment passes it.
                entries += entries_of(BOUNDARY)
            posted = seed(base_url, entries)
            print(f"seeded the guest book of {environment} with {posted} entries")
        else:
            print(f"the guest book of {environment} already has entries; left alone")

        # The to-do list, on its own condition -- whatever the guest book held.
        if to_do_list_is_empty(base_url):
            added = seed_tasks(base_url, _seed_half("tasks"))
            print(f"seeded the to-do list of {environment} with {added} example tasks")
        else:
            print(f"the to-do list of {environment} already holds a task; left alone")
    except (urllib.error.URLError, OSError, ValueError, RuntimeError) as error:
        print(f"error: seeding {environment} failed: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

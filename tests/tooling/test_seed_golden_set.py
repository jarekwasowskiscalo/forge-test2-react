"""The seeder's two refusals, which are what make it safe to run on every deploy.

`scripts/deploy.sh` and `scripts/preview.sh` both call it unconditionally. That is
only defensible because it decides for itself whether to do anything:

- **It refuses production**, by asking the deployment which environment it is
  rather than inferring one from a URL. Test data in production cannot be undone
  by hand once a real visitor has replied to it, and a guard that depended on a
  caller passing the right flag would fail the first time somebody added a caller.
- **It refuses a list that already holds something**, and it asks each list on its
  own: the guest book gets its welcome entries when it holds none, whatever the
  to-do list holds, and the to-do list gets its example tasks when it holds none,
  whatever the guest book holds (`spec/design/architecture.md` § What a new
  environment starts with). That is what makes "seed every new environment" and
  "run on every deploy" the same sentence -- and what fills the to-do list of an
  environment that existed before it did.

It posts `golden-set/seed/` -- the half of the corpus that exists to be looked at.
Which half is itself a property worth holding: seeding from the fixture half is
what coupled a preview's screen to a paging test's arithmetic.

**A task arrives the way a person's does**: added, and therefore not done, then
marked through the marking route when the corpus says it ends done -- so an
example shown done got there the way any task does, never born done (`BR-08`).

`urllib.request.urlopen` is replaced rather than the seeder's own helpers, so what
runs here includes the JSON encoding, the headers and the method -- the parts a
test that stubbed `_get`/`_post` would have skipped over. That the round trip works
against a real application was established by pointing it at one.

**Expectations are derived from the corpus, never written out here.** That is what
keeps this module on the right side of the line
`tests/fitness/test_golden_set.py::test_no_suite_reads_the_seed_corpus` draws: it
asserts about the seeder, not about the data, so adding a welcome entry or an
example task leaves it green.
"""

# `_Response` is named in a signature above its definition; under the syntax floor
# (py312, see pyproject.toml) an unquoted forward reference needs lazy annotations.
from __future__ import annotations

import io
import json
import urllib.error
import urllib.parse
import urllib.request
import uuid
from typing import Any

import pytest
import seed_golden_set

from tests._golden_set import SEED_FILES, story_of

BASE = "http://example.invalid/api"

ENTRIES = "/api/guestbook-entries"
TASKS = "/api/todo-tasks"


class _Response(io.BytesIO):
    """Enough of an `http.client.HTTPResponse` for `urlopen`'s context manager."""

    def __init__(self, payload: Any, status: int = 200) -> None:
        super().__init__(json.dumps(payload).encode("utf-8"))
        self.status = status

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *exception: object) -> None:
        self.close()


class Fake:
    """An application with a guest book and a to-do list, recording what was asked of it.

    It answers the routes the seeder may use and fails loudly on any other, so a
    seeder that reached for a route the application does not have is caught here
    rather than against a live environment.
    """

    def __init__(
        self,
        environment: str,
        entries: list[dict[str, Any]] | None = None,
        tasks: list[str] | None = None,
    ) -> None:
        self.environment = environment
        self.entries = list(entries or [])
        self.tasks: list[dict[str, Any]] = []
        for text in tasks or []:
            self._store_task(text)
        #: Every body POSTed, to either list, in order.
        self.posted: list[dict[str, Any]] = []
        #: Every write, in order: (method, path, body).
        self.writes: list[tuple[str, str, dict[str, Any]]] = []
        self.post_status = 201

    def _store_task(self, text: str) -> dict[str, Any]:
        task = {
            "id": str(uuid.uuid4()),
            "text": text,
            "done": False,
            "created_at": "2026-09-24T12:00:00Z",
        }
        self.tasks.append(task)
        return task

    @property
    def posted_entries(self) -> list[dict[str, Any]]:
        return [body for method, path, body in self.writes if method == "POST" and path == ENTRIES]

    @property
    def posted_tasks(self) -> list[dict[str, Any]]:
        return [body for method, path, body in self.writes if method == "POST" and path == TASKS]

    @property
    def patched_tasks(self) -> list[tuple[str, dict[str, Any]]]:
        return [
            (path.rsplit("/", 1)[1], body)
            for method, path, body in self.writes
            if method == "PATCH"
        ]

    def __call__(self, request: urllib.request.Request, timeout: float = 0) -> _Response:
        method = request.get_method()
        path = urllib.parse.urlsplit(request.full_url).path.rstrip("/")
        if method == "GET" and path.endswith("/health"):
            return _Response({"status": "ok", "environment": self.environment, "version": "0"})
        if method == "GET" and path == ENTRIES:
            return _Response(
                {
                    "items": self.entries[:1],
                    "total": len(self.entries),
                    "total_all": len(self.entries),
                }
            )
        if method == "GET" and path == TASKS:
            return _Response({"items": list(self.tasks), "total": len(self.tasks)})

        body = json.loads(request.data or b"{}")
        if method == "POST" and path == ENTRIES:
            self.posted.append(body)
            self.writes.append((method, path, body))
            self.entries.append(body)
            return _Response(body, self.post_status)
        if method == "POST" and path == TASKS:
            self.posted.append(body)
            self.writes.append((method, path, body))
            return _Response(self._store_task(str(body.get("text"))), self.post_status)
        if method == "PATCH" and path.startswith(f"{TASKS}/"):
            self.writes.append((method, path, body))
            task_id = path.rsplit("/", 1)[1]
            task = next((task for task in self.tasks if task["id"] == task_id), None)
            assert task is not None, f"the seeder marked {task_id}, which no POST answered with"
            task.update({key: value for key, value in body.items() if key in {"text", "done"}})
            return _Response(task, 200)
        raise AssertionError(
            f"the seeder asked for {method} {path}, which the application does not have"
        )


@pytest.fixture
def guestbook(monkeypatch: pytest.MonkeyPatch):
    """Install a `Fake` in place of `urlopen`. Named after the one list the fake held
    first; it holds both now, and the name stays so the cases that predate the
    to-do list read exactly as they did."""

    def install(
        environment: str,
        entries: list[dict[str, Any]] | None = None,
        tasks: list[str] | None = None,
    ) -> Fake:
        fake = Fake(environment, entries, tasks)
        monkeypatch.setattr(urllib.request, "urlopen", fake)
        return fake

    return install


def _seed_corpus() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """The welcome entries and the example tasks, each half of the seed corpus read
    by the key it is held under, so the expectation follows the files."""
    entries: list[dict[str, Any]] = []
    tasks: list[dict[str, Any]] = []
    for path in SEED_FILES:
        story = story_of(path)
        entries += story.get("entries", [])
        tasks += story.get("tasks", [])
    return entries, tasks


def _assert_the_to_do_list_was_filled(fake: Fake) -> None:
    """Every example task added in file order, sent as a text alone, and the list
    ending with the marks the corpus gives."""
    assert fake.posted_tasks, "the empty to-do list was given no example task"
    _, tasks = _seed_corpus()
    assert tasks, "the seed corpus holds no example task"
    assert [body.get("text") for body in fake.posted_tasks] == [task["text"] for task in tasks]
    assert all(set(body) == {"text"} for body in fake.posted_tasks), (
        "the seeder sends a task with fields the create shape does not have"
    )
    assert [(task["text"], task["done"]) for task in fake.tasks] == [
        (task["text"], task["done"]) for task in tasks
    ], "the to-do list does not end with the example tasks and their marks"


def test_an_empty_environment_gets_the_whole_seed_corpus(guestbook) -> None:
    """Both lists, every item in file order, through the API rather than into the
    database -- and the done example marked once it has been added."""
    fake = guestbook("preview")

    assert seed_golden_set.main(["--base-url", BASE]) == 0

    entries, _ = _seed_corpus()
    assert [entry["author"] for entry in fake.posted_entries] == [
        entry["author"] for entry in entries
    ]
    assert all(set(body) == {"author", "message"} for body in fake.posted_entries), (
        "the seeder sends fields the write schema does not accept"
    )
    _assert_the_to_do_list_was_filled(fake)


def test_production_is_refused(guestbook) -> None:
    """The safety property, and the reason this can be wired into deploy.sh at all."""
    fake = guestbook("prod")

    assert seed_golden_set.main(["--base-url", BASE]) == 1
    assert fake.posted == []


def test_a_guest_book_with_entries_is_left_alone(guestbook) -> None:
    """Its entries are left alone, and the empty to-do list beside it still gets its
    examples: an environment that existed before the to-do list -- stage, an open
    preview -- holds welcome entries and no task (`Q-10`)."""
    fake = guestbook("stage", entries=[{"author": "Somebody", "message": "was here"}])

    assert seed_golden_set.main(["--base-url", BASE]) == 0

    assert fake.posted_entries == [], "a guest book that holds entries was filled again"
    _assert_the_to_do_list_was_filled(fake)


def test_a_to_do_list_holding_a_task_is_left_alone(guestbook) -> None:
    """A list with one task somebody wrote gets no example beside it, and the empty
    guest book is filled on its own condition all the same."""
    fake = guestbook("stage", tasks=["Water the plants"])

    assert seed_golden_set.main(["--base-url", BASE]) == 0

    assert fake.posted_tasks == [], "a to-do list that holds a task was given example tasks"
    assert fake.patched_tasks == []
    assert [task["text"] for task in fake.tasks] == ["Water the plants"]
    entries, _ = _seed_corpus()
    assert [entry["author"] for entry in fake.posted_entries] == [
        entry["author"] for entry in entries
    ], "a task on the list stopped the guest book from being filled"


def test_the_done_example_is_added_then_marked(guestbook) -> None:
    """Never born done: each done example is POSTed as a text alone and then marked
    with `{"done": true}`, through the id its own POST answered with, after that
    POST. A not-done example is never marked."""
    fake = guestbook("preview")

    assert seed_golden_set.main(["--base-url", BASE]) == 0

    _, tasks = _seed_corpus()
    done = [task["text"] for task in tasks if task["done"]]
    assert done, "the seed corpus holds no done example to mark"
    assert all("done" not in body for body in fake.posted_tasks), "an example was sent as done"

    ids_by_text = {task["text"]: task["id"] for task in fake.tasks}
    assert fake.patched_tasks == [(ids_by_text[text], {"done": True}) for text in done]
    for text in done:
        post = next(
            index
            for index, (method, path, body) in enumerate(fake.writes)
            if method == "POST" and path == TASKS and body.get("text") == text
        )
        patch = next(
            index
            for index, (method, path, _) in enumerate(fake.writes)
            if method == "PATCH" and path.endswith(ids_by_text[text])
        )
        assert post < patch, f"{text!r} was marked before it was added"


def test_the_boundary_corpus_is_opt_in(guestbook) -> None:
    """Values sitting exactly on the published limits are useful and are not default."""
    without = guestbook("preview")
    assert seed_golden_set.main(["--base-url", BASE]) == 0

    with_boundary = guestbook("preview")
    assert seed_golden_set.main(["--base-url", BASE, "--boundary"]) == 0

    assert len(with_boundary.posted) > len(without.posted)


def test_an_entry_the_application_refuses_fails_the_run(guestbook) -> None:
    """A corpus half in is worse than a corpus not in: the screen then lies about itself."""
    fake = guestbook("preview")
    fake.post_status = 422

    assert seed_golden_set.main(["--base-url", BASE]) == 1


def test_an_unreachable_environment_is_reported_rather_than_raised(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """It runs at the end of a deployment, where a traceback is the least useful answer."""

    def refuse(*_: object, **__: object) -> None:
        raise urllib.error.URLError("no route to host")

    monkeypatch.setattr(urllib.request, "urlopen", refuse)

    assert seed_golden_set.main(["--base-url", BASE]) == 1


def test_a_trailing_slash_on_the_base_url_is_tolerated(guestbook) -> None:
    """A Function URL comes back with one, and a caller will eventually pass it through."""
    fake = guestbook("preview")

    assert seed_golden_set.main(["--base-url", BASE + "/"]) == 0
    assert fake.posted

"""The seeder's two refusals, which are what make it safe to run on every deploy.

`scripts/deploy.sh` and `scripts/preview.sh` both call it unconditionally. That is
only defensible because it decides for itself whether to do anything:

- **It refuses production**, by asking the deployment which environment it is
  rather than inferring one from a URL. Test data in production cannot be undone
  by hand once a real visitor has replied to it, and a guard that depended on a
  caller passing the right flag would fail the first time somebody added a caller.
- **It refuses a guest book that already has entries**, which is what makes
  "seed every new environment" and "run on every deploy" the same sentence.

It posts `golden-set/seed/` -- the half of the corpus that exists to be looked at.
Which half is itself a property worth holding: seeding from the fixture half is
what coupled a preview's screen to a paging test's arithmetic.

`urllib.request.urlopen` is replaced rather than the seeder's own helpers, so what
runs here includes the JSON encoding, the headers and the method -- the parts a
test that stubbed `_get`/`_post` would have skipped over. That the round trip works
against a real application was established by pointing it at one.
"""

# `_Response` is named in a signature above its definition; under the syntax floor
# (py312, see pyproject.toml) an unquoted forward reference needs lazy annotations.
from __future__ import annotations

import io
import json
import urllib.error
import urllib.request
from typing import Any

import pytest
import seed_golden_set

from tests._golden_set import SEED_FILES, entries_of

BASE = "http://example.invalid/api"


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
    """A guest book that records what was posted to it."""

    def __init__(self, environment: str, entries: list[dict[str, Any]] | None = None) -> None:
        self.environment = environment
        self.entries = list(entries or [])
        self.posted: list[dict[str, Any]] = []
        self.post_status = 201

    def __call__(self, request: urllib.request.Request, timeout: float = 0) -> _Response:
        url = request.full_url
        if request.get_method() == "POST":
            body = json.loads(request.data or b"{}")
            self.posted.append(body)
            self.entries.append(body)
            return _Response(body, self.post_status)
        if url.endswith("/health"):
            return _Response({"status": "ok", "environment": self.environment, "version": "0"})
        return _Response({"items": self.entries[:1], "total": len(self.entries)})


@pytest.fixture
def guestbook(monkeypatch: pytest.MonkeyPatch):
    def install(environment: str, entries: list[dict[str, Any]] | None = None) -> Fake:
        fake = Fake(environment, entries)
        monkeypatch.setattr(urllib.request, "urlopen", fake)
        return fake

    return install


def test_an_empty_environment_gets_the_whole_seed_corpus(guestbook) -> None:
    """Every entry, in file order, through the API rather than into the database.

    The expectation is DERIVED from the corpus rather than written out here, and
    that is what keeps this test on the right side of the line
    `tests/fitness/test_golden_set.py::test_no_suite_reads_the_seed_corpus`
    draws: it asserts about the seeder, not about the data. Adding a welcome
    entry changes what a new environment shows and leaves this green -- which is
    the whole freedom the split was made to buy.
    """
    fake = guestbook("preview")

    assert seed_golden_set.main(["--base-url", BASE]) == 0

    expected = [entry for path in SEED_FILES for entry in entries_of(path)]
    assert len(fake.posted) == len(expected)
    assert [entry["author"] for entry in fake.posted] == [entry["author"] for entry in expected]
    assert set(fake.posted[0]) == {"author", "message"}, (
        "the seeder sends fields the write schema does not accept"
    )


def test_production_is_refused(guestbook) -> None:
    """The safety property, and the reason this can be wired into deploy.sh at all."""
    fake = guestbook("prod")

    assert seed_golden_set.main(["--base-url", BASE]) == 1
    assert fake.posted == []


def test_a_guest_book_with_entries_is_left_alone(guestbook) -> None:
    """So "every new environment" and "every deploy" are the same instruction."""
    fake = guestbook("stage", entries=[{"author": "Somebody", "message": "was here"}])

    assert seed_golden_set.main(["--base-url", BASE]) == 0
    assert fake.posted == []


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

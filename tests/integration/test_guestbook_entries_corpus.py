"""The rules, driven by the committed corpus rather than by invented values.

Why this file is separate from `test_guestbook_entries_service.py`: that one
states rules one at a time with the smallest value that shows each; this one runs
**every** case the corpus holds through the real stack and lets the file decide
the coverage. The two answer different questions -- "is the rule right" and "does
the rule hold for everything we ship as reference data" -- and merging them would
hide the second inside the first.

`tests/fitness/test_golden_set.py` has already proved the corpus is what it
claims, so a failure here is the *application* disagreeing with the corpus, never
the corpus disagreeing with itself. That ordering is what makes a red line here
readable.
"""

import uuid
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.contexts.guestbook.models.guestbook_entry import AUTHOR_MAX_LENGTH
from tests._golden_set import BOUNDARY, ORDINARY, REFUSED, entries_of

from .conftest import Entries

ENTRIES = "/api/guestbook-entries"


def _body(entry: dict[str, Any]) -> dict[str, str]:
    """A corpus entry as a request body.

    The bookkeeping keys (`case`, `refusal`) are dropped: the API ignores unknown
    fields, so sending them would not fail -- it would just quietly stop being the
    request the test meant to send.
    """
    return {"author": entry["author"], "message": entry["message"]}


def _ids(path: Any) -> list[str]:
    return [str(entry.get("case", entry["author"])) for entry in entries_of(path)]


# --------------------------------------------------------------------------- #
# Ordinary entries: everything the corpus ships as valid really is
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("entry", entries_of(ORDINARY), ids=_ids(ORDINARY))
def test_every_ordinary_corpus_entry_is_accepted(client: TestClient, fresh_database, entry) -> None:
    response = client.post(ENTRIES, json=_body(entry))

    assert response.status_code == 201, response.text


def test_the_whole_corpus_seeds_a_book_and_comes_back_newest_first(
    client: TestClient, fresh_database, entries: Entries
) -> None:
    """`BR-04` over the corpus, and the one assertion the file's ORDER exists for.

    The corpus lists entries in **writing** order; the list returns display order,
    which is its reverse. Asserting the reverse of the file rather than a
    hand-written list is what makes this a test of the rule instead of a second
    copy of the data.
    """
    written = entries_of(ORDINARY)
    for entry in written:
        assert client.post(ENTRIES, json=_body(entry)).status_code == 201

    page = client.get(ENTRIES).json()

    assert [row["author"] for row in page["items"]] == [
        e["author"].strip() for e in reversed(written)
    ]
    assert page["total"] == len(written)
    assert page["total_all"] == len(written)
    assert entries.count() == len(written)


def test_non_ascii_text_survives_the_whole_round_trip(client: TestClient, fresh_database) -> None:
    """Written, stored, read back -- byte for byte.

    The corpus is UTF-8 and the database column is text, and neither fact is
    worth anything if the value changes on the way. A machine whose default
    encoding is a single-byte code page fails here rather than three suites later
    on a count.

    The entry is found by being outside ASCII rather than by being in one
    language: what this proves is a property of the encoding, and the corpus is
    free to change which script it carries (`tests/fitness/test_golden_set.py`
    keeps it from carrying none).
    """
    entry = next(e for e in entries_of(ORDINARY) if any(ord(c) > 127 for c in e["author"]))

    created = client.post(ENTRIES, json=_body(entry)).json()
    read_back = client.get(f"{ENTRIES}/{created['id']}").json()

    assert read_back["author"] == entry["author"].strip()
    assert read_back["message"] == entry["message"].strip()


def test_line_breaks_inside_a_message_are_kept(client: TestClient, fresh_database) -> None:
    """`BR-01` trims the EDGES. Whitespace inside the message is the guest's own
    formatting and a service that collapsed it would be rewriting what they wrote."""
    entry = next(e for e in entries_of(ORDINARY) if "\n" in e["message"])

    stored = client.post(ENTRIES, json=_body(entry)).json()

    assert "\n" in stored["message"]
    assert stored["message"] == entry["message"].strip()


# --------------------------------------------------------------------------- #
# Boundary: exactly at the limit is accepted, and stored whole
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("entry", entries_of(BOUNDARY), ids=_ids(BOUNDARY))
def test_every_boundary_case_is_accepted(client: TestClient, fresh_database, entry) -> None:
    """The half of a boundary that is usually missing.

    A limit proved only where it refuses is a limit nobody has shown stands in
    the right place: the test passes identically whether the ceiling is 80 or 8000.
    """
    response = client.post(ENTRIES, json=_body(entry))

    assert response.status_code == 201, f"{entry['case']} was refused: {response.text}"


def test_a_value_at_the_limit_is_stored_whole_and_not_truncated(
    client: TestClient, fresh_database
) -> None:
    """The database column is bounded too, and a bound that truncates instead of
    refusing loses the tail silently -- the one failure mode nothing else here
    would notice."""
    from tests._golden_set import case

    at_max = case(BOUNDARY, "message_at_maximum")

    created = client.post(ENTRIES, json=_body(at_max)).json()
    read_back = client.get(f"{ENTRIES}/{created['id']}").json()

    assert read_back["message"] == at_max["message"].strip()
    assert len(read_back["message"]) == len(at_max["message"].strip())


def test_padding_is_trimmed_before_the_length_is_measured(
    client: TestClient, fresh_database
) -> None:
    """`BR-01`, in the order it happens. Measured before trimming, this entry is
    over the limit and would be refused; the corpus case exists to prove the
    order rather than to describe it."""
    from tests._golden_set import case

    padded = case(BOUNDARY, "padded_to_maximum")

    created = client.post(ENTRIES, json=_body(padded))

    assert created.status_code == 201
    assert created.json()["author"] == padded["author"].strip()


# --------------------------------------------------------------------------- #
# Refused: every case the corpus ships as refused really is
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("entry", entries_of(REFUSED), ids=_ids(REFUSED))
def test_every_refused_corpus_entry_is_refused_and_stores_nothing(
    client: TestClient, fresh_database, entries: Entries, entry
) -> None:
    """Refused **and nothing written** -- the second half is the one that bites.

    A validation error that has already inserted the row leaves a book holding an
    entry no rule allows, and the response says the opposite.
    """
    response = client.post(ENTRIES, json=_body(entry))

    assert response.status_code == 422, f"{entry['case']} was accepted: {response.text}"
    # What `"refusal": "validation"` in the corpus actually claims, asserted rather
    # than trusted: the schema refuses the body before a handler runs, so the answer
    # is FastAPI's `{"detail": [...]}` and carries no stable code. Until this, the
    # key was checked for truthiness by a fitness test and read by nobody -- it could
    # have said anything and every gate stayed green.
    assert entry["refusal"] == "validation", entry["case"]
    detail = response.json()["detail"]
    assert isinstance(detail, list) and detail, response.text
    assert all("code" not in item for item in detail), (
        f"{entry['case']} answered with a stable code; a schema refusal has none "
        "(spec/design/api.md § Refusals)"
    )
    assert entries.count() == 0


@pytest.mark.parametrize("entry", entries_of(REFUSED), ids=_ids(REFUSED))
def test_a_refused_value_is_refused_on_edit_as_well_as_on_create(
    client: TestClient, fresh_database, entry
) -> None:
    """The rule belongs to the entry, not to the route that happens to write it.

    `POST` and `PATCH` validate through different schemas, and a bound present on
    one and absent on the other is a hole reachable by editing rather than by
    creating -- which nothing in the create-path tests can see.
    """
    existing = client.post(ENTRIES, json={"author": "Anna", "message": "anything"}).json()

    field = (
        "author"
        if not entry["author"].strip() or len(entry["author"]) > AUTHOR_MAX_LENGTH
        else "message"
    )
    response = client.patch(f"{ENTRIES}/{existing['id']}", json={field: entry[field]})

    assert response.status_code == 422, f"{entry['case']} was accepted on PATCH: {response.text}"

    unchanged = client.get(f"{ENTRIES}/{existing['id']}").json()
    assert unchanged["author"] == "Anna"
    assert unchanged["message"] == "anything"


def test_a_refusal_leaves_the_rest_of_the_book_untouched(
    client: TestClient, fresh_database, entries: Entries
) -> None:
    """A refused write is not a transaction that half-happened."""
    for entry in entries_of(ORDINARY):
        client.post(ENTRIES, json=_body(entry))
    before = entries.authors_newest_first()

    for entry in entries_of(REFUSED):
        assert client.post(ENTRIES, json=_body(entry)).status_code == 422

    assert entries.authors_newest_first() == before


def test_deleting_the_whole_seeded_book_empties_it(
    client: TestClient, fresh_database, entries: Entries
) -> None:
    """`BR-03` at scale, and the only place the delete path meets more than one row.

    Each id is deleted once and refuses the second time, so the loop also proves
    the refusal is per entry rather than a state the whole collection enters.
    """
    ids = [client.post(ENTRIES, json=_body(e)).json()["id"] for e in entries_of(ORDINARY)]

    for entry_id in ids:
        assert client.delete(f"{ENTRIES}/{entry_id}").status_code == 204
        assert client.delete(f"{ENTRIES}/{entry_id}").status_code == 404

    assert entries.count() == 0
    assert client.get(ENTRIES).json() == {"items": [], "total": 0, "total_all": 0}
    assert uuid.UUID(ids[0])


# --------------------------------------------------------------------------- #
# `BR-05` over the corpus: narrowing and paging the real reference data
# --------------------------------------------------------------------------- #


def _seed_ordinary(client: TestClient) -> list[dict[str, Any]]:
    """The whole ordinary corpus, written in its own order, through the API."""
    written = entries_of(ORDINARY)
    for entry in written:
        assert client.post(ENTRIES, json=_body(entry)).status_code == 201
    return written


@pytest.mark.parametrize("entry", entries_of(ORDINARY), ids=_ids(ORDINARY))
def test_every_ordinary_corpus_entry_can_be_found_by_its_own_signature(
    client: TestClient, fresh_database, entry
) -> None:
    """Each corpus entry, searched for by the signature the corpus gave it.

    Parametrised over the file rather than over one chosen name, so the
    single-character signature (`D`) and the one built from non-ASCII letters are
    both in the search path -- and neither is here because somebody remembered
    to add it.
    """
    _seed_ordinary(client)
    signature = entry["author"].strip()

    page = client.get(ENTRIES, params={"q": signature}).json()

    assert signature in [row["author"] for row in page["items"]]
    assert page["total"] >= 1
    assert page["total_all"] == len(entries_of(ORDINARY))


def test_paging_the_seeded_corpus_tiles_it_exactly_once(client: TestClient, fresh_database) -> None:
    """Consecutive pages of two, walked to the end, reassemble the whole book.

    The claim is that the windows tile: no entry appears twice and none is
    missed. Over a corpus of five that means an odd last page, which is the case
    an even-sized fixture would never produce.
    """
    written = _seed_ordinary(client)
    expected = [entry["author"].strip() for entry in reversed(written)]

    collected: list[str] = []
    offset = 0
    while True:
        page = client.get(ENTRIES, params={"limit": 2, "offset": offset}).json()
        assert page["total"] == len(written), "the population changed while it was being paged"
        if not page["items"]:
            break
        collected += [row["author"] for row in page["items"]]
        offset += 2

    assert collected == expected


def test_reading_the_seeded_corpus_oldest_first_gives_the_file_back(
    client: TestClient, fresh_database
) -> None:
    """The one place the corpus's own order is the expected answer rather than
    its reverse: `entries-ordinary.json` is in WRITING order, and oldest-first is
    writing order."""
    written = _seed_ordinary(client)

    page = client.get(ENTRIES, params={"sort": "oldest"}).json()

    assert [row["author"] for row in page["items"]] == [e["author"].strip() for e in written]

"""The HTTP contract, over real storage.

What is asserted here is the seam the unit tests cannot reach: the status code
each outcome carries, the shape of each refusal body, and the fact that the
router's translation of a domain exception matches what `spec/design/api.md`
publishes. The rules themselves are proved one layer down.

Refusal bodies are asserted by their **code**, not by their sentence. The code is
the contract a screen branches on and must never change; the sentence is copy and
may be reworded without breaking anything -- pinning it here would make every
rewording a failing test, which is how a suite teaches people to stop rewording.
"""

import uuid

from app.contexts.guestbook.schemas.guestbook_entries import QUERY_MAX_LENGTH

from .conftest import Entries

ENTRIES = "/api/guestbook-entries"


def _post(client, author: str = "Anna", message: str = "Good morning!"):
    return client.post(ENTRIES, json={"author": author, "message": message})


def test_creating_an_entry_answers_201_with_the_stored_entry(client, fresh_database) -> None:
    response = _post(client)

    assert response.status_code == 201
    body = response.json()
    assert body["author"] == "Anna"
    assert body["message"] == "Good morning!"
    assert uuid.UUID(body["id"])


def test_a_created_entry_is_readable_at_its_own_address(client, fresh_database) -> None:
    created = _post(client).json()

    response = client.get(f"{ENTRIES}/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_the_list_answers_200_with_every_entry_in_an_envelope(client, fresh_database) -> None:
    _post(client, author="first")
    _post(client, author="second")

    response = client.get(ENTRIES)

    assert response.status_code == 200
    body = response.json()
    assert [entry["author"] for entry in body["items"]] == ["second", "first"]
    assert body["total"] == 2
    assert body["total_all"] == 2


def test_an_empty_book_answers_200_with_an_empty_page_not_404(client, fresh_database) -> None:
    """ "There are no entries" is a successful answer to "list the entries". A 404
    here would make an empty guest book indistinguishable from a broken route."""
    response = client.get(ENTRIES)

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "total_all": 0}


def test_editing_an_entry_answers_200_with_the_new_state(client, fresh_database) -> None:
    created = _post(client).json()

    response = client.patch(f"{ENTRIES}/{created['id']}", json={"message": "corrected"})

    assert response.status_code == 200
    assert response.json()["message"] == "corrected"
    assert response.json()["created_at"] == created["created_at"]


def test_a_patch_that_sets_no_field_is_refused_rather_than_succeeding_silently(
    client, fresh_database
) -> None:
    created = _post(client).json()

    response = client.patch(f"{ENTRIES}/{created['id']}", json={})

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "guestbook_entry_empty_patch"


def test_deleting_an_entry_answers_204_with_no_body(
    client, fresh_database, entries: Entries
) -> None:
    created = _post(client).json()

    response = client.delete(f"{ENTRIES}/{created['id']}")

    assert response.status_code == 204
    assert response.content == b""
    assert entries.exists(created["id"]) is False


def test_deleting_the_same_entry_twice_answers_404_the_second_time(client, fresh_database) -> None:
    created = _post(client).json()
    client.delete(f"{ENTRIES}/{created['id']}")

    response = client.delete(f"{ENTRIES}/{created['id']}")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "guestbook_entry_not_found"


def test_every_route_taking_an_id_answers_404_for_one_that_does_not_resolve(
    client, fresh_database
) -> None:
    """One test over the three routes rather than three tests: the refusal is the
    same fact each time, and stating it once is what makes a fourth route added
    later obviously missing from the list."""
    missing = uuid.uuid4()

    for response in (
        client.get(f"{ENTRIES}/{missing}"),
        client.patch(f"{ENTRIES}/{missing}", json={"message": "anything"}),
        client.delete(f"{ENTRIES}/{missing}"),
    ):
        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "guestbook_entry_not_found"


def test_an_id_that_is_not_a_uuid_is_refused_before_anything_reads_storage(
    client, fresh_database
) -> None:
    """422 and not 404: "that is not an id" and "no entry has that id" are different
    facts, and only the first one is fixed by correcting the request."""
    response = client.get(f"{ENTRIES}/not-a-uuid")

    assert response.status_code == 422


def test_an_entry_with_an_empty_author_is_refused_and_nothing_is_stored(
    client, fresh_database, entries: Entries
) -> None:
    response = _post(client, author="   ")

    assert response.status_code == 422
    assert entries.count() == 0


# --------------------------------------------------------------------------- #
# The four read parameters, on the wire
# --------------------------------------------------------------------------- #


def test_the_read_parameters_reach_the_service_from_the_query_string(
    client, fresh_database
) -> None:
    """One test over all four rather than four tests: the rules behind them are
    proved a layer down, and what is unproved here is only that the router binds
    each name to the right argument -- which is one fact, and it fails all at once.
    """
    _post(client, author="Anna", message="the sought message")
    _post(client, author="Brian", message="the sought message")
    _post(client, author="Clara", message="another message")

    response = client.get(ENTRIES, params={"q": "sought", "sort": "oldest", "limit": 1})

    assert response.status_code == 200
    body = response.json()
    assert [entry["author"] for entry in body["items"]] == ["Anna"]
    assert body["total"] == 2
    assert body["total_all"] == 3


def test_a_parameter_outside_its_bounds_is_refused_rather_than_clamped(
    client, fresh_database
) -> None:
    """422 and not a silent fall back to the default. A caller that asked for
    `limit=0` meant something, and serving it twenty entries would make the
    screen and the request disagree with nobody able to see it."""
    for params in (
        {"limit": 0},
        {"limit": 101},
        {"offset": -1},
        {"sort": "anything-at-all"},
        {"q": "x" * 201},
    ):
        response = client.get(ENTRIES, params=params)
        assert response.status_code == 422, f"{params} was accepted"


def test_a_phrase_of_nothing_but_padding_is_no_phrase_rather_than_a_refusal(
    client, fresh_database
) -> None:
    """The order the bound is applied in, asserted from outside.

    `spec/design/api.md` section Narrowing has always said the phrase is trimmed
    before it is measured, and until `NormalizedText` was put ahead of `Query` it
    was not: `max_length` saw the padding, so two hundred and five spaces earned a
    422 while two hundred and five spaces in a SIGNATURE was simply empty. One
    document, two orders, and the one a caller met was the undocumented one.

    Two hundred and five rather than a round number: it has to be past the bound,
    or the old behaviour and the new one agree and this proves nothing.
    """
    _post(client, author="Anna")

    response = client.get(ENTRIES, params={"q": " " * (QUERY_MAX_LENGTH + 5)})

    assert response.status_code == 200, "a phrase of padding is no phrase, not a refusal"
    body = response.json()
    assert body["total"] == 1, "no phrase means the question is the whole book"
    assert body["total_all"] == 1


def test_a_phrase_over_the_bound_in_code_points_is_still_refused(client, fresh_database) -> None:
    """The other side of the same move: trimming first must not stop the bound
    biting. Emoji rather than letters, because a phrase of 101 grinning faces is
    202 UTF-16 code units and 101 code points -- so a bound measured in the wrong
    unit would refuse this, and the contract says 200 code points."""
    _post(client, author="Anna")

    accepted = client.get(ENTRIES, params={"q": chr(0x1F600) * QUERY_MAX_LENGTH})
    refused = client.get(ENTRIES, params={"q": chr(0x1F600) * (QUERY_MAX_LENGTH + 1)})

    assert accepted.status_code == 200
    assert refused.status_code == 422


def test_a_search_that_matches_nothing_is_an_empty_page_over_a_non_empty_book(
    client, fresh_database
) -> None:
    """The two counts are what let the screen say "nothing matches that search"
    rather than "the book is empty" -- which are different sentences, and only one
    of them is true here."""
    _post(client, author="Anna")

    body = client.get(ENTRIES, params={"q": "no-such-word"}).json()

    assert body["items"] == []
    assert body["total"] == 0
    assert body["total_all"] == 1

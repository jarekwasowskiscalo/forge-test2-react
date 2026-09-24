"""The contract's own rules, with no database and no HTTP in sight.

These are the bounds `spec/design/api.md` § Refusals publishes and
`app/contexts/guestbook/models/guestbook_entry.py` enforces at the column. What is asserted here is
the *behaviour at the boundary*: exactly at the limit is accepted, one past it
is refused. That is the off-by-one a `<` written as `<=` produces, and nothing
else in the suite would notice it -- an integration test uses a plausible name,
never one of exactly eighty characters.

Stripping is asserted before length for the same reason it happens in that
order on the server: `str_strip_whitespace` runs first, so a signature of
nothing but spaces is *empty*, not three characters long. The frontend copies
this rule (`frontend/src/contexts/guestbook/lib/guestbookEntry.ts`) and its own test pins the same
boundary, which is what keeps the two from drifting into disagreeing about what
fits.
"""

import datetime
import uuid

import pytest
from pydantic import ValidationError

from app.contexts.guestbook.models.guestbook_entry import AUTHOR_MAX_LENGTH, MESSAGE_MAX_LENGTH
from app.contexts.guestbook.schemas.guestbook_entries import (
    GuestbookEntryCreate,
    GuestbookEntryPage,
    GuestbookEntryRead,
    GuestbookEntrySort,
    GuestbookEntryUpdate,
)


@pytest.mark.req("CR-2609-9b1e/R-1")
def test_a_created_entry_keeps_what_was_written() -> None:
    entry = GuestbookEntryCreate(author="Anna", message="Good morning!")

    assert entry.author == "Anna"
    assert entry.message == "Good morning!"


@pytest.mark.req("CR-2609-9b1e/R-2")
def test_surrounding_whitespace_is_stripped_before_anything_else_looks_at_it() -> None:
    entry = GuestbookEntryCreate(author="  Anna  ", message="\n Good morning! \n")

    assert entry.author == "Anna"
    assert entry.message == "Good morning!"


@pytest.mark.parametrize("blank", ["", " ", "   ", "\t", "\n"])
@pytest.mark.req("CR-2609-9b1e/R-2")
def test_a_signature_of_nothing_but_whitespace_is_empty_not_short(blank: str) -> None:
    """The trap: without stripping first, `"   "` measures three characters and passes."""
    with pytest.raises(ValidationError):
        GuestbookEntryCreate(author=blank, message="anything")


@pytest.mark.parametrize("blank", ["", "   ", "\n\n"])
@pytest.mark.req("CR-2609-9b1e/R-2")
def test_a_message_of_nothing_but_whitespace_is_refused(blank: str) -> None:
    with pytest.raises(ValidationError):
        GuestbookEntryCreate(author="Anna", message=blank)


@pytest.mark.req("CR-2609-9b1e/R-2")
def test_a_signature_of_exactly_the_maximum_length_is_accepted() -> None:
    entry = GuestbookEntryCreate(author="a" * AUTHOR_MAX_LENGTH, message="anything")

    assert len(entry.author) == AUTHOR_MAX_LENGTH


@pytest.mark.req("CR-2609-9b1e/R-2")
def test_one_character_past_the_signature_maximum_is_refused() -> None:
    with pytest.raises(ValidationError):
        GuestbookEntryCreate(author="a" * (AUTHOR_MAX_LENGTH + 1), message="anything")


@pytest.mark.req("CR-2609-9b1e/R-2")
def test_a_message_of_exactly_the_maximum_length_is_accepted() -> None:
    entry = GuestbookEntryCreate(author="Anna", message="x" * MESSAGE_MAX_LENGTH)

    assert len(entry.message) == MESSAGE_MAX_LENGTH


@pytest.mark.req("CR-2609-9b1e/R-2")
def test_one_character_past_the_message_maximum_is_refused() -> None:
    with pytest.raises(ValidationError):
        GuestbookEntryCreate(author="Anna", message="x" * (MESSAGE_MAX_LENGTH + 1))


@pytest.mark.req("CR-2609-9b1e/R-4")
def test_an_update_may_set_one_field_and_leave_the_other_absent() -> None:
    """A PATCH's absent field means "do not touch", which is why it is `None` and
    not an empty string -- the service branches on exactly that distinction."""
    update = GuestbookEntryUpdate(message="corrected")

    assert update.author is None
    assert update.message == "corrected"


@pytest.mark.req("CR-2609-9b1e/R-2")
def test_an_update_setting_nothing_is_a_valid_shape_and_a_refusal_elsewhere() -> None:
    """The empty body parses; the router refuses it.

    The refusal lives beside the endpoint (`app/contexts/guestbook/routers/guestbook_entries.py`)
    because the sentence an operator reads about it is about the request, not
    about the shape -- `conventions.md` § Layers. Asserting the shape is valid
    here is what stops somebody "fixing" it into the schema and leaving the
    router's branch unreachable.
    """
    update = GuestbookEntryUpdate()

    assert update.author is None
    assert update.message is None


@pytest.mark.req("CR-2609-9b1e/R-2")
def test_an_update_still_refuses_a_field_that_is_present_and_empty() -> None:
    """Present-and-blank is a different intent from absent, and it is refused:
    "clear the message" is not something an entry supports (`BR-01`)."""
    with pytest.raises(ValidationError):
        GuestbookEntryUpdate(message="   ")


# --------------------------------------------------------------------------- #
# The read envelope and the sort it is read in
# --------------------------------------------------------------------------- #


@pytest.mark.req("CR-2609-9b1e/R-3")
def test_the_sort_has_exactly_two_values_and_they_are_their_own_wire_words() -> None:
    """A closed set, and each member equal to the string it travels as.

    The equality is what lets a step, a test or a query string say `"newest"` and
    mean the member -- without it, every comparison would need `.value` and the
    one place somebody forgot would compare a member to a string and be quietly
    false.
    """
    assert [member.value for member in GuestbookEntrySort] == ["newest", "oldest"]

    # Compared through a `str`-typed name rather than against a literal: the
    # claim is that a member IS the string, and mypy reads a literal comparison
    # as an impossible one and refuses it before it can be made.
    newest: str = "newest"
    oldest: str = "oldest"
    assert newest == GuestbookEntrySort.NEWEST
    assert oldest == GuestbookEntrySort.OLDEST


@pytest.mark.req("CR-2609-9b1e/R-3")
def test_a_word_that_is_not_a_sort_is_refused_rather_than_defaulted() -> None:
    """Falling back to the default would leave a caller that misspelled `oldest`
    reading the newest first while its screen said otherwise -- and nothing
    anywhere would say so."""
    with pytest.raises(ValueError):
        GuestbookEntrySort("anything-at-all")


def _read(author: str) -> GuestbookEntryRead:
    instant = datetime.datetime(2026, 8, 31, 12, 0, tzinfo=datetime.UTC)
    return GuestbookEntryRead(
        id=uuid.uuid4(),
        author=author,
        message="anything",
        created_at=instant,
        updated_at=instant,
    )


@pytest.mark.req("CR-2609-9b1e/R-7")
def test_the_page_carries_two_counts_that_are_free_to_differ_from_its_length() -> None:
    """The envelope's whole purpose, asserted as a shape rather than as a query.

    A page of one over a population of nineteen is the case
    `e2e/harness/list_response.py` was written about: the page length is a
    plausible-looking count, so nothing about a wrong one looks wrong.
    """
    page = GuestbookEntryPage(items=[_read("Anna")], total=19, total_all=42)

    assert len(page.items) == 1
    assert page.total == 19
    assert page.total_all == 42


@pytest.mark.parametrize("field", ["total", "total_all"])
@pytest.mark.req("CR-2609-9b1e/R-7")
def test_a_negative_count_is_not_a_page(field: str) -> None:
    """There is no reading of "minus one entries", so the shape refuses it here
    rather than letting it reach a screen that would render it."""
    counts = {"total": 0, "total_all": 0} | {field: -1}

    with pytest.raises(ValidationError):
        GuestbookEntryPage(items=[], **counts)


@pytest.mark.req("CR-2609-9b1e/R-7")
def test_an_empty_page_is_a_valid_answer() -> None:
    """A search that matched nothing, and an empty book, are both this shape --
    which is why neither of them is a 404."""
    page = GuestbookEntryPage(items=[], total=0, total_all=0)

    assert page.items == []

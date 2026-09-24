"""The service's rules, against a real database.

These are the assertions that need storage to be true at all: an ordering the
database performs, a timestamp column that must not move, a row that must
actually stop existing. Everything provable without a database is in
`tests/unit/`.

Each test asks for `fresh_database`, so the entries it writes cannot be seen by
any other test -- and, more to the point, the counts it asserts are counts of its
own writes rather than of whatever the session-wide database has accumulated.
"""

import datetime as dt
import uuid

import pytest

from app.contexts.guestbook.models.guestbook_entry import AUTHOR_MAX_LENGTH, GuestbookEntry
from app.contexts.guestbook.schemas.guestbook_entries import (
    GuestbookEntryCreate,
    GuestbookEntrySort,
    GuestbookEntryUpdate,
)
from app.contexts.guestbook.services.guestbook_entries import (
    GuestbookEntryNotFoundError,
    create_entry,
    delete_entry,
    get_entry,
    list_entries,
    update_entry,
)

from .conftest import Entries


def _write(author: str, message: str = "anything"):
    return create_entry(GuestbookEntryCreate(author=author, message=message))


def _authors(**kwargs) -> list[str]:
    """The signatures on one page, in the order the service returned them.

    A helper rather than a comprehension at fourteen call sites, because every
    one of these tests is about the ORDER or the MEMBERSHIP of that list and
    nothing else -- the two counts get their own assertions.
    """
    return [entry.author for entry in list_entries(**kwargs).items]


@pytest.mark.req("CR-2609-9b1e/R-1")
def test_a_created_entry_gets_an_id_the_caller_did_not_choose(fresh_database) -> None:
    entry = _write("Anna")

    assert isinstance(entry.id, uuid.UUID)


@pytest.mark.req("CR-2609-9b1e/R-1")
def test_a_created_entry_carries_one_instant_in_both_timestamps(fresh_database) -> None:
    """`BR-02`: an entry that has never been edited must be distinguishable from one
    that has, and the distinguishing fact is the two columns being equal.

    Two separate `datetime.now()` calls would round to the same value most of the
    time and differ occasionally, which is the worst of both -- a screen that says
    "corrected" on a fresh entry once in a hundred loads.
    """
    entry = _write("Anna")

    assert entry.created_at == entry.updated_at


@pytest.mark.req("CR-2609-9b1e/R-3")
def test_the_list_comes_back_newest_first(fresh_database, entries: Entries) -> None:
    """`BR-04`. The order is the database's, asserted through the service and again
    against the rows, so a service that sorted in Python would still be caught."""
    _write("first")
    _write("second")
    _write("third")

    assert _authors() == ["third", "second", "first"]
    assert entries.authors_newest_first() == ["third", "second", "first"]


@pytest.mark.req("CR-2609-9b1e/R-3")
def test_entries_sharing_an_instant_still_have_a_total_order(fresh_database) -> None:
    """The tie-break on `id` is what makes the order total.

    Without it two entries with the same `created_at` come back in whatever order
    the planner felt like -- stable in a test, and not stable under a paginated
    read, where it shows one entry twice and silently drops another. The
    collision is written directly rather than raced for, because the clock is too
    coarse to produce it on demand and a test that waits for luck is a test that
    fails on somebody else's machine.
    """
    instant = dt.datetime(2026, 8, 30, 20, 0, tzinfo=dt.UTC)
    ids = sorted(uuid.uuid4() for _ in range(3))
    with fresh_database() as session:
        for index, entry_id in enumerate(ids):
            session.add(
                GuestbookEntry(
                    id=entry_id,
                    author=f"autor {index}",
                    message="ten sam moment",
                    created_at=instant,
                    updated_at=instant,
                )
            )
        session.commit()

    listed = [entry.id for entry in list_entries().items]

    # Descending on id, because the ORDER BY is `created_at DESC, id DESC`.
    assert listed == list(reversed(ids))
    assert listed == [entry.id for entry in list_entries().items], "the order is not stable"

    # And the tie-break turns with the sort, so oldest-first really is the
    # reverse of newest-first rather than the same pair in the same order.
    oldest = [entry.id for entry in list_entries(sort=GuestbookEntrySort.OLDEST).items]
    assert oldest == ids


@pytest.mark.req("CR-2609-9b1e/R-4")
def test_an_edit_moves_updated_at_and_leaves_created_at_alone(fresh_database) -> None:
    """`BR-02`, the half that matters: "when was this written" survives every
    later correction."""
    entry = _write("Anna", "the first version")

    edited = update_entry(entry.id, GuestbookEntryUpdate(message="the second version"))

    assert edited.message == "the second version"
    assert edited.created_at == entry.created_at
    assert edited.updated_at > entry.updated_at


@pytest.mark.req("CR-2609-9b1e/R-4")
def test_an_edit_leaves_untouched_a_field_the_caller_did_not_send(fresh_database) -> None:
    """PATCH semantics: absent means "do not touch", never "clear"."""
    entry = _write("Anna", "a message")

    edited = update_entry(entry.id, GuestbookEntryUpdate(message="another message"))

    assert edited.author == "Anna"


@pytest.mark.req("CR-2609-9b1e/R-4")
def test_editing_an_unknown_entry_refuses(fresh_database) -> None:
    with pytest.raises(GuestbookEntryNotFoundError):
        update_entry(uuid.uuid4(), GuestbookEntryUpdate(message="anything"))


@pytest.mark.req("CR-2609-9b1e/R-5")
def test_deleting_removes_the_row_rather_than_flagging_it(fresh_database, entries: Entries) -> None:
    """`BR-03`: deletion is permanent. A soft delete would leave the row readable
    by anything that queries the table directly, which is not what a guest who
    asked for their entry to be removed was told happened."""
    entry = _write("Anna")

    delete_entry(entry.id)

    assert entries.exists(entry.id) is False
    assert entries.count() == 0


@pytest.mark.req("CR-2609-9b1e/R-5")
def test_deleting_the_same_entry_twice_refuses_the_second_time(fresh_database) -> None:
    """Reporting success for something that was not done is how a caller comes to
    believe two deletes happened."""
    entry = _write("Anna")
    delete_entry(entry.id)

    with pytest.raises(GuestbookEntryNotFoundError):
        delete_entry(entry.id)


@pytest.mark.req("CR-2609-9b1e/R-5")
def test_reading_an_unknown_entry_refuses(fresh_database) -> None:
    with pytest.raises(GuestbookEntryNotFoundError):
        get_entry(uuid.uuid4())


@pytest.mark.req("CR-2609-9b1e/R-1")
def test_a_written_entry_reads_back_field_for_field(fresh_database) -> None:
    written = _write("Anna", "Good morning!")

    read = get_entry(written.id)

    assert read == written


# --------------------------------------------------------------------------- #
# `BR-05` -- narrowing the book by a phrase, and cutting it into pages
# --------------------------------------------------------------------------- #


@pytest.mark.req("CR-2609-9b1e/R-6")
def test_a_phrase_matches_the_signature_or_the_text(fresh_database) -> None:
    """Both columns, because a guest looking for a name cannot know whether that
    name signed an entry or is written inside somebody else's.

    One field would make half the hits invisible, and invisible in the way that
    looks exactly like "there are none".
    """
    _write("Anna", "anything")
    _write("Brian", "greetings to Anna")
    _write("Clara", "nothing in common")

    assert sorted(_authors(query="Ann")) == ["Anna", "Brian"]


@pytest.mark.req("CR-2609-9b1e/R-6")
def test_the_search_ignores_the_case_of_the_phrase(fresh_database) -> None:
    _write("Anna", "Good morning")

    assert _authors(query="ANNA") == ["Anna"]
    assert _authors(query="anna") == ["Anna"]


@pytest.mark.req("CR-2609-9b1e/R-6")
def test_non_ascii_letters_survive_the_search_unchanged(fresh_database) -> None:
    """The phrase reaches the database as a `LIKE` pattern, so this is really an
    assertion that nothing along the way mangles the encoding.

    Same case on both sides, so the claim is about bytes and nothing else. That
    `Å` also finds `å` is a different claim and gets its own test below.

    The characters are outside ASCII and belong to no particular language on
    purpose: what is being proved is a property of the encoding, and tying it to
    one alphabet would make the test read as being about that alphabet.
    """
    _write("Ångström", "blåbærsyltetøj og smørrebrød")

    assert _authors(query="smørrebrød") == ["Ångström"]
    assert _authors(query="Ångström") == ["Ångström"]


@pytest.mark.req("CR-2609-9b1e/R-2")
def test_a_stored_value_is_normalized_and_within_the_bound_in_code_points(
    fresh_database,
) -> None:
    """`D-01`…`D-04`'s newest member, asserted where it has to be true: the row.

    The unit tests prove the SCHEMA normalizes. This proves the value that reaches
    storage and comes back is the normalized one -- a service that measured the
    trimmed form and wrote the raw one would satisfy every length assertion in the
    suite and still put a decomposed name in the column, where `varchar(80)`
    counts code points and would refuse the next one like it.

    Eighty decomposed accented letters: 160 code points as typed, 80 after NFC.
    Under the old rule this was refused outright, which is the other half of why
    the invariant is worth stating.
    """
    decomposed = ("e" + chr(0x0301)) * AUTHOR_MAX_LENGTH
    precomposed = chr(0x00E9) * AUTHOR_MAX_LENGTH

    written = _write(decomposed, "  a message with padding  ")
    read_back = get_entry(written.id)

    assert read_back.author == precomposed, "the stored value is the composed one"
    assert len(read_back.author) == AUTHOR_MAX_LENGTH, "and it fits the column exactly"
    assert read_back.message == "a message with padding", "trimmed before it was stored"


@pytest.mark.req("CR-2609-9b1e/R-6")
def test_the_search_folds_case_across_non_ascii_letters(fresh_database) -> None:
    """Postgres folds case by Unicode, so a lower-case phrase finds an upper-case
    signature even outside ASCII.

    Its own test rather than a line in the one above, because the two claims fail
    for different reasons: that one fails when something mangles the encoding,
    this one when the folding rule changes under the search.
    """
    _write("Ångström", "anything")

    assert _authors(query="ångström") == ["Ångström"]


@pytest.mark.req("CR-2609-9b1e/R-6")
def test_a_phrase_of_only_spaces_is_no_phrase_at_all(fresh_database) -> None:
    """Stripped before it is measured, exactly as `BR-01` strips what it stores.

    Treating it as a phrase would search for a space and hand back only the
    entries that happen to contain one -- to somebody who typed nothing.
    """
    _write("Anna")
    _write("Brian")

    assert sorted(_authors(query="   ")) == ["Anna", "Brian"]
    assert sorted(_authors(query=None)) == ["Anna", "Brian"]


@pytest.mark.req("CR-2609-9b1e/R-6")
def test_a_wildcard_in_a_phrase_matches_itself_and_not_everything(fresh_database) -> None:
    """`%` and `_` are `LIKE` wildcards. Unescaped, a guest searching for `100%`
    would match the whole book -- silently, and looking exactly like a search
    that found a lot."""
    _write("Anna", "100% off everything")
    _write("Brian", "nothing about discounts")

    assert _authors(query="100%") == ["Anna"]
    # A bare `%` finds the entry that contains a percent sign, and only it. As a
    # wildcard it would have matched the whole book, which is the failure this
    # assertion is shaped to tell apart from a search that legitimately found a
    # lot: one of two, not two of two.
    assert _authors(query="%") == ["Anna"]
    assert _authors(query="_") == []


@pytest.mark.req("CR-2609-9b1e/R-7")
def test_the_two_counts_describe_the_population_and_the_book_never_the_page(
    fresh_database,
) -> None:
    """The whole reason the envelope exists.

    `len(items)` is a plausible-looking number, so a screen that derived either
    count from the page would be wrong in a way nobody notices: "3 matches" over
    a page of three, out of nine.
    """
    for index in range(5):
        _write(f"Anna {index}", "the sought message")
    for index in range(4):
        _write(f"Brian {index}", "another message")

    page = list_entries(query="sought", limit=2)

    assert len(page.items) == 2
    assert page.total == 5, "total counts what matches, not what fits on the page"
    assert page.total_all == 9, "total_all counts the book, and the phrase does not touch it"


@pytest.mark.req("CR-2609-9b1e/R-7")
def test_a_page_is_a_window_the_caller_moves(fresh_database) -> None:
    """Consecutive windows over a total order tile the book: no entry twice, none
    missed. That is the property `BR-04`'s tie-break exists for, and a page is
    the only place it can be observed."""
    for name in ("first", "second", "third", "fourth", "fifth"):
        _write(name)

    first = _authors(limit=2, offset=0)
    second = _authors(limit=2, offset=2)
    third = _authors(limit=2, offset=4)

    assert first == ["fifth", "fourth"]
    assert second == ["third", "second"]
    assert third == ["first"]
    assert first + second + third == _authors(limit=5)


@pytest.mark.req("CR-2609-9b1e/R-7")
def test_an_offset_past_the_end_is_an_empty_page_and_not_an_error(fresh_database) -> None:
    _write("Anna")

    page = list_entries(offset=50)

    assert page.items == []
    assert page.total == 1, "the book did not shrink because the caller asked past its end"


@pytest.mark.req("CR-2609-9b1e/R-3")
def test_reading_the_book_oldest_first_reverses_it(fresh_database) -> None:
    """`BR-04` in the other direction. Asserted as the reverse of the default
    rather than as a written-out list, because the claim is that the two orders
    are opposites -- a second hand-written list would pass even if they were not.
    """
    for name in ("first", "second", "third"):
        _write(name)

    assert _authors(sort=GuestbookEntrySort.OLDEST) == list(reversed(_authors()))


@pytest.mark.req("CR-2609-9b1e/R-7")
def test_a_search_and_a_sort_and_a_page_compose(fresh_database) -> None:
    """Each of the three is proved on its own above; this is the one assertion
    that they still hold when applied together, which is how the screen actually
    calls this -- somebody types a phrase, flips the order, and presses for more.
    """
    for name in ("Anna", "Brian", "Clara", "Diana"):
        _write(name, "a shared message")
    _write("Edward", "does not match")

    page = list_entries(query="shared", sort=GuestbookEntrySort.OLDEST, limit=2, offset=1)

    assert [entry.author for entry in page.items] == ["Brian", "Clara"]
    assert page.total == 4
    assert page.total_all == 5

"""The guest book, in steps.

This module is where business language becomes HTTP and back again. The
`.feature` file says "the entry should be refused"; the fact that a refusal
is a 422 with a code lives here, so a change to the contract is a change to one
file rather than to every scenario.

Assertions go through `e2e.harness.assertions` without exception -- pytest does
not rewrite asserts in this package, so a bare `assert a == b` here prints its
message and nothing else. That is what keeps a whole response body out of the
JUnit `<failure>` element, and it is invisible unless it is written down.
"""

import uuid
from typing import Any

from pytest_bdd import given, parsers, then, when

from e2e.harness.assertions import found, should_answer, should_be
from e2e.harness.client import Row
from e2e.harness.list_response import row_where, rows, total_of
from e2e.suite.golden_set import BOUNDARY, ORDINARY, REFUSED, bodies_of, body_of, described
from e2e.suite.target import Target

#: The one resource this module drives. Named once: a path spelled a second time
#: is a path that can be spelled differently.
ENTRIES = "/guestbook-entries"


#: An id no entry can have. Generated per call rather than fixed, so a scenario
#: cannot accidentally pass because a previous run left that exact row behind.
def _unknown_id() -> str:
    return str(uuid.uuid4())


def _write(target: Target, author: str, message: str) -> Row:
    """Create one entry and hand back what the application stored.

    Used by the `Given` steps, which set a scenario's world up. They assert
    the write succeeded: a precondition that silently failed produces a `Then`
    about the wrong thing, and the reader is sent to the application over a
    fixture that never ran.
    """
    answer = target.api.send("POST", ENTRIES, body={"author": author, "message": message})
    should_answer(answer, 201, meaning="the entry to be stored")
    payload = answer.payload
    assert isinstance(payload, dict), f"expected the stored entry, got {answer}"
    return payload


# --------------------------------------------------------------------------
# Given -- the world before the scenario acts
# --------------------------------------------------------------------------


@given("the guestbook is empty")
def book_is_empty(target: Target) -> None:
    """Nothing to do, and the step still earns its place.

    The world is emptied before every scenario by the autouse `empty_world`
    fixture, so this asserts rather than acts -- and asserting it is the point:
    a scenario whose counts start from somebody else's rows fails with a wrong
    number, which reads as an application defect.
    """
    answer = target.api.get(ENTRIES)
    should_answer(answer, 200, meaning="the guest book to be readable")
    should_be(len(rows(answer)), 0, subject="the number of entries the book starts with")


@given(parsers.parse('the guestbook holds an entry signed "{author}" with the message "{message}"'))
def an_entry_exists(target: Target, author: str, message: str) -> None:
    target.entry = _write(target, author, message)


@given("the guests have already left their entries")
def the_corpus_has_been_left(target: Target) -> None:
    """Seed the book from the committed corpus, in the order it was written.

    Through the API and not behind its back: the black box may only reach the
    application the way anybody else does, and a scenario that seeded the
    database directly would pass while the write path was broken.
    """
    for body in bodies_of(ORDINARY):
        answer = target.api.send("POST", ENTRIES, body=body)
        should_answer(answer, 201, meaning="every corpus entry to be stored")


@given(parsers.parse('the guestbook holds entries signed "{first}", "{second}" and "{third}"'))
def three_entries_exist(target: Target, first: str, second: str, third: str) -> None:
    """Written in the order the sentence reads, so "newest" means the last one.

    Three separate writes rather than a bulk insert: the ordering the next step
    asserts is the application's, and seeding rows behind its back would prove
    the seeding instead.
    """
    for author in (first, second, third):
        _write(target, author, "anything")


# --------------------------------------------------------------------------
# When -- what the scenario does
# --------------------------------------------------------------------------


@when(parsers.parse('a guest leaves an entry signed "{author}" with the message "{message}"'))
def guest_leaves_an_entry(target: Target, author: str, message: str) -> None:
    target.api.send("POST", ENTRIES, body={"author": author, "message": message})


@when("a guest tries to leave an entry with no signature")
def guest_leaves_an_entry_without_a_signature(target: Target) -> None:
    target.api.send("POST", ENTRIES, body={"author": "   ", "message": "anything"})


@when("a guest tries to leave an entry with no message")
def guest_leaves_an_entry_without_a_message(target: Target) -> None:
    target.api.send("POST", ENTRIES, body={"author": "Anna", "message": "   "})


@when(parsers.parse("a guest leaves an entry in which {description}"))
def a_guest_leaves_a_boundary_entry(target: Target, description: str) -> None:
    entry = described(BOUNDARY, description)
    target.entry = entry
    target.api.send("POST", ENTRIES, body=body_of(entry))


@when(parsers.parse("a guest tries to leave an entry in which {description}"))
def a_guest_tries_a_refused_entry(target: Target, description: str) -> None:
    entry = described(REFUSED, description)
    target.entry = entry
    target.api.send("POST", ENTRIES, body=body_of(entry))


@when("the entry with non-ASCII characters is looked up")
def the_entry_with_diacritics_is_read(target: Target) -> None:
    """Find it by what makes it the one this scenario is about, not by position.

    Reaching for `entries[2]` starts asserting about a different entry the moment
    somebody inserts one above it, and does so silently.
    """
    wanted = next(e for e in bodies_of(ORDINARY) if any(ord(c) > 127 for c in e["author"]))
    listing = target.api.get(ENTRIES)
    row = found(
        row_where(listing, author=wanted["author"].strip()),
        subject="the entry written with non-ASCII characters",
        answer=listing,
    )
    target.entry = {**row, "expected_message": wanted["message"].strip()}
    target.api.get(f"{ENTRIES}/{row['id']}")


@when("the guestbook is displayed")
def the_book_is_listed(target: Target) -> None:
    target.api.get(ENTRIES)


@when(parsers.parse('the author amends that entry\'s message to "{message}"'))
def the_author_edits_the_entry(target: Target, message: str) -> None:
    entry = _the_entry(target)
    target.api.send("PATCH", f"{ENTRIES}/{entry['id']}", body={"message": message})


@when("somebody tries to amend an entry that is not there")
def somebody_edits_an_entry_that_is_not_there(target: Target) -> None:
    target.api.send("PATCH", f"{ENTRIES}/{_unknown_id()}", body={"message": "anything"})


@when("the author deletes that entry")
def the_author_deletes_the_entry(target: Target) -> None:
    entry = _the_entry(target)
    target.api.send("DELETE", f"{ENTRIES}/{entry['id']}", body={})


@when("the author deletes that entry again")
def the_author_deletes_the_entry_again(target: Target) -> None:
    """A separate step from the one above, deliberately.

    `When ... And ...` reads as two actions in the `.feature`, and it must be two
    actions here: reusing one step twice would make the scenario's second line
    invisible to anybody reading only the step definitions.
    """
    entry = _the_entry(target)
    target.api.send("DELETE", f"{ENTRIES}/{entry['id']}", body={})


@when(parsers.parse('the author deletes the entry signed "{author}"'))
def the_author_deletes_the_entry_signed(target: Target, author: str) -> None:
    listing = target.api.get(ENTRIES)
    row = found(
        row_where(listing, author=author), subject=f"entry signed {author!r}", answer=listing
    )
    target.api.send("DELETE", f"{ENTRIES}/{row['id']}", body={})


@when(parsers.parse('a guest searches for entries containing "{phrase}"'))
def a_guest_searches_for(target: Target, phrase: str) -> None:
    target.api.get(ENTRIES, q=phrase)


@when("a guest searches for entries nobody wrote")
def a_guest_searches_for_something_nobody_wrote(target: Target) -> None:
    """A phrase no fixture in this suite can accidentally contain.

    Spelled here rather than in the `.feature`, because the sentence a reader
    needs is "something nobody wrote" -- the exact letters are a detail of how
    this suite makes that true.
    """
    target.api.get(ENTRIES, q="no-such-word-in-any-entry")


@when("the guestbook is displayed oldest first")
def the_book_is_listed_oldest_first(target: Target) -> None:
    target.api.get(ENTRIES, sort="oldest")


@when(parsers.parse("a guest views the first {size:d} entries"))
def a_guest_reads_the_first(target: Target, size: int) -> None:
    target.api.get(ENTRIES, limit=size)


@when(parsers.parse("a guest views the guestbook {size:d} entries at a time, to the end"))
def a_guest_reads_the_whole_book_in_pieces(target: Target, size: int) -> None:
    """Walk every piece to the end and remember what each one showed.

    Kept on `target.entry` rather than re-read by the `Then`, because the claim
    is about the WALK: that consecutive pieces tile the book. A `Then` that asked
    for the whole list again would be asserting one more read instead.
    """
    seen: list[str] = []
    offset = 0
    answer = target.api.get(ENTRIES, limit=size, offset=offset)
    while True:
        should_answer(answer, 200, meaning="the guest book to be readable in pieces")
        piece = rows(answer)
        if not piece:
            break
        seen += [str(row.get("id")) for row in piece]
        offset += size
        answer = target.api.get(ENTRIES, limit=size, offset=offset)
    target.entry = {"seen": seen, "total": total_of(answer)}


# --------------------------------------------------------------------------
# Then -- what must be true afterwards
# --------------------------------------------------------------------------


@then("the entry should be saved")
def the_entry_should_be_stored(target: Target) -> None:
    answer = target.api.last
    if answer.status not in (200, 201):
        raise AssertionError(f"expected the entry to be stored, got {answer}")


@then("the entry should be refused")
def the_entry_should_be_refused(target: Target) -> None:
    should_answer(target.api.last, 422, meaning="the entry to be refused as incomplete")


@then("the operation should be refused as being about an entry that does not exist")
def the_operation_should_be_refused_as_unknown(target: Target) -> None:
    should_answer(target.api.last, 404, meaning="the operation to be refused: no such entry")


@then(parsers.parse("the guestbook should hold {expected:d} entry"))
@then(parsers.parse("the guestbook should hold {expected:d} entries"))
def the_book_should_hold(target: Target, expected: int) -> None:
    """Two spellings, one step. English inflects the noun after the number, and a
    scenario written in the wrong form is a scenario a non-programmer would not
    have written.

    Counted from what the book reports holding, not from the length of the piece
    that came back: the sentence is about the guest book, and a page is not the
    book. They agree today at five entries and would stop agreeing at twenty-one.
    """
    answer = target.api.get(ENTRIES)
    should_answer(answer, 200, meaning="the guest book to be readable")
    should_be(total_of(answer), expected, subject="the number of entries in the guest book")


@then("the guestbook should show every entry that was left")
def the_book_should_show_every_seeded_entry(target: Target) -> None:
    listing = target.api.last
    should_answer(listing, 200, meaning="the guest book to be readable")
    should_be(
        len(rows(listing)),
        len(bodies_of(ORDINARY)),
        subject="the number of entries the book came back with",
    )


@then("they should be ordered newest first")
def they_should_be_newest_first(target: Target) -> None:
    """`BR-04`, asserted as the REVERSE of the corpus.

    The corpus lists entries in writing order, so comparing against its reverse
    is asserting the rule; comparing against a list typed out here would be
    asserting a second copy of the data.
    """
    listed = [str(row.get("author")) for row in rows(target.api.last)]
    written = [body["author"].strip() for body in bodies_of(ORDINARY)]

    should_be(listed, list(reversed(written)), subject="the order the book came back in")


@then("its message should come back unchanged")
def its_message_should_come_back_unchanged(target: Target) -> None:
    entry = _the_entry(target)
    answer = target.api.last
    should_answer(answer, 200, meaning="the entry to be readable")
    payload = answer.payload
    assert isinstance(payload, dict), f"expected one entry, got {answer}"

    should_be(payload["message"], entry["expected_message"], subject="the message read back")


@then("the stored message should be exactly what was sent")
def the_stored_value_should_be_exactly_what_was_sent(target: Target) -> None:
    """Stored whole, not truncated.

    A column bound that truncates instead of refusing loses the tail silently,
    and a boundary scenario that only checks the status code would call that a
    pass.
    """
    entry = _the_entry(target)
    created = target.api.last
    should_answer(created, 201, meaning="the entry to be stored")
    payload = created.payload
    assert isinstance(payload, dict), f"expected the stored entry, got {created}"

    should_be(payload["author"], entry["author"].strip(), subject="the stored signature")
    should_be(payload["message"], entry["message"].strip(), subject="the stored message")


@then(parsers.parse('the entry signed "{author}" should be at the top of the list'))
def the_top_of_the_list_should_be(target: Target, author: str) -> None:
    listing = target.api.last
    should_answer(listing, 200, meaning="the guest book to be readable")
    listed = rows(listing)
    if not listed:
        raise AssertionError(f"the guest book came back empty. The application answered {listing}")
    should_be(listed[0].get("author"), author, subject="the signature on the first entry")


@then(parsers.parse('that entry should have the message "{message}"'))
def the_entry_should_read(target: Target, message: str) -> None:
    entry = _reread(target)
    should_be(entry.get("message"), message, subject="the message on the entry")


@then("that entry should be marked as edited")
def the_entry_should_be_marked_edited(target: Target) -> None:
    """Being edited is derived, not stored: the two timestamps stop being equal.

    That is the whole of `BR-02` as a reader can observe it from outside, which
    is why this suite asserts the derivation rather than a flag column.
    """
    entry = _reread(target)
    if entry.get("updated_at") == entry.get("created_at"):
        raise AssertionError("the entry is not marked as edited: its two timestamps still match")


@then("the date that entry was written should not change")
def the_written_date_should_not_move(target: Target) -> None:
    """The half of `BR-02` that only a before-and-after can state.

    `target.entry` is the entry as the `Given` created it -- no single
    response can support this assertion, which is exactly why the field exists.
    """
    before = _the_entry(target)
    after = _reread(target)
    should_be(
        after.get("created_at"), before.get("created_at"), subject="the date the entry was written"
    )


@then(parsers.parse('there should be no entry signed "{author}" in the guestbook'))
def the_book_should_not_hold(target: Target, author: str) -> None:
    listing = target.api.get(ENTRIES)
    should_answer(listing, 200, meaning="the guest book to be readable")
    if row_where(listing, author=author) is not None:
        raise AssertionError(f"the entry signed {author!r} is still in the guest book")


@then(parsers.parse("they should find {expected:d} matching entry"))
@then(parsers.parse("they should find {expected:d} matching entries"))
def the_search_should_match(target: Target, expected: int) -> None:
    """How many entries matched -- the whole population, not the piece shown.

    Read from the count the answer carries rather than from `len(rows(...))`:
    the two agree on a small book and stop agreeing the moment a search matches
    more than fits, which is precisely when the number starts mattering.
    """
    answer = target.api.last
    should_answer(answer, 200, meaning="the search to be answerable")
    should_be(total_of(answer), expected, subject="the number of entries that matched")


@then(parsers.parse("they should see {expected:d} entries"))
def the_guest_should_see(target: Target, expected: int) -> None:
    """How many entries came back in this piece. The other half of the pair
    above: one counts what was shown, the other what exists."""
    answer = target.api.last
    should_answer(answer, 200, meaning="the piece of the book to be readable")
    should_be(len(rows(answer)), expected, subject="the number of entries on this piece")


@then("they should be told how many entries the whole guestbook holds")
def the_piece_should_say_how_big_the_book_is(target: Target) -> None:
    """The one fact a piece cannot imply about itself.

    Without it "show more" has nothing to count down from, and a screen would
    have to guess from the size of what it was handed -- which is a plausible
    number and therefore a wrong one nobody notices.
    """
    answer = target.api.last
    should_be(
        total_of(answer),
        len(bodies_of(ORDINARY)),
        subject="the number of entries the book reports holding",
    )


@then("they should see every entry exactly once")
def every_entry_should_appear_exactly_once(target: Target) -> None:
    """Consecutive pieces tile the book: nothing twice, nothing missed.

    This is what `BR-04`'s tie-break exists for and the only place it can be
    observed from outside. Without a total order, two entries written in the
    same tick straddle a boundary and one of them is shown twice while the other
    disappears -- quietly, and never in a test that reads a single piece.
    """
    walk = _the_entry(target)
    seen = walk["seen"]
    assert isinstance(seen, list), "the walk recorded nothing to assert about"

    should_be(len(set(seen)), len(seen), subject="the number of DISTINCT entries the walk saw")
    should_be(len(seen), walk["total"], subject="the number of entries the walk saw in total")


# --------------------------------------------------------------------------


def _the_entry(target: Target) -> Row:
    """The entry this scenario is about, or a sentence about the missing step."""
    if target.entry is None:
        raise AssertionError(
            "this step is about an entry, but no `Given` created one in this scenario"
        )
    return target.entry


def _reread(target: Target) -> Row:
    """Fetch the entry again, so an assertion is about stored state.

    Reading it off the edit's own response would let a service that answered
    correctly and wrote nothing pass every one of these scenarios -- which is
    the failure a black box exists to catch.
    """
    entry = _the_entry(target)
    answer = target.api.get(f"{ENTRIES}/{entry['id']}")
    should_answer(answer, 200, meaning="the entry to be readable")
    payload: Any = answer.payload
    assert isinstance(payload, dict), f"expected one entry, got {answer}"
    return payload

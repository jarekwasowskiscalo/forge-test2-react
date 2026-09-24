"""The server's half of one rule that two languages keep.

`golden-set/fixtures/text-measurement.json` is the whole subject. This module
drives every case in it through `app.platform.schemas.text` and through the real
Pydantic models; `frontend/src/contexts/guestbook/lib/entryText.test.ts` drives the
same bytes through the browser's copy. Neither file asserts anything the other does
not, which is the point -- two suites reading one corpus is the only shape that can
prove the two sides agree, because agreement is not a property either side has by
itself.

**What this replaces is a test that could not see its own subject.**
`tests/fitness/test_length_constants.py` compares the literal `80` beside the model
with the literal `80` in the browser and passes. It has always passed. It cannot
fail on the defect it was written for, because the browser was measuring UTF-16
code units and the server code points, so both sides read `80` and meant different
strings -- and each side's own suite was green. A number can only be checked against
a number; a UNIT has to be checked against data.

The cases are driven twice on purpose. Once through `normalize`/`length`, which is
the rule itself, and once through `GuestbookEntryCreate`, which is the rule as a
caller meets it -- the second would still pass if the schema stopped using the
first, so it is the wiring that is under test there rather than the arithmetic.

No database and no HTTP: the rule is a pure function of a string, and the only
reason it was ever hard to see is that nobody had written the string down.
"""

import json
import unicodedata
from typing import Any, Final

import pytest
from pydantic import ValidationError

from app.contexts.guestbook.models.guestbook_entry import AUTHOR_MAX_LENGTH, MESSAGE_MAX_LENGTH
from app.contexts.guestbook.schemas.guestbook_entries import (
    QUERY_MAX_LENGTH,
    GuestbookEntryCreate,
)
from app.platform.schemas.text import TRIMMED, length, normalize
from tests._golden_set import TEXT_RULES, cases_of

#: The bound each field is held to, by the name the corpus uses for it.
BOUNDS: Final[dict[str, int]] = {
    "author": AUTHOR_MAX_LENGTH,
    "message": MESSAGE_MAX_LENGTH,
    "q": QUERY_MAX_LENGTH,
}

#: A value that passes on the field a case is not about, so a case about `author`
#: is refused for its author and never for its message.
FILLER: Final[str] = "anything"


def _verdict(case: dict[str, Any]) -> str:
    """What the rule says about one case: the corpus's own claim, recomputed."""
    text = normalize(str(case["input"]))
    if not text:
        return "empty"
    return "too_long" if length(text) > BOUNDS[str(case["field"])] else "accepted"


def _cases(field: str) -> list[dict[str, Any]]:
    return [case for case in cases_of(TEXT_RULES) if case["field"] == field]


def _identify(case: dict[str, Any]) -> str:
    return str(case["case"])


# --------------------------------------------------------------------------- #
# The rule itself
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("case", cases_of(TEXT_RULES), ids=_identify)
@pytest.mark.req("CR-2609-9b1e/R-2")
def test_every_case_gets_the_verdict_the_corpus_states(case: dict[str, Any]) -> None:
    """The corpus is the claim; this is the claim being true of the server."""
    assert _verdict(case) == case["verdict"], (
        f"{case['case']}: the corpus expects {case['verdict']!r} and the rule says "
        f"{_verdict(case)!r}"
    )


@pytest.mark.parametrize("case", cases_of(TEXT_RULES), ids=_identify)
@pytest.mark.req("CR-2609-9b1e/R-2")
def test_every_accepted_case_is_as_long_as_the_corpus_says(case: dict[str, Any]) -> None:
    """The verdict alone would pass with the wrong unit.

    `accepted` is true of a signature of eighty emoji whether they are counted as
    eighty code points or eighty of anything else that happens to fit. The LENGTH
    is what names the unit, and it is the number the browser has to reproduce.
    """
    if case["verdict"] != "accepted":
        pytest.skip("only an accepted case carries a length")

    assert length(normalize(str(case["input"]))) == case["length"]


@pytest.mark.req("CR-2609-9b1e/R-2")
def test_normalizing_makes_the_two_spellings_of_one_word_one_value() -> None:
    """The case the corpus states twice, asserted here as the identity it is.

    Decomposed and precomposed are the same eighty letters to every person who
    will ever type them, and the only thing that decided between acceptance and
    refusal was which one the keyboard happened to emit.
    """
    decomposed = ("e" + chr(0x0301)) * AUTHOR_MAX_LENGTH
    precomposed = chr(0x00E9) * AUTHOR_MAX_LENGTH

    assert normalize(decomposed) == normalize(precomposed)
    assert length(normalize(decomposed)) == AUTHOR_MAX_LENGTH
    assert len(decomposed) == AUTHOR_MAX_LENGTH * 2, "the raw forms differ, which is the point"


@pytest.mark.req("CR-2609-9b1e/R-2")
def test_the_trimmed_set_is_the_union_of_what_the_two_runtimes_removed() -> None:
    """Stated as arithmetic rather than as a list nobody recounts.

    Python's own `str.strip()` set is `White_Space` plus the four C0 separators;
    JavaScript's is `White_Space` plus the BOM. The union is what neither side may
    disagree about, and a code point dropped from it here is a code point that
    becomes content on one side only.
    """
    python_strips = {chr(code) for code in range(0x110000) if chr(code).isspace()}

    assert python_strips < TRIMMED, "the set must remove everything Python already removed"
    assert TRIMMED - python_strips == {chr(0xFEFF)}, "the BOM is the only addition"
    assert len(TRIMMED) == 30


@pytest.mark.req("CR-2609-9b1e/R-2")
def test_whitespace_inside_a_value_is_content() -> None:
    """Only the ends. A message is written in lines and keeping them is `BR-01`."""
    assert normalize("Anna" + chr(0x85) + "B") == "Anna" + chr(0x85) + "B"
    assert normalize("first\nsecond") == "first\nsecond"


# --------------------------------------------------------------------------- #
# The rule as a caller meets it
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("case", _cases("author"), ids=_identify)
@pytest.mark.req("CR-2609-9b1e/R-2")
def test_the_schema_answers_every_author_case_the_way_the_rule_does(case: dict[str, Any]) -> None:
    """The wiring, not the arithmetic: that the schema uses the rule at all."""
    if case["verdict"] == "accepted":
        entry = GuestbookEntryCreate(author=str(case["input"]), message=FILLER)
        assert length(entry.author) == case["length"]
        assert entry.author == normalize(str(case["input"])), "the stored value is the measured one"
    else:
        with pytest.raises(ValidationError):
            GuestbookEntryCreate(author=str(case["input"]), message=FILLER)


@pytest.mark.parametrize("case", _cases("message"), ids=_identify)
@pytest.mark.req("CR-2609-9b1e/R-2")
def test_the_schema_answers_every_message_case_the_way_the_rule_does(case: dict[str, Any]) -> None:
    if case["verdict"] == "accepted":
        entry = GuestbookEntryCreate(author=FILLER, message=str(case["input"]))
        assert length(entry.message) == case["length"]
        assert entry.message == normalize(str(case["input"]))
    else:
        with pytest.raises(ValidationError):
            GuestbookEntryCreate(author=FILLER, message=str(case["input"]))


@pytest.mark.req("CR-2609-9b1e/R-2")
def test_what_the_schema_keeps_is_what_it_measured() -> None:
    """The half a length check cannot see.

    A schema that trimmed for the measurement and stored the raw value would pass
    every length assertion above and still write the padding to the column.
    """
    entry = GuestbookEntryCreate(author="  Anna  ", message=chr(0xFEFF) + "Good morning")

    assert entry.author == "Anna"
    assert entry.message == "Good morning"


# --------------------------------------------------------------------------- #
# The detectors, with proof that they fire
# --------------------------------------------------------------------------- #


@pytest.mark.req("CR-2609-9b1e/R-2")
def test_measuring_in_utf16_units_would_redden_the_corpus() -> None:
    """The browser's old rule, run against the corpus that was written for it.

    This is the assertion the repair exists for: a suite that cannot show the old
    behaviour failing has not shown that it tests the new one. UTF-16 is what
    `String.prototype.length` counts, and it is reproduced here rather than
    described so the corpus is proved capable of seeing the difference.
    """
    disagreed = [
        case["case"]
        for case in cases_of(TEXT_RULES)
        if case["verdict"] == "accepted"
        and len(normalize(str(case["input"])).encode("utf-16-le")) // 2 != case["length"]
    ]

    assert disagreed, (
        "no case in the corpus distinguishes a code point from a UTF-16 code unit, "
        "so the corpus cannot see the defect it was written for"
    )


@pytest.mark.req("CR-2609-9b1e/R-2")
def test_trimming_with_the_runtime_default_would_redden_the_corpus() -> None:
    """The server's old rule: `str.strip()`, which leaves the BOM behind.

    Compared on the verdict **and** the length, not on emptiness alone. A value
    wrapped in byte order marks is non-empty under either rule and differs only by
    two code points, so an emptiness check would call the two rules equal on
    exactly the case that shows a bound being crossed.
    """

    def under_the_old_rule(case: dict[str, Any]) -> tuple[str, int]:
        text = unicodedata.normalize("NFC", str(case["input"])).strip()
        bound = BOUNDS[str(case["field"])]
        verdict = "empty" if not text else ("too_long" if len(text) > bound else "accepted")
        return verdict, len(text)

    disagreed = [
        case["case"]
        for case in cases_of(TEXT_RULES)
        if under_the_old_rule(case) != (str(case["verdict"]), length(normalize(str(case["input"]))))
    ]

    assert disagreed == [
        "only_the_byte_order_mark",
        "only_every_trimmed_code_point",
        "byte_order_mark_wraps_the_maximum",
    ], (
        "the corpus must distinguish the union from Python's own whitespace set, and "
        f"name exactly the cases that do: {disagreed}"
    )


@pytest.mark.req("CR-2609-9b1e/R-2")
def test_skipping_normalization_would_redden_the_corpus() -> None:
    """The third leg: NFC is load-bearing and not decoration."""
    raw = ("e" + chr(0x0301)) * AUTHOR_MAX_LENGTH

    assert length(raw.strip()) > AUTHOR_MAX_LENGTH, "without NFC this value is refused"
    assert length(normalize(raw)) == AUTHOR_MAX_LENGTH, "with it, it is accepted"


# --------------------------------------------------------------------------- #
# The corpus reaches both sides
# --------------------------------------------------------------------------- #


@pytest.mark.req("CR-2609-9b1e/R-6")
def test_the_corpus_covers_every_bounded_field() -> None:
    """Scale. A corpus that forgot the search phrase would leave the one field
    whose bound was applied in the wrong order proved by nothing."""
    covered = {str(case["field"]) for case in cases_of(TEXT_RULES)}

    assert covered == set(BOUNDS), f"the corpus covers {sorted(covered)}"


@pytest.mark.req("CR-2609-9b1e/R-2")
def test_the_corpus_is_written_in_escapes_rather_than_bytes() -> None:
    """Every input is ASCII on disk.

    A corpus carrying raw non-ASCII bytes would make `.gitattributes`, a checkout
    on another platform and an editor's re-encoding part of the data -- and the
    first of those already rewrites line endings in this repository. Escapes are
    the only spelling no tool in the chain touches.
    """
    raw = TEXT_RULES.read_bytes()

    assert all(byte < 0x80 for byte in raw), "the corpus carries a byte above U+007F"
    assert json.loads(raw.decode("ascii"))["cases"], "and it still parses"

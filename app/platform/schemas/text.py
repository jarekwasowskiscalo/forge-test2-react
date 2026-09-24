"""How this API trims a text field and how long it considers it to be.

Not named after a resource, like `refusals.py` beside it, and for the same reason:
the unit a bound is counted in is a fact about EVERY text field this API accepts,
not about guest book entries. The *bounds* stay where their domain is
(`AUTHOR_MAX_LENGTH` beside the model); what lives here is what the number counts.

**The unit is code points, after NFC normalization. Not graphemes, and not UTF-16
code units.** The choice is forced rather than preferred, and the argument is worth
keeping because the alternative looks more humane:

- `author` is `varchar(80)` and PostgreSQL counts **code points** in it. Eighty
  graphemes of family emoji is up to four hundred code points, so a grapheme rule
  would have the column refuse a value the application had just accepted.
- `maxLength: 80` in `contracts/openapi/guestbook.yaml` is, by the JSON Schema
  specification, in code points. A grapheme rule would make the published contract
  false for every independent client built against it.
- Python has no grapheme segmentation in its standard library; JavaScript has
  `Intl.Segmenter`. Two implementations would have to declare the same version of
  UAX #29 or the disagreement returns one floor up.

So three of the four layers already count code points, and the repair is to bring
the fourth -- the browser -- to the rule, rather than to move the other three.

**Trimming is a written set rather than a default.** `str.strip()` removes 29 code
points; JavaScript's `String.prototype.trim` removes 25. Five are stripped only by
Python (the C0 separators and NEL) and one only by JavaScript (the BOM), so before
this module six code points were content in one language and whitespace in the
other -- in both directions, which is why no amount of care on one side could have
found it. The set below is the **union**, listed literally: both runtimes now
perform the same written operation instead of their own.

`golden-set/fixtures/text-measurement.json` is where the rule is proved, and it is
read by this suite and by the browser's own, against the same bytes.
"""

import unicodedata
from typing import Final

from pydantic import BeforeValidator

#: Unicode's `White_Space` property -- the 25 code points both runtimes already
#: agreed about.
WHITE_SPACE: Final[tuple[int, ...]] = (
    0x0009,
    0x000A,
    0x000B,
    0x000C,
    0x000D,
    0x0020,
    0x0085,
    0x00A0,
    0x1680,
    0x2000,
    0x2001,
    0x2002,
    0x2003,
    0x2004,
    0x2005,
    0x2006,
    0x2007,
    0x2008,
    0x2009,
    0x200A,
    0x2028,
    0x2029,
    0x202F,
    0x205F,
    0x3000,
)

#: The C0 separators. `str.isspace()` is true of all four, so `str.strip()` has
#: always removed them; `String.prototype.trim` never has. Kept in the set rather
#: than dropped from it, because a file separator arriving inside a signature is a
#: paste accident either way and neither side should store it as content.
C0_SEPARATORS: Final[tuple[int, ...]] = (0x001C, 0x001D, 0x001E, 0x001F)

#: The byte order mark, which JavaScript trims and Python does not. It is in the
#: set for the plainest of reasons: it arrives by itself, at the front of text
#: pasted out of an ordinary editor, and a guest who pasted it did not type it.
BYTE_ORDER_MARK: Final[tuple[int, ...]] = (0xFEFF,)

#: The 30 code points removed from either end of a value, and the only ones.
#: `U+200B` ZERO WIDTH SPACE and `U+180E` MONGOLIAN VOWEL SEPARATOR are deliberately
#: absent -- neither runtime treats them as whitespace, so they are content, and the
#: corpus says so in a case of its own rather than leaving it to be discovered.
TRIMMED: Final[frozenset[str]] = frozenset(
    chr(code) for code in WHITE_SPACE + C0_SEPARATORS + BYTE_ORDER_MARK
)

#: `str.strip` takes a string of characters rather than a set. Built once here so
#: the set above stays the single declaration and this is only its other spelling.
_TRIMMED_CHARACTERS: Final[str] = "".join(sorted(TRIMMED))


def normalize(value: str) -> str:
    """The value as it will be measured, sent and stored.

    NFC first, then the edges. The order matters and only in one direction:
    normalizing afterwards could compose a combining mark with a letter the trim
    had just exposed, so a value would measure differently depending on what was
    trimmed off it.

    Normalization is what makes the bound honest to a person. Without it the same
    eighty letters are accepted or refused depending on nothing but whether the
    keyboard emitted `e` + U+0301 or the single `U+00E9` -- a distinction no guest
    can see and no guest chose.

    Only the ends are trimmed. Whitespace inside a value is content: a message is
    written in lines and keeping them is the point (`BR-01`).
    """
    return unicodedata.normalize("NFC", value).strip(_TRIMMED_CHARACTERS)


def length(value: str) -> int:
    """How long `value` is, in the unit the bounds are written in.

    `len()` over a `str` is already code points in Python, so this function adds no
    arithmetic -- it adds a NAME. The browser's counterpart cannot be `.length`,
    which is UTF-16 code units, and a rule that is implicit on one side is a rule
    the other side can quietly stop keeping. Calling the same named function on
    both sides is what makes the agreement reviewable.

    Measures the value as given: a caller that means the trimmed length normalizes
    first, which is what `NormalizedText` does before Pydantic counts.
    """
    return len(value)


def _normalized(value: object) -> object:
    """`normalize` for Pydantic, which may hand this anything at all.

    A non-string passes straight through so that Pydantic's own type error is what
    the caller reads -- a `TypeError` from inside a validator would replace a
    sentence about the field with a stack trace about this module. `None` reaches
    here on every optional field (`GuestbookEntryUpdate`, the search phrase), and
    passing it on is what lets those stay `str | None` without a second validator.
    """
    return normalize(value) if isinstance(value, str) else value


#: Put in a field's `Annotated[...]` **before** its bound, which is the whole point:
#: `BeforeValidator` runs ahead of the length constraint, so what Pydantic measures
#: is the normalized, trimmed value. A signature of nothing but spaces is then empty
#: rather than three characters long, and a phrase of two hundred and five spaces is
#: no phrase rather than a refusal.
NormalizedText: Final = BeforeValidator(_normalized)

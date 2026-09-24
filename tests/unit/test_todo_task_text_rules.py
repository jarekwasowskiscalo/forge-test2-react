"""The server's half of the rule a task's text is judged by (`BR-06`, `BR-07`).

`golden-set/fixtures/todo-task-text.json` is the subject. This module drives every
case in it through the service's judgement of a text;
`frontend/src/contexts/todo_list/lib/todoTask.test.ts` drives the same bytes through
the browser's copy of the rule. Neither asserts anything the other does not: two
suites reading one corpus is the only shape that can prove the screen accepts
exactly the texts the service accepts (`CR-2609-823a/R-2` clause 5), because
agreement is not a property either side has by itself -- the defect `D-04` records,
one context over.

**What this module fixes for the implementation.** The judgement is a function of a
string alone, in `app.contexts.todo_list.services.todo_tasks`:

- `judge_todo_task_text(text) -> str` returns the text as it will be stored --
  normalized and trimmed by the shared kernel (`app/platform/schemas/text.py`) -- or
  raises exactly one of the three domain exceptions
  `tests/integration/test_todo_tasks_service.py` already imports:
  `TodoTaskTextEmptyError`, `TodoTaskTextMultilineError`, `TodoTaskTextTooLongError`.
  The order is the one `spec/design/architecture.md` § The layer per rule gives:
  normalize, then empty, then one line, then measure. The add and the correction
  call it; that one judgement serves both is what makes "a correction is held to
  `BR-06` and `BR-07` exactly as an addition is" true by construction.
- `TODO_TASK_TEXT_MAX_LENGTH` and `LINE_BREAKS` beside `TodoTask`, in
  `app.contexts.todo_list.models.todo_task` -- `LINE_BREAKS` written as code-point
  numbers, the way `WHITE_SPACE` is written in the kernel.

**Red first.** None of that exists yet, so every name above is imported inside the
test that needs it, never at the top of the module: a failed top-level import would
un-collect every case in the file, and a declared failure the runner does not collect
fails the gate (`spec/design/testing.md` § CR-2609-823a, "Red first").

**The bound is read from `TODO_TASK_TEXT_MAX_LENGTH`, never from `QUERY_MAX_LENGTH`.**
The guestbook's search phrase is also bounded at 200, and a test that reads the
phrase's constant to prove the task's bound proves the wrong rule -- it would stay
green the day one of the two moved.

**The seven line breaks are written down here as the requirement states them**
(`CR-2609-823a/R-2` clause 6, confirmed as `A-1`), and the model's `LINE_BREAKS` is
held to that list rather than the list being read from the model: a test that took
its expectation from the code under test would pass whatever the code said.

No database and no HTTP: the rule is a pure function of a string. What reached the
column is `tests/integration/`'s question, and what the refusal is called on the wire
is `tests/integration/test_todo_tasks_corpus.py`'s.
"""

import unicodedata
from collections.abc import Callable
from typing import Any, Final

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from app.platform.schemas.text import TRIMMED, length, normalize
from tests._golden_set import TODO_TASK_TEXT, cases_of

#: The line breaks, as `CR-2609-823a/R-2` clause 6 writes them and `spec/contexts/todo_list.md`
#: § Language repeats them: line feed, line tabulation, form feed, carriage return,
#: next line, line separator, paragraph separator. One written set that both sides
#: read -- never either language's own idea of a line break, because the two disagree
#: about U+000B, U+000C and U+0085 among others.
_WRITTEN_LINE_BREAKS: Final[tuple[int, ...]] = (
    0x000A,
    0x000B,
    0x000C,
    0x000D,
    0x0085,
    0x2028,
    0x2029,
)

_LINE_BREAK_CHARACTERS: Final[frozenset[str]] = frozenset(chr(c) for c in _WRITTEN_LINE_BREAKS)

#: The verdicts the corpus uses, one per way the judgement can end.
_REFUSED_AS: Final[dict[str, str]] = {
    "TodoTaskTextEmptyError": "empty",
    "TodoTaskTextMultilineError": "multiline",
    "TodoTaskTextTooLongError": "too_long",
}

#: The accepted cases alone: only they carry a length, and the corpus states one
#: exactly for them (`tests/fitness/test_golden_set.py` holds the file to that).
_ACCEPTED: Final[list[dict[str, Any]]] = [
    case for case in cases_of(TODO_TASK_TEXT) if case["verdict"] == "accepted"
]

#: Hypothesis' deadline measures one example, and the first pays for importing the
#: service and for building the long texts the strategy below draws near the bound.
#: That is a fixed cost, not a property of the rule, so the deadline is off -- as in
#: `tests/unit/test_data_invariant_properties.py` -- and the count stays far under
#: the 120-second per-test ceiling.
_SETTINGS = settings(
    max_examples=200,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


def _identify(case: dict[str, Any]) -> str:
    return str(case["case"])


def _judgement() -> tuple[Callable[[str], str], tuple[type[Exception], ...]]:
    """The service's judgement of a text and its three refusals, reached from inside a test.

    Imported together, so a service missing any one of the four names fails every
    test that judges a text, the same way and at the same line.
    """
    from app.contexts.todo_list.services.todo_tasks import (
        TodoTaskTextEmptyError,
        TodoTaskTextMultilineError,
        TodoTaskTextTooLongError,
        judge_todo_task_text,
    )

    return judge_todo_task_text, (
        TodoTaskTextEmptyError,
        TodoTaskTextMultilineError,
        TodoTaskTextTooLongError,
    )


def _judged(text: str) -> tuple[str, str | None]:
    """What the service says about `text`: a verdict, and the text it keeps if it keeps one.

    A refusal is read by the exception's own class, never by an `isinstance` over a
    shared base: the three reasons are three codes on the wire, and a judgement that
    raised a common parent would name none of them.
    """
    judge, refusals = _judgement()
    try:
        kept = judge(text)
    except refusals as refusal:
        return _REFUSED_AS[type(refusal).__name__], None
    return "accepted", kept


def _the_rule_as_written(text: str, bound: int) -> str:
    """`BR-06` and `BR-07` exactly as `spec/contexts/todo_list.md` states them, in their order.

    Normalized and trimmed by the shared kernel first; then empty; then a line break
    left inside, from the written set; then longer than the bound in code points. It
    reads the requirement's seven rather than the model's `LINE_BREAKS`, so the
    generator below cannot agree with a judgement for the reason that both read one
    wrong list.
    """
    trimmed = normalize(text)
    if not trimmed:
        return "empty"
    if _LINE_BREAK_CHARACTERS & set(trimmed):
        return "multiline"
    return "too_long" if length(trimmed) > bound else "accepted"


# --------------------------------------------------------------------------- #
# The corpus both languages read
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("case", cases_of(TODO_TASK_TEXT), ids=_identify)
@pytest.mark.req("CR-2609-823a/R-2")
def test_every_case_gets_the_verdict_the_corpus_states(case: dict[str, Any]) -> None:
    """The corpus is the claim; this is the claim being true of the service.

    The same verdicts the browser's rule is held to, against the same bytes. A case
    on which the two sides differ is a text the screen lets through and the service
    refuses, or a text the screen stops that the service would have stored.
    """
    verdict, _ = _judged(str(case["input"]))

    assert verdict == case["verdict"], (
        f"{case['case']}: the corpus says {case['verdict']!r} and the service's judgement "
        f"says {verdict!r}"
    )


@pytest.mark.parametrize("case", _ACCEPTED, ids=_identify)
@pytest.mark.req("CR-2609-823a/R-2")
def test_every_accepted_case_has_the_length_the_corpus_states(case: dict[str, Any]) -> None:
    """The verdict alone would pass with the wrong unit.

    `accepted` is true of a hundred and one emoji however they are counted, as long as
    the count fits. The LENGTH of the text the judgement keeps is what names the unit
    -- code points, after normalizing and trimming -- and it is the number the browser
    has to reproduce.
    """
    verdict, kept = _judged(str(case["input"]))

    assert kept is not None, (
        f"{case['case']} is refused as {verdict!r}; the corpus says it is accepted"
    )
    assert length(kept) == case["length"], (
        f"{case['case']}: the corpus says the kept text is {case['length']} code points "
        f"long and the judgement kept {length(kept)}"
    )


@pytest.mark.req("CR-2609-823a/R-2")
def test_the_create_and_update_shapes_carry_no_bound() -> None:
    """Only the rule can refuse a text, so every case builds a valid shape.

    A bound or a validator in a request shape answers before the route runs, with
    FastAPI's list of `{loc, msg, type}` and no code -- and it would call "too long" a
    text whose trouble is a line break (`spec/design/api.md` § Shapes, `TodoTaskCreate`).
    So the published schema carries `text` as a string with no `minLength`,
    `maxLength` or `pattern`; every case of the corpus, the refused ones included,
    builds both shapes; and a shape keeps the text as it was sent, because holding no
    part of the rule means importing none of it -- the service normalizes, the shapes
    do not (`spec/design/conventions.md` § Layers).

    Which code each verdict earns on the wire is proved by
    `tests/integration/test_todo_tasks_corpus.py`, not here.
    """
    from app.contexts.todo_list.schemas.todo_tasks import TodoTaskCreate, TodoTaskUpdate

    def constraints(schema: object) -> list[str]:
        """Every length or pattern constraint anywhere under one property's schema."""
        if isinstance(schema, dict):
            found = [key for key in schema if key in {"minLength", "maxLength", "pattern"}]
            return found + [key for value in schema.values() for key in constraints(value)]
        if isinstance(schema, list):
            return [key for value in schema for key in constraints(value)]
        return []

    published = {
        shape.__name__: constraints(shape.model_json_schema()["properties"]["text"])
        for shape in (TodoTaskCreate, TodoTaskUpdate)
    }
    assert published == {"TodoTaskCreate": [], "TodoTaskUpdate": []}, (
        f"a request shape publishes a bound on `text`: {published}"
    )

    refused_by_a_shape: list[str] = []
    rewritten_by_a_shape: list[str] = []
    for case in cases_of(TODO_TASK_TEXT):
        sent = str(case["input"])
        for shape in (TodoTaskCreate, TodoTaskUpdate):
            try:
                built = shape(text=sent)
            except ValidationError:
                refused_by_a_shape.append(f"{shape.__name__}: {case['case']}")
                continue
            if built.text != sent:
                rewritten_by_a_shape.append(f"{shape.__name__}: {case['case']}")

    assert refused_by_a_shape == [], (
        f"a request shape refuses, with no code, a text only the rule may refuse: "
        f"{refused_by_a_shape}"
    )
    assert rewritten_by_a_shape == [], (
        f"a request shape changes the text it was sent -- it holds part of the rule: "
        f"{rewritten_by_a_shape}"
    )


# --------------------------------------------------------------------------- #
# The rule's edges, built from the constants
# --------------------------------------------------------------------------- #


@pytest.mark.req("CR-2609-823a/R-2")
def test_a_text_too_long_and_on_two_lines_is_refused_as_multiline() -> None:
    """`BR-07` before `BR-06`: the reason given is the one a person cannot see.

    A pasted U+2028 is often invisible in a one-line field while a text's length is
    there to be seen, so a text that breaks both rules is refused as more than one
    line -- on the screen and by the service alike. Built from the constant, with
    every one of the seven: without its break the text is one past the bound, which
    this asserts first, or the case would prove no precedence at all.
    """
    from app.contexts.todo_list.models.todo_task import TODO_TASK_TEXT_MAX_LENGTH

    before = "a" * (TODO_TASK_TEXT_MAX_LENGTH // 2)
    after = "a" * (TODO_TASK_TEXT_MAX_LENGTH + 1 - len(before))

    assert _judged(before + after)[0] == "too_long", (
        "without its line break the text must be one past the bound, or this proves nothing"
    )

    verdicts = {
        f"U+{code:04X}": _judged(before + chr(code) + after)[0] for code in _WRITTEN_LINE_BREAKS
    }
    wrong = {code: verdict for code, verdict in verdicts.items() if verdict != "multiline"}

    assert wrong == {}, f"a text both too long and on two lines was refused for its length: {wrong}"


@pytest.mark.req("CR-2609-823a/R-2")
def test_the_bound_stands_where_the_constant_says() -> None:
    """Both sides of the bound, both built from `TODO_TASK_TEXT_MAX_LENGTH`.

    A bound proved only where it fails passes identically whether the limit is 200 or
    2000 (`spec/design/testing.md` § Choosing what proves what). Three spellings,
    because the unit is the claim: ASCII letters, emoji beyond the Basic Multilingual
    Plane (two UTF-16 units each), and letters written as `e` + U+0301, which are two
    code points each until NFC makes them one.
    """
    from app.contexts.todo_list.models.todo_task import TODO_TASK_TEXT_MAX_LENGTH

    spellings = {"ascii": "a", "emoji": chr(0x1F600), "decomposed": "e" + chr(0x0301)}
    wrong: list[str] = []
    for name, unit in spellings.items():
        verdict, kept = _judged(unit * TODO_TASK_TEXT_MAX_LENGTH)
        if kept is None or length(kept) != TODO_TASK_TEXT_MAX_LENGTH:
            wrong.append(f"{name} at the bound: {verdict}, kept {kept and length(kept)}")
        over, _ = _judged(unit * (TODO_TASK_TEXT_MAX_LENGTH + 1))
        if over != "too_long":
            wrong.append(f"{name} one past the bound: {over}")

    assert wrong == [], f"the bound does not stand at TODO_TASK_TEXT_MAX_LENGTH: {wrong}"


@pytest.mark.req("CR-2609-823a/R-2")
def test_the_line_breaks_are_the_seven_written_code_points_and_all_are_trimmed() -> None:
    """`LINE_BREAKS` is the requirement's list, and every one of them trims like a space.

    Every line break is also in the kernel's trim set, so one at either end is removed
    before the rule looks, and only a line break left inside the text is refused
    (`BR-07`). Held both as sets and through the judgement: the first names the
    constant that drifted, the second proves the judgement trims before it looks.
    """
    from app.contexts.todo_list.models.todo_task import LINE_BREAKS

    assert sorted(LINE_BREAKS) == sorted(_WRITTEN_LINE_BREAKS), (
        f"LINE_BREAKS is {LINE_BREAKS!r}; the requirement writes the seven code points "
        f"{[f'U+{code:04X}' for code in _WRITTEN_LINE_BREAKS]}, as numbers, the way the "
        "kernel writes its trim set"
    )
    assert {chr(code) for code in LINE_BREAKS} <= TRIMMED, (
        "a line break outside the trim set would be refused at the end of a text"
    )

    at_the_ends = {
        f"U+{code:04X}": _judged(chr(code) + "Buy bread" + chr(code))
        for code in _WRITTEN_LINE_BREAKS
    }
    wrong = {
        code: judged for code, judged in at_the_ends.items() if judged != ("accepted", "Buy bread")
    }

    assert wrong == {}, f"a line break at the ends of a text was not trimmed away: {wrong}"


# --------------------------------------------------------------------------- #
# Any text, not only the ones somebody listed
# --------------------------------------------------------------------------- #

#: The kernel's thirty trimmed code points, the seven line breaks among them.
_WHITESPACE: Final[list[str]] = sorted(TRIMMED)

#: Marks NFC composes with the letter before them, so a text measures shorter after
#: normalizing than as typed -- the `BR-06` order made visible.
_COMBINING_MARKS: Final[tuple[str, ...]] = (chr(0x0301), chr(0x0308), chr(0x0327), chr(0x030A))

#: One character, weighted toward what the rule is about: anything at all, the trim
#: set, the seven line breaks drawn again so they turn up inside texts often,
#: combining marks, and characters beyond the Basic Multilingual Plane.
_ANY_CHARACTER = st.one_of(
    st.characters(),
    st.sampled_from(_WHITESPACE),
    st.sampled_from(sorted(_LINE_BREAK_CHARACTERS)),
    st.sampled_from(_COMBINING_MARKS),
    st.characters(min_codepoint=0x10000, max_codepoint=0x10FFFF),
)

#: What a long text near the bound is made of: letters in three spellings, a mark that
#: composes with some of them, and an emoji.
_LETTERS = st.sampled_from(("a", "e", chr(0x00E9), chr(0x0301), chr(0x1F600)))


@st.composite
def _text_near(draw: st.DrawFn, bound: int) -> str:
    """A text whose body is within two code points of the bound, padded and interrupted.

    Padding from the trim set on either side, and up to two characters of anything
    dropped somewhere into the body -- a line break, a mark, a space, a letter -- so the
    four verdicts all turn up on both sides of the bound.
    """
    left = draw(st.text(st.sampled_from(_WHITESPACE), max_size=3))
    body = draw(st.text(_LETTERS, min_size=bound - 2, max_size=bound + 2))
    intruder = draw(st.text(_ANY_CHARACTER, max_size=2))
    at = draw(st.integers(min_value=0, max_value=len(body)))
    right = draw(st.text(st.sampled_from(_WHITESPACE), max_size=3))
    return left + body[:at] + intruder + body[at:] + right


@pytest.mark.req("CR-2609-823a/R-2")
@given(data=st.data())
@_SETTINGS
def test_any_text_is_either_refused_or_kept_normalized_one_line_and_within_the_bound(
    data: st.DataObject,
) -> None:
    """`BR-06` and `BR-07` are rules about a VALUE, so a generator earns its place.

    For any text drawn: the judgement gives the verdict the rule as written gives --
    so it never refuses a text the rule accepts, which "refused or kept" alone would
    allow -- and a text it keeps is the text it measured, NFC, trimmed at both ends,
    free of every line break and 1 to `TODO_TASK_TEXT_MAX_LENGTH` code points long.
    That last clause is the task's own data invariant, the counterpart of `D-04`,
    and this is one of its three witnesses (`spec/design/testing.md` § CR-2609-823a,
    "The witness for a task's text").

    The bound is read inside the test, so the draws near it move when it moves.
    """
    from app.contexts.todo_list.models.todo_task import TODO_TASK_TEXT_MAX_LENGTH

    text = data.draw(
        st.one_of(st.text(_ANY_CHARACTER, max_size=24), _text_near(TODO_TASK_TEXT_MAX_LENGTH)),
        label="text",
    )
    verdict, kept = _judged(text)

    assert verdict == _the_rule_as_written(text, TODO_TASK_TEXT_MAX_LENGTH), (
        f"the judgement says {verdict!r} and the rule as written says "
        f"{_the_rule_as_written(text, TODO_TASK_TEXT_MAX_LENGTH)!r}"
    )
    if kept is None:
        return
    assert kept == normalize(text), "what is kept is not what was measured"
    assert unicodedata.is_normalized("NFC", kept), "a kept text is not NFC"
    assert normalize(kept) == kept, "a kept text still carries trimmed whitespace at an end"
    assert not _LINE_BREAK_CHARACTERS & set(kept), "a kept text carries a line break"
    assert 1 <= length(kept) <= TODO_TASK_TEXT_MAX_LENGTH, "a kept text is outside the bound"

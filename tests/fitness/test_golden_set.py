"""The corpus obeys its own rules, checked rather than described.

`golden-set/README.md` states them and nothing held them. A corpus is committed
data read by two suites and by the environment seeder, so every way it can
quietly stop being what it claims is a way its readers quietly stop proving --
or showing -- what they claim:

- a file nobody can reach through the locator demonstrates nothing to anybody;
- an "ordinary" entry that the rules actually refuse turns a helper that fills a
  book into a refusal test nobody wrote;
- a "boundary" entry one character off the limit passes identically whether the
  limit is right or an order of magnitude out;
- a plausible-looking surname or account number in a committed file is exactly
  the personal data article XI keeps out of this repository;
- **a suite that asserts about the seed half has undone the split** -- the two
  halves are then one corpus again, wearing two directory names.

**The rules are cut three ways, and the cut is the point.** What both halves owe
(the envelope, the naming, the encoding, article XI, the rules really passing)
is checked over `ALL_FILES`. What only the fixture half owes (named cases,
sentences a scenario can use, bounds computed from the model's constants) is
checked over `FIXTURE_FILES`. What only the seed half owes (nothing near a
limit, and no reader but the seeder) is checked over `SEED_FILES`. A rule
applied to the wrong half is how the halves grow back together.

The boundary file is checked **against the constants the model publishes**, not
against literals repeated here. A test that writes `80` is a test that keeps
proving the old number after the rule moves.

**Three shapes of item, and a rule reaches only the shape it is about.** A guest
book file lists `entries` (a signature and a message); `text-measurement.json` and
`todo-task-text.json` list `cases` of a rule (an input and the verdict expected of
it); the to-do list's files list `tasks` (a text, and in a sequence the done mark it
ends with, `CR-2609-823a`). A rule written for one shape and swept over another
either fails on a key the file never had, or -- worse -- passes over it in silence.
So the rules that index `author` and `message` sweep the guest book's files alone,
the rule demanding a line break in every sequence is the guest book's alone (a task
is one line, `BR-07`), and the to-do list's files get rules of their own below.

**The to-do list's constants are imported inside the cases that read them.**
`TODO_TASK_TEXT_MAX_LENGTH` and `LINE_BREAKS` live beside `TodoTask`
(`spec/design/data-model.md` § `todo_tasks`), which the implementation wave writes
after these rules; an import at the top of this module would un-collect every rule
in it until then, the guest book's included (`spec/design/testing.md`
§ CR-2609-823a, "Red first"). The rules that read only the to-do list's fixture
files import nothing from it, which is why they hold from the first run.

Reads the source and the data, and imports the application only for the constants
it compares against; opens no database.
"""

import json
import pathlib
import re
from typing import Any, Final

from app.contexts.guestbook.models.guestbook_entry import AUTHOR_MAX_LENGTH, MESSAGE_MAX_LENGTH
from app.contexts.guestbook.schemas.guestbook_entries import QUERY_MAX_LENGTH
from app.platform.schemas.text import length, normalize
from tests import _golden_set
from tests._golden_set import (
    ALL_FILES,
    BOUNDARY,
    FIXTURE_FILES,
    FIXTURES,
    GOLDEN_SET,
    ORDINARY,
    REFUSED,
    SEED,
    SEED_FILES,
    TEXT_RULES,
    TODO_TASK_TEXT,
    TODO_TASKS_BOUNDARY,
    TODO_TASKS_EXAMPLE,
    TODO_TASKS_ORDINARY,
    TODO_TASKS_REFUSED,
    WELCOME,
    cases_of,
    entries_of,
    tasks_of,
)

#: The keys every entry carries, whatever file it is in.
_REQUIRED_KEYS: Final[frozenset[str]] = frozenset({"author", "message"})

#: Files with named cases must name every one of them; the ordinary and welcome
#: files must not, because their entries are a sequence rather than a set of
#: situations.
_CASE_FILES: Final[tuple[pathlib.Path, ...]] = (BOUNDARY, REFUSED)

#: The guest book's files whose entries are a sequence somebody wrote, in order --
#: one per half. Neither may carry a `case` key. Named file by file rather than as
#: `SEED_FILES`: the seed half now holds the to-do list's example tasks as well, and
#: a rule about signatures swept over a file of tasks fails on a key it never had.
_SEQUENCE_FILES: Final[tuple[pathlib.Path, ...]] = (ORDINARY, WELCOME)

#: Every file whose items are guest book ENTRIES. `text-measurement.json` holds cases
#: of the trimming and length rule -- an input, the field it is about, the verdict
#: expected of it -- and the to-do list's files hold tasks or cases of a task's text,
#: so the rules about `author` and `message` reach none of them and the rules below
#: give each its own.
_ENTRY_FILES: Final[tuple[pathlib.Path, ...]] = _CASE_FILES + _SEQUENCE_FILES

#: The to-do list's files whose tasks are a sequence -- ordinary tasks in adding
#: order, and the example tasks a new environment opens with, one per half. Each task
#: is a `text` and the `done` mark it ends with, and nothing else.
_TASK_SEQUENCE_FILES: Final[tuple[pathlib.Path, ...]] = (TODO_TASKS_ORDINARY, TODO_TASKS_EXAMPLE)

#: The keys a task in a sequence carries -- exactly these, so a sequence can carry
#: neither a `case` nor a `description` for a test to reach for by name.
_TASK_SEQUENCE_KEYS: Final[frozenset[str]] = frozenset({"text", "done"})

#: The to-do list's files of named tasks, and exactly the keys each of their tasks
#: carries (`spec/design/testing.md` § CR-2609-823a, "The fixture half this change
#: adds"): the boundary file states the text each task is `stored` as, the refused
#: file the `refusal` code the contract gives it.
_TASK_CASE_KEYS: Final[dict[pathlib.Path, frozenset[str]]] = {
    TODO_TASKS_BOUNDARY: frozenset({"case", "description", "text", "stored"}),
    TODO_TASKS_REFUSED: frozenset({"case", "description", "text", "refusal"}),
}

#: Every file whose items are TASKS, in either half -- the fixture half first, so a sweep
#: that meets a missing seed file has already held every fixture file to its rule.
_TASK_FILES: Final[tuple[pathlib.Path, ...]] = (
    TODO_TASKS_ORDINARY,
    *_TASK_CASE_KEYS,
    TODO_TASKS_EXAMPLE,
)

#: The codes a refused task may name: the three the contract gives a task's text
#: (`spec/design/api.md` § The to-do list's refusals). A closed set, for the reason
#: `_REFUSAL_MECHANISMS` is one. Unlike the guest book's refused file, these are
#: stable codes rather than mechanisms, because a task's text is refused by the
#: service with a code of its own and never by the schema.
_TASK_TEXT_REFUSALS: Final[frozenset[str]] = frozenset(
    {"todo_task_text_empty", "todo_task_text_too_long", "todo_task_text_multiline"}
)

#: What a case in `todo-task-text.json` may say the rule does with its input: the
#: three verdicts of `text-measurement.json` and a fourth, `multiline` (`BR-07`).
_TASK_TEXT_VERDICTS: Final[frozenset[str]] = frozenset(
    {"accepted", "empty", "too_long", "multiline"}
)

#: The keys a case of a task's text carries. No `field`, because there is one field;
#: `length` is conditional -- present exactly when the verdict is `accepted` -- so it
#: is checked separately rather than listed here.
_TASK_TEXT_CASE_KEYS: Final[frozenset[str]] = frozenset({"case", "description", "input", "verdict"})

#: The seven line breaks as the requirement writes them (`CR-2609-823a/R-2` clause 6,
#: confirmed as `A-1`; `spec/contexts/todo_list.md` § Language). The rules that read
#: only the to-do list's fixture files hold the corpus to THIS list rather than to
#: `LINE_BREAKS` beside the model, so they need nothing the implementation writes;
#: `tests/unit/test_todo_task_text_rules.py` holds the model's constant to it.
_WRITTEN_LINE_BREAKS: Final[tuple[int, ...]] = (
    0x000A,
    0x000B,
    0x000C,
    0x000D,
    0x0085,
    0x2028,
    0x2029,
)

#: What a case in `text-measurement.json` may say the rule does with its input.
#: A closed set, for the reason `_REFUSAL_MECHANISMS` is one: an open string was
#: checked for truthiness alone and could have read anything at all.
_VERDICTS: Final[frozenset[str]] = frozenset({"accepted", "empty", "too_long"})

#: The bound each field of a case is held to, by the name the corpus uses.
_BOUNDS: Final[dict[str, int]] = {
    "author": AUTHOR_MAX_LENGTH,
    "message": MESSAGE_MAX_LENGTH,
    "q": QUERY_MAX_LENGTH,
}

#: The keys a case carries. `length` is conditional -- present exactly when the
#: verdict is `accepted` -- so it is checked separately rather than listed here.
_CASE_KEYS: Final[frozenset[str]] = frozenset({"case", "description", "field", "input", "verdict"})

#: The two modules under `frontend/src` allowed to name a corpus file, each with the
#: ONE file it may name: its own context's cases, and never the other context's. The
#: guest book's reader holds the guest book's bounds and the to-do list's reader the
#: to-do list's, and a module of one context may not import the other's folder
#: (`tests/fitness/test_context_boundaries.py`), so a reader of both files could not
#: check either verdict. Written as paths rather than a pattern so that widening it is
#: an edit somebody has to make and defend, exactly as the seed guard's list is below.
_MAY_READ_ONE_CORPUS_FILE: Final[dict[str, str]] = {
    "frontend/src/contexts/guestbook/lib/entryText.test.ts": TEXT_RULES.name,
    "frontend/src/contexts/todo_list/lib/todoTask.test.ts": TODO_TASK_TEXT.name,
}

#: A corpus file's name: lower case, hyphen-separated, `.json`. Enforced rather
#: than described so the twentieth file is named like the first.
_FILENAME: Final = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*\.json$")

#: Shapes that would make a committed file look like it holds a real person's
#: data. Deliberately crude: the rule is "unmistakably synthetic", and anything
#: this catches was too close to the line to keep.
_LOOKS_PERSONAL: Final[tuple[tuple[str, re.Pattern[str]], ...]] = (
    ("an e-mail address", re.compile(r"[^\s@]+@[^\s@]+\.[a-z]{2,}", re.IGNORECASE)),
    ("an IBAN", re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,}\b")),
    ("a long digit run (account or national id)", re.compile(r"\d{9,}")),
    ("a telephone number", re.compile(r"\+\d[\d\s-]{7,}")),
)


def _files_on_disk() -> list[pathlib.Path]:
    """Every corpus file, in either half.

    One level down rather than at the top: the halves are directories, and a
    JSON file left loose at the root of `golden-set/` belongs to neither half.
    `test_no_corpus_file_sits_outside_a_half` is what catches that.
    """
    return sorted(GOLDEN_SET.glob("*/*.json"))


def _text_of(entry: dict[str, Any]) -> str:
    return f"{entry.get('author', '')} {entry.get('message', '')}"


def _items_of(path: pathlib.Path) -> list[dict[str, Any]]:
    """The items of one sequence file -- guest book entries or tasks, by the key it lists.

    For the rules both halves owe whatever their items are (a seed file shows a list,
    nothing in it stands near a limit). A file listing neither key is a shape no rule
    here knows, and says so rather than reading as empty.
    """
    story = _golden_set.story_of(path)
    if "tasks" in story:
        return tasks_of(path)
    assert "entries" in story, f"{path.name} lists neither `entries` nor `tasks`"
    return entries_of(path)


def _task_case(path: pathlib.Path, name: str) -> dict[str, Any]:
    """One named task out of a to-do list file of named tasks, by name and not by index."""
    for task in tasks_of(path):
        if task.get("case") == name:
            return task
    available = ", ".join(sorted(str(task.get("case")) for task in tasks_of(path)))
    raise AssertionError(f"no case {name!r} in {path.name}. Available: {available}")


def _task_bound() -> int:
    """`TODO_TASK_TEXT_MAX_LENGTH`, read from beside `TodoTask` at the moment a rule asks.

    Imported here rather than at the top of the module: the constant arrives with the
    implementation, and a failed import at the top would un-collect every rule in this
    file. Never `QUERY_MAX_LENGTH`, which is also 200 -- two rules sharing a number,
    and a corpus held to the phrase's bound proves the wrong one.
    """
    from app.contexts.todo_list.models.todo_task import TODO_TASK_TEXT_MAX_LENGTH

    bound: int = TODO_TASK_TEXT_MAX_LENGTH
    return bound


def _task_text_verdict(text: str) -> str:
    """`BR-06` and `BR-07` over one text, through the shared kernel and the model's constants.

    Normalized and trimmed first; then empty; then a line break of `LINE_BREAKS` left
    inside; then longer than the bound in code points -- the order
    `spec/contexts/todo_list.md` gives, so a text too long and on two lines is
    `multiline`. The same verdict names `todo-task-text.json` uses.
    """
    from app.contexts.todo_list.models.todo_task import LINE_BREAKS

    trimmed = normalize(text)
    if not trimmed:
        return "empty"
    if {chr(code) for code in LINE_BREAKS} & set(trimmed):
        return "multiline"
    return "too_long" if length(trimmed) > _task_bound() else "accepted"


# --------------------------------------------------------------------------- #
# The corpus and the locator agree about what exists
# --------------------------------------------------------------------------- #


def test_every_corpus_file_is_named_by_the_locator() -> None:
    """A file the locator cannot hand out demonstrates nothing to anybody.

    The comparison is on **equality**: a file on disk and absent from `ALL_FILES`
    is unreachable, and a constant pointing at a file that is gone raises only
    when somebody happens to run the test that uses it.
    """
    on_disk = {p.name for p in _files_on_disk()}
    named = {p.name for p in ALL_FILES}

    assert on_disk == named, (
        f"corpus and locator disagree. Only on disk: {sorted(on_disk - named)}; "
        f"only in tests/_golden_set.py: {sorted(named - on_disk)}"
    )


def test_the_corpus_has_exactly_one_locator() -> None:
    """There used to be two, and they diverged.

    Every other reader may WRAP the locator; none may compute the path itself. The
    check is on the *source*: a second module joining `golden-set` to a repository
    root it worked out for itself is the twin coming back.

    Two readers now, and the second is the reason this test is worth more than it
    was: `scripts/seed_golden_set.py` runs on a deployed environment, where a path
    that resolved somewhere plausible and wrong would fail far from here.
    """
    readers = ("e2e/suite/golden_set.py", "scripts/seed_golden_set.py")

    for relative in readers:
        reader = _golden_set.REPO_ROOT / relative
        # Asserted rather than left to `read_text`: a renamed reader used to surface
        # as a FileNotFoundError from inside a fitness test, which reads as the suite
        # being broken rather than as the rule being broken.
        assert reader.is_file(), (
            f"{relative} is gone. It was one of the corpus's declared readers -- if it "
            "moved, update `readers` here; if it was deleted, this rule has one fewer "
            "thing to hold and should say so."
        )
        source = reader.read_text(encoding="utf-8")
        assert "from tests._golden_set import" in source, (
            f"{relative} no longer imports the locator -- if it computes the corpus "
            "path itself, the twin is back"
        )
        # Anchored on the opening quote, which is what makes this catch the twin
        # rather than only its shortest spelling. The pair of exact literals this
        # replaces -- `"golden-set"` and `'golden-set'` -- missed every path
        # written in one piece, and `REPO_ROOT / "golden-set/seed"` is the more
        # natural way to write the mistake, not the less. Prose is unaffected:
        # both readers discuss `golden-set/` in their docstrings, where the word
        # follows a backtick or a space and never an opening quote. The lookbehind
        # is for the one shape that would otherwise read as a path: a docstring
        # whose text begins `golden-set`, where the third `"` of `\"\"\"` sits right
        # against it. A quote preceded by a quote opens a string; it is not one.
        assert not re.search(r"(?<![\"'])[\"']golden-set", source), (
            f"{relative} names the corpus directory itself; only tests/_golden_set.py "
            "may decide where the corpus is"
        )


def test_every_file_is_named_the_way_the_convention_says() -> None:
    """The naming convention, enforced rather than described."""
    wrong = [p.name for p in _files_on_disk() if not _FILENAME.match(p.name)]

    assert wrong == [], f"corpus files must be lower-case, hyphen-separated JSON: {wrong}"


def test_every_file_says_which_story_it_is_and_what_it_demonstrates() -> None:
    """A corpus file whose purpose lives only in the test that reads it is a file
    the next author copies for the wrong reason."""
    for path in ALL_FILES:
        story = _golden_set.story_of(path)
        assert story.get("story"), f"{path.name} has no `story`"
        assert len(str(story.get("demonstrates", ""))) > 40, (
            f"{path.name} does not say what it demonstrates, or says it in too few words"
        )


def test_every_entry_carries_the_keys_an_entry_has() -> None:
    for path in _ENTRY_FILES:
        for index, entry in enumerate(entries_of(path)):
            missing = _REQUIRED_KEYS - set(entry)
            assert not missing, f"{path.name}[{index}] is missing {sorted(missing)}"


def test_files_of_named_cases_name_every_case_and_never_repeat_one() -> None:
    """Cases are reached by name, so a duplicate makes `case()` return whichever
    came first and the second one silently stops being exercised."""
    for path in _CASE_FILES:
        names = [entry.get("case") for entry in entries_of(path)]
        assert all(names), f"{path.name} has an entry with no `case` name"
        assert len(names) == len(set(names)), f"{path.name} repeats a case name: {names}"


def test_every_named_case_carries_a_sentence_a_scenario_can_use() -> None:
    """The bridge between the corpus and a `.feature` a non-programmer reads.

    A scenario may say `the signature is nothing but spaces`; it may not say
    `author_whitespace_only`. The sentence lives in the corpus rather than in a
    mapping beside the step definitions, so there is one list -- and a case added
    without a sentence fails here instead of silently becoming unreachable from
    the black box.
    """
    for path in _CASE_FILES:
        sentences = [entry.get("description") for entry in entries_of(path)]
        assert all(sentences), f"{path.name} has a case with no `description`"
        assert len(sentences) == len(set(sentences)), (
            f"{path.name} gives two cases the same sentence, so a scenario naming it "
            f"reaches whichever comes first: {sentences}"
        )
        for sentence in sentences:
            assert str(sentence) == str(sentence).lower().replace("  ", " "), (
                f"{path.name}: {sentence!r} -- a scenario reads it mid-sentence, so it is "
                "lower case and has no double spaces"
            )


def test_the_sequence_files_have_no_case_names() -> None:
    """Their entries are a sequence somebody wrote, not a set of situations. Either
    key would invite a test to reach for one by name and stop caring about the order
    the file exists to carry.

    Both keys, because the rule in `golden-set/README.md` names both and only `case`
    was ever checked -- so half of a written rule was enforced and the other half was
    a sentence."""
    for path in _SEQUENCE_FILES:
        for key in ("case", "description"):
            assert all(key not in entry for entry in entries_of(path)), (
                f"{path.name} carries a {key!r}; its entries are a sequence"
            )


# --------------------------------------------------------------------------- #
# Each file is what it claims
# --------------------------------------------------------------------------- #


def test_every_entry_meant_to_pass_really_passes() -> None:
    """`BR-01`, applied to the corpus itself, on both halves.

    An ordinary entry the service would refuse turns every helper that fills a
    book from it into a refusal test nobody wrote -- and the failure surfaces as a
    count being wrong somewhere else entirely. A seed entry the service would
    refuse is worse and quieter: the seeder raises on the first non-201 against a
    live environment, so the preview a reviewer was waiting for comes up empty
    with the reason in a log nobody reads.
    """
    for path in _SEQUENCE_FILES:
        for index, entry in enumerate(entries_of(path)):
            author, message = normalize(entry["author"]), normalize(entry["message"])
            assert author, f"{path.name}[{index}] has an empty signature after trimming"
            assert message, f"{path.name}[{index}] has an empty message after trimming"
            assert length(author) <= AUTHOR_MAX_LENGTH, (
                f"{path.name}[{index}] signature is over the limit"
            )
            assert length(message) <= MESSAGE_MAX_LENGTH, (
                f"{path.name}[{index}] message is over the limit"
            )


def test_the_corpus_exercises_characters_outside_ascii() -> None:
    """The encoding path, end to end, on data rather than on a claim.

    Without a single character above U+007F in the corpus, a run on a machine
    whose default encoding is a single-byte code page decodes the file into
    different characters and every assertion still passes.

    Non-ASCII rather than any one alphabet: the repository is English
    (`spec/design/conventions.md` § Language), and what this proves is that bytes
    survive the round trip -- a property of the encoding, not of one language. The
    corpus is free to carry any script; it is not free to carry none.
    """
    for path in _SEQUENCE_FILES:
        text = " ".join(_text_of(e) for e in entries_of(path))

        assert any(ord(character) > 127 for character in text), (
            f"every character in {path.name} is ASCII -- the encoding path is then "
            "proved by nothing. Keep at least one entry outside ASCII."
        )


def test_the_corpus_exercises_a_message_with_line_breaks() -> None:
    """Inner whitespace is kept and outer whitespace is trimmed (`BR-01`). A corpus
    of single-line messages proves only the half that is easy.

    Owed by each half separately, and that is the whole reason the halves can
    diverge safely: the seed corpus stopped being the fixture corpus, so the
    properties that made the fixture worth looking at are now properties the seed
    corpus owes in its own right rather than ones it inherited.

    **The guest book's alone.** A message keeps its line breaks; a task is one line
    and a text with a line break inside it is refused (`BR-07`), so the to-do list's
    sequences owe the opposite -- `test_every_task_in_a_sequence_is_a_text_and_a_done_mark_on_one_line`.
    """
    for path in _SEQUENCE_FILES:
        assert any("\n" in e["message"] for e in entries_of(path)), (
            f"no message in {path.name} has a line break"
        )


def test_every_boundary_entry_sits_exactly_on_a_published_limit() -> None:
    """Read from the model's constants, never from a literal here.

    A test that writes `80` keeps proving the old number after the rule moves;
    this one moves with it and fails only when the FILE stops matching.
    """
    at_author_max = _golden_set.case(BOUNDARY, "author_at_maximum")
    assert length(normalize(at_author_max["author"])) == AUTHOR_MAX_LENGTH

    at_message_max = _golden_set.case(BOUNDARY, "message_at_maximum")
    assert length(normalize(at_message_max["message"])) == MESSAGE_MAX_LENGTH

    at_minimum = _golden_set.case(BOUNDARY, "both_at_minimum")
    assert length(normalize(at_minimum["author"])) == 1
    assert length(normalize(at_minimum["message"])) == 1

    padded = _golden_set.case(BOUNDARY, "padded_to_maximum")
    assert length(padded["author"]) > AUTHOR_MAX_LENGTH, "the padded case is not padded"
    assert length(normalize(padded["author"])) == AUTHOR_MAX_LENGTH


def test_every_boundary_entry_is_one_the_rules_accept() -> None:
    """The file's whole claim. An entry here that would be refused makes the
    boundary test assert a refusal while reading as if it asserted acceptance."""
    for entry in entries_of(BOUNDARY):
        author, message = normalize(entry["author"]), normalize(entry["message"])
        assert 1 <= length(author) <= AUTHOR_MAX_LENGTH, f"{entry['case']} would be refused"
        assert 1 <= length(message) <= MESSAGE_MAX_LENGTH, f"{entry['case']} would be refused"


def test_every_refused_entry_really_would_be_refused() -> None:
    """The mirror of the check above, and the one that matters more: a `refused`
    entry the rules happen to accept is a test that passes for the wrong reason."""
    for entry in entries_of(REFUSED):
        author, message = normalize(entry["author"]), normalize(entry["message"])
        breaks_a_rule = (
            not author
            or not message
            or length(author) > AUTHOR_MAX_LENGTH
            or length(message) > MESSAGE_MAX_LENGTH
        )
        assert breaks_a_rule, f"{entry['case']} breaks no rule -- it would be accepted"


#: The refusal mechanisms a corpus entry may name. `validation` is the schema
#: refusing the body before any handler runs, which answers `422` with FastAPI's
#: `{"detail": [...]}` and carries NO stable code -- `spec/design/api.md` § Refusals
#: says so, and `contracts/openapi/guestbook.yaml` declares codes only for the two
#: refusals a handler raises. The key names the MECHANISM, never a contract code;
#: an open string here was checked for truthiness alone and could have read
#: anything at all.
_REFUSAL_MECHANISMS: Final[frozenset[str]] = frozenset({"validation"})


def test_every_refused_entry_names_the_refusal_it_expects() -> None:
    for entry in entries_of(REFUSED):
        named = entry.get("refusal")
        assert named in _REFUSAL_MECHANISMS, (
            f"{entry['case']} names the refusal {named!r}, which is not one of "
            f"{sorted(_REFUSAL_MECHANISMS)}. This is the mechanism that refuses the "
            "entry, not a stable refusal code -- a schema refusal answers 422 with no "
            "code at all. Add the mechanism here when a second one becomes real."
        )


def test_the_refused_file_covers_both_fields_and_both_directions() -> None:
    """Scale, not verdict. A refusal file that only ever empties the signature
    stops covering the message the day somebody deletes the one case that did."""
    cases = {entry["case"] for entry in entries_of(REFUSED)}

    assert any("author_empty" in c or "author_whitespace" in c for c in cases)
    assert any("message_empty" in c or "message_whitespace" in c for c in cases)
    assert any(c.startswith("author") and "maximum" in c for c in cases)
    assert any(c.startswith("message") and "maximum" in c for c in cases)


def test_the_over_limit_cases_are_over_by_exactly_one() -> None:
    """One past the limit, never ten past it. The off-by-one is the defect a
    boundary test exists to catch, and a value an order of magnitude out passes
    identically whether the comparison is `>` or `>=`."""
    assert (
        length(_golden_set.case(REFUSED, "author_one_past_maximum")["author"])
        == AUTHOR_MAX_LENGTH + 1
    )
    assert (
        length(_golden_set.case(REFUSED, "message_one_past_maximum")["message"])
        == MESSAGE_MAX_LENGTH + 1
    )


# --------------------------------------------------------------------------- #
# The one file that holds cases rather than entries
# --------------------------------------------------------------------------- #


def test_every_case_carries_the_keys_a_case_has() -> None:
    """The shape the two readers agree on, held here rather than in either of them.

    Python's reader and the browser's reader both index these keys. A case missing
    one would fail in whichever suite happened to run first, with a message about
    that language rather than about the corpus.
    """
    for index, case in enumerate(cases_of(TEXT_RULES)):
        missing = _CASE_KEYS - set(case)
        assert not missing, f"{TEXT_RULES.name}[{index}] is missing {sorted(missing)}"


def test_every_case_is_named_and_described_exactly_once() -> None:
    """Cases are reached by name in both languages, so a duplicate silences one."""
    names = [case["case"] for case in cases_of(TEXT_RULES)]
    sentences = [case["description"] for case in cases_of(TEXT_RULES)]

    assert all(names), f"{TEXT_RULES.name} has a case with no name"
    assert len(names) == len(set(names)), f"{TEXT_RULES.name} repeats a case name"
    assert len(sentences) == len(set(sentences)), f"{TEXT_RULES.name} repeats a sentence"


def test_every_case_names_a_field_that_has_a_bound() -> None:
    """A case about a field nobody bounds is a case asserting nothing."""
    for case in cases_of(TEXT_RULES):
        assert case["field"] in _BOUNDS, (
            f"{case['case']} is about {case['field']!r}, which is not one of {sorted(_BOUNDS)}"
        )


def test_every_bounded_field_has_at_least_one_case() -> None:
    """Scale. The search phrase is the field whose bound was applied in the wrong
    order for the whole life of this repository, and a corpus that forgot it would
    leave that half proved by nothing."""
    covered = {str(case["field"]) for case in cases_of(TEXT_RULES)}

    assert covered == set(_BOUNDS), f"{TEXT_RULES.name} covers only {sorted(covered)}"


def test_every_case_states_a_verdict_the_rule_can_give() -> None:
    for case in cases_of(TEXT_RULES):
        assert case["verdict"] in _VERDICTS, (
            f"{case['case']} expects {case['verdict']!r}, which is not one of {sorted(_VERDICTS)}"
        )


def test_a_length_is_stated_exactly_when_one_exists() -> None:
    """`accepted` without a length would let a case pass under the wrong unit.

    "Accepted" is true of eighty emoji whether they are counted as eighty code
    points or as anything else that happens to fit. The length is what names the
    unit, so it is required -- and forbidden on a refusal, where there is no
    length to state and a number would be read as one.
    """
    for case in cases_of(TEXT_RULES):
        if case["verdict"] == "accepted":
            assert "length" in case, f"{case['case']} is accepted and states no length"
        else:
            assert "length" not in case, (
                f"{case['case']} is {case['verdict']} and states a length anyway"
            )


def test_every_case_really_gets_the_verdict_it_claims() -> None:
    """The file's whole claim, against the rule itself.

    The mirror of `test_every_refused_entry_really_would_be_refused` one section
    up, and it matters for the same reason: a case that claims `too_long` and is
    accepted makes both readers assert acceptance while reading as if they
    asserted a refusal.
    """
    for case in cases_of(TEXT_RULES):
        text = normalize(str(case["input"]))
        bound = _BOUNDS[str(case["field"])]
        verdict = "empty" if not text else ("too_long" if length(text) > bound else "accepted")

        assert verdict == case["verdict"], (
            f"{case['case']} claims {case['verdict']!r} and the rule says {verdict!r}"
        )
        if verdict == "accepted":
            assert length(text) == case["length"], (
                f"{case['case']} claims length {case['length']} and the rule says {length(text)}"
            )


def test_the_cases_are_written_in_escapes_rather_than_bytes() -> None:
    """Pure ASCII on disk, which is a rule this file owes and the others do not.

    The other corpus files must carry characters above U+007F, because what they
    prove is that bytes survive the round trip. This one proves the opposite kind
    of thing -- what a rule does to particular code points -- so the code points
    have to arrive unaltered, and `.gitattributes` already rewrites line endings
    in this repository. A case whose input is a raw U+2028 would be data one
    checkout setting could change.
    """
    raw = TEXT_RULES.read_bytes()
    above_ascii = [index for index, byte in enumerate(raw) if byte > 0x7F]

    assert above_ascii == [], (
        f"{TEXT_RULES.name} carries {len(above_ascii)} bytes above U+007F; every input "
        "is written as an escape so that no tool in the chain is part of the data"
    )


def test_the_cases_reach_past_what_a_runtime_default_can_see() -> None:
    """The corpus arrives with proof that it can see the defect it was written for.

    Two claims, because the defect had two halves. A case must exist whose length
    in code points differs from its length in UTF-16 code units -- otherwise the
    corpus cannot tell `[...v].length` from `v.length`. And a case must exist that
    `str.strip()` and this rule disagree about -- otherwise it cannot tell the
    written set from Python's own.
    """
    astral = [
        case["case"]
        for case in cases_of(TEXT_RULES)
        if len(normalize(str(case["input"])).encode("utf-16-le")) // 2
        != length(normalize(str(case["input"])))
    ]
    whitespace = [
        case["case"]
        for case in cases_of(TEXT_RULES)
        if str(case["input"]).strip() != normalize(str(case["input"]))
        and normalize(str(case["input"])) == str(case["input"]).strip().strip(chr(0xFEFF))
    ]

    assert astral, "no case distinguishes a code point from a UTF-16 code unit"
    assert whitespace, "no case distinguishes the written whitespace set from str.strip()"


# --------------------------------------------------------------------------- #
# The to-do list's files (`CR-2609-823a`): tasks, and cases of a task's text
# --------------------------------------------------------------------------- #


def test_every_task_in_a_sequence_is_a_text_and_a_done_mark_on_one_line() -> None:
    """The third key, `tasks`, as a sequence: `{text, done}` and nothing else, one line each.

    Exactly those two keys, so a sequence carries neither a `case` nor a
    `description` for a test to reach for by name -- its tasks are an order somebody
    added them in, and the ordinary file's reader asserts the reversal of that order
    (`BR-11`). `done` is a JSON boolean, because the file is read as the state a task
    ENDS with and a reader marks exactly the ones it names. And no line break anywhere
    in a text, from the seven the requirement writes: a task is one line (`BR-07`), and
    a sequence that carried one would make its reader's first addition a refusal
    nobody wrote. Owed by both halves -- the ordinary tasks and the example tasks a new
    environment opens with.
    """
    breaks = {chr(code) for code in _WRITTEN_LINE_BREAKS}
    for path in _TASK_SEQUENCE_FILES:
        for index, task in enumerate(tasks_of(path)):
            assert set(task) == _TASK_SEQUENCE_KEYS, (
                f"{path.name}[{index}] carries {sorted(task)}; a task in a sequence is "
                f"exactly {sorted(_TASK_SEQUENCE_KEYS)}"
            )
            assert isinstance(task["text"], str), f"{path.name}[{index}] has no text"
            assert isinstance(task["done"], bool), (
                f"{path.name}[{index}] marks done as {task['done']!r}, not a boolean"
            )
            carried = sorted(f"U+{ord(c):04X}" for c in breaks & set(task["text"]))
            assert not carried, f"{path.name}[{index}] carries the line breaks {carried}"


def test_the_task_sequences_exercise_characters_outside_ascii() -> None:
    """The encoding path, end to end, for the to-do list's sequences as for the guest book's.

    A task is sent, stored and shown like an entry, so a corpus of ASCII tasks would
    let a single-byte code page decode the file into different characters with every
    assertion still passing. Owed by each half, the example tasks included: a preview
    whose tasks are all ASCII shows a reviewer nothing about how the list renders
    anything else (`CR-2609-823a/R-11`, "one text above U+007F").
    """
    for path in _TASK_SEQUENCE_FILES:
        text = " ".join(str(task["text"]) for task in tasks_of(path))

        assert any(ord(character) > 127 for character in text), (
            f"every character in {path.name} is ASCII -- the encoding path is then "
            "proved by nothing. Keep at least one task outside ASCII."
        )


def test_the_ordinary_tasks_repeat_a_text_and_end_both_done_and_not_done() -> None:
    """What the ordinary file exists to show its reader, held rather than hoped for.

    A repeated text, because the same text twice is two tasks (`BR-12`) and a file
    without one lets a uniqueness check pass its reader unseen. Both marks, because
    the reader adds every task and only then marks the done ones -- a new task is never
    born done (`BR-08`) -- so a file with no done task never exercises a marking, and a
    file with no task left not done never shows a marking that stays put.
    """
    tasks = tasks_of(TODO_TASKS_ORDINARY)
    texts = [str(task["text"]) for task in tasks]

    assert len(texts) != len(set(texts)), (
        f"{TODO_TASKS_ORDINARY.name} repeats no text, so it cannot show that the same "
        "text twice is two tasks"
    )
    assert {task["done"] for task in tasks} == {True, False}, (
        f"{TODO_TASKS_ORDINARY.name} must end with some tasks done and some not"
    )


def test_every_named_task_carries_the_keys_its_file_gives_it() -> None:
    """The boundary file states what each task is `stored` as, the refused file the
    `refusal` it earns -- exactly those keys, each, so a reader indexing one never meets
    a task that lacks it, and a key nobody reads is not smuggled in beside them."""
    for path, keys in _TASK_CASE_KEYS.items():
        for index, task in enumerate(tasks_of(path)):
            assert set(task) == keys, (
                f"{path.name}[{index}] carries {sorted(task)}; each of its tasks is "
                f"exactly {sorted(keys)}"
            )


def test_files_of_named_tasks_name_every_case_and_sentence_once() -> None:
    """Cases are reached by name and by sentence, so a duplicate silences one of them.

    The sentence is what a scenario would read mid-sentence -- lower case, no double
    spaces -- the same bridge `test_every_named_case_carries_a_sentence_a_scenario_can_use`
    holds for the guest book's files.
    """
    for path in _TASK_CASE_KEYS:
        names = [task.get("case") for task in tasks_of(path)]
        sentences = [task.get("description") for task in tasks_of(path)]

        assert all(names), f"{path.name} has a task with no `case` name"
        assert len(names) == len(set(names)), f"{path.name} repeats a case name: {names}"
        assert all(sentences), f"{path.name} has a task with no `description`"
        assert len(sentences) == len(set(sentences)), f"{path.name} repeats a sentence"
        for sentence in sentences:
            assert str(sentence) == str(sentence).lower().replace("  ", " "), (
                f"{path.name}: {sentence!r} -- a scenario reads it mid-sentence, so it is "
                "lower case and has no double spaces"
            )


def test_every_refused_task_names_a_code_the_contract_gives() -> None:
    """A closed set: an open string was checked for truthiness alone and could read anything."""
    for task in tasks_of(TODO_TASKS_REFUSED):
        assert task["refusal"] in _TASK_TEXT_REFUSALS, (
            f"{task['case']} names the refusal {task['refusal']!r}, which is not one of "
            f"{sorted(_TASK_TEXT_REFUSALS)} -- the codes spec/design/api.md gives a task's text"
        )


def test_every_ordinary_task_is_one_the_rules_accept() -> None:
    """`BR-06` and `BR-07`, applied to the ordinary tasks themselves.

    An ordinary task the service would refuse turns the reader that adds all six into a
    refusal test nobody wrote, and the failure surfaces as the list read back being
    wrong. Through the shared kernel and the model's constants, never a literal here.
    """
    refused = {
        f"{TODO_TASKS_ORDINARY.name}[{index}]": verdict
        for index, task in enumerate(tasks_of(TODO_TASKS_ORDINARY))
        if (verdict := _task_text_verdict(str(task["text"]))) != "accepted"
    }

    assert refused == {}, f"ordinary tasks the rules refuse: {refused}"


def test_every_boundary_task_sits_exactly_on_the_task_bound() -> None:
    """Read from `TODO_TASK_TEXT_MAX_LENGTH`, never from a literal, and never from `QUERY_MAX_LENGTH`.

    Every boundary task stands exactly on a bound -- the maximum or the one-code-point
    minimum -- once normalized and trimmed, is accepted, and is `stored` as the shared
    rule leaves it. Both ends are present, and the padded task really is padded: it is
    over the bound as sent and on it once trimmed, which is the order `BR-06` gives. A
    value one code point off passes identically whether the comparison is `>` or `>=`;
    a value on the bound is the only one that tells them apart.
    """
    bound = _task_bound()
    off: list[str] = []
    for task in tasks_of(TODO_TASKS_BOUNDARY):
        kept = normalize(str(task["text"]))
        if kept != task["stored"]:
            off.append(f"{task['case']}: `stored` is not the text as the rule leaves it")
        if length(kept) not in {bound, 1}:
            off.append(f"{task['case']}: {length(kept)} code points, on neither bound")
        if (verdict := _task_text_verdict(str(task["text"]))) != "accepted":
            off.append(f"{task['case']}: the rules refuse it as {verdict}")

    assert off == [], f"boundary tasks off the bound: {off}"
    lengths = {length(normalize(str(task["text"]))) for task in tasks_of(TODO_TASKS_BOUNDARY)}
    assert lengths == {bound, 1}, f"the boundary tasks stand on {sorted(lengths)} only"

    padded = _task_case(TODO_TASKS_BOUNDARY, "text_padded_to_maximum")
    assert length(str(padded["text"])) > bound, "the padded task is not padded"


def test_every_task_refused_as_too_long_is_over_the_bound_by_exactly_one() -> None:
    """One past the bound, never ten past it, once normalized and trimmed.

    The off-by-one is the defect a boundary test exists to catch, and a value an order
    of magnitude out passes identically whether the comparison is `>` or `>=`. Measured
    after the trim: two hundred and five spaces are an empty text, not a long one
    (`BR-06`), and a padded text is over by one only once its padding is gone.
    """
    bound = _task_bound()
    too_long = [
        task
        for task in tasks_of(TODO_TASKS_REFUSED)
        if task["refusal"] == "todo_task_text_too_long"
    ]

    assert too_long, f"{TODO_TASKS_REFUSED.name} refuses no task as too long"
    off = {
        str(task["case"]): length(normalize(str(task["text"])))
        for task in too_long
        if length(normalize(str(task["text"]))) != bound + 1
    }
    assert off == {}, f"tasks refused as too long, not over the bound by exactly one: {off}"


def test_every_refused_task_really_breaks_the_rule_its_code_names() -> None:
    """The mirror of the ordinary tasks' rule, and the one that matters more.

    A refused task the rules happen to accept -- or refuse for a different reason -- is a
    test that passes for the wrong reason: its reader expects one code and the service
    gives another, or none. The verdict the rules give, through the model's constants,
    has to be the one the task's code stands for.
    """
    code_for = {
        "empty": "todo_task_text_empty",
        "multiline": "todo_task_text_multiline",
        "too_long": "todo_task_text_too_long",
        "accepted": "(accepted)",
    }
    wrong = {
        str(task["case"]): f"names {task['refusal']}, the rules give {given}"
        for task in tasks_of(TODO_TASKS_REFUSED)
        if (given := code_for[_task_text_verdict(str(task["text"]))]) != task["refusal"]
    }

    assert wrong == {}, f"refused tasks the rules treat otherwise: {wrong}"


def test_the_example_tasks_show_one_done_and_every_one_is_accepted() -> None:
    """The seed half's to-do file: tasks a reviewer can judge, and one of them done.

    At least one example task is done (`CR-2609-823a/R-11` clause 6), so a new
    environment shows a reviewer what a done task looks like without anybody ticking
    one. And every example task is one the rules accept (`BR-06`, `BR-07`, through the
    shared kernel and the model's constants): the seeder posts them through the
    application, so a refused one would stop the filling of a live environment on its
    first non-201, and the preview a reviewer was waiting for would come up empty with
    the reason in a log nobody reads.
    """
    tasks = tasks_of(TODO_TASKS_EXAMPLE)

    assert any(task.get("done") is True for task in tasks), (
        f"no example task in {TODO_TASKS_EXAMPLE.name} is done"
    )
    refused = {
        f"{TODO_TASKS_EXAMPLE.name}[{index}]": verdict
        for index, task in enumerate(tasks)
        if (verdict := _task_text_verdict(str(task.get("text", "")))) != "accepted"
    }
    assert refused == {}, f"example tasks the rules refuse: {refused}"


def test_every_task_text_case_carries_the_keys_a_case_has() -> None:
    """The shape the server's reader and the browser's reader agree on, held here.

    Both readers index these keys; a case missing one would fail in whichever suite ran
    first, with a message about that language rather than about the corpus. No `field`,
    because a task has one text: a key nobody reads invites a reader that branches on it.
    """
    for index, case in enumerate(cases_of(TODO_TASK_TEXT)):
        extra = set(case) - _TASK_TEXT_CASE_KEYS - {"length"}
        missing = _TASK_TEXT_CASE_KEYS - set(case)
        assert not missing, f"{TODO_TASK_TEXT.name}[{index}] is missing {sorted(missing)}"
        assert not extra, f"{TODO_TASK_TEXT.name}[{index}] carries {sorted(extra)} as well"


def test_every_task_text_case_is_named_and_described_exactly_once() -> None:
    """Cases are reached by name in both languages, so a duplicate silences one."""
    names = [case["case"] for case in cases_of(TODO_TASK_TEXT)]
    sentences = [case["description"] for case in cases_of(TODO_TASK_TEXT)]

    assert all(names), f"{TODO_TASK_TEXT.name} has a case with no name"
    assert len(names) == len(set(names)), f"{TODO_TASK_TEXT.name} repeats a case name"
    assert all(sentences), f"{TODO_TASK_TEXT.name} has a case with no sentence"
    assert len(sentences) == len(set(sentences)), f"{TODO_TASK_TEXT.name} repeats a sentence"


def test_every_task_text_case_states_one_of_the_four_verdicts() -> None:
    """A closed set of four, and every one of the four present.

    Closed, because an open string could claim anything. All four, because a corpus that
    lost a whole verdict lets a rule that never gives it pass on both sides -- a suite of
    zero disagreements over zero cases reads exactly like one that agreed.
    """
    stated = [case["verdict"] for case in cases_of(TODO_TASK_TEXT)]
    unknown = sorted({str(verdict) for verdict in stated} - _TASK_TEXT_VERDICTS)

    assert unknown == [], f"{TODO_TASK_TEXT.name} states verdicts outside the four: {unknown}"
    assert set(stated) == _TASK_TEXT_VERDICTS, (
        f"{TODO_TASK_TEXT.name} never states {sorted(_TASK_TEXT_VERDICTS - set(stated))}"
    )


def test_a_task_text_length_is_stated_exactly_when_the_case_is_accepted() -> None:
    """`accepted` without a length would let a case pass under the wrong unit.

    A hundred and one emoji are accepted whether they are counted as 101 code points or
    as 202 UTF-16 units under a bound of 400; the length is what names the unit, so it
    is required -- and forbidden on a refusal, where a number would be read as one.
    """
    for case in cases_of(TODO_TASK_TEXT):
        if case["verdict"] == "accepted":
            assert isinstance(case.get("length"), int), (
                f"{case['case']} is accepted and states no length"
            )
        else:
            assert "length" not in case, (
                f"{case['case']} is {case['verdict']} and states a length anyway"
            )


def test_the_task_text_cases_are_written_in_escapes_rather_than_bytes() -> None:
    """Pure ASCII on disk, for the reason `text-measurement.json` is.

    What this file proves is what a rule does to particular code points -- seven of them
    line breaks -- so the code points have to arrive unaltered, and `.gitattributes`
    already rewrites line endings in this repository. A case whose input is a raw
    U+2028 would be data one checkout setting could change.
    """
    raw = TODO_TASK_TEXT.read_bytes()
    above_ascii = [index for index, byte in enumerate(raw) if byte > 0x7F]

    assert above_ascii == [], (
        f"{TODO_TASK_TEXT.name} carries {len(above_ascii)} bytes above U+007F; every input "
        "is written as an escape so that no tool in the chain is part of the data"
    )
    assert json.loads(raw.decode("ascii"))["cases"], "and it still parses"


def test_the_task_text_cases_carry_every_one_of_the_seven_line_breaks_inside_a_text() -> None:
    """Each of the seven, left inside a text after the trim, in a case refused as `multiline`.

    The screen and the service read one written set, and a corpus missing one of the
    seven could not see the side that dropped it -- the two languages' own line-break
    defaults disagree about U+000B, U+000C and U+0085 among others, which is why the
    set is written down at all (`A-1`). Inside the text, because a line break at an end
    is trimmed and never refused.
    """
    inside: set[int] = set()
    for case in cases_of(TODO_TASK_TEXT):
        if case["verdict"] == "multiline":
            inside |= {ord(c) for c in normalize(str(case["input"]))} & set(_WRITTEN_LINE_BREAKS)
    missing = sorted(f"U+{code:04X}" for code in set(_WRITTEN_LINE_BREAKS) - inside)

    assert missing == [], f"no multiline case of {TODO_TASK_TEXT.name} carries {missing} inside"


def test_the_task_text_cases_hold_a_text_a_utf16_counter_would_refuse() -> None:
    """The known positive for the unit: a text well under the bound that UTF-16 puts over it.

    An accepted case whose length in code points is under the longest length the corpus
    accepts, and whose length in UTF-16 code units is over it -- a hundred and one emoji.
    A browser counting `.length` refuses it and the service stores it, so a corpus
    without such a case cannot see the defect `D-04` records. A case exactly ON the bound
    does not serve: whatever a rule counts, a text of emoji on the bound tells only
    whether it stops at the bound, not what it counts below it.
    """
    accepted = [case for case in cases_of(TODO_TASK_TEXT) if case["verdict"] == "accepted"]
    longest = max(int(case["length"]) for case in accepted)

    def utf16_units(value: str) -> int:
        return len(value.encode("utf-16-le")) // 2

    seen_by_unit: list[str] = []
    for case in accepted:
        kept = normalize(str(case["input"]))
        if length(kept) < longest < utf16_units(kept):
            seen_by_unit.append(str(case["case"]))

    assert seen_by_unit, (
        f"no accepted case of {TODO_TASK_TEXT.name} is under the bound in code points and "
        "over it in UTF-16 units, so the corpus cannot tell the two counts apart"
    )


# --------------------------------------------------------------------------- #
# The seam between the halves
# --------------------------------------------------------------------------- #


def test_no_corpus_file_sits_outside_a_half() -> None:
    """Every file belongs to `fixtures/` or to `seed/`, and the directory says
    which.

    A JSON file left at the root of `golden-set/` is a file whose purpose nobody
    declared -- which is exactly the state the split was made to end. It would
    also be invisible to `_files_on_disk()`, so every other rule in this module
    would pass over it in silence.
    """
    loose = sorted(p.name for p in GOLDEN_SET.glob("*.json"))

    assert loose == [], (
        f"corpus files outside a half: {loose}. Put each in golden-set/fixtures/ "
        "(the suites read it) or golden-set/seed/ (a new environment is filled "
        "with it)."
    )


def test_no_file_name_is_used_by_both_halves() -> None:
    """`golden()` searches the halves in order, so a repeated name would resolve
    to one of them and quietly shadow the other."""
    names = [p.name for p in _files_on_disk()]

    assert len(names) == len(set(names)), f"a file name appears in both halves: {names}"


def test_each_half_agrees_with_the_locator_about_what_is_in_it() -> None:
    """Per half, not only in aggregate -- and the difference is a real defect.

    `ALL_FILES` is the two tuples concatenated, so a seed file listed in
    `FIXTURE_FILES` satisfies every check that sweeps the whole corpus. It would
    then be held to the fixture rules and skipped by the seed rules: no check that
    it stays clear of a bound, and no check that no suite reads it. The file would
    be in the right directory and the wrong half, which is the split failing
    quietly rather than loudly.
    """
    for directory, declared in ((FIXTURES, FIXTURE_FILES), (SEED, SEED_FILES)):
        on_disk = {path.name for path in sorted(directory.glob("*.json"))}
        named = {path.name for path in declared}

        assert on_disk == named, (
            f"{directory.name}/ holds {sorted(on_disk)} and the locator names "
            f"{sorted(named)} for that half. A file in one half and declared in "
            "the other is held to the wrong rules."
        )


def test_the_frontend_reads_no_corpus_file() -> None:
    """The other half of the rule the seed guard covers, for the other tree.

    `golden-set/README.md` says "the frontend reads neither half" -- component
    fixtures are synthetic and written beside the test that needs them. Nothing held
    it: the seed guard scans `frontend/src`, but only for the SEED half, so a
    component test importing `entries-ordinary.json` was a rule with no mechanism.

    It matters more here than the directory suggests. The corpus is sized and shaped
    by what the server must prove; a component asserting against it acquires a
    dependency on a file whose reason to change lives in another suite entirely.

    **One exception per context, and it is the opposite case rather than a hole in
    this one.** `text-measurement.json` is not sized by what the server must prove --
    it is sized by what the two sides must AGREE about, and a claim about agreement
    cannot be checked from one side. Giving the browser its own copy would be the
    very defect this corpus exists to end, wearing a second file name: two lists
    that have to stay equal and nothing making them. `todo-task-text.json` is the
    same kind of file for the to-do list's own rule (`CR-2609-823a`). So exactly two
    modules may each read exactly their own context's file -- the directory it lies
    in, and that one name -- they are named in `_MAY_READ_ONE_CORPUS_FILE`, and every
    other file in `frontend/src` is refused as before, as is either reader reaching
    for the other's file or any other.
    """
    names = {path.name for path in ALL_FILES} | {"golden-set", "golden_set"}
    offenders: list[str] = []
    for source_file in sorted((_golden_set.REPO_ROOT / "frontend" / "src").rglob("*")):
        if source_file.suffix not in {".ts", ".tsx"} or not source_file.is_file():
            continue
        relative = source_file.relative_to(_golden_set.REPO_ROOT).as_posix()
        allowed = (
            {"golden-set", "golden_set", _MAY_READ_ONE_CORPUS_FILE[relative]}
            if relative in _MAY_READ_ONE_CORPUS_FILE
            else set()
        )
        text = source_file.read_text(encoding="utf-8")
        named = sorted(name for name in names - allowed if name in text)
        if named:
            offenders.append(f"{relative} names {named}")

    assert offenders == [], (
        f"the frontend reaches into the corpus: {offenders}. A component fixture is "
        "written beside the test that needs it; the corpus is sized by what the "
        "server has to prove, and it changes for reasons this suite cannot see."
    )


def test_no_suite_reads_the_seed_corpus() -> None:
    """The guard that makes the split real rather than decorative.

    The seed half exists to be looked at, not asserted about. A test that reaches
    for it re-couples the two: the seed corpus can then no longer be changed for
    the reason it exists -- to make a screen worth judging -- without reddening a
    suite, which is the exact defect the split was made to remove, restored under
    a new directory name.

    Checked on the source of the suites rather than by import, because the
    coupling that matters is a test NAMING the seed half, whether or not that
    line ever runs.
    """
    # Every name that reaches the seed half, not only the two the split shipped
    # with. `ALL_FILES` is the hole that mattered: it is the concatenation of both
    # tuples, it is how this very module sweeps the corpus, and a test written
    # `for path in ALL_FILES:` asserts about the seed half while containing none of
    # `SEED_FILES`, `WELCOME` or the file's own name. `SEED` is the same hole one
    # step earlier -- `SEED.glob("*.json")` needs no other name at all.
    # `TODO_TASKS_EXAMPLE` is the to-do list's seed file by its locator name
    # (`CR-2609-823a`): a suite asserting about the example tasks would re-couple the
    # halves exactly as one asserting about the welcome entries would.
    seed_names = {"SEED_FILES", "SEED", "ALL_FILES", "WELCOME", "TODO_TASKS_EXAMPLE"} | {
        p.name for p in SEED_FILES
    }
    permitted = {
        # The seeder is what the seed half is for.
        "scripts/seed_golden_set.py",
        # The locator declares it, and this module guards it.
        "tests/_golden_set.py",
        "tests/fitness/test_golden_set.py",
        # The seeder's own case: it proves the seeder, not the corpus.
        "tests/tooling/test_seed_golden_set.py",
    }

    # Whole words. `SEED` as a bare substring would match inside `SEED_FILES` and
    # inside any future `NO_SEED`, and a guard that cries wolf is one somebody
    # widens the permitted list to silence. `_` is a word character, so `SEED_FILES`
    # and `SEED` stay two distinct tokens under this.
    patterns = {
        name: re.compile(rf"\b{re.escape(name)}\b" if name.isidentifier() else re.escape(name))
        for name in seed_names
    }

    offenders: list[str] = []
    # Every tree that holds a suite of this application, so a test left out of this
    # list is a test the rule does not reach -- and the rule is only worth what it
    # reaches. The change process's suite under `.claude/` is not this rule's
    # business: it reads none of this corpus and is not this application's. The root
    # `conftest.py` is named separately: it is loaded for every collection and is
    # test infrastructure by its own docstring, but it sits above every tree here.
    scanned = [_golden_set.REPO_ROOT / "conftest.py"]
    for root in ("tests", "e2e", "frontend/src"):
        scanned.extend(sorted((_golden_set.REPO_ROOT / root).rglob("*")))

    for source_file in scanned:
        if source_file.suffix not in {".py", ".ts", ".tsx"} or not source_file.is_file():
            continue
        relative = source_file.relative_to(_golden_set.REPO_ROOT).as_posix()
        if relative in permitted:
            continue
        text = source_file.read_text(encoding="utf-8")
        named = sorted(name for name, pattern in patterns.items() if pattern.search(text))
        if named:
            offenders.append(f"{relative} names {named}")

    assert offenders == [], (
        "the seed corpus is read by a suite, which undoes the split: "
        f"{offenders}. A test needs a fixture; golden-set/fixtures/ is where "
        "fixtures live."
    )


def test_no_seed_entry_stands_near_a_published_limit() -> None:
    """The seed half is not a boundary file, and must not drift into being one.

    A signature padded to eighty characters proves a limit beautifully and makes
    a screen nobody can judge -- which is the job the seed half has. The margin is
    generous rather than exact: what is being refused is the habit, not a
    particular character count.

    An example task is held under three quarters of `TODO_TASK_TEXT_MAX_LENGTH` --
    under 150 code points while the bound is 200 (`CR-2609-823a/R-11` clause 2) --
    read from the constant, so the margin moves with the bound.
    """
    room = 0.75
    task_bound = _task_bound()

    for path in SEED_FILES:
        story = _golden_set.story_of(path)
        if "tasks" in story:
            for index, task in enumerate(tasks_of(path)):
                assert len(task["text"]) < task_bound * room, (
                    f"{path.name}[{index}] has a task near the limit. The seed corpus "
                    "is looked at; boundary values belong in "
                    "golden-set/fixtures/todo-tasks-boundary.json."
                )
            continue
        for index, entry in enumerate(entries_of(path)):
            assert len(entry["author"]) < AUTHOR_MAX_LENGTH * room, (
                f"{path.name}[{index}] has a signature near the limit. The seed "
                "corpus is looked at; boundary values belong in "
                "golden-set/fixtures/entries-boundary.json."
            )
            assert len(entry["message"]) < MESSAGE_MAX_LENGTH * room, (
                f"{path.name}[{index}] has a message near the limit. The seed "
                "corpus is looked at; boundary values belong in "
                "golden-set/fixtures/entries-boundary.json."
            )


def test_the_seed_half_shows_a_list_rather_than_an_entry() -> None:
    """One entry proves the screen renders; it does not show what a LIST looks
    like -- the spacing, the ordering, the ragged right edge of messages of
    different lengths. That is most of what a reviewer opens a preview for.

    The same holds for a list of tasks, done and not done side by side, so the
    example tasks owe at least three as well (`CR-2609-823a/R-11` clause 1)."""
    for path in SEED_FILES:
        assert len(_items_of(path)) >= 3, (
            f"{path.name} holds fewer than three items; a new environment then "
            "opens on a screen that does not show what a list looks like"
        )


# --------------------------------------------------------------------------- #
# Article XI -- the corpus is committed
# --------------------------------------------------------------------------- #


def test_no_corpus_value_looks_like_a_real_person() -> None:
    """The corpus is committed and its values reach JUnit reports and logs.

    Unmistakably synthetic, not merely fictional: a plausible IBAN in a git
    repository is something that looks like a real account to everyone who finds
    it later, whoever wrote it and whyever.
    """
    offenders: list[str] = []
    for path in _ENTRY_FILES:
        for entry in entries_of(path):
            for what, pattern in _LOOKS_PERSONAL:
                if pattern.search(_text_of(entry)):
                    offenders.append(f"{path.name}: {entry.get('case', entry['author'])} -- {what}")
    # Article XI reaches every committed value, whatever shape its file holds. The
    # cases files carry one string per item rather than two, and an assertion
    # message quoting a case is as public as one quoting an entry.
    for cases_file in (TEXT_RULES, TODO_TASK_TEXT):
        for case in cases_of(cases_file):
            for what, pattern in _LOOKS_PERSONAL:
                if pattern.search(str(case["input"])):
                    offenders.append(f"{cases_file.name}: {case['case']} -- {what}")

    assert offenders == [], f"corpus values that look like real personal data: {offenders}"


def test_no_task_looks_like_a_real_person() -> None:
    """Article XI for the to-do list's tasks, in both halves.

    A task is one line anybody may type, and the example tasks are shown to everybody
    who opens a preview, so they are held to the same "unmistakably synthetic" as the
    guest book's entries -- the text as sent, and the text a boundary task is stored as.
    A rule of its own rather than a branch of the one above: a task carries a `text`,
    and a sweep that read `author` and `message` from it would find nothing to check.
    """
    offenders: list[str] = []
    for path in _TASK_FILES:
        for index, task in enumerate(tasks_of(path)):
            values = f"{task.get('text', '')} {task.get('stored', '')}"
            for what, pattern in _LOOKS_PERSONAL:
                if pattern.search(values):
                    offenders.append(f"{path.name}[{index}] -- {what}")

    assert offenders == [], f"tasks that look like real personal data: {offenders}"


def test_the_detector_would_see_a_plausible_value() -> None:
    """The known positive, without which the check above proves nothing.

    A detector that has stopped detecting passes everything, silently, exactly
    when the rule starts being broken.
    """
    planted = {"author": "John Miller", "message": "contact: john.miller@example.com"}

    assert any(pattern.search(_text_of(planted)) for _, pattern in _LOOKS_PERSONAL)


# --------------------------------------------------------------------------- #
# The files parse the way the locator reads them
# --------------------------------------------------------------------------- #


def test_every_file_is_utf8_json_and_ends_with_a_newline() -> None:
    """The trailing newline is not cosmetic: a file without one makes every later
    diff show its last line as changed, which is how a corpus edit hides inside
    an unrelated review."""
    for path in ALL_FILES:
        raw = path.read_bytes()
        assert raw.endswith(b"\n"), f"{path.name} does not end with a newline"
        json.loads(raw.decode("utf-8"))


def test_a_missing_file_is_reported_with_the_directory_listing() -> None:
    """The locator's own contract: after a rename, the difference between a
    one-line fix and a hunt."""
    import pytest

    with pytest.raises(FileNotFoundError, match="Available:"):
        _golden_set.golden("no-such-file.json")

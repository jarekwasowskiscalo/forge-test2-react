"""The to-do list, in steps.

This module is where the to-do list's business language becomes HTTP and back
again. `todo_list.feature` says "the change should be refused as being about a
task that no longer exists"; the fact that such a refusal is a 404 carrying the
code `todo_task_not_found` lives here, so a change to the contract
(`spec/design/api.md` § The to-do list's endpoints and § The to-do list's
refusals) is a change to one file rather than to every scenario.

Assertions go through `e2e.harness.assertions` without exception -- pytest does
not rewrite asserts in this package, and a bare `assert a == b` here would print
its message and nothing else. That is what keeps a whole response body out of
the JUnit `<failure>` element.

**No fixture file is read here.** `e2e/suite/golden_set.py` re-exports the
guestbook's corpus alone, and the to-do list's corpus is proved by
`tests/integration/test_todo_tasks_corpus.py`, which reads it directly
(`spec/design/testing.md` § CR-2609-823a, "What the black box binds"). Every
value a scenario names is in the scenario, or produced by the one counting rule
the hundred-and-one scenario states.

Three conventions hold every step below, and each exists because its absence lets
a scenario pass while asserting nothing:

- **The task a scenario is about lives on `target.entry`**, exactly as the
  guestbook's entry does -- the `Given` that put it on the list writes it there,
  and "it", "its text", "that task" and "this person's screen" all read it. A
  `Then` that needs stored state reads the list again by that task's identifier
  rather than trusting any one answer.
- **"somebody" acts, and asserts that the act went through; "this person" acts,
  and leaves the answer to the `Then`.** A marking by "somebody" that silently
  failed would leave the order unchanged, and a scenario about the order would
  pass. A marking by "this person" is the thing a `Then` is about: saved in one
  scenario, refused as gone in another, from the same sentence.
- **"somebody else" is another visitor**, with a connection of their own -- so a
  list kept per visitor could not pass a scenario about a list everybody shares.
"""

import re
import threading
from collections.abc import Iterator, Mapping
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from typing import Any, Final

from pytest_bdd import given, parsers, then, when

from e2e.harness.assertions import found, should_answer, should_be
from e2e.harness.client import Answer, ApiClient, Row
from e2e.harness.list_response import rows, total_of
from e2e.suite.target import Target

#: The one resource this module drives. Named once: a path spelled a second time
#: is a path that can be spelled differently.
TASKS: Final[str] = "/todo-tasks"

#: The code a refusal carries when the task it is about no longer exists. Read
#: rather than the status alone: an unanswered route can answer with the same
#: status and no code, and the scenario would then pass against a route that is
#: not there.
TASK_NOT_FOUND: Final[str] = "todo_task_not_found"

#: The status each kind of write answers with when it went through.
_SAVED_WITH: Final[Mapping[str, int]] = {"POST": 201, "PATCH": 200}

#: The four things a task is (`spec/design/api.md` § `TodoTaskRead`). "Unchanged"
#: is these four, compared one at a time so a failure names the one that moved.
_A_TASK_IS: Final[tuple[str, ...]] = ("id", "text", "done", "created_at")

#: Where the deletion step records what the other tasks looked like at the moment
#: it deleted one -- the "before" of "the others should be unchanged".
_NEIGHBOURS: Final[str] = "neighbours_before_the_deletion"

#: How long the two halves of a simultaneous change wait for each other, and how
#: long for their answers. Finite, so a wedged request fails with a sentence rather
#: than hanging the run.
_RELEASE_SECONDS: Final[float] = 5.0
_ANSWER_SECONDS: Final[float] = 30.0

#: One quoted task text inside a sentence. Kept to the texts this file names: none
#: of them holds a quotation mark.
_QUOTED: Final[re.Pattern[str]] = re.compile(r'"([^"]+)"')


def _texts(sentence_fragment: str) -> list[str]:
    """`"First", "Second" and "Third"` as the three texts, in the order written."""
    return _QUOTED.findall(sentence_fragment)


def _path_of(task: Row) -> str:
    return f"{TASKS}/{task['id']}"


def _add(api: ApiClient, text: str) -> Row:
    """Put one task on the list and hand back what the application stored.

    Asserts the add went through: a precondition that silently failed produces a
    `Then` about the wrong thing, and the reader is sent to the application over a
    step that never ran.
    """
    answer = api.send("POST", TASKS, body={"text": text})
    should_answer(answer, 201, meaning="the task to be added")
    return answer.record()


def _mark(api: ApiClient, task: Row, *, done: bool) -> Answer:
    """Send the state chosen -- never "the opposite of what is stored"."""
    return api.send("PATCH", _path_of(task), body={"done": done})


def _correct(api: ApiClient, task: Row, text: str) -> Answer:
    return api.send("PATCH", _path_of(task), body={"text": text})


def _delete(api: ApiClient, task: Row) -> Answer:
    return api.send("DELETE", _path_of(task), body={})


def _listing(target: Target) -> Answer:
    """Read the whole list, as a person opening or reloading it does."""
    answer = target.api.get(TASKS)
    should_answer(answer, 200, meaning="the to-do list to be readable")
    return answer


def _read(answer: Answer) -> list[str]:
    """The texts of the list, top to bottom."""
    return [str(row.get("text")) for row in rows(answer)]


def _reading(answer: Answer, text: str) -> Row:
    """The one task on the list reading `text`, or a sentence about why there is not one.

    Found by what makes it the task this step means rather than by position:
    reaching for the second row starts asserting about a different task the moment
    the order is wrong, and does so silently.
    """
    matching = [row for row in rows(answer) if row.get("text") == text]
    if len(matching) != 1:
        raise AssertionError(
            f"expected exactly one task reading {text!r} on the to-do list, found "
            f"{len(matching)}. The application answered {answer}"
        )
    return matching[0]


def _with_id(answer: Answer, task: Row) -> Row | None:
    return next((row for row in rows(answer) if row.get("id") == task.get("id")), None)


def _the_task(target: Target) -> Row:
    """The task this scenario is about, or a sentence about the missing step."""
    if target.entry is None:
        raise AssertionError(
            "this step is about one task, but no earlier step of this scenario put one "
            "on the to-do list"
        )
    return target.entry


def _as_stored_now(target: Target, subject: str) -> Row:
    """The task this scenario is about, read back from the list as it is stored now."""
    listing = _listing(target)
    return found(_with_id(listing, _the_task(target)), subject=subject, answer=listing)


def _remember_what_was_added(target: Target, answer: Answer) -> None:
    """Make the task an add produced the one this scenario is about -- if it made one.

    Nothing is remembered from a refused add, and nothing is asserted here: the
    `Then` that follows ("the task should be saved") is what says whether the add
    went through, in its own words.
    """
    if answer.status == 201:
        target.entry = answer.record()


def _refusal_code(answer: Answer) -> object:
    """The code a refusal carries, or `None` when the answer carries none."""
    payload = answer.payload
    detail = payload.get("detail") if isinstance(payload, Mapping) else None
    return detail.get("code") if isinstance(detail, Mapping) else None


def _this_persons_task(target: Target, text: str) -> Row:
    """The task as this person's screen shows it -- which may no longer be stored.

    The scenario names it by its text; the screen knows it by what it read. The
    two have to agree, or the step is acting on a different task than the sentence
    says.
    """
    task = _the_task(target)
    should_be(task.get("text"), text, subject="the text of the task this person's screen shows")
    return task


@contextmanager
def _somebody_else() -> Iterator[ApiClient]:
    """Another visitor: a client and a connection of their own, shared with nobody."""
    client = ApiClient()
    try:
        yield client
    finally:
        client.close()


def _both_before_either_is_answered(task: Row, *bodies: Mapping[str, Any]) -> list[Answer]:
    """Send each change from a person of its own, all released at the same instant.

    Each person has a connection of their own and reads the list first, which is
    also what opens that connection -- so the barrier releases requests rather
    than handshakes, and no change waits for another's answer before it is sent.
    Sending them one after the other would pass over the whole-task write-back
    these scenarios exist to catch.

    What a client cannot do is choose which of the two the application applies
    later; only a test holding the stored list can
    (`tests/integration/test_todo_tasks_concurrency.py`). The answers come back in
    the order the changes were given.
    """
    people = [ApiClient() for _ in bodies]
    try:
        for person in people:
            should_answer(
                person.get(TASKS), 200, meaning="each person's screen to have read the list"
            )
        release = threading.Barrier(len(people), timeout=_RELEASE_SECONDS)

        def send(person: ApiClient, body: Mapping[str, Any]) -> Answer:
            release.wait()
            return person.send("PATCH", _path_of(task), body=body)

        with ThreadPoolExecutor(max_workers=len(people)) as pool:
            sent = [
                pool.submit(send, person, body) for person, body in zip(people, bodies, strict=True)
            ]
            return [change.result(timeout=_ANSWER_SECONDS) for change in sent]
    finally:
        for person in people:
            person.close()


# --------------------------------------------------------------------------
# Given -- the world before the scenario acts
# --------------------------------------------------------------------------


@given("the to-do list is empty")
def the_todo_list_is_empty(target: Target) -> None:
    """Nothing to do, and the step still earns its place.

    The world is emptied before every scenario by the autouse `empty_world`
    fixture, so this asserts rather than acts: a scenario whose counts start from
    somebody else's tasks fails with a wrong number, which reads as a defect.
    """
    listing = _listing(target)
    should_be(total_of(listing), 0, subject="the number of tasks the to-do list starts with")


@given(parsers.parse('the to-do list holds the task "{text}"'))
def the_list_holds_one_task(target: Target, text: str) -> None:
    target.entry = _add(target.api, text)


@given(parsers.parse('the to-do list holds the task "{text}", not done'))
def the_list_holds_one_task_not_done(target: Target, text: str) -> None:
    task = _add(target.api, text)
    should_be(task.get("done"), False, subject=f"the mark on {text!r} as it was added")
    target.entry = task


@given(parsers.parse('the to-do list holds the task "{text}", done'))
def the_list_holds_one_task_done(target: Target, text: str) -> None:
    """Added, then marked: a task is never born done, so "done" takes two acts."""
    task = _add(target.api, text)
    marked = _mark(target.api, task, done=True)
    should_answer(marked, 200, meaning=f"{text!r} to be marked done before the scenario acts")
    target.entry = marked.record()


@given(
    parsers.re(
        r'the to-do list holds the tasks (?P<texts>"[^"]+"(?:, "[^"]+")* and "[^"]+")'
        r"(?:, added in that order)?"
    ),
    converters={"texts": _texts},
)
def the_list_holds_these_tasks(target: Target, texts: list[str]) -> None:
    """Added one at a time, in the order the sentence reads, so "newest" is the last.

    Separate adds rather than anything in bulk: the order the next step asserts is
    the application's, and putting tasks there behind its back would prove the
    putting instead.
    """
    for text in texts:
        _add(target.api, text)


@given(parsers.parse('"{text}" is done'))
def a_listed_task_is_done(target: Target, text: str) -> None:
    task = _reading(_listing(target), text)
    should_answer(
        _mark(target.api, task, done=True),
        200,
        meaning=f"{text!r} to be marked done before the scenario acts",
    )


@given(parsers.parse('{count:d} tasks have been added, "{first}" first and "{last}" last'))
def many_tasks_have_been_added(target: Target, count: int, first: str, last: str) -> None:
    """The counting rule, "Task 001" onwards, zero-padded to three digits.

    A rule rather than a file of a hundred and one lines, which would be a second
    copy of the rule. The sentence names the first and the last task, so the step
    holds the rule to the sentence before it adds anything: a scenario whose words
    and data disagree asserts about neither.
    """
    names = [f"Task {number:03d}" for number in range(1, count + 1)]
    should_be(
        (names[0], names[-1]),
        (first, last),
        subject="the first and the last task the counting rule produces",
    )
    for name in names:
        _add(target.api, name)


@given(parsers.parse('somebody has the to-do list open, showing the task "{text}"'))
def somebody_has_the_list_open(target: Target, text: str) -> None:
    task = _add(target.api, text)
    should_be(_read(_listing(target)), [text], subject="what the first person's list shows")
    target.entry = task


def _marked_behind_this_persons_back(target: Target, *, done: bool) -> None:
    """This person reads the list; then somebody else marks the task the other way.

    Read on this person's own connection first, because that read *is* their
    screen: the task as it was shown to them is what their own marking will aim
    at, whatever is stored by the time they act.
    """
    task = _the_task(target)
    listing = _listing(target)
    shown = found(_with_id(listing, task), subject=f"task {task.get('text')!r}", answer=listing)
    should_be(
        shown.get("done"),
        not done,
        subject=f"the mark this person's screen shows on {shown.get('text')!r}",
    )
    with _somebody_else() as other:
        should_answer(
            _mark(other, shown, done=done), 200, meaning="somebody else's marking to be stored"
        )
    target.entry = shown


@given("somebody else has marked it done while this person's screen still shows it not done")
def somebody_else_has_marked_it_done(target: Target) -> None:
    _marked_behind_this_persons_back(target, done=True)


@given("somebody else has marked it not done while this person's screen still shows it done")
def somebody_else_has_marked_it_not_done(target: Target) -> None:
    _marked_behind_this_persons_back(target, done=False)


@given("somebody else has deleted it while this person's screen still shows it")
def somebody_else_has_deleted_it(target: Target) -> None:
    task = _the_task(target)
    listing = _listing(target)
    target.entry = found(
        _with_id(listing, task), subject=f"task {task.get('text')!r}", answer=listing
    )
    with _somebody_else() as other:
        should_answer(_delete(other, task), 204, meaning="somebody else's deletion to go through")


# --------------------------------------------------------------------------
# When -- what the scenario does
# --------------------------------------------------------------------------


@when(parsers.parse('somebody adds the task "{text}"'))
def somebody_adds_a_task(target: Target, text: str) -> None:
    _remember_what_was_added(target, target.api.send("POST", TASKS, body={"text": text}))


@when(parsers.parse('somebody adds the task "{text}" again'))
def somebody_adds_the_same_task_again(target: Target, text: str) -> None:
    """The second add of the same words. The first stays the task this scenario is about."""
    _add(target.api, text)


@when(parsers.parse('somebody adds the task "{text}", sent as if it were already done'))
def somebody_adds_a_task_claiming_done(target: Target, text: str) -> None:
    """A done mark on a new task: something only a caller going around the screen sends."""
    answer = target.api.send("POST", TASKS, body={"text": text, "done": True})
    _remember_what_was_added(target, answer)


@when(parsers.parse('somebody adds the task "{text}" with a line break after it'))
def somebody_adds_a_task_ending_in_a_line_break(target: Target, text: str) -> None:
    """One line feed after the last word: inside the written set trimmed from both ends."""
    _remember_what_was_added(target, target.api.send("POST", TASKS, body={"text": f"{text}\n"}))


@when(parsers.parse('somebody marks the newer "{text}" as done'))
def somebody_marks_the_newer_task_done(target: Target, text: str) -> None:
    """The newer is the one task reading `text` that is not the one added first.

    Told apart by identity rather than by position, because the position is the
    order's promise and this scenario is about identity: two tasks, marked apart.
    """
    older = _the_task(target)
    listing = _listing(target)
    newer = [
        row for row in rows(listing) if row.get("text") == text and row.get("id") != older.get("id")
    ]
    if len(newer) != 1:
        raise AssertionError(
            f"expected one more task reading {text!r} besides the one added first, found "
            f"{len(newer)}. The application answered {listing}"
        )
    should_answer(
        _mark(target.api, newer[0], done=True), 200, meaning="the newer task to be marked"
    )


def _somebody_marks(target: Target, text: str, *, done: bool) -> None:
    task = _reading(_listing(target), text)
    should_answer(_mark(target.api, task, done=done), 200, meaning=f"{text!r} to be marked")


@when(parsers.parse('somebody marks "{text}" as done'))
def somebody_marks_a_task_done(target: Target, text: str) -> None:
    _somebody_marks(target, text, done=True)


@when(parsers.parse('somebody marks "{text}" as not done'))
def somebody_marks_a_task_not_done(target: Target, text: str) -> None:
    _somebody_marks(target, text, done=False)


@when(parsers.parse('this person marks "{text}" as done'))
def this_person_marks_it_done(target: Target, text: str) -> None:
    _mark(target.api, _this_persons_task(target, text), done=True)


@when(parsers.parse('this person marks "{text}" as not done'))
def this_person_marks_it_not_done(target: Target, text: str) -> None:
    _mark(target.api, _this_persons_task(target, text), done=False)


@when(parsers.parse('somebody changes the text of "{old}" to "{new}"'))
def somebody_corrects_a_listed_task(target: Target, old: str, new: str) -> None:
    task = _reading(_listing(target), old)
    should_answer(_correct(target.api, task, new), 200, meaning=f"{old!r} to be corrected")


@when(parsers.parse('somebody changes its text to "{text}"'))
def somebody_corrects_the_task(target: Target, text: str) -> None:
    _correct(target.api, _the_task(target), text)


@when(parsers.parse('this person changes the text of "{old}" to "{new}"'))
def this_person_corrects_it(target: Target, old: str, new: str) -> None:
    _correct(target.api, _this_persons_task(target, old), new)


@when("the to-do list is displayed")
def the_todo_list_is_displayed(target: Target) -> None:
    target.api.get(TASKS)


@when("the list is reloaded")
def the_list_is_reloaded(target: Target) -> None:
    target.api.get(TASKS)


@when(parsers.parse('somebody else adds the task "{text}"'))
def somebody_else_adds_a_task(target: Target, text: str) -> None:
    """Asserted here, because no `Then` can see an answer made on another visitor's connection."""
    with _somebody_else() as other:
        _add(other, text)


@when("the first person reloads the list")
def the_first_person_reloads(target: Target) -> None:
    target.api.get(TASKS)


@when(parsers.parse('somebody deletes "{text}" and confirms'))
def somebody_deletes_a_task(target: Target, text: str) -> None:
    """One deletion: the question before it is the screen's, and here it was answered yes.

    The task deleted becomes the one this scenario is about ("that task"), and it
    carries what the other tasks looked like when it went -- which is the "before"
    of "the others should be unchanged".
    """
    listing = _listing(target)
    task = _reading(listing, text)
    should_answer(_delete(target.api, task), 204, meaning=f"{text!r} to be deleted")
    target.entry = {
        **task,
        _NEIGHBOURS: [row for row in rows(listing) if row.get("id") != task.get("id")],
    }


@when("somebody deletes that task again")
def somebody_deletes_that_task_again(target: Target) -> None:
    """A step of its own rather than the one above twice: `When ... And ...` reads as two acts."""
    _delete(target.api, _the_task(target))


@when(
    parsers.parse(
        'somebody changes its text to "{text}" and somebody else marks it done, '
        "both before either is answered"
    )
)
def a_correction_and_a_marking_at_once(target: Target, text: str) -> None:
    correction, marking = _both_before_either_is_answered(
        _the_task(target), {"text": text}, {"done": True}
    )
    should_answer(correction, 200, meaning="the correction to be stored")
    should_answer(marking, 200, meaning="the marking to be stored")


@when("two people both mark it done, both before either is answered")
def two_markings_at_once(target: Target) -> None:
    first, second = _both_before_either_is_answered(
        _the_task(target), {"done": True}, {"done": True}
    )
    should_answer(first, 200, meaning="the first person's marking to be stored")
    should_answer(second, 200, meaning="the second person's marking to be stored")


# --------------------------------------------------------------------------
# Then -- what must be true afterwards
# --------------------------------------------------------------------------


@then("the task should be saved")
def the_task_should_be_saved(target: Target) -> None:
    """Saved as the write that was made: an add is created, a change is applied."""
    answer = target.api.last
    expected = _SAVED_WITH.get(answer.method)
    if expected is None:
        raise AssertionError(
            f"this step follows an add or a change to a task, but the last request was {answer}"
        )
    should_answer(answer, expected, meaning="the task to be saved")


@then(parsers.parse("the to-do list should hold {count:d} task"))
@then(parsers.parse("the to-do list should hold {count:d} tasks"))
def the_todo_list_should_hold(target: Target, count: int) -> None:
    """Two spellings, one step: English inflects the noun after the number.

    Both numbers are asserted -- the count the list reports and the tasks it came
    back with -- because the list is read whole and the two must agree.
    """
    listing = _listing(target)
    should_be(total_of(listing), count, subject="the number of tasks the to-do list reports")
    should_be(
        len(rows(listing)), count, subject="the number of tasks the to-do list came back with"
    )


def _should_be_marked(target: Target, text: str, *, done: bool) -> None:
    task = _reading(_listing(target), text)
    should_be(task.get("done"), done, subject=f"whether {text!r} is done")


@then(parsers.parse('the task "{text}" should be shown as not done'))
@then(parsers.parse('"{text}" should be shown as not done'))
def a_task_should_be_shown_not_done(target: Target, text: str) -> None:
    _should_be_marked(target, text, done=False)


@then(parsers.parse('"{text}" should be shown as done'))
def a_task_should_be_shown_done(target: Target, text: str) -> None:
    _should_be_marked(target, text, done=True)


@then(parsers.parse('the to-do list should hold {count:d} tasks reading "{text}"'))
def the_list_should_hold_tasks_reading(target: Target, count: int, text: str) -> None:
    listing = _listing(target)
    reading = [row for row in rows(listing) if row.get("text") == text]
    should_be(len(reading), count, subject=f"the number of tasks reading {text!r}")
    should_be(
        len({str(row.get("id")) for row in reading}),
        count,
        subject=f"the number of distinct tasks reading {text!r}",
    )


@then(parsers.parse('the older "{text}" should still be shown as not done'))
def the_older_task_should_still_be_not_done(target: Target, text: str) -> None:
    older = _as_stored_now(target, subject=f"task {text!r} that was added first")
    should_be(older.get("text"), text, subject="the text of the task added first")
    should_be(older.get("done"), False, subject="whether the task added first is done")


def _stored_text_should_be(target: Target, text: str) -> None:
    """Read back from the list, not off the add's own answer.

    An application that answered with what it was sent and stored something else
    would pass every assertion made on the answer -- which is the failure a black
    box exists to catch.
    """
    stored = _as_stored_now(target, subject="the task that was added")
    should_be(stored.get("text"), text, subject="the stored text")


@then(parsers.parse('the stored text should be exactly "{text}"'))
def the_stored_text_should_be_exactly(target: Target, text: str) -> None:
    _stored_text_should_be(target, text)


@then(parsers.parse('the stored text should be exactly "{text}", with its two and three spaces'))
def the_stored_text_should_keep_its_spaces(target: Target, text: str) -> None:
    """The sentence says the text has a run of two spaces and a run of three.

    Held to it first: an editor that tidies the feature file's whitespace would
    otherwise turn this into a scenario about "Buy two lamps", which passes on an
    application that squeezes every run of spaces to one.
    """
    runs = sorted({len(run) for run in re.findall(r" {2,}", text)})
    should_be(runs, [2, 3], subject="the runs of spaces inside the text the scenario names")
    _stored_text_should_be(target, text)


@then(parsers.re(r'it should read (?P<texts>"[^"]+"(?:, "[^"]+")+)'), converters={"texts": _texts})
def the_displayed_list_should_read(target: Target, texts: list[str]) -> None:
    listing = target.api.last
    should_answer(listing, 200, meaning="the to-do list to be readable")
    should_be(_read(listing), texts, subject="the to-do list, top to bottom")


@then(
    parsers.re(r'the list should (?:still )?read (?P<texts>"[^"]+"(?:, "[^"]+")+)'),
    converters={"texts": _texts},
)
def the_list_should_read(target: Target, texts: list[str]) -> None:
    """Read again rather than off an earlier answer: the claim is about what is stored."""
    should_be(_read(_listing(target)), texts, subject="the to-do list, top to bottom")


@then(parsers.parse('"{text}" should be at the top of their list'))
def a_task_should_be_at_the_top_of_their_list(target: Target, text: str) -> None:
    listing = target.api.last
    should_answer(listing, 200, meaning="their to-do list to be readable")
    listed = _read(listing)
    if not listed:
        raise AssertionError(
            f"their to-do list came back empty. The application answered {listing}"
        )
    should_be(listed[0], text, subject="the task at the top of their list")


@then(parsers.parse('its text should still be "{text}"'))
def its_text_should_still_be(target: Target, text: str) -> None:
    stored = _as_stored_now(target, subject=f"task {text!r}")
    should_be(stored.get("text"), text, subject="the task's text")


@then(parsers.parse("all {count:d} tasks should be shown at once"))
def all_tasks_should_be_shown_at_once(target: Target, count: int) -> None:
    """One read, every task: nothing handed out in pieces, nothing left behind."""
    listing = target.api.last
    should_answer(listing, 200, meaning="the to-do list to be readable")
    should_be(len(rows(listing)), count, subject="the number of tasks one read came back with")
    should_be(total_of(listing), count, subject="the number of tasks the to-do list reports")


@then(parsers.parse('"{top}" should be at the top and "{bottom}" at the bottom'))
def the_ends_of_the_list_should_be(target: Target, top: str, bottom: str) -> None:
    listed = _read(target.api.last)
    if not listed:
        raise AssertionError(
            f"the to-do list came back empty. The application answered {target.api.last}"
        )
    should_be(listed[0], top, subject="the task at the top of the list")
    should_be(listed[-1], bottom, subject="the task at the bottom of the list")


@then(parsers.parse('there should be no task "{text}" on the list'))
@then(parsers.parse('after a reload there should be no task "{text}" on the list'))
def there_should_be_no_task_reading(target: Target, text: str) -> None:
    left = [row for row in rows(_listing(target)) if row.get("text") == text]
    should_be(len(left), 0, subject=f"the number of tasks reading {text!r} on the list")


@then(parsers.parse('"{first}" and "{second}" should be unchanged'))
def the_other_tasks_should_be_unchanged(target: Target, first: str, second: str) -> None:
    """Each of the others, field by field, against how it stood when the deletion was made."""
    before = _the_task(target).get(_NEIGHBOURS)
    if not isinstance(before, list):
        raise AssertionError(
            "this step compares the other tasks with how they stood when one was deleted, "
            "but no deletion in this scenario recorded them"
        )
    listing = _listing(target)
    for text in (first, second):
        was = [row for row in before if row.get("text") == text]
        if len(was) != 1:
            raise AssertionError(
                f"expected exactly one task reading {text!r} when the deletion was made, "
                f"found {len(was)}"
            )
        now = _reading(listing, text)
        for field in _A_TASK_IS:
            should_be(now.get(field), was[0].get(field), subject=f"the {field} of {text!r}")


@then("the change should be refused as being about a task that no longer exists")
@then("the operation should be refused as being about a task that no longer exists")
def refused_as_a_task_that_no_longer_exists(target: Target) -> None:
    answer = target.api.last
    should_answer(answer, 404, meaning="the change to be refused: the task no longer exists")
    should_be(_refusal_code(answer), TASK_NOT_FOUND, subject="the reason the refusal gives")


@then(parsers.parse('the list should show "{text}" in its place'))
def the_corrected_text_should_stand_in_its_place(target: Target, text: str) -> None:
    """The same task reads the new text, and no task still reads the old one.

    "In its place" is identity: a correction that wrote a second task, or deleted
    the first and added another, would show the new words on the list too.
    """
    corrected = _the_task(target)
    listing = _listing(target)
    now = found(_with_id(listing, corrected), subject="the task that was corrected", answer=listing)
    should_be(now.get("text"), text, subject="the text of the task that was corrected")
    old = corrected.get("text")
    still_old = [row for row in rows(listing) if row.get("text") == old]
    should_be(len(still_old), 0, subject=f"the number of tasks still reading {old!r}")


@then(parsers.parse('the task should read "{text}"'))
def the_task_should_read(target: Target, text: str) -> None:
    stored = _as_stored_now(target, subject="the task both people changed")
    should_be(stored.get("text"), text, subject="the task's text")


@then("it should be shown as done")
def it_should_be_shown_as_done(target: Target) -> None:
    stored = _as_stored_now(target, subject="the task both people changed")
    should_be(stored.get("done"), True, subject="whether the task is done")

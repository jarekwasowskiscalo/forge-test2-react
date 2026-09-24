"""Where the golden set is -- both halves of it.

`golden-set/` at the repository root is the one corpus of reference data this
project ships, and it is cut in two by what the data is FOR:

- `golden-set/fixtures/` -- what the suites read instead of inventing. Asserted
  about, by name or by sentence, and wiped between scenarios.
- `golden-set/seed/` -- what a freshly created environment is filled with, so a
  preview or a fresh clone shows a screen somebody can judge. Loaded once,
  through the application's own API, and never asserted about.

The two were one directory until the split, and the seam was already leaking:
adding an entry to make a preview look richer weakened a paging test that
depended on the count, and adding a boundary case to prove a rule changed what a
reviewer saw on screen. The halves have different lifecycles -- one is truncated
before every scenario, the other survives for the life of the environment -- so
they are different data with one set of shared rules, not one corpus with two
uses. `tests/fitness/test_golden_set.py` holds the seam: no suite may read the
seed half.

**This module is the only place that decides where either half is.** Three
readers: the pytest suite directly, the end-to-end one through
`e2e/suite/golden_set.py` (the fixture half only), and
`scripts/seed_golden_set.py` (the seed half, plus the boundary fixture under
`seed.sh --boundary`). There used to be a hand-copied
twin, because the e2e suite ran in a virtualenv it could not import `tests/`
from; the copies were guarded by an equality check on the directory they
resolved to, and by the time the twin was deleted they had diverged in return
type, in exception type, and in what the failure listed -- none of which that
check could see. `tests/fitness/test_golden_set.py` now checks that there is
still exactly one. A second locator for the second half would re-create that
defect exactly, which is why the split is two directories and not two modules.

Imports nothing but `json`, `pathlib` and `typing`, which is what makes it safe
for the end-to-end suite to read: `tests/fitness/test_e2e_isolation.py` forbids
that suite from importing first-party code, with this as the single named
exception.

Resolved from `__file__`, never from the working directory, so `uv run pytest`,
a single-file run, an IDE runner and a CI job all read the same bytes on Linux,
macOS.

**Real committed data here; anything hostile lives in code.** The corpus holds
values a guest could plausibly submit -- including ones the rules refuse, because
somebody typing a space instead of a name is a thing that happens. Bytes built to
break a parser are not that, and belong beside the assertion that explains them
(`spec/design/testing.md` § The reference corpus).
"""

import json
import pathlib
from typing import Any, Final

#: `tests/_golden_set.py` -> `tests/` -> the repository root.
REPO_ROOT: Final[pathlib.Path] = pathlib.Path(__file__).resolve().parents[1]

GOLDEN_SET: Final[pathlib.Path] = REPO_ROOT / "golden-set"

#: The half the suites read instead of inventing data. Asserted about.
FIXTURES: Final[pathlib.Path] = GOLDEN_SET / "fixtures"

#: The half a freshly created environment is filled with. Never asserted about.
SEED: Final[pathlib.Path] = GOLDEN_SET / "seed"

#: Ordinary entries, in the order a guest wrote them. Every one satisfies `BR-01`.
#: The list order is WRITING order, not display order -- `BR-04` reverses it, and
#: a test that fills a book from here and asserts the reverse is asserting the
#: rule rather than the file.
ORDINARY: Final[pathlib.Path] = FIXTURES / "entries-ordinary.json"

#: Values exactly at the published limits. Every one must be ACCEPTED; the other
#: side of each boundary is computed by the test from the same constants, so the
#: pair proves the limit sits where the contract says rather than somewhere near it.
BOUNDARY: Final[pathlib.Path] = FIXTURES / "entries-boundary.json"

#: Entries the rules refuse, each naming the mechanism that refuses it -- not a
#: stable refusal code; a schema refusal answers 422 with none.
REFUSED: Final[pathlib.Path] = FIXTURES / "entries-refused.json"

#: What a new environment opens with. Ordinary entries chosen to be LOOKED AT:
#: they carry the same round-trip properties the suites care about (characters
#: outside ASCII, a message with line breaks) without any value near a limit,
#: because an eighty-character signature makes a screen nobody can judge.
WELCOME: Final[pathlib.Path] = SEED / "entries-welcome.json"

#: How a text field is trimmed and how long it is, in the cases where the browser
#: and the server used to disagree. **The one file in this corpus that holds cases
#: rather than entries**, and the one file the frontend may read: proving that two
#: languages measure one string identically cannot be done from one side, and a
#: second copy of the corpus beside the browser's test would be the very defect
#: being repaired, wearing a different file name. `golden-set/README.md` § The
#: frontend and this corpus carries the exception and its reason.
TEXT_RULES: Final[pathlib.Path] = FIXTURES / "text-measurement.json"

# --------------------------------------------------------------------------- #
# The to-do list's files (`CR-2609-823a`). Every one holds TASKS or cases of a
# task's text, never guest book entries, which is why they sit under a key of
# their own -- `tasks` -- and are read by `tasks_of` rather than `entries_of`.
# Named `todo-task...` and never a bare `task`, because *task* is also a word of
# the change process (`spec/glossary.md` § Task (process)).
# --------------------------------------------------------------------------- #

#: Ordinary tasks, in ADDING order, each with the done mark it ends with. A reader
#: adds every one in file order and only then marks the done ones -- a new task is
#: never born done (`BR-08`) -- and asserts the reversal of the file with its marks
#: (`BR-11`), which is a claim about the rule rather than a second copy of the data.
TODO_TASKS_ORDINARY: Final[pathlib.Path] = FIXTURES / "todo-tasks-ordinary.json"

#: Task texts exactly on the bound, each ACCEPTED, each with the text it is
#: `stored` as once normalized and trimmed. The other side of the bound is
#: `TODO_TASKS_REFUSED`, one code point further.
TODO_TASKS_BOUNDARY: Final[pathlib.Path] = FIXTURES / "todo-tasks-boundary.json"

#: Task texts the rules refuse, each naming the `refusal` code the contract gives
#: it (`spec/design/api.md` § The to-do list's refusals) -- a contract code, unlike
#: `REFUSED`, whose key names the mechanism because a schema refusal has no code.
TODO_TASKS_REFUSED: Final[pathlib.Path] = FIXTURES / "todo-tasks-refused.json"

#: How a task's text is judged -- the bound in code points and the seven line
#: breaks of `BR-07` -- as CASES, with a fourth verdict, `multiline`, beside the
#: three `TEXT_RULES` knows. Read by the server's rule test and by exactly one
#: module of the to-do list's browser folder, against the same bytes, for the
#: reason `TEXT_RULES` is read by both: agreement cannot be checked from one side.
TODO_TASK_TEXT: Final[pathlib.Path] = FIXTURES / "todo-task-text.json"

#: The example tasks a new environment's to-do list opens with. Written with the
#: seeder that posts it; named here first, because the locator is the one place
#: that decides where the corpus lies and no implementer may edit it.
TODO_TASKS_EXAMPLE: Final[pathlib.Path] = SEED / "todo-tasks-example.json"

#: The fixture half, for a test that wants to sweep all of it.
FIXTURE_FILES: Final[tuple[pathlib.Path, ...]] = (
    ORDINARY,
    BOUNDARY,
    REFUSED,
    TEXT_RULES,
    TODO_TASKS_ORDINARY,
    TODO_TASKS_BOUNDARY,
    TODO_TASKS_REFUSED,
    TODO_TASK_TEXT,
)

#: The seed half. Read by `scripts/seed_golden_set.py`, which also reaches for
#: `BOUNDARY` under `--boundary` -- the one crossing between the halves --
#: `tests/fitness/test_golden_set.py` refuses a suite that names it, because a
#: test asserting about the seed corpus has quietly undone the split.
SEED_FILES: Final[tuple[pathlib.Path, ...]] = (WELCOME, TODO_TASKS_EXAMPLE)

#: Every file the corpus holds, both halves. A file absent from this tuple is a
#: file the locator cannot hand out, and `tests/fitness/test_golden_set.py`
#: refuses it -- a fixture nobody can reach demonstrates nothing to anybody.
ALL_FILES: Final[tuple[pathlib.Path, ...]] = FIXTURE_FILES + SEED_FILES


def golden(name: str) -> pathlib.Path:
    """The path of one golden-set file, named as it is named on disk.

    Searched across both halves rather than joined to one of them: a caller that
    had to say which half a file lives in would be a second place deciding where
    the corpus is, and names are unique across the two (checked by
    `tests/fitness/test_golden_set.py`).

    A missing file raises here, with the listing of what IS there, rather than as
    a bare `FileNotFoundError` from whichever line happened to open it -- which,
    after a rename, is the difference between a one-line fix and a hunt.
    """
    for path in (FIXTURES / name, SEED / name):
        if path.is_file():
            return path
    available = ", ".join(sorted(p.name for p in GOLDEN_SET.glob("*/*.json"))) or "(empty)"
    raise FileNotFoundError(f"{name!r} is not in {GOLDEN_SET}. Available: {available}")


def story_of(path: pathlib.Path) -> dict[str, Any]:
    """One corpus file, decoded whole: its story name, what it demonstrates, its entries.

    UTF-8 is named rather than left to the platform default: the corpus carries
    characters outside ASCII on purpose, and a run on a machine whose default
    encoding is a single-byte code page would otherwise decode them into different
    characters and fail on an assertion about the data instead of about the
    encoding.
    """
    return json.loads(golden(path.name).read_text(encoding="utf-8"))  # type: ignore[no-any-return]


def entries_of(path: pathlib.Path) -> list[dict[str, Any]]:
    """Just the entries of one corpus file, in file order."""
    entries = story_of(path)["entries"]
    if not isinstance(entries, list) or not entries:
        raise AssertionError(
            f"{path.name} carries no entries -- a corpus file with none proves nothing"
        )
    return entries


def tasks_of(path: pathlib.Path) -> list[dict[str, Any]]:
    """Just the tasks of one to-do corpus file, in file order.

    A reader of its own beside `entries_of` and `cases_of`, for the reason those two
    are apart: a task is neither a guest book entry nor an input to a rule. It is a
    `text` and, in a sequence, the `done` mark it ends with -- so a caller that swept
    "whatever list the file has" would hold a task to the rules about `author` and
    `message`, or skip the rules that fit it.
    """
    tasks = story_of(path)["tasks"]
    if not isinstance(tasks, list) or not tasks:
        raise AssertionError(
            f"{path.name} carries no tasks -- a corpus file with none proves nothing"
        )
    return tasks


def cases_of(path: pathlib.Path) -> list[dict[str, Any]]:
    """Just the cases of `TEXT_RULES` or of `TODO_TASK_TEXT`, in file order.

    A separate reader from `entries_of` rather than one that accepts either key,
    because the two shapes are different data: an entry is a guest book entry and
    carries `author` and `message`; a case is one input to the trimming and length
    rule, and carries the verdict expected of it, the length expected after
    normalization, and -- in `TEXT_RULES`, which serves three fields -- the field it
    is about. A single reader returning "whatever list
    the file has" would let a caller sweep both and assert about neither.
    """
    cases = story_of(path)["cases"]
    if not isinstance(cases, list) or not cases:
        raise AssertionError(
            f"{path.name} carries no cases -- a corpus file with none proves nothing"
        )
    return cases


def case(path: pathlib.Path, name: str) -> dict[str, Any]:
    """One named case out of `entries-boundary.json` or `entries-refused.json`.

    By name and not by index: a test that reaches for `entries[2]` starts
    asserting about a different case the moment somebody inserts one above it,
    and it does so silently.
    """
    for entry in entries_of(path):
        if entry.get("case") == name:
            return entry
    available = ", ".join(sorted(str(e.get("case")) for e in entries_of(path)))
    raise AssertionError(f"no case {name!r} in {path.name}. Available: {available}")


def described(path: pathlib.Path, description: str) -> dict[str, Any]:
    """One case, found by the sentence the corpus carries for it.

    This is the lookup a Gherkin scenario uses: a `.feature` is read by somebody
    who does not write code, so it may name `the signature is all spaces` and must
    not name `author_whitespace_only`. Keeping the sentence IN the corpus rather than
    in a mapping beside the steps means there is one list, and a case added
    without a sentence fails in `tests/fitness/test_golden_set.py` rather than
    silently becoming unreachable from the black box.
    """
    for entry in entries_of(path):
        if entry.get("description") == description:
            return entry
    available = "; ".join(sorted(str(e.get("description")) for e in entries_of(path)))
    raise AssertionError(
        f"no case described as {description!r} in {path.name}. Available: {available}"
    )

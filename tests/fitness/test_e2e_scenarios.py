"""What behave gave the suite for free, and pytest-bdd does not.

The first test here is the important one: **every step of every scenario
resolves to a definition.** `behave --dry-run` did that, and CI ran it as a gate.
Its obvious successor does not work -- `pytest --generate-missing` prints the
unbound step and then exits 0 whether anything is missing or not, so a `|| die`
on it is decoration. So the check is rebuilt here out of pytest-bdd's own parts:
its `FeatureParser` reads the `.feature` files, its step decorators leave a
`StepFunctionContext` on each definition, and `parser.is_matching` is the same
call it makes when a scenario runs. Nothing here reimplements the matching, so
nothing here can disagree with it.

It also catches the mechanical mistake that the migration made most likely.
pytest-bdd treats a bare string as an **exact** matcher, so
`@then("the import should create {count:d} new cases")` without
`parsers.parse(...)` around it is a definition that can never match anything --
and it fails when the scenario runs, not when it collects.

The rest are smaller rules that used to be enforced by something else, or by
nothing:

- Every scenario asserts something, and every scenario *does* something. The
  second half was missing, and it mattered more than it looked: a scenario with
  a `Then` and no `When` used to be caught only at run time, by
  `ApiClient.last` refusing to answer -- and for a while not even then, because
  the `target` fixture's coherence check populated that answer before the first
  step ran. A `Then only 0 cases should be returned` with no `When` was green.
- Gherkin stays in business language. `.feature` files are written for somebody
  who knows what a fully paid case is and does not know what a 422 is.
- No two scenarios share a name: pytest-bdd keys them in a dict, so a duplicate
  silently collapses into one and the suite quietly runs twenty instead of
  twenty-one.
- No step text is defined twice. behave raised `AmbiguousStep`; pytest-bdd
  registers both and lets the last `import *` win, without a word.
- Every step module is imported by the binding module, and none of them defines
  `__all__` -- the two ways the wildcard imports in `e2e/suite/test_scenarios.py`
  can silently register nothing. And the steps package's own `__init__.py`
  defines no step, because nothing star-imports *it*: a step written there is
  unbound with no error anywhere.

Every detector is proved against a known positive first, in the idiom
`tests/fitness/test_layering.py` established: a check that has stopped checking passes
everything, and it does so exactly when the rule has started being broken.
"""

import ast
import importlib
import pathlib
import re
from typing import Any, Final

from pytest_bdd.parser import FeatureParser

from tests._repo import REPO_ROOT

FEATURES: Final[pathlib.Path] = REPO_ROOT / "e2e" / "suite" / "features"
STEPS: Final[pathlib.Path] = REPO_ROOT / "e2e" / "suite" / "steps"
BINDING: Final[pathlib.Path] = REPO_ROOT / "e2e" / "suite" / "test_scenarios.py"

#: The steps package's own initialiser. Not a step module -- the binding module
#: star-imports each concern module by name and never this -- which is exactly
#: why a step defined here would register nowhere and fail as unbound.
STEPS_INITIALISER: Final[pathlib.Path] = STEPS / "__init__.py"

#: The decorators that make a function a step definition.
STEP_DECORATORS: Final[frozenset[str]] = frozenset({"given", "when", "then", "step"})

#: Wire language a `.feature` file may not contain, comments included -- a
#: comment is read by the same person the rule exists for.
#:
#: Bare status codes are deliberately absent: `422` and `19 cases` are the same
#: token to a regular expression, and a rule that fires on "100 rows" is a rule
#: somebody switches off within a week. That one stays a review rule, stated in
#: spec/design/testing.md.
WIRE_IN_GHERKIN: Final[tuple[tuple[str, str], ...]] = (
    ("a URL", r"https?://"),
    ("an API path", r"/api\b|/guestbook-entries\b"),
    ("an HTTP verb", r"\b(?:GET|POST|PUT|PATCH|DELETE)\b"),
    ("a wire detail", r"\bjson\b|\bresponse body\b|\bstatus code\b"),
)

KNOWN_POSITIVE_GHERKIN: Final[str] = """
Feature: A feature that breaks every rule
  # see GET /api/entries and its response body at https://example.com

  Scenario: A duplicated title
    Given something

  Scenario: A duplicated title
    Given something
"""

#: A feature whose only scenario sets up state and then neither acts nor
#: asserts. Both shape checks below are pointed at it first.
KNOWN_POSITIVE_HOLLOW_GHERKIN: Final[str] = """
Feature: A feature whose scenario does nothing

  Scenario: All setup and no outcome
    Given something
    And something else
"""

KNOWN_POSITIVE_STEPS: Final[str] = '''
from pytest_bdd import parsers, then

__all__ = []

@then("the import should create {count:d} new cases")
def _unwrapped(count):
    """A pattern pytest-bdd will match literally, so it can never fire."""

@then(parsers.parse("the same text twice"))
def _first(): ...

@then(parsers.parse("the same text twice"))
def _second(): ...
'''


def _step_modules() -> list[pathlib.Path]:
    """The modules the binding module star-imports, which is where steps live.

    `__init__.py` is excluded on purpose and is **not** unchecked: it is not a
    step module, and treating it as one would demand that the binding module
    star-import the package. What it must not do instead -- define a step -- is
    `test_the_steps_package_initialiser_defines_no_steps`.
    """
    return sorted(path for path in STEPS.glob("*.py") if path.name != "__init__.py")


#: A scenario heading, of either kind.
_SCENARIO_TITLE: Final = r"^\s*Scenario(?: Outline)?:\s*(.+)$"

#: A placeholder in a `Scenario Outline` step: `<size>`.
_PLACEHOLDER: Final = re.compile(r"<([^<>]+)>")


def _first_example_row(scenario: object) -> dict[str, str]:
    """One row of a scenario's Examples, or nothing if it has none.

    Any row will do: the check below asks whether a step *resolves*, and every
    row of an outline substitutes into the same pattern. Taking the first keeps
    the detector reading one step per template rather than one per row.
    """
    tables = list(getattr(scenario, "examples", []) or [])
    if not tables:
        return {}
    table = tables[0]
    headers = list(getattr(table, "example_params", []) or [])
    rows = list(getattr(table, "examples", []) or [])
    if not headers or not rows:
        return {}
    return dict(zip(headers, rows[0], strict=False))


def _feature_steps() -> list[tuple[str, str, str]]:
    """Every step of every scenario, as (feature file, keyword type, text).

    An outline's steps carry `<placeholders>`, which match no step definition as
    written -- pytest-bdd substitutes them per example row at run time. Left
    unsubstituted they would make every outline look like an unbound step, so the
    detector would either be red on correct Gherkin or, if somebody silenced it by
    skipping placeholder steps, blind to a genuinely unbound one.
    """
    steps = []
    for path in sorted(FEATURES.glob("*.feature")):
        feature = FeatureParser(str(FEATURES), path.name).parse()
        for scenario in feature.scenarios.values():
            row = _first_example_row(scenario)

            def substitute(match: re.Match[str], row: dict[str, str] = row) -> str:
                # Bound as a default rather than captured: the lambda this replaces
                # read the loop variable, which is the shape of a real bug even
                # where -- as here -- `sub` calls it before the next iteration.
                return row.get(match.group(1), match.group(0))

            for step in scenario.steps:
                steps.append((path.name, step.type, _PLACEHOLDER.sub(substitute, step.name)))
    return steps


def _scenarios_without(source_dir: pathlib.Path, filename: str, keyword: str) -> list[str]:
    """The scenarios in one feature file that have no step of `keyword` type."""
    feature = FeatureParser(str(source_dir), filename).parse()
    return [
        f"{filename}: {name}"
        for name, scenario in feature.scenarios.items()
        if not any(step.type == keyword for step in scenario.steps)
    ]


def _scenarios_missing(keyword: str, tmp_path: pathlib.Path) -> list[str]:
    """Every scenario in the real suite with no step of `keyword` type.

    The known positive is parsed from a file rather than a string because
    pytest-bdd's `FeatureParser` takes a directory and a name, not source -- so
    proving the detector can see a hollow scenario means writing one out.
    """
    hollow = tmp_path / "hollow.feature"
    hollow.write_text(KNOWN_POSITIVE_HOLLOW_GHERKIN, encoding="utf-8")
    assert _scenarios_without(tmp_path, hollow.name, keyword), (
        f"the detector for a missing `{keyword}` finds nothing in a scenario that has "
        "only `Given` steps, so a passing result below would mean nothing"
    )

    features = sorted(FEATURES.glob("*.feature"))
    assert features, f"no feature files under {FEATURES} -- has the layout moved?"
    return [
        entry for path in features for entry in _scenarios_without(FEATURES, path.name, keyword)
    ]


def _definitions() -> list[Any]:
    """Every registered step definition, read the way pytest-bdd reads them.

    A pytest-bdd decorator does not return a marker -- it writes a fixture into
    its defining module's globals and hangs a `StepFunctionContext` off it. That
    context carries the parser and the keyword type, which is exactly what the
    runner consults, so reading it here cannot drift from what actually happens.
    """
    contexts = []
    for path in _step_modules():
        module = importlib.import_module(f"e2e.suite.steps.{path.stem}")
        contexts += [
            value._pytest_bdd_step_context
            for value in vars(module).values()
            if hasattr(value, "_pytest_bdd_step_context")
        ]
    return contexts


def _decorator_patterns(source: str, label: str) -> list[tuple[str, str]]:
    """Every step pattern in `source`, as (label:line, the literal text).

    Reads the string out of `parsers.parse("...")` or out of a bare
    `@then("...")`, and reports which of the two it was by prefixing the
    unwrapped ones -- that distinction is the subject of one of the tests below.
    """
    patterns = []
    for node in ast.walk(ast.parse(source, filename=label)):
        if not isinstance(node, ast.FunctionDef):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call) or not decorator.args:
                continue
            name = getattr(decorator.func, "attr", None) or getattr(decorator.func, "id", None)
            if name not in STEP_DECORATORS:
                continue
            argument = decorator.args[0]
            if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
                patterns.append((f"{label}:{decorator.lineno}", f"BARE {argument.value}"))
            elif isinstance(argument, ast.Call) and argument.args:
                inner = argument.args[0]
                if isinstance(inner, ast.Constant) and isinstance(inner.value, str):
                    patterns.append((f"{label}:{decorator.lineno}", inner.value))
    return patterns


def test_every_step_of_every_scenario_resolves_to_a_definition() -> None:
    """The replacement for `behave --dry-run`.

    Unbound steps used to be caught before the application was even started.
    `pytest --generate-missing` prints them and exits 0 regardless, so this is
    the gate instead -- and it is a better one, because it needs no application
    and therefore runs on every platform and in `check.sh --fast`.
    """
    steps = _feature_steps()
    assert steps, f"no steps found under {FEATURES} -- has the layout moved?"

    definitions = _definitions()
    assert definitions, f"no step definitions found under {STEPS} -- has the layout moved?"

    unbound = [
        f'{filename}: {step_type.capitalize()} "{text}"'
        for filename, step_type, text in steps
        if not any(
            context.type in (None, step_type) and context.parser.is_matching(text)
            for context in definitions
        )
    ]

    assert unbound == [], (
        "these steps resolve to no definition, so the scenarios using them fail at run "
        "time rather than here. A pattern containing `{...}` must be wrapped in "
        f"`parsers.parse(...)`; a bare string is matched literally: {unbound}"
    )


def test_no_step_line_matches_more_than_one_definition() -> None:
    """The gate `test_no_step_text_is_defined_twice` cannot be.

    That one compares decorator *literals*, so it catches the same text written
    twice and nothing else. What it cannot see is two **different** patterns that
    both match one line -- and `parsers.parse` makes those easy to write by
    accident, because `{name}` matches anything at all, quotation marks included.
    So `an entry signed "{signature}" is added by "{author}"` also matches
    `... is added by "qa" with the message "x"`, with `author` swallowing the tail.
    pytest-bdd then binds whichever definition it reached first, silently, and the
    scenario asserts against the wrong entry.

    This is the same question the runner asks, asked for every line: how many
    definitions match it? One is the only acceptable answer. Zero is the previous
    test's business; two or more is this one's.

    It is also the standing hazard, not a historical one. Every `When` that ends in
    a quoted placeholder is exposed, so the next step text that extends one of them
    -- `... is added by "qa" at "12:00"` -- would be swallowed exactly
    the same way. This fails when that is written rather than when a figure comes
    out wrong.
    """
    steps = _feature_steps()
    assert steps, f"no steps found under {FEATURES} -- has the layout moved?"

    definitions = _definitions()
    assert definitions, f"no step definitions found under {STEPS} -- has the layout moved?"

    ambiguous = []
    for filename, step_type, text in steps:
        matching = [
            context
            for context in definitions
            if context.type in (None, step_type) and context.parser.is_matching(text)
        ]
        if len(matching) > 1:
            named = ", ".join(sorted(context.parser.name for context in matching))
            ambiguous.append(f'{filename}: {step_type.capitalize()} "{text}" <- {named}')

    assert ambiguous == [], (
        "these lines are matched by more than one step definition, and pytest-bdd binds "
        "whichever it reaches first -- so the scenario runs a step it does not name. Give "
        "the newer pattern a distinguishing clause *before* its last placeholder rather "
        f"than after it: {ambiguous}"
    )


def test_every_scenario_asserts_something(tmp_path: pathlib.Path) -> None:
    """A scenario of nothing but `Given` asserts nothing and still reports green."""
    hollow = _scenarios_missing("then", tmp_path)

    assert hollow == [], f"these scenarios assert nothing: {hollow}"


def test_every_scenario_acts_on_the_application(tmp_path: pathlib.Path) -> None:
    """A `Then` with no `When` asserts against a response nothing in it produced.

    This half used to be missing while the test claiming to cover it was called
    `..._has_at_least_one_when_or_then` and checked only `then`. It is not a
    naming nit: the runtime backstop is `ApiClient.last`, which refuses to answer
    when no request has been made -- and that backstop was itself disabled for a
    while, because `e2e/suite/conftest.py` asked its "is the world empty" question
    on the very client the scenario was handed. With `_last` already populated,
    `Then only 0 cases should be returned` with no `When` read the fixture's own
    empty page and passed. The fixture now probes on a throwaway client, and this
    is the static half of the same guarantee -- it fails at collection time,
    without an application.
    """
    inert = _scenarios_missing("when", tmp_path)

    assert inert == [], (
        "these scenarios never act on the application, so every `Then` in them asserts "
        f"about a response no step of theirs produced: {inert}"
    )


def test_no_feature_file_names_a_url_a_verb_or_a_wire_detail() -> None:
    """`.feature` files are the artifact a non-programmer reads and reviews.

    Every technical detail -- which endpoint, which field, which status code
    means what -- belongs one level below, in `e2e/suite/steps/`.
    """
    for described, pattern in WIRE_IN_GHERKIN:
        assert re.search(pattern, KNOWN_POSITIVE_GHERKIN), (
            f"the detector for {described} finds nothing in a feature that contains one, "
            "so a passing result below would mean nothing"
        )

    features = sorted(FEATURES.glob("*.feature"))
    assert features, f"no feature files under {FEATURES} -- has the layout moved?"

    offenders: dict[str, list[str]] = {}
    for path in features:
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            for described, pattern in WIRE_IN_GHERKIN:
                if re.search(pattern, line):
                    offenders.setdefault(path.name, []).append(
                        f"{number}: {described} -- {line.strip()}"
                    )

    assert offenders == {}, (
        "a `.feature` file is read and reviewed by somebody who knows what a fully paid "
        f"case is and does not know what a 422 is: {offenders}"
    )


def test_no_two_scenarios_share_a_name() -> None:
    """pytest-bdd keys scenarios by name, so a duplicate silently becomes one."""
    # `Scenario Outline:` counts too: it is one entry in `feature.scenarios`, the
    # same as a plain scenario, so a detector that only counted `Scenario:` read
    # every outline as a scenario that had vanished.
    titles = re.findall(_SCENARIO_TITLE, KNOWN_POSITIVE_GHERKIN, re.MULTILINE)
    assert len(titles) != len(set(titles)), (
        "the duplicate-title detector sees no duplicate in a source that has one"
    )

    offenders: dict[str, list[str]] = {}
    for path in sorted(FEATURES.glob("*.feature")):
        found = re.findall(_SCENARIO_TITLE, path.read_text(encoding="utf-8"), re.MULTILINE)
        parsed = FeatureParser(str(FEATURES), path.name).parse()
        if len(found) != len(parsed.scenarios):
            repeated = sorted({title for title in found if found.count(title) > 1})
            offenders[path.name] = repeated

    assert offenders == {}, (
        "two scenarios sharing a title collapse into one, so the suite runs fewer than "
        f"it reports: {offenders}"
    )


def test_no_step_text_is_defined_twice() -> None:
    """behave raised `AmbiguousStep`; pytest-bdd lets the last import win.

    Honest limit, and it is in the docstring rather than only in a review: this
    compares decorator *literals*, so it catches identical text and does not
    catch two genuinely different patterns that both match one line. `parse`
    matches literal frames case-insensitively, so `entry "{id}" should ...` and
    `Entry "{id}" should ...` would both match and neither is caught here.
    Three domain-scoped modules with disjoint vocabularies make that unlikely,
    not impossible.
    """
    positive = _decorator_patterns(KNOWN_POSITIVE_STEPS, "<known positive>")
    texts = [text for _, text in positive]
    assert len(texts) != len(set(texts)), (
        "the duplicate-pattern detector finds no duplicate in a source that has one"
    )

    seen: dict[str, list[str]] = {}
    for path in _step_modules():
        label = path.relative_to(REPO_ROOT).as_posix()
        for where, text in _decorator_patterns(path.read_text(encoding="utf-8"), label):
            seen.setdefault(text, []).append(where)

    offenders = {text: places for text, places in seen.items() if len(places) > 1}
    assert offenders == {}, (
        "the same step text is defined more than once. pytest-bdd registers both and the "
        f"last wildcard import wins, silently, so one of them never runs: {offenders}"
    )


def test_every_step_module_is_imported_by_the_binding_module() -> None:
    """A step module nobody star-imports registers nothing at all."""
    source = BINDING.read_text(encoding="utf-8")
    imported = {
        node.module.rsplit(".", 1)[-1]
        for node in ast.walk(ast.parse(source, filename=str(BINDING)))
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }

    missing = sorted(path.stem for path in _step_modules() if path.stem not in imported)
    assert missing == [], (
        f"these step modules are not imported by {BINDING.name}, so their steps are never "
        f"registered and every scenario using them fails as unbound: {missing}"
    )


def test_no_step_module_defines_dunder_all() -> None:
    """`__all__` makes `import *` skip everything pytest-bdd needs.

    The decorators write fixtures into module globals under generated
    `pytestbdd_stepdef_*` names. `__all__` -- even a correct-looking one listing
    the step functions -- excludes those, so the wildcard import in the binding
    module brings across nothing and every scenario using that module fails as
    unbound.
    """
    assert "__all__" in KNOWN_POSITIVE_STEPS, "the known positive no longer defines __all__"

    offenders = []
    for path in _step_modules():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.stmt):
                continue
            targets = node.targets if isinstance(node, ast.Assign) else []
            if any(getattr(target, "id", None) == "__all__" for target in targets):
                offenders.append(f"{path.name}:{node.lineno}")

    assert offenders == [], (
        "a step module may not define __all__: the step definitions are fixtures written "
        "into module globals under generated names, and __all__ excludes them from "
        f"`import *`, so every scenario using that module fails as unbound: {offenders}"
    )


def test_the_steps_package_initialiser_defines_no_steps() -> None:
    """The one file under `steps/` that is not a step module, and looks like one.

    `e2e/suite/test_scenarios.py` star-imports the three concern modules **by
    name**; nothing imports the package itself. So a `@then(...)` written in
    `steps/__init__.py` registers nowhere -- and because the other checks here
    read only the concern modules, nothing said so. The scenario using it would
    fail as unbound at run time, in the one place this file exists to precede.

    Deliberately narrower than "the initialiser must be empty": a docstring
    explaining the split is the reason the file exists, and all four initialisers
    in `e2e/` are exactly that.
    """
    assert _decorator_patterns(KNOWN_POSITIVE_STEPS, "<known positive>"), (
        "the step-definition detector finds nothing in a source full of them, so a "
        "passing result below would mean nothing"
    )
    assert STEPS_INITIALISER.is_file(), (
        f"{STEPS_INITIALISER} does not exist, so this check applies to nothing. It is "
        "named directly rather than globbed precisely so its disappearance fails here"
    )

    defined = _decorator_patterns(
        STEPS_INITIALISER.read_text(encoding="utf-8"),
        STEPS_INITIALISER.relative_to(REPO_ROOT).as_posix(),
    )

    assert defined == [], (
        "a step defined in the steps package's `__init__.py` is registered nowhere: the "
        "binding module star-imports the concern modules by name and never the package, "
        f"so every scenario using it fails as unbound. Move these into the module for "
        f"their business concern: {defined}"
    )

"""Every scenario written in Gherkin is a scenario the runner collected.

The failure this exists for is silent by construction. A `.feature` file can declare
twenty-one scenarios while pytest-bdd collects nineteen -- a renamed step, a scenario
under a `Rule:` the binding does not reach, a file that stopped being discovered
because its directory lost its `__init__` -- and every report downstream says the
suite passed. Nobody counts, because counting by hand is exactly the job nobody does
twice.

So the census is a subtraction: what the feature files declare, minus what the
runner collected, read off the junit `test.sh e2e` has just written. `test.sh e2e`
already refuses a zero-collection run, which catches the catastrophic case; this
catches the case that matters more, where almost everything ran.

Called by `scripts/test.sh e2e` AFTER the report is written, and never with a
`--junitxml` of its own; `tests/tooling/test_suite_census_wiring.py` holds that
order. Stdlib only, no application import: it runs on the interpreter the scripts
run on.

Exit: 0 the counts agree, or there is nothing to count and it says so; 1 they do not,
or the report the run was meant to leave is not there.
"""

import argparse
import pathlib
import re
import sys
import xml.etree.ElementTree as ElementTree
from collections import Counter
from typing import Final

REPO_ROOT: Final[pathlib.Path] = pathlib.Path(__file__).resolve().parent.parent
FEATURES: Final[pathlib.Path] = REPO_ROOT / "e2e" / "suite" / "features"
JUNIT: Final[pathlib.Path] = REPO_ROOT / "e2e" / "reports" / "junit.xml"

_SCENARIO: Final = re.compile(r"^\s*Scenario(?: Outline)?:\s*(?P<name>.+?)\s*$")
_EXAMPLES_ROW: Final = re.compile(r"^\s*\|")

#: The module pytest-bdd binds every feature to, and so the `classname` every
#: scenario reports under. `e2e/ui/` reports under its own -- which is the whole
#: reason the two suites can be told apart inside one report.
BDD_CLASSNAME: Final = "e2e.suite.test_scenarios"

#: What `e2e/ui/` reports under. Only a report whose every case carries this prefix
#: is a `--only-ui` run, and only such a report has nothing for the subtraction to
#: answer.
UI_PREFIX: Final = "e2e.ui."


def declared(features: pathlib.Path = FEATURES) -> dict[str, list[str]]:
    """Scenario names per feature file, in declaration order."""
    found: dict[str, list[str]] = {}
    for path in sorted(features.glob("*.feature")):
        found[path.name] = [
            match.group("name")
            for line in path.read_text(encoding="utf-8").splitlines()
            if (match := _SCENARIO.match(line))
        ]
    return found


def expanded(features: pathlib.Path = FEATURES) -> dict[str, int]:
    """How many test items each feature file should produce.

    A `Scenario` is one item. A `Scenario Outline` is one item **per Examples data
    row**, because pytest-bdd expands it before collection -- so counting headings
    against collected items compares two different things, and the gap is not small:
    this suite declares 21 headings and collects 30 items. Rows are counted after the
    header row of each Examples block, and an outline may carry more than one block.
    """
    found: dict[str, int] = {}
    for path in sorted(features.glob("*.feature")):
        items = 0
        in_outline = False
        in_examples = False
        seen_header = False
        for line in path.read_text(encoding="utf-8").splitlines():
            if _SCENARIO.match(line):
                in_outline = "Outline" in line.split(":", 1)[0]
                in_examples = False
                items += 0 if in_outline else 1
            elif in_outline and line.strip().startswith("Examples:"):
                in_examples = True
                seen_header = False
            elif in_examples and _EXAMPLES_ROW.match(line):
                items += 0 if not seen_header else 1
                seen_header = True
            elif in_examples and line.strip():
                in_examples = False
        found[path.name] = items
    return found


def duplicated(features: pathlib.Path = FEATURES) -> dict[str, list[str]]:
    """Scenario names a feature file declares more than once -- they make every later
    count ambiguous, including this one."""
    out: dict[str, list[str]] = {}
    for name, scenarios in declared(features).items():
        repeated = sorted(title for title, count in Counter(scenarios).items() if count > 1)
        if repeated:
            out[name] = repeated
    return out


def collected(junit: pathlib.Path) -> tuple[int, list[str]]:
    """The BDD cases the report holds, and every classname present."""
    root = ElementTree.parse(junit).getroot()
    cases = list(root.iter("testcase"))
    present = sorted({str(case.get("classname")) for case in cases})
    return sum(1 for case in cases if case.get("classname") == BDD_CLASSNAME), present


def census(features: pathlib.Path = FEATURES, junit: pathlib.Path = JUNIT) -> tuple[int, str]:
    """The verdict and the sentence that explains it."""
    files = list(features.glob("*.feature"))
    if not files:
        return 0, f"nothing to count: no .feature files under {features}"
    twice = duplicated(features)
    if twice:
        named = "; ".join(f"{name}: {', '.join(titles)}" for name, titles in twice.items())
        return 1, f"a scenario name is declared more than once ({named}), so no count is meaningful"
    if not junit.is_file():
        return 1, f"no report at {junit}: the run this census follows left nothing to count"
    newest = max(path.stat().st_mtime for path in files)
    if newest > junit.stat().st_mtime:
        return 1, f"{junit} predates a feature file, so it describes a different suite"
    bdd, present = collected(junit)
    if present and all(name.startswith(UI_PREFIX) for name in present):
        return (
            0,
            "every case in this report is an e2e/ui case -- a --only-ui run wrote it; nothing to count",
        )
    if not bdd:
        return 1, (
            f"the report holds {present} and not one {BDD_CLASSNAME} case: either the module "
            "pytest-bdd binds the features to was renamed -- then correct BDD_CLASSNAME here -- "
            "or the Gherkin suite stopped being collected, which is the silence this census exists to break"
        )
    expected = sum(expanded(features).values())
    if bdd != expected:
        return 1, (
            f"Gherkin declares {expected} test items and the runner collected {bdd}: the "
            "difference is scenarios that exist in a file a colleague reads and run nowhere"
        )
    return 0, f"{bdd} scenario items declared, {bdd} collected"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--features", type=pathlib.Path, default=FEATURES)
    parser.add_argument("--junit", type=pathlib.Path, default=JUNIT)
    args = parser.parse_args(argv)
    code, sentence = census(args.features, args.junit)
    print(f"scenario census: {sentence}", file=sys.stderr if code else sys.stdout)
    return code


if __name__ == "__main__":
    raise SystemExit(main())

"""`scripts/scenario_census.py`: what the feature files declare, minus what ran.

Proved on fabricated positives before it is trusted on the real suite: a counter that
finds nothing is indistinguishable from a broken one until it is handed a file built
to trip it. No database, no Docker, no application import.
"""

import pathlib

import scenario_census

_FEATURE: str = (
    "Feature: x\n\n  Scenario: the first\n    Given a\n\n"
    "  Scenario Outline: the second\n    Given <v>\n\n    Examples:\n"
    "      | v |\n      | 1 |\n      | 2 |\n"
)


def _junit(path: pathlib.Path, cases: list[tuple[str, str]]) -> pathlib.Path:
    body = "".join(f'<testcase classname="{c}" name="{n}"/>' for c, n in cases)
    path.write_text(f'<testsuites><testsuite name="s">{body}</testsuite></testsuites>')
    return path


def _features(tmp_path: pathlib.Path, text: str = _FEATURE) -> pathlib.Path:
    features = tmp_path / "features"
    features.mkdir(parents=True)
    (features / "x.feature").write_text(text, encoding="utf-8")
    return features


def test_the_scenario_counter_finds_scenarios_and_expands_outlines(tmp_path: pathlib.Path) -> None:
    features = _features(tmp_path)
    assert scenario_census.declared(features) == {"x.feature": ["the first", "the second"]}
    assert scenario_census.expanded(features) == {"x.feature": 3}, "one plain + two example rows"


def test_an_examples_row_is_not_a_scenario_declaration(tmp_path: pathlib.Path) -> None:
    features = _features(tmp_path, "Feature: x\n\n  Scenario: one\n    Given a\n    | column |\n")
    assert scenario_census.declared(features) == {"x.feature": ["one"]}
    assert scenario_census.expanded(features) == {"x.feature": 1}


def test_matching_counts_pass_and_a_missing_scenario_fails(tmp_path: pathlib.Path) -> None:
    features = _features(tmp_path)
    bdd = scenario_census.BDD_CLASSNAME
    full = _junit(
        tmp_path / "full.xml", [(bdd, "a"), (bdd, "b"), (bdd, "c"), ("e2e.ui.test_x", "d")]
    )
    code, sentence = scenario_census.census(features, full)
    assert code == 0, sentence
    short = _junit(tmp_path / "short.xml", [(bdd, "a"), (bdd, "b")])
    code, sentence = scenario_census.census(features, short)
    assert code == 1 and "declares 3" in sentence and "collected 2" in sentence


def test_a_ui_only_report_has_nothing_to_count_and_a_bdd_less_one_is_a_failure(
    tmp_path: pathlib.Path,
) -> None:
    features = _features(tmp_path)
    ui_only = _junit(tmp_path / "ui.xml", [("e2e.ui.test_x", "d")])
    assert scenario_census.census(features, ui_only)[0] == 0
    renamed = _junit(tmp_path / "renamed.xml", [("e2e.suite.other", "a"), ("e2e.ui.test_x", "d")])
    code, sentence = scenario_census.census(features, renamed)
    assert code == 1 and scenario_census.BDD_CLASSNAME in sentence


def test_a_missing_report_and_a_duplicate_name_are_failures(tmp_path: pathlib.Path) -> None:
    features = _features(tmp_path)
    code, sentence = scenario_census.census(features, tmp_path / "absent.xml")
    assert code == 1 and "no report" in sentence
    twice = _features(
        tmp_path / "twice",
        "Feature: x\n\n  Scenario: same\n    Given a\n\n  Scenario: same\n    Given b\n",
    )
    junit = _junit(tmp_path / "twice.xml", [(scenario_census.BDD_CLASSNAME, "same")] * 2)
    code, sentence = scenario_census.census(twice, junit)
    assert code == 1 and "more than once" in sentence


def test_no_feature_files_is_nothing_to_count(tmp_path: pathlib.Path) -> None:
    empty = tmp_path / "none"
    empty.mkdir()
    assert scenario_census.census(empty, tmp_path / "absent.xml") == (
        0,
        f"nothing to count: no .feature files under {empty}",
    )


def test_the_real_suite_declares_scenarios_and_names_none_twice() -> None:
    total = sum(len(names) for names in scenario_census.declared().values())
    assert total > 0, "no scenario is declared in e2e/suite/features/"
    assert scenario_census.duplicated() == {}

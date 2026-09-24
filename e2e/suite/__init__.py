"""This application's scenarios, and the vocabulary they are written in.

`features/` is the artifact: the scenarios -- some of them `Scenario Outline`
with an Examples table -- written for somebody on the
collections desk who knows what a fully paid case is and does not know what a
422 is. No URL, no JSON field name and no HTTP status code appears in a
`.feature` file, and `tests/fitness/test_e2e_scenarios.py` fails the build if one does.

`steps/` is where all of that lives instead -- one module per business concern,
matching the modules under `app/services/`, so a reader who knows
the backend already knows which file to open. They are the only modules in the
repository that know which endpoint answers what.

Everything mechanical -- making the request, reading a list answer, phrasing a
failure, emptying the database -- comes from `e2e.harness`. The dependency runs
this way and never the other.
"""

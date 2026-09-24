# Scenarios — the guestbook, the template's worked example

> Retrospective. These are not seeds waiting to be turned into a `.feature` file: the file
> exists, at `e2e/suite/features/guestbook.feature`, and every scenario below is already
> written there and tagged with the requirement it proves. This document records the
> mapping so the coverage table has a source.

## Coverage

| Requirement | Scenarios | Unhappy path? |
|---|---|---|
| R-1 | Leaving the first entry; Characters outside ASCII survive a write and a read | no |
| R-2 | An entry with no signature is not saved; An entry with no message is not saved; An entry at the boundary size is accepted; An entry breaking a rule is not saved | yes |
| R-3 | The list shows the newest entry at the top; The guestbook shows everything the guests left; The guestbook can be read oldest first | no |
| R-4 | Amending an entry's message; An amendment does not change the date the entry was written; Amending an entry that is not there | yes |
| R-5 | Deleting an entry; Deleting the same entry twice; Deleting one entry leaves the rest | yes |
| R-6 | A guest finds an entry by its signature; A guest finds an entry by its message, not only by its signature; Searching ignores case | no |
| R-7 | A search that finds nothing does not empty the guestbook; A piece of the guestbook says how many entries there are in total; Viewing the guestbook a piece at a time shows every entry exactly once | yes |

Twenty-one scenarios over seven requirements — but twenty-one is the count of *declarations*,
and it is not the number of cases that run. Nineteen are plain `Scenario:`; two are
`Scenario Outline:`, carrying four and seven Examples rows between them, so pytest-bdd executes
**thirty** cases. Both outlines belong to `R-2`, whose four named scenarios are thirteen
executed cases — which is why the refusal rules are the best-covered thing here and the table
above understates it.

Four of the seven requirements carry an unhappy path, and the three that do not are the ones
whose failure mode is an ordering defect rather than a refusal — those are proved by comparing
two reads, not by provoking an error.

## Test data

The scenarios that need a corpus take it from `golden-set/fixtures/` rather than inventing
values, so the boundary cases are the same three files the backend suite reads:

- `golden-set/fixtures/entries-ordinary.json` — the everyday entries: characters outside
  ASCII, a message with line breaks, a short one beside a long one, and a single-character
  pair.
- `golden-set/fixtures/entries-boundary.json` — a signature at exactly 80 characters, a
  message at exactly 1000, a one-character pair, and a padded value that reaches the maximum
  only after trimming. This is the file that proves `R-2.2`.
- `golden-set/fixtures/entries-refused.json` — every value the system has to refuse: the
  empty cases, the whitespace-only cases that separate "empty" from "short", and one value a
  single character past each of the two maxima.

The corpus has a second half, `golden-set/seed/`, and no scenario here reads it: it is what a
freshly created environment opens with, and a fitness test refuses a suite that asserts about
it. `tests/_golden_set.py` is the one place that decides where either half lies; nothing else
names the directory.

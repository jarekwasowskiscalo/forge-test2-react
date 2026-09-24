# `golden-set/` — the reference corpus

The only home for committed data this project ships, cut in two by **what the data is for**:

| Half | What it is | Read by | Lifetime |
|---|---|---|---|
| [`fixtures/`](fixtures/) | what the suites read instead of inventing | pytest, the black box, and `seed_golden_set.py` under `--boundary` | wiped before every scenario |
| [`seed/`](seed/) | what a freshly created environment opens with | `scripts/seed_golden_set.py` | the life of the environment |

**The halves were one directory, and the seam leaked.** The seeder posted
`entries-ordinary.json`, on the argument that a reviewer should look at the very data the
assertions are written about. The argument did not survive contact: an entry added to make a
preview look richer weakened a paging test that counted them, and a boundary case added to
prove a rule put an eighty-character signature on the screen. One corpus cannot be sized by
what a test needs to prove **and** by what a person needs to see.

What the halves keep in common is the properties that make data worth having at all —
characters outside ASCII, a message with line breaks — and each now owes them **in its own
right** rather than inheriting them. `tests/fitness/test_golden_set.py` holds all of it.

## `fixtures/` — what the suites read

Four files, each with one story, each saying in its own header what it proves:

| File | Story |
|---|---|
| `entries-ordinary.json` | ordinary entries in **writing** order — characters outside ASCII, a multi-line message, single-character entries |
| `entries-boundary.json` | values **exactly** on the bound; every one must be accepted |
| `entries-refused.json` | entries the rules refuse; each naming the mechanism that refuses it |
| `text-measurement.json` | how a field is trimmed and how long it is — **cases, not entries**, and the one file both languages read |

**Three hold entries; the fourth holds cases.** An entry is a guest book entry and carries
`author` and `message`. A case carries an input, the field it is about, the verdict the rule
gives it and the length it has afterwards — so the rules about entries do not reach it and it
owes rules of its own instead (§ Rules only `text-measurement.json` obeys).

**By name or by sentence, never by position.** A test reaching for `entries[2]` starts
asserting about a different case the moment somebody inserts one above it — and does so
silently.

**The sentence exists so that a `.feature` can name the case.** A scenario is read by somebody
who does not write code, so it says `the signature is all spaces` rather than
`author_whitespace_only`. The sentence lives in the corpus rather than in a mapping beside the
steps — one list instead of two that have to agree.

## `seed/` — what a new environment opens with

One file: `entries-welcome.json`. A preview with an empty guest book is a preview of a screen
nobody can judge, so `scripts/seed.sh` fills one — through the application's own HTTP API, so
the entries arrive the way a guest's entry arrives, or do not arrive at all.

**Nothing asserts about it, and a fitness test enforces that.** A suite that reaches for this
half re-couples the two: the seed corpus could then no longer change for the reason it exists
— to make a screen worth judging — without reddening a test.
`test_no_suite_reads_the_seed_corpus` refuses it, and names the offender.

The one exception is the seeder's own case in `tests/tooling/`, which derives its expectation
**from** the corpus rather than writing it out. That asserts about the seeder, not the data:
adding a welcome entry leaves it green.

## How it is read

**Never by building a path.** `tests/_golden_set.py` is the only place that decides where
either half lies; the black box reaches the fixture half through `e2e/suite/golden_set.py`,
and that is the **only** crossing from `e2e/` into first-party code this project allows. There
were once two locators, because the e2e suite ran in its own environment — and they diverged
in their return type and in their exception type before anybody noticed. **A second locator
for the second half would be that defect returning**, which is why the split is two
directories and not two modules.

```python
from tests._golden_set import BOUNDARY, ORDINARY, REFUSED, case, described, entries_of

for entry in entries_of(ORDINARY):      # all of them, in file order
    ...
case(BOUNDARY, "author_at_maximum")      # one case, by name
described(REFUSED, "the signature is all spaces")   # one case, by its sentence
```

## Rules both halves obey

- **One file per story it shows.** A file showing five things at once does not say which of
  them broke.
- **Every file carries a `story` and a `demonstrates`** — what it proves, in its own words. A
  file whose purpose lives only in the test that reads it is a file later copied for the wrong
  reason.
- **An entry that claims to pass really passes.** Checked rather than declared: a fixture that
  lies about itself turns a helper that fills a book into a refusal test nobody wrote, and a
  seed entry that lies leaves a preview empty with the reason in a log nobody reads.
- **No data that looks like somebody's.** The corpus is committed, and a run's artefacts
  (JUnit, logs) can quote its values — constitution, article XI. Not "fictional" but
  **unambiguously artificial**: a plausible IBAN in a repository looks like a real account to
  anybody who finds it later.
- **Both halves carry characters outside ASCII, and a message with line breaks.** That is what
  proves bytes survive the round trip through the database, the contract and the browser — a
  property of the encoding rather than of any one language, which is why the rule is
  "non-ASCII" and not "a particular alphabet".
- **The frontend reads neither half, with one named exception.** Component fixtures are
  synthetic and written on the spot, and `tests/fitness/test_golden_set.py` holds
  `frontend/src/` to it — the guard scans for the corpus file names and for the word
  `golden-set` itself, so even a path in a comment trips it.

  The exception is `text-measurement.json`, read by
  `frontend/src/contexts/guestbook/lib/entryText.test.ts` and by no other module in that
  tree. It is the opposite case rather than a hole in this one: every other file here is
  sized by what the SERVER must prove, which is why a component asserting against one
  acquires a dependency it cannot see the reasons for. That file is sized by what the two
  sides must AGREE about, and a claim about agreement cannot be checked from one side.
  Giving the browser its own copy would be the very defect the file exists to end, wearing a
  second name: two lists that have to stay equal, and nothing making them.
- **A file whose entries are a SEQUENCE carries no `case` and no `description`.** That is
  `entries-ordinary.json` and the whole of `seed/` — filed here rather than under one half,
  because it follows from what the file is and not from which directory it sits in. Those
  keys invite a test to reach for an entry by name and stop caring about the order the file
  exists to carry.

## Rules only `fixtures/` obeys

- **Bounds are computed from the constants, not transcribed.** `entries-boundary.json` was
  produced from `AUTHOR_MAX_LENGTH` and `MESSAGE_MAX_LENGTH`;
  `tests/fitness/test_golden_set.py` checks that agreement on every run. Moving a rule is to
  redden the corpus rather than invalidate it silently.
- **Crossing a bound is by ONE CODE POINT.** A value an order of magnitude too large passes a
  `>` written as `>=` — and that is exactly the defect a boundary test exists for. The unit
  is named rather than left as "character" because the two sides of the contract once meant
  different things by the word: `app/platform/schemas/text.py` says which one won and why.
- **Hostile input does not belong here.** The boundary runs where what a guest could really
  send ends: a signature of nothing but spaces **belongs**, because that happens; bytes built
  to break a parser do not. Those live in the test's code, beside the assertion that explains
  them.

  `text-measurement.json` sits on the near side of that line and it is worth saying why,
  because it looks like the far side. A byte order mark is not an attack — it arrives at the
  front of text pasted out of an ordinary editor, and the guest who pasted it did not type
  it. Neither are a decomposed `é`, which is what a Mac keyboard emits, or a family emoji,
  which is on the picker. What the file carries is not input built to break anything: it is
  the ordinary input that happened to fall where two implementations disagreed. A corpus
  that DEFINES which code points are whitespace has to contain them, or it defines nothing.
- **If your feature has a "newer than the previous one" rule,** give the file a day strictly
  later than the last day of its story. A reused day makes the file unimportable, and a
  scenario then breaks on a rule it was not testing.

## Rules only `text-measurement.json` obeys

- **Every input is an escape, never a raw byte.** The other files must carry characters above
  U+007F, because what they prove is that bytes survive the round trip. This one proves the
  opposite kind of thing — what a rule does to particular code points — so the code points
  have to arrive unaltered. `.gitattributes` already rewrites line endings in this
  repository, and a case whose input were a raw U+2028 would be data one checkout setting
  could change. The whole file is ASCII on disk and a fitness test holds it there.
- **A case states a length exactly when it is accepted.** "Accepted" is true of eighty emoji
  whether they are counted as eighty code points or as anything else that fits; the LENGTH is
  what names the unit. On a refusal there is no length to state, and a number would be read
  as one.
- **Both readers assert the same thing.** `tests/unit/test_entry_text_rules.py` and
  `frontend/src/contexts/guestbook/lib/entryText.test.ts` read these bytes and assert the same
  verdicts and the same lengths. Neither may assert something the other does not — a case only
  one side checks is a case that proves nothing about agreement.
- **The file carries its own known positives.** A case must exist whose length in code points
  differs from its length in UTF-16 code units, and a case the written whitespace set and
  `str.strip()` disagree about. Without them the corpus cannot see the defect it was written
  for, and a detector that has stopped detecting passes everything.

## Rules only `seed/` obeys

- **Nothing near a bound.** A signature padded to the maximum proves a limit beautifully and
  makes a screen nobody can read. Boundary values are the other half's job, and
  `scripts/seed.sh --boundary` is how a person asks for them on purpose.
- **Enough entries to look like a list.** One entry proves the screen renders; it does not
  show the spacing, the ordering, or the ragged edge of messages of different lengths — which
  is most of what a reviewer opens a preview for.

## When you add a file

1. **Decide which half.** Will something assert about it, or will somebody look at it? A file
   that answers "both" is the state this split ended — write two.
2. Name it `<story>.json`, lower case with hyphens. Names are unique across both halves.
3. Add a constant in `tests/_golden_set.py` and put it in `FIXTURE_FILES` or `SEED_FILES` — a
   file its locator cannot hand out shows nobody anything, and `test_golden_set.py` refuses
   that.
4. Give every fixture case a `case` **and** a `description`, if a scenario is to name it.
5. **Decide whether it holds entries or cases**, and say so in the key: `entries` for guest
   book entries, `cases` for inputs to a rule. The fitness module sweeps the two with
   different rules, and a file under the wrong key is held to rules that do not fit it while
   the ones that do are skipped.

Placement and naming rules: `spec/design/conventions.md`.
Which suites read the fixture half and why those: `spec/design/testing.md`.
What a new environment starts with, and the two refusals that make it safe:
`spec/design/architecture.md` § Environments.

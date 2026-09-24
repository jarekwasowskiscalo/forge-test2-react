---
date: 2026-09-17
branch: fix/one-semantics-of-length-and-whitespace
pr: 54
kind: fix
---

# Measure and trim text the same way on both sides of the contract

Closes GitHub issue #28 (audit finding A33). Taken on the trunk rather than through
`/forge:sdd`, by decision, so there is no change record and this entry is the whole record.

## What changed

**The rule, written once per language.** `app/platform/schemas/text.py` is new: the 30 code
points that are trimmed, `normalize()` (NFC, then those 30 off either end), `length()` (code
points) and `NormalizedText`, a Pydantic `BeforeValidator`. It sits in `app/platform/` for the
reason `refusals.py` does — the unit a bound counts in is a fact about every text field this API
accepts, not about guest book entries. `frontend/src/contexts/guestbook/lib/entryText.ts` is its
counterpart: the same 30 code points as numbers, `normalizeText`, `textLength`.

**Applied.** `app/contexts/guestbook/schemas/guestbook_entries.py` gains the `Author` and
`Message` annotated types and **loses `ConfigDict(str_strip_whitespace=True)` from both models**.
`routers/guestbook_entries.py` puts `NormalizedText` **ahead of** `Query(max_length=…)` on `q`.
`services/guestbook_entries.py` swaps `.strip()` for `normalize()`.
`frontend/src/contexts/guestbook/lib/guestbookEntry.ts` delegates to `entryText.ts`, measures with
`textLength`, and gains `QUERY_MAX_LENGTH` — the search bound had no copy in the browser at all.
`EntryComposer.tsx` and `EntryCard.tsx` lose all four `maxLength` attributes; the composer's
counter measures the trimmed, normalized message. `useEntryQueryParams.ts` normalizes the phrase
with the shared rule instead of `.trim()`.

**The corpus.** `golden-set/fixtures/text-measurement.json` is new — 41 cases, **cases and not
entries**, every input written as an escape so the file is ASCII on disk. It is read by
`tests/unit/test_entry_text_rules.py` and by
`frontend/src/contexts/guestbook/lib/entryText.test.ts`, which assert the same verdicts and the
same lengths against the same bytes. `tests/_golden_set.py` gains `TEXT_RULES` and `cases_of`.

**The rules the corpus owes, and the one exception it needed.**
`tests/fitness/test_golden_set.py` splits the entry rules from the case rules, gains eight rules
for the new file, and judges every bound by `normalize`/`length` instead of `str.strip()`/`len()`.
`test_the_frontend_reads_no_corpus_file` gains a `permitted` set of exactly one module — the same
shape `test_no_suite_reads_the_seed_corpus` beside it already uses. `golden-set/README.md`
carries the reasoning for all of it.

**Proof and documents.** New tests in `tests/integration/test_guestbook_entries_router.py` (the
phrase's ordering) and `test_guestbook_entries_service.py` (what actually reached the column).
Two new fixture cases in `entries-boundary.json` and `entries-refused.json` with their
`guestbook.feature` rows, and one new browser test in `e2e/ui/test_smoke.py`.
`contracts/invariants/guestbook.md` gains `D-04` and rises to version 2;
`contracts/openapi/guestbook.yaml` rises to 1.3.0. Edits to `spec/contexts/guestbook.md`,
`spec/design/api.md`, `spec/design/data-model.md`, `spec/design/testing.md`,
`spec/design/conventions.md` and `spec/design/ui/guestbook.md`. `.github/workflows/ci.yml` adds
`golden-set/` to the `frontend` routing filter.

## Why

The number 80 was written identically in four places and a fitness test held all four equal. The
units were not equal, and nothing could see it: `tests/fitness/test_length_constants.py` compares
a number with a number, so it passed throughout the entire life of the defect, on both sides.

Measured on this machine before any change, with `node` v24.21.0 and `python3` 3.14.7:

- **Length.** The browser measured `value.length` — UTF-16 code units. Everything else measured
  code points: `varchar(80)` in Postgres, `maxLength: 80` in the published contract (JSON Schema
  defines it that way), and Pydantic. A signature of 41 grinning faces is 82 to the first and 41
  to the rest, so **the browser refused an entry the API stored with a 201**.
- **Whitespace, in both directions.** `str.strip()` removes 29 code points and
  `String.prototype.trim` removes 25. Five are removed only by Python (`U+001C`–`U+001F`,
  `U+0085`) and one only by JavaScript (`U+FEFF`). So six code points were content in one
  language and whitespace in the other — and because the divergence ran both ways, neither
  runtime's default could be called the right answer.
- **A third semantics in the DOM.** `maxLength` counts UTF-16 code units, so the signature field
  stopped accepting input after 40 emoji — **silently**, with no message anywhere. That was the
  worst of the three: the guest loses what they typed and nothing says why.
- **A fourth in the counter.** `{message.length}` measured the untrimmed value in code units
  while the validator beside it measured the trimmed one in code points.

And a fifth disagreement next door: `spec/design/api.md` has always said the search phrase "is
trimmed before it is measured", while `Query(max_length=200)` measured the raw query string. A
phrase of 205 spaces earned a 422; 205 spaces in a signature was simply empty.

The comment above `normalizeEntryField` said "Trim the way the server trims, so the browser
measures the same string the database will store." It was false for six code points. The test
under it was titled "trims the way the server trims, so both measure the same string" and asserted
only about the ASCII space — a character in the **intersection** of the two sets, so it could not
fail on the disagreement it claimed to cover.

## From what, to what

| | before | after |
|---|---|---|
| unit, browser | UTF-16 code units | code points |
| unit, everywhere else | code points | code points, and now written down |
| normalization | none, anywhere | NFC before measuring and storing |
| trimmed set, server | `str.strip()` — 29 code points | one written set — 30 |
| trimmed set, browser | `trim()` — 25 code points | the same written set — 30 |
| `U+1F600`×41 as a signature | screen refuses, API stores it (201) | both accept |
| 41 emoji typed into the field | cut at 40, no message | all 41 kept |
| `é` as `e`+`U+0301` ×80 | refused (160) | accepted (80), same as the composed form |
| `q` of 205 spaces | 422 | no phrase, 200 |
| the counter | untrimmed, UTF-16 | trimmed, normalized, code points |
| binding between the sides | one number equals one number | one number, **and one corpus both read** |

## How it works now

A value is normalized to NFC and trimmed of a written 30-code-point set — Unicode `White_Space`,
the four C0 separators, the byte order mark — and then measured in code points. The same sentence
is true of the browser and of the server, because both call a named function rather than their
runtime's default, and the two functions are held together by
`golden-set/fixtures/text-measurement.json`: 41 cases, each with an input, a verdict and the
length it has afterwards, read by a pytest module and a vitest module that assert the same things.

The bounds did not move. 80, 1000 and 200 are still 80, 1000 and 200 — what moved is that all four
layers now count the same things with them.

Code points rather than graphemes, which is what a guest means by "character", and the reason is
recorded in three places because it will be asked again: `varchar(80)` counts code points so a
grapheme rule would have the column refuse what the application accepted; `maxLength` in the
frozen contract is code points by specification; and Python has no grapheme segmentation in its
standard library, so the two sides would have to agree on a version of UAX #29 and the problem
would return one floor up.

No field stops accepting input at its bound any more. The message under it is the bound.

## What it means for the process

Nothing about running or changing this repository moves, with two exceptions worth knowing:

- **A new corpus file must say whether it holds `entries` or `cases`.** The fitness module sweeps
  the two with different rules, and a file under the wrong key is held to rules that do not fit
  while the ones that do are skipped. `golden-set/README.md` § When you add a file says so.
- **`golden-set/` now routes the `frontend` CI job.** A corpus-only edit runs vitest, because the
  browser's half of the agreement claim lives there. Without it that edit would have gone green
  with the claim unrechecked.

## What it does not change

- **No stored row was rewritten.** There is no migration and no backfill. A value written before
  today keeps its old shape, so a decomposed `é` in an old row is not found by a phrase typed the
  composed way. Recorded in `D-04`, in `BR-01` and in the `_match` docstring rather than assumed;
  the guestbook is this template's worked example and holds no data anybody depends on.
- **No new refusal code.** `spec/design/api.md` already records minting codes for the Pydantic
  cases as rejected, and a bad length is still FastAPI's uncoded 422.
- **The numbers did not move**, and `tests/fitness/test_length_constants.py` still holds them
  equal. It is necessary and was never sufficient; it now has a second binding beside it rather
  than a replacement.
- **`q` is still not frozen in the OpenAPI contract.** That omission is a recorded decision —
  the read parameters' bounds are numbers `spec/design/api.md` owns — and this change had no
  reason to overturn it.
- **`U+200B` and `U+180E` are still content**, on both sides. Neither runtime ever treated them as
  whitespace; what changed is that the corpus now says so in a case of its own instead of leaving
  it to be discovered.

## How it was verified

Every gate: `./scripts/check.sh` — green. `sdd-specs` — green.

Each detector was seen failing first, on the code it was written against:

1. `tests/unit/test_entry_text_rules.py` — **10 failures** against the unwired schema
   (`str_strip_whitespace` + implicit `len`), green after `Author`/`Message` landed.
2. `tests/integration/test_guestbook_entries_router.py::test_a_phrase_of_nothing_but_padding_is_no_phrase_rather_than_a_refusal`
   — **red** with `NormalizedText` removed from ahead of `Query`, green with it restored.
3. `e2e/ui/test_smoke.py::test_a_signature_of_emoji_is_bounded_in_the_unit_the_server_uses`
   — **red** with `maxLength={AUTHOR_MAX_LENGTH}` put back on the signature field: Playwright
   reported the field holding 40 of the 41 characters typed. Green without it. This is the one
   assertion that can see the DOM attribute at all — a unit test of `authorProblem` passes
   whether or not the field truncates.
4. `tests/fitness/test_golden_set.py` — **3 failures** when the corpus first landed (the frontend
   guard, the entry-key sweep, article XI), each closed by a named rule rather than a widening.
5. Both suites carry known positives that assert the corpus can still see the defect: measuring
   in UTF-16 units, trimming with the runtime default, and skipping NFC each redden it.

Counts after: 234 unit, 270 fitness, 131 integration, 213 frontend, 51 e2e — all green.
`./scripts/contracts.sh` reports 0 problems against 2 contracts and 23 fields;
`frontend/src/api/schema.d.ts` regenerated identical, which is expected — the bounds did not move.

The e2e and UI suites were run with `POSTGRES_HOST_PORT=5642` because other worktrees on this
machine hold the default port. Nothing else about the run differed, and CI has the port to itself.

Not run here: the macOS leg, the Lambda package and the production image's runtime assertions —
`spec/design/testing.md` § What only CI can answer names them and they are unaffected by a change
that adds no dependency and moves no script.

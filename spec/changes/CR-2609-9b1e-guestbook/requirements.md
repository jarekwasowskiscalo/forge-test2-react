# Requirements — the guestbook, the template's worked example

**Change:** CR-2609-9b1e
**Source:** `spec/contexts/guestbook.md`, `contracts/openapi/guestbook.yaml`, `spec/design/api.md`

> **This record is retrospective, and says so rather than pretending otherwise.** The
> guestbook shipped in the template's initial state (`b025cc5`), before there was a record
> for a change to travel in. It is written now because the third gate of the change process
> — every requirement has a witness — was passing over an empty set: no change directory
> existed, so no requirement was declared, so no test cited one, so the gate reported "no
> change with a requirements.md" and went green. A gate that is green because there is
> nothing to check teaches nobody anything, least of all somebody forking this template.
>
> The requirements below were **read back out of** the specification and the suites that
> already exist. Nothing here asks for behaviour the system does not have; every acceptance
> criterion names a test that was already passing when this file was written.

## Goal

A guest can leave a signed message in a shared book, read what everybody left, correct their
own words and take them back — with no account, and with the book keeping the same order for
everybody who reads it.

## Success criteria

| Id | Criterion | How measured |
|---|---|---|
| **SC-1** | A guest who has never seen the system leaves an entry and finds it at the top of the book, without instruction. | `e2e/ui/test_smoke.py::test_an_entry_written_through_the_form_appears_in_the_list` writes one through the form and reads it back from the list. It runs against an empty application, so *at the top* is satisfied there rather than asserted; the position is proved by `test_reading_the_book_from_the_other_end_reverses_it` in the same file. |
| **SC-2** | Two guests reading the same book see the entries in the same order, and reading it a piece at a time never shows one entry twice nor loses one. | The scenario "Viewing the guestbook a piece at a time shows every entry exactly once" in `e2e/suite/features/guestbook.feature`. |
| **SC-3** | A guest searching a full book can tell "nothing matches my phrase" from "the book is empty". | The screen renders two different sentences — `Nothing matches that search.` and `No entries yet. Be the first.` — and `describeEmpty` in `frontend/src/contexts/guestbook/lib/entryListCopy.ts` chooses between them by whether the phrase is empty. The two counts are what the *other* two sentences rest on: `total` gives the result line, `total_all` the header count, and `frontend/src/contexts/guestbook/pages/GuestbookPage.tsx` reads them separately. |

## Requirements

### R-1: Leaving an entry — **P1**
**Objective:** As a guest, I want to leave a signed message, so that I leave a trace of having
been here.
**Why this priority:** Without it there is no guestbook. Every other requirement operates on
an entry that this one creates.
**Independent test:** Post one entry to an empty book and read it back at its own address.

1. WHEN a guest submits a signature and a message, the system SHALL store one entry, issue it
   an identifier, and return the stored entry.
2. WHEN an entry is created, the system SHALL stamp the moment of writing and the moment of
   last amendment with the same instant.
3. WHERE the submitted values carry surrounding whitespace, the system SHALL trim them before
   storing.

**Acceptance**
- **R-1.1** GIVEN an empty book, WHEN a guest leaves an entry, THEN the answer carries the
  identifier and both moments, and the entry is readable at its own address.
- **R-1.2** GIVEN a new entry, WHEN it is read back, THEN its two moments are equal by
  construction rather than by rounding, so "edited" is derivable and never stored (`BR-02`).

### R-2: Refusing what is not an entry — **P1**
**Objective:** As a reader of the book, I want incomplete entries kept out, so that the book
never shows a row with nobody and nothing in it.
**Why this priority:** The refusal is the same rule as the acceptance in `R-1`; shipping one
without the other stores empty rows on the first day.
**Independent test:** Submit a signature of three spaces and confirm nothing is stored.

1. IF the signature or the message is empty after trimming, THEN the system SHALL refuse the
   entry and store nothing.
2. IF the signature exceeds 80 characters or the message exceeds 1000, THEN the system SHALL
   refuse the entry.
3. The system SHALL trim before it measures, so that a value of nothing but whitespace is
   refused as empty rather than accepted as its untrimmed length (`BR-01`).
4. WHEN an amendment sets no field at all, the system SHALL refuse it rather than report a
   success it did not perform.

**Acceptance**
- **R-2.1** GIVEN a signature of `"   "`, WHEN it is submitted, THEN the entry is refused and
  the book is unchanged.
- **R-2.2** GIVEN a signature of exactly 80 characters, WHEN it is submitted, THEN it is
  accepted; at 81 it is refused.
- **R-2.3** GIVEN the signature's maximum, WHEN the browser, the contract and the column are
  each asked for it, THEN all three answer 80 (`spec/design/api.md` § Shapes, and the column in
  `spec/design/data-model.md`). The message's 1000 has no column to answer with — the column is
  `Text` by decision, not `String(1000)` (`spec/design/data-model.md` § `guestbook_entries`) —
  so that bound holds between the model's constant and the browser's copy of it, and
  `tests/fitness/test_length_constants.py` is what keeps the two equal.

### R-3: A book with one order, in both directions — **P1**
**Objective:** As a reader, I want the book to have a settled order, so that two readers see
the same thing and a piece boundary loses nothing.
**Why this priority:** `R-7` reads the book in pieces, and a piece of an unordered set is not
a well-defined thing.
**Independent test:** Write two entries within one instant and read the book twice.

1. WHEN the book is read, the system SHALL return the entries newest first by default (`BR-04`).
2. WHERE two entries share a moment of writing, the system SHALL settle the order by the
   identifier, so that the order is total.
3. WHEN the book is read oldest first, the system SHALL reverse the tie-break as well as the
   date, so that one direction is the exact reverse of the other.
4. IF a word that is not a known sort arrives, THEN the system SHALL refuse it rather than
   fall back to a default.

**Acceptance**
- **R-3.1** GIVEN two entries written in the same instant, WHEN the book is read twice, THEN
  both reads return them in the same order.
- **R-3.2** GIVEN a book read oldest first, WHEN it is compared with the same book read newest
  first, THEN one is the exact reverse of the other, tie included.

### R-4: Amending an entry — **P2**
**Objective:** As a guest, I want to correct what I wrote, so that a typo does not stand
forever.
**Why this priority:** The book is useful without it; a guest who cannot correct a typo is
inconvenienced, not blocked.
**Independent test:** Amend one entry's message and compare both of its moments with the
values from before.

1. WHEN a guest amends the signature, the message or both, the system SHALL store the new
   values and return the amended entry.
2. WHEN an entry is amended, the system SHALL move the moment of last amendment and SHALL
   leave the moment of writing untouched (`BR-02`).
3. IF the entry named by an amendment does not exist, THEN the system SHALL refuse rather
   than create one.

**Acceptance**
- **R-4.1** GIVEN an entry, WHEN its message is amended, THEN the moment of writing is
  unchanged and the moment of last amendment has moved.
- **R-4.2** GIVEN an identifier nothing resolves to, WHEN an amendment names it, THEN the
  system refuses and the book is unchanged.

### R-5: Deleting an entry, permanently — **P2**
**Objective:** As a guest, I want to take my words back, so that leaving them is not
irreversible.
**Why this priority:** Valuable, and independent of every other operation.
**Independent test:** Delete one entry out of three and confirm the other two remain.

1. WHEN a guest deletes an entry, the system SHALL remove it with no bin, no flag and no
   recovery (`BR-03`).
2. IF the same entry is deleted a second time, THEN the system SHALL refuse, so that a caller
   is never told they deleted something twice.
3. WHEN one entry is deleted, the system SHALL leave every other entry untouched.

**Acceptance**
- **R-5.1** GIVEN three entries, WHEN one is deleted, THEN the book holds the other two.
- **R-5.2** GIVEN a deleted entry, WHEN it is deleted again, THEN the system refuses.

### R-6: Narrowing the book by a phrase — **P2**
**Objective:** As a reader of a book that has grown, I want to find an entry by a phrase, so
that reading it does not mean reading all of it.
**Why this priority:** Only worth building once a book is long enough to be unreadable.
**Independent test:** Search a phrase present in one entry's message and absent from its
signature.

1. WHEN a phrase is given, the system SHALL return the entries containing it in the signature
   or in the message, regardless of case (`BR-05`).
2. The system SHALL trim the phrase before measuring it, so that a phrase of nothing but
   whitespace narrows nothing.
3. WHERE the phrase contains characters that mean "anything" to the search mechanism, the
   system SHALL match them literally.

**Acceptance**
- **R-6.1** GIVEN an entry whose message contains the phrase and whose signature does not,
  WHEN that phrase is searched, THEN the entry is found.
- **R-6.2** GIVEN a phrase in a different case from the text, WHEN it is searched, THEN the
  entry is found.
- **R-6.3** GIVEN the phrase `100%`, WHEN it is searched, THEN only the entries containing
  those three characters come back.

### R-7: Reading the book a piece at a time — **P2**
**Objective:** As a reader, I want a piece of the book plus the two counts, so that the screen
can tell "nothing matches" from "the book is empty".
**Why this priority:** A bare list cannot say how many it came from, and the two sentences it
cannot distinguish are the ones a reader most needs.
**Independent test:** Read a book of five entries two at a time and assemble the pieces.

1. WHEN the book is read, the system SHALL return a piece together with two counts: how many
   entries match the phrase, and how many the book holds in total (`BR-05`, whose second half
   is this requirement — the rule covers being read a piece at a time as well as being
   narrowed by a phrase).
2. WHEN successive pieces are read, the system SHALL cover the book exactly once, with no
   entry repeated and none lost.
3. WHEN the book is empty, the system SHALL answer with an empty piece rather than a refusal.

**Acceptance**
- **R-7.1** GIVEN a book of five entries read two at a time, WHEN the pieces are assembled,
  THEN each entry appears exactly once.
- **R-7.2** GIVEN a phrase matching nothing in a book that holds entries, WHEN it is searched,
  THEN the matching count is zero and the total count is not.
- **R-7.3** GIVEN an empty book, WHEN it is read, THEN the answer is an empty piece and not a
  refusal.

## Edge cases

### Defects that have already happened once

Two, and neither is `BR-01`'s or `BR-04`'s. Those two rules describe what **would** go wrong
without them — the context says so in the subjunctive (`BR-01`: "Measuring before trimming
would let through…"; `BR-04`: "Without a tie-break… can show one entry twice") — and the
guestbook shipped in a single commit with both already in force, so neither failure has ever
occurred here. They are listed under Attacks below, as `E-6` and `E-7`, which is where a
failure mode a rule prevents belongs.

| Source | What it was | Can this change bring it back? | Evidence |
|---|---|---|---|
| `spec/invariants.md` § Deliberate non-goals | A layer echoed an `X-CSRF-Token` header no service set or checked: it protected nothing and looked to an auditor exactly like protection | No — CSRF protection is a named non-goal of this change too, and there is no session or cookie to forge | `spec/invariants.md` § Deliberate non-goals; `spec/contexts/guestbook.md` § Deliberate non-goals, "this project once had exactly that" |
| `spec/design/api.md`, the preamble | Until 2026-09-02 the register named the Pydantic schemas as the one source of truth about shapes, contradicting article VI — and because of that contradiction this change's own `404` was declared in no generated artefact: the routers raised it without `responses=` | No — both refusals are now declared on the routes they can come from, and `./scripts/contracts.sh` compares the hand-written contract against the dump | `spec/design/api.md`, the dated paragraph in the preamble; the declarations in `app/contexts/guestbook/routers/guestbook_entries.py` |

### Attacks
- **E-1 — empty:** a signature of nothing but whitespace — it costs: a row on the screen with
  nobody in it — the requirements say: `R-2`.
- **E-2 — boundary:** a signature of exactly 80 characters and one of 81 — it costs: the
  browser and the database disagreeing about what is storable — the requirements say: `R-2`.
- **E-3 — malformed:** an identifier that is not a UUID — it costs: a storage read on
  attacker-shaped input — the requirements say: `R-4`, `R-5`.
- **E-4 — malformed:** a phrase containing search metacharacters, such as `100%` — it costs:
  a search for a discount returning the entire book — the requirements say: `R-6`.
- **E-5 — repeated:** deleting the same entry twice — it costs: a caller believing they
  destroyed two things — the requirements say: `R-5`.
- **E-6 — ordering:** two entries written in the same instant, read a piece at a time with no
  tie-break — it costs: one entry shown twice and another lost, silently, while scrolling, and
  never in a test that reads one piece (`BR-04`) — the requirements say: `R-3`, and `R-3.2`
  catches it by comparing both directions.
- **E-7 — empty:** a value measured before it is trimmed — it costs: an entry that passes the
  length check and turns out empty once stored, so the screen shows a row with nobody and
  nothing in it (`BR-01`) — the requirements say: `R-2`, clause 3, which fixes the order of the
  two operations.

### Races
- **W-1 — two guests writing in the same instant:** read-then-write: both rows land with the
  same moment of writing; what the database holds at that moment: two rows whose dates tie,
  separated only by their identifiers — settled by `R-3.2`, which is why the tie-break exists.

### With no defined behaviour
- None. The four operations of `P-01` have no intermediate states and no lifecycle to police:
  an entry either exists or it does not.

## Impact analysis

- **Collisions with invariants:** none. The context writes to nothing but its own table and
  nobody writes to it. Measured against the three the boundary declares in
  `contracts/invariants/guestbook.md`: `D-01` (one row for a record's whole lifecycle — there
  is one table and no archive beside it), `D-02` (a relation replaces a copied column — this
  context has no relations to copy from) and `D-03` (a technical identifier is a UUID — the
  primary key is a `Uuid` the application generates).
- **Decisions that already settle this:** none numbered — `spec/ADR/` is deliberately empty in
  the template, and the reasoning lives in the section that owns it.
- **Dependencies:** none. This is the first context.
- **Frozen rules:** `BR-01`, `BR-02`, `BR-03`, `BR-04`, `BR-05` and `P-01`, all in
  `spec/contexts/guestbook.md` — consistent; these requirements are the ones those rules were
  written from.
- **Tests that would fail:** `tests/unit/test_guestbook_entry_schemas.py`,
  `tests/integration/test_guestbook_entries_router.py`,
  `tests/integration/test_guestbook_entries_service.py`,
  `e2e/suite/features/guestbook.feature`, `e2e/ui/test_smoke.py`.
- **Other changes in flight:** none.

## Non-Goals

Named, so that an absence does not read as an oversight. The first four are the corresponding
entries in `spec/contexts/guestbook.md` § Deliberate non-goals — which holds exactly those four
— restated here as scope rather than as description. The fifth has no entry there and is not an
omission: recovering a deleted entry is settled by `BR-03`, a rule rather than a non-goal, and
it is repeated here because a reader of this record's scope should not have to go and find the
rule to learn that the exclusion is deliberate.

- **Authentication and authorisation** — there are no accounts, sessions or roles, so anybody
  can amend and delete any entry, and a signature is a claim rather than an identity. Decided
  by the template's author: a worked example that carried auth would teach auth, not the
  process. `spec/invariants.md` names it as a non-goal of the whole system.
- **Moderation** — no reports, no hiding, no word list. Same reason.
- **Search relevance** — no inflection, no synonyms, no ranking; results come back in the
  book's order rather than by how well they match. A product needing this starts with a
  full-text index and an ADR.
- **CSRF protection** — there is no cookie or header to forge, because there are no sessions.
  A protective layer that protects nothing while looking like protection is worse than none.
- **Recovering a deleted entry** — `BR-03` makes deletion permanent by decision, not by
  omission.

## Bounds

| Quantity | Value | Where it comes from |
|---|---|---|
| Signature, maximum length | 80 characters | `spec/design/api.md` § Shapes and the column in `spec/design/data-model.md` — the same number in both, and in the migration that made the column |
| Message, maximum length | 1000 characters | `spec/design/api.md` § Shapes. **Not the column**: `spec/design/data-model.md` gives the message `Text`, so this bound holds between the model's constant and the browser's copy, and `tests/fitness/test_length_constants.py` keeps them equal |
| Signature and message, minimum length | 1 character after trimming | `BR-01` |
| Search phrase, maximum length | 200 characters | `spec/design/api.md` § Collection read parameters |
| Sorts accepted | exactly two, each its own wire word | `spec/design/api.md` § Collection read parameters |

## Open questions

None. The change is retrospective: every question it could have raised was answered by
shipping, and the answers are in `spec/contexts/guestbook.md`.

## Self-check

- Is `R-3` testable without `R-7`? Yes — two entries and two reads need no paging; if paging
  were required to observe the order, the two would have to merge into one requirement.
- Does any requirement describe an implementation rather than a behaviour? `R-3.2` comes
  closest by naming the identifier as the tie-break; it stays because the *totality* of the
  order is unobservable without saying what settles a tie.
- Are the two counts in `R-7.1` distinguishable in every case? Only when both are returned
  separately; if the contract ever collapsed them into one number, `SC-3` would become
  unmeasurable and the screen would lose a sentence.
- Is "permanently" in `R-5.1` observable? Only negatively — by the absence of any route that
  returns a deleted entry. A recovery route added later would contradict this requirement
  rather than extend it.
- Do the bounds hold in two places or one? It depends which bound, and that asymmetry is the
  point of `R-2.3`. The signature's 80 reaches the column, so the browser, the contract and the
  database can be asked and compared. The message's 1000 does not — the column is `Text` — so
  its two places are the model's constant and the browser's copy, and only a fitness test holds
  them together. Drop `R-2.3` and the first pair drifts silently; drop
  `tests/fitness/test_length_constants.py` and the second does.
- What happens if a sixth business rule is added to the context? This record stays as it is —
  it describes what shipped, and a new rule travels in its own change.

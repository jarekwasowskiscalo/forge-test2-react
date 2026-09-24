# Tasks — the guestbook, the template's worked example

> Retrospective. The work below was done in this order, in the template's initial commit.
> It is written out because the plan is part of what a fork copies: the wave structure is
> the mechanism, and a record with no `tasks.md` teaches that the mechanism is optional.

## Wave 1 — the tests, before any code exists

### T-1 · build-tests-unit · R-1, R-2, R-3, R-7
**Files:** `tests/unit/test_guestbook_entry_schemas.py`, `tests/unit/test_guestbook_entry_model.py`
**Scope:** `tests/unit/` — nothing beyond it
**Does:** Pins the pure rules with no database: trimming before measuring, the two length
bounds and their off-by-one neighbours, the two sort words, and a page carrying two counts
that are free to differ from its own length.
**Depends on:** —
**Verification:** `./scripts/test.sh unit` — the named tests fail, nothing else changes

### T-2 · build-tests-integration · R-1, R-3, R-4, R-5, R-6, R-7
**Files:** `tests/integration/test_guestbook_entries_service.py`, `tests/integration/test_guestbook_entries_router.py`, `tests/integration/test_guestbook_entries_corpus.py`
**Scope:** `tests/integration/` — nothing beyond it
**Does:** Pins the four operations against a real Postgres, including the total order under a
shared instant, the search that matches signature or message, and the corpus round trip.
**Depends on:** —
**Verification:** `./scripts/test.sh integration` — the named tests fail

### T-3 · build-tests-e2e · R-1, R-2, R-3, R-4, R-5, R-6, R-7
**Files:** `e2e/suite/features/guestbook.feature`, `e2e/suite/steps/`
**Does:** Writes the twenty-one scenarios in business language, each tagged with the
requirement it proves, and binds the steps to the HTTP boundary.
**Depends on:** —
**Must be red:** every scenario in `e2e/suite/features/guestbook.feature`
**Verification:** `./scripts/test.sh e2e` — the scenarios fail against an application that
answers 404 on every route

### T-4 · build-tests-frontend · R-1, R-2, R-4, R-5, R-6, R-7
**Files:** `frontend/src/contexts/guestbook/lib/guestbookEntry.test.ts`, `frontend/src/contexts/guestbook/lib/entryListCopy.test.ts`, `frontend/src/contexts/guestbook/components/`, `frontend/src/contexts/guestbook/pages/GuestbookPage.test.tsx`
**Scope:** `frontend/src/**/*.test.ts`, `frontend/src/**/*.test.tsx`
**Does:** Pins the browser-side rules that have to agree with the server's — the same trim,
the same two bounds — and the copy that turns two counts into two different sentences.
**Depends on:** —
**Verification:** `./scripts/test.sh frontend` — the named tests fail

## Wave 2 — the implementation

### T-5 · build-migration · R-1
**Files:** `alembic/versions/`
**Scope:** `alembic/versions/` — one revision
**Does:** Creates the entries table with a UUID primary key the application generates, two
timezone-aware timestamps, a length-bounded signature column and a text message column, plus
the index that carries the default order.
**Depends on:** —
**Verification:** `./scripts/db.sh migrate` from an empty database, on Postgres (the only engine; the SQLite escape hatch this line once named was removed on 2026-08-31)

### T-6 · build-backend · R-1, R-2, R-3, R-4, R-5, R-6, R-7
**Files:** `app/contexts/guestbook/models/guestbook_entry.py`, `app/contexts/guestbook/schemas/guestbook_entries.py`, `app/contexts/guestbook/services/guestbook_entries.py`, `app/contexts/guestbook/routers/guestbook_entries.py`
**Scope:** the four files above — a subset of what the design says this change owns
**Does:** Implements the four operations through the layers until T-1, T-2 and T-3 pass,
with the tie-break on the identifier that makes the order total in both directions.
**Depends on:** T-1, T-2, T-5
**Verification:** `./scripts/test.sh backend` — T-1's and T-2's tests pass

### T-7 · build-frontend · R-1, R-2, R-4, R-5, R-6, R-7
**Files:** `frontend/src/contexts/guestbook/pages/GuestbookPage.tsx`, `frontend/src/contexts/guestbook/components/`, `frontend/src/contexts/guestbook/hooks/useGuestbookEntries.ts`, `frontend/src/contexts/guestbook/lib/`
**Scope:** `frontend/src/` excluding the generated `frontend/src/api/schema.d.ts`
**Does:** Builds the one screen against the frozen contract: the composer, the list, the
card with its inline correction, the delete dialog, and the phrase and paging carried in the
address so a link reproduces what the reader is looking at.
**Depends on:** T-4, T-6
**Verification:** `./scripts/test.sh frontend` and `./scripts/test.sh ui`

## Scope against the design

| Path from the design | Tasks that touch it |
|---|---|
| `alembic/versions/` | T-5 |
| `app/contexts/guestbook/models/guestbook_entry.py` | T-6 |
| `app/contexts/guestbook/schemas/guestbook_entries.py` | T-6 |
| `app/contexts/guestbook/services/guestbook_entries.py` | T-6 |
| `app/contexts/guestbook/routers/guestbook_entries.py` | T-6 |
| `frontend/src/` | T-4, T-7 |
| `tests/` | T-1, T-2 |
| `e2e/` | T-3 |

> Paths updated on 2026-09-08, after the tree was cut by bounded context (2026-09-07): the
> record describes the files as they stand, not as they were laid out when the change shipped.
> The SQLite verification step above was corrected on the same day; the engine was removed on
> 2026-08-31 (`spec/design/architecture.md` § One engine).

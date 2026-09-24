---
date: 2026-09-16
branch: fix/ui-state-names-its-operation
pr: 49
kind: fix
---

# Bind every UI state to the operation that caused it

## What changed

Four findings of the 2026-09-15 audit — A27, A28, A31 and A32 — in one change, because they
overlap in three files and in one cause. They are issue #26 in this repository,
`Scalo-Sales-Engineering-Consulting/forge_template_python_react#26`.

- `frontend/src/contexts/guestbook/lib/entryPaging.ts` — **new**. The paging arithmetic with no
  React in it: `SHOWN_MAX`, `shownFrom`, `firstPageRequest`, `nextPageRequest`.
- `frontend/src/contexts/guestbook/hooks/useGuestbookEntries.ts` — `useInfiniteQuery` instead of
  `useQuery`, `offset` on the wire, `limit` out of the query key, the answered question carried
  back with the data, and the effect that fills the screen up to what the address asks for.
- `frontend/src/contexts/guestbook/hooks/useEntryQueryParams.ts` — the search draft carries the
  address it was seeded from and is reseeded by every navigation; a write deferred from before a
  navigation is refused; `showMore` became `onShownChange`.
- `frontend/src/contexts/guestbook/pages/GuestbookPage.tsx` — the result sentence is built from
  the question the visible entries answer; `isPlaceholderData` drives a visible waiting state;
  a save's `onSuccess` closes only the editor that sent it; the pending marker is bound to
  `update.variables.id`.
- `frontend/src/contexts/guestbook/components/EntryToolbar.tsx` — an `isStale` prop, put on the
  existing `aria-live` region as `aria-busy`.
- `frontend/src/contexts/guestbook/components/EntryCard.tsx` — an `isSaveInFlight` prop; "Edit"
  is locked on every card while an amendment travels.
- `frontend/src/contexts/guestbook/lib/entryListCopy.ts` — `describeResult` takes `settled` and
  appends ` — updating…`; `READ_FAILED_LABEL` is new.
- Tests: `entryPaging.test.ts` and `useEntryQueryParams.test.tsx` are new;
  `GuestbookPage.test.tsx`, `useGuestbookEntries.test.tsx` and `entryListCopy.test.ts` grew;
  `e2e/ui/test_smoke.py` gained two — a guestbook of 101 entries read to its end, and a reload
  that brings back the stretch "Load more" put on screen.
- Specification: `spec/design/ui/guestbook.md` (the reversed paging decision with its dated
  `Rejected` block, the `stale` and `saving` rows, `?shown=`, two events, two copy rows) and
  `spec/design/testing.md` (the hook is no longer deliberately untested).
- `docs/user-guide.md` — two sentences: what a search in flight looks like, and that the address
  records how far down the book you are.

**No backend, no contract, no migration.** `offset` was implemented, contracted in
`spec/design/api.md`, tested, and already present in `frontend/src/api/schema.d.ts`. The screen
was the only thing not using it.

## Why

One cause wearing four faces: **a global flag describing "the current thing" used to describe one
particular operation in flight.**

The expensive one was A27. `?shown=` was clamped to the contract's ceiling of 100 — which
silently redefined it from *how many entries are on screen* to *how big one request may be*. Once
a reader reached the hundredth entry the clamp stopped the number moving, the query key is what
`limit` fed, so the key stopped moving too, and no refetch was issued. The button stayed, because
`remaining` was computed against a list that could no longer grow. Every entry past the hundredth
was unreachable from the screen, with no error anywhere — and the whole of it was invisible to the
test suite, whose fixture held nine entries.

A28 was a hidden trigger. `setParams` from `useSearchParams` closes over the current parameters,
so its identity changes on **every** navigation; an effect listing it in its dependencies re-ran
as though somebody had typed, and wrote the pre-navigation phrase back into the address with
`replace: true`. Back returned you to a filter you had just left, and took the paging with it.
A debounce timer outliving the navigation did the same thing a quarter of a second later.

A31 and A32 are the same sentence about two different states. The result line took the phrase from
the address (already new) and the counts from the cache (still the previous key's), so it read
`2 matches for "Zzz"` over two entries that matched nothing of the sort — announced, through
`aria-live`. The comment promising `isPlaceholderData` had no implementation anywhere in the tree.
And a save's `onSuccess` called `setEditingId(undefined)` with no reference to the entry it was
sent for, so the answer to A closed whatever editor was open by then.

## From what, to what

| | Before | After |
|---|---|---|
| Reading past entry 100 | impossible; the button stayed and did nothing | the next piece is read by `offset`; the button goes at the end |
| `?shown=104` | clamped to `100` | 104 on screen, restored in two reads of 100 and 4 |
| The query key | `{search, sort, limit}` | `{search, sort}`; how much is on screen is an argument |
| Navigating to `?q=brian` with the hook mounted | the address went back to `?q=anna` | the field follows the address; the deferred write is cancelled |
| A post | `navigate()` **and** `onSearchChange('')` | `navigate()` alone |
| The count while a search travels | attributed to the new phrase | attributed to the phrase it came back for, plus ` — updating…` |
| Waiting for a new phrase | no indicator at all | the sentence says so, the live region is `aria-busy` |
| The count after a failed read | a blank line | `The entries could not be loaded.` |
| Saving A, then opening B | B's editor closed; the marker followed B | "Edit" is locked until A settles; the marker stays on A |

## How it works now

The address is the source of truth and everything follows it in one direction.

`?q=`, `?sort=` and `?shown=` are the whole question. A navigation reseeds the search field;
typing writes back after ~250 ms, and only typing that happened after the last navigation may do
so. Pressing "Load N more" writes `?shown=` and nothing else — an effect in the reading hook then
asks for pieces until that many entries are on screen or the guestbook runs out, each request
within the contract's cap of 100. So a reload of the same address restores the same stretch of the
book, in the fewest reads that can carry it.

Every read hands back the question it answered alongside its entries and counts, so the sentence
under the toolbar is assembled from one source rather than two. While a newer question is
travelling the previous answer stays, says whose answer it is, and carries ` — updating…`.

An amendment belongs to the entry it was sent for: its "Saving…" marker is bound to the request's
own id, its answer closes only the editor that sent it, and "Edit" is locked everywhere until it
settles.

## What it means for the process

Nothing about running or changing this repository moves, but two things this change had to do are
worth the next person's time.

**It took the manual road for a change of behaviour, and paid the stated price.** `change-directory`
is red for it and always would be: twelve behaviour files moved with no change record for the gate
to find. It is let through by a dated row in `spec/changes/EXEMPTIONS.md`, expiring 2026-09-30, and
the `spec-exempt` label on the pull request — which prints the exemption to the job summary, so the
exception is read rather than taken silently. The other two diff-scoped gates it tripped,
`recorded-decision` and `e2e-scenario`, were **not** waived: both were asking for something the
change owed, and both were paid.

**No ADR was written**, for the reverse of the paging decision or for the testing one.

`spec/design/conventions.md` § When a decision is an ADR keeps `spec/ADR/` empty until the first
change goes through the process, and `spec/changes/EXEMPTIONS.md` names the substitute — the
decision goes into the document whose rule it changes, as a dated
`Rejected (decision of <date>, cr: historical — …)` block. That is where the reversal of
"Load more asks for a bigger piece" stands, in `spec/design/ui/guestbook.md`, and the reversal of
"three files carry no test of their own" in `spec/design/testing.md`.

## What it does not change

- **The API.** No endpoint, parameter, refusal or status moved; `contracts/openapi/guestbook.yaml`
  and `frontend/src/api/schema.d.ts` are untouched, and `npm run gen:api` was not needed.
- **The database.** No migration, no column.
- **The black box.** `e2e/suite/features/guestbook.feature` and `e2e/ui/test_smoke.py` are
  unchanged and pass as they stood: the smoke seeds six entries, presses "Load 2 more" and sees
  the button go, which is true under both paging models.
- **The debounce.** `frontend/src/hooks/useDebouncedValue.ts` is untouched; the cancellation is a
  refusal to write a stale value, not a new API on the hook.
- **A29 and A30** (the accessibility findings, issue #27) — a disjoint set of files, untouched
  here.

## How it was verified

- `./scripts/check.sh` — **`Check: OK`**, every gate it runs, including the 44 black-box tests (30
  BDD scenarios plus the 14-test Chromium smoke) against a live application. Both were unchanged
  by this work and both stayed green.
- `./scripts/test.sh frontend` — 133 tests over 14 files. It was 105 over 12.
- `sdd-specs` — the specification gates, green.
- **Each of the four fixes was mutated back and the suite rerun**, because a test for a defect that
  passes against the defect proves nothing. Restoring the `PAGE_SIZE_MAX` clamp fails 6 tests;
  removing the deferred-write guard fails 4; building the result sentence from the address fails
  the attribution test; rebinding the save marker to `editingId` fails the held-PATCH test.
- **By hand, in a browser, against a guestbook of 105 entries** — the size at which A27 and A28
  actually appear, and which no fixture in the repository had: reading past the hundredth entry
  reached all 105 with no duplicate and the button then went away; `?shown=104` restored in exactly
  two reads, `limit=100` and `limit=4&offset=100`, with no request above the contract's cap and no
  `offset=0` sent; and Back arriving mid-pause landed on the earlier phrase, reseeded the field,
  never wrote the phrase being typed, and left Forward working.

**Not observed by hand:** the two states that need a held response — the stale result line and a
save in flight. The browser could not be made to delay them, because `openapi-fetch` captures
`globalThis.fetch` when the module loads and a patch installed afterwards is never seen. Both are
covered instead by tests that hold the response open and read the screen at each moment, and both
were mutation-checked above.

# Acceptance tests — the guestbook, the template's worked example

*A script for a human, after delivery. No requirement here is marked
`**Verified-by:** manual` — all seven carry automated proofs — so this script exists for a
different reason: it is what a person runs the first time they stand up a fork, to confirm the
example works end to end before they start deleting it. The names below are short on purpose,
so that a tester can see the order at a glance; the corpus in `golden-set/fixtures/` is what
the suites read, and nothing here is asserted about by a test.*

## Preconditions

- What has to be built first: `./scripts/build.sh` — the SPA is compiled into `app/static`,
  which is generated and gitignored. `start.sh` does not build it, so on a fresh clone the API
  answers and every screen route returns a JSON 404 telling you to run this.
- What has to be running: `./scripts/start.sh --no-seed` — Postgres, the migrations and the
  application on `:8080`. **The flag is not optional for this script.** Without it `start.sh`
  fills an empty guest book from `golden-set/seed/` as soon as the application answers, and
  then step 1 has no empty state to lose and step 3's ordering is judged against four entries
  the tester did not write.
- What data has to be loaded: nothing; step 1 starts from an empty book, which is what
  `--no-seed` is for
- What the tester should see before step 1: the one screen at `http://localhost:8080`, with
  its empty state inviting a first entry

## Steps

| # | Screen | What to do | What is to happen (exactly) | Requirement | Result |
|---|---|---|---|---|---|
| 1 | Guestbook | Leave an entry signed `Anna` with the message `Good morning!` | The entry appears at the top of the list; the empty-state sentence is gone | `CR-2609-9b1e/R-1` | yes / no |
| 2 | Guestbook | Type a signature of nothing but spaces and a message | The submit control stays closed; nothing is sent | `CR-2609-9b1e/R-2` | yes / no |
| 3 | Guestbook | Leave two more entries, signed `Bo` and `Cyd` | `Cyd` is at the top and `Anna` at the bottom | `CR-2609-9b1e/R-3` | yes / no |
| 4 | Guestbook | Switch the order to oldest first | The list is the exact reverse of what step 3 showed | `CR-2609-9b1e/R-3` | yes / no |
| 5 | Guestbook | Correct `Anna`'s message inside its card | The new text is shown and the card is marked as edited; the date it was written is unchanged | `CR-2609-9b1e/R-4` | yes / no |
| 6 | Guestbook | Delete `Bo`'s entry and confirm the dialog | `Bo` is gone; `Anna` and `Cyd` are still there | `CR-2609-9b1e/R-5` | yes / no |
| 7 | Guestbook | Search for `cyd` in lower case | Only `Cyd`'s entry is listed, case notwithstanding | `CR-2609-9b1e/R-6` | yes / no |
| 8 | Guestbook | Search for a phrase nothing contains | The screen says nothing matched — **not** that the book is empty | `CR-2609-9b1e/R-7` | yes / no |
| 9 | Guestbook | Clear the search | Both remaining entries come back | `CR-2609-9b1e/R-6` | yes / no |

Step 8 is the one worth being slow about. It is the only step whose failure looks like
success: a screen that says "the guestbook is empty" in front of a book holding two entries
is a screen reporting the wrong one of two sentences, and it reads as a system that has lost
its data.

## Tester's notes

*<filled in by a human after the run>*

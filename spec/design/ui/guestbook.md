---
screen: guestbook
route: /guestbook
info_ref: S-01
requirements: [CR-2609-9b1e/R-1, CR-2609-9b1e/R-2, CR-2609-9b1e/R-3, CR-2609-9b1e/R-4, CR-2609-9b1e/R-5, CR-2609-9b1e/R-6, CR-2609-9b1e/R-7]
mockup: null
---

# Guestbook

One of the application's two screens, and the one its main address opens; the other is the
to-do list ([`todo-list.md`](todo-list.md)). A guest opens it, reads what others wrote, and adds an
entry of their own; they can also find an entry, view the guestbook a piece at a time, and amend
or delete any entry — including somebody else's, because there is no identity here
([`../../contexts/guestbook.md`](../../contexts/guestbook.md) § Deliberate non-goals).

The screen was built from a Claude Design mock-up
([`spec/rationale/mockup-guestbook/Guestbook.dc.html`](../../rationale/mockup-guestbook/Guestbook.dc.html)):
one centred column on a cream background, a serif title, a dark green accent.

`mockup: null`, and that is **a record of a fact rather than an absence**: the mock-up arrived in
an archive outside the SDD process, and [`README.md`](README.md) § HTML is the evidence foresees
one place for it — `spec/changes/<CR>/design/ui/index.html` — which this change does not have,
because it opened no change record. A field pointing at a file that is not in the repository
would be worse than an empty one. The first change to this screen carried out through `/sdd` will
put the mock-up where it belongs and fill this field in.

The mock-up differs from what was built in two places, and **both are deliberate**:

1. **A signature is required.** The mock-up substituted "Anonymous" for an empty signature;
   `BR-01` does not allow for that, and changing a business rule is not changing an appearance.
2. **Deleting asks.** The mock-up deletes outright on a click; `BR-03` is irreversible, and a
   layout drawing is not a decision to remove the only warning.

The frame, the palette, the typeface and the primitives: [`system-states.md`](system-states.md).

## Regions

Top to bottom, inside the page frame:

1. **Header and title** — the frame's lockup and its navigation between the screens, with
   "Guestbook" marked as the screen on show ([`system-states.md`](system-states.md) § Regions),
   the number of entries in the whole guestbook, the title "Leave a note" and a sentence saying
   there is no sign-in here.
2. **The composer card** (`EntryComposer`) — signature, message, length counter, button.
3. **The toolbar** (`EntryToolbar`) — a search field, two order pills, and beneath them one
   sentence about the result.
4. **The list of cards** (`EntryCard`) — one entry is one card, with two actions and **in-place
   editing**.
5. **The load-more button** — only when something is left.
6. **The confirmation dialog** (`DeleteEntryDialog`) — above the screen, only when deleting.

## Components and their states

### The composer card (`EntryComposer`)

| State | What is visible |
|---|---|
| `default` | two empty fields with no border, the counter `0 / 1000`, the button **`disabled`** |
| `focus` | a focus ring in the accent colour; no change of layout |
| `error` | a sentence under the field, `role="alert"`, `aria-invalid` on the field |
| `disabled` | both fields and the button locked while a write is in flight |
| `loading` | the button says "Posting…"; the card stays on screen, it does not disappear |

**The fields have no visible label**, as in the mock-up — two placeholders in a card that is
obviously a form. They do carry an `aria-label`: a placeholder on its own is a label that
disappears at exactly the moment somebody starts typing.

**The placeholder is therefore text under WCAG 1.4.3, not decoration**, and is held to the same
4.5:1 floor as everything else ([`system-states.md`](system-states.md) § Tokens). It is the only
thing on screen saying what goes in the field.

**The focus ring is the screen's, and no component may cancel it.** It is declared once, in
`frontend/src/index.css`, on `:focus-visible` inside `@layer base` — and a Tailwind utility on
the element (`outline-none`) beats it whatever its specificity, because `@layer utilities` is a
**later layer** and layer order settles the cascade before specificity is consulted. A field that
wants a different ring says so with a `focus-visible:outline-*` utility, which competes inside
the same layer; it never removes the ring and leaves nothing.

Rejected (decision of 2026-09-16, `cr: historical` — found by measuring the *built* stylesheet,
from the trunk, where neither an ADR nor a `delta.md` is available):

- **Strengthen the base rule instead — `!important`, a heavier selector.** Neither reaches it.
  The rule matched and lost on one property in a later layer, so no amount of specificity
  changes the outcome; the only cure at that level is to move the ring into `@layer utilities`,
  which would put the screen's one accessibility guarantee in the layer components write to.
- **Assert the ring in `vitest`.** The component suite runs in jsdom, which loads no application
  CSS, implements no `@layer`, and does not support `:focus-visible` — a test for the ring's
  presence in the *source* would have passed on a screen with no visible ring at all, which is
  exactly the state the repository was in. The assertion belongs in a browser: `e2e/ui/`.

**An error appears only after the field is left**, never on every character. Telling somebody
their signature is too short at the first letter is noise — and noise is what teaches people to
ignore red text that means something real.

**No field stops accepting input at its bound; the message under it is the bound.** Both fields
carried `maxLength` until 2026-09-17 and it was removed on purpose. The HTML attribute counts
UTF-16 code units, which nothing else in this system counts, so the signature field stopped
accepting characters after 40 emoji rather than 80 — and it stopped *silently*, which is the
worst of the three symptoms the bound had: the guest loses what they typed with no sentence
anywhere saying why. A validator message a person can read is the whole remedy, and it now
counts the same code points the server counts.

Rejected (decision of 2026-09-17, `cr: historical` — taken outside `/forge:sdd` on GitHub issue
#28, so there is no `delta.md` in which to declare it):

- **Keep `maxLength` as a generous safety valve (×4).** It would still truncate silently, only
  later and at a number matching no rule anywhere. A cap nobody can predict is worse than no cap
  for the person meeting it.
- **Clamp on paste to the code-point bound.** A visible, correct hard stop — but it is a fourth
  place that measures text, it needs a screen state of its own to explain itself, and the
  message under the field already says the same thing without any of that.
- **Leave it and fix only the validator.** The two would then disagree about the same field: the
  message would say 80 while the field accepted 40. That is the defect, not a smaller version
  of it.

**The button is `disabled` until both fields have content.** The rule lives in
`frontend/src/contexts/guestbook/lib/guestbookEntry.ts`; the screen only applies it.

Rejected (decision of 2026-09-07, `cr: historical` — the two files this document cites moved
when the tree was recut by bounded context. The decision itself is
[`../conventions.md`](../conventions.md) § Frontend — where a file goes and
[`../architecture.md`](../architecture.md) § What a new feature adds; this edit is only its
consequence, and it is recorded because the edit was made from the trunk, where no `delta.md`
exists to call it editorial):

- **Leave the citations pointing at the old paths.** They resolve to nothing, and
  `backtick-paths` says so on every pull request. A screen specification pointing at a file
  that is not there is precisely the drift between screen and specification this document
  exists to prevent — and the rule it points at did not move, only the file did.

**The card clears after a successful post and does not clear after a failed one.** The first, so
that the next guest does not send somebody else's entry a second time. The second, because a
form that empties its fields after an error is a form nobody retries.

**After a successful post the screen returns to the unfiltered guestbook, newest first.** An
entry sent while searching would land outside the result, and an entry you cannot see looks like
an entry that was not saved.

### The toolbar (`EntryToolbar`)

| State | What is visible |
|---|---|
| `default` | an empty search field, "Newest" selected |
| `searching` | the typed phrase, the result sentence says how many match |
| `stale` | the previous answer stays on screen, its sentence carries ` — updating…`, and the live region is `aria-busy` |

**Search asks the server, it does not filter an array on screen.** An entry that did not fit in
the first piece must be findable — a browser-side filter finds only what is already visible.

**The phrase waits ~250 ms before it travels.** Without that every character is a separate
request, the answers race, and the one that came back last wins.

**Changing the phrase or the order resets the number of entries shown.** Otherwise twelve
loaded entries become twelve results for a phrase that matches two — and the other way round, a
narrow piece reads as "that is all".

**The question lives in the address**, not in a component's memory: `?q=`, `?sort=oldest`,
`?shown=8`. A result can be sent as a link and survives a reload. Every parameter is **absent at
its default value**, so an ordinary address is `/guestbook` rather than
`/guestbook?q=&sort=newest&shown=4`. A write **replaces** the history entry: a six-letter
phrase would otherwise leave six entries, and "back" would remove the letters one at a time.

**The address is the source of truth, and the search field follows it.** A navigation — a link
followed in place, Back, Forward, the jump after a successful post — reseeds the field, and only
typing that happened after that navigation may write back. A phrase still waiting out its ~250 ms
when a navigation arrives is **cancelled**, never written. The other direction is a screen that
undoes the reader's own Back, and does it a quarter of a second later, where nothing connects the
two.

**`?shown=` says how many entries are on screen**, not how big one request may be. The contract
caps a single read at 100 (`api.md` § Collection read parameters), so an address asking for more
is restored by **repeating the read** — each request inside that cap, none of them a refusal. The
number is still clamped, at ten reads' worth: an address typed by hand should show the guestbook,
and should not cost five hundred requests either.

**The result sentence has two forms and they are two different questions.** Without a phrase:
`Showing 4 of 12` — how much of the guestbook is visible. With a phrase: `3 matches for "anna"` —
whether the search worked at all. The number matching is the count of **the whole population**,
not of the piece; deriving it from the length of the list is a defect nobody sees, because what
comes out of it is a plausible-looking number.

**The sentence belongs to the answer on screen, not to the phrase in the field.** While a newer
question is travelling those are two different things, and a sentence assembled from one of each
says `2 matches for "Zzz"` over two entries that match nothing of the sort. The phrase quoted is
the one the visible entries came back for, and ` — updating…` says the answer is behind. After a
failed read the sentence says the read failed, rather than keeping numbers that no longer stand
for anything.

### The entry card (`EntryCard`)

| State | What is visible |
|---|---|
| `default` | the signature, the entry's age, "Edit" and "Delete", the message |
| `edited` | "· edited" joins the age |
| `editing` | two fields and "Save"/"Cancel" instead of the message; "Edit" says "Editing" |
| `saving` | "Saving…" and the fields locked on the card whose amendment is travelling; "Edit" locked on **every** card until it settles |
| `deleting` | "Deleting…", both actions locked |

**Editing happens in the card.** The words somebody is correcting stay where they read them, and
the list does not run away from under them. At most **one** card is ever open: two at once is a
state this screen cannot settle.

**An amendment in flight belongs to the entry it was sent for, and no editor may move while it
is.** "Edit" is closed on every card until the answer lands. Without that, opening a second card
mid-save moved the editor out from under the save: the answer closed whichever card happened to
be open by then, and the "Saving…" marker moved with it, so the entry actually being written
stopped being marked as written. The alternative — let the second card open and keep the marker
on the first — shows a "Saving…" on a card that is no longer an editor, which is a state with
nothing to read it on. The lock lasts exactly as long as the request.

**The editor is remounted on the entry's key.** Without that a second editing session shows the
first entry's content — and nothing on screen says so.

**"Save" is closed when a field is empty.** `BR-01` is about entries, not about how they came to
be: an amendment may not do what a new entry is forbidden.

**The age is text, but the instant stays in the markup.** `<time dateTime="…">` carries the exact
moment; "2 hours ago" rounds. A card that rendered only words would lose when the entry was
really written.

**"· edited" is derived** from comparing both instants (`BR-02`), not read from a column.

### The list and its states

| State | What is visible |
|---|---|
| `loading` | four skeletons in the shape of cards, never a blank screen |
| `empty (guestbook)` | "No entries yet. Be the first." in a dashed frame |
| `empty (search)` | "Nothing matches that search." — **a different sentence**, because a different fact |
| `error` | an `ErrorState` with `role="alert"` and a "Try again" action |
| `more` | a "Load N more" button, where N never promises more than is left |

**"Be the first" in front of a guestbook full of entries reads like an application that has lost
them.** Hence two sentences, decided by whether the phrase is empty, not by whether the list is.

**The list does not sort what it was given.** The order is the server's (`BR-04`); a list that
reorders the rows it received can disagree with paging and show an entry twice.

**"Load more" appends the next piece, by `offset`.** Each press asks for the four entries after
the ones on screen and writes the new total into `?shown=`; the button goes away when `offset`
has reached the count that matched. An entry added or removed while several pieces are on screen
cannot duplicate or vanish, because every write invalidates the whole read and the pieces are
replayed from the first over the order as it now stands — the order is total (`BR-04`), so a piece
boundary is a place in it rather than a guess.

Rejected (decision of 2026-09-16, `cr: historical` — this reverses a decision recorded in this
document, and it is recorded here rather than in `spec/ADR/` because
[`../conventions.md`](../conventions.md) § When a decision is an ADR keeps that directory empty
until the first change goes through the process, and a rule with two homes is the failure it is
kept empty to avoid; the repair was made on the trunk and carries no `delta.md`):

- **Keep asking for a bigger piece from the same start.** It was chosen because a growing window
  over a total order cannot duplicate or lose an entry while somebody writes, and that much was
  true. What it could not do was reach past the hundredth entry: the contract caps a single read
  at 100, so the window stopped growing there while `?shown=` went on counting, the read stopped
  changing with it, and "Load N more" stayed on screen for ever offering entries it could no
  longer fetch. A decision that holds only for guestbooks smaller than a hundred is not a decision
  about this guestbook. The property it was chosen for is kept by other means, named above.
- **Raise the cap on a single read.** It moves the wall rather than removing it, and it does so by
  making the API answer an unbounded page — a contract change paid for by every client, to buy a
  screen one that pages properly does not need.

### The delete dialog (`DeleteEntryDialog`)

| State | What is visible |
|---|---|
| `default` | the entry's signature and message, a sentence about irreversibility, two buttons |
| `loading` | "Deleting…", both buttons locked, the dialog **not closeable** |

**The dialog quotes the entry it is about.** Cards differ only in their content, so a
confirmation that does not name what it will destroy cannot be answered correctly.

**Focus lands on "Cancel", not on the destructive action.** An Enter pressed out of habit is to
delete nothing.

**Focus lands *inside the dialog* in every state, and "Cancel" is the preference rather than the
promise.** In `loading` both buttons are locked, so there is nothing in the dialog that can hold
the keyboard except the dialog itself: focus goes to the `role="dialog"` container. The screen
asks whether the element it wanted actually took the focus rather than whether it exists — a
`disabled` button is a perfectly live element that silently refuses, and so are a hidden one, a
`display: none` one and one that has already left the page.

**Tab cannot leave the dialog, from either direction, including when focus is already outside
it.** The cycle closes both ways; a Tab pressed with focus somewhere behind the modal brings it
back. The last condition is not hypothetical — it is what a browser leaves behind after the
element that opened the dialog goes away.

**The rest of the page is inert while the dialog is open**, and is exactly as it was afterwards.
`aria-modal="true"` tells a screen reader the page behind is unavailable, and a reader given that
claim while focus is physically behind the dialog has two incompatible models of one page — worse
than never having claimed it.

**Focus returns to whatever opened the dialog, and to the nearest thing still on screen when that
is gone.** A confirmed delete removes the card the "Delete" button sat in, so there is nothing to
hand focus back to; it goes to the closest ancestor still in the document — the list being read —
and never to `<body>`, from where the next Tab restarts at the top of the page.

Rejected (decision of 2026-09-16, `cr: historical` — the mechanism was repaired from the trunk,
where neither an ADR nor a `delta.md` is available; `../conventions.md` § When a decision is an
ADR keeps `spec/ADR/` empty until the first change carried out through `/sdd`, so the decision is
recorded here, in the document whose rule it concerns):

- **A native `<dialog>` with `showModal()`.** It would supply the backdrop, the inertness, the
  entering focus and Escape for nothing. Three things stand against it. It paints in the browser's
  **top layer**, over every z-index there is, and this application's toast host is an ordinary
  always-mounted `fixed` node — so `::backdrop` would cover the one region that has anything to
  say while the dialog is open, and a failed delete is announced exactly there. A `<dialog>`
  closes on Escape natively, so the `loading` row above — the dialog is **not closeable** while
  the request is in flight — costs an intercepted `cancel` event, which is the same amount of
  code as owning the key. And both `aria-live` regions are deliberately mounted at all times, so
  moving the dialog into the top layer changes what a reader observes about a region it is
  already watching. Revisit it together with the toast host, not on its own.
- **Leave the reason as it stood.** The component's own comment blamed "this app's
  `position: absolute` overlays", of which there is not one in the tree. A recorded reason that
  is false is worse than none: the next reader checks it, finds it wrong, and throws out the
  decision along with it.

## Copy

All of it here — it is product content rather than an implementation detail. The language is
settled by [`../conventions.md`](../conventions.md) § Language.

| Key | Text |
|---|---|
| screen title | `Leave a note` |
| introductory sentence | `No account, no sign-in. Write something, and it appears below straight away. Anyone can edit or remove an entry.` |
| entry count | `1 entry` / `7 entries` |
| signature placeholder | `Your name` |
| message placeholder | `Write your message…` |
| character counter | `0 / 1000` — code points of the trimmed, normalized message |
| post button | `Post entry` |
| button in flight | `Posting…` |
| search placeholder | `Search entries` |
| order | `Newest` · `Oldest` |
| result, no phrase | `Showing 4 of 12` |
| result, with phrase | `3 matches for “anna”` / `1 match for “anna”` |
| result, answer still travelling | the sentence above plus ` — updating…` |
| result, read failed | `The entries could not be loaded.` |
| card actions | `Edit` · `Delete` |
| card being edited | `Editing` |
| saving an amendment | `Save` · `Saving…` · `Cancel` |
| amendment marker | `· edited` |
| entry age | `just now` · `1 minute ago` · `2 hours ago` · `3 days ago` · `31 Aug 2026` |
| load more | `Load 4 more` |
| empty guestbook | `No entries yet. Be the first.` |
| empty search | `Nothing matches that search.` |
| dialog — title | `Delete this entry?` |
| dialog — quotation | `<signature> wrote:` |
| dialog — consequence | `This cannot be undone.` |
| dialog — confirmation | `Delete entry` · `Deleting…` · `Cancel` |
| toast after posting | `Entry posted.` |
| toast after amending | `Entry updated.` |
| toast after deleting | `Entry deleted.` |
| error — empty signature | `Add a name or a signature — an entry without one is not saved.` |
| error — empty message | `Write something — an empty entry is not saved.` |
| error — signature too long | `A signature can be at most 80 characters.` — the sentence says "characters" because that is the word a guest uses; the rule counts code points (`../../contexts/guestbook.md` § `BR-01`) |
| error — message too long | `An entry can be at most 1000 characters.` |
| footer | `Entries are public and editable by anyone with this link.` |

### Accessibility labels

Text nobody sees and assistive technology reads — `aria-label`, the names of regions and states.
Here for the same reason as the rest, because a component test and the smoke look elements up by
them:

| Text | Component |
|---|---|
| `Your message` | `frontend/src/contexts/guestbook/components/EntryComposer.tsx` |
| `Edit name` | `frontend/src/contexts/guestbook/components/EntryCard.tsx` |
| `Edit message` | `frontend/src/contexts/guestbook/components/EntryCard.tsx` |
| `Order` | `frontend/src/contexts/guestbook/components/EntryToolbar.tsx` |
| `Dismiss notification` | `frontend/src/components/ui/Toast.tsx` |

The **server's** refusal sentences live beside the endpoint that produces them
([`../api.md`](../api.md) § Refusals): they are backend text rather than this screen's text. The
screen can display two of them: `guestbook_entry_not_found` (when somebody else deleted the entry
in the meantime) and `guestbook_entry_empty_patch`. Both are English, like everything else
(`../conventions.md` § Language); the router holds the sentences and this screen displays them.

Rejected (decision of 2026-09-05, `cr: historical` — found by auditing this document against
`app/contexts/guestbook/routers/guestbook_entries.py`, from the trunk, where neither an ADR nor a `delta.md` is
available):

- **Leave the sentence as a harmless note.** A screen specification saying its refusal copy
  "is still written in Polish, and moves to English together with the router" is an
  instruction to the next author, in a document `design-ui` and `build-frontend` both read as
  the authority on copy. The move it promises happened before this document was last touched.

## Data

| What | From where |
|---|---|
| the phrase, the order, the piece size | the page address, through `useEntryQueryParams()` |
| a piece of the list + two numbers | `GET /api/guestbook-entries?q&sort&limit&offset` through `useGuestbookEntries()` |
| posting | `POST /api/guestbook-entries` through `useCreateGuestbookEntry()` |
| amending | `PATCH /api/guestbook-entries/{entry_id}` through `useUpdateGuestbookEntry()` |
| deleting | `DELETE /api/guestbook-entries/{entry_id}` through `useDeleteGuestbookEntry()` |

**What is posted and amended is the text the screen judged, not the text as typed.** The composer
and the entry card send each field as the shared text rule leaves it — normalized and trimmed —
so the browser and the service measure the same value; the service normalizes it again either
way.

**Components never call `client.GET` directly** — one hook per resource, the query keys in one
object (`spec/design/conventions.md` § Frontend). The list's key carries the phrase, the order
and the piece size, so two different questions are two cache entries rather than one that jumps
between two answers. Every mutation invalidates the resource's key, so a refresh corresponds to
something that really happened.

## Interactions

| Event | Effect |
|---|---|
| typing in the composer card | the button unlocks when both fields have content; the counter rises — over the **trimmed, normalized** message in code points, which is the string the validator beside it measures and the server will store. It read the raw value in UTF-16 units until 2026-09-17, so it could show `1000 / 1000` for a message the validator called shorter, and again for five hundred emoji |
| leaving a field | that field's error appears, if there is one |
| posting | a write; on success a toast, an empty card and a return to the clean address `/guestbook`; on failure a toast and **the text stays** |
| typing in the search field | after ~250 ms the phrase lands in the address and travels to the server, the number of entries shown returns to 4 |
| "Newest"/"Oldest" | the order lands in the address, a read from the other end of the guestbook, the number of entries shown returns to 4 |
| "Load N more" | the next piece is read from `offset`; `?shown=` in the address becomes the new total; the button disappears when nothing is left |
| arriving by a link with parameters | the screen starts exactly on what the link says, including the contents of the search field and how many entries are on screen |
| Back, Forward, or a link followed in place | the address wins: the search field is reseeded from it and a phrase still waiting out its pause is cancelled rather than written |
| "Edit" | the card opens an editor with **this** entry's content; the previously open one closes |
| "Edit" while an amendment is in flight | nothing — the action is locked on every card until that amendment settles |
| "Cancel" | the editor disappears, the entry is unchanged |
| "Save" | an amendment; on success a toast and the card returns to reading |
| "Delete" | opens the dialog |
| confirming in the dialog | deletion; an entry being edited, if it is the same one, stops being edited |
| Escape / clicking the backdrop | closes the dialog — **except** while a deletion is in flight |

## Tokens

The shared rules: [`system-states.md`](system-states.md) § Tokens.

## Out of scope for this screen

- **Anything to do with identity.** There is no sign-in, no "my entry", no avatar.
- **A mobile view.** The column narrows with the window, but it is not designed for a phone.

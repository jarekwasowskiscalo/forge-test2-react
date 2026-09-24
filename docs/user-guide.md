# Using the guest book

**For:** the person using the screen.
**Normative source:** [`spec/contexts/guestbook.md`](../spec/contexts/guestbook.md) for the rules,
[`spec/design/ui/guestbook.md`](../spec/design/ui/guestbook.md) for every state of the screen.

> **This feature is an example.** The repository it lives in is a template, and the guest book
> exists so that the change process has something real to travel through. If you have taken
> delivery of a product built on this template, the screen described here has probably been
> replaced — and this page with it.

## What it is

One screen, at `/guestbook`. Visitors leave a signed message; everybody can read, search, correct
and delete. **There is no sign-in**, and that follows through everything below: the book does not
know who you are, so it cannot show you only your own entries and cannot stop somebody amending
yours.

## Leaving an entry

Fill in both fields and submit. Both are required — an entry with a signature and no message is not
an entry, and neither is the reverse.

| Field | Limit |
|---|---|
| Signature | 1 to 80 characters |
| Message | 1 to 1000 characters |

Leading and trailing spaces are trimmed, so a field of nothing but spaces counts as empty. Text in
any script is accepted and stored as written.

The new entry appears at the top, because the book is ordered newest first by default.

## Reading the book

**Search.** Type a phrase to narrow the list. It matches the signature and the message, ignores
case, and a phrase of nothing but spaces narrows nothing rather than returning nothing. The count
above the list tells you how many entries matched, out of how many there are. While a new search
is still on its way the previous results stay on screen, and the count keeps naming the phrase
they belong to — it reads `… — updating…` until the new answer lands.

**Order.** Newest first or oldest first. Nothing else — an order somebody has to think about is one
they will read wrong.

**Reading further.** The list arrives a page at a time; ask for more at the bottom. When there is
nothing further, the control goes away rather than answering an empty page. The address records
how much you have asked for, so the link you copy opens on the same stretch of the book.

## Correcting an entry

Edit it in place, and change either field or both. **The time it was written does not change** — the
book records that this entry was written then and amended since. Both moments are visible, and that
is deliberate: a guest book whose entries can change silently is a guest book nobody can rely on.

Submitting a correction that changes nothing is refused with *"No field was given to change. The
entry is unchanged."* Nothing has been lost; add a change or cancel.

## Deleting an entry

**Deletion is permanent.** There is no undo, no archive and no bin. The entry is gone from the
database, and a restore from backup is the only way back — which takes tens of minutes and returns
the whole book to a moment in the past, not one entry.

Deleting an entry that somebody else has already deleted is answered with *"There is no such entry.
Somebody else may have deleted it."* That is the expected answer rather than an error: two people
looking at the same list is the ordinary case.

## When something goes wrong

| What you see | What happened | What to do |
|---|---|---|
| "There is no such entry. Somebody else may have deleted it." | it was deleted while your screen was open | refresh the list |
| "No field was given to change. The entry is unchanged." | a correction that changed nothing was submitted | change a field, or cancel |
| A field is refused as too long | 80 characters for the signature, 1000 for the message | shorten it — the count is shown as you type |
| The screen sits on a skeleton, then shows an error | the service did not answer | try again; if it persists, whoever operates the environment should read [`troubleshooting.md`](troubleshooting.md) |
| The very first load of the day is slow | outside production the database sleeps when nothing is using it, and takes ten to fifteen seconds to wake | wait, once |

## What the book cannot do

Written down because each is a decision rather than a gap: no accounts and no ownership of an entry;
no moderation, approval queue or reporting; no attachments or images; no replies or threads; no
export. Adding any of them starts with
[`spec/contexts/guestbook.md`](../spec/contexts/guestbook.md), not with the screen.

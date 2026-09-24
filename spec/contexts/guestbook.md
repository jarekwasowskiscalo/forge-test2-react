---
context: guestbook
classification: core
owns: [guestbook_entries]
neighbours: [todo_list:peer:shared-kernel]
processes: [P-01]
screens: [spec/design/ui/guestbook.md]
features: [e2e/suite/features/guestbook.feature]
---

# Guestbook

A bounded context of this system, sharing one rule with the to-do list and nothing else
(§ Boundaries). A guest leaves an entry signed with a name; entries are visible to anybody who
opens the screen; an entry can be amended and it can be deleted.

This is an **example for the template**, not a product. It is here so that every step of the
SDD process has something to show a change travelling through all the layers on — and so that
it can be deleted when your first real feature replaces it.

The shapes on the wire are in [`spec/design/api.md`](../design/api.md); the columns in
[`spec/design/data-model.md`](../design/data-model.md). This document is the rules.

## Language

| Term | What it means here |
|---|---|
| **Entry** | One utterance by a guest: a signature and a message, with the moment it was written and the moment it was last amended. The smallest thing this system stores. |
| **Author** | What the guest signed with. **It is not an identity**: the system authenticates nobody, so a signature is a claim rather than a statement of fact. |
| **Edited** | An entry whose moment of last amendment differs from its moment of writing. A **derived** fact, never stored. |

## `P-01` — leaving and maintaining an entry

There is one flow and it has four steps, each of which works on its own:

1. **Adding.** The guest gives a signature and a message. The system stores the entry, issues
   it an identifier and stamps both moments with the same instant.
2. **Reading.** Anybody sees the entries, newest first by default. A guestbook that has grown
   can be narrowed by a phrase and read a piece at a time (`BR-05`).
3. **Amending.** The signature, the message or both are changed. The moment of amendment moves.
4. **Deleting.** The entry disappears. Permanently.

There are no intermediate states, no lifecycle, no transitions to police. An entry either
exists or it does not.

### `BR-01` — an entry requires a signature and a message

An empty field is not an entry. The refusal also covers a field made only of whitespace:
values are **trimmed before they are measured**, so the signature `"   "` is empty rather than
three characters long.

The order is a rule, not an implementation detail. Measuring before trimming would let through
an entry that turns out to be empty once stored — and then the screen shows a row with nobody
and nothing in it.

**Trimmed of what, exactly, is written down.** Thirty code points: Unicode's `White_Space`
property, the four C0 separators, and the byte order mark. A written set rather than "whatever
the language calls whitespace", because the two languages this system is built in disagree
about six of them — and disagree in both directions, so neither one could be called the right
answer by default. Whitespace *inside* a value is content and is kept; only the ends go.

**A signature is at most 80 code points, a message at most 1000, and the value is normalized
to Unicode NFC before either is counted.** The unit is part of the rule. "Character" is the
word a guest would use and it has no single meaning a machine can hold: the browser's natural
count is UTF-16 code units, the column's and the contract's is code points, and eighty emoji
are eighty of one and a hundred and sixty of the other. Code points won because three of the
four layers already counted them and only one did not.

Normalization is what makes the bound honest to the guest: without it the same eighty letters
are accepted or refused depending on nothing but whether their keyboard produced `é` as one
code point or as `e` followed by a combining accent — a difference nobody can see and nobody
chose.

Both numbers are in the contract ([`api.md`](../design/api.md) § Shapes). The signature's is
also in the column ([`data-model.md`](../design/data-model.md)) and they are **the same number
counting the same things**: the browser measures what the database will accept. That sentence
was written before it was true — the numbers matched and the units did not — and what makes it
true now is one corpus both sides read rather than two literals a test compares. The message's
bound is not in a column — that one is `Text` by decision — so its two homes are the model's
constant and the browser's copy of it.

**The to-do list is held to this rule too.** A task's text is normalized, trimmed of the same
thirty code points and counted in the same unit as a signature and a message; only the bounds
differ, and each context sets its own. The words of the rule have this one home for both
contexts, so a change to the normalization, the trim set or the unit changes the to-do list as
well, and is made with both sets of rules in view ([`todo_list.md`](todo_list.md) § Neighbours).

Rows written before 2026-09-17 were stored as they arrived. Nothing rewrote them, so an old
entry may hold a decomposed letter that a phrase typed the composed way will not find; the
guestbook is this template's worked example and holds no data anybody depends on.

Rejected (decision of 2026-09-17, `cr: historical` — the unit of the bound and the set of
trimmed code points were chosen here, on GitHub issue #28, outside `/forge:sdd`, so there is no
`delta.md` in which to declare the edit and `../design/conventions.md` § When a decision is an
ADR puts the decision in the document whose rule it changes):

- **Count grapheme clusters** — what a guest means by "character", and the only reading that is
  intuitive. Unreachable without a cascade: `author` is `varchar(80)` and Postgres counts code
  points, so eighty graphemes of family emoji is up to four hundred code points and the column
  would refuse what the application had just accepted; `maxLength: 80` in the published contract
  is code points by the JSON Schema specification, so the contract would become false for every
  independent client; and Python has no grapheme segmentation in its standard library, so the two
  sides would have to declare the same version of UAX #29 and the disagreement would return one
  floor up. Choosing it would also have required an Alembic migration changing the column's type.
- **Keep each runtime's own whitespace set and document the difference.** It is one sentence of
  prose and no code, and it leaves the defect exactly where it was: six code points that are
  content in one language and whitespace in the other, in both directions, so neither side's
  default is the right answer and every future reader has to rediscover which is which.
- **Take the INTERSECTION of the two sets rather than the union.** Symmetrical and smaller, and
  wrong in the direction that matters: `U+0085` and the four C0 separators would become storable
  content, so a signature could consist of nothing a person can see and still be accepted.
  Trimming more is the safe direction; trimming less admits values no guest meant to send.
- **Normalize to NFKC rather than NFC.** NFKC folds compatibility characters, so it would rewrite
  what a guest typed — ligatures split, full-width letters narrowed, a superscript digit turned
  into an ordinary one. `BR-01` stores what was written; NFC changes the encoding of a value and
  never the value.
- **Leave the browser alone and widen the server to match it.** It would mean the API accepting
  in UTF-16 code units, which neither the column nor the published contract can express — the
  disagreement would move rather than close.

### `BR-02` — an amendment moves the moment of amendment and never the moment of writing

"When this was written" survives every later correction. That is the only reason an entry has
two moments rather than one.

The consequence the screen rests on: an entry never amended has both moments **equal to the
instant**, by construction rather than by rounding. That is what makes "edited" a fact derived
from a comparison, rather than a column somebody has to keep true separately.

### `BR-03` — deletion is permanent

A deleted entry stops existing. There is no bin, no "deleted" flag, no recovery.

Deleting **somebody else's** entry is possible, and that is a deliberate property of this
example: without authentication there is no such thing as "my entry". See § Deliberate
non-goals.

A second deletion of the same entry **refuses**. Reporting success for an operation that was
not performed is what makes a caller start believing they deleted twice.

### `BR-04` — the guestbook has an order, and it has it both ways

Newest first by default. The order is a promise of the contract, not a side effect of write
order. A tie on the moment of writing is settled by the identifier, so **the order is total**:
two entries from the same instant always come back in the same order.

Without a tie-break, reading a piece at a time can show one entry twice and lose another —
silently, while scrolling, and never in a test that reads one piece.

**The guestbook can also be read oldest first, and then the tie is settled the other way
round.** Reversing only the date would leave two entries from the same instant in the *same*
order relative to each other in both directions — so a guestbook read oldest first would not
be the reverse of the same guestbook read newest first. A piece boundary falling between those
two entries would then lose one of them.

### `BR-05` — the guestbook can be narrowed by a phrase and read a piece at a time

The guest gives a phrase; the system shows the entries containing it — **in the signature or
in the message**, regardless of case. Searching the signature alone would lose half the
matches, and lose them in a way that looks like there being no entries.

The phrase is **trimmed before it is measured**, by the same rule as an entry's values
(`BR-01`): a phrase of nothing but spaces is not a phrase and narrows nothing. Characters that
mean "anything" to the search mechanism are matched **literally** — a guest searching for
`100%` should get the entry about the discount, not the whole guestbook.

A read returns a piece of the guestbook and **two numbers, which are two different facts**:
how many entries match the phrase, and how many entries the guestbook has at all. That is the
only reason the answer is not a bare list — a piece cannot say how many it came from.

The consequence the screen rests on: **"nothing matches" and "the guestbook is empty" are two
different sentences**, and they can only be told apart when both numbers arrive separately.
The first sentence in front of a guestbook full of entries reads like a system that has lost
them.

## Boundaries

This context stores nothing but its own entries, and nothing outside it writes to them. It
borders on one context, as a peer joined by a shared kernel:

| Neighbour | Role | Pattern | What crosses, and what happens when they change it |
|---|---|---|---|
| **To-do list** | `peer` | `shared-kernel` | **The text rule of `BR-01`, and nothing else.** Its words are in this document; what each side keeps, what happens when the rule changes, and where its words go if this context is deleted are written once, in [`todo_list.md`](todo_list.md) § Neighbours, and are not restated here. |

**How a neighbour is declared.** A neighbour is declared as
`<context>:<role>:<pattern>`, and the pattern is the load-bearing half: an arrow says who
calls whom, while the pattern says what happens when the other side changes. The legal
pairings, and why they are the legal ones, are in
[`.specconf/templates/system/context.md`](../../.specconf/templates/system/context.md)
§ Neighbours; `tests/fitness/test_context_declarations.py` refuses every other pairing.

Rejected (decision of 2026-09-07, `cr: historical` — the front matter was rewritten into the
grammar the repository's one reader accepts, and `writes_into` became `neighbours`; framework
and specification shape are edited on the trunk and carry no `delta.md` in which to declare
the edit):

- **Keep `writes_into`.** It records a direction and nothing else. Two contexts can point the
  same arrow and mean opposite things — one translating the other's model at the seam, one
  adopting it whole — and the difference is exactly what the next change needs to know. A
  direction is the half of the boundary that was already obvious from the code.
- **Keep the block-sequence front matter.** It was not merely unread: `frontmatter.py` —
  the repository's only front-matter reader — **refuses** it, because block sequences are
  outside the grammar it accepts. So the header was illegal by this repository's own rule and
  nothing said so, which is what a declaration nobody parses always comes to.
- **Add a second, more permissive parser for context documents.** Two readers of one shape is
  the failure `tests/_golden_set.py` already exists to prevent: the hand-copied twin diverged
  in return type and in exception type before anybody noticed. One reader, one grammar.
- **Nest the neighbour rows as a mapping**, which is what YAML would suggest. The grammar
  takes flat scalars and inline lists on purpose — a header of a few keys does not justify a
  third-party parser in the one package that has to keep working when the environment is
  broken. A colon-separated triple is readable, greppable and parses with `str.split`.

## Deliberate non-goals

Named, so that an absence does not read as an oversight:

- **Authentication and authorisation.** There are no accounts, sessions or roles. Anybody may
  add, amend and delete any entry. The signature is a claim. A product that needs this starts
  with an ADR and hangs the check on the router aggregate — which file that is has one home,
  [`design/conventions.md`](../design/conventions.md) § Backend — where a file goes.
- **Moderation.** There are no reports, no hiding and no word list.
- **Search relevance.** A phrase is either in the text or it is not. There is no inflection, no
  synonyms, no ranking — `colour` will not find `coloured`, and results come back in the
  guestbook's order rather than by how well they match. A product that needs this starts with a
  full-text index and an ADR.
- **CSRF protection.** There is no cookie or header to forge, because there are no sessions. A
  protective layer that protects nothing while looking like protection is worse than none — this
  project once had exactly that.

Rejected (decision of 2026-09-08, `cr: historical` — the router aggregate's path had two homes;
[`../invariants.md`](../invariants.md) § Deliberate non-goals recorded on 2026-09-07 that a
placement fact has one, and this document was the copy that decision missed, corrected here on
the trunk with no `delta.md` to declare the edit in):

- **Keep naming `app/api.py` here.** True today and wrong on the day the aggregate moves. A
  non-goal says what the system does not do; where the check would hang if the non-goal were
  lifted is a placement fact, and placement facts have one home.

## What proves this

`e2e/suite/features/guestbook.feature` — scenarios in business language, without a single
HTTP code and without a single path, readable by somebody who does not write code. Every rule
above has its scenario there, and two have several: `BR-02` — one for what moves and one for
what must not; `BR-05` — one each for a match in the signature, a match in the message, case,
a search with no matches, the other end of the guestbook, both numbers, and the fact that
successive pieces cover the guestbook exactly once.

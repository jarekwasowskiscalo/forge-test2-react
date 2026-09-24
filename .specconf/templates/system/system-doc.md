# <Area>

The shape of a document under `spec/design/`. Not a form to fill in — a set of properties
every one of them has.

## Present tense, normative

Say what **is**, not what was decided or what is planned. "Endpoints return JSON", never "we
decided to return JSON" and never "endpoints will return JSON".

A reader has to be able to open any paragraph and know that it describes the system as it is
today. That is true only when nothing here is historical.

## One rule per paragraph

A paragraph stating two rules gets edited for one of them and quietly changes the other.
Separate them.

## The "why" is a link, never a subordinate clause

Where a rule has a justification, the justification lives in an ADR and the rule links to it:

> Technical identifiers are UUIDs
> ([`data-model.md`](../design/data-model.md) § Identifiers).

And not:

> Technical identifiers are UUIDs, because pasting from Excel collided and changed on a
> correction, and auto-incremented numbers would leak the volume…

That second shape is what made the pre-framework steering notes impossible to maintain:
rewriting a rule destroyed the justification, so nobody could tell a settled decision from an
accident. Keep the rule editable and the justification immutable, in different files.

## Name the enforcement

Where something checks a rule, say so and name it:

> …checked by the layering test under this stack's fitness suite.

A rule nothing enforces is a hope, and saying which test holds it tells the next person what
will break if they change it.

## Incidents stay

Where a rule exists because something broke, the incident stays in the text — what failed,
where and what it cost. This project already writes that way; `scripts/check.sh` names the
failure behind every gate it runs.

This prose is not decoration. It is a regression suite written in prose, and it is the main
thing standing between a rule and somebody who will "simplify" it because the cost is
invisible from the diff.

## No dates, no changelog

History lives in git and in the ADRs. A document that collects "since 2026-08 we now do…"
becomes a journal nobody trusts, because a reader cannot tell which line is current.

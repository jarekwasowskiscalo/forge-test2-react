# Invariants

Things that must always be true. An invariant has no date and no rejected alternative — if it
had one it would be a decision and would belong in [`ADR/`](ADR/).

**These identifiers are load-bearing.** An identifier from here is never renamed or reused; a
superseded invariant keeps its heading and gains a "Superseded by" line. A hole in the
numbering is information, not mess.

**But a hole is information only when what was in it can still be read, and one of them fails
that.** Gate `G9` is cited in this repository solely as a precedent for withdrawal — in
[`design/conventions.md`](design/conventions.md) § Scripts, in `stages.py` and in its test —
and **what it held is stated by no document, no comment and no commit**. What is left is the
information "something was here" without the information "what", which is exactly as much as
no entry at all carries. Hence the rule for the next withdrawal: **a withdrawal is recorded
together with one sentence about what the gate held.** `G13` has one (the decision about
POSIX scripts: the `.sh` and `.ps1` twins must change in one diff) and that is the pattern;
`G9` does not, and can no longer be reconstructed.

### The rule, amended for gate names

**An identifier whose subject is fixed by a document is never renamed. A gate name is renamed
only together with a mapping table that keeps every archived citation readable.** The two are
not the same kind of identifier, and treating them as one is what this amendment corrects: an
invariant's number is a handle on a *decision*, while a gate's identifier is a handle on a
*check that still runs* and is read every time it goes red. A handle nobody can decode is a
cost paid on every reading.

Rejected (decision of 2026-09-06, `cr: historical` — the gates were renamed from `G1` to `G20`
into descriptive names, which is the one thing the rule above forbids, so the rule is amended
here rather than quietly broken; framework changes are made on the trunk and carry no
`delta.md` in which to declare the edit):

- **Rename without amending this rule.** The rename would then stand as a violation of a
  document saying it cannot happen — which teaches that the rules here are advisory, and that
  is more expensive than any gate name.
- **Rename and drop the old codes from history.** The audits under `spec/rationale/` and the
  notes under `retro/` record what was true on a date. Rewriting their nouns makes them agree
  with today at the cost of no longer being records.
- **Extend "never renamed" to cover gates explicitly, and keep the numbers.** Consistent, and
  it settles the cost in exactly the wrong direction: the identifiers a person reads most
  often would be the ones guaranteed to stay unreadable.

Consequences: gate names are the single renameable identifier space in this repository, and the
price of that is the mapping table in
[the process's `spec_gates.py`](https://github.com/Scalo-Sales-Engineering-Consulting/claude-marketplace/blob/main/plugins/forge/skills/_shared/sdd/spec_gates.py), where every gate declares the code it
carried, held to the register by `test_sdd_spec_lint.py`. `D-*`, `R-*`, `CR-*` and the headings in this file are
unchanged: never renamed, never reused.

Rejected (decision of 2026-09-10, `cr: historical` — the forge plugin deleted its `docs/` tree
on 2026-09-10 and kept only what the process runs on, so `sdd-reference.md` and its table of
old numeric codes exist nowhere; the mapping from a retired code to a gate's name lives in the
gate register itself, `spec_gates.py`, where every gate declares the code it carried, and the
links here name that. Framework changes are made on the trunk and carry no `delta.md`): leaving
links that return 404, or copying the mapping into this document — the second home this section
argues against.

**What this file holds today.** Deliberate non-goals and the rule about the rules themselves —
the things that have no version. The data invariants `D-01`…`D-03` moved out to
[`contracts/invariants/guestbook.md`](../contracts/invariants/guestbook.md); the section below
says why.

---

## Data invariants

**Moved to [`contracts/invariants/guestbook.md`](../contracts/invariants/guestbook.md),
2026-09-02.** The identifiers `D-01`…`D-03` were not renamed or reused and will not be — after
this change the `D-*` space has a single owner.

What they held, one sentence each, so the hole can be read without opening the other file —
the rule at the top of this document demands exactly that:

- **`D-01`** — a domain entity has one row from creation to end, not a copy in an "archive
  sheet", where history is destroyed by separation rather than by deletion.
- **`D-02`** — a fact belonging to another entity is pointed at, not transcribed; the
  exception is a deliberate historical snapshot, which has to be named as one.
- **`D-03`** — every primary key is a UUID generated on the application side, never a number
  from a sequence ([`design/data-model.md`](design/data-model.md) § Identifiers).

**Why they left.** A data invariant is a statement about a system boundary — about what may be
relied on without looking inside — and a boundary is a versioned contract (constitution,
article VI). This file stayed with what has no version: the rule about the rules themselves,
and the deliberate non-goals.

**The move closed, in passing, a gap this section used to admit outright.** The previous
wording said that `D-01`…`D-03` were held by the data model and by the decision about UUIDs,
"rather than by a test that names them". The new home does not accept an invariant without a
`**Witness:**` and a `**Kind of evidence:**` line, and the witnesses exist: sweepers over
`Base.metadata` in `tests/fitness/test_data_invariants.py` and a property with a generator in
`tests/unit/test_data_invariant_properties.py`.

**The editing route has not changed, and does not change for either half.** The rule from
§ Deliberate non-goals — "every edit to this file within a change cycle belongs to the
convergence round" — is inherited by the new home: the write set of `review-converge` covers
`contracts/` for the same reason it covers `spec/`.

**Which stage's convergence round writes a new data invariant is settled by its witnesses.** The
new home accepts no invariant whose `**Witness:**` names a test that does not exist
(`tests/fitness/test_invariant_witnesses.py`). So an invariant decided in design whose witnesses
the implementation stage writes is written by the first convergence round after they exist —
the `spec_sync` stage's — and until then the design document that decided it states the call,
and `spec/design/testing.md` names its witnesses and that round. The user decided it so in
`CR-2609-823a` (`Q-21`): "stated in the data model now and written into the data-rules folder at
the reconciliation stage, once its tests exist."

---

## Deliberate non-goals

Standing product decisions, not oversights: they bind every change exactly as an invariant
does, and that is why they live here. Adding any one of them is a change with its own
requirements, not a gap somebody spotted.

**Lifting a non-goal has one route, and that route is written here, because its absence cost
four authors of one stage.** A non-goal is lifted by **a human decision recorded in a change
record** (question and answer in `requirements.md`), and an ADR names it only when it is
cross-cutting ([`design/conventions.md`](design/conventions.md) § When a decision is an ADR).
The striking-out is done by the **stage's convergence round**, in this file and in the same PR
as the code, because the author of a design document does not have this path in their write
set — and does not have it deliberately: a document standing above `spec/design/**` cannot be
changed by what stands below it. A lifted item **stays** with its heading and gains a "lifted
by `<CR>`" line together with its former wording; it is never renamed or deleted.

**This route applies to the whole file, not only to the striking-out.** **Every edit to
`spec/invariants.md` within a change cycle** belongs to the convergence round — lifting a
non-goal, adding an invariant, fixing a broken cross-reference. No fan-out author gets this
path in their write set; an author who sees a divergence here **reports it as a finding and
does not try to fix it**. The rule is in this wording because the previous one — written from
a single action — did not catch the second case on the same change.

- **Authentication and authorisation.** There are no accounts, sessions or roles; anybody may
  add, amend and delete anything the system stores: any guestbook entry and any to-do task. The
  signature under an entry is a claim rather than an identity, and no document or screen may assign it a meaning it does not have. A product
  built from this template lifts this non-goal with an ADR and hangs the check on **the router
  aggregate** — once, never per router: a router added later would be left open until somebody
  happened to remember. Which file that is has one home, and it is
  [`design/conventions.md`](design/conventions.md) § Backend — where a file goes.
Rejected (decision of 2026-09-07, `cr: historical` — this file named the router aggregate by
path, and the path changed when the tree was recut by bounded context; the recut is recorded in
[`design/architecture.md`](design/architecture.md) § What a new feature adds, and this document
is edited from the trunk, where no `delta.md` exists in which to call the edit editorial):

- **Update the path and keep it here.** It is the smaller edit and it puts this document back
  in the business of tracking where a file lives — which it would then have to do again on
  every later move. A non-goal is a statement about what the system does not do; the file that
  would enforce it if the non-goal were lifted is a placement fact, and placement facts have
  one home.

- **CSRF protection.** There are no sessions, so there is no cookie or header to forge. This
  project once had a layer that echoed an `X-CSRF-Token` header no service set or checked:
  **it protected nothing and looked to an auditor exactly like protection**. A named non-goal
  is more honest than a stub.
- **Content moderation.** There are no reports, no hiding and no word list.
- **Paging and search.** ~~`GET` returns everything. For an example that is right; `BR-04` has
  already prepared the total order that paging will stand on when it is needed.~~ **Lifted
  outside the SDD process, 2026-08-31**, together with replacing the screen with the mock-up:
  `GET` accepts `q`, `sort`, `limit` and `offset`, and the rule is `BR-05` in
  [`contexts/guestbook.md`](contexts/guestbook.md).

  **The lifting was incomplete for one turn, and that is worth recording.** The rule changed in
  the context, in the contract and in the code, and this item stayed — so a document that binds
  every change was saying something untrue, and no gate caught it. `delta-coverage` holds that a changed
  specification file is covered by a delta; it does not hold that a file which **should**
  change did change. Work outside `/sdd` has no convergence round, which is the only place
  this file may be edited — and that is exactly what was missing.
- **A mobile version.** The screen is a single column up to 860 px and narrows with the
  window, but it is **not designed for a phone**: a mobile view is a separate decision with its
  own requirements, not a scaling of what is there. (Wording corrected 2026-08-31: it spoke of
  a 1440×900 frame, which has not existed since the screen was replaced with the mock-up.)
- **A data retention policy.** An entry, like a to-do task, lives until somebody deletes it. A product storing
  personal data needs a policy here before it can be specified in code.
- **A second database engine.** The application runs on PostgreSQL and only on PostgreSQL
  ([`design/architecture.md`](design/architecture.md) § One engine). This is not a lack of
  portability but a refusal to maintain a mode in which a green test says nothing about
  production. A machine without Docker points at its own Postgres; a machine with neither gets
  a **named gap**, not silent green.

## The manual this document cites has moved

The reference tables it points at travel with the process now — the gate register with its retired codes is [the process's `spec_gates.py`](https://github.com/Scalo-Sales-Engineering-Consulting/claude-marketplace/blob/main/plugins/forge/skills/_shared/sdd/spec_gates.py) — and not in `docs/`. `docs/` holds
the documentation of the **system** — setting up the AWS account, deploying, configuring,
operating it — and the manual for the **change process** moved beside the framework it
describes.

Rejected (decision of 2026-09-06, `cr: historical` — the rule and its rejected alternatives
live in one place, and this is a pointer to it rather than a second copy; framework changes are
made on the trunk and carry no `delta.md`): recording the argument again here. See
[`design/conventions.md`](design/conventions.md) § Documentation — where a document goes.

Rejected (decision of 2026-09-09, `cr: historical` — the reference tables moved a second time
on the same day: out of the process's old home here and out of this repository, into the plugin that now
carries the process. The relative links this document used named a path no clone of this
template has. Framework changes are made on the trunk and carry no `delta.md`): restating the
gate names here so this document could stop citing anything. The whole point of the citation is
that the names have one home, and a copy of them here is the drift it exists to prevent.

Rejected (decision of 2026-09-10, `cr: historical` — the reference tables moved a third time,
and this time not by path but by owner: the marketplace that carries them is now in the Scalo
organisation. The absolute links this document used named the organisation it was forked out
of. Framework changes are made on the trunk and carry no `delta.md`): pinning the citations to
that fork because it still answers today. The block above rejected a link into a tree no clone
has; a link into a repository the reader cannot open fails in exactly the same way, one
permission check later.

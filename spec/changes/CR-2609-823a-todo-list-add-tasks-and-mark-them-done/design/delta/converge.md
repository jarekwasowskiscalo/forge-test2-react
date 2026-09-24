# Delta fragment — `review-converge`

*Written by the convergence round of coherence pass 1, `requirements` stage. The requirements
stage has no fragment directory of its own, and `close_stage` assembles `delta.md` from
`design/delta/` and `reconcile/delta/` alone, so this entry sits in the first of them. The
edits this round made to `requirements.md` and `impact.md` are inside the change record and
need no entry.*

- `MODIFIED` `spec/invariants.md` § Deliberate non-goals, "Authentication and authorisation" and
  "A data retention policy"
  **Was:** "anybody may add, amend and delete any entry", and "An entry lives until somebody
  deletes it." Both were the guestbook's noun, written when an entry was the only thing the
  system stored.
  **Now:** "anybody may add, amend and delete anything the system stores: any guestbook entry and
  any to-do task.", and "An entry, like a to-do task, lives until somebody deletes it."
  **Why:** COH-requirements-5. `requirements.md` § Non-Goals cited both standing non-goals as
  covering tasks while their wording covered entries alone ("by intent yes, by wording no",
  Self-check 23). The authentication half: the user confirmed the intent at the `Q-9` read-back
  (`brainstorm.md` § Deliberately out of scope: the standing non-goal "holds for the to-do list as
  it does for the guestbook: anybody may add, tick, edit and delete any task"). The retention
  half: the first convergence round left it worded for entries, because no user decision then
  extended it to tasks and `requirements.md` carried it as assumption `A-2` ("nothing removes a
  task except a person deleting it, with no expiry and no retention policy, as for a guestbook
  entry"). The user approved `requirements.md` at the stage gate on 2026-09-24, and that document
  says of its named assumptions that "the user confirms or overrules each one at the approval of
  this document"; none was overruled, so `A-2` is a human decision and the retention item now
  names tasks too. Neither rewording lifts anything, so neither gains a "lifted by" line.
  **ADR:** none — it rewords two standing non-goals so that they name what the system now stores,
  and it lifts nothing and adds no rule.
  **Requirements:** CR-2609-823a/R-1, CR-2609-823a/R-4, CR-2609-823a/R-6, CR-2609-823a/R-7

# Delta fragment — `review-converge`

*Written by the convergence round of coherence pass 1, `requirements` stage. The requirements
stage has no fragment directory of its own, and `close_stage` assembles `delta.md` from
`design/delta/` and `reconcile/delta/` alone, so this entry sits in the first of them. The
edits this round made to `requirements.md` and `impact.md` are inside the change record and
need no entry.*

- `MODIFIED` `spec/invariants.md` § Deliberate non-goals, "Authentication and authorisation"
  **Was:** "anybody may add, amend and delete any entry". That was the guestbook's noun, written
  when an entry was the only thing the system stored.
  **Now:** "anybody may add, amend and delete anything the system stores: any guestbook entry and
  any to-do task."
  **Why:** COH-requirements-5. `requirements.md` § Non-Goals cited this standing non-goal as
  covering tasks while its wording covered entries alone ("by intent yes, by wording no",
  Self-check 23). The user confirmed the intent at the `Q-9` read-back (`brainstorm.md`
  § Deliberately out of scope: the standing non-goal "holds for the to-do list as it does for the
  guestbook: anybody may add, tick, edit and delete any task"). The rewording lifts nothing, so
  it gains no "lifted by" line. The retention item ("An entry lives until somebody deletes it")
  is deliberately left as it was. No user decision extends it to tasks, and `requirements.md`
  carries that half as assumption `A-2`.
  **ADR:** none. It rewords a standing non-goal so that it names what the system now stores, and
  it lifts nothing and adds no rule.
  **Requirements:** CR-2609-823a/R-1, CR-2609-823a/R-4, CR-2609-823a/R-6, CR-2609-823a/R-7

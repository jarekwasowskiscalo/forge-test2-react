# <do the thing>

**For:** <who reaches for this, in one phrase>
**Normative source:** <the `spec/` or `docs/` document that owns the facts this uses>

Not a form to fill in — the three properties every runbook in `docs/runbooks/` has, and the
reason each one is there. The shape is declared in
[`../../../spec/design/conventions.md`](../../../spec/design/conventions.md) § Documentation —
where a document goes, and the `documentation-set` gate refuses a file here without the first
and the third.

## When to use this

The situation, **and the situations this is not for.** A runbook reached for in the wrong
situation does more damage than no runbook: the two nearest neighbours are named here, with the
one sentence that distinguishes them. Where a wrong choice is expensive and irreversible — a
restore rather than a rollback — say what it costs, here, before the first step.

Say what the reader needs before starting: an access, a decision somebody else has to take, a
person who has to be reachable.

## Steps

Numbered, in the order they happen. Each one:

- **A command through `scripts/`** (the constitution, article XII), or an action in a named
  console. Never a raw tool the stack profile refuses — a step that teaches somebody to walk
  past the guard has removed it. A console or a vendor CLI nothing wraps is a named exception,
  and the runbook says so where it uses one.
- **What it prints when it works**, so the reader can tell.
- **Where it can fail in a way worth naming**, at that step rather than in a section at the end.
  An operator reads a runbook one step at a time.

Steps that discard something — writes, an environment, data — say so in the step, in the
imperative, before the command.

## How you know it worked

The observable that ends the procedure. **This section is not optional and is the one that gets
left out.** Without it the person who did not write this cannot tell finished from
half-finished, and half-finished is how an environment ends up in a state nobody planned for.

Where the procedure only *contains* a problem rather than resolving it, say that too: what is
still true afterwards, and what has to happen next.

## Afterwards

Optional. What to record, what to clean up, and what somebody should do differently next time —
the second person to run this will want the numbers the first one measured.

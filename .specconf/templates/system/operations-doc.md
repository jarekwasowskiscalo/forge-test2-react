# <the subject>

**For:** <who reads this, in one phrase>
**Normative source:** <the `spec/` or `contracts/` document that owns the facts this explains>

Not a form to fill in — the properties every document under `docs/` has. The rule is
[`../../../spec/design/conventions.md`](../../../spec/design/conventions.md) § Documentation —
where a document goes; this stack's documentation fitness test holds the claims to the code,
and the `documentation-set` gate holds the shape.

**One subject, named after the subject.** `configuration.md`, `monitoring.md` — never `misc.md`,
and never a number in the filename. A directory that numbers its documents has stopped being
able to say what is in them.

**Nothing here binds.** Where a rule holds, it holds because it stands in `spec/` or
`contracts/`, and this page **cites the one that owns it** rather than restating it. That is
what the `**Normative source:**` line above is: a descriptive document read as normative is a
second home for one rule.

**Name things exactly.** The component, the endpoint, the variable, the column, the resource.
This is the opposite of the rule for user-facing documentation, and deliberately: vagueness in
an operations document is not tact, it is a reader searching a console for something you could
have named.

**Say what does not exist.** The absences are as operational as the presences — no alerting, no
authentication, a procedure nobody has ever performed. A page that implies coverage it does not
have is worse than no page, because it stops somebody adding the thing.

**Every instruction invokes a script.** The constitution, article XII. A procedure — anything a
person carries out on a live environment — is not a section here at all: it is a file in
`docs/runbooks/`, from `runbook.md` beside this one.

**No credential, account identifier or ARN carrying one.** The constitution, article XI, in the
tree most likely to be handed to somebody outside the team.

## <the first question this page answers>

Prose, tables where a table is the honest shape — a variable and its default, an environment and
its numbers, a symptom and its cause. Link rather than repeat: the fact's home is one hop away
and it will be edited there.

# Runbooks

**For:** whoever has to make something happen to a running environment.
**Normative source:** [`spec/design/conventions.md`](../../spec/design/conventions.md)
§ Documentation — where a document goes.

A procedure that somebody carries out on a live system lives here, one file per procedure,
named after the procedure. Nothing else does: an explanation belongs in the subject document
one level up, and a rule belongs in [`spec/`](../../spec/README.md).

## The shape

Every file in this directory has three parts, in this order, and none of them is optional:

1. **`## When to use this`** — the situation, and the situations this is *not* for. A runbook
   reached for in the wrong situation does more damage than no runbook.
2. **The steps, numbered.** Each one a command through [`scripts/`](../../scripts/) — the
   constitution, article XII — or an action in a named console, with what it prints when it
   works.
3. **`## How you know it worked`** — the observable that ends the procedure. Without it the
   person who did not write this cannot tell finished from half-finished, and half-finished is
   how an environment ends up in a state nobody planned for.

Where a step can fail in a way worth naming, it says so at that step rather than in a section
at the end: an operator reads a runbook one step at a time.

## The procedures

| Runbook | When |
|---|---|
| [`incident-first-response.md`](incident-first-response.md) | something is broken and you do not yet know why. **Start here** |
| [`roll-back-a-release.md`](roll-back-a-release.md) | the version now serving is worse than the one before it |
| [`release-to-production.md`](release-to-production.md) | putting the current trunk in front of users |
| [`run-a-migration.md`](run-a-migration.md) | preparing a schema change, or dealing with one that failed in a deployment |
| [`restore-the-database.md`](restore-the-database.md) | data has been lost. Slow, coarse, and never performed on this stack |
| [`preview-environment.md`](preview-environment.md) | putting a branch in front of somebody, and taking it down again |
| [`rotate-database-credentials.md`](rotate-database-credentials.md) | the master password has to change |

Two of these are one decision apart and it is worth knowing which is which before you need either:
a bad **deploy** is undone in seconds by a rollback, and only bad **data** needs a restore, which
returns the whole book to a moment in the past.

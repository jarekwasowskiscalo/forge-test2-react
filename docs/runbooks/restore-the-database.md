# Restore the database

**For:** whoever has lost data.
**Normative source:** [`backup-and-recovery.md`](../backup-and-recovery.md) for what is backed up
and for how long.

> **This procedure has never been performed on this stack.** It is written from the Terraform and
> from Aurora's documented behaviour. Expect it to take longer than you think, and read it all the
> way through before starting anything.

## When to use this

When guest book entries or to-do tasks have been damaged or deleted and you want them back. Only
then — this is slow, disruptive and coarse.

**Not for a bad deploy.** If the code is wrong but the data is intact,
[`roll-back-a-release.md`](roll-back-a-release.md) takes seconds. Establish which of the two you
have before doing anything: a restore returns the *whole database*, both lists, to a moment in the
past. Every entry written and every task added, ticked or corrected since that moment is lost by
the act of recovering.

**Not available past the window.** 14 days on production, 7 on stage, 1 on a preview. Beyond that
there is no copy of anything.

## Before you start

1. **Write down the target moment**, in UTC, and how you decided it. Everything after it will be
   gone; everything before it comes back. If you are unsure, pick earlier — you can restore twice,
   and you cannot un-lose.
2. **Decide whether to stop writes.** There is no maintenance mode and no read-only switch. The
   crude, effective lever is to set the API function's reserved concurrency to 0, which makes the
   service refuse rather than accept writes you are about to discard. It is an apply, and it is an
   outage — a deliberate one, which is better than an inconsistent recovery.
3. **Tell whoever needs to know** what the target moment is, because that is the sentence they will
   have to repeat: "anything written after 11:04 is gone".

## Steps

1. **Restore to a new cluster**, in the AWS console or the CLI: RDS → the cluster → Actions →
   *Restore to point in time*. Aurora **always** restores into a new cluster; it never overwrites a
   running one, and there is no option that does.

   Give it a name you will recognise as temporary, and put it in the same VPC and subnet group as
   the original — otherwise nothing in this account can reach it.

   This is the long step: expect **20 to 45 minutes**. Note the real figure and put it in
   [`backup-and-recovery.md`](../backup-and-recovery.md), replacing the estimate.

2. **Check that what came back is what you wanted**, before touching anything live. Connect with the
   master credentials from Secrets Manager (`sdd-guestbook-<env>/database/master`) and count the
   rows of `guestbook_entries` and of `todo_tasks`. The
   restored cluster is reachable only from inside the VPC, so this is done from a bastion or a
   throwaway Lambda in the same subnets — there is no public endpoint anywhere in this stack.

3. **Choose how to finish**, and say which one you chose in the incident note:

   **A — point the environment at the restored cluster.** Faster. Terraform's state now describes a
   cluster that is not the live one, and it stays wrong until you reconcile it — which is a second
   piece of work, on the same day, not "later".

   **The restored cluster is at the schema of the target moment too.** A moment earlier than the
   first deployment that carried the to-do list has no `todo_tasks` table: its `alembic_version`
   names a revision older than `5c58af1f8e8a`, the one that creates it. Served by a version that has the to-do list, that
   database answers the to-do screen with a failure until a migration has run against it. Under A,
   check `alembic_version` in step 2 before you point anything at it.

   **B — copy the data into the running cluster.** `pg_dump` from the restored cluster,
   `pg_restore` into the live one. Slower, keeps Terraform truthful throughout, and it is the only
   option when only *part* of the data is wrong, because you can copy the rows you need instead of
   the whole database. The two lists are two tables with no key between them, so when only one
   list is wrong, B can copy that table alone and leave the other list as it is now.

   B is the default. Take A only when the whole database is wrong and the clock matters more than
   the tidiness.

4. **Put writes back on** — restore the reserved concurrency you changed in step 2 — and confirm the
   application answers.

5. **Delete the restored cluster** once you are certain, and not before. It costs money, and a
   second cluster nobody remembers creating is its own future incident.

## How you know it worked

The entries or tasks that were lost are visible on their screen, the application is accepting writes
again, and a collection read returns the expected count. Terraform agrees with reality:

```bash
./scripts/infra.sh <env> plan
```

An empty plan is the end of this procedure. A plan that wants to change the database is step 3A left
unfinished.

## Afterwards

Write down the target moment, which option you took, the real duration, and what was lost. Then do
the exercise in [`backup-and-recovery.md`](../backup-and-recovery.md) § What to do about the untested
part on stage, while it is fresh — the second time this is needed, somebody will want the numbers to
be measurements.

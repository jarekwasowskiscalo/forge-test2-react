# Run a migration

**For:** whoever is changing the schema of a deployed database, or dealing with one that failed.
**Normative source:** [`spec/design/data-model.md`](../../spec/design/data-model.md) § Owner of the
schema — `alembic/versions/` owns it, and the application never calls `create_all()`.

## When to use this

A migration is **not run by hand against a deployed environment**. It runs as step 3 of a
deployment, before the new code goes live, by invoking that environment's migration function. This
runbook covers the two things a person actually does: getting a revision ready, and dealing with one
that failed in a deployment.

For the local database, `./scripts/db.sh` is the whole interface and none of this applies.

## Steps — preparing a revision

1. **Draft it from the model change.**

   ```bash
   ./scripts/db.sh revision "what changed"
   ```

   Autogeneration is a **first draft, not an answer**. It reliably misses data movement, and it will
   happily write a destructive step it has no way of knowing is destructive.

2. **Read the `upgrade` and the `downgrade` as a pair.** A revision that cannot be described going
   backwards is one that has to be split.

3. **Prove it runs from empty.**

   ```bash
   ./scripts/db.sh reset
   ```

   Destructive locally, and that is the point: it drops the database and migrates from scratch, so
   a revision that only works on *your* database fails here.

4. **Prove it runs against data.** Stage's database is never reset, so migrations accumulate on it
   exactly as they do on production. That is what makes stage worth deploying to first — a migration
   that works on an empty database and not on one with data is the migration stage catches.

5. **Deploy to stage**, and only then release. Article X of
   [`spec/constitution.md`](../../spec/constitution.md): between two steps the application works.

## Steps — when a deployment's migration fails

1. **Nothing is live.** The alias has not moved and the previous version is still serving. The
   script says so in as many words. Do not roll back — there is nothing to roll back.

2. **Read the real message.** The workflow log carries the invocation payload; the script searches
   it for `errorMessage` because **a Lambda that raises still returns 200**, so the step would
   otherwise look green.

3. **Find out how far it got.**

   ```
   /aws/lambda/sdd-guestbook-<env>-migrate
   ```

   Alembic logs each revision as it applies it. A migration that fails part way has applied the
   revisions before the failing one and they are not rolled back.

4. **Decide which of the three situations you are in.**

   | Situation | What to do |
   |---|---|
   | The revision is wrong | fix it, cut a new revision if the broken one already applied part of its work, and deploy again |
   | The revision is right and the environment is not (a lock, a timeout, capacity) | deploy again. The applied revisions are skipped |
   | The revision applied and something *after* it failed | the schema is ahead of the code, which is the safe direction. Deploy again once the later step is fixed |

5. **Never edit an applied revision.** Its identifier is in the database's `alembic_version` table on
   every environment that ran it. Change it and stage and production diverge silently. A mistake in
   an applied revision is corrected by a new revision.

## How you know it worked

The deployment continues past step 3 and the alias moves, `/api/health` reports the new version, and
a collection read returns entries. Locally, `./scripts/db.sh status` reports the head revision
applied and nothing pending.

## What can go wrong that this does not cover

A migration that takes long enough to matter. The migration function's timeout is 300 seconds and
nothing in this schema comes near it — but a table lock on a large table is the failure mode to
expect if that changes, and it stops the deployment rather than the application, because the alias
has not moved yet.

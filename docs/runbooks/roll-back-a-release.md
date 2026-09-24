# Roll back a release

**For:** whoever has a bad version serving traffic.
**Normative source:** `scripts/deploy.sh --help`, which is where the semantics are defined;
[`deployment.md`](../deployment.md) § What a rollback is, and what it is not.

## When to use this

When the version now serving is worse than the one before it, and you want the previous one back in
seconds. It is the right first move for almost any production incident caused by a deploy: it is
fast, it is reversible, and it buys time to diagnose.

**It is not for bad data.** A rollback moves code and touches nothing in the database. If entries
have been damaged or deleted, this will not bring them back — see
[`restore-the-database.md`](restore-the-database.md), and read it before doing anything else,
because a restore's recovery point is "a moment in the past" and every minute of new writes widens
what you lose.

**It is not for a failed deploy.** If the deployment stopped at the migration step, nothing went
live and the previous version is still serving. There is nothing to roll back.

## Steps

1. **Record what is serving now**, before you change it.

   ```bash
   curl -s https://<prod>/api/health
   ```

   Keep the `version`. You will want to know what you rolled away from, and the deploy log for that
   version is the diagnosis you have not done yet.

2. **Actions → Deploy → Run workflow**, environment `prod`, mode `rollback`.

   This builds nothing, applies nothing and migrates nothing. It moves the Lambda alias back to the
   **last version that actually served this environment and passed its smoke** — read from the
   release manifest, not worked out from the version numbers — and re-runs the smoke.

   **It can refuse, and a refusal is not a failure to work around.** The two you are most likely to
   meet: the current version is not in the manifest, which is what a deploy that moved the alias and
   then failed its smoke leaves behind; or everything before it has already been rolled back. Both
   print the `aws lambda list-versions-by-function` / `aws lambda update-alias` pair. Running that
   pair by hand is a legitimate answer — what the script will not do is choose for you.

3. **Approve the `prod` gate** if the environment has a required reviewer.

4. **Confirm the alias moved.**

   ```bash
   curl -s https://<prod>/api/health
   ```

   `version` is the previous release.

5. **Hard-refresh the screen in a browser.** The SPA was *not* rolled back — see below — so this is
   where you find out whether the older API and the newer screen get along.

## How you know it worked

`/api/health` reports the previous version, the screen loads, and every read-only endpoint the
contract declares answers with the envelope it promises. The incident is contained, not resolved:
the next step is a fix that goes forward.

**One reading to keep in mind if the rollback's smoke goes red.** It asks the questions of the
branch you dispatched from, not of the version it rolled to. If the trunk has added an endpoint
since that release, the older version is being asked for something it never promised — which looks
exactly like a broken rollback and is not one. The failing endpoint is named in the log; check it
before you conclude the older version is bad.

## What it did not undo, and what to do about each

**The schema.** Deliberately. Migrating before moving the alias is the whole shape of a deployment,
precisely because old code against a new schema ignores a column it does not know about and carries
on. That is what makes rolling the code back safe on its own. A migration run backwards on a live
database is far more dangerous than the thing it would be undoing; **if a revision has to go, it
goes forward, in a new revision.**

**The SPA.** `index.html` in S3 is overwritten by each deploy, so the browser keeps the newer shell
while the API serves the older version. The bundles that shell names are still there — publication
deletes nothing — so the screen loads rather than going blank. The API contract is what makes
that survivable rather than lucky — but if the bad release changed the contract, the screen is now
calling an endpoint the rolled-back API does not have, and the fix has to go forward rather than
back. That is the case where a rollback is not enough, and it is worth checking early: the failing
requests will be 404s or 422s from the browser, not errors in the application log.

## Then

Roll forward. A rollback is followed by a fix, not treated as one — the version that was rolled away
from is still the head of the trunk, and the next release will deploy it again unless something
changes.

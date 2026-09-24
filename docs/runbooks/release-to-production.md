# Release to production

**For:** whoever is putting a version in front of users.
**Normative source:** [`deployment.md`](../deployment.md) for what a deployment does and in what
order.

## When to use this

To put the current trunk into production. Not for stage — that is a Deploy dispatch, and it should
have happened already. Not for an urgent fix to something that is broken right now: if production is
failing on the version it is running, roll back first
([`roll-back-a-release.md`](roll-back-a-release.md)) and release the fix afterwards.

You need write access to the repository, and somebody with approval rights on the `prod`
environment has to be reachable — the release stops and waits for them.

## Steps

1. **Confirm what stage is running, and that somebody has looked at it.**

   ```bash
   curl -s https://<stage>/api/health
   ```

   The `version` it reports is what you are about to promote. Acceptance testing happens on stage
   *before* the merge, so if nobody has exercised this version there, stop here and do that.

2. **Confirm the trunk is green.** The `CI passed` check on the last commit to the default branch.
   A release cut from a red trunk deploys a red trunk.

   Worth a look rather than a duty: `release.sh` reads the same check itself and refuses before it
   tags anything. This step is so that you find out now instead of from a failed workflow.

3. **Actions → Release → Run workflow.** Pick the bump — `patch`, `minor` or `major` — and leave
   `dry_run` unticked. Run it from the default branch; the workflow refuses any other.

   The `tag` job computes the next version and tags the head of the default branch with it — a
   commit that is already there because a pull request put it there. It writes no version into
   `pyproject.toml` and makes no commit, so it needs no write access to the branch and no bypass of
   the branch rule: the one ref it pushes is `refs/tags/vX.Y.Z`, which no ruleset covers.

   Before tagging it refuses three things, and each leaves nothing published: a lockfile that is out
   of date, a `HEAD` that is not exactly what `origin` carries on the trunk, and a `CI passed` on
   that commit that is not green.

4. **Approve the `prod` gate.** The `prod` job calls the deploy workflow and stops on the
   environment's required reviewer. This is the last point at which nothing has changed in
   production.

5. **Watch the deploy job.** Seven steps, and the one to watch is the migration: if it fails,
   nothing has gone live and the previous version is still serving. The alias moves in the step
   *after* it.

6. **Confirm the release is serving.**

   ```bash
   curl -s https://<prod>/api/health
   ```

   `version` is the tag you just cut, and `environment` is `prod`.

7. **Load the screen once, in a browser.** The deploy smokes the API and the shell; nobody has
   looked at the rendered page. A stale CloudFront copy of `index.html` is the failure this catches,
   and a hard refresh distinguishes it from a real one.

## How you know it worked

`/api/health` reports the new version and `environment: prod`; the guest book loads and lists
entries, and `/todo-list` loads; the tag exists on the default branch and the GitHub release names
it. If all four hold, the release is done.

On the first release that carries the to-do list, production's list is **empty** and says "No tasks
yet. Add the first one above." That is correct and not a failed seed: the seeder never gives
production example tasks, and the deploy log's *"the seed corpus did not go in"* warning on `prod`
is that refusal.

If `/api/health` still reports the previous version, the alias did not move — the deploy log says at
which step it stopped, and production is still serving the old version, which is the safe direction
for this to fail in.

## What this does not do

It does not touch the database beyond running the migration that travelled with the code, and it
does not create a way back other than the Lambda version that last served — the one this release's
own record names, in the environment's release manifest. `index.html` in S3 is overwritten, which
is why a rollback returns the API and not the screen; the bundles it names survive, so the screen
loads rather than going blank — see [`roll-back-a-release.md`](roll-back-a-release.md).

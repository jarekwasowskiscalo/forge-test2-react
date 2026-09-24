# Deployment and release

**For:** whoever puts a version in front of somebody.
**Normative source:** [`spec/design/architecture.md`](../spec/design/architecture.md) § Deployment
and § Environments. The procedures themselves are in [`runbooks/`](runbooks/README.md).

## Nothing deploys by accident

Every deployment is somebody's decision, taken through GitHub Actions. A workstation cannot deploy
at all: the deployment roles trust GitHub's OIDC provider and nothing else, so there are no
credentials on a laptop to do it with, whatever any script does or does not check.

| Target | How | What gates it |
|---|---|---|
| A branch's preview | Actions → **Preview** → Run workflow | write access |
| `stage` | Actions → **Deploy** → Run workflow, from any branch | write access, plus any reviewer you add |
| `stage`, automatically | a merge to the trunk | the same, once `AWS_DEPLOY_ROLE_ARN` is set |
| `prod` | Actions → **Release**, which tags and then calls the deploy | the required reviewer on the `prod` environment |
| `prod`, by hand | push a `v*` tag | the same reviewer |

**The reviewer is a promise this repository cannot keep yet.** A required reviewer lives on a
GitHub Environment, and environment protection rules on a private repository need a paid plan;
this repository has no environments at all (measured 2026-09-09). Every row above that says
"reviewer" describes the intended state. What actually stands between a dispatch and production
today is that `AWS_DEPLOY_ROLE_ARN` is unset, so the job skips — an absence, not a gate. Set the
ARN only after the environment and its reviewer exist.

A release does **not** rely on its own tag to trigger the deployment, and that is deliberate: a tag
pushed with `GITHUB_TOKEN` does not fire `push:` workflows, so a release that stopped at the tag
would leave production behind with every step green. `release.yml` calls `deploy.yml` as a job
instead, which keeps `environment: prod` — and the required reviewer — exactly where it was.

## The order the steps happen in

`scripts/deploy.sh` runs seven steps, and the order is the only one with no window in which the code
and the schema disagree:

1. **Build** the Lambda package and the SPA.
2. **Apply** the infrastructure. The API function publishes a new immutable version here; the
   gateway keeps routing to the alias, which Terraform never moves.
3. **Migrate**, by invoking the migration function. Its payload is searched for `errorMessage`,
   because a Lambda that raises still returns 200.
4. **Move the alias** onto the newly published version. *This is the moment the new code goes live*,
   and it is after the migration rather than before it.
5. **Upload the SPA** — the fingerprinted assets with a one-year immutable cache, then the shell
   with `no-cache`. **Nothing is deleted**: the bundles earlier releases wrote stay, so a shell
   a browser loaded five minutes ago still has files to name.
6. **Invalidate** `/index.html` and `/` at CloudFront.
7. **Smoke** the result: `/api/health`, the shell, and every read-only endpoint
   `contracts/openapi/` declares — the paths and the fields are read out of the contract at that
   moment rather than written into the script, which is how they came to disagree with it.
8. **Record what served.** The version, its build digest and the commit go into the environment's
   release manifest — an SSM parameter — and that record is what a rollback reads.

Then the seed runs, and does nothing unless the guest book is empty.

If step 3 fails, nothing has gone live — the alias has not moved, and the script says so: *"the
migration failed. The code has NOT been rolled; the previous version is still serving."*

## What a rollback is, and what it is not

```bash
./scripts/deploy.sh prod --rollback
```

It moves one pointer: the alias stops serving the version it is on and serves **the last version
that actually served this environment and passed its smoke**. That is the whole operation, and it
takes seconds because the old version was never deleted.

**"Served" is read, not inferred.** Every apply publishes a version, and one that never served —
because the migration failed, or because somebody ran `infra.sh apply` on its own — sits above the
alias looking exactly like a release. Choosing by number picked those. So a deploy writes what
served into the release manifest, and a rollback reads it; when it cannot name a target it refuses,
says which case it is in, and prints the `aws lambda update-alias` command for a person who knows
which version they want. It never falls back to arithmetic.

The commonest refusal is worth knowing before you meet it: **a deploy that moved the alias and then
failed its smoke leaves a serving version that no green deploy recorded.** The manifest says what
the last good release was; moving to it is a decision a person makes, not one this script infers.

Two limits, both real:

- **It does not revert the schema.** That is deliberate. The whole shape rests on migrating before
  rolling, precisely because old code against a new schema ignores a column it does not know about
  and carries on. A migration run backwards on a live database is far more dangerous than the thing
  it would be undoing; if a revision has to go, it goes forward, in a new revision.
- **It does not revert the SPA.** `index.html` is overwritten by each deploy, so the browser keeps
  the newer shell while the API serves the older version. The hashed bundles that shell names are
  still in the bucket — publication deletes nothing — so the screen loads; whether it gets along
  with the older API is the contract's question, and the contract is what makes that survivable
  rather than lucky.

So a rollback buys time; it is followed by a fix, not treated as one. The procedure is
[`runbooks/roll-back-a-release.md`](runbooks/roll-back-a-release.md).

## A new environment is not empty

`deploy.sh` and `preview.sh` both call `scripts/seed.sh` once the environment answers, and it posts
the seed corpus through the application's own HTTP API — not into the database — so what a reviewer
looks at arrived the way a guest's entry arrives, and could not be something the rules would have
refused. Two refusals make it safe to run unconditionally: it asks `/api/health` and **will not seed
production**, and it **will not seed a guest book that already has entries**. Every deploy after the
first costs one `GET`.

## Previews

One workflow, one GitHub environment named `preview`, and per-branch identity from a slug: the
branch name lowercased and trimmed to twenty characters, plus six hex characters of the full ref, so
two branches that shorten to the same string still get different stacks. The slug decides the
Terraform state key and the database name (`preview_<slug>`, with hyphens as underscores).

A preview is two Lambda functions and a public, unauthenticated function URL. It has no VPC, no
cluster, no bucket and no distribution of its own — it borrows the shared layer, and one function
answers both the screen and the API, which is what keeps it same-origin without a CloudFront
distribution per branch.

Teardown runs when the pull request is closed or the branch is deleted, and it works **without the
branch**: the workflow checks out the default branch, recomputes the slug from the event, destroys
the stack and then asks the maintenance function to drop the database. It installs neither uv nor
Node, deliberately — a teardown that needs a toolchain is a teardown that fails when you most want
it.

## What CI proves before any of this

`./scripts/check.sh` is the local definition of "will CI pass", and it is not quite the whole one.
CI additionally builds the Lambda package, asserts the production image's runtime properties, runs
a macOS leg, computes the routing verdict and refuses a frontend suite that collected no test.
[`spec/design/testing.md`](../spec/design/testing.md) § What only CI can answer names all five, so
the gap is a list rather than a surprise.

# Raise and tear down a preview

**For:** whoever wants a branch running somewhere other than their laptop.
**Normative source:** [`spec/design/architecture.md`](../../spec/design/architecture.md)
§ Environments.

## When to use this

To put a branch in front of somebody — a reviewer, a designer, whoever asked for the change. One
preview per branch, on a shared layer, and a branch that nobody is looking at costs essentially
nothing.

Not for acceptance testing before a release: that happens on `stage`, which has its own database and
is served the way production is. A preview serves the screen from the function rather than from
CloudFront, so it is the right place to judge behaviour and the wrong place to judge caching.

**Anything you put in a preview is public.** The URL is an unauthenticated Lambda function URL.

## Steps — raising one

1. **Push the branch.** The workflow runs the file from the branch you pick, so a branch cut before
   these workflows landed has to be rebased first, or its buttons will not appear.

2. **Actions → Preview → Run workflow**, choosing your branch.

3. **Wait.** It packages the preview zip (the Lambda *and* the SPA in one artefact), applies the
   branch's Terraform root, invokes the migration function — which creates the branch's database and
   then migrates it — polls health for up to two minutes, and seeds.

4. **Take the URL from the pull request comment.** The workflow edits one comment rather than adding
   a new one each run.

To find out which preview a branch gets, without running anything:

```bash
./scripts/preview.sh slug
```

The slug is the branch name lowercased, trimmed to twenty characters, plus six hex characters of the
full ref — so two branches that shorten to the same string still get different stacks. It decides
the Terraform state key and the database name.

## Steps — tearing one down

**Normally you do nothing.** Teardown fires when the pull request is closed or the branch is
deleted. It checks out the *default* branch, recomputes the slug from the event, destroys the stack
and asks the maintenance function to drop the database — in that order, because the functions hold
connections to it.

By hand, if the automatic one did not fire:

```bash
./scripts/preview.sh down <branch>
```

Running it twice is fine and is expected: a pull request closed and then a branch deleted fires it
twice, and it must exit green either way.

## How you know it worked

**Raised:** the URL in the pull request comment loads the screen, and the guest book has the seed
entries in it — a preview that comes up empty means the seed step did not run, and the workflow log
says why.

**Torn down:** the URL stops answering, and

```bash
./scripts/infra.sh preview-branch output
```

has no state to read. The branch's database is gone from the shared cluster.

## When it goes wrong

**The workflow skipped without running.** `AWS_DEPLOY_ROLE_ARN` is not set at the **repository**
level. The job's `if:` is evaluated before the environment resolves, so an environment-level value
alone is invisible to it.

**It ran as an administrator.** The workflow log names the role it assumed. If a preview run assumed
`sdd-guestbook-deploy`, the `preview` environment is missing its variable override — see
[`../security.md`](../security.md), which explains why that matters more than it looks.

**The apply cannot find the shared layer.** `./scripts/infra.sh preview-shared apply` has not been
run in this account, or was run under a different project name: the branch root reads ten SSM
parameters under `/sdd-guestbook/preview/` and creates nothing itself.

**A stack is left behind by a branch nobody remembers.** The state keys are listable —
`sdd-guestbook/preview/<slug>/` in the state bucket — and `preview.sh down` takes a branch name, so
a stale preview is removed by naming its branch.

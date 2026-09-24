# Rotate the database credentials

**For:** whoever has to change the master password — on a schedule, or after somebody saw it.
**Normative source:** [`security.md`](../security.md) § Where the secrets are.

## When to use this

When the Aurora master password must change: a periodic rotation, somebody leaving who had the
deploy role, or a Terraform state file that went somewhere it should not have.

**Check first whether you actually need to.** The application does not use this password. The API
function holds no credential at all — it signs an RDS IAM token as `app_iam`, and that token expires
in fifteen minutes. Only the migration function and the preview maintenance function use the master
password, and only during a deployment. So the exposure of this secret is narrower than it looks,
and rotating it is disruptive in a way that reading that sentence carefully may spare you.

If what you actually want is to cut off the *application's* access, that is not a password at all:
it is the `rds-db:connect` grant on `app_iam`, and revoking it is an IAM change that takes effect
within the token lifetime.

## What makes this awkward

The password lives in three places, and Terraform is only sure about two of them:

| Where | How it got there |
|---|---|
| Secrets Manager, `sdd-guestbook-<env>/database/master` | written by Terraform |
| The Terraform state, in cleartext | a `random_password` resource |
| Aurora itself | set at cluster creation |

The cluster resource carries `lifecycle { ignore_changes = [master_password] }`, which is what stops
an ordinary apply fighting with a password changed elsewhere — and it is also why a rotation is not
simply "apply again".

## Steps

1. **Do it on stage first.** This procedure ends with a deployment, and a deployment is where a
   wrong password surfaces. Stage is the environment where that costs nothing.

2. **Change the password on the cluster.** RDS → the cluster → Modify → new master password → apply
   immediately. Generate it; do not choose it. RDS refuses `!`, `/`, `@`, `"` and space, which is
   why the generated one uses a restricted set of specials.

3. **Update the secret to match.** Secrets Manager → `sdd-guestbook-<env>/database/master` → Retrieve
   and edit the value. It is a JSON object; change **only** `password`, leaving `username`, `engine`,
   `host`, `port` and `dbname` as they are. A secret whose shape changes breaks the consumer more
   thoroughly than a wrong password does.

4. **Confirm Terraform is not about to undo it.**

   ```bash
   ./scripts/infra.sh <env> plan
   ```

   An empty plan is what you want, and is what `ignore_changes` should give you. **If the plan wants
   to change the password, stop** — applying it would set the cluster back to the value in the state
   and leave the secret wrong. Reconcile the state before going further.

5. **Prove it, by deploying.** Actions → Deploy → that environment. The migration function is the
   only consumer of this password, so the deployment's migration step is the test: it either
   connects or it does not.

6. **Repeat on production**, and only after stage has been through the whole of the above.

## How you know it worked

The deployment's migration step succeeds — that is the actual proof, because it is the only thing
that uses the credential. `/api/health` answers as it did before, which proves the API function was
never affected; if it stops answering, something other than a rotation has gone wrong, because that
function does not hold this password.

## Afterwards

The old password is still in the Terraform state's history: S3 versioning is on for the state bucket
and previous versions are retained. If the rotation was in response to an exposure, the old state
versions are part of what was exposed, and expiring them is a separate piece of work on the bucket's
lifecycle rules.

Note the date somewhere durable. There is no automatic rotation configured, so the only record that
this happened is the one you make.

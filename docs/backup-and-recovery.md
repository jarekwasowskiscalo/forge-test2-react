# Backup and recovery

**For:** whoever has to answer "can we get it back?".
**Normative source:** `infra/terraform/modules/database/main.tf` for what is configured;
[`configuration.md`](configuration.md) for the retention each environment declares.

> **Read this first.** The backups described here are configured and taken by AWS. **No restore has
> ever been performed on this stack.** The procedure in
> [`runbooks/restore-the-database.md`](runbooks/restore-the-database.md) is written from the
> Terraform and from AWS's documented behaviour, not from an exercise. Until somebody has run it on
> a stage clone, treat the recovery time below as an estimate and not a commitment.

## What is backed up

| | preview | stage | prod |
|---|---|---|---|
| Automated Aurora backups | 1 day | 7 days | 14 days |
| Storage encrypted | yes | yes | yes |
| Final snapshot on destroy | no — `skip_final_snapshot` | **yes**, `sdd-guestbook-stage-final` | **yes**, `sdd-guestbook-prod-final` |
| Deletion protection | no | **yes** | **yes** |

Aurora's automated backups give **continuous point-in-time recovery** within the retention window,
to any second in it. That is the mechanism to reach for: not "last night's backup" but "the state at
11:04, just before the bad deploy".

Deletion protection and the final snapshot are both derived from the same `disposable` flag, so a
long-lived environment cannot be destroyed without leaving a snapshot behind, and a preview always
can be.

## What is not backed up, and does not need to be

| Thing | Why not |
|---|---|
| The SPA in S3 | rebuilt from the commit by `./scripts/package.sh`. The bucket is versioned as well |
| The Lambda code | every deploy publishes an immutable version, and none is deleted — that is what makes a rollback a pointer move |
| The schema | `alembic/versions/` in git is its only owner |
| The seed data | `golden-set/seed/`, in git, posted through the API |
| Terraform state | S3 versioning is on for the state bucket, and the bucket carries `prevent_destroy` |

So the only thing in this system that cannot be reconstructed from the repository is **the contents
of the database** — the guest book's entries (`guestbook_entries`) and the to-do list's tasks
(`todo_tasks`) people wrote. Everything else is a build artefact.

## What a restore costs

| | Estimate |
|---|---|
| Recovery point (how much you lose) | seconds — continuous PITR within the window |
| Recovery time (how long you wait) | **20–45 minutes**, dominated by Aurora provisioning a new cluster. It restores to a *new* cluster; it never overwrites the running one |
| Beyond the window | nothing. Past 14 days on prod there is no copy |

The second row is why the runbook's first step is to decide whether you are restoring or rolling
back: a bad *deploy* is undone in seconds by
[`runbooks/roll-back-a-release.md`](runbooks/roll-back-a-release.md); only bad *data* needs this.

## The shape of a restore, and why it needs a decision

Aurora restores to a new cluster with a new endpoint. Nothing in this stack follows a cluster
automatically — the API function's `DATABASE_URL` is built by Terraform from the cluster it manages —
so a restore is not complete until Terraform owns the new cluster. There are two ways to finish, and
the runbook makes you choose consciously:

- **Point the environment at the restored cluster** — faster, and it leaves Terraform's state
  describing a cluster that is no longer the live one until you reconcile it.
- **Export from the restored cluster and load into the running one** — slower, keeps Terraform
  truthful throughout, and is the only option when only part of the data is wrong.

Neither is automated, and pretending otherwise in a runbook is how a recovery goes wrong at the step
nobody rehearsed.

## What to do about the untested part

The cheapest honest exercise, worth an hour once:

1. Restore stage's cluster to a point in time, into a new cluster, and let it come up.
2. Time it, and write the real number into this page.
3. Connect to it with the master credentials and count the rows.
4. Delete the restored cluster.

It costs one cluster for the length of the exercise, touches nothing live, and replaces the estimate
above with a measurement. Until that has happened, this page says so.

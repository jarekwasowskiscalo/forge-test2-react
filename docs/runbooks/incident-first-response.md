# First response to an incident

**For:** whoever has just been told something is broken.
**Normative source:** none — this is a decision procedure. Each branch hands off to the runbook or
document that owns it.

## When to use this

Production is failing or behaving wrongly and you do not yet know why. Work through it in order; it
is arranged so that the cheap, reversible actions come before the expensive, irreversible ones.

**Nothing here will page you.** There is no alerting in this system — see
[`monitoring.md`](../monitoring.md), which says so plainly and lists what to add. In practice an
incident starts because a person noticed, which means by the time you read this it has been going on
for a while. Ask when it was first seen; the answer shapes step 4.

## Steps

1. **Establish what is actually true.** Two questions, deliberately separate, because the health
   check does not touch the database:

   ```bash
   curl -s https://<prod>/api/health
   curl -s "https://<prod>/api/guestbook-entries?limit=1"
   ```

   | What you get | What it means |
   |---|---|
   | Both answer | the service is up. This is a behaviour problem, not an outage — go to 3 |
   | Health answers, the read fails | the process is up and the database is not. Go to 5 |
   | Neither answers | the service is down. Go to 2 |
   | Health returns HTML | you called `/health`, not `/api/health`. Try again |

2. **If nothing answers, check whether it is being throttled before you assume it is dead.** The
   Lambda `Throttles` metric in the console. Throttling is invisible in the application's own logs —
   the request never reaches the application — and it looks exactly like an outage from outside.
   Concurrency is the connection ceiling, so this is what back-pressure looks like here.

3. **Find out what version is serving and whether it just changed.** The `version` from step 1, and
   the last run of the Deploy or Release workflow. **If a deployment landed shortly before the first
   report, roll back now** — [`roll-back-a-release.md`](roll-back-a-release.md), seconds, reversible.
   Do it before diagnosing. Diagnosis is easier with the service working.

4. **Decide whether data has been damaged**, and decide it early, because the cost of getting this
   wrong grows every minute. If entries or tasks are missing or wrong — as opposed to unreachable —
   stop and read [`restore-the-database.md`](restore-the-database.md) before anything else: a restore
   returns the whole database, both lists, to a moment in the past, so every write that happens
   while you deliberate is a write you will lose recovering.

5. **Read the logs, by request id.** `/aws/lambda/sdd-guestbook-prod-api` in CloudWatch Logs:

   ```
   fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc | limit 50
   ```

   Then take the bracketed request id from an interesting line and follow that one request:

   ```
   fields @timestamp, @message | filter @message like "<the id>" | sort @timestamp asc
   ```

   The catch-all handler logs every unexpected failure and returns a fixed body, so a failure is
   always in the log and never in the response. **What it logs is the exception's type and the
   frames it passed through — never the exception's text**, which is how log lines carry
   identifiers and counts and never values even when the record is a crash. So you will find which
   exception, and the file and line of every frame, and you will not find what somebody wrote — by
   design, and no longer by accident.

   The block starts `exception (article XI: ...)` and each frame reads
   `at app/contexts/guestbook/services/guestbook_entries.py:40 in list_entries`. Open that file at
   that line: the values that produced the failure are not in the log and are not meant to be.

   The access log, `/aws/apigateway/sdd-guestbook-prod`, gives status and latency per request when
   the question is "which endpoint" rather than "which exception".

6. **Check the database if the read failed.** RDS → the cluster. Capacity at its maximum is what a
   runaway query looks like here rather than a CPU spike. Note that a cold cluster is *not* the
   cause on production, which keeps a floor of 0.5 ACU — that symptom belongs to stage and preview.

7. **Check whether it is one of the known ones.** [`troubleshooting.md`](../troubleshooting.md) is a
   symptom index, and [`infra/README.md`](../../infra/README.md) § What was wrong before has the four
   failures this stack produced before it ever carried traffic. Three of the four would have been
   diagnosed from the wrong end.

## How you know it worked

Both calls from step 1 answer, the screen loads in a browser, and the error rate in the log has
returned to what it was. Containment is not resolution: if you rolled back, the trunk still carries
the version you rolled away from, and it will deploy again unless something changes.

## Afterwards

Write down what happened, when it started, what you did and in which order — the reasoning
especially, because that is the part nobody can reconstruct later. Durable reasoning about the
system belongs in [`spec/rationale/`](../../spec/rationale/README.md), and a rule that turns out to
be missing belongs in [`spec/`](../../spec/README.md), through the change process rather than as a
note. An incident that produces neither has been survived rather than learned from.

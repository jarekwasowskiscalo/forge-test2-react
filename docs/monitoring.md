# Monitoring

**For:** whoever is asked "how will we know?".
**Normative source:** none — there is no monitoring rule in `spec/`, because there is no monitoring.
This page is a statement of what exists and what does not.

## What exists

| Signal | Where | Retention |
|---|---|---|
| A liveness answer naming the release | `GET /api/health` | — |
| Application logs, request-id correlated | CloudWatch Logs, `/aws/lambda/sdd-guestbook-<env>-api` | 14 days stage, 30 prod |
| Migration output, once per deploy | `/aws/lambda/sdd-guestbook-<env>-migrate` | the same |
| HTTP access logs as structured JSON | `/aws/apigateway/sdd-guestbook-<env>` | the same |
| Lambda and Aurora's built-in CloudWatch metrics | the AWS console | AWS's own |
| A post-deploy smoke, on every deployment | `scripts/deploy.sh`, step 7 | the workflow log |

Reading them is [`operations.md`](operations.md) § The logs.

## What does not exist

Said plainly, because a monitoring page that implies coverage it does not have is worse than no page
at all:

- **No alarms.** There is not one `aws_cloudwatch_metric_alarm` in the Terraform.
- **No notification channel.** No SNS topic, no email, no chat, no pager.
- **No dashboards** and no custom metrics. Nothing is emitted beyond what Lambda and Aurora publish
  by themselves.
- **No tracing.** No X-Ray, no OpenTelemetry. A request is followed by grepping its id, and only
  within one function.
- **No uptime check.** Nothing calls `/api/health` between deployments. If the application stops
  answering at three in the morning, the first thing that notices is a person.
- **No error budget, no SLO, no on-call rota.**

**So the honest summary is: this system is observable and unmonitored.** When something breaks you
can find out why; nothing will tell you that it broke.

That is a defensible position for a template and for an internal stage environment. It is not one
for a production service with users, and it should be the first thing added when this stops being a
template.

## What to add first, in order

Each of these is a small, self-contained change, and they are listed in the order that buys the most
per unit of work.

1. **An external uptime check on `/api/health`.** Anything that calls a URL every minute and
   complains. This is the single largest gap: everything below assumes somebody already knows the
   service is up.
2. **An SNS topic and two alarms** — the API function's `Errors` and its `Throttles`. Throttles
   matter more than they look: reserved concurrency is the connection ceiling, so throttling is what
   back-pressure looks like from outside, and it is invisible in the application's own logs.
3. **A metric filter on `ERROR` in the application log group**, with the same topic. The catch-all
   handler in `app/core/errors.py` logs the exception's type and the frames it passed through, and
   returns a fixed body — so an unexpected failure is always in the log and never in the response.
   It does not log the exception's text, and neither does anything else: a filter on every sink
   reduces an exception to its category and its position (`app/core/logging_config.py`), which is
   what keeps article XI true of a traceback as well as of a message.
4. **An alarm on Aurora `ServerlessDatabaseCapacity` at the maximum**, which is the shape a runaway
   query takes here rather than a CPU spike.
5. **A budget alarm on the account.** Not availability, but the failure this architecture makes
   quietly possible: everything scales to zero at rest, so a cost anomaly is the first sign of
   traffic nobody expected.

The first two are roughly thirty lines of Terraform in `infra/terraform/modules/api/`, one address
to subscribe, and a variable per environment so preview does not page anybody.

## What deliberately stays out

**The health check will not touch the database.** It is asked to say whether the process answers, and
a health check that opens a connection turns a slow query into an outage across every probe at once.
"Is it reachable?" is a different question and has its own answer in
[`operations.md`](operations.md).

**Logs will not carry values.** Article XI of [`spec/constitution.md`](../spec/constitution.md) keeps
personal data out of artefacts, so an application log line carries identifiers and counts and the
access log carries no query string and no body. Any monitoring added later inherits that
constraint: an alert that quotes what somebody wrote has moved the data somewhere new.

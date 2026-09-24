"""The application-agnostic half of the suite.

Four modules, one question each: how a request is made (`client`), how a list
answer is read (`list_response`), how a failure is phrased (`assertions`), and
how the target database is emptied (`database`).

Nothing here knows what any domain concept is. Paths are opaque
strings, field names are the caller's words, and status codes are numbers the
caller supplies with a sentence saying what they mean. That is what makes the
`e2e/suite/steps/` modules the single place in the repository where "which
endpoint, which field, which status code" is written down.

No test framework in the harness.
"""

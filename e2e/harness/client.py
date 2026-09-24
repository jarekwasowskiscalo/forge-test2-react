"""How a request is made, and what came back.

`Answer` deliberately does not keep the response body. Every assertion in the
suite this replaces ended `: {context.response.text}`, so a failing scenario put
a nineteen-row page of real names, e-mail addresses and phone numbers into the
JUnit `<failure>` element -- which CI uploads as an artifact and keeps for seven
days. Not carrying the body at all makes that a property of the type rather than
a rule somebody has to remember at thirty call sites.

**`_log` prints the exchange, but not the whole of it.** pytest captures print
output into the failing test's report, which is the seven-day CI artefact the
paragraph above exists to keep clean. So `_log` drops the value -- and the name --
of every field whose name says it is a credential, and says how many it dropped;
a body carrying none is printed exactly as before. `spec/constitution.md`
§ Article XIII lists "logging secrets, tokens or personal data" among the
forbidden, and a captured stdout is a log, a report and a committed artefact in
one. This template has no endpoint that takes a credential; the harness refuses
to be the module that would print one on the day a product built on it does,
which is why the redaction is a property of this module rather than a rule each
step has to remember.

One `httpx.Client` for the scenario, not a fresh connection per call, and the
timeout lives on it rather than on each request: per-call is a thing to remember
at fourteen call sites and the suite this replaces remembered at none, so a hung
application hung the run until CI's twenty-minute kill with no line of output
naming the request.

No test framework in the harness.
"""

import json
import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Final

import httpx

#: One row of a JSON list answer. A plain alias rather than a PEP 695 `type`
#: statement: nothing in `app/`, `scripts/` or `tests/` uses that syntax yet and
#: this is not the change that introduces it.
Row = Mapping[str, Any]

#: Where the application answers. **Keep the `/api` if you override this.**
#: Every JSON route lives under that prefix; the unprefixed path is matched by
#: the SPA catch-all in `app/main.py`, which answers the HTML shell -- 200 for a
#: GET and 405 for anything else. A suite pointed at the bare origin fails every
#: scenario at once with a 405 that names nothing, which is how this suite once
#: spent five days reporting 15/20.
BASE_URL: Final[str] = os.environ.get("TARGET_BASE_URL", "http://127.0.0.1:8080/api")

#: Seconds. Generous, because a scenario's first request may pay for a cold
#: application; the number that matters is that it is finite.
TIMEOUT_SECONDS: Final[float] = 15.0

#: How many keys of an object answer `Answer.shape` names before giving up. The
#: shape exists to make a failure legible, not to reproduce the body -- and keys
#: are structure, where values would be the personal data this type refuses to
#: carry.
_SHAPE_KEY_LIMIT: Final[int] = 8

#: What `send` will do. A closed set rather than any string: a typo in a step's
#: method name would otherwise reach the application as an unroutable verb and come
#: back as the SPA catch-all's 405 -- a failure that names nothing, which is exactly
#: the five-day diagnosis `BASE_URL` above already paid for once.
_WRITE_METHODS: Final[frozenset[str]] = frozenset({"POST", "PATCH", "PUT", "DELETE"})

#: Field names whose **value** never reaches stdout. Matched as a substring of the
#: lower-cased key, so `password`, `new_password` and `passwordConfirm` are all
#: covered by one entry and a field added to a request shape later is covered
#: without an edit here.
#:
#: The key is dropped along with its value rather than printed with the value
#: masked. Masking leaves the field *name* in the report, and a name in the report
#: is one unredacted branch away from the value -- which is why
#: `tests/tooling/test_e2e_harness.py` refuses the name too, not only the secret.
#:
#: The set held two Polish spellings of "password" while the tree was bilingual.
#: They are gone with the rest of the Polish (`spec/design/conventions.md`
#: § Language): the fields this harness sends are named by this repository's own
#: contract, and that contract is English. The day a client of another language
#: sends one, this is the one line to grow -- the set fails safe in one direction
#: only, so an entry that never matches costs nothing and a missing one prints a
#: credential to stdout.
_CREDENTIAL_FIELDS: Final[frozenset[str]] = frozenset(
    {"password", "passwd", "pwd", "secret", "token", "credential"}
)


def _is_credential(key: object) -> bool:
    """Whether a field name says the value behind it is a credential."""
    lowered = str(key).lower()
    return any(marker in lowered for marker in _CREDENTIAL_FIELDS)


def _redact(value: Any) -> tuple[Any, int]:
    """`value` with every credential field removed, and how many were removed.

    Recursive, because a credential does not have to be at the top level of a
    body for printing it to be the same defect. The count is returned rather
    than substituted in place for the reason `_CREDENTIAL_FIELDS` gives: a
    placeholder sits under the field's own name, and the name is what has to go.
    """
    if isinstance(value, Mapping):
        kept: dict[str, Any] = {}
        removed = 0
        for key, item in value.items():
            if _is_credential(key):
                removed += 1
                continue
            kept[str(key)], nested = _redact(item)
            removed += nested
        return kept, removed
    if isinstance(value, list):
        items: list[Any] = []
        removed = 0
        for item in value:
            redacted, nested = _redact(item)
            items.append(redacted)
            removed += nested
        return items, removed
    return value, 0


def _describe_request_body(body: bytes) -> str:
    """One line for a request body: printable, or an honest refusal to print it.

    A body that does not parse as JSON is not printed at all. That is the
    conservative branch on purpose -- this module cannot tell a credential from
    any other bytes in a form encoding or an opaque blob, and the rule it is
    keeping has no "probably fine" case.
    """
    text = body.decode("utf-8", "replace")
    try:
        parsed = json.loads(text)
    except ValueError:
        return "not JSON, not printed -- this module cannot tell what is in it"
    redacted, removed = _redact(parsed)
    printed = json.dumps(redacted, ensure_ascii=False)
    if not removed:
        return printed
    return f"{printed}  ({removed} credential field(s) removed)"


@dataclass(frozen=True)
class Answer:
    """What one request produced -- everything except the body itself.

    `shape` is a short structural description ("array of 19", "object with keys:
    id, rows_total"). It says enough to tell a page from an envelope from an
    error in a failure message, and names no value.
    """

    method: str
    path: str
    status: int
    payload: Any
    shape: str

    def __str__(self) -> str:
        return f"{self.method} {self.path} -> {self.status} ({self.shape})"

    def record(self) -> Row:
        """The payload as a single object, or an explanation of what it was.

        A step that reads a field off "the case" wants this; a step that got a
        list back has asked the wrong endpoint or the wrong question, and the
        message says which answer surprised it rather than raising
        `TypeError: list indices must be integers`.
        """
        if not isinstance(self.payload, Mapping):
            raise AssertionError(f"expected a single object, but {self} answered")
        return self.payload


def _describe(payload: Any, response: httpx.Response) -> str:
    """A structural one-liner for `Answer.shape`. Never includes a value."""
    if isinstance(payload, Mapping):
        keys = list(payload)
        shown = ", ".join(str(key) for key in keys[:_SHAPE_KEY_LIMIT])
        if len(keys) > _SHAPE_KEY_LIMIT:
            shown += f", ... {len(keys)} keys"
        return f"object with keys: {shown}" if keys else "empty object"
    if isinstance(payload, list):
        return f"array of {len(payload)}"
    content_type = response.headers.get("content-type", "unknown").split(";")[0]
    return f"{content_type}, {len(response.content)} bytes -- not JSON"


def _log(response: httpx.Response) -> None:
    """Print the exchange for a human, minus anything that says it is a credential.

    Captured by pytest and shown under a failed test, written to no file. That
    split *was* the whole PII story, and it stopped being enough the moment this
    suite gained a write whose body is a password: pytest's capture lands in the
    JUnit report, which CI keeps for seven days. So the request body goes through
    `_describe_request_body`, which drops credential fields and keeps the rest --
    the diagnostic is worth having, and it is worth having without the secret.

    Article XIII of `spec/constitution.md` forbids logging secrets; `R-1` pkt 4
    says the same for this change. Neither has an exception for a diagnostic.
    """
    request = response.request
    print("--- HTTP call ---")
    print(f"> {request.method} {request.url}")
    #: The content type is read *before* the body, and a multipart body is never
    #: read at all. `httpx` streams a multipart request, so touching
    #: `request.content` on one raises `RequestNotRead` -- from inside the
    #: logger, after the request already succeeded, which turns every upload
    #: into a failure about logging.
    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" in content_type:
        print(f"> body: multipart ({content_type.split('boundary=')[0].strip()})")
    else:
        try:
            body = request.content
        except httpx.RequestNotRead:
            body = b""
        if body:
            print(f"> body: {_describe_request_body(body)}")
    print(f"< status: {response.status_code}")
    try:
        print(f"< body: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except ValueError:
        print(f"< body: {response.text}")
    print("-----------------")


class ApiClient:
    """The one way this suite reaches the application.

    It remembers its own last answer, so a step asserting about "the response"
    asks the thing that made the request instead of reading a field somebody
    else had to remember to set -- which is how the suite this replaces came to
    assert about the previous scenario's upload.
    """

    def __init__(
        self,
        base_url: str = BASE_URL,
        timeout: float = TIMEOUT_SECONDS,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        #: `transport` exists for `tests/tooling/test_e2e_harness.py`, which drives an
        #: `httpx.MockTransport` -- so the client is testable without a server
        #: and without monkeypatching a module global.
        self._client = httpx.Client(base_url=base_url, timeout=timeout, transport=transport)
        self._last: Answer | None = None

    def get(self, path: str, **query: str | int) -> Answer:
        return self._record("GET", path, self._client.get(path, params=dict(query)))

    def send(self, method: str, path: str, *, body: Mapping[str, Any]) -> Answer:
        """POST, PATCH, PUT or DELETE one JSON body, and remember the answer.

        General -- the method is an argument -- rather than one `post_json` per
        endpoint, so the next resource needs no new verb and every write a person
        authors is provable black-box with this one.

        `Answer` still refuses to carry the body of the response; the request body
        is the caller's own fixture, so it holds no personal data this suite did not
        already choose to send.
        """
        verb = method.upper()
        if verb not in _WRITE_METHODS:
            raise AssertionError(
                f"{verb} is not a write this harness makes. Use one of "
                f"{', '.join(sorted(_WRITE_METHODS))}, or `get()` for a read."
            )
        return self._record(verb, path, self._client.request(verb, path, json=dict(body)))

    @property
    def last(self) -> Answer:
        """The most recent answer, or an explanation of why there is none."""
        if self._last is None:
            raise AssertionError(
                "no request has been made in this scenario, so there is no answer to "
                "assert about. A `Then` step is reading a response that no `When` step "
                "produced."
            )
        return self._last

    def describe_last(self) -> str:
        """The same thing, for a message. **Defined never to raise.**

        The diagnostic it feeds explains that a precondition step did not run,
        which is exactly the case where there is no last answer -- so a version
        of it that could raise would fail with an `AttributeError` about `None`
        instead of the sentence it exists to print. That is not hypothetical:
        `_last_import_summary` in the suite this replaces did precisely that.
        """
        return "nothing has been sent yet" if self._last is None else str(self._last)

    def close(self) -> None:
        self._client.close()

    def _record(self, method: str, path: str, response: httpx.Response) -> Answer:
        _log(response)
        try:
            payload = response.json()
        except ValueError:
            payload = None
        self._last = Answer(
            method=method,
            path=path,
            status=response.status_code,
            payload=payload,
            shape=_describe(payload, response),
        )
        return self._last

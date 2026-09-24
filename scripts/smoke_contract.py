"""What a deployment's smoke asks, read out of the contract rather than remembered.

`scripts/deploy.sh` used to carry its own copy of the question: `/api/entries?limit=1`,
and a body that had to hold `items`, `total` and `matching`. The application serves
`/api/guestbook-entries` and the third field was renamed `total_all` before either
line was written, so the smoke had been wrong since the day it was added -- and the
sentence it failed with, "the list endpoint did not answer with the contract's
envelope", accused the application of the smoke's own wrong URL.

**A copy is what made that possible, so this module removes the copy.** The smoke's
question is derived, at the moment it is asked, from the same
`contracts/openapi/*.yaml` the constitution (article VI) already makes the authority.
Nothing here is typed twice, so nothing here can drift: rename a field in the
contract and the smoke asks for the new name on the next deploy.

**Which operations.** Every `get` whose path takes no parameter -- those are the
questions that can be asked of a deployment knowing nothing about its contents, and
they are read-only, which is what makes a smoke safe to run against production. An
operation that declares a `limit` query parameter is asked with `limit=1`, because a
smoke wants the envelope rather than the page; that too is read off the contract
rather than assumed. `GET /api/guestbook-entries/{entry_id}` is excluded by the same
rule that includes its collection, and delete the guestbook example and the smoke
shrinks to `/api/health` on its own -- there is no domain word in here or in
`deploy.sh` to delete afterwards.

**Two verbs, because the request belongs to the shell.** `operations` prints what to
ask; `envelope` judges one answer that has already arrived, reading the body from
stdin. `deploy.sh` keeps `curl` -- it is the thing that knows about retries, timeouts
and the distribution -- and the three verdicts stay here, where they can be tested
without a network:

    no answer at all                curl failed, or the status was not 200 -- the shell sees it
    an answer that is not JSON      `verdict` says so, and names the media type that came
    JSON without the promised keys  `verdict` names each key that is missing

The middle verdict reports what arrived and does not narrate why. A wrong `/api/` path
today comes back as a JSON 404 from the application (`app/main.py`) rather than as the
SPA shell -- the edge stopped rewriting statuses in the change before this one -- so a
sentence about the shell would be the same sin in the other direction: a mechanism
asserted rather than observed.

Usage:
    uv run python scripts/smoke_contract.py operations [--contracts DIR]
    uv run python scripts/smoke_contract.py envelope --required items,total < body
"""

import argparse
import json
import pathlib
import sys
from typing import Any, Final, NamedTuple

from openapi_contract import Contract, json_body, read_contracts, ref_name

REPO_ROOT: Final = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_CONTRACTS: Final = REPO_ROOT / "contracts" / "openapi"

#: The status a smoke reads. A contract may document others; none of them is the
#: answer to "is this deployment serving".
OK: Final = "200"

#: Asked of any operation that declares it, so the answer carries the envelope
#: rather than a page of rows. The value is the smallest page the register allows.
LIMIT: Final = "limit"


class Question(NamedTuple):
    """One read-only question a deployment can be asked, and the answer it owes."""

    #: The path as the contract writes it, `/api` prefix included.
    path: str
    #: The query string to append, or `""`. Never a guess: derived from a declared parameter.
    query: str
    #: Every key the 200 body promises. Empty when the contract froze no field of it.
    required: tuple[str, ...]


class Unreadable(Exception):
    """A contract this cannot follow. Raised rather than skipped: an endpoint quietly
    demoted to "promises nothing" is a smoke that passes while checking less than it
    says, which is the shape of the defect this module exists to remove."""


def _schema(document: dict[str, Any], schema: Any) -> Any:
    """Follow a `$ref` into `components/schemas`, once. Nothing here nests deeper."""
    name = ref_name(schema)
    if name is None:
        return schema
    components = document.get("components")
    schemas = components.get("schemas") if isinstance(components, dict) else None
    if not isinstance(schemas, dict) or name not in schemas:
        raise Unreadable(
            f"the response schema points at {name!r}, and this document has no such "
            "schema under components/schemas. A $ref into another file is not followed."
        )
    return schemas[name]


def _required(document: dict[str, Any], operation: dict[str, Any]) -> tuple[str, ...]:
    responses = operation.get("responses")
    if not isinstance(responses, dict):
        return ()
    schema = _schema(document, json_body(responses.get(OK)))
    if not isinstance(schema, dict):
        return ()
    required = schema.get("required")
    if not isinstance(required, list):
        return ()
    return tuple(str(key) for key in required)


def _parameters(operation: dict[str, Any]) -> list[dict[str, Any]]:
    declared = operation.get("parameters")
    return [one for one in declared if isinstance(one, dict)] if isinstance(declared, list) else []


def questions(contracts: list[Contract]) -> list[Question]:
    """Every read-only, parameterless GET the contracts declare, in path order.

    Sorted rather than left in file order so a deploy log reads the same way twice,
    and so a test can state the whole expected list rather than a set.
    """
    found: list[Question] = []
    for contract in contracts:
        paths = contract.document.get("paths")
        if not isinstance(paths, dict):
            continue
        for path, operations in paths.items():
            if not isinstance(operations, dict):
                continue
            operation = operations.get("get")
            if not isinstance(operation, dict):
                continue
            parameters = _parameters(operation)
            # A path parameter has to be invented, and a required query parameter too.
            # Either way the answer would be about the value this made up rather than
            # about the deployment -- a 404 or a 422, read as a broken release.
            if any(
                one.get("in") == "path" or (one.get("in") == "query" and one.get("required"))
                for one in parameters
            ):
                continue
            query = f"?{LIMIT}=1" if any(one.get("name") == LIMIT for one in parameters) else ""
            found.append(Question(str(path), query, _required(contract.document, operation)))
    return sorted(found)


def verdict(body: str, required: tuple[str, ...], media_type: str = "") -> str | None:
    """`None` when the answer honours the contract, otherwise the sentence to print.

    The two failures are told apart rather than merged, because they are repaired in
    different places: a body that is not JSON says something other than the
    application answered, and a body missing a key says the application did and
    answered something else. `media_type` is reported, never interpreted -- it is the
    evidence for which of the two this is, and the previous version of this check
    guessed at a cause instead of printing one.
    """
    try:
        page = json.loads(body)
    except ValueError:
        opening = " ".join(body.split())[:120]
        arrived = f" as {media_type}" if media_type else ""
        return (
            f"answered{arrived} with something that is not JSON, where the contract "
            f"promises a JSON object. It came back with: {opening}"
        )
    if not isinstance(page, dict):
        return f"answered with a {type(page).__name__} where the contract promises an object"
    missing = [key for key in required if key not in page]
    if missing:
        return (
            f"answered without {', '.join(missing)} -- the envelope is not the one "
            "contracts/openapi/ promises"
        )
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="verb", required=True)

    asking = sub.add_parser("operations", help="print what a smoke should ask")
    asking.add_argument("--contracts", type=pathlib.Path, default=DEFAULT_CONTRACTS)

    judging = sub.add_parser("envelope", help="judge one answer, read from stdin")
    judging.add_argument("--required", default="", help="comma-separated keys the body owes")
    judging.add_argument("--media-type", default="", help="what the answer said it was")

    arguments = parser.parse_args(argv)

    if arguments.verb == "operations":
        contracts, findings = read_contracts(arguments.contracts, REPO_ROOT)
        for finding in findings:
            print(f"error: {finding.path}: {finding.message}", file=sys.stderr)
        if findings:
            return 1
        try:
            asking_for = questions(contracts)
        except Unreadable as unreadable:
            print(f"error: {unreadable}", file=sys.stderr)
            return 1
        for question in asking_for:
            print(f"{question.path}\t{question.query}\t{','.join(question.required)}")
        return 0

    required = tuple(key for key in arguments.required.split(",") if key)
    failure = verdict(sys.stdin.read(), required, arguments.media_type)
    if failure is not None:
        print(failure, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Hold the application to the OpenAPI contract somebody wrote by hand.

`contracts/openapi/` is authored, committed and versioned. `openapi.json` is a dump of
the Pydantic schemas and is gitignored. The constitution (Article VI) says which of the
two has authority -- "the contract is the authority and the code is validated against it,
not the other way round" -- and this module is that sentence written as an algorithm.

**The contract is a SUBSET of the dump, and the asymmetry is the whole design.** Every
sentence the contract states must be true of the dump; the dump may carry more. Two
alternatives were measured and rejected:

- *Compare everything after normalising both sides.* The exclusion list -- `operationId`,
  `title` generated from field names, `ValidationError`, `anyOf` with `null`, key order --
  would then BE the real scope of the contract, only written in Python instead of YAML,
  and discovered by trial. Every FastAPI bump that emits one new key reddens every pull
  request. That is the shape the first version of `backtick-paths` had: 92 findings, 1 of them real.
- *Compare a chosen projection for equality.* Equality is symmetric, and symmetry is the
  defect here: it forbids the dump to carry anything the projection did not foresee, and
  every contract sentence outside the projection is unenforced while looking enforced.

Under a subset the number of findings cannot exceed the number of sentences a human
wrote, so 92 findings are structurally impossible. A partial contract is legal, and the
scale line says how much was checked.

**One rule runs the other way**, without which "subset" degenerates into "an empty
contract passes" -- a gate green over an empty set, which the 2026-09-01 audit names as a
serious finding (F-03). Every `/api/*` path in the dump must fall under a prefix that some
contract already claims. Deliberately one level deep: a new path is a new boundary and
therefore a decision, while a new optional field is an extension.

**`x-refusals` closes what neither the dump nor any diff-scoped gate can see.** A stable
refusal code lives in the `detail` of a raised `HTTPException`, so FastAPI never emits it,
yet `spec/design/api.md` calls it a contract that "never changes". The contract
lists the codes and this module looks for each one as a literal in every router module
under `app/` -- one per bounded context, plus the platform slice --
cheap, textual, and silent on a refactor that keeps the codes.

This module imports no application code: it reads two documents and some source text. That
is what lets `tests/tooling/test_openapi_contract.py` drive it over hand-built pairs without
starting anything. That sentence named a suite that did not exist for a long time, and the
absence was not free: the two comparisons the test now pins -- a parameter's `$ref` and the
constraints on a schema that has no `properties` -- were both silently absent.

Usage:
    uv run python scripts/openapi_contract.py [--dump PATH] [--contracts DIR] [--json]

`scripts/contracts.sh` is the interface a human and CI use; it produces the dump first.
"""

import argparse
import json
import pathlib
import sys
from typing import Any, Final, NamedTuple

import yaml

REPO_ROOT: Final = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_CONTRACTS: Final = REPO_ROOT / "contracts" / "openapi"
DEFAULT_DUMP: Final = REPO_ROOT / "openapi.json"
ROUTERS: Final = REPO_ROOT / "app"

#: Everything that ran and agreed.
EXIT_OK: Final = 0
#: The contract and the dump disagree, or the contract is unreadable.
EXIT_MISMATCH: Final = 1
#: Nothing to compare. A NAMED GAP, never a pass: `check.sh` renders it INCOMPLETE, and
#: that third state exists precisely so a green that skipped a gate cannot read like a
#: green that passed it.
EXIT_NOTHING: Final = 4

#: The operation keys of an OpenAPI path item. Everything else under a path -- `summary`,
#: `description`, `parameters`, `servers` -- is not an operation and is skipped rather
#: than reported as a method the dump is missing.
_METHODS: Final[frozenset[str]] = frozenset(
    {"get", "put", "post", "delete", "options", "head", "patch", "trace"}
)

#: Compared only where the contract states them. A contract that says nothing about
#: `maxLength` is a contract that did not freeze it, and freezing by omission is how the
#: exclusion list of the rejected full comparison would have grown.
_CONSTRAINTS: Final[tuple[str, ...]] = (
    "type",
    "format",
    "enum",
    "maxLength",
    "minLength",
    "maximum",
    "minimum",
    "exclusiveMaximum",
    "exclusiveMinimum",
    "pattern",
)

#: How deep a claimed prefix reaches: `/api/guestbook-entries` out of
#: `/api/guestbook-entries/{entry_id}`. Two segments, so one contract file covers a
#: resource and its item routes without listing every one of them.
_PREFIX_SEGMENTS: Final = 2


class Finding(NamedTuple):
    """One disagreement, addressed at the document a reviewer can edit."""

    #: Repository-relative path. The CONTRACT wherever there is one: `openapi.json` is
    #: gitignored, so its line numbers mean nothing to a reviewer reading a diff.
    path: str
    #: 1-based, or 0 when the finding is about the dump rather than a contract line.
    line: int
    message: str


class Contract(NamedTuple):
    """One authored contract document, with the line of every key kept beside it."""

    path: str
    document: dict[str, Any]
    #: Key path (`"paths"`, `"/api/x"`, `"get"`, ...) to the 1-based line of that key.
    lines: dict[tuple[str, ...], int]


def line_index(text: str) -> dict[tuple[str, ...], int]:
    """Map every key path in a YAML document to the line its key stands on.

    Built from the composed node tree rather than by scanning for text, because a
    scan cannot tell `version:` under `info` from `version:` anywhere else, and the
    whole point of reporting a line is that it is the right one.
    """
    index: dict[tuple[str, ...], int] = {}

    def walk(node: yaml.Node, prefix: tuple[str, ...]) -> None:
        if isinstance(node, yaml.MappingNode):
            for key_node, value_node in node.value:
                key = str(key_node.value)
                here = (*prefix, key)
                index[here] = int(key_node.start_mark.line) + 1
                walk(value_node, here)
        elif isinstance(node, yaml.SequenceNode):
            for position, item in enumerate(node.value):
                walk(item, (*prefix, str(position)))

    root = yaml.compose(text)
    if root is not None:
        walk(root, ())
    return index


def _relative(path: pathlib.Path, root: pathlib.Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def read_contracts(
    directory: pathlib.Path, root: pathlib.Path
) -> tuple[list[Contract], list[Finding]]:
    """Load every `*.yaml` under `directory`, newest problems first.

    A document that does not parse is a finding rather than a crash: a contract the
    machine cannot read is not a contract, and saying so with a path beats a traceback.
    """
    contracts: list[Contract] = []
    findings: list[Finding] = []
    for path in sorted(directory.glob("*.yaml")) if directory.is_dir() else []:
        where = _relative(path, root)
        text = path.read_text(encoding="utf-8")
        try:
            document = yaml.safe_load(text)
        except yaml.YAMLError as error:
            findings.append(Finding(where, 0, f"the contract does not parse as YAML: {error}"))
            continue
        if not isinstance(document, dict):
            findings.append(Finding(where, 0, "the contract is not a YAML mapping"))
            continue
        contracts.append(Contract(where, document, line_index(text)))
    return contracts, findings


def _prefix(path: str) -> str:
    """The claim a contract stakes by naming one path: two segments, no more."""
    segments = [segment for segment in path.split("/") if segment]
    return "/" + "/".join(segments[:_PREFIX_SEGMENTS])


def ref_name(schema: Any) -> str | None:
    """The schema name behind a `$ref`, which is what becomes a type in `schema.d.ts`.

    Public, with `json_body` below, because `scripts/smoke_contract.py` reads the same
    two shapes out of the same documents: a name two modules read is not a private one.
    """
    if isinstance(schema, dict):
        reference = schema.get("$ref")
        if isinstance(reference, str):
            return reference.rsplit("/", 1)[-1]
    return None


def json_body(response: Any) -> Any:
    if not isinstance(response, dict):
        return None
    content = response.get("content")
    if not isinstance(content, dict):
        return None
    body = content.get("application/json")
    return body.get("schema") if isinstance(body, dict) else None


def _compare_operation(
    contract: Contract,
    path: str,
    method: str,
    operation: dict[str, Any],
    dump_operation: dict[str, Any],
) -> list[Finding]:
    """Responses and parameters, each asserted only where the contract speaks."""
    findings: list[Finding] = []
    where = contract.path
    shown = f"{method.upper()} {path}"
    dump_responses = dump_operation.get("responses")
    dump_responses = dump_responses if isinstance(dump_responses, dict) else {}

    responses = operation.get("responses")
    for code, response in (responses if isinstance(responses, dict) else {}).items():
        code = str(code)
        at = contract.lines.get(("paths", path, method, "responses", code), 0)
        dump_response = dump_responses.get(code)
        if dump_response is None:
            findings.append(
                Finding(
                    where,
                    at,
                    f"the contract freezes {code} on {shown}; the dump declares no such "
                    f"response. A status the router raises without `responses={{{code}: ...}}` "
                    "on its decorator reaches neither openapi.json nor schema.d.ts.",
                )
            )
            continue
        wanted = ref_name(json_body(response))
        if wanted is None:
            continue
        found = ref_name(json_body(dump_response))
        if found != wanted:
            findings.append(
                Finding(
                    where,
                    at,
                    f"the contract freezes {code} on {shown} as {wanted}; the dump answers "
                    f"with {found or 'no JSON body'}. The schema NAME is what becomes a type "
                    "in frontend/src/api/schema.d.ts.",
                )
            )

    dump_parameters = dump_operation.get("parameters")
    by_name = {
        parameter.get("name"): parameter
        for parameter in (dump_parameters if isinstance(dump_parameters, list) else [])
        if isinstance(parameter, dict)
    }
    parameters = operation.get("parameters")
    for position, parameter in enumerate(parameters if isinstance(parameters, list) else []):
        if not isinstance(parameter, dict):
            continue
        name = parameter.get("name")
        at = contract.lines.get(("paths", path, method, "parameters", str(position), "name"), 0)
        found_parameter = by_name.get(name)
        if found_parameter is None:
            findings.append(
                Finding(
                    where,
                    at,
                    f"the contract freezes the parameter {name} on {shown}; "
                    "the dump has no parameter by that name",
                )
            )
            continue
        for key in ("in", "required"):
            if key in parameter and parameter[key] != found_parameter.get(key):
                findings.append(
                    Finding(
                        where,
                        at,
                        f"the contract freezes {name}.{key} as {parameter[key]!r} on {shown}; "
                        f"the dump says {found_parameter.get(key)!r}",
                    )
                )
        findings += _compare_parameter_schema(contract, parameter, found_parameter, at, shown)
    return findings


def _compare_parameter_schema(
    contract: Contract,
    parameter: dict[str, Any],
    found_parameter: dict[str, Any],
    at: int,
    shown: str,
) -> list[Finding]:
    """What a parameter's `schema` says -- and only what the contract chose to write.

    Until this existed a parameter froze its name, its `in` and its `required`, and
    nothing else: a `schema` written under it was parsed into the dict and then never
    read. So a closed set could be declared in the contract, rendered into
    `schema.d.ts` as a union the browser has to satisfy, and agree with the
    application by nobody's decision.

    The `$ref` is the half that matters. A `$ref` gives the set a NAME, and the name is
    what survives into the generated types; an inline enum that drifted would change a
    type the frontend compiles against, silently, in the direction of accepting more.
    """
    declared = parameter.get("schema")
    if not isinstance(declared, dict):
        return []
    name = parameter.get("name")
    found = found_parameter.get("schema")
    found = found if isinstance(found, dict) else {}
    findings: list[Finding] = []
    wanted = ref_name(declared)
    if wanted is not None and wanted != ref_name(found):
        findings.append(
            Finding(
                contract.path,
                at,
                f"the contract points {name} at the schema {wanted} on {shown}; "
                f"the dump points it at {ref_name(found)!r}",
            )
        )
    for key in _CONSTRAINTS:
        if key in declared and declared[key] != found.get(key):
            findings.append(
                Finding(
                    contract.path,
                    at,
                    f"the contract freezes {key} {declared[key]!r} on the parameter "
                    f"{name} of {shown}; the dump says {found.get(key)!r}",
                )
            )
    return findings


def _compare_schema(
    contract: Contract, name: str, schema: dict[str, Any], dump_schema: dict[str, Any]
) -> list[Finding]:
    """Fields the contract names, and only those.

    A field the contract lists without a `type` freezes its existence and nothing else.
    That is the useful default for an optional field, which Pydantic renders as
    `anyOf: [{...}, {type: null}]` with no `type` of its own -- stating `type: string`
    for one of those would be freezing a shape the dump never had.
    """
    findings: list[Finding] = []
    where = contract.path
    properties = schema.get("properties")
    dump_properties = dump_schema.get("properties")
    dump_properties = dump_properties if isinstance(dump_properties, dict) else {}
    required = set(schema.get("required") or [])
    dump_required = set(dump_schema.get("required") or [])

    # The schema's OWN constraints, not only its fields'. A schema with no `properties`
    # -- an enum, a scalar alias -- used to be compared against nothing whatsoever: the
    # loop below iterated an empty dict and this function returned clean. That is how
    # `GuestbookEntrySort` came to freeze a closed set that no check has ever read.
    for key in _CONSTRAINTS:
        if key in schema and schema[key] != dump_schema.get(key):
            findings.append(
                Finding(
                    where,
                    contract.lines.get(("components", "schemas", name), 0),
                    f"the contract freezes {key} {schema[key]!r} on the schema {name}; "
                    f"the dump from app/schemas/ says {dump_schema.get(key)!r}",
                )
            )

    for field, declared in (properties if isinstance(properties, dict) else {}).items():
        at = contract.lines.get(("components", "schemas", name, "properties", field), 0)
        found = dump_properties.get(field)
        if not isinstance(found, dict):
            findings.append(
                Finding(
                    where, at, f"the contract freezes {name}.{field}; the dump has no such field"
                )
            )
            continue
        if not isinstance(declared, dict):
            continue
        for key in _CONSTRAINTS:
            if key in declared and declared[key] != found.get(key):
                findings.append(
                    Finding(
                        where,
                        at,
                        f"the contract freezes {key} {declared[key]!r} on {name}.{field}; "
                        f"the dump from app/schemas/ says {found.get(key)!r}",
                    )
                )
        if (field in required) != (field in dump_required):
            was, now = ("required", "optional") if field in required else ("optional", "required")
            findings.append(
                Finding(
                    where,
                    at,
                    f"the contract freezes {name}.{field} as {was}; the dump makes it {now}. "
                    "Either direction is a breaking change for somebody.",
                )
            )
    return findings


def _compare_contract(
    contract: Contract,
    dump_paths: dict[str, Any],
    dump_schemas: dict[str, Any],
    router_source: str,
) -> tuple[list[Finding], set[str]]:
    """Every sentence of one contract, and the path prefixes it thereby claims."""
    findings: list[Finding] = []
    claimed: set[str] = set()
    where = contract.path
    document = contract.document

    paths = document.get("paths")
    for path, item in (paths if isinstance(paths, dict) else {}).items():
        claimed.add(_prefix(str(path)))
        dump_item = dump_paths.get(path)
        if not isinstance(dump_item, dict):
            findings.append(
                Finding(
                    where,
                    contract.lines.get(("paths", str(path)), 0),
                    f"the contract freezes the path {path}; the dump has no such path",
                )
            )
            continue
        for method, operation in (item if isinstance(item, dict) else {}).items():
            if method not in _METHODS or not isinstance(operation, dict):
                continue
            dump_operation = dump_item.get(method)
            if not isinstance(dump_operation, dict):
                findings.append(
                    Finding(
                        where,
                        contract.lines.get(("paths", str(path), method), 0),
                        f"the contract freezes {method.upper()} {path}; the dump does not "
                        "serve that method on that path",
                    )
                )
                continue
            findings += _compare_operation(contract, str(path), method, operation, dump_operation)

    components = document.get("components")
    schemas = (components or {}).get("schemas") if isinstance(components, dict) else None
    for name, schema in (schemas if isinstance(schemas, dict) else {}).items():
        dump_schema = dump_schemas.get(name)
        if not isinstance(dump_schema, dict):
            findings.append(
                Finding(
                    where,
                    contract.lines.get(("components", "schemas", str(name)), 0),
                    f"the contract freezes the schema {name}; the dump has no schema by that name",
                )
            )
            continue
        if isinstance(schema, dict):
            findings += _compare_schema(contract, str(name), schema, dump_schema)

    # `x-refusals` -- the half of the contract the dump structurally cannot carry.
    refusals = document.get("x-refusals")
    names = refusals if isinstance(refusals, dict | list) else {}
    for code in names:
        at = contract.lines.get(("x-refusals", str(code)), 0)
        if f'"{code}"' not in router_source and f"'{code}'" not in router_source:
            findings.append(
                Finding(
                    where,
                    at,
                    f"the contract freezes the refusal code {code}; no router module "
                    "under app/ contains it as a literal. FastAPI never puts these in "
                    "openapi.json, so this line is the only thing holding the code still.",
                )
            )
    return findings, claimed


def compare(contracts: list[Contract], dump: dict[str, Any], router_source: str) -> list[Finding]:
    """Every contract against the dump, plus the one rule that runs the other way."""
    findings: list[Finding] = []
    dump_paths = dump.get("paths")
    dump_paths = dump_paths if isinstance(dump_paths, dict) else {}
    components = dump.get("components")
    dump_schemas = (components or {}).get("schemas") if isinstance(components, dict) else None
    dump_schemas = dump_schemas if isinstance(dump_schemas, dict) else {}

    claimed: set[str] = set()
    for contract in contracts:
        found, staked = _compare_contract(contract, dump_paths, dump_schemas, router_source)
        findings += found
        claimed |= staked

    for path in sorted(dump_paths):
        if not str(path).startswith("/api/") or _prefix(str(path)) in claimed:
            continue
        findings.append(
            Finding(
                "openapi.json",
                0,
                f"{path} is served and no contract under contracts/openapi/ claims the prefix "
                f"{_prefix(str(path))}. A boundary the application answers on and no contract "
                "describes is the state this directory exists to end.",
            )
        )
    return findings


def router_source(app_root: pathlib.Path) -> str:
    """Every router module under `app/`, concatenated.

    The tree is cut by bounded context, so routers live at
    `app/contexts/<name>/routers/` and `app/platform/routers/` rather than in one
    directory. A reader pointed at a single path would find nothing after the
    recut and every refusal code would go unfrozen -- silently, because "the
    literal is absent" and "the directory is absent" produce the same answer.
    """
    if not app_root.is_dir():
        return ""
    modules = sorted(
        path for routers in app_root.glob("*/routers") for path in routers.glob("*.py")
    )
    modules += sorted(
        path for routers in app_root.glob("*/*/routers") for path in routers.glob("*.py")
    )
    return "\n".join(path.read_text(encoding="utf-8") for path in modules)


def scale(contracts: list[Contract]) -> dict[str, int]:
    """How much was checked, printed whether or not anything was wrong.

    A subset comparison is only as strong as the contract is complete, so the number of
    frozen sentences is not decoration: it is the reader's only way to tell a contract
    that agrees with the code from one that says almost nothing.
    """
    paths = operations = responses = fields = refusals = parameters = 0
    for contract in contracts:
        document = contract.document
        items = document.get("paths")
        for item in (items if isinstance(items, dict) else {}).values():
            paths += 1
            for method, operation in (item if isinstance(item, dict) else {}).items():
                if method not in _METHODS or not isinstance(operation, dict):
                    continue
                operations += 1
                declared = operation.get("responses")
                responses += len(declared) if isinstance(declared, dict) else 0
                listed = operation.get("parameters")
                parameters += len(listed) if isinstance(listed, list) else 0
        components = document.get("components")
        schemas = (components or {}).get("schemas") if isinstance(components, dict) else None
        for schema in (schemas if isinstance(schemas, dict) else {}).values():
            properties = schema.get("properties") if isinstance(schema, dict) else None
            fields += len(properties) if isinstance(properties, dict) else 0
        refusals += len(document.get("x-refusals") or {})
    return {
        "contracts": len(contracts),
        "paths": paths,
        "operations": operations,
        "responses": responses,
        "parameters": parameters,
        "fields": fields,
        "refusals": refusals,
    }


_ADVICE: Final = """
The contract is the authority (constitution, Article VI). Close the gap on ONE side:
  1. the code is right     -> edit the contract under contracts/openapi/, raise info.version,
                              and declare the edit in this change's delta.md
  2. the contract is right -> edit the context's schemas/ or routers/ until the dump satisfies it
Never by copying the dump into the contract: a contract produced from the dump is not a
contract, it is a copy -- and `contracts` refuses one.
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check the application against the hand-written OpenAPI contract."
    )
    parser.add_argument("--dump", type=pathlib.Path, default=DEFAULT_DUMP)
    parser.add_argument("--contracts", type=pathlib.Path, default=DEFAULT_CONTRACTS)
    parser.add_argument("--routers", type=pathlib.Path, default=ROUTERS)
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    arguments = parser.parse_args(argv)

    contracts, findings = read_contracts(arguments.contracts, REPO_ROOT)
    if not contracts and not findings:
        message = (
            f"{_relative(arguments.contracts, REPO_ROOT)}: holds no *.yaml, so there is "
            "nothing to compare. This is a named gap, not a pass."
        )
        if arguments.json:
            print(json.dumps({"gap": message, "scale": scale([]), "findings": []}, indent=2))
        else:
            print(message, file=sys.stderr)
        return EXIT_NOTHING

    if not arguments.dump.is_file():
        print(
            f"{_relative(arguments.dump, REPO_ROOT)}: [openapi] the dump is missing. "
            "./scripts/contracts.sh writes it with scripts/dump_openapi.py before comparing.",
            file=sys.stderr,
        )
        return EXIT_MISMATCH

    dump = json.loads(arguments.dump.read_text(encoding="utf-8"))
    if not isinstance(dump, dict):
        print(
            f"{_relative(arguments.dump, REPO_ROOT)}: [openapi] the dump is not an object",
            file=sys.stderr,
        )
        return EXIT_MISMATCH

    findings += compare(contracts, dump, router_source(arguments.routers))
    measured = scale(contracts)

    if arguments.json:
        print(
            json.dumps(
                {"scale": measured, "findings": [f._asdict() for f in findings]},
                indent=2,
                ensure_ascii=False,
            )
        )
        return EXIT_MISMATCH if findings else EXIT_OK

    for finding in findings:
        where = f"{finding.path}:{finding.line}" if finding.line else finding.path
        print(f"{where}: [openapi] {finding.message}")
    counted = ", ".join(f"{value} {key}" for key, value in measured.items())
    print(f"{len(findings)} problem(s) against {counted}")
    if findings:
        # Flushed first, or the advice lands above the findings it is about whenever
        # stdout is a pipe (block-buffered) and stderr is not.
        sys.stdout.flush()
        print(_ADVICE, file=sys.stderr)
        return EXIT_MISMATCH
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())

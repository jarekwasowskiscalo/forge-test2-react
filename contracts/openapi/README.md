# HTTP contract

One `.yaml` file per API area, in OpenAPI 3.x, **written by hand and committed**. The rules
behind the shapes are in [`spec/design/api.md`](../../spec/design/api.md); this directory
carries the same thing in a form a machine can compare against the running application.

**Contracts:** `guestbook.yaml` (guestbook entries, `/api/guestbook-entries`) and
`health.yaml` (the `/api/health` probe). Compatibility mode of both: **Backward** (below).

## Convention

- **One file per area**, named after the area. A file claims every path whose first two
  segments it names — `/api/guestbook-entries` also covers
  `/api/guestbook-entries/{entry_id}`.
- **`info.version` is the contract's version.** It rises when any frozen sentence changes. A
  breaking change raises the major version.
- **Compatibility mode: Backward.** A path, an operation, a response code and an optional
  field may be added. Removing a field, changing a type, narrowing a numeric bound and
  changing a stable refusal code are breaking.
- **`x-refusals`** lists the stable refusal codes. They appear in no OpenAPI document,
  because FastAPI does not look inside the body of a raised exception — and
  `spec/design/api.md` calls them a contract that "never changes". This list is the only
  place that holds them.

## The contract is a SUBSET of the dump, and that is the whole construction

Every sentence the contract states must be true of the dump. The dump may carry more — and
inevitably does: an `operationId` derived from the function name, a `title` generated from
field names, `ValidationError`, and a `422` added to every operation that takes a parameter.

The consequence worth knowing while writing a contract: **what you write is what you freeze,
and nothing else.** A field named without a `type` freezes its existence and no more — which
is the right default for an optional field that Pydantic renders as an `anyOf` with `null`. A
numeric bound is compared if and only if the contract states it.

One rule runs the other way, because without it "subset" would mean "an empty contract
passes": **every `/api/*` path the application serves must fall under a prefix some contract
here claims.** Deliberately one level deep — a new path is a new boundary, which is a
decision; a new optional field is an extension.

## The gate

```bash
./scripts/contracts.sh
```

It rebuilds `openapi.json` from the Pydantic schemas (an intermediate artefact, gitignored —
in git it would set) and compares it against every contract here. The engine is
`scripts/openapi_contract.py`, which does not import the application: it reads two documents
and the source of the routers as text. Exit code `4` means "there is nothing to compare" and
is a **named gap**, never a pass.

A divergence is closed on **one** side: either the contract was wrong and its version rises,
or the code was wrong and the context's `schemas/` or `routers/` changes. Never by copying the dump
into the contract — `contracts` refuses a file carrying a generator banner, and that is the rule
that defends the whole construction.

# `contracts/` — system boundaries as versioned contracts

A boundary is where this system meets something it does not compile together with itself:
somebody else's HTTP client, somebody else's event consumer, yesterday's database state. At
a boundary **the contract is the authority and the code is validated against it, not the
other way round** — that is [Article VI of the constitution](../spec/constitution.md),
marked `[CRITICAL]`.

This directory is that article turned into files. It is not documentation of the
boundaries; it is the set of documents the boundaries are checked against on every run.

## Why a contract is written rather than generated

A contract derived from code carries exactly as much truth as the code happened to declare
— and is silent exactly where the code is silent. This is not a hypothesis: in this
repository a context's `routers/` used to raise a `404` refusal without declaring it in a decorator,
so the Pydantic dump did not know about it, `frontend/src/api/schema.d.ts` had no type for it, and
the frontend normalised it by hand. A normative document promised it the whole time and nobody
had anything to compare the promise against — until the contracts below existed (§ Four boundaries
says how the refusal is declared now).

So a file under `contracts/` is **written by hand and committed**, while the machine's
output (`openapi.json`) stays output and is gitignored. Gate `contracts` refuses a file carrying a
generator banner — a copy of a dump has no authority over what it was copied from.

**Decision of 2026-09-02, rejected alternatives:**

- **Keep the Pydantic-first direction and not build `contracts/`** — this would require
  changing Article VI, and the article speaks of *every* boundary, not of the HTTP boundary.
  Changing an article costs incomparably more than one directory and one gate.
- **Compare both documents for full equality after normalisation** — the exclusion list
  (`operationId` from the function name, `title` from field names, `ValidationError`, `anyOf`
  with `null`, key order) *would* then be the real scope of the contract, only written in
  Python and discovered by trial; every FastAPI version bump would redden every pull request.
- **Compare a chosen projection for equality** — equality is symmetric, and symmetry says
  "the dump is an authority too", which is precisely what this decision reverses.
- **Generate the contract from the dump and commit the result** — a copy of a dump has no
  authority over what it was copied from; `contracts` refuses a generator banner exactly so that
  this alternative cannot come back with one shell command.

The comparison is therefore a **subset**: every sentence of the contract must be true of the
dump, and the dump may carry more — with one rule in the other direction: every `/api/*` path
the application serves must be covered by some contract's prefix, because without it "subset"
would mean "an empty contract passes". A contract has to be written and maintained — for this
template that is three paths, six operations and eight schemas — and refusals with codes had
to stop being prose: `app/platform/schemas/refusals.py` declares their shape, the routers name it in
`responses=`, and that is why `frontend/src/api/schema.d.ts` carries a `Refusal` type.

## Compatibility mode

A contract with no declared mode does not say whether it may be deployed before the code or
after — and that is a question answered at three in the morning. Each subdirectory declares
one of three values in its own `README.md`:

| Mode | What is allowed without a major version bump |
|---|---|
| **Backward** | adding optional things: a new optional field, a new path, a new response code |
| **Forward** | removing optional things; an old sender gets along with a new receiver |
| **Full** | only changes that are both at once |

Removing a field, changing its type, narrowing a numeric bound and changing a stable refusal
code are **breaking** in all three modes and require a major version bump.

## Four boundaries, three directories

| Boundary | Where its contract lives |
|---|---|
| HTTP | `contracts/openapi/` |
| events and messages | `contracts/asyncapi/` |
| data invariants | `contracts/invariants/` |
| database schema | **`alembic/versions/`** — not here |

**There is no directory here for the database schema, and that is a decision rather than a
gap.** The set of Alembic revisions *is* the schema contract: it is versioned by revision id,
ordered, released once and never edited after release. Its owner is `alembic/versions/`, and
the application does not create the schema itself —
[`spec/design/data-model.md`](../spec/design/data-model.md) § Owner of the schema. A second
directory would carry either a copy of that SQL or a pointer to it; the copy diverges on the
first change, and a pointer is not a contract. The schema's compatibility mode is declared
beside the schema, in `spec/design/data-model.md`.

## What enforces this

| Check | What it holds |
|---|---|
| `contracts` | a file under `contracts/` is hand-written, versioned, and names the check that enforces it |
| `delta-coverage` | a contract change is declared in its change's `delta.md` |
| `english` | a document under `contracts/` is written in English — as are the fields of the contracts themselves |
| `./scripts/contracts.sh` | **the comparison**: every sentence of the HTTP contract is true of the running application |

The first three are cheap and textual. The fourth is the one this directory exists for.
The full gate table: [`CLAUDE.md`](../CLAUDE.md).

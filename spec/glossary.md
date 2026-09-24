# Glossary

Domain words used across the repository, with the source form that is the identifier in the
code. A term that means something **only inside one context** lives in that context's
document, not here. With two contexts the split is no longer an exercise: a word earns a row
here when it names a context, or when it means one thing on one side of a boundary and another
thing on the other, or in the process (`Session` and `Task`, below). The guestbook's rows were
written while it was the only context, and they stay until a change moves them into its
document.

The language rule behind this: the whole repository is written in English, and a **domain term
keeps its source form inside an identifier** — so that a field can be grepped from a sentence
in the specification to a column in the database (`spec/design/conventions.md` § Language).

| Term | Meaning |
|---|---|
| **Guestbook** | A bounded context: the set of entries left by guests. It shares one rule with the to-do list, how a text is trimmed and measured, and nothing else ([`contexts/todo_list.md`](contexts/todo_list.md) § Neighbours). |
| **To-do list** | A bounded context: the one list of tasks every visitor shares, each task one line of text that is done or not done. Its words (task, done, the moment of adding) are defined in [`contexts/todo_list.md`](contexts/todo_list.md) § Language. Source form `todo_list`. |
| **Task** | One line of text on the to-do list, done or not done; defined in [`contexts/todo_list.md`](contexts/todo_list.md) § Language. Source form `TodoTask`, table `todo_tasks`: the identifier is qualified because *task* is also a process word (below), and an unqualified `task` would be found by every search for the other one. |
| **Entry** | One utterance by a guest: a signature, a message, the moment it was written and the moment it was last amended. The smallest thing this system stores. Table `guestbook_entries`. |
| **Author** | What the guest signed with. **It is not an identity** — the system authenticates nobody, so a signature is a claim rather than a statement of fact. Column `author`. |
| **Message** | What the guest wrote. Column `message`. |
| **Edited** | An entry whose moment of last amendment differs from its moment of writing. A fact **derived** by comparing `created_at` and `updated_at`, never stored (`BR-02`). |

## Process words, not domain words

They live here because they come up in every conversation about this repository and get
confused with domain words.

| Term | Meaning |
|---|---|
| **Bounded context** | A slice of the domain with its own vocabulary and its own document under `spec/contexts/`. The same word is allowed to mean different things in two contexts; that is the entire reason the boundary exists. |
| **Strategic classification** | What a context is worth: **core** is what the product competes on, **supporting** is specific to this business but not a differentiator, **generic** is what you would buy if somebody sold it. Declared as `classification` in a context document's front matter, and it decides how much modelling a context deserves. |
| **Integration pattern** | What one context does about another's model at the seam — an anti-corruption layer translates it, a conformist adopts it whole, an open host service publishes one. Declared per neighbour as `<context>:<role>:<pattern>`; the legal pairings and the reason they are the legal ones are in [`../.specconf/templates/system/context.md`](../.specconf/templates/system/context.md) § Neighbours. A boundary recorded only as a direction says who calls whom and not what breaks when they change. |
| **Golden set** | `golden-set/` — the only home of committed data this project ships, cut in two by what the data is for: **fixtures** and **seed data** (both below). One locator, `tests/_golden_set.py`, decides where either half lies. |
| **Fixtures (the fixture half)** | `golden-set/fixtures/` — what the suites read instead of inventing, and assert about: ordinary, boundary and refused entries. Wiped before every scenario. |
| **Seed data (the seed half)** | `golden-set/seed/` — what a freshly created environment opens with, so a preview or a fresh clone shows a screen somebody can judge. Posted through the application's own API by `scripts/seed.sh`; asserted about by nothing, which `tests/fitness/test_golden_set.py` enforces. |
| **Escape hatch** | Historical: SQLite as the database for a machine without Docker. Removed 2026-08-31 ([`design/architecture.md`](design/architecture.md) § One engine) — today such a machine points at its own Postgres through `APP_TEST_DATABASE_URL`. The term stays, because archived change records still read it. |
| **Fitness function** | A test that reads **this repository's source as text**, to hold a structural rule no compiler enforces. `tests/fitness/`. |
| **sdd107** | An external text on ownership-first architecture the author drew on when cutting the tree by bounded context; cited in `design/conventions.md` § Backend, `design/architecture.md` and `.github/CODEOWNERS`. **It is not in this repository and cannot be checked from it** (found by the 2026-09-08 audit): the reasoning written beside each citation is this repository's own and is meant to stand without it, so the name is an attribution, not an authority. |
| **Session** | In this repository **always** a SQLAlchemy unit of work (`SessionLocal`). There is no user session, because there is no authentication — and when the product adds one, this is exactly the trap to name: two different concepts, one word. |
| **Task (process)** | A unit of planned work in a change's `tasks.md` (`T-n`), and the job one script under `scripts/` does. **Never the domain's task**, which is a line on the to-do list (above). The same trap as `Session`: two concepts, one word — which is why the domain's identifiers say `todo_task` and never a bare `task`. |

## Identifiers and their spaces

Every space has exactly one home in which a citation resolves. The `frozen-ids` gate holds this for
the first five spaces below — an identifier named in prose and defined nowhere goes red. A change
id and a requirement id are held by the change record and `traceability` instead.

| Space | Means | Home |
|---|---|---|
| `P-xx` | a flow within a context | `spec/contexts/<context>.md` |
| `BR-xx` | a business rule | `spec/contexts/<context>.md` |
| `S-xx` | a screen | front matter of `spec/design/ui/<screen>.md` |
| `D-xx` | a data invariant | `contracts/invariants/<domain>.md` |
| `ADR-xxxx` | a dated decision from a change record | `spec/ADR/` (empty today — [`design/conventions.md`](design/conventions.md) § When a decision is an ADR) |
| `CR-YYMM-xxxx` | a change | `spec/changes/` |
| `CR-YYMM-xxxx/R-n` | a requirement of a change | that change's `requirements.md` |

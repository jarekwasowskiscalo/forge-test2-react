# Constitution

The rules the process itself is subject to. Specifications, designs, code and agents are
subordinate to this document; where anything below disagrees with it, this document wins.

Every article carries an enforcement level. **[CRITICAL]** blocks a merge, and an agent is to
stop and escalate rather than work around it. **[SHOULD]** is a strong default whose departure
needs a reason recorded in the change. **[MAY]** is guidance.

Changing an article requires an ADR in [`ADR/`](ADR/).

---

## Article I — The specification is the source of truth [CRITICAL]

Behaviour is described in `spec/` before it is built. Code contradicting `spec/` is either a
defect in the code or a change not applied to the specification. It is never an accepted
divergence, and "the code is the documentation" is not an answer this project accepts.

It is the specification, not the code, that the next person reads at three in the morning. The
code says what happens; only the specification says what was *meant* to happen — and that is the
only thing that lets anybody tell a feature from a bug.

## Article II — Requirements are testable sentences with identifiers [CRITICAL]

A requirement uses the EARS keywords — `WHEN`, `WHILE`, `IF … THEN`, `WHERE` — together with
`MUST` or `SHALL`. Never *should*, *may*, *could*, *probably* or *etc.* A requirement that
cannot be failed cannot be satisfied.

Every requirement carries a unique identifier scoped by its change (`CR-2608-a7f3/R-3`) and
every one has acceptance criteria written as Given/When/Then. A criterion no observer could
check is not a criterion.

## Article III — Every requirement is proved by a test [CRITICAL]

No requirement travels without at least one test that refers to it by identifier. The reference
is mechanical — a `req` marker, a Gherkin tag or the identifier in a test's name — and the
`specs` gate checks both directions: a requirement nothing refers to fails, and a reference to a
requirement that does not exist also fails. The second half matters more than the first, because
a typo is what every traceability scheme actually dies of.

Where a requirement genuinely cannot be tested automatically, it says so about itself in its own
text (`**Verified-by:** manual — <reason>`). The exception is then counted and printed, and that
is the difference between a gap considered and a gap passed over.

## Article IV — The specification changes on the same branch as the code [CRITICAL]

A change of behaviour and the specification edit that describes it land in one pull request.
Never in the next one. The next one guarantees a window in which the trunk describes code that
no longer exists, and it rests on a step nobody is blocked by.

Every edit under `spec/` is declared in that change's `delta.md` as `ADDED` / `MODIFIED` /
`REMOVED` together with a `**Why:**`. The declared set and the actual diff must be *equal* — an
edit absent from the delta fails, and a delta entry with no edit also fails.

## Article V — Non-goals are written down [SHOULD]

Every change says what it deliberately does **not** do. Silent scope is what makes a reviewer
and an author finish agreeing about two different things, and what turns a "missing" feature
into an argument six months later rather than a decision anybody remembers.

## Article VI — A rule the database does not hold is not a rule [CRITICAL]

A constraint the application relies on and the storage layer does not enforce is a constraint
that falls over under concurrency. Business uniqueness is a unique index rather than a
convention: a rule checked by read-before-write passes every sequential test and lets two
concurrent requests through. The same principle governs every boundary: the contract is the
authority and the code is validated against it, not the other way round.

## Article VII — Ambiguity is a question, never an improvisation [CRITICAL]

Where a requirement, a field, a label or a rule is unclear, the process stops and asks a human.
It does not pick the more likely reading and does not rationalise the choice in an artefact
where the next reader will take it for a decision.

The question is closed — two to four options, the recommendation first, each with its
consequence in one sentence — with free text always available. A free-text answer is
interpreted, announced and recorded; it never produces the same question a second time.

## Article VIII — A divergence is a measurement and it edits the specification [CRITICAL]

Independent artefacts are produced in parallel from one specification, and a disagreement
between them is not an accident to patch. It is a measurement of where the specification was
ambiguous.

Every settled disagreement is followed by an edit to the *earliest* document which, had it been
clearer, would have prevented it. Fixing only the artefact at the end of the chain leaves the
ambiguity in place, and the next change walks into it again.

A ruling may be taken automatically **only** when it follows from a document higher in the
hierarchy, and the record must name that document and section:

```
constitution.md  >  invariants.md  ~  contracts/invariants/  >  design/**  >  a change's requirements  >  a change's design
```

`invariants.md` and `contracts/invariants/` stand on the **same rung**, because after the move
they are two halves of one document: the first holds the deliberate non-goals and the rule about
the rules themselves, the second the data invariants. The order between them is arbitrary and
stays that way until the first case in which a non-goal and a data invariant contradict each
other; then a human decides, not this arrow.

Everything else is a product decision and belongs to a human.

## Article IX — The why is recorded where it cannot be edited out [CRITICAL]

A decision is an ADR when it rejects a named alternative **and** is cross-cutting — reversing it
touches more than one module, layer or suite — **and** is expensive to reverse: undoing it needs
a data migration, a rewritten contract or a change in CI, not an edit to one file. An ADR is
dated, numbered, never rewritten, and superseded only by a later ADR. Normative documents state
the rule in the present tense and link to it.

A decision that only rejects an alternative is also recorded and has its address: a fact always
true of the data goes to `contracts/invariants/`, a deliberate non-goal to `spec/invariants.md`,
a placement or naming rule to `spec/design/conventions.md`, the choice of a suite or a fixture
to `spec/design/testing.md`, a column or a constraint to `spec/design/data-model.md`, a contract
field or a refusal code to `spec/design/api.md`. All five are normative, so the rule binds
exactly as hard as it would in `ADR/` — it merely stops costing a row in an index everybody has
to read before writing the next decision. The threshold and the table of homes:
[`design/conventions.md`](design/conventions.md) § When a decision is an ADR.

Beside ADRs, **intent** is recorded in the code itself: a non-obvious rule carries the reason it
exists, and where there was an incident — that incident. This project already writes that way —
[`scripts/check.sh`](../scripts/check.sh) names the failure behind every gate it runs — and it is
the main defence against somebody "simplifying" a rule whose cost is invisible from a diff.

Module docstrings cite the specification: `spec/design/data-model.md`, `BR-02`, `P-01`,
`CR-2608-a7f3/R-3`. Keep that density.

## Article X — Between two steps the application works [CRITICAL]

After every stage the full gate runs and must be green. A stage never ends red.

The only exception is a failure the process created deliberately: a test written before its
implementation. Such a failure is declared *before* the run that shows it, must be proved to
have actually occurred, and expires. A declaration made after seeing the failure, or a declared
failure the runner does not even collect, fails the gate — otherwise deleting a failing test
reads exactly like fixing it.

## Article XI — Personal data does not leave the machine that needs it [CRITICAL]

This template holds no personal data today — a guestbook entry is a signature somebody gave
themselves. A product built from it will hold some, and an assertion message can quote every
value a test saw. That is the reason [`pyproject.toml`](../pyproject.toml) sets
`junit_logging = "no"` and the reason no committed artefact — a state file, a report, a change
record — carries the text of a test failure. Identities and counts, never contents.

One exception, and it is named rather than implied: `spec/changes/*/sessions/**` holds raw Claude
Code transcripts, deliberately unsanitised, so that the process can be studied from what actually
happened. The archive counts the shapes of personal data it carries and refuses to hide that
count; the price is that nothing may be pasted into an SDD session that is not to live in that
history forever. The exception extends to that path and to nothing else.

Authentication, personal data and every regulated surface require a human decision. An agent
escalates; it never merges such a change on its own.

## Article XII — The project's scripts are the interface [CRITICAL]

Every task is a script. Run the script, never a command from inside it: each checks its own
prerequisites, and those checks exist because their absence produced failures that took a day to
find. `scripts/check.sh` is the definition of "will CI pass" — a gate added to CI belongs there
too, and a fitness function proves the two lists are equal rather than believing they are.

There are two interfaces, and which directory a script sits in says which one it is.

[`scripts/`](../scripts/) is the **human's** interface to the application — running, testing,
linting, migrating. Run by a person or by CI. Every task exists there as **one** `.sh` script
over the shared `_lib.sh`; task scripts written in Python are libraries that the `.sh` calls,
not a second entry point to the same task.

The scripts are POSIX and that is a decision rather than neglect
([`design/conventions.md`](design/conventions.md) § Scripts). Windows is supported through WSL
or Git Bash and through nothing else; a named absence of support is more honest than a second
copy of every script that diverges in the week nobody is looking at it.

[the engine](https://github.com/Scalo-Sales-Engineering-Consulting/claude-marketplace/blob/main/plugins/forge/skills/_shared/sdd/) is the **agent's** interface to
the change *process*. Called by the skills that name it, from the repository root, one
implementation per platform. It ships with those skills — in the plugin, not in this
repository — so that a skill and the script it calls change together, and `skill_lint.py`
breaks the build when they do not. The process's own
commands under [the process's own `bin/`](https://github.com/Scalo-Sales-Engineering-Consulting/claude-marketplace/blob/main/plugins/forge/bin/) are the bridge — its CI runs a shell script, and
the shell script runs Python. `scripts/` is the application's interface and never calls the
process; what the process may call in `scripts/` is the script contract
([`script-contract.md`](https://github.com/Scalo-Sales-Engineering-Consulting/claude-marketplace/blob/main/plugins/forge/docs/script-contract.md)).

Rejected (decision of 2026-09-09, `cr: historical` — the process became independent of the
application it works on: a template ships `scripts/` and a stack profile, the process ships
the process's own commands and reads the profile; two trees, two CIs, one contract between them): a script
in `scripts/` as the bridge from the application's CI into the process. It made the application
depend on the process, in the one direction the split forbids, and it put a gate the process
owns into a list the template's CI keeps.

Neither directory is a place to opt out of anything. Both are covered by `ruff` and
`mypy --strict`; choosing a folder has never been a way to lower the standard here.

## Article XIII — Allowed and forbidden [CRITICAL]

**Allowed.** Python ≥ 3.12, FastAPI, SQLAlchemy 2.0 with Alembic, Pydantic 2, PostgreSQL 16 and
only it ([`design/architecture.md`](design/architecture.md) § One engine), `uv` in the range
`>=0.12,<0.13`; TypeScript 5.9, React 19, Vite, TanStack Query, react-hook-form with zod,
Tailwind 4 over CSS design tokens; pytest, pytest-bdd, vitest, testcontainers; Playwright
(Chromium alone) only in `e2e/ui/` — [`design/testing.md`](design/testing.md) § The UI smoke in
a browser.

**Forbidden.** Business logic in routers. `fastapi` or `starlette` imported from `services/`,
`models/` or `schemas/`. `create_all()`. A raw hex colour or a magic pixel size in a component.
A file named `utils.py`, `helpers.py`, `common.py`, `format.ts` or `utils.ts`. Star imports,
with one mechanical exception documented in
[`design/architecture.md`](design/architecture.md). Unpinned tool versions in a gate. Logging
secrets, tokens or personal data.

## Where the process's own files are named

Rejected (decision of 2026-09-09, `cr: historical` — the change process left this repository
for the plugin `forge@scalo`. Article XII still holds word for word: a tool the stack
profile refuses is not run by hand, and the process's own commands are the bridge from the
process into Python. What changed is only where those commands come from — they arrive on
PATH with the plugin instead of sitting in a directory of this repository's — so the article's links now name
the repository that ships them. No article was reworded; `spec/ADR/` stays empty until the
first change goes through `/forge:sdd`, and framework changes are made on the trunk and carry no
`delta.md`): rewording Article XII to describe a plugin. The article is about not assembling
commands by hand, which is true of every layout, and an article edited to track a directory
would need editing again at the next move.

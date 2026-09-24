<!-- TEMPLATE: filled in by the design stage; the file counts as non-existent until this marker is gone -->
# Delta fragment — `<author name>`

*One fragment per author, in `design/delta/<name>.md` or `reconcile/delta/<name>.md`.
`close_stage` assembles `delta.md` out of them, deterministically — do not edit `delta.md`
by hand. Eight authors appending in parallel to one file is a merge conflict in a document's
costume, and that is the only file where they would meet.*

*Where each part of this fragment goes: the `ADDED`/`MODIFIED`/`REMOVED` entries go into the
brief, `delta.md`, one per path — a reconciliation entry about a file the design already
named supersedes it there, and the superseded one is kept in `delta-history.md`. Everything
else here, the table below included, goes to `delta-history.md` too. Nothing is dropped, so
write the entry for a reader of the brief and the table for the boundary that reads it.*

- `MODIFIED` `spec/design/<document>.md`
  **Why:** <at least 80 characters — the reason, not a paraphrase of the change; why the
  system is to behave this way>
  **ADR:** <ADR-nnnn or `none — <reason>` when the edit is editorial>
  **Requirements:** <CR>/R-n, <CR>/R-m

## This change owns

*The paths **this change** may touch, and nothing else. `sdd-engine change_state set-boundary
--cr <CR> --from-design` reads this table out of the fragments and records it; from then on
every wave's `git diff --name-only` is compared against what it recorded. A directory ends in
`/` and owns what is under it; a file is owned exactly, and nothing beside it.*

*What it records is this table **plus the trees the reconciliation will write** — the write
allowlists the engine declares for the `spec_sync` members this composition dispatches, which
live in the engine and in no project file, so there is nothing local for you to read them out
of. Do not list them here: the engine adds them because it is the only party that knows the
composition, and `set-boundary` prints what it added. Everything else is yours, including
every tree the implement fan-out writes — a path you leave out is a path its author is
refused.*

*Who fills it in: the author whose preflight envelope says `owns_boundary_section: true` —
`design-architecture` when the composition runs it, and `design-spec` when it does not. One
author per composition, so two fragments never state a boundary that disagrees.*

| Path | Why |
|---|---|
| `<path>` | <one sentence — why this change needs to touch it> |

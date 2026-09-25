# Delta fragment — `review-converge`

*Written by the convergence round of coherence pass 10, `spec_sync` stage, for the seven findings
`COH-spec_sync-1` to `COH-spec_sync-7`. Findings 1 to 5 were settled automatically from the
document each one's `auto_basis` names; 6 and 7 by the user, at `Q-30` and `Q-31`. Each entry below
is an edit to the earliest document a finding names as its `ambiguity_source`, or the ready patch
under a finding where that patch lands in `spec/` or `contracts/`. `COH-spec_sync-6` has no entry:
its `ambiguity_source`, `docs/runbooks/restore-the-database.md` § When to use this, is under
`docs/`, which binds nothing and is outside the set Article IV makes a delta declare, and no
document in `spec/` or `contracts/` let the two readings in. The artefact repairs outside this
round's write set belong to their authors afterwards and are not declared here as made: the
`docs/` edits of `COH-spec_sync-6` and `COH-spec_sync-7`, the move of
`reconcile/user-guide-todo-list.md`, and the `--help` and comment text of `COH-spec_sync-5` in
`scripts/start.sh`, `scripts/help.sh`, `scripts/deploy.sh` and `scripts/preview.sh`.*

- `ADDED` `contracts/invariants/todo_list.md` § `D-05`
  **Was:** no file. `spec/design/data-model.md` § `todo_tasks` called, in the present tense, for "a data invariant of the to-do list's own under `contracts/invariants/`, the counterpart of `D-04`", and `contracts/invariants/` held `guestbook.md` alone.
  **Now:** `contract: invariants`, `domain: todo_list`, `version: 1`, and one entry: "`D-05` — a stored task's text is normalized, one line, and within its bound in code points". Every `text` in `todo_tasks` is NFC, carries no member of the written trim set at either end, holds none of the seven code points of `LINE_BREAKS`, and is 1 to `TODO_TASK_TEXT_MAX_LENGTH` (200) code points long (`BR-06`, `BR-07`). Its three witnesses are the ones `spec/design/testing.md` § CR-2609-823a, the to-do list names, and each exists: the service round trip, the corpus case and the generator. The ready patch landed as written, with the browser's corpus reader named by path, as `D-04` names its own.
  **Why:** COH-spec_sync-1. `spec/invariants.md` § Data invariants gives an invariant decided in design, whose witnesses the implementation stage writes, to the first convergence round after they exist, the `spec_sync` stage's; `testing.md` named that round, and the user decided it at `Q-21` (6): "stated in the data model now and written into the data-rules folder at the reconciliation stage, once its tests exist." None of the four `spec_sync` members writes `contracts/`, and each said so, so without this round the data model would have merged citing a contract that did not exist. `D-05` is the next free identifier: nothing in `contracts/` or `spec/` used it.
  **ADR:** none — it writes down, where data invariants live, a rule the data model already stated and the user already placed.
  **Requirements:** CR-2609-823a/R-2, CR-2609-823a/R-6
- `MODIFIED` `contracts/invariants/README.md` — the **Contracts:** line
  **Was:** "`guestbook.md` — `D-01`…`D-03`, each with a witness and a kind of evidence."
  **Now:** "`guestbook.md` — `D-01`…`D-04`; `todo_list.md` — `D-05`; each with a witness and a kind of evidence."
  **Why:** COH-spec_sync-1, the second half of its ready patch. The line is the directory's list of its contracts, and a new contract that the list does not name is found only by listing the directory. The count also corrects `D-03` to `D-04`: `guestbook.md` has held `D-04` since before this change, and the line never caught up.
  **ADR:** none — an index line brought level with the files it indexes.
  **Requirements:** CR-2609-823a/R-2, CR-2609-823a/R-6
- `MODIFIED` `spec/invariants.md` § Data invariants: one paragraph added after "Which stage's convergence round writes a new data invariant is settled by its witnesses"
  **Was:** the section named "the first convergence round after they exist — the `spec_sync` stage's" as the writer, and did not say what makes that round run.
  **Now:** "What makes that round run is its stage's coherence pass." No member of the `spec_sync` stage writes `contracts/`, so an invariant a design document calls for, whose witnesses exist and which `contracts/invariants/` does not yet hold, is a finding of that pass in its own right; a pass that finds nothing else still records it, or the stage closes with the invariant unwritten.
  **Why:** COH-spec_sync-1, its ambiguity source. A convergence round is sent only for what a coherence pass records, and nothing obliged the pass to record an invariant it owed. Every `spec_sync` member left the invariant to "the round", and a clean pass would have closed the stage with no round at all. Settled automatically by the section itself, whose route this sentence completes.
  **ADR:** none — it says what triggers an existing route, and no rule about the data moves.
  **Requirements:** CR-2609-823a/R-2
- `MODIFIED` `spec/glossary.md` § Identifiers and their spaces — the `ADR-xxxx` row
  **Was:** "`spec/ADR/` (empty today — `design/conventions.md` § When a decision is an ADR)".
  **Now:** "`spec/ADR/` (what it holds: `design/conventions.md` § When a decision is an ADR)", the link kept.
  **Why:** COH-spec_sync-2, its ambiguity source. This stage promoted `ADR-0001` and `ADR-0002`, and `conventions.md` § When a decision is an ADR, the paragraph the row cites as its authority, now says the directory holds them. The row restated the directory's state instead of only pointing at its home, so the promotion edited the home and left the copy false. Settled automatically by the constitution, Article IV: the edit describing a fact this change creates lands in its pull request.
  **ADR:** none — a pointer that stops restating what it points at.
  **Requirements:** CR-2609-823a/R-1
- `MODIFIED` `spec/README.md` — the `spec/ADR/**` bullet, its last sentence
  **Was:** "The directory is empty today: the template's decisions, taken without a change record, stand as "decision of <date>" paragraphs in the normative documents, and the first ADR will come out of the first change through `/forge:sdd`".
  **Now:** "The template's decisions taken without a change record stand as "decision of <date>" paragraphs in the normative documents. The ADRs here come out of changes carried out through `/forge:sdd`, the first two from `CR-2609-823a`", the link to `conventions.md` kept.
  **Why:** COH-spec_sync-2, the second of the two sentences its ready patch names. It said the directory holds nothing, while `spec/ADR/index.md` lists two ADRs. It is edited with the glossary row because the finding's resolution is one: both copies stop stating the directory's state. Settled automatically by the constitution, Article IV.
  **ADR:** none — a fact this change made true, and no rule moves.
  **Requirements:** CR-2609-823a/R-1
- `MODIFIED` `spec/ADR/ADR-0001-todo-list-is-its-own-bounded-context.md` § Consequences — the bullet "Deleting the guestbook is no longer the deletion of one unit", one sentence
  **Was:** "That edit is outside every write set of this change and was reported by `design-spec`, and nothing enforces it."
  **Now:** "`design-spec` reported that the list was silent, `reconcile-docs` wrote the paragraph in the `spec_sync` stage of this change, and nothing enforces it."
  **Why:** COH-spec_sync-3. The draft said "this change" and meant the stages its author could see, design and implement. In the same wave that promoted the ADR, reconcile-docs wrote the paragraph into `CLAUDE.md` § What is an example ("One thing moves before the guestbook goes"), so the sentence became false. Once accepted, an ADR is never edited (`spec/design/conventions.md` § When a decision is an ADR); it is still `Proposed`, so this is the last moment the sentence can be corrected. Settled automatically by the constitution, Article IV.
  **ADR:** this entry edits the ADR itself, before acceptance; the decision is unchanged.
  **Requirements:** CR-2609-823a/R-1
- `MODIFIED` `spec/design/architecture.md` § What a new environment starts with — the second paragraph, its last clause
  **Was:** "because "an environment nobody has written in yet" is one condition and not two."
  **Now:** "because "a list that holds nothing yet" is one condition, asked of each list, whatever kind of environment holds it."
  **Why:** COH-spec_sync-4. Six lines apart the section said "Each list is filled on its own" and named "an environment nobody has written in yet" as the condition. An environment with a guest book entry and no task gets its example tasks, so the seeder (`scripts/seed_golden_set.py`) is not asking the second question, and `reconcile/delta/docs.md` names that phrase as the alternative `Q-10` rejected. `requirements.md` § Impact analysis read it as the fill condition; the design read "one condition" as clone against preview and kept it. Settled automatically by the constitution, Article IV.
  **ADR:** none — the sentence now says what the paragraph above it and the user's `Q-10` already decided.
  **Requirements:** CR-2609-823a/R-11
- `MODIFIED` `spec/design/architecture.md` § The to-do list — where each rule lives › The files — one row added after the `scripts/` row
  **Was:** the one `scripts/` row gave build-backend `seed_golden_set.py` and `seed.sh`, "filling each list on its own, and saying so in `--help`": `seed.sh`'s own help. § What a new environment starts with names `start.sh`, `preview.sh` and `deploy.sh` as the callers of `seed.sh`, and no row placed what their help and comments say about seeding.
  **Now:** a row for `start.sh`, `help.sh`, `deploy.sh` and `preview.sh`, written by build-backend: "text only: each calls or lists `seed.sh`, so every `--help` line and comment of theirs that describes the seeding says what `seed.sh` does — each list filled on its own when it holds nothing, a list that already holds something never touched, one `GET` per list on every run after the first; nothing they do moves".
  **Why:** COH-spec_sync-5, its ambiguity source. `./scripts/start.sh --help` still says `--no-seed` leaves "the guest book" empty, `./scripts/help.sh` says `seed.sh` fills "an environment's guest book", and the comments in `start.sh`, `deploy.sh` and `preview.sh` count one `GET`, while this document counts one per list and `--no-seed` skips `seed.sh` altogether. `--help` is the human interface (constitution, Article XII), and code contradicting `spec/` is a defect in the code (Article I). The writer is build-backend because § Who writes what gives it `scripts/`, as does `.specconf/stack.json`, which names `scripts/` as deliberately not build-platform's.
  **ADR:** none — who writes which file in this change, and reversing it edits one table row.
  **Requirements:** CR-2609-823a/R-11
- `MODIFIED` `spec/design/conventions.md` § Documentation — where a document goes: the `docs/` row of the table, and one paragraph added after the table
  **Was:** the `docs/` row gave the tree "the system: how to set it up, run it, configure it, watch it, back it up and repair it", for "whoever operates or takes delivery of the application". It named no home for a guide addressed to the person using a screen, although `docs/user-guide.md`, the guest book's, stood there before this change.
  **Now:** the subject adds "and how each of its screens is used", and the reader adds "and the person using one of its screens". The paragraph: "A screen's user guide is therefore `docs/`'s, one per screen beside `user-guide.md`, the guest book's: it describes the running system to the person using it, and binds nothing either." The user's words close it.
  **Why:** COH-spec_sync-7. reconcile-ops, the member whose tree is `docs/`, read the row and left the to-do list's guide out as not operations documentation. reconcile-docs read the precedent, took `docs/` for the guide's home, and could not write there, so the page sat in the change record with a note saying it was in the wrong place. The user decided `Q-31` = A: "Move it to docs/ with the other guide."
  **ADR:** none — a placement rule, in the document where placement rules live (constitution, Article IX).
  **Requirements:** CR-2609-823a/R-5

*Written by the convergence round of coherence pass 11, `spec_sync` stage, for the five findings
`COH-spec_sync-8` to `COH-spec_sync-12`. Three were settled by the user: `COH-spec_sync-8` at
`Q-32`, `COH-spec_sync-9` and `COH-spec_sync-10` at `Q-30`, `COH-spec_sync-11` at `Q-33`.
`COH-spec_sync-12` was settled automatically from `spec/design/architecture.md` § Who writes what,
and where the sets meet. Three of the five have no entry here. `COH-spec_sync-9` and
`COH-spec_sync-10` are about `docs/`, which binds nothing, and no document in `spec/` or
`contracts/` states what a restore brings back. `COH-spec_sync-12` is about `reconcile/delta/ops.md`
F-1, another member's fragment. Their ambiguity sources, the runbook and pass 10's resolutions in
`review/coherence.md`, are outside this round's write set. Their repairs are reconcile-ops' and are
not declared here as made: `docs/user-guide-todo-list.md` § Deleting a task, `docs/user-guide.md`
§ Deleting an entry, and `reconcile/delta/ops.md` (§ Confirmed correct and left alone, § The
convergence round, F-1). `CLAUDE.md` § What is an example took `COH-spec_sync-11`'s ready patch,
with a pointer to `spec/invariants.md` in place of its "Superseded by" clause. It lies outside
`spec/` and `contracts/` and needs no entry. No script is edited in this change (`Q-32`).*

- `MODIFIED` `spec/design/architecture.md` § The to-do list — where each rule lives › The files — the row for `start.sh`, `help.sh`, `deploy.sh` and `preview.sh`, its "Written by" cell
  **Was:** "build-backend", which pass 10's round wrote for `COH-spec_sync-5`: the four scripts' seeding text corrected in this change.
  **Now:** "not this change: a text-only pull request with a changelog entry corrects them right after it merges, because build-backend does not run in the stage that found the text stale. The user decided it in `CR-2609-823a` (`Q-32`) in these words: "Follow-up fix right after merge."" The "Holds" cell is unchanged. It still says what the four scripts' help and comments must say.
  **Why:** COH-spec_sync-8. The row named a writer, and nobody was dispatched to write it. `git diff main --stat -- scripts/` touches only `seed.sh` and `seed_golden_set.py`, and `./scripts/start.sh --help` still says `--no-seed` leaves "the guest book" empty. Only build-backend may write `scripts/`, and it does not run in `spec_sync`. The user chose at `Q-32` not to send the change back: "This change goes on to delivery now; the stale help text is recorded as a known item and fixed in a small separate pull request with a changelog entry." The row now says who corrects the text and when, as § Who writes what already does for `golden-set/README.md` (`Q-26`).
  **ADR:** none. It says who writes four files and when; reversing it edits one cell.
  **Requirements:** CR-2609-823a/R-11
- `MODIFIED` `spec/invariants.md` § Data invariants: one paragraph added after the three one-sentence summaries of `D-01`…`D-03`
  **Was:** the section moved `D-01`…`D-03` into `contracts/invariants/guestbook.md` and stated them of every entity and every primary key. It did not say that the file bearing the guestbook's name holds every table's rules, or what happens to them when the guestbook is deleted.
  **Now:** "They are every table's, although the file that holds them is named for the guestbook, the example a reader may delete." `D-01`…`D-03` hold for `todo_tasks` as for every table, and `D-05` is written as `D-04` for a task. So `D-01`…`D-04` move first into `contracts/invariants/todo_list.md`, keeping their identifiers, and `guestbook.md` goes after them. It closes with the user's words at `Q-33`: "Move the four data rules too."
  **Why:** COH-spec_sync-11, its ambiguity source. The file's name says the rules are the guestbook's, and its content says they are every table's. The deletion lists in `CLAUDE.md` and `spec/README.md` followed the name: "One thing moves before the guestbook goes: the words of the text rule". `contracts/invariants/todo_list.md` followed the content: "`D-01`…`D-04` stand in `guestbook.md`". Deleting the guestbook as the lists said would turn three checks red. `tests/fitness/test_invariant_witnesses.py` asserts `{"D-01", "D-02", "D-03"} <= found`, `frozen-ids` fails on every citation of `D-04`, and `links` fails on `todo_list.md`:10. The user decided at `Q-33` that the lists name the move.
  **ADR:** none. It says where four existing invariants go when their file's context is deleted. No invariant's body changes, and neither does the rule for their identifiers.
  **Requirements:** CR-2609-823a/R-1, CR-2609-823a/R-2
- `MODIFIED` `spec/README.md` § This directory describes a template — one sentence added after the deletion list
  **Was:** the list deleted `contracts/invariants/guestbook.md` with the example and named nothing that moves out first.
  **Now:** "Two things move out first, because the to-do list stays and is held to both: the words of the text rule, `BR-01`, into `contexts/todo_list.md` (its § Neighbours), and the data invariants `D-01`…`D-04`, into `contracts/invariants/todo_list.md`, keeping their identifiers (`invariants.md` § Data invariants)."
  **Why:** COH-spec_sync-11. The finding names this list beside `CLAUDE.md`'s, and `Q-33` names this file: "CLAUDE.md, spec/README.md and ADR-0001 say D-01 to D-04 move into the to-do list's rules file first, keeping their identifiers, before the guestbook's file is deleted". The sentence names `BR-01` too. Without it this list would name one move where `CLAUDE.md` names two, which is how the finding arose.
  **ADR:** none. It is a deletion list, brought level with `CLAUDE.md`'s.
  **Requirements:** CR-2609-823a/R-1
- `MODIFIED` `spec/ADR/ADR-0001-todo-list-is-its-own-bounded-context.md` § Consequences — the bullet "Deleting the guestbook is no longer the deletion of one unit", one sentence added after the `BR-01` sentence
  **Was:** the bullet named the words of `BR-01` as the one thing that moves before the guestbook is deleted.
  **Now:** "The same holds for `D-01`…`D-04`, which `contracts/invariants/todo_list.md` builds on: they move into it first, keeping their identifiers, before `contracts/invariants/guestbook.md` is deleted (`spec/invariants.md` § Data invariants)."
  **Why:** COH-spec_sync-11. `Q-33` names ADR-0001 as one of the three texts that say it. The ADR is still `Proposed`, so it can be edited now and not after acceptance (`spec/design/conventions.md` § When a decision is an ADR). The same bullet already explains why `contracts/openapi/todo_list.yaml` does not `$ref` into `guestbook.yaml`. The invariants contract written in this stage points into `guestbook.md`, which is the same trap.
  **ADR:** this entry edits the ADR itself, before acceptance. The decision is unchanged.
  **Requirements:** CR-2609-823a/R-1

## This change owns

No path. Pass 10's round listed `scripts/start.sh`, `scripts/help.sh`, `scripts/deploy.sh` and
`scripts/preview.sh` here, text only and build-backend's, for `COH-spec_sync-5`. The user then
decided at `Q-32`: "Follow-up fix right after merge". So this change edits none of the four, and
the pull request after it that corrects them carries its own changelog entry.

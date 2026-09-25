# Delta fragment — `design-domain`

*A new bounded context, the to-do list, opened only after placing the requirements in the one
context that exists was tried and failed. The evidence for both is below the entries.*

- ADDED `spec/contexts/todo_list.md`
  **Why:** The requirements bring a stored thing no context describes — a task with a state that
  is switched both ways — and every rule about it (`R-1`…`R-4`, `R-6`…`R-9`) needs one owner.
  The guestbook cannot be that owner: its flow `P-01` states that an entry "either exists or it
  does not", its words (entry, author, edited) describe nothing a task has, no rule in the
  requirements relates a task to an entry, and it is the template's example, declared deletable
  as a unit — a list the user chose to keep beside it would be deleted with it. So the task gets
  a context of its own, which shares exactly one rule with the guestbook, the text rule of
  `BR-01`, as a declared shared kernel, and owns `P-02` and `BR-06`…`BR-13` exclusively.
  **ADR:** required — design-adr drafts it. Decision: the to-do list is a bounded context of its
  own (`todo_list`, classified `supporting`), a peer of the guestbook joined by a shared kernel
  that is the text rule alone. Rejected: (1) placing tasks inside the guestbook context — it
  would make `P-01`'s "no states" false for its own context, put a second vocabulary under one
  owner, and tie a feature the user kept to an example the template tells its reader to delete;
  (2) placing them in Platform — Platform holds no domain rules by definition
  (`spec/design/architecture.md` § Platform); (3) `guestbook:upstream:conformist` — true of the
  prose's location and false of the rule, which is a fact about every text field this API accepts
  and lives in neither context's code; (4) `separate-ways` — false, because both contexts are
  held to one rule and a change to it changes both; (5) classifying it `core` — nothing about it
  is what the application competes on, and the non-goals strip out everything that would make a
  to-do list distinctive; (6) `generic` — a bought to-do product brings the accounts
  `spec/invariants.md` refuses and a second place to go. Cross-cutting and expensive to reverse:
  undoing the context moves a table, a contract, a screen and a test tree.
  **Requirements:** CR-2609-823a/R-1, CR-2609-823a/R-2, CR-2609-823a/R-3, CR-2609-823a/R-4,
  CR-2609-823a/R-6, CR-2609-823a/R-7, CR-2609-823a/R-8, CR-2609-823a/R-9

- MODIFIED `spec/glossary.md` — the opening paragraph, the rows **Guestbook**, **To-do list**
  and **Task**, and the process row **Task (process)**
  **Was:** "today there is one context, so the split is an exercise for the future"; Guestbook
  "The only bounded context of this system"; no row for the to-do list, the task or the process
  word *task*.
  **Now:** the split is real and says when a word earns a row here; Guestbook is "a bounded
  context" that shares the text rule with the to-do list and nothing else; To-do list (source
  form `todo_list`) and Task (source form `TodoTask`, table `todo_tasks`) point to the context's
  § Language; Task (process) names the collision with `tasks.md` and the scripts.
  **Why:** A second context makes two of the glossary's sentences false the moment it exists,
  and the new words need a home before anybody writes them anywhere else, or the next author
  invents a second name and both survive. *Task* is also a process word in this repository
  (`tasks.md`, `T-n`, "every task is a script"), which is the `Session` trap the glossary already
  names; qualifying the identifier as `todo_task` is what keeps a search for one from finding
  the other.
  **ADR:** none — the entry records the words the new context brings and corrects two sentences
  its arrival makes untrue; the decision it follows from is the ADR marked on the entry above.
  **Requirements:** CR-2609-823a/R-1, CR-2609-823a/R-4

## The concept is absent — the search

Run from the repository root on 2026-09-24, before any edit:

| Search | Where | Found |
|---|---|---|
| `grep -niE "to-do\|todo\|\btasks?\b\|\bdone\b\|tick" spec/glossary.md` | the glossary | nothing |
| the same, `-r` | `spec/contexts/` (one document, `guestbook.md`) | nothing |
| `grep -rniEl "to-do\|todo" spec --exclude-dir=changes` | the whole specification | `spec/invariants.md` lines 124 and 162 — "any to-do task", "like a to-do task", written by this change's own convergence round (COH-requirements-5, `design/delta/converge.md`); `spec/rationale/AUDIT-2026-09-01.md` — "TODO/FIXME" markers, not the concept |
| `grep -rciE "\btasks?\b"` over `spec/` outside `spec/changes/` | the whole specification | only the process word: "every task is a script" (constitution art. XII, conventions § Scripts), the `tasks` gate (conventions § Naming) |
| `grep -rnwI todo` over `app/ frontend/src e2e golden-set alembic contracts` | the code and the corpus | nothing (0 lines), and no `TODO` marker in first-party source |
| `grep -rhoE "\bBR-[0-9]{2}\b\|\bP-[0-9]{2}\b"` over `spec/ contracts/ CLAUDE.md` | the frozen spaces | `BR-01`…`BR-05`, `P-01` declared; `BR-14` appears only as an illustration in `spec/ADR/index.md`, which the `frozen-ids` gate does not hold. So `P-02` and `BR-06`…`BR-13` are fresh |

`impact.md` § What is missing ran the wider search (`todo|to-do|todos|task|tasks|done|complete|completed|zadani|checkbox|checked`
over twelve trees) and found the same. The term is not in the glossary after all, so the
`new_context` signal stands.

## The alternative that was tried — placing the requirements in the guestbook

| Test | Guestbook | Result |
|---|---|---|
| Does its language cover a task? | Entry, Author, Message, Edited. A task has no signature, no moment of amendment, no "edited"; an entry has no state. | fails |
| Does its flow hold a state? | `P-01`: "There are no intermediate states, no lifecycle … An entry either exists or it does not." Tasks would make that sentence false for its own context (requirements Self-check 24). | fails |
| Is any rule shared? | Only the text rule of `BR-01` (NFC, the trim set, code points). `BR-03` and `BR-04` are the same *shape* of rule about a different thing, and each side can change its own without the other (the list is read one way; the guestbook both ways). | one rule, handled as a kernel |
| Does a flow cross? | No step of either flow reads or writes the other's records; `Q-10` fills each list on its own. | nothing crosses |
| Can one owner hold both? | The guestbook is the template's example, deleted as a unit (`CLAUDE.md` § What is an example; `spec/contexts/guestbook.md`, "it can be deleted when your first real feature replaces it"). The user kept it beside the list (`Q-1`), so the list must survive its deletion. | fails |
| Could Platform hold it? | Platform has no domain rules (`spec/design/architecture.md` § Platform). | fails |

## Traceability — every rule to its requirement

| Rule | Requirements |
|---|---|
| `P-02` step 1, `BR-08` | R-1 (clauses 1-5; R-1.4) |
| `BR-06` | R-2 clauses 1-3, 4, 5; R-6 clause 4 |
| `BR-07` | R-2 clause 6 (assumption `A-1` set, `A-3` reading); R-6 clause 4 |
| `BR-11`, `P-02` step 2 | R-3 clauses 1-5 |
| `BR-09` | R-4 clauses 1-5; R-4 clause 6 by reference to the screen's floor |
| `BR-10` | R-6 clauses 1-3; R-9 clauses 1-3 |
| `BR-12` | R-1 clause 5 |
| `BR-13`, `P-02` step 5 | R-7 clauses 1-4; R-8 clauses 1-2 |

**Handed over, not owned by this context:** R-5 (the way between screens, the main address, the
404 copy) to the frame, `spec/design/ui/system-states.md`; R-3 clause 6 and R-10 (how an empty,
unreadable or failed state looks) to the screen specification; R-11 (example tasks in a new
environment) to `spec/design/architecture.md` § What a new environment starts with — bound by
`BR-06`…`BR-08` like any task.

## Checked against `spec/invariants.md` and `contracts/invariants/`

Authentication: consistent — anybody adds, marks, corrects and deletes any task, and the
non-goal already names tasks. CSRF, moderation, mobile, one engine: consistent. Paging and
search, lifted for the guestbook alone: consistent — the list has neither. Retention: consistent
— a task lives until deleted, and the non-goal names tasks. `D-01`: a done task stays one record
in its place, never moved to an archive. `D-02`, `D-03`: nothing here conflicts. `D-04` names
the guestbook's two fields; whether the task's text gets an invariant of its own is design-data's
call. No rule here contradicts an invariant.

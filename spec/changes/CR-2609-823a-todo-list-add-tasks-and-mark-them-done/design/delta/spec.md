# Delta fragment — `design-spec`

*The to-do list's context document was opened by `design-domain` in the wave before this one
(`design/delta/domain.md`), with `P-02` and `BR-06`…`BR-13`. This pass read it whole against
every requirement, brought the guestbook's document level with the new boundary, and closed two
gaps in the rules. No rule identifier is minted: the highest in use is `BR-13`, and every edit
below amends a section that already has one.*

- MODIFIED `spec/contexts/guestbook.md` — the front matter's `neighbours`, the opening sentence,
  § `BR-01` (one paragraph added) and § Boundaries (its first paragraph, and the lead-in of its
  second)
  **Was:** "The only bounded context of this system and the only feature it has";
  `neighbours: []`, with § Boundaries saying the context borders on nothing and "this one shows
  what the document looks like when there is nothing to draw", and a paragraph headed "What the
  second context will have to write"; `BR-01` said nothing about any text but an entry's.
  **Now:** the opening names the guestbook as a bounded context sharing one rule with the to-do
  list; `neighbours: [todo_list:peer:shared-kernel]`; § Boundaries carries the one neighbour row,
  whose account points at the to-do list's § Neighbours instead of restating it, and the second
  paragraph is headed "How a neighbour is declared" with its body unchanged; `BR-01` gains one
  paragraph saying a task's text is held to the same normalization, trim set and unit, with each
  context keeping its own bounds, and that a change to the rule changes both contexts.
  **Why:** The to-do list declares a shared kernel with the guestbook over the text rule of `BR-01`, and from that moment three sentences of the guestbook's own document were false: it called itself the only context, declared that it borders on nothing, and described its boundary as the empty example. A shared kernel is a peer relation held by both sides, so a header saying `[]` on one side and `shared-kernel` on the other is a boundary drawn in two different ways. The paragraph in `BR-01` is the one that matters most: the to-do list's § Neighbours says the rule "changes only with both sets of rules in view", and the person who changes it reads `BR-01`, not the to-do list — without a sentence there, the rule's home would be silent about its second holder. The rule itself is not touched: its normalization, its thirty code points, its unit and its bounds of 80 and 1000 read as they did.
  **ADR:** none — the decision behind this edit (a to-do list context of its own, joined to the guestbook by a shared kernel that is the text rule alone) is the ADR `design/delta/domain.md` marks as required for `design-adr`; this entry records the guestbook's side of that boundary and changes no rule.
  **Requirements:** CR-2609-823a/R-1, CR-2609-823a/R-2

- MODIFIED `spec/contexts/todo_list.md` — § `BR-07` (one paragraph added) and § `BR-10` (one
  paragraph added)
  **Was:** `BR-06` refused a text over 200 code points as too long and `BR-07` refused a text with
  an inner line break as more than one line, "never 'empty' or 'too long'", and neither said
  which reason a text breaking both gets. `BR-10` said a correction changes the text and nothing
  else, and nothing said in words that a correction is held to `BR-06` and `BR-07`.
  **Now:** `BR-07` states that a text both too long and more than one line is refused as more
  than one line, on the screen and by the application alike, and why that order. `BR-10` states
  that a correction is held to `BR-06` and `BR-07` exactly as an addition is, that a refused
  correction leaves the task with the text it had, and that the person is told the reason an
  addition of that text would get.
  **Why:** Two gaps, each of which would have been settled twice by two authors who never talk. First, for a text over 200 code points with a line break inside it, `BR-06` and `BR-07` both applied and named different reasons — a contradiction between two rules, left to the contract and the screen to resolve separately, while `R-2` clause 5 demands that the screen and the application give one verdict for one text (`scenarios.md` § Bounds the requirements did not give, item 1, recorded it as unsettled). The order chosen is the one `BR-07`'s own words already read as ("never 'too long'") and the one `R-2.7` uses ("refused with the one-line reason, not as empty or too long"), with its reason stated: a pasted line break can be invisible in a one-line field, a length never is. Second, `R-6` clause 4 — a refused correction keeps the previous text and says why — was carried only by inference from `BR-06`'s "nothing is stored", in words written for adding; `S-33` fails exactly on "an edit is held to weaker rules than an add", so the rule is now said where corrections live.
  **ADR:** none — the first paragraph resolves an overlap between two rules of this same change in the direction `BR-07` and `R-2.7` already read, and one sentence reverses it with no migration and no rewritten contract; the second says for corrections what `BR-06` and `BR-07` already require, and adds no rule.
  **Requirements:** CR-2609-823a/R-2, CR-2609-823a/R-6

## Traceability — every requirement to where the live specification carries it

| Requirement | Carried by | This pass |
|---|---|---|
| R-1 | `P-02` step 1, `BR-08`, `BR-12` | read, no edit needed |
| R-2 | `BR-06`, `BR-07`; the shared text rule in the guestbook's `BR-01` | `BR-07` amended (two reasons meeting); `BR-01` names its second holder |
| R-3 | `P-02` step 2, `BR-11` | read, no edit needed |
| R-4 | `BR-09` (clause 6 by reference to the screen's floor) | read, no edit needed |
| R-5 | the frame every screen renders inside — owned by no context (todo_list § Neighbours, what no context owns) | no edit here; the guestbook's "only bounded context and only feature" sentence is corrected |
| R-6 | `P-02` step 4, `BR-10` | `BR-10` amended (a correction held to `BR-06` and `BR-07`) |
| R-7 | `P-02` step 5, `BR-13` | read, no edit needed |
| R-8 | `BR-13` | read, no edit needed |
| R-9 | `BR-10` | read, no edit needed |
| R-10 | how a screen shows a failure — owned by no context (todo_list § Neighbours) | no edit here |
| R-11 | a new environment's starting state — owned by no context; `BR-08` binds example tasks | no edit here |

## Checked against the invariants

Authentication and retention: consistent — the non-goals name tasks, and a correction or a
refusal needs no identity. `D-01`: a refused correction leaves one record as it was. `D-02`,
`D-03`: untouched. `D-04` names the guestbook's two fields; the sentence added to `BR-01` says a
task's text is held to the same rule and leaves to design-data whether the task's own domain
gets a data invariant for it. No edit here contradicts an invariant.

## Found outside this write set, left for the members who own it

Four documents still say there is one context, and none of them is a context document: the
specification's README (the row "What the guestbook does" and "The only domain context is the
guestbook"), architecture § the opening line and § Rules between contexts ("One domain context
has nothing to border on"), and testing's fitness table ("vacuously true with one context", on
the boundaries and declarations rows). The project's CLAUDE.md lists what deleting the guestbook
deletes; since this change it also has to say that the text rule's words move into the to-do
list first.

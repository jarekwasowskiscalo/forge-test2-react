# Delta fragment — `reconcile-spec`

*The design wrote `spec/contexts/` before any code existed (`design/delta/domain.md`,
`design/delta/spec.md`). This pass set every claim in those two fragments against the built
branch: the service, schemas, router and model of the to-do list, the screen's rule, hooks, page,
row, composer and delete question, the seeder and its corpus, and what the tests assert. The
design held, with one gap. Two rules the design left side by side (`BR-10` and `BR-13`) name
different reasons for one corner case. The build settles it, deliberately and under test, and
the context document now says so in one paragraph. No rule identifier is minted, and no
behaviour was found wrong.*

- `MODIFIED` `spec/contexts/todo_list.md` — § `BR-13` (one paragraph added after its second
  paragraph; every other paragraph byte-identical)
  **Was:** `BR-13` said that a change aimed at a task that no longer exists "tells the person the
  task no longer exists — a marking, a correction and a second deletion alike". `BR-10` said
  that a corrected text `BR-06` or `BR-07` refuses is refused "with the reason an addition of that
  text would get". Neither said which reason a person gets when both apply at once: a corrected
  text the rules refuse, aimed at a task somebody has deleted.
  **Now:** `BR-13` states that such a correction is told the text's reason, on the screen and by
  the application alike, because the screen refuses the text before anything is sent. Only a
  change that could otherwise be made learns that its task no longer exists.
  **Why:** As written, the bold sentence of `BR-13` was false for one case the build handles on purpose. The service judges a correction's text before it writes, and the lookup is the write itself, so a refused text is refused for its text whatever task it names (`judge_todo_task_text` runs before the one `UPDATE` in `change_todo_task`). The contract publishes that order as "the lookup last" (`spec/design/api.md` § The to-do list's refusals), and `test_a_request_is_refused_for_what_it_is_whatever_its_identifier_names` holds it under `CR-2609-823a/R-8`. The screen cannot behave any other way: `BR-06` forbids it to let through a text the application would refuse, so the editor refuses that text before sending anything, and a person there never learns that the task is gone. `R-6` clause 4 and `R-8` clause 1 both apply to this case and name different reasons. The design-spec pass settled the matching overlap of `BR-06` and `BR-07` inside `BR-07`, for the same reason: one text, one verdict, on both sides. This one was left for the contract and the screen to settle separately. They agree, and the context document now says what they agree on. This is the design being vague, not the build drifting. The edit adds no rule the code does not hold.
  **ADR:** none. The order was decided in design and is published in `spec/design/api.md`. It is reversible by one line of the service, with no migration and no rewritten contract shape, and this entry adds no decision of its own.
  **Requirements:** CR-2609-823a/R-6, CR-2609-823a/R-8

## Every claim of the design baseline against the built branch

| Claim (where the design put it) | What the branch does | Verdict |
|---|---|---|
| `P-02` step 1, `BR-08`: a new task is stored not done with its moment of adding, whatever the request claims, and appears first without a reload | the create shape has no `done` and a sent one is ignored; the service writes `done` false and the moment from its own clock; the screen reads the whole list again after every add that went through | holds |
| `BR-06`: normalized and trimmed by the shared rule, then empty, then over 200 code points; 205 spaces are empty; inner whitespace kept | `normalize` then the three verdicts in the service and in the browser's rule; corpus `todo-task-text.json` read by both suites | holds |
| `BR-06`: the screen accepts exactly what the application accepts and never stops at a length | no length limit on either field; the same verdict function gates add and correction; the two bounds and the two sets of line breaks are held equal by `test_length_constants.py` | holds |
| `BR-07` (design-domain): one written set of seven line breaks, read after the trim | `LINE_BREAKS` in the model and its browser copy, both applied to the trimmed text | holds |
| `BR-07` (design-spec paragraph): too long and more than one line is refused as more than one line, on the screen and by the application alike | the line-break check comes before the length check on both sides; `test_a_text_too_long_and_on_two_lines_is_refused_as_multiline` | holds |
| `BR-08`: an example task shown done is added not done and then marked | the seeder adds all five examples, then marks the done one | holds |
| `BR-09`: marking records the state chosen, leaves the text alone, and a done task stays readable | a marking sends `done` alone and the service writes it as sent; done is shown by the box, a strike-through and the checked state, never by fading | holds |
| `BR-10` (design-domain): a correction changes the text alone; later wins per aspect; a correction never undoes a marking under concurrency | one `UPDATE` naming only the columns given, no read before it; `test_todo_tasks_concurrency.py` interleaves two writers | holds |
| `BR-10` (design-spec paragraph): a correction is held to `BR-06` and `BR-07`, a refused one keeps the old text, and the person gets the addition's reason | one judgement serves both writes; the editor uses the add field's verdict and sentences; `test_a_refused_correction_keeps_the_text_it_had` | holds |
| `BR-11`: one list, newest first, total order, never moved by marking or correcting, one direction | ordered by moment of adding then identifier, both descending, with no parameters; the screen never sorts again | holds |
| `BR-12`: the same text twice is two tasks | no uniqueness anywhere; the scenario marks one of two "Buy bread" | holds |
| `BR-13`: deletion is permanent; a change to a gone task changes and creates nothing and says so; a second deletion is refused | single-statement update and delete with no upsert; not found when no row matched | holds, with the gap recorded in the entry above |
| § Neighbours: one shared rule, nothing else crosses | the browser's text rule moved out of the guestbook's folder into the frame's shared `lib/text.ts`; the guestbook's own diff is import lines only; no record, read or screen crosses | holds |
| § Open questions: no ceiling on the number of tasks | none in the service, the schema or the screen | holds |
| guestbook.md `BR-01` paragraph (design-spec): a task's text follows the same normalization, trim set and unit, with bounds of its own | both contexts call the one `normalize` and `length`; the guestbook's bounds of 80 and 1000 are untouched | holds |
| guestbook.md opening, § Boundaries, `neighbours`: the guestbook is one of two contexts joined by a shared kernel | the guestbook's behaviour is unchanged (its diff is imports and one comment line), and the declaration is read by `test_context_declarations.py` | holds |

## Every requirement accounted for in the built behaviour

| Requirement | Where the build carries it | In a context document |
|---|---|---|
| R-1 | service `add_todo_task`, create shape without `done`, page refetch after add | `P-02` step 1, `BR-08`, `BR-12` |
| R-2 | `judge_todo_task_text` and `todoTaskTextVerdict`, the shared text rule | `BR-06`, `BR-07` |
| R-3 | `list_todo_tasks` order, `staleTime: 0`, the page's empty sentence | `P-02` step 2, `BR-11` |
| R-4 | `mark_todo_task`, the row's box and done styling | `BR-09` |
| R-5 | the router and the frame's navigation | none, the frame's by design (§ Neighbours) |
| R-6 | `correct_todo_task`, the row's editor | `BR-10`, and now the corner in `BR-13` |
| R-7 | `delete_todo_task`, the delete question | `P-02` step 5, `BR-13` |
| R-8 | not found on no row matched; the refusal order | `BR-13` |
| R-9 | single-statement column-scoped writes | `BR-10` |
| R-10 | cache written only from answers; `todoTaskFailure` | none, the screen's by design (§ Neighbours) |
| R-11 | the seeder and `todo-tasks-example.json` | none, the environment's by design; `BR-08` binds the examples |

No requirement is unaccounted for. No built behaviour was classified as a defect.

## Divergences left to other members

- **Technical, for `reconcile-design`, and already carried there:** a request that changes both
  the text and the state at once, the refusal of a request that sets neither, and the standard
  validation answer for a body of the wrong shape. The screen never sends any of them, they
  are about the shape of a request rather than a person's action, and `spec/design/api.md`
  already describes each. No context document mentions them, and none should.

# Delta fragment — `reconcile-docs`

*The documentation half of the reconcile fan-out, in two documents for two readers. This
fragment is the intent note, written for whoever changes the to-do list in six months: why each
part has the shape it has, what lost, and what would have to change for the loser to win. The
user documentation is a separate page for the person using the screen:
`docs/user-guide-todo-list.md`.*

*This member edited nothing under `spec/` outside this change record, so the fragment carries no
entry for `delta.md`. The two files it edited outside the record, `README.md` and `CLAUDE.md`,
lie outside `spec/` and `contracts/` and need no entry. That is the rule
`design/delta/converge.md` applied to `CLAUDE.md` in the implement stage. Everything below is
carried by `close_stage` into `delta-history.md`.*

## The documentation written for the other reader

| File | What changed | Why |
|---|---|---|
| `README.md` | the opening paragraph: "The one feature is an example: a guest book" becomes two features, one of them an example; § Start here: the application opens with the guest book's entries and five example tasks, one of them done | both sentences became false with this change, and the first is the first thing a person taking the template reads |
| `CLAUDE.md` | the opening line names the to-do list beside the example; § What is an example gains a paragraph: the words of `BR-01` move into `spec/contexts/todo_list.md` before the guestbook is deleted, and the rule's code and the seeder's task half stay; "Everything else … stays" names the to-do list; the `--no-seed` comment names both lists | ADR-0001 § Consequences and `design/delta/spec.md` § Found outside this write set both reported that the deletion list was silent about `BR-01`. Nothing enforces it, and no design or implement author could write it. This stage's write set is the first to hold `CLAUDE.md`. The `--no-seed` comment described one list, and the seeder now fills two |
| `reconcile/user-guide-todo-list.md` | added, then removed in the convergence round: the to-do list for the person using it. It covers adding, ticking, correcting and deleting, other people on the same list, the example tasks, every refusal and failure sentence with what to do about it, what changed on the guest book, and what the list cannot do. The page now stands at `docs/user-guide-todo-list.md` | `docs/` is outside this member's write set, so the page was first written here with a note naming its destination. COH-spec_sync-7 settled the home (`Q-31`: "Move it to docs/ with the other guide."), and `spec/design/conventions.md` § Documentation now gives `docs/` a screen's user guide. The move and the row in `docs/README.md` are `reconcile-ops`'s; this member removed the copy here |

**The clean room found nothing to correct.** `evidence/cleanroom.md` is GREEN on all four steps
(setup, migrate, generate, check), so no first-run instruction was proved wrong. Its one warning
(an uncommitted file at the time of the run) is about what the run proved, not about any
instruction.

**The acceptance script needed no translation.** Every step of `uat.md` names what a person does
and sees in words the screen uses.

## Why this shape

Each entry gives what was chosen, what lost and why, what would have to change for the loser to
win, and the source. A source is always a durable document. Where a reason is an implementer's, it
is the one that implementer wrote into its module docstring or into the `ASSUMPTIONS` it
returned, which were banked at `loop back`. The `INTENT` paragraphs themselves did not reach this
step (§ What we do not know).

### 1. The to-do list is a bounded context of its own

- **Chosen:** `todo_list` sits beside the guestbook in every tree. The two share one rule, the
  text rule of `BR-01`, as a declared shared kernel.
- **Lost:**
  - *Tasks inside the guestbook.* Its `P-01` says an entry "either exists or it does not". Worse,
    the list would be deleted with the example the template tells its reader to delete.
  - *Tasks in Platform.* Platform holds no domain rules.
  - *The guestbook upstream and the to-do list conformist.* That describes where the rule's words
    sit, not whose rule it is.
  - *Separate ways, each context with its own copy of the rule.* Two copies is the shape of the
    `D-04` defect.
  - *A bought to-do product.* It brings the accounts the non-goals refuse.
- **Would flip it:** a rule that relates a task to an entry, or the guestbook no longer being
  deletable. Reversing costs a data migration and a rewritten contract (ADR-0001 § Consequences).
- **Source:** `spec/ADR/ADR-0001-todo-list-is-its-own-bounded-context.md`;
  `design/delta/domain.md` § The alternative that was tried.

### 2. A task's text is refused with a code, judged in the service, never by a schema constraint

- **Chosen:** three coded refusals, `todo_task_text_empty`, `todo_task_text_multiline` and
  `todo_task_text_too_long`, judged by the service. The request shapes carry `text` with no bound
  and import no part of the rule.
- **Lost:**
  - *The guestbook's convention, `Field(min_length, max_length)` answered with FastAPI's list.* It
    gives no code the screen can branch on. And a length constraint answers before anything else
    looks, so a long text with a line break inside would be called too long.
  - *A custom Pydantic error raised from a validator.* The code would sit inside the list that the
    frontend reduces to its message. It would also sit outside the router module, which is where
    the contract gate looks for each code.
  - *A handler in `app/core/errors.py`.* That puts domain knowledge into the framework module.
- **Would flip it:** a screen that no longer tells three reasons apart, together with `BR-07`'s
  precedence being dropped. Then the guestbook's convention would be enough. Until then one API
  has two regimes on purpose, and neither is to be "harmonised" toward the other (ADR-0002
  § Consequences).
- **How it broke first:** design-architecture followed the guestbook as the worked example and
  put the rule in the schema. design-api put it in the service, with codes. The user settled it
  (`Q-17`: "The service checks it, with a coded reason"). `spec/design/conventions.md` § Layers
  now says that a rule whose refusal carries a code is judged in `services/` (COH-design-1,
  COH-design-2).
- **Source:** `spec/ADR/ADR-0002-task-text-refusals-are-coded-not-schema-constraints.md`;
  `design/delta/converge.md`, pass 4; the module docstring of
  `app/contexts/todo_list/schemas/todo_tasks.py`.

### 3. One judgement for adding and correcting, in the order empty, one line, length

- **Chosen:** the shared kernel normalizes and trims the text first. Then an empty text is
  refused, then a line break left inside, then a text over 200 code points. A correction goes
  through the same function as an addition, and the browser applies the same order.
- **Lost:**
  - *Measuring before the line-break check*, which is what a schema length constraint would do.
    A pasted line break is often invisible in a one-line field, while a length is always visible.
    So the reason a person cannot find for themselves is the one they are given (`BR-07`).
  - *A separate check for corrections.* It could drift from the check for additions (`BR-10`).
- **Would flip it:** a field that shows line breaks. Then a person could see both reasons, and the
  order would stop hiding anything.
- **Source:** build-backend, the module docstring of
  `app/contexts/todo_list/services/todo_tasks.py`; `design/delta/spec.md`, the `BR-07` entry.

### 4. Two writers on one task are held by the shape of each statement

- **Chosen:** every write is one statement. It names only the columns the person changed, reads
  nothing first, never upserts, and runs at `READ COMMITTED`. `RETURNING` hands back the row as the
  statement left it. A tick writes the state chosen, never a flip.
- **Lost:**
  - *A version column.* It refuses the second writer, which is the opposite of `BR-10`, and
    telling a person their change lost is a named non-goal.
  - *A locking read.* It is correct, but it holds only while every path remembers to take the lock.
  - *The ORM's load, modify and flush.* A deletion that lands between the load and the flush
    surfaces as a stale-data error instead of "no longer exists".
  - *`REPEATABLE READ`.* The waiting statement fails with a serialization error instead of
    re-reading the row.
- **Would flip it:** lifting the non-goal "Telling a person that somebody else's change replaced
  theirs" (`spec/contexts/todo_list.md` § Deliberate non-goals). Then the version column wins, at
  the cost of a column, a refusal in the contract and a screen state.
- **The warning left in the code:** the service's docstring names each of the losing shapes, so
  that nobody "simplifies" the service into one of them. No sequential test tells them apart. Only
  `tests/integration/test_todo_tasks_concurrency.py` can, because it interleaves two writers on one
  row lock.
- **Source:** `spec/design/data-model.md` § `todo_tasks` › Two writers on one task;
  `design/delta/data-model.md`, decision (3); the service's module docstring.

### 5. `total` is the length of the one read, not a second count

- **Chosen:** `total = len(items)`.
- **Lost:** a `COUNT(*)` in a second statement, as the guestbook has. At `READ COMMITTED` the
  second statement sees its own snapshot. It can disagree with the rows beside it when somebody
  adds a task between the two. The guestbook needs its count because its read is one page.
- **Would flip it:** pages on the to-do list, which are a non-goal today. A page cannot imply how
  many tasks there are, so the count would have to come from the database.
- **Source:** build-backend, the docstring of `list_todo_tasks` in
  `app/contexts/todo_list/services/todo_tasks.py`.

### 6. `text` is `String(200)`, the rest of the rule is no `CHECK`, and the revision writes the literal

- **Chosen:**
  - a `varchar(200)` column: the last layer's refusal of a value that skipped the rule, and
    Postgres counts code points, which is the rule's unit;
  - no `CHECK` for an empty text or a line break;
  - `200` written as a literal in the revision;
  - no server default on any column.
- **Lost:**
  - *`Text`.* It leaves no last line of defence.
  - *`CHECK` constraints.* They would be a second hand-written copy of the thirty-code-point trim
    set and the seven line breaks, in SQL.
  - *The constant in the revision.* A released revision would change whenever the constant moved.
  - *A server default.* It would be drift, which the next autogeneration drafts away.
- **Would flip it:** moving the bound takes a new revision that widens the column, plus the
  constant, its browser copy and the boundary fixtures. `tests/integration/test_migrations.py` goes
  red on the day the constant moves without one. The 200 itself is the requester's number (`Q-9`,
  "up to 200 characters").
- **Source:** `spec/design/data-model.md` § `todo_tasks`; the module docstrings of
  `app/contexts/todo_list/models/todo_task.py` and
  `alembic/versions/5c58af1f8e8a_create_todo_tasks_table.py`; build-migration's `ASSUMPTIONS`.

### 7. The seven line breaks are one written set beside the model

- **Chosen:** `LINE_BREAKS`, seven code points written as numbers beside `TodoTask`. Its one
  browser copy is held equal to it by `tests/fitness/test_length_constants.py`.
- **Lost:**
  - *Each language's own idea of a line break.* Python's `str.splitlines` also breaks on the four
    C0 separators. JavaScript's line terminators leave out U+000B, U+000C and U+0085. A pasted
    text would then be refused on one side and stored on the other.
  - *U+000A and U+000D alone*, the other reading of `A-1`.
  - *Platform.* The guestbook keeps these characters as content, so the set is a fact about one
    context.
- **Would flip it:** the guestbook refusing line breaks too. Then the set is a fact about every
  text, and it moves to `app/platform/schemas/text.py`.
- **Source:** the model's module docstring; `design/delta/architecture.md`, decision 3;
  `requirements.md` § Named assumptions, `A-1`.

### 8. The browser's text rule moved out of the guestbook, and its test stayed behind

- **Chosen:** the rule moved unchanged from `frontend/src/contexts/guestbook/lib/entryText.ts` to
  `frontend/src/lib/text.ts`. The guestbook's corpus reader, `entryText.test.ts`, stays in the
  guestbook's folder with one import changed.
- **Lost:**
  - *A copy in the to-do context.* A rule with two homes is the shape of the `D-04` defect.
  - *Importing the guestbook's folder.* `test_no_screen_reaches_into_another_contexts_folder`
    refuses it.
  - *Moving the test up too.* It needs the guestbook's bounds, and nothing in the shared `lib/`
    imports a context.
- **Would flip it:** nothing in sight. This is where `spec/design/conventions.md` § Frontend puts
  a rule a second context needs ("Only the rule moves up"). One consequence: when the guestbook is
  deleted, its reader goes with it. What is left exercising the shared rule in the browser is the
  to-do list's `todoTask.test.ts`, which reaches `text.ts` through the to-do verdict.
- **Source:** `design/delta/architecture.md`, decision 4; COH-design-3; `design/delta/testing.md`
  § Where this departs from `design/delta/architecture.md`.

### 9. The screen shows a change only once the service has stored it

- **Chosen:** the query hook writes its cache only from the service's answer. It reads the whole
  list again after every change that went through, and it waits for that read inside the change.
  So the notice "Task added." and the new row arrive together.
- **Lost:** an optimistic update, rolled back on failure. It shows a change as made before it is
  stored, which `R-10` clause 2 forbids even for a moment. In the hook's words: "An optimistic tick
  rolled back on failure is still a tick the person saw made."
- **Would flip it:** relaxing `R-10` clause 2. The screen would feel faster on a slow connection,
  at the price of briefly lying on the one list whose point is to say what is done.
- **Source:** `design/delta/architecture.md`, decision 6; the module comment of
  `frontend/src/contexts/todo_list/hooks/useTodoTasks.ts`. The rejected alternative has no
  paragraph in `spec/design/`; `spec/design/architecture.md` states only the rule (§ Candidates for
  `spec/rationale/`).

### 10. The list is read afresh every time it is opened, and an earlier copy may show for a moment

- **Chosen:** `staleTime: 0` on the to-do query. The header link, the address and a reload all read
  the list. A copy read earlier in the same tab stays on screen until that read answers.
- **Lost:**
  - *Inheriting the 30 seconds of `frontend/src/main.tsx`.* A header link opened within 30 s
    showed the old read. The UAT would have failed a working system at step 14 (COH-implement-1).
  - *`gcTime: 0`*, which draws a loading outline instead of the earlier copy. The user decided:
    "Briefly showing it is fine." (`Q-28`).
- **The guestbook keeps its 30 s**, because this change froze the guestbook's behaviour (`SC-5`,
  and the architecture's freeze on its hook).
- **Would flip it:** people confused by the earlier copy changing into the fresh one. Then
  `gcTime: 0` is the change, plus one paragraph in `spec/design/ui/system-states.md`
  § Interactions.
- **Source:** `Q-25`, `Q-28`, `Q-29`; COH-implement-1, COH-implement-7, COH-implement-8;
  `design/delta/converge.md`, passes 7 and 8.

### 11. The add field never stops input, judges when it is left, and sends what it judged

- **Chosen:**
  - no `maxLength` and no counter;
  - the verdict and its sentence appear when the field is left or Enter is pressed;
  - Enter is handled on the key, because a form does not submit through a closed button, and
    Enter on a refused text has to say why;
  - the text is sent normalized and trimmed;
  - a failed add keeps the text in the field.
- **Lost:**
  - *`maxLength`.* It counts UTF-16 units, so a text of emoji stops at half the bound. That is the
    guestbook's `D-04` defect, one context over.
  - *Sending the text as typed.* The browser and the service would then measure different strings
    (`Q-21`, item 2; COH-design-11).
  - *Emptying the field on failure.* "Retrying otherwise means typing it again."
- **Would flip it:** a change to the unit the rule counts in. That is a change to `BR-01`, for
  both contexts.
- **Source:** build-frontend, the module comment of
  `frontend/src/contexts/todo_list/components/TodoTaskComposer.tsx`;
  `spec/design/ui/todo-list.md` § The add field; COH-design-11.

### 12. Each list is filled on its own condition, and an example task is added, then ticked

- **Chosen:** the seeder asks the guest book whether it has entries and the to-do list whether its
  `total` is zero, each whatever the other holds. Every example task is posted with its text alone,
  and the done one is then marked through the marking route.
- **Lost:**
  - *One condition for the whole environment*, "nobody has written in it yet". An environment
    that existed before the to-do list, such as stage or an open preview, would never get its
    example tasks (`Q-10`).
  - *An example born done.* The create shape has no `done`, and a task is never born done (`BR-08`,
    `Q-12`).
  - *A guarantee in the store.* "Only while empty" is a statement about the absence of every row,
    and no key or index can state that.
- **Accepted as the price:** a person who adds a task in the seconds between the read and the
  posts, or two fillings at once, leaves the examples beside that task or twice over. And outside
  production, a list emptied by hand is filled again at the next deploy, because every deploy runs
  the seeder. The user guide says so.
- **Would flip it:** environments that never outlive the arrival of a new list. Then one condition
  per environment would do. While stage and open previews outlive it, one condition cannot.
- **Source:** the module docstring of `scripts/seed_golden_set.py`; `spec/design/architecture.md`
  § What a new environment starts with, whose condition is "a list that holds nothing yet", asked
  of each list (COH-spec_sync-4); `spec/design/data-model.md` § `todo_tasks`, its last
  paragraphs.

### 13. The contract: one `PATCH`, an envelope with a count, and the moment of adding on the wire

- **Chosen:**
  - marking and correcting are one `PATCH`, and its absent fields are never written;
  - the list is `{items, total}`, although it has no pages;
  - `created_at` is published, although the screen does not show it;
  - there is no read of one task.
- **Lost:**
  - *Two sub-resources, `PUT …/done` and `PUT …/text`.* The guestbook's `PATCH` is the shape in
    force, and with it a future field is an optional addition. A toggle endpoint was never open,
    because `BR-09` forbids a flip.
  - *A bare array.* Adding the count later would break every caller.
  - *Leaving `created_at` off.* `BR-08` and `BR-11` make promises about it that nobody could check.
- **Would flip it:** a requirement to read one task. That adds an endpoint and changes none of
  these.
- **Source:** `design/delta/api.md`, the `spec/design/api.md` entry, "Also taken here".

### 14. The frame: two text links, and a name that is plainly a placeholder

- **Chosen:**
  - "Guestbook" and "To-do list" are text links after the lockup, with the current one marked,
    grouped as "Screens";
  - the lockup is the placeholder "Product name" with the initial "P", and it still leads to the
    guestbook;
  - the not-found sentence, "There is nothing at this address.", counts no screens.
- **Lost:**
  - *A pill switcher.* It reads as a filter, like the guestbook's Newest and Oldest.
  - *The lockup as the only way back.* It leads in one direction only.
  - *A top bar or a side panel.* § One column withdrew both.
  - *Keeping "Guestbook" as the lockup.* It would stand beside a navigation link of the same name,
    and it named the product after one of its screens.
- **Would flip it:** nothing named. A third screen adds a link in `PageFrame.tsx`. The not-found
  sentence was chosen so that the next screen cannot make it false.
- **Source:** `design/delta/ui.md`, choices C-1, C-2 and C-22; the module comment of
  `frontend/src/components/shell/PageFrame.tsx`.

### 15. A done task is shown three ways, and never faded

- **Chosen:** the tick, the strike-through and the checked state together. The text is in
  `--color-muted`, which measures 7.09:1 on the card.
- **Lost:** greying the text with `--color-disabled` or with opacity. That defect has happened
  once already: quiet text measured 2.92:1 on a card, below the 4.5:1 floor (`R-4` clause 6).
- **Would flip it:** a token that looks quieter and still clears 4.5:1. The rule is the floor,
  not the colour.
- **Source:** `spec/design/ui/todo-list.md` § A task's row; `requirements.md` § Defects that have
  already happened once.

### 16. Two temporary shapes, each with its exit named

- **The guestbook's footer lives in the frame, as a default.** The footer is each screen's own.
  But `GuestbookPage.tsx` was frozen for this change, so `PageFrame`'s `footer` defaults to the
  guestbook's sentence, and the not-found page passes none. **Exit:** the guestbook screen passes
  its own sentence, and the constant goes. **Source:** build-frontend's `ASSUMPTIONS`; the comment
  on the constant in `PageFrame.tsx`.
- **The done-text contrast check lives in `e2e/ui/test_smoke.py`**, not beside the style helpers in
  `e2e/ui/styles.py`, because T-12's file list left `styles.py` out. **Exit:** a change whose write
  set holds `styles.py` can move it. **Source:** build-tests-e2e's `ASSUMPTIONS`.

### 17. The to-do list's ownership rows come last in `.github/CODEOWNERS`

- **Chosen:** five per-context rows at the end of the file, naming the owner the catch-all names.
- **Lost:**
  - *Placing them earlier.* GitHub applies the last matching rule, so a row above the catch-all
    would be overridden.
  - *Rows for the guestbook.* It is the example that gets replaced.
- **Would flip it:** a real owner for the to-do list, recorded somewhere. Today none is (T-24).
- **Source:** build-platform's `ASSUMPTIONS`; `tasks.md` T-24.

## How we know

| Kind of source | Entries |
|---|---|
| An ADR, promoted in this stage | 1, 2 |
| A user decision recorded in the change | 2 (`Q-17`), 6 (`Q-9`), 10 (`Q-25`, `Q-28`, `Q-29`), 11 (`Q-21`), 12 (`Q-10`, `Q-12`) |
| A design fragment's recorded decision and its rejected alternatives | 3, 4, 7, 8, 9, 13, 14 |
| A normative document under `spec/design/` | 4, 6, 8, 11, 12, 15 |
| A resolved coherence finding | 2, 8, 10, 11, 12, and § What broke along the way |
| An implementer's module docstring (build-backend, build-migration, build-frontend) | 3, 4, 5, 6, 7, 9, 11, 12, 14 |
| An implementer's `ASSUMPTIONS`, banked at `loop back` | 6 (build-migration), 16 (build-frontend, build-tests-e2e), 17 (build-platform), and § What broke along the way |

## What we do not know

1. **The implementers' `INTENT` paragraphs.** The dispatch to this step carried none. The
   session-history tools return a sub-agent's hand-back cut to a few hundred characters, and the
   raw transcripts are not to be read directly. So the why of every implementation choice above
   rests on the module docstrings and the banked `ASSUMPTIONS`. Whatever an implementer weighed and
   rejected without writing it into either is lost. This concerns all nine members of the implement
   stage: build-backend, build-frontend, build-migration and build-platform, and the five test
   authors.
2. **Three values build-tests-integration chose that no document fixes.** They are the letter `a`
   as "an ASCII letter" in the boundary cases, every second task of the 101-task case marked done,
   and the descriptions in `todo-task-text.json`. Its report says so and gives no reason. None is
   needed for correctness, and each can change without touching a rule.
3. **Why 200.** The number is the requester's (`Q-9`). No reason beyond that choice was asked for
   or recorded. Moving it is a product decision, and entry 6 says what it costs.
4. **Not decided: the largest number of tasks.** No ceiling is set, and the whole list is read and
   drawn at once (`spec/contexts/todo_list.md` § Open questions). This is a decision for a person,
   not a gap in anybody's reasoning.
5. **Two seams nothing guards.** Both are known and named in the ADRs, and neither is guarded
   because nobody built the guard, not because somebody decided against one. No test refuses a
   foreign key from `todo_tasks` to `guestbook_entries` (ADR-0001). The five refusal sentences have
   two copies, one in the router and one in `spec/design/api.md`, and nothing compares them
   (ADR-0002).

## What broke along the way

No debug stage ran, and nothing needed `build-debug`. This is what broke, and why:

1. **A migration landed in another project's database.** build-migration's first
   `./scripts/db.sh migrate` applied this change's revision to a different project's Postgres. That
   project's container held `0.0.0.0:5432`, this repository's default database URL names
   `localhost:5432`, and the scripts check only that compose lists `db` as running. The user
   approved a revert. The other container was stopped, and this repository's database went back to
   `127.0.0.1:5432`. The template's scripts still cannot tell the two databases apart (banked as
   `PROC-46`). **Source:** build-migration's `ASSUMPTIONS`; `sessions/76720804-…/summary.md`, S5,
   W9 and W10.
2. **The black box could not run between the test waves.** So its 22 scenarios and 4 smoke cases
   were collected but never seen failing. `./scripts/test.sh e2e` builds the SPA first, and that
   build type-checks all of `frontend/src`. That includes the first wave's vitest files, which
   import modules only the second wave writes (`PROC-41`). The suite's green is evidence of
   behaviour. It is not a red-first proof. **Source:** build-tests-e2e's `ASSUMPTIONS` (status
   CONTENTION); `sessions/76720804-…/summary.md` § What was not done.
3. **A defect in a first-wave test surfaced only in the second wave.** The test wrote
   `await act(() => mutation.mutate(...))`, which awaits the `void` that TanStack's `mutate`
   returns. `@typescript-eslint/await-thenable` needs types, and while the imported modules did not
   exist, their types were `any`. build-frontend returned `TEST_DISPUTED`, and the test author fixed
   the test (TD-3). **Source:** build-frontend's `ASSUMPTIONS`; `PROC-45`.
4. **The missing routes answered 405, not 404.** While no to-do route existed, `POST`, `PATCH` and
   `DELETE` got 405 because a GET-only route matched those paths. The plan had predicted a JSON 404.
   This is worth knowing when reading the red-first failures of a new resource. **Source:**
   build-tests-integration's `ASSUMPTIONS`.
5. **The header link showed an old list.** Entry 10 covers it.
6. **Documents were left false by the new corpus files.**
   - The deletion lists in `spec/README.md` and `CLAUDE.md` would have deleted the to-do list's
     fixtures with the guestbook (COH-implement-3). Fixed.
   - Five test docstrings and three comments still counted one table, one context or one resource
     (COH-implement-4, COH-implement-9). Fixed.
   - Five sentences of `golden-set/README.md` are still false, because no member may write that
     file. They go to a follow-up pull request (`Q-26`) and template issue #92.

   **Source:** `review/coherence.md`, passes 7 and 8; `design/delta/converge.md`.

## Candidates for `spec/rationale/`

**None was written, on purpose.** `spec/rationale/README.md` sends a rejected alternative to its
ADR or to the decision paragraph of a normative document, "never here", and a rule that holds to
`spec/design/`. Every durable reason in § Why this shape already has such a home:

- ADR-0001 and ADR-0002 (entries 1 and 2);
- `spec/design/data-model.md` § `todo_tasks` (entries 4 and 6);
- `spec/design/conventions.md` § Layers and § Frontend (entries 2 and 8);
- `spec/design/ui/system-states.md` § Interactions (entry 10);
- `spec/design/api.md` § The to-do list's refusals (entries 2, 3 and 13);
- `spec/design/ui/todo-list.md` (entries 11 and 15).

The implementation-level reasons are in module docstrings, which is where the constitution
(article IX) puts intent. A note under `spec/rationale/` would be a second home for each of them.

**One reason has no normative home.** The rejection of an optimistic update (entry 9) lives in
the change record and in the hook's module comment, and `spec/design/architecture.md` states the
rule without it. If it is to bind, its home is a decision paragraph in that document, which is
`reconcile-design`'s, not this tree.

## Candidates for operator documents and runbooks

These are for `reconcile-ops`, whose tree is `docs/`, and for the orchestrator:

- **`docs/user-guide-todo-list.md`**, moved from `reconcile/user-guide-todo-list.md`, with a row in
  `docs/README.md`'s table. Decided at `Q-31` (COH-spec_sync-7), and `reconcile-ops`'s to make.
- **`docs/troubleshooting.md`: migrations or tests reaching another project's database.** Symptom,
  cause (another container holds `0.0.0.0:5432`), and fix (find it with `docker ps`, then stop it
  or move one project's port). It is needed until `PROC-46` lands.
- **`docs/operations.md`: an emptied list is filled again at the next deploy** outside production,
  for the to-do list exactly as for the guest book.
- **Script help and comments that still describe one list.** build-backend reported some of them,
  and each was confirmed here:
  - `scripts/start.sh`: `--help` ("--no-seed leave the guest book empty") and the comment on
    `seed_when_up`;
  - `scripts/deploy.sh`: the comment above the seed step, line 621;
  - `scripts/preview.sh`: the comment at line 199;
  - `scripts/help.sh`: the `seed.sh` row, line 89.

  Scripts belong to no reconcile member, so this item is the orchestrator's.

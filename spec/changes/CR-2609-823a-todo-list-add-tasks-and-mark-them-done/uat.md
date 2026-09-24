# Acceptance tests — the to-do list: add tasks and mark them done

*A script for a person, run after delivery, on the delivered branch and before it is merged
(`requirements.md` § Success criteria, `SC-1`). It holds what no automated suite can show: the
example tasks a new environment opens with (`CR-2609-823a/R-11`, `**Verified-by:** manual`), the
contrast of a done task's text (`CR-2609-823a/R-4` clause 6, which no suite that owns a citation
can measure), and the five success criteria, each of which `requirements.md` measures with this
script. Everything else the change promises is proved by the suites `spec/design/testing.md`
§ CR-2609-823a, the to-do list maps, and is not repeated here. About 25 minutes.*

*Every step is answered `yes` or `no`. Anything worth saying about a step goes under § Tester's
notes, by step number. No personal data anywhere in this file: no names, no e-mail addresses,
not even the tester's.*

## Preconditions

- **Where:** a machine with this repository checked out on the branch
  `sdd/CR-2609-823a-todo-list-add-tasks-and-mark-them-done`, where `./scripts/setup.sh` has run
  once. `./scripts/preflight.sh` says what is missing, if anything.
- **Browser:** Chrome or Edge, because step 5 uses the Lighthouse check built into both, and one
  that can open a private window (step 8).
- **Two terminals** open at the repository root, called **A** and **B** below, with no
  `DATABASE_URL` set in either: `./scripts/db.sh reset` refuses a database it did not start.
- **What has to be running.** In terminal A, in this order:
  1. `./scripts/build.sh` compiles the screens this branch changed.
  2. `./scripts/db.sh reset` **destroys the local development database** and creates it again,
     empty. That is what makes this a freshly created environment. Nothing outside this machine
     is touched.
  3. `./scripts/start.sh` starts the application on port 8080. Leave it running. A few seconds
     after the application answers, it fills each empty list from `golden-set/seed/`.
- **What data has to be loaded:** none by hand. The environment fills itself from the seed half of
  the declared corpus: the guestbook's five welcome entries (`golden-set/seed/entries-welcome.json`)
  and the to-do list's five example tasks (`golden-set/seed/todo-tasks-example.json`, the five that
  `scenarios.md` § Seed data specifies, one of them done). The only texts anybody types in this
  script are "Water the plants", "Buy bread" and "Buy rye bread". They come from the acceptance
  criteria of `requirements.md` and name nobody.
- **What the tester should see before step 1:** terminal A has printed "Starting the application"
  and stays busy. Wait ten seconds, then begin.

## Steps

### Part A — a freshly created environment, and somebody who has never seen the list

| # | Screen | What to do | What is to happen (exactly) | Requirement | Result |
|---|---|---|---|---|---|
| 1 | Browser, window A | Open `http://127.0.0.1:8080/` in a new window. This is window A. | The guestbook: the title "Leave a note", the header reads `5 entries`, and after the "Product name" lockup the header shows two links, "Guestbook" and "To-do list", with "Guestbook" underlined as the screen on show. The address bar ends in `/guestbook`. (If the header reads `0 entries`, the filling has not finished: wait five seconds, reload once, then answer.) | `CR-2609-823a/R-5` | yes / no |
| 2 | Guestbook | Ask a colleague who has never seen the to-do list to find it, starting from this screen and without typing an address. Give no other hint. If nobody is at hand, do it yourself without reading further in this table. Write "newcomer" or "self" in the notes, never a name. | The person reaches the screen titled "Things to do" without typing an address and without asking for help. The address bar ends in `/todo-list`. | `CR-2609-823a/R-5` | yes / no |
| 3 | To-do list | Before anybody adds anything, read the list and the header. | The header reads `5 tasks`, and the list holds five tasks that nobody typed. At least one of them is shown done: its box is filled and ticked and its text is struck through. The others show an empty box and plain text. | `CR-2609-823a/R-11` | yes / no |
| 4 | To-do list | Ask the same person to add the task "Water the plants". Give no other instruction. | "Water the plants" appears as the first row, above the five example tasks, with an empty box, without the page reloading. The header reads `6 tasks`. | `CR-2609-823a/R-1` | yes / no |

### Part B — what only a person can look at

| # | Screen | What to do | What is to happen (exactly) | Requirement | Result |
|---|---|---|---|---|---|
| 5 | To-do list, with the browser's developer tools | Open the developer tools (F12, or Cmd+Option+I on a Mac) and choose the "Lighthouse" tab (it hides behind "»" when the panel is narrow). Set Mode to "Snapshot", tick the category "Accessibility" and no other, and press "Analyze page state". | The report opens with an Accessibility score. The check "Background and foreground colors have a sufficient contrast ratio" is listed under "Passed audits". If it is listed among the failures instead, expand it. The answer is **no** when the struck-through text of the done example task is one of the elements it names. Any other element it names goes in the notes. (The floor is 4.5:1. The screen's specification expects the done text at 7.09:1 against its card.) | `CR-2609-823a/R-4` | yes / no |
| 6 | To-do list | Press the box of "Water the plants" once. | The box is filled and ticked and the text is struck through: the task is shown done. "Water the plants" is still the first row, and no other row has moved. | `CR-2609-823a/R-4`, `CR-2609-823a/R-3` | yes / no |
| 7 | To-do list | Press the same box once more. | The box is empty and the text is plain again: the task went back to not done in one press. It is still the first row, and no other row has moved. | `CR-2609-823a/R-4`, `CR-2609-823a/R-3` | yes / no |

### Part C — two people on one list

| # | Screen | What to do | What is to happen (exactly) | Requirement | Result |
|---|---|---|---|---|---|
| 8 | Browser, window B | Open a private window (Ctrl+Shift+N, or Cmd+Shift+N on a Mac) at `http://127.0.0.1:8080/todo-list`. This is window B. Keep window A open beside it. | Window B shows the same list as window A: the same six tasks, in the same order, with the same done marks. Both headers read `6 tasks`. | `CR-2609-823a/R-3` | yes / no |
| 9 | To-do list, window A | Add the task "Buy bread". | In window A, "Buy bread" is the first row and the header reads `7 tasks`. Window B still reads `6 tasks`, because nothing is pushed to a screen that is already open. | `CR-2609-823a/R-3` | yes / no |
| 10 | To-do list, window B | Reload the page. | Window B shows "Buy bread" first, then "Water the plants", then the five example tasks. The order and the done marks are the same as in window A, and both headers read `7 tasks`. | `CR-2609-823a/R-3` | yes / no |
| 11 | To-do list, window B | Press the box of "Buy bread". | In window B, "Buy bread" is shown done. Window A has not been reloaded and still shows it with an empty box. | `CR-2609-823a/R-4` | yes / no |
| 12 | To-do list, window A (not reloaded) | Press "Edit" on "Buy bread", replace the text with "Buy rye bread" and press "Save". | The notice "Task updated." appears. The first row reads "Buy rye bread" and is shown **done** (box ticked, text struck through): the list is read again after the change, and the tick made in window B was kept. The answer is **no** if "Buy rye bread" is shown not done. | `CR-2609-823a/R-6` | yes / no |
| 13 | To-do list, window B | Reload the page. | Window B shows "Buy rye bread" first, shown done, and below it the same list as window A. Both headers read `7 tasks`. | `CR-2609-823a/R-3`, `CR-2609-823a/R-6` | yes / no |

### Part D — filling an environment that is no longer new

**Set-up (not a step).** Close window B. In terminal A, stop the application with Ctrl+C, run
`./scripts/db.sh reset`, then run `./scripts/start.sh --no-seed` and leave it running. Wait ten
seconds. In window A the guestbook now says "No entries yet. Be the first." and the to-do list says
"No tasks yet. Add the first one above.". On the to-do list, add the task "Water the plants", which
is then its only task.

| # | Screen | What to do | What is to happen (exactly) | Requirement | Result |
|---|---|---|---|---|---|
| 14 | Guestbook, window A | In terminal B run `./scripts/seed.sh`. When the prompt returns, open the guestbook with the header link "Guestbook". | The guestbook lists its welcome entries and the header reads `5 entries`. The guestbook was filled although the to-do list holds a task (scenario S-53). | `CR-2609-823a/R-11` | yes / no |
| 15 | To-do list, window A | Open the to-do list with the header link "To-do list". | Exactly one task, "Water the plants", and the header reads `1 task`. No example task was added beside a task somebody wrote (scenario S-53). | `CR-2609-823a/R-11` | yes / no |
| 16 | To-do list, window A | In terminal B run `./scripts/seed.sh` again. When the prompt returns, reload the to-do list. | Still exactly one task, "Water the plants", and the header reads `1 task`. Filling again added nothing (scenario S-50). | `CR-2609-823a/R-11` | yes / no |

**Set-up (not a step).** On the to-do list, delete "Water the plants": press "Delete", then
"Delete task" in the question. The list says "No tasks yet. Add the first one above.", and the
guestbook still holds its welcome entries.

| # | Screen | What to do | What is to happen (exactly) | Requirement | Result |
|---|---|---|---|---|---|
| 17 | To-do list, window A | In terminal B run `./scripts/seed.sh`. When the prompt returns, reload the to-do list. | The header reads `5 tasks`, and the list holds five tasks nobody typed. At least one of them is shown done (scenario S-52). | `CR-2609-823a/R-11` | yes / no |
| 18 | Guestbook, window A | Open the guestbook with the header link "Guestbook". | The header still reads `5 entries`, and no welcome entry appears twice. Filling the to-do list gave the guestbook nothing (scenario S-52). | `CR-2609-823a/R-11` | yes / no |

### Part E — production is never given example tasks

**Set-up (not a step).** In terminal A, stop the application with Ctrl+C, run
`./scripts/db.sh reset`, then run `APP_ENV=prod ./scripts/start.sh` and leave it running.
`APP_ENV=prod` makes this copy answer as production does, and that answer is what the seeder asks
before it fills anything (`docs/configuration.md`, `APP_ENV`). Wait ten seconds.

| # | Screen | What to do | What is to happen (exactly) | Requirement | Result |
|---|---|---|---|---|---|
| 19 | To-do list, window A | Open `http://127.0.0.1:8080/todo-list`. | "No tasks yet. Add the first one above." and the header reads `0 tasks`. Starting the application did not fill the list (scenario S-51). | `CR-2609-823a/R-11` | yes / no |
| 20 | To-do list, window A | In terminal B run `./scripts/seed.sh`. When the prompt returns, reload the to-do list. | Terminal B printed that it refuses to seed `prod`, and nothing saying it seeded anything. The to-do list still says "No tasks yet. Add the first one above." and the header reads `0 tasks` (scenario S-51). | `CR-2609-823a/R-11` | yes / no |

**Clean-up.** In terminal A, stop the application with Ctrl+C and run `./scripts/db.sh reset`.
Run `./scripts/start.sh` if you want the application back the way a fresh clone has it.

## What each step answers for

| What | Steps |
|---|---|
| `CR-2609-823a/R-11`: a fresh environment opens with at least three example tasks, one of them done (scenario S-49, `SC-4`) | 3 |
| `CR-2609-823a/R-11`: a list holding a task and an empty guestbook, where only the guestbook is filled (scenario S-53) | 14, 15 |
| `CR-2609-823a/R-11`: filling again adds nothing to a list that holds a task (scenario S-50) | 16 |
| `CR-2609-823a/R-11`: a guestbook with its welcome entries and an empty list, where the list is filled and the guestbook keeps its entries (scenario S-52) | 17, 18 |
| `CR-2609-823a/R-11`: production gets no example task (scenario S-51) | 19, 20 |
| `CR-2609-823a/R-4` clause 6: a done task's text clears 4.5:1 | 5 |
| `SC-1`: somebody new reaches the list from the guestbook and adds a task, with no instruction | 2, 4 |
| `SC-2`: two people see the same tasks, in the same order, with the same done marks | 8–13 |
| `SC-3`: a task ticked by mistake goes back in one press, and neither press moves it | 6, 7 |
| `SC-5`: the main address still opens the guestbook | 1 |

**Deliberately left out.** Everything else `CR-2609-823a/R-1` to `CR-2609-823a/R-10` promise:
the text rules and their boundaries, the refusal sentences, a service that cannot be reached, a
task deleted underneath somebody, the order, and the addresses. The suites that
`spec/design/testing.md` § CR-2609-823a, the to-do list maps prove all of it on every run.
`CR-2609-823a/R-9` is out as well. Its changes are sent before either is answered, which nobody
can do by hand, and `tests/integration/test_todo_tasks_concurrency.py` produces exactly that.
Steps 11 to 13 check the promise behind it at a person's pace (a tick is never undone by somebody
else's edit) and cite `CR-2609-823a/R-6`, which is what they prove. The length half of
`CR-2609-823a/R-11` (every example under 150 code points) is held by
`tests/fitness/test_golden_set.py`, since nobody counts code points by eye. Steps 3 and 17 show
that all five examples arrived, which means every one of them passed the same text rules as a
typed task.

## Tester's notes

Run on: `<date>` · commit: `<short hash of the branch head>` · step 2 done by: `newcomer` / `self`

| Step | Note |
|---|---|
| | |

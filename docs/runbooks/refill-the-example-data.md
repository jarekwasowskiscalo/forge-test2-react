# Refill an environment's example data

**For:** whoever is about to put a preview or stage in front of somebody and finds its example
tasks or welcome entries partial or doubled.
**Normative source:** [`spec/design/architecture.md`](../../spec/design/architecture.md) § What a
new environment starts with — what the seeder fills, and on which condition;
[`spec/design/data-model.md`](../../spec/design/data-model.md) § Two writers on one task — why
"only while the list is empty" is not held by the database.

> **This procedure has not yet been performed on a deployed environment.** The seeder's two
> conditions and its refusal of production are proved by `tests/tooling/test_seed_golden_set.py`
> against a faked API, and by nothing that reached stage or a preview. Read it through before
> starting, and note here what differed when you run it.

## When to use this

A preview or stage came up with its example data wrong, and somebody is about to judge the screen
by it:

- **the to-do list holds fewer than the five example tasks, or none of them is done.** A seeder run
  stopped part way. It adds every example task first and marks the done one last, so a run that
  stopped between the two leaves all five not done;
- **the example tasks appear twice, or beside a task somebody added.** Two runs filled one
  environment at the same moment, or a person added a task in the seconds between the seeder's
  check and its posts;
- **the guest book holds only some of its welcome entries**, the same failure on the other list.

**The seeder never repairs any of these by itself.** It fills a list only while the list is empty,
and a list holding one leftover is not empty: every later deploy prints `… already holds a task;
left alone` or `… already has entries; left alone` for it and adds nothing.

**Not for a list that is merely empty.** Run step 3 alone, which is
[`../operations.md`](../operations.md) § Filling an environment with something to look at.

**Not for production.** The seeder refuses it, and the example data is test data. A production
to-do list that opens empty is correct.

**Not for a list people have written in** unless the people who wrote there agree. That includes
stage during acceptance testing. Step 2 deletes, and a deleted task or entry is gone for good: there
is no undo, no archive and no bin.

You need the environment's URL (for a preview, the one in the pull request comment) and `uv` on
your machine, which `./scripts/seed.sh` checks for before it does anything.

## Steps

1. **Find out which environment answers and what each list holds.**

   ```bash
   curl -s https://<the environment>/api/health
   curl -s "https://<the environment>/api/guestbook-entries?limit=1"
   curl -s https://<the environment>/api/todo-tasks
   ```

   The first names the environment in `environment`. **If it says `prod`, stop here.** The second
   gives the number of entries in `total_all`. The third gives the number of tasks in `total` and
   every task with it, so you can tell the examples from anything a person wrote. The example texts
   are in `golden-set/seed/todo-tasks-example.json`, the welcome entries in
   `golden-set/seed/entries-welcome.json`. On stage or a preview the first read of a list after a
   quiet spell can take ten to fifteen seconds while the database wakes. That is not a fault.

2. **Empty only the list you are refilling, on its screen, one row at a time.** This deletes those
   rows for good.

   - The to-do list: open `/todo-list`, press "Delete" on a row, then "Delete task" in the question
     "Delete this task?". Repeat until the list says "No tasks yet. Add the first one above."
   - The guest book: open `/guestbook`, press "Delete" on an entry, then "Delete entry" in the
     question "Delete this entry?". Repeat until the book holds no entry.

   Leave the other list alone. The seeder asks each list on its own, so a list that still holds
   something keeps it.

3. **Fill it.**

   ```bash
   ./scripts/seed.sh --base-url https://<the environment>/api
   ```

   It prints one line per list. The list you emptied reads
   `seeded the to-do list of <environment> with 5 example tasks` or
   `seeded the guest book of <environment> with 5 entries`, and the other reads `… left alone`.

   Where it can fail:

   | It prints | What it means |
   |---|---|
   | `refusing to seed prod: the corpus is test data` | the URL is production's. Nothing was written. Stop |
   | `error: seeding <environment> failed: …` | the run stopped part way again. The line names the task or entry and the status it was answered with, and the list now holds what went in before it. Find out why the service refused or did not answer ([`../troubleshooting.md`](../troubleshooting.md)), then go back to step 2 |
   | `… already holds a task; left alone` for the list you emptied | something was added between step 2 and this step. Look at the list again before deleting anything more |

## How you know it worked

`curl -s https://<the environment>/api/todo-tasks` answers with a `total` of 5. On `/todo-list` the
header reads `5 tasks`, and exactly one of them, "This one is already done. …", is shown done: its
box ticked, its text struck through. For the guest book, `/guestbook` shows each welcome entry once
and the header reads `5 entries`. Both numbers are the counts in `golden-set/seed/` today.

Running step 3 a second time prints `left alone` for both lists and changes nothing. That is the
proof the environment is back in the state every later deploy will leave alone.

## Afterwards

If the run that failed was a deployment's, the failing status in its log is the fault worth
chasing. A seed that does not go in is only a warning (*"the seed corpus did not go in; the
deployment itself is fine"*), and whatever refused the seeder refuses people too. Once this has
been run on a real environment, replace the note at the top with what happened.

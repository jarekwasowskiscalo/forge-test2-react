# The process's self-audit loop

*This document has a twin.* The forge plugin carries a near-identical copy of it under its
own documentation, addressed to whoever works on the process; this one is addressed to whoever
works in this project. They are near-identical and are allowed to drift where the reader differs — nothing
compares them, and an edit worth making here is usually worth making there.


The change process is judged from its own traces. That is a loop separate from the process
itself: `/sdd` runs a change, and this runs **improving how `/sdd` runs changes**.

The loop has two roles and one place where they meet.

---

## The first role: you are running a change

**You do not run it. The stage boundary does.** `close_stage.py` prints the boundary as a
numbered sequence — the stage commit, then `/sdd-retro`, then its archive commit, then the
push — and `checkpoint.py push` refuses while the archive is missing. Which boundaries run
it is `boundary.retro` in `.specconf/process.json`; `every_stage` is the shipped answer,
because a boundary tells you to open a new window and a session's end is exactly when its
archive can still be written.

It runs **on the change's branch, before the merge**, never after: the skill reads the
change from the branch through `focus.py`, and there is none on the trunk. You can still
type `/sdd-retro` yourself — for a session that ended without closing a stage, say — and it
behaves identically.

It used to be a sentence below the boundary's stop line, prefixed with the word "Optional".
Over the whole life of this repository that sentence produced zero archives, which is how
the loop below came to have nothing to read.

It does **three things and not one more**:

1. **fetches and stores the history** — the raw transcript with its sidecar, copied by the
   script, edited by nobody;
2. **audits from the context** — from the conversation it stands in, never from the transcript
   and never through an MCP server;
3. **creates a place for your feedback**.

It leaves in `spec/changes/<CR>/sessions/<session-id>/`:

| file | who writes it | role |
|---|---|---|
| `transcript.jsonl` + `sidecar/` + `manifest.json` | the script | the raw evidence |
| `summary.md` | the agent | the **witness** — what happened, with no proposals |
| `audit.md` | the agent, from the context | the **judge** — what went wrong and **what worked** |
| `feedback.md` | **you** | the third statement; empty passes |

Three statements about one run, because that is the smallest number at which what the agent
does not know about itself becomes visible: the agent's two documents agree with each other by
definition, and the numbers have no opinion. `summary.md` has to stay an uncorrected sample for
whoever will count across many sessions; `audit.md` has to say outright what went wrong. One
document cannot be both, and an attempt at that once ended with the analysis being deleted from
this skill.

**This skill produces no numbers.** The tokens, the Bash share, the rule breaches and the rest
come into being once, at the corpus harvest — for **every** session, not only for the sessions
of changes, and without a single token of context.

**A note during the work.** A sentence beginning with "note: …" or "for the retro: …" lands in
`retro/notes/<date>.md` through `notes.py add`, with the branch, the change and the session
identifier. It works in any state of the repository, on a trunk with no open change too.

**Transcripts are archived raw** — a deliberate decision, not an oversight — so nothing you do
not want in the repository forever may be pasted into a session.

---

## The second role: you are improving the process

**One round per CR**, at the end of a run. One command and one prompt.

```bash
sdd-retro round --cr CR-2608-f9b6 --dump
```

It builds `retro/rounds/<date>-<CR>/` — every dimension of that one run in one directory, in
the order `INDEX.md` writes out. The order comes in **two blocks** and that is a rule of the
audit rather than a document's tidiness:

| # | file | what question it answers |
|---|---|---|
| ① 1 | `statistics.md` | how long it took and what it cost: the bill, the time axis, the ledger |
| ① 2 | `divergences.md` | the contracts' promise against the record |
| ① 3 | `artefacts.md` | what came into being, with the line churn |
| ① 4 | `metrics.md`, `metrics.json` | the corpus numbers, to subtract from the next round |
| ② 5 | `audits.md` | three statements about every run: the witness, the judge and the human |
| ② 6 | `feedback.md` | **your statement about this run — fill it in before the prompt** |
| ② 7 | `notes.md` | this change's process notes |
| ② 8 | `previous-round.md` | the previous round's promises with the before/after |

Block ① is the numbers and the trace, block ② is somebody else's opinion — and an audit goes ①,
then ②, because the judged agent's self-assessment read before the measurement becomes a
starting point. An audit that began with `audits.md` confirms it, adds cosmetics and copies
"what worked" out of a section the judged party wrote — and then the divergence between its
opinion and the numbers stops being visible.

**Three inputs, three tracks, and mixing them costs the most.** `feedback.md` judges **this**
run, `notes.md` carries what you noticed during the work, and the third input does not lie in
the round directory: **you paste your notes and proposals into the chat beside the prompt**.
The round settles them point by point, separately — because a proposal for the future does not
have to be visible in the trace to be a good change, and a statement about the run that is
absent from the numbers is a gap in the measurement, not an absence of a problem. No point from
any of the three channels may disappear without a verdict.

**Per CR, not periodic, and that is a substantive difference.** A round across every change at
once is a trend: `audits.md` mixed the sessions of different runs, and a divergence taken
against another change's promise is noise — and noise reads as agreement. The loop's ratchet
also becomes meaningful because of it: "this CR against the previous CR". Without `--cr` a round
still spans everything, and that is a mode for looking at a trend rather than for an audit.

`round` **recomputes the indexes itself** (`reindex`) before building. Without that every reader
parses megabytes anew: measured on CR-2608-f9b6 — 0 of 8 session archives had an `index.json`,
so `metrics`, `change_cost` and the MCP server re-parsed 63 MB, each separately and on every
call.

A round also appends **one line to `retro/ledger.jsonl`** — once per change, not once per
rebuild. That is the one comparative number per run that makes "the process is faster now" a
sentence that can be checked by subtraction.

Then paste **the round prompt** ([round.md](https://github.com/Scalo-Sales-Engineering-Consulting/claude-marketplace/blob/main/plugins/forge/retro-prompts/round.md), which travels with the forge plugin) into a fresh Claude Code session in plan mode, and
beside it — in the same message — your own notes and proposals, one per line. One prompt, always
the same one, with no session identifiers to type: everything it is to read lies in the round
directory or in the `sdd-history` MCP server, and the only thing it cannot read from anywhere
is your opinion.

The round **dives into every session of the run**, two calls per session (`sdd_session` and
`sdd_flow`), and writes one row of verdict per session **before** opening that session's
`audit.md`. That is a deliberate price: a session with no row is a session nobody looked into,
and "I went through them all" is a sentence that cannot be refuted.

**A round's product is an improved process**, not a report about what ought to be improved: the
prompt analyses, weighs the pros and cons, plans, and after you accept the plan **carries it
out**. `report.md` is the trace left behind afterwards, so that the next round has something to
subtract from; the accepted promises go into `fixes.md` at the root of this directory, with a
target metric.

The most valuable finding this round can produce is the place where `audit.md` says "it went
well" and `feedback.md` says "I had to correct it by hand" — that is, where the agent was
confident and was wrong.

---
## The corpus

`retro/corpus/<YYYY-MM>/<session>/` holds **every** Claude Code session of this directory, apart
from the sessions of changes — those live in their change's record. One byte, one home.

```bash
sdd-retro plan              # how much there is and what it weighs -- writes NOTHING
sdd-retro dump --confirm    # copies and counts
sdd-retro reindex           # recomputes the numbers from what is already archived
sdd-retro verify            # the manifests and the checksums
sdd-retro prune --before 2026-06-01 --confirm
```

Three things you have to know about it:

- **`plan` counts, `dump --confirm` writes.** `plan` prints the number of sessions, the
  megabytes and the shapes of personal data, and writes nothing; `dump` without `--confirm`
  **refuses and points at `plan`**, it does not print the plan itself. Those bytes stay in the
  repository forever, so the count belongs before the write, not after.
- **`--push` is never the default.** It publishes the raw transcripts of every session of this
  directory, permanently, to everybody who reads the remote.
- **`prune` keeps `index.json` and `audit.json`.** The measurement outlives the megabytes; a
  deletion that takes the numbers too turns the corpus into a cost with no return.

**Read the history with the `sdd-history` MCP server** (`sdd_sessions`, `sdd_session`,
`sdd_flow`, `sdd_search`), never by opening a `.jsonl` — that is hundreds of megabytes, and one
transcript costs more context than a whole audit. `sdd-history` reads both sources: the corpus
from the repository (which works from a clone, regardless of which machine recorded the session)
and this machine's history.

**`sdd_cost` computes a change's bill, not the model.** Tokens in five buckets per model and
speed, the cost from the rates in `.specconf/pricing.json`, the "what if everything ran on one
model" scenarios, the time split into work, breaks and waiting, the distributions and the
cross-sections. The run over time — the sessions, the dispatch waves, the question blocks — is
`sdd_timeline`. A model adding up columns from `sdd_session` is forbidden, because it was
measured: eight calls, 60k tokens and three errors in one report.

The vendored `claude-history` server stays untouched and still serves deep Claude Code forensics
on disk. Its numbers about hooks, sidechains and subagents are unreliable on this corpus — the
reasons are listed in the process's `sdd-history/README.md`.

---

## What this loop does not do

- **It fixes nothing itself.** A round names, a human decides, the fixes are separate work. A
  fix to the process is not a change to the application's behaviour: there is no change record,
  no ADR, and it does not touch `spec/`.
- **It does not prune the archive itself.** `prune` is an explicit command with a date and
  `--confirm`.
- **It collects nothing from other people's machines.** The corpus is this machine and whatever
  somebody committed.

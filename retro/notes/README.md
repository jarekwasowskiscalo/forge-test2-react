# `retro/notes/` — dated process notes

One file per day, `<YYYY-MM-DD>.md`, appended to with a **verb**, never by hand:

```bash
sdd-engine notes add --text "what went wrong"
```

The script attaches the branch, the change and the session identifier, because a note without
those three things is a sentence the next round cannot place.

**This is an input to the retro round, not its output.** The round reads from here what a human
noticed during the work — that is, the one source that cannot be recreated from a transcript,
because a transcript shows what the agent did rather than what hurt you while it did it.

A note comes into being when something is worth noticing, not on a schedule: the directory
holding one file for a busy week is an ordinary state, and so is holding none.

**Do not edit the files here after the fact.** A note rewritten a week later stops saying what
was noticed at the time — and that is its whole value.

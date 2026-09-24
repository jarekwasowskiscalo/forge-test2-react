# Drop box — input material for this change

This directory is your drop box. Put everything you have about this change here — the
process reads every file in this directory before it starts writing the specification.
Any format: `.md` or `.txt` notes, screenshots, an Excel file with an example.

## What to drop in

1. **Requirement notes** — in your own words. The more concrete they are, the fewer
   questions you get later.
2. **New test data** — files showing the case this change is about, shaped like the ones
   in the project's own reference corpus, when it keeps one.
   The data has to be synthetic: no real names, addresses or account numbers.
3. **A Claude Design mockup** — an HTML file with the designed view. That one file does
   NOT go here: save it as `design/ui/index.html` (the directory next to `input/`).

## The minimum the process wants to know

- **What data the change processes** — new fields? changes to existing fields?
- **The process step by step** — what happens, in what order, who sees what.
- **A list of test scenarios** — in words, one sentence each: "when X, then Y".
- **Functional and non-functional requirements** — what has to work and how fast/safely.
- **What this change does NOT do** — the exclusions outside the scope. This is the most
  important point: silent scope is how an author and a reviewer agree on two different
  things.

## When you are done

Write **go on** or **build the specification** in the chat. If the drop box stays empty,
the process will ask you these questions one by one in conversation (the brainstorm stage)
— that works too, just more slowly.

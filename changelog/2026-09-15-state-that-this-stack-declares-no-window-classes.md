---
date: 2026-09-15
branch: design/declare-window-classes
pr:
kind: process
---

# State that this stack declares no window classes, rather than leaving it unsaid

## What changed

**The stack profile.** `.specconf/stack.json` gains a `window_classes` section holding nothing
but a `$comment`: this stack's screens ship one layout, and that is a written-down absence rather
than an omission.

One file, plus this entry. The screen form's half — the `## Layout by window class` section in
`.specconf/templates/system/ui-screen.md` — arrived separately, mirrored from the plugin's seed in
the change of 2026-09-15 that also said twenty-three gates. The seed itself says that section is
omitted entirely by a stack that declares no classes, which is this one. No specification
document changed here, no screen document, no code.

## Why

The forge plugin at `0.1.35` lets a stack declare the shapes of window it lays a screen out for,
so that `design-ui` can be told about them. This stack has one layout — and the whole point of
the profile is that an empty section says "not applicable" where a missing one says nothing.
`trees.schema: []` is the same sentence about schemas; `plugins` here has been an object with
nothing but a comment in it since the template was written.

Declaring it also keeps this template ready for the day the key stops being optional in the
engine: it is optional now only so that both pinned templates survive the release that
introduced it.

## From what, to what

Before: the key did not exist and nothing anywhere said whether this stack had one layout or
several. After: it says one, with the reason beside it, and `sdd-engine stack` prints
`WINDOW CLASSES  none declared`.

## How it works now

Exactly as before. `design-ui`'s preflight carries no `WINDOW CLASSES` section, the skill's
window-class rules are silent by their own wording, and a screen document here omits the
`## Layout by window class` section. `spec/design/ui/guestbook.md` and
`spec/design/ui/system-states.md` are untouched and remain correct.

## What it means for the process

Nothing. A worker sees what it saw before, and every gate answers what it answered before. This
entry exists because the absence is now expressible, and an expressible absence left unwritten is
the failure mode the profile was designed against.

## What it does not change

No screen document gains a section, no requirement is added to any of them, and no gate moves. A
fork of this template that grows a second layout declares both classes in this section with the
change that needs them — not before.

## How it was verified

`sdd-engine stack --check` prints `OK` and `sdd-engine stack` prints
`WINDOW CLASSES  none declared`; `skill_brief._window_class_lines('design-ui')` returns an empty
list, so no worker sees a heading. The engine's suite against this template
(`SDD_PROJECT_DIR=templates/python-react plugins/forge/bin/sdd-tests`) is green with
`test_sdd_document_templates.py` passing — this repository's copy of every form and the plugin's
seed are byte identical. `plugins/forge/bin/sdd-specs` against this template is `Specs: OK`.

The application's own gates were not run and did not need to be: no file under `app/`,
`frontend/`, `tests/`, `e2e/` or `scripts/` moved.

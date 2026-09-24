# Screens

One document per screen, saying what that screen is: regions, components with the full set of
their states, the copy, the data bindings to the API contract, the interactions and the tokens
used. Template: `.specconf/templates/system/ui-screen.md`.

## HTML is the evidence, Markdown is the truth

A change touching a screen delivers a Claude Design mock-up as
`spec/changes/<CR>/design/ui/index.html` and derives the screen document from it.

The mock-up is kept, in the change's directory, as a record of what was agreed. It is not the
specification and cannot be, for three reasons, all of them mechanical rather than stylistic:

- **It cannot be diffed.** Changing one word of copy and completely relaying the layout produce
  the same unreadable diff, so no reviewer can tell them apart.
- **It cannot be merged.** Two changes touching the same screen produce a conflict nobody will
  resolve by reading it.
- **A requirement cannot be cited in it.** A screenshot has nowhere to put
  `@req:CR-2608-a7f3/R-6`, and traceability that stops at the browser stops.

So the Markdown carries the requirement references, the states, the copy and the bindings; the
HTML carries the pixels. An implementer builds from the Markdown and may open the HTML for
orientation.

## Why states are enumerated

Every component lists **only the states that exist on the built screen** (`default`, `empty`,
`error`, `loading`, `disabled`, … — the names keep their source form, because they are
identifiers matching CSS and component states). A row whose content would be "not implemented"
says nothing a reader can use. It also lists the ones the mock-up does not draw, where they
exist in the code: a mock-up draws the happy path, and the `empty` state is the one a
back-office screen actually lives in on its first day. States considered and genuinely absent
are declared in a "States omitted" line under the table — the template says how.

A state not listed is not an oversight for an implementer to fill in quietly; it is a question
for that change's requirements stage.

## Why the copy is here

Labels, hints, empty-state sentences and messages are **product content** rather than an
implementation detail — English, like the rest of this repository
([`../conventions.md`](../conventions.md) § Language). They are agreed with the person who will
read them, they are reviewed, and they belong in a document a non-programmer can open.

The refusal sentences an operator sees are the exception that proves the rule: they live beside
the endpoint that produces them (see [`../api.md`](../api.md)), and a screen document says which
of them that screen can display.

## Naming

`<screen-slug>.md`, matching the route, with front matter carrying `route`, `info_ref` (the
frozen screen identifier `S-xx`, if one exists) and the requirements the screen satisfies.

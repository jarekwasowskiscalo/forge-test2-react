---
screen: <screen-slug>
route: /<route>
info_ref: S-NN                # the screen's frozen identifier, or null
requirements: []              # the CR-YYMM-xxxx/R-n identifiers this screen satisfies
mockup: spec/changes/CR-YYMM-xxxx/design/ui/index.html
---

# <Screen name>

One sentence: whose screen this is and what that person does on it all day.

## Regions

A short list, top to bottom. Not a pixel layout — the mockup holds that.

## Components and their states

One table per component, listing **only the states that exist on the built screen** — a row
whose content would be "not implemented" says nothing a reader can use. What the mockup does
not draw still matters when it exists in the code: `empty` is the state a back-office screen
actually lives in on its first day, and a `disabled` control has to say *why* it is disabled,
or it is a dead end. States considered and genuinely absent are declared once, on a line
below the table — when none was considered, the line is omitted.

State names stay in their source form — they are identifiers matching the CSS and component
states, not product copy.

### <Component>

| State | What the user sees |
|---|---|
| default | |
| empty | the sentence shown when there is nothing, and what the user is to do next |
| error | the message, verbatim |

States omitted: <state> — <why it cannot occur on this component>.

## Copy

Verbatim, reviewed with the person who reads it. This is product content, not an
implementation detail.

| Key | Copy |
|---|---|
| title | |
| empty state | |
| primary action | |

The refusal messages an operator sees stay beside the endpoint that produces them
(`spec/design/api.md`); list here only *which* of them this screen can show.

## Data

Bound to the live contract in `spec/design/api.md`, the same document the Copy section above
points at. Every field named here has to exist there — a screen showing a field the contract
does not carry is exactly the divergence the coherence gate looks for.

**Never bind to a change's own `design/delta/api.md`.** A change produces that fragment and
only that fragment: it describes what this change alters, so a binding into it resolves, looks
successful and is measured against a difference rather than against the contract.

The Source column names whatever this stack binds a field to (`binding_target` in
`.specconf/stack.json`; your preflight names it under `MECHANISMS`) — an endpoint where the
contract is served over HTTP, a repository and method where it is an interface in the stack's
own language.

| Element | Source | Fields |
|---|---|---|

## Interactions

- **<action>** → <what happens>, <what the user sees meanwhile>, <what happens on failure>.

Keyboard: <the paths that have to work without a mouse>.

## Layout by window class

One row per window class this stack declares (`window_classes` in `.specconf/stack.json`;
your preflight names them under `WINDOW CLASSES`). **A stack that declares none omits this
section entirely** — a screen there is one layout, as it always was.

| Window class | What is on the screen |
|---|---|

A screen whose layout does not change says that in one line: that is an answer, and an absent
section is not. A class this screen deliberately does not serve is named here with the reason,
not left out — left out reads as a screen somebody drew at one width and nobody asked about at
the others.

The class changes where a region is, rarely whether it exists. Where it does remove one, say so
here and say why the thing that region reached is already on the screen.

## Tokens

Named tokens only. Where the tokens live — the one file for colour, the scale or the file for
sizes, spacing, radii and shadows — is this stack's rule, in `spec/design/conventions.md`, and
this stack's `HAND-OFF` note for `design-ui` names the files. **Never a raw colour value or a
magic number** in a component: a raw colour is a token nobody has named yet, and it is
invisible to every later change of the palette.

| Use | Token |
|---|---|

## Out of scope for this screen

What it deliberately does not do, so that the absence reads as a decision rather than a gap.

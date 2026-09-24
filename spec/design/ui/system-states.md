---
screen: system-states
route: "all routes"
info_ref: null
requirements: [CR-2609-823a/R-5, CR-2609-823a/R-10]
mockup: null
---

# The page frame and the shared states

Not one screen, but what every screen shares: the page frame (`PageFrame`) and the primitives
every list in this application needs — emptiness, error and loading
(`frontend/src/components/ui/Feedback.tsx`) — plus the status page outside the normal flow.

## One column

**There is no top bar and no side panel.** The application has two screens, the guestbook and
the to-do list, and the way between them is **two text links in the page header, beside the
lockup** (§ Components and their states) — not a bar of its own, and not a switcher that looks
like the guestbook's order pills, which would read as a filter. The screen is a single centred
column up to 860 px wide, with its own header and its own footer; the frame is drawn by
`frontend/src/components/shell/PageFrame.tsx` and by nothing else.

The navigation is here because this is the one seam — `PageFrame` — and the second screen added
it here rather than as a route alone. A third screen adds one link to the same navigation: an
edit to one file rather than a hunt through components.

The frame is **part of the page, not a shell the pages live inside**: every screen renders its
own `PageFrame` and `frontend/src/router.tsx` has no layout route. A layout route with one child
is indirection with nothing on the other side of it.

## One palette

**The dark theme was withdrawn, and that is a decision rather than an oversight.** The switch
lived in the top bar that was deleted, and the mock-up this screen comes from has a single
palette. `frontend/src/styles/theme.css` remains the only home of colour and carries one
palette; there is no `:root[data-theme='dark']` rule and no `localStorage`.

The consequence to know before restoring a theme: **no component branches on the theme** and
that property is to stay. A second theme comes back as a second block of tokens in the same
file, together with the mock-up that describes it — never as an `if` in a component. This is
held by `frontend/src/styles/theme.test.ts`.

**A token name may not collide with a class name from the Tailwind scale.** The token
`--color-base` produced a `.text-base` class beside the built-in `text-base` size, the colour
won, and the whole body of every entry was white on white — in the built application, without a
single red test. That is why the card surface is called `card` rather than `base`, and why this
rule is checked by code rather than remembered.

## Typeface

Two families from a font host: **Instrument Serif** for the screen title, **Instrument Sans**
for the rest. Each has a fallback stack in its token, and that is a requirement rather than an
ornament: a screen that needs a successful network request before it can say anything is blank
on a bad connection. The smoke proves this by blocking the font stylesheet and demanding the
heading anyway.

## Regions

- **Page header** — the product lockup on the left, followed by the navigation between the
  screens; one fact about the whole page on the right, supplied by the screen (the guestbook: its
  number of entries; the to-do list: its number of tasks; the not-found page: none).
- **Title and introductory sentence** — the serif screen title and one sentence about what it is
  for and what using it costs.
- **Content** — variable; today two built screens.
- **Footer** — one sentence about who sees this, and it belongs to the screen: each screen's
  document carries its words ([`guestbook.md`](guestbook.md) § Copy,
  [`todo-list.md`](todo-list.md) § Copy), and the not-found page has none.
- **Not-found page** (route `*`, **inside** the frame) — every path with no matching route. The
  navigation is on it too, with neither screen marked as the one on show.

**The lockup is an explicit placeholder and is meant to look like one.** A square with the
initial "P" and the name "Product name" in `PageFrame.tsx` (`PRODUCT_NAME`, `PRODUCT_INITIAL`) —
two strings to replace. A template shipping a plausible-looking mark would ship as somebody's
product under a brand nobody chose. With two screens the lockup cannot carry either screen's
name: "Guestbook" there named the product after one of its screens, and stood beside a
navigation link of the same name — two identical links side by side.

**The lockup is a link on every screen, including the one it points at.** It leads to the
guestbook's address, as it did. It is the way back from a 404, and a way back that exists only
on the page you did not get lost on is a way back nobody finds.

**There is no "signed in" section and no login route.** This application authenticates nobody. A
product that starts to mounts a 401 redirect in `frontend/src/api/client.ts` — that module's
docstring names the place.

## Components and their states

### The navigation between the screens

| State | What is visible |
|---|---|
| default | after the lockup, two text links, "Guestbook" and "To-do list", in `--color-muted`; the group is named "Screens" for assistive technology |
| hover | the link's text turns `--color-ink` |
| focus | the screen's focus ring around the link |
| current | the link of the screen on show is in `--color-ink`, medium weight and underlined, and says so to assistive technology (`aria-current="page"`); on the not-found page neither link is current |

States omitted: active — no pressed look of its own, since a link simply navigates; disabled —
both links always lead somewhere, the current one included; loading, error, empty — the
navigation reads nothing, so it has nothing to wait for, to fail at or to lack.

**The navigation is on every screen, the not-found page included**, and the link of the screen
on show stays a link, marked rather than removed.

### `EmptyState`

| State | What is visible |
|---|---|
| `empty` | a title, a hint sentence, an optional action |

Emptiness **always carries a sentence about what to do**. A bare "No data" title leaves a person
wondering whether it is their fault or a failure.

### `ErrorState`

| State | What is visible |
|---|---|
| `error` | `role="alert"`, a title, the sentence from the refusal, a list of fields on a `422`, a "Try again" action |

**The retry action disappears on refusals a retry will not fix.** A `404` is such a case: asking
again for something that is not there cannot succeed, so inviting it is lying. This is settled by
`describeProblem` in `frontend/src/api/problem.ts` — reading a status code and deciding what it
means to a person is knowledge about **this** API and cannot live in a primitive that only
paints.

### `Skeleton`

| State | What is visible |
|---|---|
| `loading` | rectangles in the shape of the content being loaded |

A skeleton, not a spinner: the height is reserved, so content does not jump under the cursor the
moment it arrives. The guestbook screen composes its own skeleton from `Skeleton` in the shape of
cards; a table primitive will appear together with the first real table and not before
(`conventions.md`: a primitive with no caller is removed).

### `Toast`

| Variant | When |
|---|---|
| `success` | the write succeeded |
| `warning` | it succeeded partly or with a caveat |
| `error` | the write failed |

A toast is **a confirmation, never the only carrier of information**, so a fact that must
survive belongs to the screen rather than to a toast. **A success or warning toast disappears on
its own after a few seconds; an error toast stays until it is dismissed** with its "×" — an
error that vanished while somebody looked elsewhere would be quieter than the success beside
it. Either way the screen under it is unchanged by a write that failed, and that unchanged
screen is the lasting fact. There are two `aria-live` regions — polite for successes, assertive
for errors.

## Copy

English, like the rest of this repository ([`../conventions.md`](../conventions.md) § Language).

| Key | Text |
|---|---|
| product name | `Product name` |
| product initial | `P` |
| navigation — name read aloud | `Screens` |
| navigation — links | `Guestbook` · `To-do list` |
| 404 — title | `Nothing here` |
| 404 — sentence | `There is nothing at this address.` |
| 404 — action | `Go to the guestbook` |
| error — cannot reach | `Could not reach the service` |
| error — 404 | `That is gone` |
| error — 404, sentence | `What you asked for does not exist. Somebody else may have deleted it.` |
| error — no detail | `The service returned no detail. Try again, or check whether the backend answers on /api/health.` |
| retry action | `Try again` |

**The 404 sentence counts no screens.** "There is one screen in this application: the guestbook."
stopped being true when the to-do list arrived, and a sentence that counts screens stops being
true again with the next one. The footer is not here because it is each screen's own
(§ Regions).

## Data

The frame reads nothing. There is no session query and no modules query. This is a property
rather than a saving: a frame that waits for an answer flickers on every entry. The fact in the
header is supplied by the screen, which has it anyway — the guestbook's number of entries, the
to-do list's number of tasks. The navigation is two fixed addresses and reads nothing either.

## Interactions

| Event | Effect |
|---|---|
| clicking the lockup | React Router navigation to `/guestbook`, without a reload |
| clicking "Guestbook" or "To-do list" | React Router navigation to `/guestbook` or `/todo-list`, without a reload |
| entering `/` | a redirect to `/guestbook` |
| entering `/todo-list` | the to-do list ([`todo-list.md`](todo-list.md)) |
| entering an unknown route | the 404 page **inside** the frame — the way back stays on screen |

**Opening the to-do list reads its list, every time — the header link included.** Opened by its
address, by a reload or by the link "To-do list", the screen shows the tasks as they are stored at
that moment, other people's changes of the last few seconds included, and never a copy it read
earlier (`CR-2609-823a/R-3`). The user decided it in `CR-2609-823a` (`Q-25`) in these words:
"Always fetch the latest." The guestbook is unchanged by that decision: opened by a link within
30 seconds of its last read, it shows that read without asking the service again
(`frontend/src/main.tsx`, `staleTime`), and a reload, or a change made on it, reads it afresh.

**The browser stores nothing.** There is no `localStorage`, no cookie, no state that survives a
tab — after the theme was withdrawn nothing was left that belonged there.

## Tokens

Named tokens only, all in `frontend/src/styles/theme.css`. **Never a raw hex value or a bracketed
value for colour** (`bg-[#222]`) in a component: a raw colour is a token nobody has named yet, and
it is invisible to every later change of the palette. Sizes outside the Tailwind scale
(`rounded-[14px]`, `px-[18px]`) are allowed — they come from the mock-up and are not colour.

**A text token clears 4.5:1 against the darkest surface it can be painted on** (WCAG 2.1,
success criterion 1.4.3). The floor is a property of **the token**, not of the place it happens
to be used: a value chosen against white and then painted on `--color-surface-medium` is a value
nobody measured. Two exemptions, and both are written down because a default nobody recorded
cannot be told from an oversight:

| Exempt | Why |
|---|---|
| `--color-disabled` (1.82:1) | 1.4.3 exempts the text of an inactive control. The token has no other use. |
| An `aria-hidden` graphic | Not text. The toolbar's magnifier is decoration beside a labelled field. |

Two checks hold it, and they answer different questions.
`tests/fitness/test_design_tokens.py` reads this file and judges **the palette**, including a
pairing no screen currently renders; `e2e/ui/test_smoke.py` measures **the screen** in a browser,
taking the background from the ancestor that actually paints one rather than from the token the
component names. A palette checked only where it is used today fails on the day somebody uses a
token somewhere new; a palette checked only in the abstract never notices what a component
actually put behind the text.

Rejected (decision of 2026-09-16, `cr: historical` — measured from the trunk, where neither an
ADR nor a `delta.md` is available):

- **Measure against white and call the rest close enough.** `--color-faint` at `#9b978c` gave
  2.92:1 on a card and 2.54:1 on `--color-surface-medium`. Both fail, but only the second says
  what the fix has to clear, and a floor that is not the real floor is a number people round.
- **Allow the 3:1 large-text floor as a general escape.** Every site this palette paints in a
  quiet token is 12px or 13px. An exemption nothing qualifies for is an invitation to make
  something qualify.
- **Darken `--color-faint` to `--color-muted` and delete one of them.** The token exists to be
  quieter than `--color-muted`; a palette with one grey says less, and the sentence "this is
  chrome, that is content" then has to be carried by size alone.

## Out of scope

- **Responsiveness.** The column narrows with the window, but a mobile view is not designed —
  that is a separate decision and a separate mock-up.
- **Dark theme.** Withdrawn, see § One palette.
- **A navigation bar, a module switcher or a side panel.** The way between the screens is the
  header's two links (§ One column).

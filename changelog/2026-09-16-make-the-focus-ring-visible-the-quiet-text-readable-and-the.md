---
date: 2026-09-16
branch: a11y/visible-focus-and-contrast-floor
pr: 50
kind: fix
---

# Make the focus ring visible, the quiet text readable, and the dialog genuinely modal

## What changed

**The focus ring.** `outline-none` removed from the six elements that carried it —
`frontend/src/contexts/guestbook/components/EntryComposer.tsx` (both fields),
`EntryCard.tsx` (both editor fields), `EntryToolbar.tsx` (search) and
`frontend/src/components/ui/Modal.tsx` (the `role="dialog"` container).

**The palette.** `frontend/src/styles/theme.css` — `--color-faint` darkened from `#9b978c` to
`#6e6a5f`. One value; six of its seven call sites are fixed by it.

**The dialog.** `frontend/src/components/ui/Modal.tsx`: the initial focus is now verified rather
than assumed; the Tab trap moved from the overlay's `onKeyDown` to a `document` listener; the
background is marked `inert` for the dialog's lifetime; focus restore falls back up the trigger's
own ancestry when the trigger has left the page; and the comment explaining why this is not a
native `<dialog>` was rewritten, because the reason it gave was false.

**Tests.** New `e2e/ui/styles.py` (computed styles, the painting ancestor, WCAG arithmetic) and
three tests in `e2e/ui/test_smoke.py`. New `frontend/src/components/ui/Modal.test.tsx`, ten tests.
`frontend/src/contexts/guestbook/components/DeleteEntryDialog.test.tsx` gains the
`document.activeElement` assertion its `in flight` block never made.
`tests/fitness/test_design_tokens.py` gains the palette's contrast floor and the proof that the
detector fires.

**Specification.** `spec/design/ui/guestbook.md` (the ring as a rule, the dialog's focus
behaviour, the `<dialog>` decision), `spec/design/ui/system-states.md` § Tokens (the 4.5:1 floor
and its two written exemptions), `spec/design/testing.md` (§ The UI smoke in a browser, and the
fitness table's row for `test_design_tokens.py`).

## Why

Two confirmed findings of the 2026-09-15 audit, filed as
[#27](https://github.com/Scalo-Sales-Engineering-Consulting/forge_template_python_react/issues/27).
They travel together because both edit `Modal.tsx`, and because the first blocks the second: the
dialog container carries the ring that the repaired focus fallback needs in order to be visible.

`frontend/src/index.css` declares the ring on `:focus-visible` inside `@layer base` and says, in
a comment, that it is "deliberately visible: this screen is walked with a keyboard".
`spec/design/ui/guestbook.md` promised the same. The built stylesheet shipped
`outline-style: none` on every field, because `@layer utilities` is a **later layer** than
`@layer base` and layer order settles the cascade before specificity is consulted. The rule
matched and lost. Nothing failed: the component suite runs in jsdom, which loads no application
CSS, implements no `@layer` and does not support `:focus-visible`, so the question could not be
asked there at all.

`--color-faint` painted the card's own Edit and Delete actions, every timestamp, the character
counter, the footer, and — through `::placeholder` — the only label the composer's fields have.
`--color-muted` measured 7.09:1 throughout, which is what says one token was wrong rather than
the palette.

The dialog claimed `aria-modal="true"` and did not implement it. Its focus target was chosen with
`??`, which falls through on `null` alone — and a *disabled* Cancel button is a live element, so
`.focus()` was called, ignored, and the container fallback never reached. The component's own
comment describes that exact scenario as handled. The Tab trap sat on the overlay's `onKeyDown`,
but the dialog is a React sibling of the page, so a keydown from a control behind it never
reached the handler; the branch written to recover focus from outside the container had never
run. Escape had been bound to `document` for precisely this reason, with a comment explaining it.
One mechanism knew the trap; the other did not.

## From what, to what

| | Before | After |
|---|---|---|
| Focus ring, built CSS | `outline-style: none`, `outline-width: 2px` — the base rule matched and lost one property | a 2px accent ring at every keyboard stop |
| `--color-faint` on a card | 2.92:1 | 5.40:1 |
| …on the page surface | 2.67:1 | 4.95:1 |
| …on `--color-surface-medium` | 2.54:1 | 4.69:1 |
| Focus when the dialog opens with both buttons locked | on the Delete button **behind** the modal | on the `role="dialog"` container |
| Tab with focus behind the modal | walks further into the page | returns into the dialog |
| The page behind the dialog | reachable by mouse, Tab and screen reader | `inert` for the dialog's lifetime, restored exactly as found |
| Focus after a confirmed delete | `<body>` — the next Tab restarts at the top | the nearest ancestor of the vanished button still on screen |
| Why not `<dialog>` | "this app's `position: absolute` overlays" — there is not one in the tree | the top layer would cover the toast host; `<dialog>` closes on Escape and the `loading` state may not |

## How it works now

The ring is the screen's and no component cancels it. It is declared once, on `:focus-visible` in
`@layer base`. A field that wants a different ring writes `focus-visible:outline-*` as a utility,
which competes inside the same layer; it never removes the ring and leaves nothing.

A text token clears 4.5:1 against the **darkest surface it can be painted on**, not against
white. Two exemptions are written down rather than assumed: `--color-disabled`, which WCAG 1.4.3
exempts because it is the text of an inactive control, and an `aria-hidden` graphic, which is not
text. Both checks that hold this are named in `spec/design/ui/system-states.md` § Tokens.

`Modal` asks whether the element it wanted actually took the focus — `document.activeElement`
after the call — instead of whether that element exists. That covers a disabled node, a hidden
one, a `display: none` one and a detached one, rather than the single case reported. Its focus,
inert and restore now live in **one** layout effect, because their order is the mechanism:
marking the background inert blurs whatever is focused inside it, so the trigger must be read
first, and restoring focus to the trigger needs the background live again, so the cleanup must
undo them in the opposite order. It is a layout effect rather than a passive one because
`GuestbookPage` clears the dialog and pushes the error toast in the same commit when a delete
fails, and the toast's `aria-live` host lives inside `#root` — a cleanup after paint would put
the announcement into a still-inert subtree.

The background is "every element under `<body>` except this dialog's own portal node". In the
application that is `#root`; saying it that way keeps the rule true under a test renderer too,
and nodes that were already inert are left out so the cleanup restores the page it found.

## What it means for the process

Nothing about running or changing this repository moves. One habit is now enforced rather than
hoped for: a colour token is measured before it is added, and the failure names the surface it
failed against. `e2e/ui/styles.py` is where a browser-side style measurement goes;
`tests/fitness/test_ui_suite.py` keeps `playwright` inside `e2e/ui/`, so it could not live
anywhere else.

## What it does not change

- **No ADR was written.** `spec/design/conventions.md` § When a decision is an ADR keeps
  `spec/ADR/` empty until the first change carried out through `/sdd`, and
  `spec/changes/EXEMPTIONS.md` says outright that a decision taken on the trunk goes into the
  document whose rule it changes, as a dated `Rejected (…, cr: historical — …)` block. Both
  decisions here are recorded that way. `spec/ADR/index.md` is untouched.
- **`--color-disabled` stays at 1.82:1.** Exempt, now in writing.
- **The native `<dialog>` is still refused**, and the reason is now true. Revisit it together
  with the toast host, not on its own.
- **No behaviour of the API, the schema or the black box moves.** No new dependency: the WCAG
  arithmetic is fifteen lines in `e2e/ui/styles.py` and fifteen in the fitness module.
- **The mobile view and the dark theme remain named non-goals.**

## How it was verified

**Every new test was seen failing first, on this branch, before the fix.** The three browser
tests reported `outline-style=none outline-width=2px` on all five fields — both properties at
once, which is the point of asserting both — and the contrast pairs at 2.92:1 and 2.67:1, the
numbers the audit reported. Five of the ten `Modal.test.tsx` tests failed, one per defect. The
fitness test named `--color-faint` on all three surfaces.

One of them was green for the wrong reason and was rewritten: Tab from the background landed in
the dialog with no trap at all, because the portal is last in the document and jsdom's Tab simply
walks in document order. It now starts from the **first** background control, where the next stop
is another background control, so only the trap can produce the expected result.

After the fix:

- `./scripts/test.sh frontend` — 112 passed, 13 files.
- `./scripts/test.sh fitness` — 255 passed.
- `./scripts/test.sh ui` — 17 passed, against a **rebuilt** bundle.
- `./scripts/check.sh` and `sdd-specs` — below.

A trap worth recording: `scripts/test.sh` builds the SPA only when `app/static/index.html` is
**missing**, never when it is stale, so the first run after the fix graded the previous bundle
and reported three failures against code that was already correct. `./scripts/build.sh` before
`./scripts/test.sh ui` is the local remedy; CI never sees it, because a clean checkout has no
`app/static/`.

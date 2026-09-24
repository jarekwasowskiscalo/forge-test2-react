# Claude Design mock-up — guestbook, 2026-08-31

The source material the guestbook screen was built from, and from which
[`spec/design/ui/guestbook.md`](../../design/ui/guestbook.md) was derived.

| File | What it is |
|---|---|
| `Guestbook.dc.html` | the mock-up — this is what both documents cite |
| `support.js` | the Claude Design runtime the mock-up needs in order to render |

Open `Guestbook.dc.html` in a browser; both files must sit beside each other.

## Why this is in the repository

Because two normative documents referred to `Guestbook.dc.html` in backticks while the file was
not in the tree — it lived only in an untracked archive in the root, which a fresh clone does not
have and which `git clean` would delete. A cross-cutting decision stood on evidence nobody but
its author could open.

No gate caught this and none could: `backtick-paths` (`G10` then) reads tokens that look like a path, and a bare file
name with no slash fails on the first condition of `_path_shaped`. That is a known and recorded
blind spot rather than an oversight — see the engine's `check_specs.py`,
`_directory_shaped`.

## What this directory does NOT mean

The mock-up is **a description of where the screen came from**, not a rule that holds now. What
holds is `spec/design/ui/guestbook.md`; when the screen and the mock-up diverge, the screen's
specification is right, and the mock-up stays as it was on the day it was made
(`spec/rationale/README.md` § A document here is dated).

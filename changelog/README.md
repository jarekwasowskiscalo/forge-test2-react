# The changelog

**For:** anyone who wants to know what was done to this repository outside the change
process, and why.
**Normative source:** `spec/constitution.md` § Where the process's own files are named,
which makes framework changes on the trunk and gives them no `delta.md`.

One file per pull request. A change that did **not** go through `/forge:sdd` writes an entry
here saying what it changed, why, from what to what, how the thing works now, and what it
means for the process.

## What belongs here, and what does not

The two registers cut the same history in one place, by the road a change took:

| The change | Where its record is |
|---|---|
| went through `/forge:sdd` | `spec/changes/<CR>/`, and its `delta.md` declares every line it moved under `spec/` |
| did not — the scripts, CI, the documentation, the tooling, a repair on the trunk | here |

So an entry here is never written for a change that has a change directory, and a change
directory is never opened to record something this file would hold. One byte, one home.

This is not the release notes. Nothing here is generated from commits and nothing here is
published; it is the reasoning behind a change, kept where the next person reading the tree
will find it.

## Writing one

```bash
./scripts/changelog.sh new "Say what the change makes true"
```

That writes `changelog/<today>-<slug>.md` from the form and opens nothing — fill it in. The
gate in CI reads it on the pull request; `./scripts/changelog.sh check` is the same gate,
locally.

The title is the commit subject: an imperative sentence, no type prefix, no ticket. *Refuse a
malformed stored note in the serializer, so a corrupt record is a failure and not a crash* —
what the change makes true, not what was edited.

**Do not remove a section.** An empty section is information; a missing one is a hole in the
record. Where a section has no content, write the sentence that says so: *None — this is
internal to the tooling and no operator sees it.*

**Name paths in `backticks`, never as a Markdown link.** The `links` gate resolves every
link in every document in this tree and has no exception for history, so a link to a file
that later moves turns a future build red over a record nobody should edit. Backticks are
also how the rest of this repository names a file.

## When an entry is not required

Three cases, and the gate knows all three:

- **A change record exists.** The pull request touches `spec/changes/CR-*/`; the process
  already recorded it.
- **The author is a bot.** Dependabot cannot write prose, and a rule that demands it would be
  red on every weekly bump until somebody typed a sentence that told nobody anything.
- **The `no-changelog` label is on the pull request.** For a typo or a whitespace fix. It is
  visible on the pull request, which is the point: an exception a path filter makes silently
  is an exception nobody reviews. The label is a repository setting rather than a file, so a
  clone of this template starts without it and the exemption cannot be taken until somebody
  creates it — `.github/labels.md` registers the three CI branches on and says how.

## Why these files are at the root and not under `docs/`

`docs/` is what somebody operates the system with, and it is held to that: the
`documentation-set` gate wants every page named in `docs/README.md` and carrying its two
declaration lines, which a growing set of dated records cannot pay per file.

The deciding reason is a different gate. `operations-doc` is satisfied by any edit under
`docs/`, so a changelog living there would answer it — and a one-line entry would quietly
excuse skipping the operator documentation a change actually owed. A gate turned off by
accident is worse than a directory in an unusual place.

Entries are exempt from `backtick-paths` for the reason the dated audits under
`spec/rationale/` are: a record describes the tree on the day it was written, and editing it
years later to satisfy a path checker makes it agree with today at the cost of no longer
being a record.

<!-- Short on purpose. A checklist long enough to skim is a checklist nobody reads,
     and every box here is one a machine cannot tick for you. Everything mechanical
     is already asserted by `scripts/check.sh` and by CI. -->

## What changes, and why

<!-- One paragraph. The reviewer's first question is never "what did you type". -->

## The specification

- [ ] This change touches `spec/`, `contracts/` or `alembic/versions/` — and the
      edit travels in **this** pull request, declared line by line in the change's
      `delta.md`.
- [ ] It does not, and that is a fact rather than an omission.

<!-- One of the two, not both. sdd120's finding is that the element teams miss is
     never the gate -- it is the enforced return to the specification. Gates are
     visible, so they get built; the loop back is invisible, so it stays an
     aspiration. This box is that loop, and it costs one line. -->

## The changelog

- [ ] This change went through `/forge:sdd` — the record is `spec/changes/<CR>/` and no
      entry is owed.
- [ ] It did not, and it adds one entry under `changelog/` saying what changed, why, and
      what it means for the process.

<!-- One of the two. `./scripts/changelog.sh new "<title>"` writes the form. A typo or a
     whitespace fix takes the `no-changelog` label instead -- visible on the pull request,
     which is the point of having a label rather than a path filter. -->

## Evidence

<!-- What you ran, and what it said. `./scripts/check.sh` is the local definition
     of "will CI pass"; name anything you could not run and why. -->

---

<!-- Reaching for the `spec-exempt` label? It is a break-glass, not a shortcut: it
     needs a matching open row in `spec/changes/EXEMPTIONS.md`, with a reason and
     an expiry date. An exemption nobody has to renew is a rule that was quietly
     deleted. How a change travels: the process's `sdd-handbook.md`. -->

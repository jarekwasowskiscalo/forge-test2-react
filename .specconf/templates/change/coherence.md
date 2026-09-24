<!-- TEMPLATE: filled in by any stage; the file counts as non-existent until this marker is gone -->
# Coherence — <change title>

*ONE file for the whole change, one section per pass. Previously there was a file per
finding: 24 files and 1 677 lines for four requirements, and then 24 separate calls to
close them. The `coherence_files: 1` budget in `.specconf/process.json` is hard.*

## Pass 1 — stage `<stage>`

### COH-<stage>-1 — <the contradiction, as one question or one sentence>

- **kind:** contradiction
- **severity:** critical
- **decision_mode:** AUTO
- **auto_basis:** <the rule, contract or invariant that settles it — empty when nothing does>
- **ambiguity_source:** <the document and section that let them disagree>
- **artifacts:** <artefact one>, <artefact two>

**What each says.** <one paragraph per document, in its own words, with the section cited>

**Why they cannot both be true.** <one paragraph>

**What settles it.** <the citation — or "nothing; NEEDS_DECISION">

**Resolution.** <one sentence>

**What was ambiguous.** <the sentence that admits both readings>

**What was not found.** <one sentence — silence and "checked, they agree" look identical
afterwards, and only one of them is information>

*One `###` block per finding, numbered after the ones already recorded; the stage lives in
the identifier, never in a heading. `kind` is one of `contradiction`, `gap`, `quality`,
`verification`; `severity` is one of `critical`, `major`, `minor`.
`sdd-engine change_state record-coherence` parses exactly this shape and refuses any other
value, naming the identifier — a block in another shape is a finding that never reaches the
record.
A repository path inside a quotation is written as a plain backticked path from the
repository root, never as a Markdown link. A link is resolved from the file that carries it,
so a target quoted faithfully out of a document at another depth points nowhere from here —
and the `links` gate then goes red on the quotation rather than on the document quoted.*

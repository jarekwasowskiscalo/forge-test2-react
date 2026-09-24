# Change-record templates

**One set of templates for every tier.** The `p0/` and `p1/` directories disappeared
together with the skills that read them: a tier now selects STEPS from one skills catalogue
(`.specconf/process.json`) rather than forms from a separate template directory. Two sets of
forms for one process are two versions of the same document, of which only one was ever
maintained.

What comes into being in a change record, and by whom:

| File | Stage | Author |
|---|---|---|
| `input/README.md` | intake | an instruction for a human, not a form |
| `impact.md` | requirements | `cr-impact` — plus the measured tier signals |
| `requirements.md` | requirements | `cr-requirements`, with a `## Self-check` section |
| `scenarios.md` | requirements | `cr-scenarios` |
| `tasks.md` | plan | `design-plan` |
| `uat.md` | implement | `build-tests-uat` |
| `delta.md` | every stage boundary | **assembled** from fragments by `close_stage` |

Three templates are deliberately not scaffolded. `delta-fragment.md` and `coherence.md` sit in
this directory as patterns but are absent from `scaffold.MANIFEST`: they are written per author
and per pass, and an empty copy would read as "somebody checked and found nothing", which is
exactly what those files cannot claim without being written.
`brainstorm.md` comes into being only when the conversation actually happened.

**The design has no template here, because it does not live in the change record.** The
`design-*` authors edit `spec/contexts/`, `spec/design/` and `spec/design/ui/` and leave a
delta fragment in `design/delta/<name>.md`.

The budget philosophy: a specification is to be readable by the human who approves it. The
line budgets stand in the headers of the templates themselves (the `BUDGET` comment) — write
the shortest version that is unambiguous; every sentence that changes neither the system's
behaviour nor a test is to be deleted.

Copying the templates into a change directory (and choosing the tier) is managed by
the engine's `scaffold.py` — this directory only supplies the forms.
Every form opens with a `TEMPLATE` marker; the file counts as non-existent until that
marker is gone.

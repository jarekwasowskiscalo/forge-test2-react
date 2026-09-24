# Specification delta — the guestbook, the template's worked example

> Retrospective, and assembled by hand rather than by `close_stage`: this change shipped
> before there were delta fragments to assemble, so the generator's section below is empty
> and truthfully so. The entries here name the specification documents the guestbook created.

## Entries

- `ADDED` `spec/contexts/guestbook.md` — the bounded context: the language, the one process
  `P-01` with its four steps, and the five business rules `BR-01` to `BR-05`.
  **Why:** A behaviour with no context document is a behaviour that lives only in code, and
  the first question anybody asks about this template is what the application actually does.
  It is also the file that fixes the shape of every later context: a rule and a flow live
  here, a column lives in the data-model register and a contract field in the API register,
  so that one fact has exactly one home and no document can contradict another about it.

- `ADDED` `spec/design/ui/guestbook.md` — the screen specification: regions, every component
  state, the copy and the bindings to the API contract.
  **Why:** Two implementers build the backend and the frontend against a frozen contract
  without talking to each other, and the half of the agreement that a contract cannot carry
  is what the screen does when there are no entries, when a search matches nothing, and when
  a value is being typed but is not yet wrong. Without that document those three states get
  invented twice and differently.

- `MODIFIED` `spec/design/api.md` — the entry endpoints, their shapes, the two sort words
  and a stable code plus a finished sentence for every refusal.
  **Why:** The register is what the frontend is built against before the backend exists, so
  it has to answer more than "what fields": it has to name each refusal in words a screen can
  show a person, because a refusal rendered as a raw status code is a defect the contract
  invited rather than one the implementer introduced.

- `MODIFIED` `spec/design/data-model.md` — the entries table, its columns, the bounds and
  the index that carries the default order.
  **Why:** The two length bounds have to be the same numbers in the browser and in the
  column, and the only way that stays true is for one document to own them and both sides to
  cite it. The index is here for the same reason: the order is a promise of the contract, so
  what makes it cheap belongs in the register rather than in whichever migration happened to
  add it.

- `ADDED` `contracts/openapi/guestbook.yaml` — the HTTP boundary, hand-written and versioned.
  **Why:** The constitution's article VI makes the contract the authority and the code the
  thing validated against it, which only means something if a human wrote the contract. A
  document generated from the implementation agrees with the implementation by construction
  and can therefore never catch it drifting — it records what the code does rather than what
  the code owes.

- `ADDED` `contracts/invariants/guestbook.md` — the data invariants this domain's storage has
  to keep: `D-01`, a record is one record for its whole lifecycle; `D-02`, a relation replaces
  a copied column; `D-03`, a technical identifier is a UUID. Each carries a witness and a kind
  of evidence, and the guestbook satisfies all three by construction — one table, no relations
  to copy from, and an application-generated `Uuid` primary key.
  **Why:** These are promises about the *shape* of stored data, and an HTTP schema cannot
  express one of them. They are stated here rather than inside the context document because
  they outlive this example: a fork that deletes the guestbook keeps them, which is the whole
  reason the boundary owns a file of its own. The rules specific to the guestbook's own
  behaviour — both moments equal on a new entry, a total order, trimming before measuring —
  are not here and were never meant to be: they live as `BR-01` to `BR-05` in
  `spec/contexts/guestbook.md`, and the contract that carries them to the wire is the OpenAPI
  document above.

- `ADDED` `golden-set/fixtures/entries-ordinary.json`,
  `golden-set/fixtures/entries-boundary.json`, `golden-set/fixtures/entries-refused.json` —
  the reference corpus the suites read instead of inventing values. Shipped flat, directly
  under `golden-set/`; the corpus was later cut in two by what the data is for, and these
  three are the half that is asserted about.
  **Why:** Boundary values invented inside a test drift from the boundary values invented
  inside another test, and the pair that matters most here — eighty characters and
  eighty-one — is exactly the pair somebody gets wrong twice in different directions. One
  corpus, located by one module (`tests/_golden_set.py`), means the browser suite and the
  backend suite are arguing about the same strings.

- `ADDED` `golden-set/seed/entries-welcome.json` — the other half: what a freshly created
  environment opens with, posted through the API by `scripts/seed.sh` and asserted about by
  nothing.
  **Why:** An empty screen is a screen nobody can judge, so a preview or a fresh clone needs
  something on it — but the moment a suite asserts about that something, it stops being free
  to change and the seed becomes a fixture by accident. The split is what keeps the two kinds
  of data from being confused, and a fitness test refuses a suite that reads this half.

- `ADDED` `e2e/suite/features/guestbook.feature` and the steps under `e2e/suite/steps/` — the
  black box, in business language, every scenario tagged with the requirement it proves.
  **Why:** A requirement with no witness outside the code is a requirement the code gets to
  mark its own homework, and the tag is what makes the traceability gate able to see the
  witness at all. Written in Gherkin rather than as more pytest because the audience is
  somebody who will not read pytest — the scenarios are the artefact a non-programmer uses to
  find out what the system promises.

- `ADDED` `spec/rationale/mockup-guestbook/` — the Claude Design mock-up the screen
  specification was written from.
  **Why:** The screen document says what every state does; the mock-up says what it looks
  like, and the two are written at different times by different means. Keeping the source
  artefact means a later reader can tell which of the two moved when they disagree, instead of
  guessing that the specification was always the drawing's equal.

<!-- ASSEMBLED FROM FRAGMENTS -- do not edit below; the source: design/delta/, reconcile/delta/ -->

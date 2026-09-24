"""Step definitions, one module per business concern.

The split matches `app/services/` and the routers of the same names, so a reader
who knows the backend already knows which file a step belongs in. One concern
today; the convention is what keeps the second one from landing in the first
one's file.

These modules own -- and are the only thing in the repository that owns -- which
endpoint a scenario means, which JSON field carries the answer, and what a status
code means to the business. **The `.feature` files must contain none of that**,
which is why the translation lives here and nowhere else.

Private helpers stay in the module that uses them: the file this convention
replaces reached into another module for three underscore-prefixed names, and
that import is the reason one write step could skip the bookkeeping every other
one went through.
"""

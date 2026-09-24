"""the Pydantic request and response shapes at this context's edge.

The layer is a directory inside the context rather than a directory above it.
Layering is unchanged -- `routers` -> `services` -> `models`/`schemas`, one way
only, checked by `tests/fitness/test_layering.py` -- but the outermost cut is now
the context, because that is the cut somebody can own
(`spec/design/conventions.md` § Backend -- where a file goes).
"""

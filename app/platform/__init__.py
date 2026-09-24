"""The supporting technical slice: HTTP with no domain rules in it.

`spec/design/architecture.md` § Contexts and their boundaries has always listed
Platform beside the domain contexts; until the tree was cut by context, it was
the one of the two with no home. It knows about requests, logs and the process;
it does not know what an entry is.

What lives here is the part of Platform that is on the wire -- liveness, the
health shape, the refusal envelope every endpoint shares. What does not is the
infrastructure underneath it: `app/core/` (errors, logging, the request
identifier) and `app/db/` (the engine, the session, the IAM token) are used by
Platform and by every context alike, so putting them under one slice's name would
say something untrue about who they belong to.
"""

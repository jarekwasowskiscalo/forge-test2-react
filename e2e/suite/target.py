"""What a scenario has done to the application so far.

behave handed every step a `context` object that any step could write any
attribute to. Eleven attributes ended up on it, declared nowhere: five were
initialised in `environment.py` and six came into existence whenever the step
that wrote them happened to run first. A scenario that reached a `Then` without
its `When` failed with `AttributeError` rather than with a sentence about the
missing step.

This is the same thing with the fields written down, and the docstring on each
says what it is for.

**The bound on this class growing back: a new field needs a `When` step whose
answer a later `Then` cannot safely read off `api.last`.** That is not a style
rule, it is the one defect this class exists to prevent. A `Then` that reads
`api.last` is asserting about *whatever request happened most recently*, which is
the request it means only as long as no step in between issues one -- and steps
do, because reading a list back is a GET.

Not frozen, because a scenario accumulates. The alternative is routing every
step through pytest-bdd's `target_fixture`, which is the one code path that
still raises a removal warning under pytest 9.
"""

from dataclasses import dataclass

from e2e.harness.client import ApiClient, Row


@dataclass
class Target:
    """The application under test, and what this scenario knows about it."""

    #: The one way to reach it. It remembers its own last answer, so a step
    #: asserting about "the response" asks the object that made the request
    #: rather than reading a field somebody else had to remember to set.
    #:
    #: What it may **not** carry is an assertion that has to survive an
    #: intervening request -- see the class docstring and the field below.
    api: ApiClient

    #: The entry a `Given` created and the rest of the scenario is about.
    #:
    #: Held separately from the last answer for exactly the reason the class
    #: docstring gives: `that entry should have the message ...` runs after a step that
    #: re-read the whole list, so `api.last` by then is the list rather than the
    #: entry. It also carries the entry as it was **before** any edit, which is
    #: what lets a `Then` compare a date against what it used to be -- an
    #: assertion no single response can support.
    entry: Row | None = None

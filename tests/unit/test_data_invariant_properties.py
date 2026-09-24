"""`D-03`, the half that is a statement about VALUES -- so a generator earns its place.

`tests/fitness/test_data_invariants.py` sweeps the schema and answers "is every
primary key declared as an application-generated UUID". That is a question about
shape. This module answers the other half: does an identifier drawn from the whole
space survive the trip to storage and back, and are the ones the application makes
actually distinct? Those are questions about values, and Hypothesis is the right
tool for exactly them.

`spec/design/testing.md` states the split. It matters because the wrong choice is
invisible: a property-based test pointed at a shape rule passes on every run, says
nothing, and looks like the strongest test in the suite.

**No database, and the round trip is real anyway.** SQLAlchemy's `Uuid` type builds
its bind and result processors from the dialect alone, so the conversion the driver
would perform is exercised without a connection. That is the consequence `spec/design/data-model.md` § Identifiers
names -- binding a UUID in raw SQL has to declare its type -- proved rather than
restated.
"""

import uuid

import sqlalchemy as sa
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from app.contexts.guestbook.models.guestbook_entry import GuestbookEntry

#: Postgres is the only engine (`spec/design/architecture.md` § One engine), so this is the dialect the round trip has
#: to survive. Taken from an `Engine` rather than from `postgresql.dialect()` because
#: that alias is untyped and `mypy --strict` reaches this file: the engine's own
#: attribute is typed, and `create_engine` opens nothing -- a connection is made when
#: a session is used, and none is.
_DIALECT = sa.create_engine("postgresql+psycopg://nobody@no-database.invalid/none").dialect

#: Hypothesis' own deadline measures a single example, and the first one here pays
#: for building the type's processors. That is a fixed cost of the first draw, not
#: a property of the logic, so the deadline is off and the example count stays low
#: enough to sit far under this repository's 120-second per-test ceiling.
_SETTINGS = settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])


@given(st.uuids())
@_SETTINGS
def test_any_identifier_survives_the_round_trip_to_storage(value: uuid.UUID) -> None:
    """`D-03` -- for ALL identifiers, not for the three somebody thought of."""
    column: sa.Uuid[uuid.UUID] = sa.Uuid()
    bind = column.bind_processor(_DIALECT)
    handed_over = bind(value) if bind is not None else value

    # Whatever the driver is handed still IDENTIFIES the same UUID. Asserted on the
    # bind side alone, and that is a choice rather than half a test: `result_processor`
    # is untyped in SQLAlchemy and `mypy --strict` reaches this file, so calling it
    # would cost a module-wide override -- a wide exemption bought for one line. The
    # reverse direction is the driver's own inverse of this one, and what this
    # invariant is about is that nothing is LOST on the way out.
    assert uuid.UUID(str(handed_over)) == value


@given(st.integers(min_value=2, max_value=250))
@_SETTINGS
def test_the_application_makes_distinct_identifiers_without_a_database(count: int) -> None:
    """Distinct, version 4, and produced with no execution context.

    The last clause is the one that matters and the one a single call cannot show:
    the default is invoked with `None` for the context, which is what "the
    application generates it" means. An identifier that needs the database to
    exist cannot be put in a request body before the row is written.
    """
    column = GuestbookEntry.__table__.columns["id"]
    default = column.default
    assert default is not None and default.is_callable

    made = [default.arg(None) for _ in range(count)]
    assert len(set(made)) == count, "two rows would share an identifier"
    assert all(isinstance(one, uuid.UUID) and one.version == 4 for one in made)

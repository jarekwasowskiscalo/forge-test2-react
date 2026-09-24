"""Getting a database URL into Alembic's config without it being read as a template.

Alembic keeps its options in a `configparser.ConfigParser`, which treats `%` as
the start of an interpolation. `Config.set_main_option` passes the value straight
through, so **a URL containing a percent sign raises `ValueError: invalid
interpolation syntax` at the moment it is set** -- not later, not on read, and
with a message that says nothing about a database.

That is not a hypothetical. The deployed migration function's `DATABASE_URL`
carries the master password percent-encoded (`urlencode()` in
`infra/terraform/modules/api/main.tf`), and the password is generated from
`-_=+[]{}<>:?` -- every one of which encodes to a `%xx`. So `alembic/env.py`
raised on every AWS environment, before applying a single revision, while working
perfectly against a local password of `app`.

Doubling the sign is the escape ConfigParser documents. It is done here, once, so
the three places that set the option do not each have to remember -- and so this
paragraph has one home rather than three.
"""


def for_alembic_config(url: str) -> str:
    """Escape `url` so `Config.set_main_option` stores it and reads it back unchanged.

    Takes the URL as it really is and returns the form Alembic's config wants.
    `Config.get_main_option` and `get_section` interpolate on the way out, so what
    Alembic hands to SQLAlchemy is the original string again.
    """
    return url.replace("%", "%%")

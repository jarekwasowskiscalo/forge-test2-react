"""Shared SQLAlchemy declarative base.

Framework-agnostic (no fastapi/starlette imports) so this module stays usable
by both the application runtime and Alembic migrations. All domain models
share this single `Base` so its `.metadata` reflects every table.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass

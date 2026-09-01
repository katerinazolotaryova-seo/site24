"""Portable column types shared across ORM models.

`PortableJSONB` stores JSON payloads. On PostgreSQL it uses native `JSONB`
(what production runs on, per the architecture plan); on any other dialect
(SQLite in tests/local dev) it falls back to the generic `JSON` type. This
lets the same models power both a throwaway SQLite test database and the
real Postgres instance without two schemas to maintain.
"""

from __future__ import annotations

from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB
from sqlalchemy.types import TypeDecorator


class PortableJSONB(TypeDecorator):
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_JSONB())
        return dialect.type_descriptor(JSON())

"""Timezone helpers.

SQLite has no native datetime type — SQLAlchemy stores `DateTime(timezone=True)` values as ISO
strings and, on read-back, does not reliably reattach tzinfo, so a value written as UTC-aware can
come back naive. Postgres (the documented migration path, PRD.md §10.3) does not have this
problem, but code that runs correctly against both needs to treat every datetime as UTC and
normalize before comparing.
"""
from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def as_aware_utc(dt: datetime) -> datetime:
    """Attach UTC tzinfo to a naive datetime (assumed to already be UTC); pass a tz-aware one
    through unchanged. Use this on any datetime read back from the database before comparing it
    against `utcnow()`.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

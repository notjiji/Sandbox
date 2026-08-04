"""Database transaction helpers."""

from __future__ import annotations

from contextlib import contextmanager
from collections.abc import Iterator

from sqlalchemy.orm import Session


@contextmanager
def transaction(db: Session) -> Iterator[Session]:
    """Commit on success, rollback on any exception."""
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise

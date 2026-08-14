"""
Dependencies — FastAPI dependency injection.
"""

from __future__ import annotations

from typing import Generator

from sqlalchemy.orm import Session

from database.database import db_manager


def get_db_session() -> Generator[Session, None, None]:
    """Yield a database session for request scope."""
    yield from db_manager.get_session()

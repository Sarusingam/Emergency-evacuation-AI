"""
Database Engine — SQLAlchemy engine, session, and Base.

Supports PostgreSQL (production) and SQLite (demo/dev).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

logger = logging.getLogger(__name__)

DEFAULT_DB_URL = "sqlite:///./data/evacuation.db"


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all ORM models."""

    pass


class DatabaseManager:
    """Manages the SQLAlchemy database engine and sessions."""

    def __init__(
        self,
        db_url: str | None = None,
        echo: bool = False,
    ) -> None:
        self.db_url = db_url or DEFAULT_DB_URL
        self.echo = echo
        self._engine = None
        self._session_factory = None

    def initialize(self) -> None:
        """Create or recreate the database engine and session factory."""

        # If an engine already exists, release its connections first.
        self.dispose()

        # Ensure the SQLite directory exists.
        if self.db_url.startswith("sqlite"):
            db_path = self.db_url.replace("sqlite:///", "", 1)
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        connect_args: dict = {}

        if self.db_url.startswith("sqlite"):
            connect_args["check_same_thread"] = False

        self._engine = create_engine(
            self.db_url,
            echo=self.echo,
            connect_args=connect_args,
        )

        # Enable WAL mode for SQLite.
        if self.db_url.startswith("sqlite"):

            @event.listens_for(self._engine, "connect")
            def set_sqlite_pragma(dbapi_conn, connection_record):
                cursor = dbapi_conn.cursor()
                try:
                    cursor.execute("PRAGMA journal_mode=WAL")
                finally:
                    cursor.close()

        self._session_factory = sessionmaker(
            bind=self._engine,
            autoflush=True,
            autocommit=False,
        )

        logger.info(
            "Database initialized: %s",
            (
                self.db_url.split("@")[-1]
                if "@" in self.db_url
                else self.db_url
            ),
        )

    def create_tables(self) -> None:
        """Create all tables from ORM models."""

        if self._engine is None:
            self.initialize()

        Base.metadata.create_all(self._engine)
        logger.info("Database tables created")

    def get_session(self) -> Generator[Session, None, None]:
        """
        Yield a database session.

        Designed for FastAPI dependency injection and other
        generator-based session consumers.
        """

        if self._session_factory is None:
            self.initialize()

        session = self._session_factory()

        try:
            yield session
            session.commit()

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()

    @property
    def engine(self):
        """Return the active SQLAlchemy engine."""

        if self._engine is None:
            self.initialize()

        return self._engine

    def dispose(self) -> None:
        """
        Dispose the SQLAlchemy engine and release all pooled
        database connections.

        This is especially important for SQLite on Windows,
        where an open connection can prevent the database file
        from being deleted or replaced.
        """

        if self._engine is not None:
            try:
                self._engine.dispose()
                logger.info("Database engine disposed")
            finally:
                self._engine = None
                self._session_factory = None

    def reset(self) -> None:
        """
        Dispose the current engine and recreate the database
        connection using the current db_url.
        """

        self.dispose()
        self.initialize()


# Global database manager instance.
db_manager = DatabaseManager()

"""PostgreSQL database connection and session management.

This module provides SQLAlchemy 2.0 async database operations with connection pooling.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from nyxai.config import get_settings


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class DatabaseManager:
    """Manages async database connections and sessions.

    This class handles the lifecycle of the async SQLAlchemy engine and session factory,
    providing connection pooling and session management.

    Example:
        >>> db_manager = DatabaseManager()
        >>> await db_manager.initialize()
        >>> async with db_manager.get_session() as session:
        ...     result = await session.execute(text("SELECT 1"))
        >>> await db_manager.dispose()
    """

    def __init__(self) -> None:
        """Initialize the database manager without engine."""
        self._engine: AsyncEngine | None = None
        self._session_maker: async_sessionmaker[AsyncSession] | None = None

    @property
    def engine(self) -> AsyncEngine:
        """Get the async engine.

        Raises:
            RuntimeError: If the engine has not been initialized.

        Returns:
            AsyncEngine: The SQLAlchemy async engine.
        """
        if self._engine is None:
            raise RuntimeError("Database engine not initialized. Call initialize() first.")
        return self._engine

    @property
    def session_maker(self) -> async_sessionmaker[AsyncSession]:
        """Get the session maker.

        Raises:
            RuntimeError: If the session maker has not been initialized.

        Returns:
            async_sessionmaker[AsyncSession]: The async session factory.
        """
        if self._session_maker is None:
            raise RuntimeError("Session maker not initialized. Call initialize() first.")
        return self._session_maker

    async def initialize(self) -> None:
        """Initialize the async engine and session maker.

        This method creates the async engine with connection pooling configured
        from application settings.
        """
        settings = get_settings()
        db_settings = settings.db

        self._engine = create_async_engine(
            str(db_settings.url),
            echo=db_settings.echo,
            pool_size=db_settings.pool_size,
            max_overflow=db_settings.max_overflow,
            pool_timeout=db_settings.pool_timeout,
            pool_pre_ping=True,
            future=True,
        )

        self._session_maker = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )

    async def dispose(self) -> None:
        """Dispose of the engine and close all connections."""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_maker = None

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get an async database session as a context manager.

        Yields:
            AsyncSession: An async database session.

        Example:
            >>> async with db_manager.get_session() as session:
            ...     result = await session.execute(text("SELECT 1"))
        """
        if self._session_maker is None:
            raise RuntimeError("Session maker not initialized. Call initialize() first.")

        session = self._session_maker()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def health_check(self) -> bool:
        """Check database connectivity.

        Returns:
            bool: True if the database is reachable, False otherwise.
        """
        try:
            async with self.get_session() as session:
                result = await session.execute(text("SELECT 1"))
                return result.scalar() == 1
        except Exception:
            return False

    async def create_tables(self) -> None:
        """Create all tables defined in the ORM models."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self) -> None:
        """Drop all tables defined in the ORM models."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


# Global database manager instance
_db_manager: DatabaseManager | None = None


async def init_db() -> DatabaseManager:
    """Initialize the global database manager.

    Returns:
        DatabaseManager: The initialized database manager instance.
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
        await _db_manager.initialize()
    return _db_manager


async def close_db() -> None:
    """Close the global database manager."""
    global _db_manager
    if _db_manager is not None:
        await _db_manager.dispose()
        _db_manager = None


def get_db_manager() -> DatabaseManager:
    """Get the global database manager instance.

    Raises:
        RuntimeError: If the database manager has not been initialized.

    Returns:
        DatabaseManager: The global database manager instance.
    """
    if _db_manager is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _db_manager


# Async session factory for direct use
AsyncSessionLocal = async_sessionmaker(
    create_async_engine(
        str(get_settings().db.url),
        echo=get_settings().db.echo,
        pool_size=get_settings().db.pool_size,
        max_overflow=get_settings().db.max_overflow,
        pool_timeout=get_settings().db.pool_timeout,
        pool_pre_ping=True,
        future=True,
    ),
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session for dependency injection.

    This function is designed to be used with FastAPI's dependency injection
    system. It provides a context manager that handles session lifecycle.

    Yields:
        AsyncSession: An async database session.

    Example:
        >>> from fastapi import Depends
        >>> @app.get("/items")
        ... async def get_items(session: AsyncSession = Depends(get_db_session)):
        ...     # Use session here
        ...     pass
    """
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()

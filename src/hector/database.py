"""Database configuration and session management."""

import logging
from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from .config import Settings, get_settings

LOG = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


# Global engine instance
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine(settings: Settings | None = None) -> AsyncEngine:
    """Get or create the database engine."""
    global _engine

    if _engine is None:
        if settings is None:
            settings = get_settings()

        LOG.info(
            "Creating database engine",
            extra={
                "pool_size": settings.db_pool_size,
                "max_overflow": settings.db_max_overflow,
                "echo": settings.db_echo,
            },
        )

        # Determine if we should use NullPool (for testing)
        use_null_pool = "test" in settings.environment.lower()

        # Create async engine with appropriate pool configuration
        engine_args: dict[str, Any] = {
            "echo": settings.db_echo,
            "pool_pre_ping": True,  # Enable connection health checks
        }

        if use_null_pool:
            engine_args["poolclass"] = NullPool
        else:
            engine_args["pool_size"] = settings.db_pool_size
            engine_args["max_overflow"] = settings.db_max_overflow

        _engine = create_async_engine(settings.database_url, **engine_args)

        # Add connection event listeners
        @event.listens_for(_engine.sync_engine, "connect")
        def receive_connect(dbapi_conn: Any, connection_record: Any) -> None:
            """Log when a new connection is established."""
            LOG.debug("Database connection established")

        @event.listens_for(_engine.sync_engine, "close")
        def receive_close(dbapi_conn: Any, connection_record: Any) -> None:
            """Log when a connection is closed."""
            LOG.debug("Database connection closed")

    return _engine


def get_session_factory(settings: Settings | None = None) -> async_sessionmaker[AsyncSession]:
    """Get or create the session factory."""
    global _session_factory

    if _session_factory is None:
        engine = get_engine(settings)
        _session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

    return _session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session.

    Usage in FastAPI endpoints:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database (create tables if they don't exist)."""
    LOG.info("Initializing database tables")
    engine = get_engine()

    async with engine.begin() as conn:
        # Import all models to ensure they're registered
        from . import models  # noqa: F401

        await conn.run_sync(Base.metadata.create_all)

    LOG.info("Database initialization complete")


async def close_db() -> None:
    """Close database connections and dispose of engine."""
    global _engine, _session_factory

    if _engine is not None:
        LOG.info("Closing database connections")
        await _engine.dispose()
        _engine = None
        _session_factory = None


async def check_db_connection() -> bool:
    """
    Check if database connection is working.

    Returns:
        True if connection is healthy, False otherwise
    """
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        LOG.error("Database connection check failed", exc_info=e)
        return False

"""Tests for database connectivity and session management."""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from hector.database import (
    check_db_connection,
    get_db,
    get_engine,
    get_session_factory,
)


@pytest.mark.asyncio
async def test_get_engine_creates_async_engine():
    """Test that get_engine returns an async engine."""
    engine = get_engine()
    assert engine is not None
    assert hasattr(engine, "connect")
    assert engine.__class__.__name__ == "AsyncEngine"


@pytest.mark.asyncio
async def test_get_session_factory_creates_session_maker():
    """Test that get_session_factory returns a session maker."""
    session_factory = get_session_factory()
    assert session_factory is not None
    assert callable(session_factory)


@pytest.mark.asyncio
@pytest.mark.skipif(
    "not config.getoption('--run-db-tests')",
    reason="Database tests require --run-db-tests flag and running PostgreSQL",
)
async def test_session_basic_query():
    """Test that we can execute a basic query through a session."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        result = await session.execute(text("SELECT 1 as num"))
        row = result.fetchone()
        assert row is not None
        assert row[0] == 1


@pytest.mark.asyncio
@pytest.mark.skipif(
    "not config.getoption('--run-db-tests')",
    reason="Database tests require --run-db-tests flag and running PostgreSQL",
)
async def test_get_db_dependency_yields_session():
    """Test that get_db dependency yields a valid session."""
    session_gen = get_db()
    session = await session_gen.__anext__()

    assert isinstance(session, AsyncSession)
    assert session.is_active

    # Clean up
    try:
        await session_gen.__anext__()
    except StopAsyncIteration:
        pass


@pytest.mark.asyncio
@pytest.mark.skipif(
    "not config.getoption('--run-db-tests')",
    reason="Database tests require --run-db-tests flag and running PostgreSQL",
)
async def test_get_db_dependency_commits_on_success():
    """Test that get_db commits when no exception occurs."""
    session_gen = get_db()
    session = await session_gen.__anext__()

    # Perform a simple operation
    await session.execute(text("SELECT 1"))

    # Close the context (should commit)
    try:
        await session_gen.__anext__()
    except StopAsyncIteration:
        pass

    # Session should be closed
    assert not session.is_active


@pytest.mark.asyncio
@pytest.mark.skipif(
    "not config.getoption('--run-db-tests')",
    reason="Database tests require --run-db-tests flag and running PostgreSQL",
)
async def test_check_db_connection_success():
    """Test that check_db_connection returns True when database is available."""
    is_connected = await check_db_connection()
    assert is_connected is True


@pytest.mark.asyncio
async def test_check_db_connection_failure_with_invalid_url(monkeypatch):
    """Test that check_db_connection returns False with invalid database URL."""
    # Mock the Settings to return an invalid database URL
    from hector import config

    original_url = config.Settings().database_url
    monkeypatch.setenv(
        "HECTOR_DATABASE_URL", "postgresql+asyncpg://invalid:invalid@localhost:9999/invalid"
    )
    monkeypatch.setenv("HECTOR_ENVIRONMENT", "test")

    # Clear the engine singleton to force recreation with new settings
    from hector import database

    database._engine = None

    is_connected = await check_db_connection()
    assert is_connected is False

    # Restore
    monkeypatch.setenv("HECTOR_DATABASE_URL", original_url)
    database._engine = None

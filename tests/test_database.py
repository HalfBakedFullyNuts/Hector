"""Tests for database connectivity and session management."""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from hector.database import check_db_connection, get_db


@pytest.mark.asyncio
async def test_session_basic_query(db_engine: AsyncEngine) -> None:
    """Test that we can execute a basic query through a session."""
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        result = await session.execute(text("SELECT 1 as num"))
        row = result.fetchone()
        assert row is not None
        assert row[0] == 1


@pytest.mark.asyncio
async def test_get_db_dependency_yields_session(
    db_engine: AsyncEngine, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that get_db dependency yields a valid session."""
    from hector import database

    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    monkeypatch.setattr(database, "_session_factory", factory)

    session_gen = get_db()
    session = await session_gen.__anext__()

    assert isinstance(session, AsyncSession)
    assert session.is_active


@pytest.mark.asyncio
async def test_get_db_dependency_commits_on_success(
    db_engine: AsyncEngine, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that get_db persists writes when the request succeeds."""
    from sqlalchemy import select

    from hector import database
    from hector.models.user import User

    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    monkeypatch.setattr(database, "_session_factory", factory)

    session_gen = get_db()
    session = await session_gen.__anext__()
    session.add(User(email="commit@example.com", hashed_password="x", role="dog_owner"))
    try:
        await session_gen.__anext__()
    except StopAsyncIteration:
        pass

    async with factory() as verifier:
        found = await verifier.scalar(select(User).where(User.email == "commit@example.com"))
        assert found is not None

    from tests.conftest import _truncate_all

    await _truncate_all(db_engine)


@pytest.mark.asyncio
async def test_check_db_connection_success(
    db_engine: AsyncEngine, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that check_db_connection returns True when database is available."""
    from hector import database

    monkeypatch.setattr(database, "_engine", db_engine)
    is_connected = await check_db_connection()
    assert is_connected is True


@pytest.mark.asyncio
async def test_check_db_connection_failure_with_invalid_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that check_db_connection returns False with unreachable database."""
    from sqlalchemy.ext.asyncio import create_async_engine

    from hector import database

    bad_engine = create_async_engine("postgresql+asyncpg://invalid:invalid@127.0.0.1:9999/invalid")
    try:
        monkeypatch.setattr(database, "_engine", bad_engine)
        is_connected = await check_db_connection()
        assert is_connected is False
    finally:
        await bad_engine.dispose()


@pytest.mark.asyncio
async def test_truncate_isolation_helper(db_engine: AsyncEngine) -> None:
    """Truncating between tests leaves every table empty."""
    from sqlalchemy import select
    from sqlalchemy import text as sqltext
    from tests.conftest import _truncate_all

    from hector.models.user import User

    await _truncate_all(db_engine)
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        session.add(User(email="seq@example.com", hashed_password="x", role="dog_owner"))
        await session.commit()
        assert len((await session.execute(select(User))).scalars().all()) == 1

    await _truncate_all(db_engine)

    async with factory() as session:
        await session.execute(sqltext("SELECT 1"))
        assert len((await session.execute(select(User))).scalars().all()) == 0

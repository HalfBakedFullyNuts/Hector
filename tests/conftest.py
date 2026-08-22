"""Pytest configuration and fixtures for tests."""

import os
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

TEST_DATABASE_URL = "postgresql+asyncpg://hector:hector@127.0.0.1:5433/hector_test"
_TEST_JWT_SECRET = "test-only-signing-key-with-more-than-32-characters"


def pytest_configure(config):
    """Register markers and pin deterministic settings for the test process."""
    config.addinivalue_line(
        "markers",
        "skipif: conditionally skip tests based on command line options",
    )
    os.environ.setdefault("HECTOR_ENVIRONMENT", "test")
    os.environ.setdefault("HECTOR_DATABASE_URL", TEST_DATABASE_URL)
    os.environ.setdefault("HECTOR_JWT_SECRET_KEY", _TEST_JWT_SECRET)


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--run-db-tests",
        action="store_true",
        default=False,
        help="Run tests that require a database connection",
    )


@pytest.fixture(scope="session")
def database_url() -> str:
    """Return the test database URL from env or compose convention."""
    return os.environ.get("HECTOR_DATABASE_URL", TEST_DATABASE_URL)


@pytest.fixture
async def db_engine(database_url: str) -> AsyncGenerator[AsyncEngine, None]:
    """Provide an engine with the full schema created if it does not exist."""
    import hector.models  # noqa: F401 - registers all mappers on Base.metadata
    from hector.database import Base

    engine = create_async_engine(database_url, pool_pre_ping=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


async def _truncate_all(engine: AsyncEngine) -> None:
    """Delete every row so tests stay isolated despite endpoint commits."""
    from hector.database import Base

    names = ", ".join(f'"{t.name}"' for t in reversed(Base.metadata.sorted_tables))
    assert names, "metadata must define at least one table"
    async with engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE TABLE {names} RESTART IDENTITY CASCADE"))


@pytest.fixture
async def db_session(db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Provide an isolated database session (truncates before and after)."""
    await _truncate_all(db_engine)
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
    await _truncate_all(db_engine)


@pytest.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client wired to the isolated database session."""
    from hector.app import create_app
    from hector.config import Settings
    from hector.database import get_db

    settings = Settings()
    app = create_app(settings)

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()

"""Pytest configuration and fixtures for tests."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "skipif: conditionally skip tests based on command line options",
    )


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--run-db-tests",
        action="store_true",
        default=False,
        help="Run tests that require a database connection",
    )


@pytest.fixture
async def db_session():
    """Provide a database session for tests."""
    from hector.database import get_session_factory

    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database session."""
    from hector.app import create_app
    from hector.config import Settings
    from hector.database import get_db

    settings = Settings()
    app = create_app(settings)

    # Override database dependency
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Clean up override
    app.dependency_overrides.clear()

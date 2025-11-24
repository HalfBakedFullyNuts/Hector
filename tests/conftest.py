"""Pytest configuration and fixtures for tests."""

import pytest


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

"""Tests for the donation requests browse endpoint."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from hector.app import create_app
from hector.config import Settings, reset_settings_cache
from hector.models.dog_profile import BloodType
from hector.models.donation_request import RequestStatus, RequestUrgency


@pytest.fixture()
def test_settings() -> Settings:
    """Create test settings."""
    reset_settings_cache()
    return Settings(
        environment="test",
        log_level="INFO",
        port=8100,
        database_url="postgresql+asyncpg://test:test@localhost:5432/test",
    )


@pytest.fixture
def mock_clinic() -> MagicMock:
    """Create a mock clinic object."""
    clinic = MagicMock()
    clinic.id = uuid4()
    clinic.name = "Test Veterinary Clinic"
    clinic.city = "Berlin"
    clinic.phone = "+49 30 12345678"
    return clinic


@pytest.fixture
def mock_donation_request(mock_clinic: MagicMock) -> MagicMock:
    """Create a mock donation request object."""
    request = MagicMock()
    request.id = uuid4()
    request.clinic_id = mock_clinic.id
    request.blood_type_needed = BloodType.DEA_1_1_POSITIVE
    request.volume_ml = 200
    request.urgency = RequestUrgency.URGENT
    request.patient_info = "3-year-old German Shepherd needs emergency surgery"
    request.needed_by_date = datetime.now(UTC) + timedelta(days=2)
    request.status = RequestStatus.OPEN
    request.created_at = datetime.now(UTC)
    request.clinic = mock_clinic
    return request


@pytest.mark.asyncio
async def test_browse_requests_empty(
    test_settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test browsing requests when no requests exist."""
    monkeypatch.setenv("HECTOR_ENVIRONMENT", "test")
    monkeypatch.setenv("HECTOR_DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

    # Create mock session
    mock_session = AsyncMock()

    # Mock the execute calls
    # First call for count
    mock_count_result = MagicMock()
    mock_count_result.scalar.return_value = 0

    # Second call for items
    mock_items_result = MagicMock()
    mock_items_result.scalars.return_value.all.return_value = []

    mock_session.execute = AsyncMock(side_effect=[mock_count_result, mock_items_result])
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()

    async def mock_get_db():
        yield mock_session

    app = create_app(test_settings)
    app.dependency_overrides = {}

    from hector.database import get_db

    app.dependency_overrides[get_db] = mock_get_db

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/requests/browse")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []
    assert data["limit"] == 20
    assert data["offset"] == 0
    assert data["has_more"] is False


@pytest.mark.asyncio
async def test_browse_requests_with_results(
    test_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
    mock_donation_request: MagicMock,
) -> None:
    """Test browsing requests with results."""
    monkeypatch.setenv("HECTOR_ENVIRONMENT", "test")
    monkeypatch.setenv("HECTOR_DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

    mock_session = AsyncMock()

    # Mock count result
    mock_count_result = MagicMock()
    mock_count_result.scalar.return_value = 1

    # Mock items result
    mock_items_result = MagicMock()
    mock_items_result.scalars.return_value.all.return_value = [mock_donation_request]

    # Mock response count result (empty)
    mock_response_count_result = MagicMock()
    mock_response_count_result.all.return_value = []

    mock_session.execute = AsyncMock(
        side_effect=[mock_count_result, mock_items_result, mock_response_count_result]
    )
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()

    async def mock_get_db():
        yield mock_session

    app = create_app(test_settings)

    from hector.database import get_db

    app.dependency_overrides[get_db] = mock_get_db

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/requests/browse")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["urgency"] == "URGENT"
    assert data["items"][0]["blood_type_needed"] == "DEA_1_1_POSITIVE"
    assert data["items"][0]["clinic"]["name"] == "Test Veterinary Clinic"


@pytest.mark.asyncio
async def test_browse_requests_with_filters(
    test_settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test browsing requests with query filters."""
    monkeypatch.setenv("HECTOR_ENVIRONMENT", "test")
    monkeypatch.setenv("HECTOR_DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

    mock_session = AsyncMock()

    mock_count_result = MagicMock()
    mock_count_result.scalar.return_value = 0

    mock_items_result = MagicMock()
    mock_items_result.scalars.return_value.all.return_value = []

    mock_session.execute = AsyncMock(side_effect=[mock_count_result, mock_items_result])
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()

    async def mock_get_db():
        yield mock_session

    app = create_app(test_settings)

    from hector.database import get_db

    app.dependency_overrides[get_db] = mock_get_db

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/requests/browse",
            params={
                "urgency": "CRITICAL",
                "blood_type": "DEA_1_1_NEGATIVE",
                "city": "Berlin",
                "limit": 10,
                "offset": 5,
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 10
    assert data["offset"] == 5


@pytest.mark.asyncio
async def test_browse_requests_pagination(
    test_settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test browsing requests with pagination parameters."""
    monkeypatch.setenv("HECTOR_ENVIRONMENT", "test")
    monkeypatch.setenv("HECTOR_DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

    mock_session = AsyncMock()

    # Total is higher than returned items
    mock_count_result = MagicMock()
    mock_count_result.scalar.return_value = 50

    mock_items_result = MagicMock()
    mock_items_result.scalars.return_value.all.return_value = []

    mock_session.execute = AsyncMock(side_effect=[mock_count_result, mock_items_result])
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()

    async def mock_get_db():
        yield mock_session

    app = create_app(test_settings)

    from hector.database import get_db

    app.dependency_overrides[get_db] = mock_get_db

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/requests/browse", params={"limit": 10, "offset": 0})

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 50
    assert data["has_more"] is True


@pytest.mark.asyncio
async def test_browse_requests_invalid_limit(
    test_settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that invalid limit parameter returns validation error."""
    monkeypatch.setenv("HECTOR_ENVIRONMENT", "test")
    monkeypatch.setenv("HECTOR_DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

    app = create_app(test_settings)
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/requests/browse", params={"limit": 200})

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_browse_requests_invalid_status(
    test_settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that invalid status parameter returns validation error."""
    monkeypatch.setenv("HECTOR_ENVIRONMENT", "test")
    monkeypatch.setenv("HECTOR_DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

    app = create_app(test_settings)
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/requests/browse", params={"status": "INVALID"})

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_get_single_request_not_found(
    test_settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test getting a non-existent request returns 404."""
    monkeypatch.setenv("HECTOR_ENVIRONMENT", "test")
    monkeypatch.setenv("HECTOR_DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

    mock_session = AsyncMock()

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None

    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()

    async def mock_get_db():
        yield mock_session

    app = create_app(test_settings)

    from hector.database import get_db

    app.dependency_overrides[get_db] = mock_get_db

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/requests/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Request not found"


@pytest.mark.asyncio
async def test_get_single_request_success(
    test_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
    mock_donation_request: MagicMock,
) -> None:
    """Test getting a single request successfully."""
    monkeypatch.setenv("HECTOR_ENVIRONMENT", "test")
    monkeypatch.setenv("HECTOR_DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

    mock_session = AsyncMock()

    # Mock request result
    mock_request_result = MagicMock()
    mock_request_result.scalar_one_or_none.return_value = mock_donation_request

    # Mock count result
    mock_count_result = MagicMock()
    mock_count_result.scalar.return_value = 3

    mock_session.execute = AsyncMock(side_effect=[mock_request_result, mock_count_result])
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()

    async def mock_get_db():
        yield mock_session

    app = create_app(test_settings)

    from hector.database import get_db

    app.dependency_overrides[get_db] = mock_get_db

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/requests/{mock_donation_request.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["urgency"] == "URGENT"
    assert data["response_count"] == 3
    assert data["clinic"]["name"] == "Test Veterinary Clinic"

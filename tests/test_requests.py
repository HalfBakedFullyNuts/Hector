"""Tests for the donation requests endpoints."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.exc import IntegrityError

from hector.app import create_app
from hector.config import Settings, reset_settings_cache
from hector.models.dog_profile import BloodType
from hector.models.donation_request import RequestStatus, RequestUrgency
from hector.models.donation_response import ResponseStatus


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


# ============================================================================
# Tests for POST /requests/{request_id}/respond (T-600)
# ============================================================================


@pytest.fixture
def mock_eligible_dog() -> MagicMock:
    """Create a mock eligible dog."""
    dog = MagicMock()
    dog.id = uuid4()
    dog.owner_id = uuid4()
    dog.name = "Max"
    dog.breed = "German Shepherd"
    dog.weight_kg = 30.0
    dog.is_active = True
    dog.last_donation_date = None
    # Mock age_years property to return 3
    type(dog).age_years = property(lambda self: 3)
    return dog


@pytest.fixture
def mock_ineligible_dog_weight() -> MagicMock:
    """Create a mock dog that's too light."""
    dog = MagicMock()
    dog.id = uuid4()
    dog.owner_id = uuid4()
    dog.name = "Tiny"
    dog.breed = "Chihuahua"
    dog.weight_kg = 5.0
    dog.is_active = True
    dog.last_donation_date = None
    type(dog).age_years = property(lambda self: 3)
    return dog


@pytest.fixture
def mock_donation_response() -> MagicMock:
    """Create a mock donation response."""
    response = MagicMock()
    response.id = uuid4()
    response.request_id = uuid4()
    response.dog_id = uuid4()
    response.owner_id = uuid4()
    response.status = ResponseStatus.ACCEPTED
    response.response_message = "Happy to help!"
    response.created_at = datetime.now(UTC)
    response.updated_at = datetime.now(UTC)
    return response


@pytest.mark.asyncio
async def test_respond_to_request_success(
    test_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
    mock_donation_request: MagicMock,
    mock_eligible_dog: MagicMock,
) -> None:
    """Test successfully responding to a donation request."""
    monkeypatch.setenv("HECTOR_ENVIRONMENT", "test")
    monkeypatch.setenv("HECTOR_DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

    mock_session = AsyncMock()

    # Mock request query result
    mock_request_result = MagicMock()
    mock_request_result.scalar_one_or_none.return_value = mock_donation_request

    # Mock dog query result
    mock_dog_result = MagicMock()
    mock_dog_result.scalar_one_or_none.return_value = mock_eligible_dog

    mock_session.execute = AsyncMock(side_effect=[mock_request_result, mock_dog_result])

    # Track added objects and simulate db.flush() populating auto-fields
    added_objects: list = []

    def mock_add(obj):
        added_objects.append(obj)

    async def mock_flush():
        # Simulate database populating auto-generated fields
        for obj in added_objects:
            if not hasattr(obj, "id") or obj.id is None:
                obj.id = uuid4()
            if not hasattr(obj, "created_at") or obj.created_at is None:
                obj.created_at = datetime.now(UTC)
            if not hasattr(obj, "updated_at") or obj.updated_at is None:
                obj.updated_at = datetime.now(UTC)

    mock_session.add = mock_add
    mock_session.flush = mock_flush
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
        response = await client.post(
            f"/requests/{mock_donation_request.id}/respond",
            json={
                "dog_id": str(mock_eligible_dog.id),
                "status": "ACCEPTED",
                "response_message": "Happy to help!",
            },
            headers={"X-User-Id": str(mock_eligible_dog.owner_id)},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "ACCEPTED"
    assert data["response_message"] == "Happy to help!"


@pytest.mark.asyncio
async def test_respond_to_request_not_found(
    test_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test responding to a non-existent request."""
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
        response = await client.post(
            f"/requests/{uuid4()}/respond",
            json={"dog_id": str(uuid4()), "status": "ACCEPTED"},
            headers={"X-User-Id": str(uuid4())},
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Donation request not found"


@pytest.mark.asyncio
async def test_respond_to_closed_request(
    test_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
    mock_donation_request: MagicMock,
) -> None:
    """Test responding to a non-OPEN request."""
    monkeypatch.setenv("HECTOR_ENVIRONMENT", "test")
    monkeypatch.setenv("HECTOR_DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

    # Set request status to FULFILLED
    mock_donation_request.status = RequestStatus.FULFILLED

    mock_session = AsyncMock()

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_donation_request

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
        response = await client.post(
            f"/requests/{mock_donation_request.id}/respond",
            json={"dog_id": str(uuid4()), "status": "ACCEPTED"},
            headers={"X-User-Id": str(uuid4())},
        )

    assert response.status_code == 400
    assert "FULFILLED" in response.json()["detail"]


@pytest.mark.asyncio
async def test_respond_with_non_existent_dog(
    test_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
    mock_donation_request: MagicMock,
) -> None:
    """Test responding with a dog that doesn't exist."""
    monkeypatch.setenv("HECTOR_ENVIRONMENT", "test")
    monkeypatch.setenv("HECTOR_DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

    mock_session = AsyncMock()

    mock_request_result = MagicMock()
    mock_request_result.scalar_one_or_none.return_value = mock_donation_request

    mock_dog_result = MagicMock()
    mock_dog_result.scalar_one_or_none.return_value = None

    mock_session.execute = AsyncMock(side_effect=[mock_request_result, mock_dog_result])
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
        response = await client.post(
            f"/requests/{mock_donation_request.id}/respond",
            json={"dog_id": str(uuid4()), "status": "ACCEPTED"},
            headers={"X-User-Id": str(uuid4())},
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Dog profile not found"


@pytest.mark.asyncio
async def test_respond_with_someone_elses_dog(
    test_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
    mock_donation_request: MagicMock,
    mock_eligible_dog: MagicMock,
) -> None:
    """Test responding with a dog that belongs to another user."""
    monkeypatch.setenv("HECTOR_ENVIRONMENT", "test")
    monkeypatch.setenv("HECTOR_DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

    mock_session = AsyncMock()

    mock_request_result = MagicMock()
    mock_request_result.scalar_one_or_none.return_value = mock_donation_request

    mock_dog_result = MagicMock()
    mock_dog_result.scalar_one_or_none.return_value = mock_eligible_dog

    mock_session.execute = AsyncMock(side_effect=[mock_request_result, mock_dog_result])
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()

    async def mock_get_db():
        yield mock_session

    app = create_app(test_settings)

    from hector.database import get_db

    app.dependency_overrides[get_db] = mock_get_db

    transport = ASGITransport(app=app)

    # Use a different user ID than the dog's owner
    different_user_id = uuid4()

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            f"/requests/{mock_donation_request.id}/respond",
            json={"dog_id": str(mock_eligible_dog.id), "status": "ACCEPTED"},
            headers={"X-User-Id": str(different_user_id)},
        )

    assert response.status_code == 403
    assert "your own dogs" in response.json()["detail"]


@pytest.mark.asyncio
async def test_respond_with_ineligible_dog(
    test_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
    mock_donation_request: MagicMock,
    mock_ineligible_dog_weight: MagicMock,
) -> None:
    """Test responding with an ineligible dog (too light)."""
    monkeypatch.setenv("HECTOR_ENVIRONMENT", "test")
    monkeypatch.setenv("HECTOR_DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

    mock_session = AsyncMock()

    mock_request_result = MagicMock()
    mock_request_result.scalar_one_or_none.return_value = mock_donation_request

    mock_dog_result = MagicMock()
    mock_dog_result.scalar_one_or_none.return_value = mock_ineligible_dog_weight

    mock_session.execute = AsyncMock(side_effect=[mock_request_result, mock_dog_result])
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
        response = await client.post(
            f"/requests/{mock_donation_request.id}/respond",
            json={"dog_id": str(mock_ineligible_dog_weight.id), "status": "ACCEPTED"},
            headers={"X-User-Id": str(mock_ineligible_dog_weight.owner_id)},
        )

    assert response.status_code == 400
    data = response.json()["detail"]
    assert data["message"] == "Dog is not eligible for donation"
    assert any("weight" in reason.lower() for reason in data["reasons"])


@pytest.mark.asyncio
async def test_respond_decline_skips_eligibility_check(
    test_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
    mock_donation_request: MagicMock,
    mock_ineligible_dog_weight: MagicMock,
) -> None:
    """Test that DECLINED responses skip eligibility check."""
    monkeypatch.setenv("HECTOR_ENVIRONMENT", "test")
    monkeypatch.setenv("HECTOR_DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

    mock_session = AsyncMock()

    mock_request_result = MagicMock()
    mock_request_result.scalar_one_or_none.return_value = mock_donation_request

    mock_dog_result = MagicMock()
    mock_dog_result.scalar_one_or_none.return_value = mock_ineligible_dog_weight

    mock_session.execute = AsyncMock(side_effect=[mock_request_result, mock_dog_result])

    # Track added objects and simulate db.flush() populating auto-fields
    added_objects: list = []

    def mock_add(obj):
        added_objects.append(obj)

    async def mock_flush():
        for obj in added_objects:
            if not hasattr(obj, "id") or obj.id is None:
                obj.id = uuid4()
            if not hasattr(obj, "created_at") or obj.created_at is None:
                obj.created_at = datetime.now(UTC)
            if not hasattr(obj, "updated_at") or obj.updated_at is None:
                obj.updated_at = datetime.now(UTC)

    mock_session.add = mock_add
    mock_session.flush = mock_flush
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
        response = await client.post(
            f"/requests/{mock_donation_request.id}/respond",
            json={
                "dog_id": str(mock_ineligible_dog_weight.id),
                "status": "DECLINED",
                "response_message": "Sorry, my dog is too small",
            },
            headers={"X-User-Id": str(mock_ineligible_dog_weight.owner_id)},
        )

    # DECLINED should succeed even with ineligible dog
    assert response.status_code == 201
    assert response.json()["status"] == "DECLINED"


@pytest.mark.asyncio
async def test_respond_duplicate_response_conflict(
    test_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
    mock_donation_request: MagicMock,
    mock_eligible_dog: MagicMock,
) -> None:
    """Test responding twice with the same dog returns 409 Conflict."""
    monkeypatch.setenv("HECTOR_ENVIRONMENT", "test")
    monkeypatch.setenv("HECTOR_DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

    mock_session = AsyncMock()

    mock_request_result = MagicMock()
    mock_request_result.scalar_one_or_none.return_value = mock_donation_request

    mock_dog_result = MagicMock()
    mock_dog_result.scalar_one_or_none.return_value = mock_eligible_dog

    mock_session.execute = AsyncMock(side_effect=[mock_request_result, mock_dog_result])
    mock_session.add = MagicMock()
    # Simulate IntegrityError on flush (duplicate unique constraint)
    mock_session.flush = AsyncMock(side_effect=IntegrityError("", "", Exception()))
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
        response = await client.post(
            f"/requests/{mock_donation_request.id}/respond",
            json={"dog_id": str(mock_eligible_dog.id), "status": "ACCEPTED"},
            headers={"X-User-Id": str(mock_eligible_dog.owner_id)},
        )

    assert response.status_code == 409
    assert "already responded" in response.json()["detail"]


@pytest.mark.asyncio
async def test_respond_missing_user_header(
    test_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test responding without X-User-Id header returns 422."""
    monkeypatch.setenv("HECTOR_ENVIRONMENT", "test")
    monkeypatch.setenv("HECTOR_DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

    app = create_app(test_settings)
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            f"/requests/{uuid4()}/respond",
            json={"dog_id": str(uuid4()), "status": "ACCEPTED"},
            # No X-User-Id header
        )

    assert response.status_code == 422  # Validation error for missing header

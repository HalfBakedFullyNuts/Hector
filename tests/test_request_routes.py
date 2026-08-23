"""Tests for /requests route ordering and compatible-request authorization."""

from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from hector.auth.password import hash_password
from hector.models.clinic import Clinic
from hector.models.dog_profile import DogProfile
from hector.models.user import User, UserRole


async def _seed_owner(db_session: AsyncSession, email: str) -> User:
    """Create and persist a dog owner."""
    owner = User(
        email=email, hashed_password=hash_password("SecurePass123"), role=UserRole.DOG_OWNER
    )
    db_session.add(owner)
    await db_session.commit()
    return owner


async def _login(client: AsyncClient, email: str) -> str:
    """Return a bearer access token for the given user."""
    response = await client.post("/auth/login", json={"email": email, "password": "SecurePass123"})
    assert response.status_code == 200
    token: str = response.json()["access_token"]
    return token


async def test_my_responses_not_shadowed_by_dynamic_route(async_client: AsyncClient) -> None:
    """GET /requests/my-responses must not 422 against /{request_id}."""
    response = await async_client.get("/requests/my-responses")
    assert response.status_code in (200, 401), (
        "route shadowing produces 422; got {response.status_code}"
    )


async def test_compatible_requires_ownership(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    """Owners may only list compatible requests for their own dogs."""
    stranger = await _seed_owner(db_session, "stranger@example.com")
    dog = DogProfile(
        owner_id=stranger.id,
        name="ForeignDog",
        breed="Labrador",
        date_of_birth=date.today() - timedelta(days=365 * 3),
        weight_kg=30.0,
        sex="MALE",
        blood_type=None,
        is_active=True,
    )
    db_session.add(dog)
    await db_session.commit()

    victim = await _seed_owner(db_session, "victim@example.com")
    victim_token = await _login(async_client, victim.email)

    response = await async_client.get(
        f"/requests/compatible?dog_id={dog.id}",
        headers={"Authorization": f"Bearer {victim_token}"},
    )
    assert response.status_code == 403


async def test_compatible_without_token_unauthorized(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    """The compatible listing requires authentication."""
    owner = await _seed_owner(db_session, "compat-owner@example.com")
    dog = DogProfile(
        owner_id=owner.id,
        name="OwnedDog",
        breed="Beagle",
        date_of_birth=date.today() - timedelta(days=365 * 3),
        weight_kg=28.0,
        sex="FEMALE",
        is_active=True,
    )
    db_session.add(dog)
    await db_session.commit()

    response = await async_client.get(f"/requests/compatible?dog_id={dog.id}")
    assert response.status_code == 401


async def test_compatible_for_own_dog_lists_open_requests(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    """Happy path: owner sees compatible OPEN requests for their dog."""
    staff = User(
        email="compat-staff@clinic.com",
        hashed_password=hash_password("SecurePass123"),
        role=UserRole.CLINIC_STAFF,
    )
    clinic = Clinic(
        name="Compat Clinic",
        address="1 Way",
        city="Berlin",
        postal_code="10115",
        phone="+49 30 0000000",
        email="compat@clinic.de",
        is_approved=True,
    )
    owner = await _seed_owner(db_session, "compat-me@example.com")
    db_session.add_all([staff, clinic])
    await db_session.commit()

    from hector.models.donation_request import BloodDonationRequest

    request = BloodDonationRequest(
        clinic_id=clinic.id,
        created_by_user_id=staff.id,
        volume_ml=300,
        urgency="URGENT",
        status="OPEN",
        needed_by_date=datetime.now(UTC) + timedelta(days=5),
    )
    db_session.add(request)
    await db_session.commit()

    dog = DogProfile(
        owner_id=owner.id,
        name="MyDonor",
        breed="Labrador",
        date_of_birth=date.today() - timedelta(days=365 * 4),
        weight_kg=31.0,
        sex="MALE",
        is_active=True,
    )
    db_session.add(dog)
    await db_session.commit()

    token = await _login(async_client, owner.email)
    response = await async_client.get(
        f"/requests/compatible?dog_id={dog.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1

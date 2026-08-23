"""Tests for donation request detail response counts (T-502)."""

from datetime import UTC, date, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from hector.auth.password import hash_password
from hector.models.clinic import Clinic
from hector.models.dog_profile import DogProfile
from hector.models.donation_request import BloodDonationRequest
from hector.models.donation_response import DonationResponse
from hector.models.user import User, UserRole


async def test_get_request_reports_real_response_count(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    """GET /requests/{id} returns the actual number of responses."""
    staff = User(
        email="count-staff@clinic.com",
        hashed_password=hash_password("SecurePass123"),
        role=UserRole.CLINIC_STAFF,
    )
    clinic = Clinic(
        name="Counting Clinic",
        address="9 Count St",
        city="Berlin",
        postal_code="10115",
        phone="+49 30 5555555",
        email="count@clinic.de",
        is_approved=True,
    )
    db_session.add_all([staff, clinic])
    await db_session.commit()

    request = BloodDonationRequest(
        clinic_id=clinic.id,
        created_by_user_id=staff.id,
        volume_ml=250,
        urgency="ROUTINE",
        status="OPEN",
        needed_by_date=datetime.now(UTC) + timedelta(days=6),
    )
    db_session.add(request)
    await db_session.commit()

    owner1 = await _seed_owner_with_dog(db_session, "c1@example.com")
    owner2 = await _seed_owner_with_dog(db_session, "c2@example.com")

    db_session.add_all(
        [
            DonationResponse(
                request_id=request.id,
                dog_id=owner1[1],
                owner_id=owner1[0],
                status="ACCEPTED",
            ),
            DonationResponse(
                request_id=request.id,
                dog_id=owner2[1],
                owner_id=owner2[0],
                status="DECLINED",
            ),
        ]
    )
    await db_session.commit()

    response = await async_client.get(f"/requests/{request.id}")
    assert response.status_code == 200
    assert response.json()["response_count"] == 2


async def _seed_owner_with_dog(db_session: AsyncSession, email: str) -> tuple:
    """Create one owner plus one dog; returns (owner_id, dog_id)."""
    owner = User(
        email=email, hashed_password=hash_password("SecurePass123"), role=UserRole.DOG_OWNER
    )
    db_session.add(owner)
    await db_session.commit()

    dog = DogProfile(
        owner_id=owner.id,
        name=f"Dog-{email}",
        date_of_birth=date.today() - timedelta(days=365 * 3),
        weight_kg=30.0,
        sex="FEMALE",
        is_active=True,
    )
    db_session.add(dog)
    await db_session.commit()
    return owner.id, dog.id

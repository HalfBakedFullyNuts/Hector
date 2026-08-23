"""Tests for compatibility scoring on /requests/compatible (T-604)."""

from datetime import UTC, date, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from hector.auth.password import hash_password
from hector.models.clinic import Clinic
from hector.models.dog_profile import DogProfile
from hector.models.donation_request import BloodDonationRequest
from hector.models.user import User, UserRole
from hector.services.compatibility import compatibility_score


def test_universal_donor_scores_highest() -> None:
    """DEA 1.1 negative dogs are universal donors: 100."""
    from hector.models.dog_profile import BloodType

    assert compatibility_score(BloodType.DEA_1_1_NEGATIVE, BloodType.DEA_1_1_POSITIVE) == 100
    assert compatibility_score(BloodType.DEA_1_1_NEGATIVE, BloodType.DEA_4_POSITIVE) == 100
    assert compatibility_score(BloodType.DEA_1_1_NEGATIVE, None) == 100


def test_exact_match_scores_75() -> None:
    """Same blood type on both sides: 75."""
    from hector.models.dog_profile import BloodType

    assert compatibility_score(BloodType.DEA_1_1_POSITIVE, BloodType.DEA_1_1_POSITIVE) == 75
    assert compatibility_score(BloodType.DEA_4_NEGATIVE, BloodType.DEA_4_NEGATIVE) == 75


def test_unspecified_request_type_scores_50() -> None:
    """Compatible only because the clinic accepts any type: 50."""
    from hector.models.dog_profile import BloodType

    assert compatibility_score(BloodType.DEA_1_1_POSITIVE, None) == 50
    assert compatibility_score(BloodType.DEA_5_POSITIVE, None) == 50


async def test_compatible_endpoint_includes_scores(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    """The endpoint response carries a compatibility_score field."""
    staff = User(
        email="score-staff@clinic.com",
        hashed_password=hash_password("SecurePass123"),
        role=UserRole.CLINIC_STAFF,
    )
    clinic = Clinic(
        name="Score Clinic",
        address="10 Score St",
        city="Berlin",
        postal_code="10115",
        phone="+49 30 6666666",
        email="score@clinic.de",
        is_approved=True,
    )
    db_session.add_all([staff, clinic])
    await db_session.commit()

    needed_by = datetime.now(UTC) + timedelta(days=3)
    db_session.add_all(
        [
            BloodDonationRequest(
                clinic_id=clinic.id,
                created_by_user_id=staff.id,
                blood_type_needed="DEA_1_1_POSITIVE",
                volume_ml=300,
                urgency="URGENT",
                status="OPEN",
                needed_by_date=needed_by,
            ),
            BloodDonationRequest(
                clinic_id=clinic.id,
                created_by_user_id=staff.id,
                blood_type_needed=None,
                volume_ml=300,
                urgency="ROUTINE",
                status="OPEN",
                needed_by_date=needed_by,
            ),
        ]
    )

    owner = User(
        email="score-owner@example.com",
        hashed_password=hash_password("SecurePass123"),
        role=UserRole.DOG_OWNER,
    )
    db_session.add(owner)
    await db_session.commit()

    dog = DogProfile(
        owner_id=owner.id,
        name="ScoreDog",
        date_of_birth=date.today() - timedelta(days=365 * 3),
        weight_kg=30.0,
        sex="MALE",
        blood_type="DEA_1_1_NEGATIVE",
        is_active=True,
    )
    db_session.add(dog)
    await db_session.commit()

    login = await async_client.post(
        "/auth/login", json={"email": owner.email, "password": "SecurePass123"}
    )
    token = login.json()["access_token"]

    response = await async_client.get(
        f"/requests/compatible?dog_id={dog.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 2

    scores = {item["blood_type_needed"]: item["compatibility_score"] for item in items}
    assert scores["DEA_1_1_POSITIVE"] == 100  # universal donor
    assert scores[None] == 100

"""Tests for match and response notifications (T-1002, T-1003)."""

from datetime import UTC, date, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hector.auth.password import hash_password
from hector.models.clinic import Clinic
from hector.models.dog_profile import DogProfile
from hector.models.donation_request import BloodDonationRequest
from hector.models.email_log import EmailLog
from hector.models.user import User, UserRole
from hector.services.notifications import MAX_EMAILS_PER_USER_PER_DAY


async def _seed_world(db_session: AsyncSession, tag: str) -> tuple[User, Clinic]:
    """Seed an approved clinic plus its linked staff user."""
    from hector.models.clinic_staff import clinic_staff_association

    staff = User(
        email=f"{tag}-staff@clinic.com",
        hashed_password=hash_password("SecurePass123"),
        role=UserRole.CLINIC_STAFF,
    )
    clinic = Clinic(
        name=f"{tag} Clinic",
        address="1 St",
        city="Berlin",
        postal_code="10115",
        phone="+49 30 0000000",
        email=f"{tag}@clinic.com",
        is_approved=True,
    )
    db_session.add_all([staff, clinic])
    await db_session.commit()
    await db_session.execute(
        clinic_staff_association.insert().values(user_id=staff.id, clinic_id=clinic.id)
    )
    await db_session.commit()
    return staff, clinic


def _dog(owner_id, name: str, blood_type: str | None) -> DogProfile:
    """Build an eligible donor dog."""
    return DogProfile(
        owner_id=owner_id,
        name=name,
        date_of_birth=date.today() - timedelta(days=365 * 3),
        weight_kg=30.0,
        sex="MALE",
        blood_type=blood_type,
        is_active=True,
        is_available_for_donation=True,
    )


async def test_compatible_owner_gets_match_email(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    """Creating a request notifies owners of eligible compatible dogs."""
    owner = User(
        email="match-owner@example.com",
        hashed_password=hash_password("SecurePass123"),
        role=UserRole.DOG_OWNER,
        city="Berlin",
    )
    db_session.add(owner)
    await db_session.commit()
    db_session.add(_dog(owner.id, "MatchDog", "DEA_1_1_NEGATIVE"))
    await db_session.commit()

    staff, clinic = await _seed_world(db_session, "notif")

    create = await async_client.post(
        "/requests",
        json={
            "volume_ml": 300,
            "urgency": "CRITICAL",
            "needed_by_date": (datetime.now(UTC) + timedelta(days=3)).isoformat(),
            "blood_type_needed": "DEA_1_1_POSITIVE",
        },
        headers={
            "Authorization": f"Bearer {(await async_client.post('/auth/login', json={'email': staff.email, 'password': 'SecurePass123'})).json()['access_token']}"
        },
    )
    assert create.status_code == 201, create.text

    emails = (
        (await db_session.execute(select(EmailLog).where(EmailLog.recipient == owner.email)))
        .scalars()
        .all()
    )
    assert len(emails) == 1
    assert "MatchDog" in emails[0].body_text
    assert emails[0].template == "match_notification"


async def test_ineligible_or_far_owners_not_emailed(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    """Unavailable dogs, wrong city, and unknown blood type stay silent."""
    far_owner = User(
        email="far@example.com",
        hashed_password=hash_password("SecurePass123"),
        role=UserRole.DOG_OWNER,
        city="Munich",
    )
    unavailable_owner = User(
        email="busy@example.com",
        hashed_password=hash_password("SecurePass123"),
        role=UserRole.DOG_OWNER,
        city="Berlin",
    )
    unknown_owner = User(
        email="unknownbt@example.com",
        hashed_password=hash_password("SecurePass123"),
        role=UserRole.DOG_OWNER,
        city="Berlin",
    )
    db_session.add_all([far_owner, unavailable_owner, unknown_owner])
    await db_session.commit()

    far_dog = _dog(far_owner.id, "FarDog", "DEA_1_1_POSITIVE")
    busy_dog = _dog(unavailable_owner.id, "BusyDog", "DEA_1_1_POSITIVE")
    busy_dog.is_available_for_donation = False
    mystery_dog = _dog(unknown_owner.id, "MysteryDog", None)
    db_session.add_all([far_dog, busy_dog, mystery_dog])
    await db_session.commit()

    staff, _ = await _seed_world(db_session, "silent")
    token = (
        await async_client.post(
            "/auth/login", json={"email": staff.email, "password": "SecurePass123"}
        )
    ).json()["access_token"]

    create = await async_client.post(
        "/requests",
        json={
            "volume_ml": 300,
            "urgency": "URGENT",
            "needed_by_date": (datetime.now(UTC) + timedelta(days=2)).isoformat(),
            "blood_type_needed": "DEA_1_1_POSITIVE",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create.status_code == 201

    for email_addr in ("far@example.com", "busy@example.com", "unknownbt@example.com"):
        rows = (
            (await db_session.execute(select(EmailLog).where(EmailLog.recipient == email_addr)))
            .scalars()
            .all()
        )
        assert rows == [], f"{email_addr} must not be notified"


async def test_daily_email_cap_enforced(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    """No recipient receives more than MAX_EMAILS_PER_USER_PER_DAY per day."""
    owner = User(
        email="capped@example.com",
        hashed_password=hash_password("SecurePass123"),
        role=UserRole.DOG_OWNER,
    )
    db_session.add(owner)
    await db_session.commit()

    from datetime import datetime as dt

    for i in range(MAX_EMAILS_PER_USER_PER_DAY):
        db_session.add(
            EmailLog(
                recipient=owner.email,
                subject=f"s{i}",
                body_text="b",
                status="logged",
                created_at=dt.now(UTC),
                updated_at=dt.now(UTC),
            )
        )
    await db_session.commit()

    db_session.add(_dog(owner.id, "CappedDog", "DEA_1_1_NEGATIVE"))
    staff, _ = await _seed_world(db_session, "cap")
    await db_session.commit()

    token = (
        await async_client.post(
            "/auth/login", json={"email": staff.email, "password": "SecurePass123"}
        )
    ).json()["access_token"]

    create = await async_client.post(
        "/requests",
        json={
            "volume_ml": 200,
            "urgency": "ROUTINE",
            "needed_by_date": (datetime.now(UTC) + timedelta(days=5)).isoformat(),
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create.status_code == 201

    total = len(
        (await db_session.execute(select(EmailLog).where(EmailLog.recipient == owner.email)))
        .scalars()
        .all()
    )
    assert total == MAX_EMAILS_PER_USER_PER_DAY


async def test_accepted_response_notifies_clinic(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    """ACCEPTED responses trigger exactly one email to the clinic; DECLINED none."""
    owner = User(
        email="resp-owner@example.com",
        hashed_password=hash_password("SecurePass123"),
        role=UserRole.DOG_OWNER,
    )
    db_session.add(owner)
    await db_session.commit()
    dog = _dog(owner.id, "RespDog", "DEA_1_1_NEGATIVE")
    db_session.add(dog)

    staff, clinic = await _seed_world(db_session, "respnotify")
    request = BloodDonationRequest(
        clinic_id=clinic.id,
        created_by_user_id=staff.id,
        volume_ml=250,
        urgency="URGENT",
        status="OPEN",
        needed_by_date=datetime.now(UTC) + timedelta(days=4),
    )
    db_session.add(request)
    await db_session.commit()

    owner_token = (
        await async_client.post(
            "/auth/login", json={"email": owner.email, "password": "SecurePass123"}
        )
    ).json()["access_token"]

    accepted = await async_client.post(
        f"/requests/{request.id}/respond",
        json={"dog_id": str(dog.id), "status": "ACCEPTED"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert accepted.status_code == 201

    clinic_emails = (
        (await db_session.execute(select(EmailLog).where(EmailLog.recipient == clinic.email)))
        .scalars()
        .all()
    )
    assert len(clinic_emails) == 1
    assert clinic_emails[0].template == "response_received"

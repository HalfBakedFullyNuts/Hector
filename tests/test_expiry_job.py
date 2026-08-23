"""Tests for the request expiry automation (T-1005)."""

from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hector.auth.password import hash_password
from hector.jobs.expire_requests import expire_overdue_requests
from hector.models.clinic import Clinic
from hector.models.donation_request import BloodDonationRequest
from hector.models.email_log import EmailLog
from hector.models.user import User, UserRole


async def _seed_clinic(db_session: AsyncSession, tag: str) -> Clinic:
    """Seed staff+clinic pair linked together."""
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
    return clinic


def _request(clinic: Clinic, needed_by: datetime, status: str = "OPEN"):
    """Build a donation request row."""
    return BloodDonationRequest(
        clinic_id=clinic.id,
        created_by_user_id=None,
        volume_ml=300,
        urgency="ROUTINE",
        status=status,
        needed_by_date=needed_by,
    )


async def test_sweep_expires_only_overdue_open(db_session: AsyncSession) -> None:
    """Overdue OPEN rows flip to EXPIRED; others untouched."""
    clinic = await _seed_clinic(db_session, "exp")
    overdue = _request(clinic, datetime.now(UTC) - timedelta(days=2))
    fresh = _request(clinic, datetime.now(UTC) + timedelta(days=2))
    cancelled = _request(clinic, datetime.now(UTC) - timedelta(days=9), status="CANCELLED")
    db_session.add_all([overdue, fresh, cancelled])
    await db_session.commit()

    flipped = await expire_overdue_requests(db_session)

    assert flipped == 1
    await db_session.refresh(overdue)
    await db_session.refresh(fresh)
    assert overdue.status == "EXPIRED"
    assert fresh.status == "OPEN"
    assert cancelled.status == "CANCELLED"


async def test_sweep_notifies_affected_clinics(db_session: AsyncSession) -> None:
    """Each affected clinic receives one expiration email."""
    clinic = await _seed_clinic(db_session, "expmail")
    db_session.add(_request(clinic, datetime.now(UTC) - timedelta(days=1)))
    await db_session.commit()

    await expire_overdue_requests(db_session)

    emails = (
        await db_session.execute(select(EmailLog).where(EmailLog.recipient == clinic.email))
    ).scalars().all()
    assert len(emails) == 1
    assert "expired" in emails[0].subject.lower()


async def test_sweep_is_idempotent(db_session: AsyncSession) -> None:
    """Running twice in a row does not double-flip or double-notify."""
    clinic = await _seed_clinic(db_session, "idem")
    db_session.add(_request(clinic, datetime.now(UTC) - timedelta(hours=3)))
    await db_session.commit()

    first = await expire_overdue_requests(db_session)
    second = await expire_overdue_requests(db_session)

    assert first == 1
    assert second == 0


async def test_endpoint_listing_hides_expired(async_client: AsyncClient) -> None:
    """Expired requests disappear from default OPEN listings."""
    response = await async_client.get("/requests?status=OPEN")
    assert response.status_code == 200

    expired = await async_client.get("/requests?status=EXPIRED")
    assert expired.status_code == 200

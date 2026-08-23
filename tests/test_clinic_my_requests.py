"""Tests for the spec-mandated /clinics/my-requests endpoint (T-505)."""

from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from hector.auth.password import hash_password
from hector.models.clinic import Clinic
from hector.models.clinic_staff import clinic_staff_association
from hector.models.donation_request import BloodDonationRequest
from hector.models.user import User, UserRole


async def test_my_requests_via_clinics_path(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    """Staff retrieve their clinic's requests via GET /clinics/my-requests."""
    staff = User(
        email="path-staff@clinic.com",
        hashed_password=hash_password("SecurePass123"),
        role=UserRole.CLINIC_STAFF,
    )
    clinic = Clinic(
        name="Path Clinic",
        address="11 Path St",
        city="Berlin",
        postal_code="10115",
        phone="+49 30 8888888",
        email="path@clinic.de",
        is_approved=True,
    )
    db_session.add_all([staff, clinic])
    await db_session.commit()
    await db_session.execute(
        clinic_staff_association.insert().values(user_id=staff.id, clinic_id=clinic.id)
    )
    await db_session.commit()

    db_session.add_all(
        [
            BloodDonationRequest(
                clinic_id=clinic.id,
                created_by_user_id=staff.id,
                volume_ml=200,
                urgency="ROUTINE",
                status="OPEN",
                needed_by_date=datetime.now(UTC) + timedelta(days=2),
            ),
            BloodDonationRequest(
                clinic_id=clinic.id,
                created_by_user_id=staff.id,
                volume_ml=250,
                urgency="URGENT",
                status="CANCELLED",
                needed_by_date=datetime.now(UTC) + timedelta(days=3),
            ),
        ]
    )
    await db_session.commit()

    login = await async_client.post(
        "/auth/login", json={"email": "path-staff@clinic.com", "password": "SecurePass123"}
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    all_reqs = await async_client.get("/clinics/my-requests", headers=headers)
    assert all_reqs.status_code == 200, all_reqs.text
    assert len(all_reqs.json()) == 2

    filtered = await async_client.get(
        "/clinics/my-requests", params={"status": "CANCELLED"}, headers=headers
    )
    assert filtered.status_code == 200
    body = filtered.json()
    assert len(body) == 1
    assert body[0]["status"] == "CANCELLED"


async def test_my_requests_requires_staff_role(async_client: AsyncClient) -> None:
    """Dog owners get 403 on the staff-only listing."""
    register = await async_client.post(
        "/auth/register",
        json={"email": "path-owner@example.com", "password": "SecurePass123", "role": "dog_owner"},
    )
    assert register.status_code == 201
    login = await async_client.post(
        "/auth/login", json={"email": "path-owner@example.com", "password": "SecurePass123"}
    )

    response = await async_client.get(
        "/clinics/my-requests",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )
    assert response.status_code == 403

"""Tests for soft-delete and availability semantics (T-304/T-305)."""

from datetime import UTC, date, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hector.auth.password import hash_password
from hector.models.clinic import Clinic
from hector.models.dog_profile import DogProfile
from hector.models.user import User, UserRole


async def _register_and_login(client: AsyncClient, email: str, role: str) -> str:
    """Register a user via the API and return an access token."""
    register = await client.post(
        "/auth/register", json={"email": email, "password": "SecurePass123", "role": role}
    )
    assert register.status_code == 201, register.text
    login = await client.post("/auth/login", json={"email": email, "password": "SecurePass123"})
    assert login.status_code == 200
    token: str = login.json()["access_token"]
    return token


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _dog_payload(name: str) -> dict:
    """Minimal valid dog creation payload."""
    return {
        "name": name,
        "breed": "Labrador",
        "date_of_birth": str(date.today() - timedelta(days=365 * 3)),
        "weight_kg": 30.0,
        "sex": "MALE",
    }


async def test_delete_dog_soft_deletes(db_session: AsyncSession, async_client: AsyncClient) -> None:
    """DELETE keeps the row but hides the profile (T-304)."""
    token = await _register_and_login(async_client, "softdel@example.com", "dog_owner")
    create = await async_client.post("/dogs", json=_dog_payload("Rexy"), headers=_auth(token))
    assert create.status_code == 201
    dog_id = create.json()["id"]

    delete = await async_client.delete(f"/dogs/{dog_id}", headers=_auth(token))
    assert delete.status_code == 204

    row = await db_session.scalar(select(DogProfile).where(DogProfile.id == dog_id))
    assert row is not None, "soft delete must keep the row"
    assert row.is_active is False

    get_after = await async_client.get(f"/dogs/{dog_id}", headers=_auth(token))
    assert get_after.status_code == 404

    listing = await async_client.get("/dogs", headers=_auth(token))
    assert listing.status_code == 200
    assert all(d["id"] != dog_id for d in listing.json())


async def test_availability_toggle_independent_of_soft_delete(
    db_session: AsyncSession, async_client: AsyncClient
) -> None:
    """Availability flag changes without touching is_active (T-305)."""
    token = await _register_and_login(async_client, "toggle@example.com", "dog_owner")
    create = await async_client.post("/dogs", json=_dog_payload("Toggly"), headers=_auth(token))
    dog_id = create.json()["id"]

    patch = await async_client.patch(
        f"/dogs/{dog_id}/availability",
        json={"is_available": False},
        headers=_auth(token),
    )
    assert patch.status_code == 200
    data = patch.json()
    assert data["is_available_for_donation"] is False
    assert data["is_active"] is True

    row = await db_session.scalar(select(DogProfile).where(DogProfile.id == dog_id))
    assert row is not None
    assert row.is_eligible_for_donation is False


async def test_unavailable_dog_cannot_respond_to_request(
    db_session: AsyncSession, async_client: AsyncClient
) -> None:
    """An unavailable-but-active dog cannot ACCEPT a request."""
    staff_token_future: str | None = None

    staff_register = await async_client.post(
        "/auth/register",
        json={
            "email": "avail-staff@clinic.com",
            "password": "SecurePass123",
            "role": "clinic_staff",
        },
    )
    assert staff_register.status_code == 201

    owner_token = await _register_and_login(async_client, "avail-owner@example.com", "dog_owner")
    dog_create = await async_client.post(
        "/dogs", json=_dog_payload("SleepyDog"), headers=_auth(owner_token)
    )
    dog_id = dog_create.json()["id"]

    await async_client.patch(
        f"/dogs/{dog_id}/availability",
        json={"is_available": False},
        headers=_auth(owner_token),
    )

    # Clinic + request seeded directly for focus on response rules.
    staff = User(
        email="seed-staff@clinic.com",
        hashed_password=hash_password("SecurePass123"),
        role=UserRole.CLINIC_STAFF,
    )
    clinic = Clinic(
        name="Seed Clinic",
        address="2 Way",
        city="Berlin",
        postal_code="10115",
        phone="+49 30 1111111",
        email="seed@clinic.de",
        is_approved=True,
    )
    db_session.add_all([staff, clinic])
    await db_session.commit()

    from hector.models.donation_request import BloodDonationRequest

    request = BloodDonationRequest(
        clinic_id=clinic.id,
        created_by_user_id=staff.id,
        volume_ml=300,
        urgency="URGENT",
        status="OPEN",
        needed_by_date=datetime.now(UTC) + timedelta(days=4),
    )
    db_session.add(request)
    await db_session.commit()

    respond = await async_client.post(
        f"/requests/{request.id}/respond",
        json={"dog_id": dog_id, "status": "ACCEPTED"},
        headers=_auth(owner_token),
    )
    assert respond.status_code == 403
    del staff_token_future


async def test_rejected_clinic_soft_deleted(
    db_session: AsyncSession, async_client: AsyncClient
) -> None:
    """Admin reject keeps the clinic row but hides it from public listings."""
    admin_row = User(
        email="reject-admin@example.com",
        hashed_password=hash_password("SecurePass123"),
        role=UserRole.ADMIN,
        is_verified=True,
    )
    db_session.add(admin_row)
    await db_session.commit()

    clinic = Clinic(
        name="RejectMe Clinic",
        address="3 Way",
        city="Hamburg",
        postal_code="20095",
        phone="+49 40 2222222",
        email="reject@clinic.de",
        is_approved=False,
    )
    db_session.add(clinic)
    await db_session.commit()
    clinic_id = clinic.id

    admin_login = await async_client.post(
        "/auth/login",
        json={"email": "reject-admin@example.com", "password": "SecurePass123"},
    )
    admin_token = admin_login.json()["access_token"]

    reject = await async_client.post(
        f"/admin/clinics/{clinic_id}/reject",
        json={"rejection_reason": "not a real clinic"},
        headers=_auth(admin_token),
    )
    assert reject.status_code == 204

    row = await db_session.scalar(select(Clinic).where(Clinic.id == clinic_id))
    assert row is not None, "rejected clinic must be soft-deleted"
    assert row.is_active is False

    public_list = await async_client.get("/clinics")
    assert public_list.status_code == 200
    assert all(c["name"] != "RejectMe Clinic" for c in public_list.json())

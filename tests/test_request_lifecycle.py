"""End-to-end request lifecycle coverage for Phases 4-7 endpoints."""

from datetime import UTC, date, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hector.auth.password import hash_password
from hector.models.dog_profile import DogProfile
from hector.models.user import User, UserRole


def _future(days: int = 5) -> str:
    """ISO datetime N days out."""
    return (datetime.now(UTC) + timedelta(days=days)).isoformat()


async def _register(client: AsyncClient, email: str, role: str) -> str:
    """Register and login; returns bearer token."""
    reg = await client.post(
        "/auth/register", json={"email": email, "password": "SecurePass123", "role": role}
    )
    assert reg.status_code == 201, reg.text
    login = await client.post(
        "/auth/login", json={"email": email, "password": "SecurePass123"}
    )
    assert login.status_code == 200
    return str(login.json()["access_token"])


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _seed_admin(db_session: AsyncSession, email: str) -> User:
    """Insert an admin directly (admins cannot self-register)."""
    admin = User(
        email=email,
        hashed_password=hash_password("SecurePass123"),
        role=UserRole.ADMIN,
        is_verified=True,
    )
    db_session.add(admin)
    await db_session.commit()
    return admin


async def _approved_clinic_token(client: AsyncClient, db_session: AsyncSession, tag: str) -> tuple[str, dict]:
    """Register staff, create clinic, approve it via admin API."""
    staff_token = await _register(client, f"{tag}-staff@clinic.com", "clinic_staff")
    create = await client.post(
        "/clinics",
        json={
            "name": f"Clinic {tag}",
            "address": "1 Main St",
            "city": "Berlin",
            "postal_code": "10115",
            "phone": "+49 30 1234567",
            "email": f"{tag}@clinic.com",
        },
        headers=_auth(staff_token),
    )
    assert create.status_code == 201, create.text
    clinic_id = create.json()["id"]

    admin = await _seed_admin(db_session, f"{tag}-admin@example.com")
    admin_login = await client.post(
        "/auth/login", json={"email": admin.email, "password": "SecurePass123"}
    )
    approve = await client.post(
        f"/admin/clinics/{clinic_id}/approve",
        json={"approval_notes": "verified"},
        headers=_auth(str(admin_login.json()["access_token"])),
    )
    assert approve.status_code == 200, approve.text
    assert approve.json()["is_approved"] is True
    return staff_token, create.json()


def _request_payload(**overrides: object) -> dict:
    """Valid donation-request payload."""
    base: dict = {
        "volume_ml": 300,
        "urgency": "URGENT",
        "needed_by_date": _future(4),
    }
    base.update(overrides)  # type: ignore[arg-type]
    return base


async def test_full_request_lifecycle(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    """Create → respond → list responses → complete → eligibility lockout."""
    staff_token, _clinic = await _approved_clinic_token(async_client, db_session, "life")

    # --- create request ---
    created = await async_client.post(
        "/requests",
        json=_request_payload(blood_type_needed="DEA_1_1_POSITIVE"),
        headers=_auth(staff_token),
    )
    assert created.status_code == 201, created.text
    request_id = created.json()["id"]
    assert created.json()["status"] == "OPEN"

    # --- owner + dog ---
    owner_token = await _register(async_client, "life-owner@example.com", "dog_owner")
    dog_create = await async_client.post(
        "/dogs",
        json={
            "name": "LifeDog",
            "breed": "Labrador",
            "date_of_birth": str(date.today() - timedelta(days=365 * 4)),
            "weight_kg": 32.0,
            "sex": "MALE",
            "blood_type": "DEA_1_1_POSITIVE",
        },
        headers=_auth(owner_token),
    )
    assert dog_create.status_code == 201, dog_create.text
    dog_id = dog_create.json()["id"]

    # --- respond ---
    respond = await async_client.post(
        f"/requests/{request_id}/respond",
        json={"dog_id": dog_id, "status": "ACCEPTED", "response_message": "ready!"},
        headers=_auth(owner_token),
    )
    assert respond.status_code == 201, respond.text
    response_id = respond.json()["id"]

    dup = await async_client.post(
        f"/requests/{request_id}/respond",
        json={"dog_id": dog_id, "status": "DECLINED"},
        headers=_auth(owner_token),
    )
    assert dup.status_code == 409

    foreign_dog = await async_client.post(
        "/dogs",
        json={
            "name": "Foreigner",
            "date_of_birth": str(date.today() - timedelta(days=365 * 3)),
            "weight_kg": 30.0,
            "sex": "FEMALE",
        },
        headers=_auth(await _register(async_client, "life-other@example.com", "dog_owner")),
    )

    steal = await async_client.post(
        f"/requests/{request_id}/respond",
        json={"dog_id": foreign_dog.json()["id"], "status": "ACCEPTED"},
        headers=_auth(owner_token),
    )
    assert steal.status_code == 403

    # --- clinic lists responses ---
    listed = await async_client.get(
        f"/requests/{request_id}/responses", headers=_auth(staff_token)
    )
    assert listed.status_code == 200
    entries = listed.json()
    assert len(entries) == 1
    assert entries[0]["owner_email"] == "life-owner@example.com"
    assert entries[0]["dog"]["name"] == "LifeDog"

    # --- complete ---
    complete = await async_client.post(
        f"/requests/responses/{response_id}/complete", headers=_auth(staff_token)
    )
    assert complete.status_code == 200
    assert complete.json()["status"] == "COMPLETED"

    row = await db_session.scalar(select(DogProfile).where(DogProfile.id == dog_id))
    assert row is not None
    assert row.last_donation_date is not None

    # --- second request now blocked by 8-week rule ---
    second = await async_client.post(
        "/requests",
        json=_request_payload(),
        headers=_auth(staff_token),
    )
    assert second.status_code == 201
    second_id = second.json()["id"]

    locked_out = await async_client.post(
        f"/requests/{second_id}/respond",
        json={"dog_id": dog_id, "status": "ACCEPTED"},
        headers=_auth(owner_token),
    )
    assert locked_out.status_code == 403
    assert "weeks" in locked_out.json()["detail"]


async def test_request_validation_and_role_rules(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    """Creation validates volume/date and requires an approved clinic staff."""
    owner_token = await _register(async_client, "val-owner@example.com", "dog_owner")
    forbidden = await async_client.post(
        "/requests", json=_request_payload(), headers=_auth(owner_token)
    )
    assert forbidden.status_code == 403

    vol_staff, _ = await _approved_clinic_token(async_client, db_session, "vol")
    bad_volume = await async_client.post(
        "/requests", json=_request_payload(volume_ml=999), headers=_auth(vol_staff)
    )
    assert bad_volume.status_code == 422

    past_staff, _ = await _approved_clinic_token(async_client, db_session, "past")
    past = await async_client.post(
        "/requests",
        json=_request_payload(needed_by_date=_future(-1)),
        headers=_auth(past_staff),
    )
    assert past.status_code == 422


async def test_request_update_and_cancel_rules(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    """Only owning staff can update/cancel; terminal states are protected."""
    staff_token, _ = await _approved_clinic_token(async_client, db_session, "upd")
    other_staff_token, _ = await _approved_clinic_token(async_client, db_session, "oth")

    created = await async_client.post(
        "/requests", json=_request_payload(), headers=_auth(staff_token)
    )
    request_id = created.json()["id"]

    outsider = await async_client.put(
        f"/requests/{request_id}",
        json={"urgency": "ROUTINE"},
        headers=_auth(other_staff_token),
    )
    assert outsider.status_code == 403

    updated = await async_client.put(
        f"/requests/{request_id}",
        json={"urgency": "ROUTINE", "patient_info": "stable now"},
        headers=_auth(staff_token),
    )
    assert updated.status_code == 200
    assert updated.json()["urgency"] == "ROUTINE"

    cancelled = await async_client.post(
        f"/requests/{request_id}/cancel", headers=_auth(staff_token)
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "CANCELLED"

    touch_cancelled = await async_client.put(
        f"/requests/{request_id}",
        json={"urgency": "CRITICAL"},
        headers=_auth(staff_token),
    )
    assert touch_cancelled.status_code == 422


async def test_admin_user_management_flow(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    """Admin lists users with counts and toggles active state."""
    admin = await _seed_admin(db_session, "flow-admin@example.com")
    target_email = "flow-target@example.com"
    await _register(async_client, target_email, "dog_owner")

    admin_login = await async_client.post(
        "/auth/login", json={"email": admin.email, "password": "SecurePass123"}
    )
    headers = _auth(str(admin_login.json()["access_token"]))

    users = await async_client.get("/admin/users?email=flow-target", headers=headers)
    assert users.status_code == 200
    matches = [u for u in users.json() if u["email"] == target_email]
    assert len(matches) == 1
    target_id = matches[0]["id"]

    toggled = await async_client.post(
        f"/admin/users/{target_id}/toggle-active",
        json={"reason": "temp ban"},
        headers=headers,
    )
    assert toggled.status_code == 200
    assert toggled.json()["is_active"] is False

    disabled_login = await async_client.post(
        "/auth/login", json={"email": target_email, "password": "SecurePass123"}
    )
    assert disabled_login.status_code == 403

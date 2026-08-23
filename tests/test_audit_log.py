"""Tests for the audit trail (T-701/T-702/T-704)."""

from datetime import UTC, datetime

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hector.auth.password import hash_password
from hector.models.audit_log import AuditLog
from hector.models.clinic import Clinic
from hector.models.user import User, UserRole


async def test_toggle_active_writes_audit_log(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    """Toggling a user writes one audit entry with actor and target."""
    admin = User(
        email="log-admin@example.com",
        hashed_password=hash_password("SecurePass123"),
        role=UserRole.ADMIN,
        is_verified=True,
    )
    target = User(
        email="log-target@example.com",
        hashed_password=hash_password("SecurePass123"),
        role=UserRole.DOG_OWNER,
    )
    db_session.add_all([admin, target])
    await db_session.commit()

    login = await async_client.post(
        "/auth/login", json={"email": "log-admin@example.com", "password": "SecurePass123"}
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = await async_client.post(
        f"/admin/users/{target.id}/toggle-active",
        json={"reason": "suspicious activity"},
        headers=headers,
    )
    assert response.status_code == 200

    entries = (
        (
            await db_session.execute(
                select(AuditLog).where(AuditLog.action == "user.toggle_active")
            )
        )
        .scalars()
        .all()
    )
    assert len(entries) == 1
    entry = entries[0]
    assert str(entry.actor_user_id) == str(admin.id)
    assert entry.target_id == str(target.id)
    assert entry.details is not None and "suspicious" in str(entry.details)


async def test_reject_clinic_writes_audit_log(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    """Rejecting a clinic records the rejection reason."""
    admin = User(
        email="clinic-audit-admin@example.com",
        hashed_password=hash_password("SecurePass123"),
        role=UserRole.ADMIN,
        is_verified=True,
    )
    clinic = Clinic(
        name="Audit Clinic",
        address="5 Audit Way",
        city="Berlin",
        postal_code="10115",
        phone="+49 30 7777777",
        email="audit@clinic.de",
        is_approved=False,
    )
    db_session.add_all([admin, clinic])
    await db_session.commit()

    login = await async_client.post(
        "/auth/login",
        json={"email": "clinic-audit-admin@example.com", "password": "SecurePass123"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    reject = await async_client.post(
        f"/admin/clinics/{clinic.id}/reject",
        json={"rejection_reason": "documents missing"},
        headers=headers,
    )
    assert reject.status_code == 204

    entry = (
        await db_session.execute(select(AuditLog).where(AuditLog.action == "clinic.reject"))
    ).scalar_one()
    assert entry.target_id == str(clinic.id)
    assert entry.details is not None and "documents missing" in str(entry.details)


async def test_audit_log_endpoint_lists_newest_first(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    """GET /admin/audit-log returns entries, newest first, admin only."""
    admin = User(
        email="list-audit-admin@example.com",
        hashed_password=hash_password("SecurePass123"),
        role=UserRole.ADMIN,
        is_verified=True,
    )
    target = User(
        email="double-target@example.com",
        hashed_password=hash_password("SecurePass123"),
        role=UserRole.DOG_OWNER,
    )
    db_session.add_all([admin, target])
    await db_session.commit()

    login = await async_client.post(
        "/auth/login",
        json={"email": "list-audit-admin@example.com", "password": "SecurePass123"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    for reason in ("first", "second"):
        toggle = await async_client.post(
            f"/admin/users/{target.id}/toggle-active",
            json={"reason": reason},
            headers=headers,
        )
        assert toggle.status_code == 200

    listing = await async_client.get("/admin/audit-log", headers=headers)
    assert listing.status_code == 200
    entries = listing.json()
    assert len(entries) >= 2
    timestamps = [e["created_at"] for e in entries]
    assert timestamps == sorted(timestamps, reverse=True)

    # Non-admin users are rejected
    owner_register = await async_client.post(
        "/auth/register",
        json={"email": "not-admin@example.com", "password": "SecurePass123", "role": "dog_owner"},
    )
    assert owner_register.status_code == 201
    owner_login = await async_client.post(
        "/auth/login", json={"email": "not-admin@example.com", "password": "SecurePass123"}
    )
    denied = await async_client.get(
        "/admin/audit-log",
        headers={"Authorization": f"Bearer {owner_login.json()['access_token']}"},
    )
    assert denied.status_code == 403

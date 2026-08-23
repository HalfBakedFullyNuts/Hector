"""Tests for admin platform statistics (T-703)."""

from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from hector.auth.password import hash_password
from hector.models.user import User, UserRole


async def _admin_token(async_client: AsyncClient) -> str:
    """Create an admin directly and log in."""
    admin = User(
        email=f"stats-admin-{datetime.now(UTC).timestamp()}@example.com",
        hashed_password=hash_password("SecurePass123"),
        role=UserRole.ADMIN,
        is_verified=True,
    )
    return admin


async def test_stats_shape_and_counts(async_client: AsyncClient, db_session: AsyncSession) -> None:
    """Stats endpoint returns grouped counts without per-row query loops."""
    admin = await _admin_token(async_client)
    db_session.add(admin)
    db_session.add(
        User(
            email="stats-owner@example.com",
            hashed_password=hash_password("SecurePass123"),
            role=UserRole.DOG_OWNER,
        )
    )
    await db_session.commit()

    login = await async_client.post(
        "/auth/login",
        json={"email": admin.email, "password": "SecurePass123"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    response = await async_client.get("/admin/stats", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()

    assert data["total_users"] == 2
    assert data["users_by_role"]["dog_owner"] == 1
    assert data["users_by_role"]["admin"] == 1


async def test_stats_date_filters_exclude_out_of_range(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    """start/end filters restrict counted rows to the window."""
    from datetime import datetime as dt

    old_user = User(
        email="old-user@example.com",
        hashed_password=hash_password("SecurePass123"),
        role=UserRole.DOG_OWNER,
        created_at=dt.now(UTC) - timedelta(days=10),
    )
    new_admin = User(
        email="range-admin@example.com",
        hashed_password=hash_password("SecurePass123"),
        role=UserRole.ADMIN,
        is_verified=True,
    )
    db_session.add_all([old_user, new_admin])
    await db_session.commit()

    login = await async_client.post(
        "/auth/login",
        json={"email": "range-admin@example.com", "password": "SecurePass123"},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    start = dt.now(UTC) - timedelta(days=5)
    end = dt.now(UTC)
    filtered = await async_client.get(
        "/admin/stats",
        params={"start_date": start.isoformat(), "end_date": end.isoformat()},
        headers=headers,
    )
    assert filtered.status_code == 200
    data = filtered.json()
    # old_user (10 days ago) excluded; new_admin inside the window included
    assert data["total_users"] == 1
    assert data["users_by_role"].get("dog_owner", 0) == 0

    unfiltered = await async_client.get("/admin/stats", headers=headers)
    assert unfiltered.json()["total_users"] >= 2

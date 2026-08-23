"""Tests for geo-proximity request listing (T-1004)."""

from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from hector.auth.password import hash_password
from hector.models.clinic import Clinic
from hector.models.donation_request import BloodDonationRequest
from hector.models.user import User, UserRole

BERLIN = (52.5200, 13.4050)
HAMBURG = (53.5511, 9.9937)


async def _seed_request(
    db_session: AsyncSession,
    tag: str,
    lat: float | None,
    lng: float | None,
) -> None:
    """Seed one approved clinic (with coords) plus an OPEN request."""
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
        latitude=lat,
        longitude=lng,
    )
    db_session.add_all([staff, clinic])
    await db_session.commit()

    db_session.add(
        BloodDonationRequest(
            clinic_id=clinic.id,
            created_by_user_id=staff.id,
            volume_ml=300,
            urgency="ROUTINE",
            status="OPEN",
            needed_by_date=datetime.now(UTC) + timedelta(days=3),
        )
    )
    await db_session.commit()


async def test_requests_sorted_and_filtered_by_distance(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    """With lat/lng params, results carry distance and respect max_distance_km."""
    await _seed_request(db_session, "near", BERLIN[0], BERLIN[1])
    await _seed_request(db_session, "far", HAMBURG[0], HAMBURG[1])

    response = await async_client.get(
        "/requests",
        params={"lat": BERLIN[0], "lng": BERLIN[1], "max_distance_km": 100},
    )
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert "near" in items[0]["clinic"]["name"]
    assert items[0]["distance_km"] < 100


async def test_distance_sort_ascending(async_client: AsyncClient, db_session: AsyncSession) -> None:
    """Results sort nearest-first when no max distance given."""
    await _seed_request(db_session, "sortfar", HAMBURG[0], HAMBURG[1])
    await _seed_request(db_session, "sortnear", BERLIN[0], BERLIN[1])

    response = await async_client.get("/requests", params={"lat": BERLIN[0], "lng": BERLIN[1]})
    assert response.status_code == 200
    names = [item["clinic"]["name"] for item in response.json()]
    assert names.index("sortnear Clinic") < names.index("sortfar Clinic")


async def test_without_coords_listing_unaffected(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    """Default listing ignores distance entirely."""
    await _seed_request(db_session, "plain", BERLIN[0], BERLIN[1])

    response = await async_client.get("/requests")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["distance_km"] is None


async def test_update_my_location(async_client: AsyncClient) -> None:
    """PATCH /auth/me stores optional coordinates."""
    register = await async_client.post(
        "/auth/register",
        json={"email": "geo-owner@example.com", "password": "SecurePass123", "role": "dog_owner"},
    )
    assert register.status_code == 201
    token = (
        await async_client.post(
            "/auth/login", json={"email": "geo-owner@example.com", "password": "SecurePass123"}
        )
    ).json()["access_token"]

    patched = await async_client.patch(
        "/auth/me",
        json={"latitude": BERLIN[0], "longitude": BERLIN[1]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert patched.status_code == 200
    data = patched.json()
    assert abs(data["latitude"] - BERLIN[0]) < 1e-6
    assert abs(data["longitude"] - BERLIN[1]) < 1e-6

    invalid = await async_client.patch(
        "/auth/me",
        json={"latitude": 999.0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert invalid.status_code == 422

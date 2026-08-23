"""Tests for dog listing pagination (T-301)."""

from datetime import date, timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


def _dog_payload(name: str) -> dict:
    """Minimal valid dog creation payload."""
    return {
        "name": name,
        "breed": "Mixed",
        "date_of_birth": str(date.today() - timedelta(days=365 * 3)),
        "weight_kg": 30.0,
        "sex": "MALE",
    }


async def test_list_dogs_paginates_and_sorts_newest_first(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    """GET /dogs supports limit/offset and sorts by created_at desc."""
    register = await async_client.post(
        "/auth/register",
        json={"email": "pager@example.com", "password": "SecurePass123", "role": "dog_owner"},
    )
    assert register.status_code == 201

    login = await async_client.post(
        "/auth/login", json={"email": "pager@example.com", "password": "SecurePass123"}
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    created_ids: list[str] = []
    for i in range(5):
        create = await async_client.post("/dogs", json=_dog_payload(f"Dog{i}"), headers=headers)
        assert create.status_code == 201, create.text
        created_ids.append(create.json()["id"])

    page1 = await async_client.get("/dogs?limit=2", headers=headers)
    assert page1.status_code == 200
    page1_ids = [d["id"] for d in page1.json()]
    assert len(page1_ids) == 2
    assert page1_ids == created_ids[-1:-3:-1], "newest two dogs first"

    page2 = await async_client.get("/dogs?limit=2&offset=2", headers=headers)
    assert page2.status_code == 200
    page2_ids = [d["id"] for d in page2.json()]
    assert page2_ids == created_ids[-3:-5:-1]

    all_dogs = await async_client.get("/dogs", headers=headers)
    assert all_dogs.status_code == 200
    assert len(all_dogs.json()) == 5


async def test_list_dogs_rejects_oversized_limit(async_client: AsyncClient) -> None:
    """limit is capped at 100 to protect the database."""
    register = await async_client.post(
        "/auth/register",
        json={"email": "biglimit@example.com", "password": "SecurePass123", "role": "dog_owner"},
    )
    assert register.status_code == 201
    login = await async_client.post(
        "/auth/login", json={"email": "biglimit@example.com", "password": "SecurePass123"}
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = await async_client.get("/dogs?limit=500", headers=headers)
    assert response.status_code == 422

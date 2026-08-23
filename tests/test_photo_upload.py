"""Tests for dog photo upload (T-1001)."""

import io

from httpx import AsyncClient
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession


def _png_bytes(size: tuple[int, int] = (800, 600), color: str = "green") -> bytes:
    """Render a small PNG in memory."""
    img = Image.new("RGB", size, color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _file(data: bytes, filename: str = "dog.png", mime: str = "image/png") -> dict:
    """Build a multipart file entry."""
    return {"file": (filename, io.BytesIO(data), mime)}


async def test_upload_sets_photo_url(async_client: AsyncClient, db_session: AsyncSession) -> None:
    """Uploading a valid JPEG stores files and returns the photo URL."""
    register = await async_client.post(
        "/auth/register",
        json={"email": "photo@example.com", "password": "SecurePass123", "role": "dog_owner"},
    )
    assert register.status_code == 201
    token = (
        await async_client.post(
            "/auth/login", json={"email": "photo@example.com", "password": "SecurePass123"}
        )
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    from datetime import date, timedelta

    dog = await async_client.post(
        "/dogs",
        json={
            "name": "PhotoDog",
            "date_of_birth": str(date.today() - timedelta(days=365 * 3)),
            "weight_kg": 30.0,
            "sex": "MALE",
        },
        headers=headers,
    )
    dog_id = dog.json()["id"]

    response = await async_client.post(
        f"/dogs/{dog_id}/photo",
        files=_file(_png_bytes()),
        headers=headers,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["photo_url"] is not None and "/media/dogs/" in body["photo_url"]


async def test_upload_rejects_wrong_type(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    """Non-JPEG/PNG payloads are rejected with 422."""
    register = await async_client.post(
        "/auth/register",
        json={"email": "photo2@example.com", "password": "SecurePass123", "role": "dog_owner"},
    )
    assert register.status_code == 201
    token = (
        await async_client.post(
            "/auth/login", json={"email": "photo2@example.com", "password": "SecurePass123"}
        )
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    from datetime import date, timedelta

    dog = await async_client.post(
        "/dogs",
        json={
            "name": "TypeDog",
            "date_of_birth": str(date.today() - timedelta(days=365 * 3)),
            "weight_kg": 30.0,
            "sex": "FEMALE",
        },
        headers=headers,
    )
    dog_id = dog.json()["id"]

    bad = await async_client.post(
        f"/dogs/{dog_id}/photo",
        files=_file(b"GIF89a-not-an-image", "cat.gif", "image/gif"),
        headers=headers,
    )
    assert bad.status_code == 422


async def test_upload_requires_ownership(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    """Another user's dog cannot be decorated with a photo."""
    for n in ("photoA", "photoB"):
        await async_client.post(
            "/auth/register",
            json={"email": f"{n}@example.com", "password": "SecurePass123", "role": "dog_owner"},
        )
    token_a = (
        await async_client.post(
            "/auth/login", json={"email": "photoA@example.com", "password": "SecurePass123"}
        )
    ).json()["access_token"]
    token_b = (
        await async_client.post(
            "/auth/login", json={"email": "photoB@example.com", "password": "SecurePass123"}
        )
    ).json()["access_token"]

    from datetime import date, timedelta

    dog = await async_client.post(
        "/dogs",
        json={
            "name": "OwnedDog",
            "date_of_birth": str(date.today() - timedelta(days=365 * 3)),
            "weight_kg": 30.0,
            "sex": "MALE",
        },
        headers={"Authorization": f"Bearer {token_a}"},
    )
    dog_id = dog.json()["id"]

    intruder = await async_client.post(
        f"/dogs/{dog_id}/photo",
        files=_file(_png_bytes()),
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert intruder.status_code == 404  # scoped query hides other owners' dogs

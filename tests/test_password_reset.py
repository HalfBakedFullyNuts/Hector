"""Tests for the password reset flow (T-1008)."""

import hashlib
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hector.auth.password import hash_password, verify_password
from hector.models.email_log import EmailLog
from hector.models.password_reset_token import PasswordResetToken
from hector.models.user import User, UserRole


async def _seed_user(db_session: AsyncSession) -> User:
    """Create a standard active user."""
    user = User(
        email="reset-me@example.com",
        hashed_password=hash_password("OldPass123"),
        role=UserRole.DOG_OWNER,
    )
    db_session.add(user)
    await db_session.commit()
    return user


async def test_forgot_password_always_200(async_client: AsyncClient) -> None:
    """Unknown and known emails both return 200 (no enumeration)."""
    known = await async_client.post("/auth/forgot-password", json={"email": "ghost@example.com"})
    unknown = await async_client.post(
        "/auth/forgot-password", json={"email": "another-ghost@example.com"}
    )

    assert known.status_code == 200
    assert unknown.status_code == 200
    assert known.json()["message"] == unknown.json()["message"]


async def test_forgot_password_creates_token_and_email(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    """A hashed single-use token plus notification email are produced."""
    await _seed_user(db_session)
    # Reuse the module-level client for consistency with other suites
    response = await async_client.post(
        "/auth/forgot-password", json={"email": "reset-me@example.com"}
    )
    assert response.status_code == 200

    tokens = (await db_session.execute(select(PasswordResetToken))).scalars().all()
    assert len(tokens) == 1
    assert tokens[0].used_at is None
    assert tokens[0].expires_at > datetime.now(UTC)

    emails = (
        (
            await db_session.execute(
                select(EmailLog).where(EmailLog.recipient == "reset-me@example.com")
            )
        )
        .scalars()
        .all()
    )
    assert len(emails) == 1

    raw_token = response.json().get("dev_token")
    assert raw_token, "log-mode exposes the token for testing convenience"

    assert hashlib.sha256(raw_token.encode()).hexdigest() == tokens[0].token_hash


async def test_reset_password_single_use(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    """Token works exactly once; new password authenticates."""
    user = await _seed_user(db_session)
    forgot = await async_client.post(
        "/auth/forgot-password", json={"email": "reset-me@example.com"}
    )
    raw_token = forgot.json()["dev_token"]

    reset = await async_client.post(
        "/auth/reset-password",
        json={"token": raw_token, "new_password": "NewStr0ngPass"},
    )
    assert reset.status_code == 200

    login = await async_client.post(
        "/auth/login",
        json={"email": "reset-me@example.com", "password": "NewStr0ngPass"},
    )
    assert login.status_code == 200

    await db_session.refresh(user)
    assert verify_password("NewStr0ngPass", user.hashed_password)

    replay = await async_client.post(
        "/auth/reset-password",
        json={"token": raw_token, "new_password": "AnotherPass1"},
    )
    assert replay.status_code in (400, 422)


async def test_reset_rejects_expired_or_weak(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    """Expired tokens and weak passwords are rejected."""
    user = await _seed_user(db_session)

    expired = PasswordResetToken(
        user_id=user.id,
        token_hash=hashlib.sha256(b"expired-token").hexdigest(),
        expires_at=datetime.now(UTC) - timedelta(minutes=5),
    )
    db_session.add(expired)
    await db_session.commit()

    stale = await async_client.post(
        "/auth/reset-password",
        json={"token": "expired-token", "new_password": "NewStr0ngPass"},
    )
    assert stale.status_code in (400, 410, 422)

    forgot = await async_client.post(
        "/auth/forgot-password", json={"email": "reset-me@example.com"}
    )
    weak = await async_client.post(
        "/auth/reset-password",
        json={"token": forgot.json()["dev_token"], "new_password": "weakpass"},
    )
    assert weak.status_code == 422

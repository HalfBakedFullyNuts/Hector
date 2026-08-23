"""Tests for the admin bootstrap CLI."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hector.cli import _create_admin, main
from hector.models.user import User, UserRole

STRONG_PASSWORD = "Sup3rSecurePW"


def test_cli_requires_subcommand() -> None:
    """CLI without a subcommand exits nonzero with usage."""
    assert main([]) != 0


def test_cli_rejects_weak_password() -> None:
    """Weak passwords are refused before touching the database."""
    code = main(
        [
            "create-admin",
            "--email",
            "admin@example.com",
            "--password",
            "weakpass",
        ]
    )
    assert code == 2


async def test_create_admin_creates_verified_admin(db_session: AsyncSession) -> None:
    """create-admin persists an active verified ADMIN user."""
    code = await _create_admin("admin-cli@example.com", STRONG_PASSWORD)
    assert code == 0

    result = await db_session.execute(
        select(User).where(User.email == "admin-cli@example.com")
    )
    user = result.scalar_one()
    assert user.role == UserRole.ADMIN
    assert user.is_active is True
    assert user.is_verified is True


async def test_create_admin_rejects_duplicate_email(db_session: AsyncSession) -> None:
    """Duplicate admin email exits nonzero without creating a row."""
    db_session.add(User(email="dupe@example.com", hashed_password="x", role=UserRole.DOG_OWNER))
    await db_session.commit()

    code = await _create_admin("dupe@example.com", STRONG_PASSWORD)
    assert code == 1

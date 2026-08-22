"""Tests for the database test fixtures themselves."""

from sqlalchemy import select

from hector.models.user import User


async def test_db_session_persists_rows_within_test(db_session) -> None:
    """Rows written during one test are visible until truncation."""
    user = User(email="fixture-a@example.com", hashed_password="x", role="dog_owner")
    db_session.add(user)
    await db_session.commit()

    result = await db_session.execute(select(User).where(User.email == "fixture-a@example.com"))
    assert result.scalar_one_or_none() is not None


async def test_db_session_truncates_between_tests(db_session) -> None:
    """Each test starts from an empty database."""
    result = await db_session.execute(select(User))
    assert result.scalars().all() == []

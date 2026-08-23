"""Shared queries for clinic-scoped donation requests (T-505)."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from hector.models.clinic_staff import clinic_staff_association
from hector.models.donation_request import BloodDonationRequest


async def resolve_clinic_ids(db: AsyncSession, user_id: UUID) -> list[UUID]:
    """Return IDs of clinics the user belongs to (may be empty)."""
    assert user_id is not None
    rows = await db.execute(
        select(clinic_staff_association.c.clinic_id).where(
            clinic_staff_association.c.user_id == user_id
        )
    )
    return [row for row in rows.scalars().all()]


async def fetch_clinic_requests(
    db: AsyncSession,
    clinic_ids: list[UUID],
    status_filter: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[BloodDonationRequest]:
    """Fetch requests for the given clinics, newest first, optionally filtered."""
    assert limit >= 1 and offset >= 0
    stmt = (
        select(BloodDonationRequest)
        .where(BloodDonationRequest.clinic_id.in_(clinic_ids))
        .order_by(BloodDonationRequest.created_at.desc())
        .limit(limit)
        .offset(offset)
        .options(selectinload(BloodDonationRequest.clinic))
    )
    if status_filter is not None:
        stmt = stmt.where(BloodDonationRequest.status == status_filter)
    result = await db.execute(stmt)
    return list(result.scalars().all())

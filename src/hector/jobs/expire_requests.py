"""Request expiration automation (T-1005)."""

import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hector.models.clinic import Clinic
from hector.models.donation_request import BloodDonationRequest, RequestStatus
from hector.services.email import send_email

LOG = logging.getLogger(__name__)


async def expire_overdue_requests(db: AsyncSession) -> int:
    """Flip overdue OPEN requests to EXPIRED; notify affected clinics.

    Returns the number of expired requests. Idempotent by construction:
    only rows currently OPEN and past needed_by_date are touched.
    """
    now = datetime.now(UTC)
    overdue_stmt = (
        select(BloodDonationRequest)
        .where(BloodDonationRequest.status == RequestStatus.OPEN)
        .where(BloodDonationRequest.needed_by_date < now)
    )
    overdue = list((await db.execute(overdue_stmt)).scalars().all())

    if not overdue:
        return 0

    notified_clinics: dict[object, int] = {}
    for request in overdue:
        assert request.status == RequestStatus.OPEN
        request.status = RequestStatus.EXPIRED
        notified_clinics[request.clinic_id] = notified_clinics.get(request.clinic_id, 0) + 1

    await db.commit()

    for clinic_id, count in notified_clinics.items():
        clinic = await db.scalar(select(Clinic).where(Clinic.id == clinic_id))
        assert clinic is not None, "expired request must reference a clinic"
        body = (
            f"{count} of your blood donation request(s) passed their needed-by date "
            "and have been marked EXPIRED.\nCreate a new request if blood is still needed."
        )
        await send_email(
            db=db,
            recipient=clinic.email,
            subject=f"{count} donation request(s) expired",
            body_text=body,
            template="request_expired",
            related_type="clinic",
            related_id=clinic.id,
        )

    LOG.info("Expired %d overdue donation requests", len(overdue))
    return len(overdue)

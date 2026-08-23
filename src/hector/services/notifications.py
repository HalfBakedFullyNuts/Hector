"""Notification services (T-1002, T-1003)."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from hector.models.clinic import Clinic
from hector.models.dog_profile import DogProfile
from hector.models.donation_request import BloodDonationRequest
from hector.models.email_log import EmailLog
from hector.models.user import User
from hector.services.compatibility import compatibility_score
from hector.services.email import UNSUBSCRIBE_FOOTER, send_email

MAX_EMAILS_PER_USER_PER_DAY = 5


async def emails_sent_today(db: AsyncSession, recipient: str) -> int:
    """Count emails already sent/logged to a recipient in the last 24h."""
    since = datetime.now(UTC) - timedelta(days=1)
    stmt = (
        select(func.count(EmailLog.id))
        .where(EmailLog.recipient == recipient)
        .where(EmailLog.created_at >= since)
    )
    return int((await db.execute(stmt)).scalar() or 0)


async def _candidate_dogs(db: AsyncSession, request: BloodDonationRequest) -> list[DogProfile]:
    """Active, available dogs worth scoring against the new request."""
    stmt = select(DogProfile).where(
        DogProfile.is_active == True,  # noqa: E712
        DogProfile.is_available_for_donation == True,  # noqa: E712
    )
    if request.blood_type_needed is not None:
        # Unknown blood type is too weak a signal to justify an email.
        stmt = stmt.where(DogProfile.blood_type.isnot(None))
    return list((await db.execute(stmt)).scalars().all())


async def notify_compatible_owners(db: AsyncSession, request: BloodDonationRequest) -> int:
    """Email eligible compatible owners about a new request (T-1002).

    Owners without a city are treated as matching any clinic location.
    Returns the number of notification emails actually sent.
    """
    clinic = await db.scalar(select(Clinic).where(Clinic.id == request.clinic_id))
    assert clinic is not None, "request must reference an existing clinic"

    sent = 0
    seen_owners: set[UUID] = set()
    for dog in await _candidate_dogs(db, request):
        if compatibility_score(dog.blood_type, request.blood_type_needed) <= 0:
            continue
        if not dog.is_eligible_for_donation or dog.owner_id in seen_owners:
            continue

        owner = await db.scalar(select(User).where(User.id == dog.owner_id))
        assert owner is not None, "dog must have an owner"
        seen_owners.add(dog.owner_id)

        if owner.city and clinic.city and owner.city != clinic.city:
            continue
        if await emails_sent_today(db, owner.email) >= MAX_EMAILS_PER_USER_PER_DAY:
            continue

        body = (
            f"Hi,\n\n{clinic.name} in {clinic.city} needs blood "
            f"({request.volume_ml} ml, urgency {request.urgency.value}).\n"
            f"Your dog {dog.name} looks like a possible match!\n\n"
            "Open the app to view and respond to this request."
            f"{UNSUBSCRIBE_FOOTER}"
        )
        await send_email(
            db=db,
            recipient=owner.email,
            subject=f"Blood donation needed: {clinic.name} ({request.urgency.value})",
            body_text=body,
            template="match_notification",
            related_type="donation_request",
            related_id=request.id,
        )
        sent += 1

    return sent


async def notify_clinic_of_response(db: AsyncSession, response) -> None:
    """Tell the requesting clinic that a donor accepted (T-1003)."""
    request = await db.scalar(
        select(BloodDonationRequest).where(BloodDonationRequest.id == response.request_id)
    )
    clinic = await db.scalar(select(Clinic).where(Clinic.id == request.clinic_id))
    dog = await db.scalar(select(DogProfile).where(DogProfile.id == response.dog_id))
    assert request is not None and clinic is not None and dog is not None

    body = (
        "Good news!\n\nA dog owner just offered their dog "
        f"{dog.name} ({dog.breed or 'mixed breed'}) for your blood request.\n"
        "Contact the owner through the platform to arrange the appointment."
        f"{UNSUBSCRIBE_FOOTER}"
    )
    await send_email(
        db=db,
        recipient=clinic.email,
        subject=f"Donor response for your blood request",
        body_text=body,
        template="response_received",
        related_type="donation_response",
        related_id=response.id,
    )

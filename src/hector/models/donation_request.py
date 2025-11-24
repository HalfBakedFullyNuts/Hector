"""Blood donation request model."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel
from .dog_profile import BloodType

if TYPE_CHECKING:
    from .clinic import Clinic
    from .user import User


class RequestUrgency(str, enum.Enum):
    """Urgency levels for blood donation requests."""

    CRITICAL = "CRITICAL"
    URGENT = "URGENT"
    ROUTINE = "ROUTINE"


class RequestStatus(str, enum.Enum):
    """Status of a blood donation request."""

    OPEN = "OPEN"
    FULFILLED = "FULFILLED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class BloodDonationRequest(BaseModel):
    """
    Blood donation request model.

    Clinics create requests when they need blood donations.
    Dog owners can browse and respond to these requests.
    """

    __tablename__ = "blood_donation_requests"

    clinic_id: Mapped[UUID] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="ID of the clinic making the request",
    )

    created_by_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        doc="ID of the user (clinic staff) who created the request",
    )

    blood_type_needed: Mapped[BloodType | None] = mapped_column(
        nullable=True,
        index=True,
        doc="Required blood type (null means any compatible donor)",
    )

    volume_ml: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Volume of blood needed in milliliters (50-500ml)",
    )

    urgency: Mapped[RequestUrgency] = mapped_column(
        nullable=False,
        index=True,
        doc="Urgency level of the request",
    )

    patient_info: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Optional information about the patient needing blood",
    )

    needed_by_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="Date by which blood is needed",
    )

    status: Mapped[RequestStatus] = mapped_column(
        default=RequestStatus.OPEN,
        nullable=False,
        index=True,
        doc="Current status of the request",
    )

    # Relationships
    clinic: Mapped["Clinic"] = relationship(  # noqa: F821
        "Clinic",
        backref="donation_requests",
        doc="Clinic that made the request",
    )

    created_by: Mapped["User"] = relationship(  # noqa: F821
        "User",
        backref="created_requests",
        foreign_keys=[created_by_user_id],
        doc="User who created the request",
    )

    # responses: Relationship to DonationResponse (one-to-many)
    # Will be defined in DonationResponse model

    def __repr__(self) -> str:
        """Return string representation of the donation request."""
        return (
            f"<BloodDonationRequest(id={self.id}, "
            f"blood_type={self.blood_type_needed}, "
            f"urgency={self.urgency}, status={self.status})>"
        )

    @property
    def is_expired(self) -> bool:
        """Check if the request has passed its needed_by_date."""
        from datetime import UTC

        return datetime.now(UTC) > self.needed_by_date

    @property
    def is_open(self) -> bool:
        """Check if the request is still open for responses."""
        return self.status == RequestStatus.OPEN and not self.is_expired

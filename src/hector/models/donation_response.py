"""Donation response model for dog owner responses to requests."""

import enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .dog_profile import DogProfile
    from .donation_request import BloodDonationRequest
    from .user import User


class ResponseStatus(str, enum.Enum):
    """Status of a donation response."""

    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    COMPLETED = "COMPLETED"


class DonationResponse(BaseModel):
    """
    Donation response model.

    Dog owners create responses to indicate their interest (or lack thereof)
    in donating blood for a specific request.
    """

    __tablename__ = "donation_responses"
    __table_args__ = (
        UniqueConstraint(
            "request_id",
            "dog_id",
            name="uq_request_dog",
        ),
    )

    request_id: Mapped[UUID] = mapped_column(
        ForeignKey("blood_donation_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="ID of the blood donation request",
    )

    dog_id: Mapped[UUID] = mapped_column(
        ForeignKey("dog_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="ID of the dog being offered for donation",
    )

    owner_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="ID of the dog owner",
    )

    status: Mapped[ResponseStatus] = mapped_column(
        nullable=False,
        index=True,
        doc="Status of the response",
    )

    response_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Optional message from the dog owner",
    )

    # Relationships
    request: Mapped["BloodDonationRequest"] = relationship(  # noqa: F821
        "BloodDonationRequest",
        backref="responses",
        doc="Blood donation request this response is for",
    )

    dog: Mapped["DogProfile"] = relationship(  # noqa: F821
        "DogProfile",
        backref="donation_responses",
        doc="Dog profile for the responding dog",
    )

    owner: Mapped["User"] = relationship(  # noqa: F821
        "User",
        backref="donation_responses",
        foreign_keys=[owner_id],
        doc="Dog owner who created the response",
    )

    def __repr__(self) -> str:
        """Return string representation of the donation response."""
        return (
            f"<DonationResponse(id={self.id}, "
            f"dog_id={self.dog_id}, "
            f"request_id={self.request_id}, "
            f"status={self.status})>"
        )

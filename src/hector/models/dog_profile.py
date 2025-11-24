"""Dog profile model for donor dogs."""

import enum
from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, Date, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .user import User


class BloodType(str, enum.Enum):
    """Canine blood types (DEA system)."""

    DEA_1_1_POSITIVE = "DEA_1_1_POSITIVE"
    DEA_1_1_NEGATIVE = "DEA_1_1_NEGATIVE"
    DEA_1_2_POSITIVE = "DEA_1_2_POSITIVE"
    DEA_1_2_NEGATIVE = "DEA_1_2_NEGATIVE"
    DEA_3_POSITIVE = "DEA_3_POSITIVE"
    DEA_3_NEGATIVE = "DEA_3_NEGATIVE"
    DEA_4_POSITIVE = "DEA_4_POSITIVE"
    DEA_4_NEGATIVE = "DEA_4_NEGATIVE"
    DEA_5_POSITIVE = "DEA_5_POSITIVE"
    DEA_5_NEGATIVE = "DEA_5_NEGATIVE"
    DEA_7_POSITIVE = "DEA_7_POSITIVE"
    DEA_7_NEGATIVE = "DEA_7_NEGATIVE"
    UNKNOWN = "UNKNOWN"


class DogSex(str, enum.Enum):
    """Dog sex."""

    MALE = "MALE"
    FEMALE = "FEMALE"


class DogProfile(BaseModel):
    """
    Dog profile model for dogs available for blood donation.

    Dog owners create profiles for their dogs, specifying health info
    and availability for donation.
    """

    __tablename__ = "dog_profiles"

    owner_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="ID of the dog owner (User)",
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Dog's name",
    )

    breed: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Dog's breed",
    )

    date_of_birth: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        doc="Dog's date of birth",
    )

    weight_kg: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Dog's weight in kilograms (must be >= 25kg for donation)",
    )

    sex: Mapped[DogSex] = mapped_column(
        nullable=False,
        doc="Dog's sex",
    )

    blood_type: Mapped[BloodType | None] = mapped_column(
        nullable=True,
        doc="Dog's blood type (if known)",
    )

    last_donation_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="Date of last blood donation (if any)",
    )

    medical_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Medical history and health information",
    )

    vaccination_status: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Current vaccination status",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether the dog profile is active",
    )

    # Relationships
    owner: Mapped["User"] = relationship(  # noqa: F821
        "User",
        backref="dog_profiles",
        doc="Dog owner relationship",
    )

    # responses: Relationship to DonationResponse (one-to-many)
    # Will be defined in DonationResponse model

    def __repr__(self) -> str:
        """Return string representation of the dog profile."""
        return (
            f"<DogProfile(id={self.id}, name={self.name}, "
            f"breed={self.breed}, blood_type={self.blood_type})>"
        )

    @property
    def age_years(self) -> int:
        """Calculate dog's age in years."""
        from datetime import datetime

        today = datetime.now().date()
        return (today - self.date_of_birth).days // 365

    @property
    def is_eligible_for_donation(self) -> bool:
        """
        Check if dog meets basic eligibility criteria for donation.

        Requirements:
        - Weight >= 25kg
        - Age between 1-8 years
        - Last donation > 8 weeks ago (if applicable)
        - Profile is active
        """
        from datetime import datetime

        # Check if profile is active
        if not self.is_active:
            return False

        # Check weight
        if self.weight_kg < 25:
            return False

        # Check age
        age = self.age_years
        if age < 1 or age > 8:
            return False

        # Check last donation date (must be at least 8 weeks ago)
        if self.last_donation_date:
            weeks_since_donation = (datetime.now().date() - self.last_donation_date).days // 7
            if weeks_since_donation < 8:
                return False

        return True

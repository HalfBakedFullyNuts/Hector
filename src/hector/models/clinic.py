"""Clinic model for veterinary clinics."""

from sqlalchemy import Boolean, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class Clinic(BaseModel):
    """
    Clinic model representing veterinary clinics.

    Clinics can post blood donation requests after being approved by admins.
    """

    __tablename__ = "clinics"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Clinic name",
    )

    address: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Clinic street address",
    )

    city: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="City where clinic is located",
    )

    postal_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        doc="Postal/ZIP code",
    )

    phone: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Contact phone number",
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Contact email address",
    )

    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        doc="Geographic latitude for proximity matching",
    )

    longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        doc="Geographic longitude for proximity matching",
    )

    is_approved: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether the clinic has been approved by an admin",
    )

    # Relationships
    # staff: Relationship to User (many-to-many through association table)
    # requests: Relationship to BloodDonationRequest (one-to-many)
    # Will be defined when implementing relationships

    def __repr__(self) -> str:
        """Return string representation of the clinic."""
        return (
            f"<Clinic(id={self.id}, name={self.name}, "
            f"city={self.city}, approved={self.is_approved})>"
        )

"""User model for authentication and authorization."""

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .clinic import Clinic


class UserRole(str, enum.Enum):
    """User roles in the system."""

    CLINIC_STAFF = "clinic_staff"
    DOG_OWNER = "dog_owner"
    ADMIN = "admin"


class User(BaseModel):
    """
    User model representing system users.

    Users can have different roles (clinic staff, dog owners, or admins).
    """

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        doc="User's email address (unique)",
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Bcrypt hashed password",
    )

    role: Mapped[UserRole] = mapped_column(
        nullable=False,
        index=True,
        doc="User's role in the system",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether the user account is active",
    )

    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether the user's email has been verified",
    )

    # Relationships
    # dog_profiles: Relationship to DogProfile (one-to-many)
    # Will be defined in DogProfile model

    clinics: Mapped[list["Clinic"]] = relationship(
        "Clinic",
        secondary="clinic_staff",
        back_populates="staff",
        doc="Clinics where this user is staff",
    )

    def __repr__(self) -> str:
        """Return string representation of the user."""
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"

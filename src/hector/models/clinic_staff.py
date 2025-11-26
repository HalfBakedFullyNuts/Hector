"""Clinic staff association table."""

from sqlalchemy import Column, ForeignKey, Table

from .base import Base

# Association table for many-to-many relationship between User and Clinic
clinic_staff_association = Table(
    "clinic_staff",
    Base.metadata,
    Column(
        "user_id",
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        doc="User ID (clinic staff member)",
    ),
    Column(
        "clinic_id",
        ForeignKey("clinics.id", ondelete="CASCADE"),
        primary_key=True,
        doc="Clinic ID",
    ),
)

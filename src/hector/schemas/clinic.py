"""Pydantic schemas for clinic management."""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ClinicCreate(BaseModel):
    """Schema for creating a new clinic."""

    name: str = Field(max_length=255, description="Clinic name")
    address: str = Field(description="Clinic street address")
    city: str = Field(max_length=100, description="City where clinic is located")
    postal_code: str = Field(max_length=20, description="Postal/ZIP code")
    phone: str = Field(max_length=50, description="Contact phone number")
    email: EmailStr = Field(description="Contact email address")
    latitude: float | None = Field(default=None, ge=-90, le=90, description="Geographic latitude")
    longitude: float | None = Field(
        default=None, ge=-180, le=180, description="Geographic longitude"
    )


class ClinicUpdate(BaseModel):
    """Schema for updating a clinic profile."""

    name: str | None = Field(default=None, max_length=255, description="Clinic name")
    address: str | None = Field(default=None, description="Clinic street address")
    city: str | None = Field(
        default=None, max_length=100, description="City where clinic is located"
    )
    postal_code: str | None = Field(default=None, max_length=20, description="Postal/ZIP code")
    phone: str | None = Field(default=None, max_length=50, description="Contact phone number")
    email: EmailStr | None = Field(default=None, description="Contact email address")
    latitude: float | None = Field(default=None, ge=-90, le=90, description="Geographic latitude")
    longitude: float | None = Field(
        default=None, ge=-180, le=180, description="Geographic longitude"
    )


class ClinicOut(BaseModel):
    """Schema for clinic output."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    address: str
    city: str
    postal_code: str
    phone: str
    email: str
    latitude: float | None = None
    longitude: float | None = None
    is_approved: bool
    created_at: Any  # datetime
    updated_at: Any  # datetime


class PaginatedClinics(BaseModel):
    """Paginated response for clinic listings."""

    items: list[ClinicOut]
    total: int = Field(description="Total number of matching clinics")
    limit: int = Field(description="Maximum items per page")
    offset: int = Field(description="Number of items skipped")
    has_more: bool = Field(description="Whether there are more items available")

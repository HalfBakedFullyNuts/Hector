"""Clinic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class ClinicCreate(BaseModel):
    """Request schema for creating a clinic profile."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Clinic name",
        examples=["Berlin Veterinary Hospital"],
    )

    address: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Clinic street address",
        examples=["123 Main Street"],
    )

    city: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="City where clinic is located",
        examples=["Berlin"],
    )

    postal_code: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Postal/ZIP code",
        examples=["10115"],
    )

    phone: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Contact phone number",
        examples=["+49 30 12345678"],
    )

    email: EmailStr = Field(
        ...,
        description="Contact email address",
        examples=["contact@berlinvet.com"],
    )

    latitude: float | None = Field(
        None,
        ge=-90.0,
        le=90.0,
        description="Geographic latitude (optional)",
        examples=[52.5200],
    )

    longitude: float | None = Field(
        None,
        ge=-180.0,
        le=180.0,
        description="Geographic longitude (optional)",
        examples=[13.4050],
    )


class ClinicUpdate(BaseModel):
    """Request schema for updating a clinic profile."""

    name: str | None = Field(
        None,
        min_length=1,
        max_length=255,
        description="Clinic name",
        examples=["Berlin Veterinary Hospital"],
    )

    address: str | None = Field(
        None,
        min_length=1,
        max_length=1000,
        description="Clinic street address",
        examples=["123 Main Street"],
    )

    city: str | None = Field(
        None,
        min_length=1,
        max_length=100,
        description="City where clinic is located",
        examples=["Berlin"],
    )

    postal_code: str | None = Field(
        None,
        min_length=1,
        max_length=20,
        description="Postal/ZIP code",
        examples=["10115"],
    )

    phone: str | None = Field(
        None,
        min_length=1,
        max_length=50,
        description="Contact phone number",
        examples=["+49 30 12345678"],
    )

    email: EmailStr | None = Field(
        None,
        description="Contact email address",
        examples=["contact@berlinvet.com"],
    )

    latitude: float | None = Field(
        None,
        ge=-90.0,
        le=90.0,
        description="Geographic latitude",
        examples=[52.5200],
    )

    longitude: float | None = Field(
        None,
        ge=-180.0,
        le=180.0,
        description="Geographic longitude",
        examples=[13.4050],
    )


class ClinicResponse(BaseModel):
    """Response schema for clinic data."""

    model_config = {"from_attributes": True}

    id: UUID = Field(..., description="Clinic unique identifier")
    name: str = Field(..., description="Clinic name")
    address: str = Field(..., description="Clinic street address")
    city: str = Field(..., description="City where clinic is located")
    postal_code: str = Field(..., description="Postal/ZIP code")
    phone: str = Field(..., description="Contact phone number")
    email: str = Field(..., description="Contact email address")
    latitude: float | None = Field(None, description="Geographic latitude")
    longitude: float | None = Field(None, description="Geographic longitude")
    is_approved: bool = Field(..., description="Whether the clinic has been approved by an admin")
    created_at: datetime = Field(..., description="Clinic creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

"""Pydantic schemas for donation responses."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .donation_request import BloodTypeEnum


class ResponseStatusEnum(str, Enum):
    """Status of a donation response."""

    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    COMPLETED = "COMPLETED"


class DogSummary(BaseModel):
    """Summary of dog information for response listings."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    breed: str | None = None
    blood_type: BloodTypeEnum | None = None
    weight_kg: float
    is_eligible: bool = Field(description="Whether dog meets donation eligibility criteria")


class OwnerSummary(BaseModel):
    """Summary of owner information for response listings."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str


class DonationResponseCreate(BaseModel):
    """Schema for creating a donation response."""

    dog_id: UUID = Field(description="ID of the dog to respond with")
    status: ResponseStatusEnum = Field(description="ACCEPTED or DECLINED")
    response_message: str | None = Field(
        default=None, max_length=1000, description="Optional message to the clinic"
    )


class DonationResponseOut(BaseModel):
    """Response schema for a donation response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    request_id: UUID
    dog_id: UUID
    owner_id: UUID
    status: ResponseStatusEnum
    response_message: str | None = None
    created_at: datetime
    updated_at: datetime


class DonationResponseDetail(BaseModel):
    """Detailed response schema with dog and owner info."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    request_id: UUID
    status: ResponseStatusEnum
    response_message: str | None = None
    created_at: datetime
    dog: DogSummary
    owner: OwnerSummary


class EligibilityCheck(BaseModel):
    """Result of checking dog eligibility for donation."""

    is_eligible: bool
    reasons: list[str] = Field(default_factory=list, description="List of reasons if not eligible")

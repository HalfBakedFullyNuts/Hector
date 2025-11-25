"""Pydantic schemas for dog profile management."""

from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .donation_request import BloodTypeEnum


class DogSexEnum(str, Enum):
    """Dog sex for API schema."""

    MALE = "MALE"
    FEMALE = "FEMALE"


class DogProfileCreate(BaseModel):
    """Schema for creating a dog profile."""

    name: str = Field(max_length=100, description="Dog's name")
    breed: str | None = Field(default=None, max_length=100, description="Dog's breed")
    date_of_birth: date = Field(description="Dog's date of birth")
    weight_kg: float = Field(ge=0, description="Dog's weight in kilograms")
    sex: DogSexEnum = Field(description="Dog's sex")
    blood_type: BloodTypeEnum | None = Field(default=None, description="Dog's blood type if known")
    medical_notes: str | None = Field(default=None, description="Medical history and notes")
    vaccination_status: str | None = Field(
        default=None, max_length=100, description="Current vaccination status"
    )

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, v: date) -> date:
        """Ensure date of birth is in the past."""
        if v >= date.today():
            raise ValueError("Date of birth must be in the past")
        return v


class DogProfileUpdate(BaseModel):
    """Schema for updating a dog profile (partial updates allowed)."""

    name: str | None = Field(default=None, max_length=100, description="Dog's name")
    breed: str | None = Field(default=None, max_length=100, description="Dog's breed")
    date_of_birth: date | None = Field(default=None, description="Dog's date of birth")
    weight_kg: float | None = Field(default=None, ge=0, description="Dog's weight in kilograms")
    sex: DogSexEnum | None = Field(default=None, description="Dog's sex")
    blood_type: BloodTypeEnum | None = Field(default=None, description="Dog's blood type if known")
    medical_notes: str | None = Field(default=None, description="Medical history and notes")
    vaccination_status: str | None = Field(
        default=None, max_length=100, description="Current vaccination status"
    )
    last_donation_date: date | None = Field(default=None, description="Date of last donation")

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, v: date | None) -> date | None:
        """Ensure date of birth is in the past."""
        if v is not None and v >= date.today():
            raise ValueError("Date of birth must be in the past")
        return v


class DogProfileOut(BaseModel):
    """Response schema for a dog profile."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_id: UUID
    name: str
    breed: str | None = None
    date_of_birth: date
    weight_kg: float
    sex: DogSexEnum
    blood_type: BloodTypeEnum | None = None
    last_donation_date: date | None = None
    medical_notes: str | None = None
    vaccination_status: str | None = None
    is_active: bool
    is_eligible: bool = Field(description="Whether dog meets donation eligibility criteria")
    age_years: int = Field(description="Dog's age in years")
    created_at: datetime
    updated_at: datetime


class PaginatedDogProfiles(BaseModel):
    """Paginated response for dog profile listings."""

    items: list[DogProfileOut]
    total: int = Field(description="Total number of matching profiles")
    limit: int = Field(description="Maximum items per page")
    offset: int = Field(description="Number of items skipped")
    has_more: bool = Field(description="Whether there are more items available")

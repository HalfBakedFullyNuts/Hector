"""Dog profile schemas."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from hector.models.dog_profile import BloodType, DogSex


class DogProfileCreate(BaseModel):
    """Request schema for creating a dog profile."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Dog's name",
        examples=["Max"],
    )

    breed: str | None = Field(
        None,
        max_length=100,
        description="Dog's breed (optional)",
        examples=["Labrador Retriever"],
    )

    date_of_birth: date = Field(
        ...,
        description="Dog's date of birth",
        examples=["2020-01-15"],
    )

    weight_kg: float = Field(
        ...,
        ge=25.0,
        le=100.0,
        description="Dog's weight in kilograms (must be >= 25kg for donation eligibility)",
        examples=[30.5],
    )

    sex: DogSex = Field(
        ...,
        description="Dog's sex",
        examples=[DogSex.MALE],
    )

    blood_type: BloodType | None = Field(
        None,
        description="Dog's blood type (optional, if known)",
        examples=[BloodType.DEA_1_1_NEGATIVE],
    )

    last_donation_date: date | None = Field(
        None,
        description="Date of last blood donation (optional, if applicable)",
        examples=["2024-10-01"],
    )

    medical_notes: str | None = Field(
        None,
        max_length=2000,
        description="Medical history and health information (optional)",
        examples=["Up to date on all vaccinations. No known health issues."],
    )

    vaccination_status: str | None = Field(
        None,
        max_length=100,
        description="Current vaccination status (optional)",
        examples=["All core vaccines current"],
    )

    @field_validator("date_of_birth")
    @classmethod
    def validate_age(cls, value: date) -> date:
        """Validate dog is between 1 and 8 years old."""
        today = datetime.now().date()
        age_years = (today - value).days // 365

        if age_years < 1:
            raise ValueError("Dog must be at least 1 year old for donation eligibility")

        if age_years > 8:
            raise ValueError("Dog must be 8 years or younger for donation eligibility")

        return value

    @field_validator("last_donation_date")
    @classmethod
    def validate_last_donation_date(cls, value: date | None) -> date | None:
        """Validate last donation date is not in the future."""
        if value is None:
            return value

        today = datetime.now().date()
        if value > today:
            raise ValueError("Last donation date cannot be in the future")

        return value


class DogProfileUpdate(BaseModel):
    """Request schema for updating a dog profile."""

    name: str | None = Field(
        None,
        min_length=1,
        max_length=100,
        description="Dog's name",
        examples=["Max"],
    )

    breed: str | None = Field(
        None,
        max_length=100,
        description="Dog's breed",
        examples=["Labrador Retriever"],
    )

    date_of_birth: date | None = Field(
        None,
        description="Dog's date of birth",
        examples=["2020-01-15"],
    )

    weight_kg: float | None = Field(
        None,
        ge=25.0,
        le=100.0,
        description="Dog's weight in kilograms",
        examples=[30.5],
    )

    sex: DogSex | None = Field(
        None,
        description="Dog's sex",
        examples=[DogSex.MALE],
    )

    blood_type: BloodType | None = Field(
        None,
        description="Dog's blood type",
        examples=[BloodType.DEA_1_1_NEGATIVE],
    )

    last_donation_date: date | None = Field(
        None,
        description="Date of last blood donation",
        examples=["2024-10-01"],
    )

    medical_notes: str | None = Field(
        None,
        max_length=2000,
        description="Medical history and health information",
        examples=["Up to date on all vaccinations. No known health issues."],
    )

    vaccination_status: str | None = Field(
        None,
        max_length=100,
        description="Current vaccination status",
        examples=["All core vaccines current"],
    )

    @field_validator("date_of_birth")
    @classmethod
    def validate_age(cls, value: date | None) -> date | None:
        """Validate dog is between 1 and 8 years old."""
        if value is None:
            return value

        today = datetime.now().date()
        age_years = (today - value).days // 365

        if age_years < 1:
            raise ValueError("Dog must be at least 1 year old for donation eligibility")

        if age_years > 8:
            raise ValueError("Dog must be 8 years or younger for donation eligibility")

        return value

    @field_validator("last_donation_date")
    @classmethod
    def validate_last_donation_date(cls, value: date | None) -> date | None:
        """Validate last donation date is not in the future."""
        if value is None:
            return value

        today = datetime.now().date()
        if value > today:
            raise ValueError("Last donation date cannot be in the future")

        return value


class DogProfileResponse(BaseModel):
    """Response schema for dog profile data."""

    model_config = {"from_attributes": True}

    id: UUID = Field(..., description="Dog profile unique identifier")
    owner_id: UUID = Field(..., description="ID of the dog owner")
    name: str = Field(..., description="Dog's name")
    breed: str | None = Field(None, description="Dog's breed")
    date_of_birth: date = Field(..., description="Dog's date of birth")
    weight_kg: float = Field(..., description="Dog's weight in kilograms")
    sex: DogSex = Field(..., description="Dog's sex")
    blood_type: BloodType | None = Field(None, description="Dog's blood type")
    last_donation_date: date | None = Field(None, description="Date of last blood donation")
    medical_notes: str | None = Field(None, description="Medical history and health information")
    vaccination_status: str | None = Field(None, description="Current vaccination status")
    is_active: bool = Field(..., description="Whether the dog profile is active")
    created_at: datetime = Field(..., description="Profile creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class DogAvailabilityUpdate(BaseModel):
    """Request schema for updating dog availability status."""

    is_active: bool = Field(
        ...,
        description="Whether the dog should be marked as active/available",
        examples=[True],
    )

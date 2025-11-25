"""Blood donation request schemas."""

from datetime import datetime, timedelta
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from hector.models.dog_profile import BloodType
from hector.models.donation_request import RequestStatus, RequestUrgency


class DonationRequestCreate(BaseModel):
    """Request schema for creating a blood donation request."""

    blood_type_needed: BloodType | None = Field(
        None,
        description="Required blood type (null means any compatible donor)",
        examples=[BloodType.DEA_1_1_NEGATIVE],
    )

    volume_ml: int = Field(
        ...,
        ge=50,
        le=500,
        description="Volume of blood needed in milliliters (50-500ml)",
        examples=[250],
    )

    urgency: RequestUrgency = Field(
        ...,
        description="Urgency level of the request",
        examples=[RequestUrgency.URGENT],
    )

    patient_info: str | None = Field(
        None,
        max_length=2000,
        description="Optional information about the patient needing blood",
        examples=["Large dog in critical condition after accident"],
    )

    needed_by_date: datetime = Field(
        ...,
        description="Date by which blood is needed (within 30 days)",
        examples=["2024-12-15T14:00:00Z"],
    )

    @field_validator("needed_by_date")
    @classmethod
    def validate_needed_by_date(cls, value: datetime) -> datetime:
        """Validate needed_by_date is in future and within 30 days."""
        from datetime import UTC

        now = datetime.now(UTC)

        # Ensure datetime is timezone-aware
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)

        if value <= now:
            raise ValueError("needed_by_date must be in the future")

        max_date = now + timedelta(days=30)
        if value > max_date:
            raise ValueError("needed_by_date must be within 30 days from now")

        return value


class DonationRequestUpdate(BaseModel):
    """Request schema for updating a blood donation request."""

    urgency: RequestUrgency | None = Field(
        None,
        description="Urgency level of the request",
        examples=[RequestUrgency.CRITICAL],
    )

    patient_info: str | None = Field(
        None,
        max_length=2000,
        description="Information about the patient needing blood",
        examples=["Patient condition deteriorating"],
    )

    volume_ml: int | None = Field(
        None,
        ge=50,
        le=500,
        description="Volume of blood needed in milliliters",
        examples=[300],
    )

    needed_by_date: datetime | None = Field(
        None,
        description="Date by which blood is needed",
        examples=["2024-12-20T14:00:00Z"],
    )

    @field_validator("needed_by_date")
    @classmethod
    def validate_needed_by_date(cls, value: datetime | None) -> datetime | None:
        """Validate needed_by_date is in future and within 30 days."""
        if value is None:
            return value

        from datetime import UTC

        now = datetime.now(UTC)

        # Ensure datetime is timezone-aware
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)

        if value <= now:
            raise ValueError("needed_by_date must be in the future")

        max_date = now + timedelta(days=30)
        if value > max_date:
            raise ValueError("needed_by_date must be within 30 days from now")

        return value


class DonationRequestResponse(BaseModel):
    """Response schema for blood donation request data."""

    model_config = {"from_attributes": True}

    id: UUID = Field(..., description="Request unique identifier")
    clinic_id: UUID = Field(..., description="ID of the clinic making the request")
    created_by_user_id: UUID | None = Field(
        None, description="ID of the user who created the request"
    )
    blood_type_needed: BloodType | None = Field(
        None, description="Required blood type (null means any compatible donor)"
    )
    volume_ml: int = Field(..., description="Volume of blood needed in milliliters")
    urgency: RequestUrgency = Field(..., description="Urgency level of the request")
    patient_info: str | None = Field(
        None, description="Information about the patient needing blood"
    )
    needed_by_date: datetime = Field(..., description="Date by which blood is needed")
    status: RequestStatus = Field(..., description="Current status of the request")
    created_at: datetime = Field(..., description="Request creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class DonationRequestWithClinic(DonationRequestResponse):
    """Response schema including clinic details."""

    from hector.schemas.clinic import ClinicResponse

    clinic: ClinicResponse = Field(..., description="Clinic that made the request")


class DonationRequestWithResponseCount(DonationRequestResponse):
    """Response schema including response count."""

    response_count: int = Field(..., description="Number of responses to this request")

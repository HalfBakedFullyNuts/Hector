"""Donation response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from hector.models.donation_response import ResponseStatus


class DonationResponseCreate(BaseModel):
    """Request schema for creating a donation response."""

    dog_id: UUID = Field(
        ...,
        description="ID of the dog being offered for donation",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )

    status: ResponseStatus = Field(
        ...,
        description="Response status (ACCEPTED or DECLINED)",
        examples=[ResponseStatus.ACCEPTED],
    )

    response_message: str | None = Field(
        None,
        max_length=2000,
        description="Optional message from the dog owner",
        examples=["My dog is available on weekdays"],
    )


class DonationResponseResponse(BaseModel):
    """Response schema for donation response data."""

    model_config = {"from_attributes": True}

    id: UUID = Field(..., description="Response unique identifier")
    request_id: UUID = Field(..., description="ID of the blood donation request")
    dog_id: UUID = Field(..., description="ID of the dog being offered")
    owner_id: UUID = Field(..., description="ID of the dog owner")
    status: ResponseStatus = Field(..., description="Status of the response")
    response_message: str | None = Field(None, description="Optional message from the dog owner")
    created_at: datetime = Field(..., description="Response creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class DonationResponseWithDetails(DonationResponseResponse):
    """Response schema including dog profile, owner, and request details."""

    from hector.schemas.clinic import ClinicResponse
    from hector.schemas.dog import DogProfileResponse
    from hector.schemas.donation_request import DonationRequestResponse

    dog: DogProfileResponse = Field(..., description="Dog profile details")
    owner_email: str = Field(..., description="Owner's email for contact")
    request: DonationRequestResponse | None = Field(None, description="Request details (optional)")
    clinic: ClinicResponse | None = Field(None, description="Clinic details (optional)")

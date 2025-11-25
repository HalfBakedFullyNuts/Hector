"""Pydantic schemas for blood donation requests."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BloodTypeEnum(str, Enum):
    """Canine blood types for API schema."""

    DEA_1_1_POSITIVE = "DEA_1_1_POSITIVE"
    DEA_1_1_NEGATIVE = "DEA_1_1_NEGATIVE"
    DEA_1_2_POSITIVE = "DEA_1_2_POSITIVE"
    DEA_1_2_NEGATIVE = "DEA_1_2_NEGATIVE"
    DEA_3_POSITIVE = "DEA_3_POSITIVE"
    DEA_3_NEGATIVE = "DEA_3_NEGATIVE"
    DEA_4_POSITIVE = "DEA_4_POSITIVE"
    DEA_4_NEGATIVE = "DEA_4_NEGATIVE"
    DEA_5_POSITIVE = "DEA_5_POSITIVE"
    DEA_5_NEGATIVE = "DEA_5_NEGATIVE"
    DEA_7_POSITIVE = "DEA_7_POSITIVE"
    DEA_7_NEGATIVE = "DEA_7_NEGATIVE"
    UNKNOWN = "UNKNOWN"


class RequestUrgencyEnum(str, Enum):
    """Urgency levels for blood donation requests."""

    CRITICAL = "CRITICAL"
    URGENT = "URGENT"
    ROUTINE = "ROUTINE"


class RequestStatusEnum(str, Enum):
    """Status of a blood donation request."""

    OPEN = "OPEN"
    FULFILLED = "FULFILLED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class ClinicSummary(BaseModel):
    """Summary of clinic information for request listings."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    city: str
    phone: str


class DonationRequestResponse(BaseModel):
    """Response schema for a single donation request."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinic_id: UUID
    blood_type_needed: BloodTypeEnum | None = None
    volume_ml: int
    urgency: RequestUrgencyEnum
    patient_info: str | None = None
    needed_by_date: datetime
    status: RequestStatusEnum
    created_at: datetime
    updated_at: datetime
    clinic: ClinicSummary


class DonationRequestBrowseResponse(BaseModel):
    """Response schema for browsing donation requests with compatibility info."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinic_id: UUID
    blood_type_needed: BloodTypeEnum | None = None
    volume_ml: int
    urgency: RequestUrgencyEnum
    patient_info: str | None = None
    needed_by_date: datetime
    status: RequestStatusEnum
    created_at: datetime
    clinic: ClinicSummary
    response_count: int = Field(default=0, description="Number of responses to this request")
    is_compatible: bool | None = Field(
        default=None, description="Whether user's dogs are compatible (null if not logged in)"
    )


class DonationRequestFilters(BaseModel):
    """Query filters for browsing donation requests."""

    status: RequestStatusEnum = Field(default=RequestStatusEnum.OPEN)
    blood_type: BloodTypeEnum | None = None
    urgency: RequestUrgencyEnum | None = None
    city: str | None = None


class PaginatedDonationRequests(BaseModel):
    """Paginated response for donation request listings."""

    items: list[DonationRequestBrowseResponse]
    total: int = Field(description="Total number of matching requests")
    limit: int = Field(description="Maximum items per page")
    offset: int = Field(description="Number of items skipped")
    has_more: bool = Field(description="Whether there are more items available")


class DonationRequestCreate(BaseModel):
    """Schema for creating a donation request."""

    blood_type_needed: BloodTypeEnum | None = Field(
        default=None, description="Required blood type (null for any)"
    )
    volume_ml: int = Field(ge=50, le=500, description="Volume of blood needed in ml (50-500)")
    urgency: RequestUrgencyEnum = Field(description="Urgency level of the request")
    needed_by_date: datetime = Field(description="Date by which blood is needed")
    patient_info: str | None = Field(default=None, description="Optional patient information")

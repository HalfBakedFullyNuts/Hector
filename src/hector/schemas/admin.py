"""Admin schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from hector.models.user import UserRole


class UserWithCounts(BaseModel):
    """User response with related counts."""

    model_config = {"from_attributes": True}

    id: str = Field(..., description="User unique identifier")
    email: str = Field(..., description="User's email address")
    role: UserRole = Field(..., description="User's role")
    is_active: bool = Field(..., description="Whether the user account is active")
    is_verified: bool = Field(..., description="Whether the user's email has been verified")
    created_at: datetime = Field(..., description="User creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    dog_count: int = Field(0, description="Number of dogs owned by this user")
    clinic_count: int = Field(0, description="Number of clinics this user is staff of")


class ToggleUserActiveRequest(BaseModel):
    """Request schema for toggling user active status."""

    reason: str | None = Field(
        None,
        max_length=500,
        description="Optional reason for disabling/enabling the account",
        examples=["Suspicious activity detected"],
    )


class DeleteUserRequest(BaseModel):
    """Request schema for deleting a user account."""

    user_id: str = Field(
        ...,
        description="User ID confirmation (must match path parameter)",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )

    reason: str | None = Field(
        None,
        max_length=500,
        description="Optional reason for deletion",
        examples=["Violated terms of service"],
    )


class PlatformStatistics(BaseModel):
    """Platform-wide statistics."""

    total_users: int = Field(..., description="Total number of users")
    users_by_role: dict[str, int] = Field(..., description="User count by role")
    total_dogs: int = Field(..., description="Total number of dog profiles")
    total_clinics: int = Field(..., description="Total number of clinics")
    approved_clinics: int = Field(..., description="Number of approved clinics")
    pending_clinics: int = Field(..., description="Number of pending clinic approvals")
    total_requests: int = Field(..., description="Total number of donation requests")
    requests_by_status: dict[str, int] = Field(..., description="Request count by status")
    total_responses: int = Field(..., description="Total number of donation responses")
    responses_by_status: dict[str, int] = Field(..., description="Response count by status")
    successful_donations_this_month: int = Field(
        ..., description="Number of completed donations this month"
    )


class ApproveClinicRequest(BaseModel):
    """Request schema for approving a clinic."""

    approval_notes: str | None = Field(
        None,
        max_length=500,
        description="Optional notes about the approval",
        examples=["Verified credentials and location"],
    )


class RejectClinicRequest(BaseModel):
    """Request schema for rejecting a clinic."""

    rejection_reason: str = Field(
        ...,
        max_length=500,
        description="Reason for rejecting the clinic application",
        examples=["Unable to verify credentials"],
    )

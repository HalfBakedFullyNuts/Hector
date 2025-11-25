"""Donation response endpoints for dog owners."""

import logging
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models import BloodDonationRequest, DogProfile
from ..models.donation_response import DonationResponse, ResponseStatus
from ..schemas import (
    BloodTypeEnum,
    ResponseStatusEnum,
)

LOG = logging.getLogger(__name__)

router = APIRouter(prefix="/my-responses", tags=["responses"])


class RequestSummaryForResponse(BaseModel):
    """Summary of donation request for response listings."""

    id: UUID
    blood_type_needed: BloodTypeEnum | None = None
    volume_ml: int
    urgency: str
    needed_by_date: Any  # datetime
    status: str
    clinic_name: str
    clinic_city: str


class DonationResponseWithRequestOut(BaseModel):
    """Response schema with request details for owner view."""

    id: UUID
    request_id: UUID
    dog_id: UUID
    status: ResponseStatusEnum
    response_message: str | None = None
    created_at: Any  # datetime
    request: RequestSummaryForResponse
    dog_name: str


class PaginatedMyResponses(BaseModel):
    """Paginated response for my donation responses."""

    items: list[DonationResponseWithRequestOut]
    total: int = Field(description="Total number of matching responses")
    limit: int = Field(description="Maximum items per page")
    offset: int = Field(description="Number of items skipped")
    has_more: bool = Field(description="Whether there are more items available")


@router.get(
    "",
    summary="List my dogs' donation responses",
    response_model=PaginatedMyResponses,
)
async def list_my_responses(
    db: Annotated[AsyncSession, Depends(get_db)],
    # TODO: Replace with proper auth dependency when T-204 is implemented
    x_user_id: Annotated[UUID, Header(description="User ID (temp auth header)")],
    response_status: Annotated[
        ResponseStatusEnum | None, Query(alias="status", description="Filter by response status")
    ] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Maximum items per page")] = 20,
    offset: Annotated[int, Query(ge=0, description="Number of items to skip")] = 0,
) -> PaginatedMyResponses:
    """
    List all donation responses for the authenticated user's dogs.

    Returns responses with request and clinic details, sorted by creation date.
    """
    # Build base query - get responses for all dogs owned by user
    base_query = (
        select(DonationResponse)
        .join(DogProfile, DonationResponse.dog_id == DogProfile.id)
        .options(
            selectinload(DonationResponse.request).selectinload(BloodDonationRequest.clinic),
            selectinload(DonationResponse.dog),
        )
        .where(DogProfile.owner_id == x_user_id)
    )

    if response_status is not None:
        base_query = base_query.where(
            DonationResponse.status == ResponseStatus(response_status.value)
        )

    # Count total matching
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply ordering and pagination
    base_query = base_query.order_by(DonationResponse.created_at.desc())
    base_query = base_query.limit(limit).offset(offset)

    # Execute query
    result = await db.execute(base_query)
    responses = result.scalars().all()

    items = [
        DonationResponseWithRequestOut(
            id=resp.id,
            request_id=resp.request_id,
            dog_id=resp.dog_id,
            status=ResponseStatusEnum(resp.status.value),
            response_message=resp.response_message,
            created_at=resp.created_at,
            request=RequestSummaryForResponse(
                id=resp.request.id,
                blood_type_needed=(
                    BloodTypeEnum(resp.request.blood_type_needed.value)
                    if resp.request.blood_type_needed
                    else None
                ),
                volume_ml=resp.request.volume_ml,
                urgency=resp.request.urgency.value,
                needed_by_date=resp.request.needed_by_date,
                status=resp.request.status.value,
                clinic_name=resp.request.clinic.name,
                clinic_city=resp.request.clinic.city,
            ),
            dog_name=resp.dog.name,
        )
        for resp in responses
    ]

    LOG.info(
        "List my responses",
        extra={
            "owner_id": str(x_user_id),
            "total": total,
            "returned": len(items),
            "status_filter": response_status.value if response_status else None,
        },
    )

    return PaginatedMyResponses(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + len(items)) < total,
    )

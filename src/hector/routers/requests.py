"""Blood donation request endpoints for browsing and listing."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models import BloodDonationRequest, Clinic
from ..models.dog_profile import BloodType
from ..models.donation_request import RequestStatus, RequestUrgency
from ..models.donation_response import DonationResponse
from ..schemas import (
    BloodTypeEnum,
    ClinicSummary,
    DonationRequestBrowseResponse,
    PaginatedDonationRequests,
    RequestStatusEnum,
    RequestUrgencyEnum,
)

LOG = logging.getLogger(__name__)

router = APIRouter(prefix="/requests", tags=["requests"])


def _map_blood_type(blood_type: BloodTypeEnum | None) -> BloodType | None:
    """Map schema blood type enum to model enum."""
    if blood_type is None:
        return None
    return BloodType(blood_type.value)


def _map_urgency(urgency: RequestUrgencyEnum | None) -> RequestUrgency | None:
    """Map schema urgency enum to model enum."""
    if urgency is None:
        return None
    return RequestUrgency(urgency.value)


def _map_status(status: RequestStatusEnum) -> RequestStatus:
    """Map schema status enum to model enum."""
    return RequestStatus(status.value)


@router.get(
    "/browse",
    summary="Browse open donation requests",
    response_model=PaginatedDonationRequests,
)
async def browse_requests(
    db: Annotated[AsyncSession, Depends(get_db)],
    status: Annotated[
        RequestStatusEnum, Query(description="Filter by status")
    ] = RequestStatusEnum.OPEN,
    blood_type: Annotated[
        BloodTypeEnum | None, Query(description="Filter by blood type needed")
    ] = None,
    urgency: Annotated[
        RequestUrgencyEnum | None, Query(description="Filter by urgency level")
    ] = None,
    city: Annotated[str | None, Query(description="Filter by clinic city")] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Maximum items per page")] = 20,
    offset: Annotated[int, Query(ge=0, description="Number of items to skip")] = 0,
) -> PaginatedDonationRequests:
    """
    Browse blood donation requests with filtering and pagination.

    Returns open requests sorted by urgency (CRITICAL first) and creation date.
    Includes clinic information and response count for each request.
    """
    # Build base query with clinic join
    base_query = (
        select(BloodDonationRequest).options(selectinload(BloodDonationRequest.clinic)).join(Clinic)
    )

    # Apply filters
    base_query = base_query.where(BloodDonationRequest.status == _map_status(status))

    if blood_type is not None:
        base_query = base_query.where(
            BloodDonationRequest.blood_type_needed == _map_blood_type(blood_type)
        )

    if urgency is not None:
        base_query = base_query.where(BloodDonationRequest.urgency == _map_urgency(urgency))

    if city is not None:
        base_query = base_query.where(Clinic.city.ilike(f"%{city}%"))

    # Count total matching requests
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply sorting: CRITICAL > URGENT > ROUTINE, then by created_at desc
    urgency_order = case(
        (BloodDonationRequest.urgency == RequestUrgency.CRITICAL, 0),
        (BloodDonationRequest.urgency == RequestUrgency.URGENT, 1),
        (BloodDonationRequest.urgency == RequestUrgency.ROUTINE, 2),
        else_=3,
    )
    base_query = base_query.order_by(urgency_order, BloodDonationRequest.created_at.desc())

    # Apply pagination
    base_query = base_query.limit(limit).offset(offset)

    # Execute query
    result = await db.execute(base_query)
    requests = result.scalars().all()

    # Get response counts for each request
    request_ids = [r.id for r in requests]
    response_counts: dict[str, int] = {}

    if request_ids:
        counts_query = (
            select(DonationResponse.request_id, func.count(DonationResponse.id))
            .where(DonationResponse.request_id.in_(request_ids))
            .group_by(DonationResponse.request_id)
        )
        counts_result = await db.execute(counts_query)
        response_counts = {str(row[0]): row[1] for row in counts_result.all()}

    # Build response items
    items = [
        DonationRequestBrowseResponse(
            id=req.id,
            clinic_id=req.clinic_id,
            blood_type_needed=(
                BloodTypeEnum(req.blood_type_needed.value) if req.blood_type_needed else None
            ),
            volume_ml=req.volume_ml,
            urgency=RequestUrgencyEnum(req.urgency.value),
            patient_info=req.patient_info,
            needed_by_date=req.needed_by_date,
            status=RequestStatusEnum(req.status.value),
            created_at=req.created_at,
            clinic=ClinicSummary(
                id=req.clinic.id,
                name=req.clinic.name,
                city=req.clinic.city,
                phone=req.clinic.phone,
            ),
            response_count=response_counts.get(str(req.id), 0),
            is_compatible=None,  # Would be set if user is authenticated
        )
        for req in requests
    ]

    LOG.info(
        "Browse requests",
        extra={
            "total": total,
            "returned": len(items),
            "filters": {
                "status": status.value,
                "blood_type": blood_type.value if blood_type else None,
                "urgency": urgency.value if urgency else None,
                "city": city,
            },
        },
    )

    return PaginatedDonationRequests(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + len(items)) < total,
    )


@router.get(
    "/{request_id}",
    summary="Get a single donation request",
    response_model=DonationRequestBrowseResponse,
)
async def get_request(
    request_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DonationRequestBrowseResponse:
    """
    Get details of a specific donation request.

    Public endpoint for transparency - anyone can view request details.
    """
    from fastapi import HTTPException

    # Query request with clinic
    query = (
        select(BloodDonationRequest)
        .options(selectinload(BloodDonationRequest.clinic))
        .where(BloodDonationRequest.id == request_id)
    )
    result = await db.execute(query)
    req = result.scalar_one_or_none()

    if req is None:
        raise HTTPException(status_code=404, detail="Request not found")

    # Get response count
    count_query = select(func.count(DonationResponse.id)).where(
        DonationResponse.request_id == req.id
    )
    count_result = await db.execute(count_query)
    response_count = count_result.scalar() or 0

    return DonationRequestBrowseResponse(
        id=req.id,
        clinic_id=req.clinic_id,
        blood_type_needed=(
            BloodTypeEnum(req.blood_type_needed.value) if req.blood_type_needed else None
        ),
        volume_ml=req.volume_ml,
        urgency=RequestUrgencyEnum(req.urgency.value),
        patient_info=req.patient_info,
        needed_by_date=req.needed_by_date,
        status=RequestStatusEnum(req.status.value),
        created_at=req.created_at,
        clinic=ClinicSummary(
            id=req.clinic.id,
            name=req.clinic.name,
            city=req.clinic.city,
            phone=req.clinic.phone,
        ),
        response_count=response_count,
        is_compatible=None,
    )

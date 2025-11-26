"""Clinic management endpoints for donation requests."""

import logging
from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
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
    ClinicCreate,
    ClinicOut,
    ClinicSummary,
    ClinicUpdate,
    DonationRequestBrowseResponse,
    DonationRequestCreate,
    DonationRequestResponse,
    PaginatedClinics,
    PaginatedDonationRequests,
    RequestStatusEnum,
    RequestUrgencyEnum,
)

LOG = logging.getLogger(__name__)

router = APIRouter(prefix="/clinics", tags=["clinics"])


# =============================================================================
# Clinic Profile Management (T-400, T-401, T-402, T-403)
# =============================================================================


@router.post(
    "",
    summary="Create a clinic profile",
    response_model=ClinicOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_clinic(
    clinic_data: ClinicCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    # TODO: Replace with proper auth dependency when T-204 is implemented
    x_user_id: Annotated[UUID, Header(description="User ID (temp auth header)")],
) -> ClinicOut:
    """
    Create a new clinic profile.

    The clinic will be created with is_approved=False. An admin must approve
    the clinic before it can create donation requests.
    """
    clinic = Clinic(
        name=clinic_data.name,
        address=clinic_data.address,
        city=clinic_data.city,
        postal_code=clinic_data.postal_code,
        phone=clinic_data.phone,
        email=clinic_data.email,
        latitude=clinic_data.latitude,
        longitude=clinic_data.longitude,
        is_approved=False,
    )

    db.add(clinic)
    await db.flush()

    LOG.info(
        "Clinic created",
        extra={
            "clinic_id": str(clinic.id),
            "name": clinic.name,
            "city": clinic.city,
            "created_by": str(x_user_id),
        },
    )

    return ClinicOut(
        id=clinic.id,
        name=clinic.name,
        address=clinic.address,
        city=clinic.city,
        postal_code=clinic.postal_code,
        phone=clinic.phone,
        email=clinic.email,
        latitude=clinic.latitude,
        longitude=clinic.longitude,
        is_approved=clinic.is_approved,
        created_at=clinic.created_at,
        updated_at=clinic.updated_at,
    )


@router.get(
    "",
    summary="List all clinics",
    response_model=PaginatedClinics,
)
async def list_clinics(
    db: Annotated[AsyncSession, Depends(get_db)],
    city: Annotated[str | None, Query(description="Filter by city")] = None,
    approved_only: Annotated[bool, Query(description="Only show approved clinics")] = True,
    limit: Annotated[int, Query(ge=1, le=100, description="Maximum items per page")] = 20,
    offset: Annotated[int, Query(ge=0, description="Number of items to skip")] = 0,
) -> PaginatedClinics:
    """
    List all clinics with optional filtering.

    By default, only approved clinics are shown. Set approved_only=false to see all.
    """
    base_query = select(Clinic)

    if approved_only:
        base_query = base_query.where(Clinic.is_approved.is_(True))

    if city:
        base_query = base_query.where(Clinic.city.ilike(f"%{city}%"))

    # Count total matching
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply ordering and pagination
    base_query = base_query.order_by(Clinic.name.asc())
    base_query = base_query.limit(limit).offset(offset)

    # Execute query
    result = await db.execute(base_query)
    clinics = result.scalars().all()

    items = [
        ClinicOut(
            id=c.id,
            name=c.name,
            address=c.address,
            city=c.city,
            postal_code=c.postal_code,
            phone=c.phone,
            email=c.email,
            latitude=c.latitude,
            longitude=c.longitude,
            is_approved=c.is_approved,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in clinics
    ]

    LOG.info(
        "List clinics",
        extra={
            "total": total,
            "returned": len(items),
            "city_filter": city,
            "approved_only": approved_only,
        },
    )

    return PaginatedClinics(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + len(items)) < total,
    )


@router.get(
    "/{clinic_id}",
    summary="Get clinic details",
    response_model=ClinicOut,
)
async def get_clinic(
    clinic_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ClinicOut:
    """
    Get details of a specific clinic.
    """
    query = select(Clinic).where(Clinic.id == clinic_id)
    result = await db.execute(query)
    clinic = result.scalar_one_or_none()

    if clinic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clinic not found")

    return ClinicOut(
        id=clinic.id,
        name=clinic.name,
        address=clinic.address,
        city=clinic.city,
        postal_code=clinic.postal_code,
        phone=clinic.phone,
        email=clinic.email,
        latitude=clinic.latitude,
        longitude=clinic.longitude,
        is_approved=clinic.is_approved,
        created_at=clinic.created_at,
        updated_at=clinic.updated_at,
    )


@router.put(
    "/{clinic_id}",
    summary="Update clinic profile",
    response_model=ClinicOut,
)
async def update_clinic(
    clinic_id: UUID,
    clinic_data: ClinicUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    # TODO: Replace with proper auth dependency when T-204 is implemented
    x_user_id: Annotated[UUID, Header(description="User ID (temp auth header)")],
) -> ClinicOut:
    """
    Update a clinic profile.

    Only clinic staff or admins can update a clinic profile.
    Only provided fields will be updated.
    """
    query = select(Clinic).where(Clinic.id == clinic_id)
    result = await db.execute(query)
    clinic = result.scalar_one_or_none()

    if clinic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clinic not found")

    # Update only provided fields
    update_data = clinic_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(clinic, field, value)

    await db.flush()

    LOG.info(
        "Clinic updated",
        extra={
            "clinic_id": str(clinic.id),
            "updated_by": str(x_user_id),
            "fields_updated": list(update_data.keys()),
        },
    )

    return ClinicOut(
        id=clinic.id,
        name=clinic.name,
        address=clinic.address,
        city=clinic.city,
        postal_code=clinic.postal_code,
        phone=clinic.phone,
        email=clinic.email,
        latitude=clinic.latitude,
        longitude=clinic.longitude,
        is_approved=clinic.is_approved,
        created_at=clinic.created_at,
        updated_at=clinic.updated_at,
    )


# =============================================================================
# Donation Request Management
# =============================================================================


def _map_blood_type(blood_type: BloodTypeEnum | None) -> BloodType | None:
    """Map schema blood type enum to model enum."""
    if blood_type is None:
        return None
    return BloodType(blood_type.value)


def _map_urgency(urgency: RequestUrgencyEnum) -> RequestUrgency:
    """Map schema urgency enum to model enum."""
    return RequestUrgency(urgency.value)


@router.post(
    "/requests",
    summary="Create a donation request",
    response_model=DonationRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_donation_request(
    request_data: DonationRequestCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    # TODO: Replace with proper auth dependency when T-204 is implemented
    x_user_id: Annotated[UUID, Header(description="User ID (temp auth header)")],
    x_clinic_id: Annotated[UUID, Header(description="Clinic ID (temp auth header)")],
) -> DonationRequestResponse:
    """
    Create a new blood donation request for a clinic.

    Only clinic staff can create requests. The request will be set to OPEN status.

    Validations:
    - Volume must be between 50-500ml
    - needed_by_date must be in the future (within 30 days)
    """
    # Verify clinic exists
    clinic_query = select(Clinic).where(Clinic.id == x_clinic_id)
    clinic_result = await db.execute(clinic_query)
    clinic = clinic_result.scalar_one_or_none()

    if clinic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clinic not found")

    if not clinic.is_approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Clinic must be approved before creating donation requests",
        )

    # Validate needed_by_date
    now = datetime.now(UTC)
    if request_data.needed_by_date <= now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="needed_by_date must be in the future",
        )

    max_date = now + timedelta(days=30)
    if request_data.needed_by_date > max_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="needed_by_date must be within 30 days",
        )

    # Create the request
    donation_request = BloodDonationRequest(
        clinic_id=x_clinic_id,
        created_by_user_id=x_user_id,
        blood_type_needed=_map_blood_type(request_data.blood_type_needed),
        volume_ml=request_data.volume_ml,
        urgency=_map_urgency(request_data.urgency),
        needed_by_date=request_data.needed_by_date,
        patient_info=request_data.patient_info,
        status=RequestStatus.OPEN,
    )

    db.add(donation_request)
    await db.flush()

    LOG.info(
        "Donation request created",
        extra={
            "request_id": str(donation_request.id),
            "clinic_id": str(x_clinic_id),
            "blood_type": (
                request_data.blood_type_needed.value if request_data.blood_type_needed else None
            ),
            "urgency": request_data.urgency.value,
        },
    )

    return DonationRequestResponse(
        id=donation_request.id,
        clinic_id=donation_request.clinic_id,
        blood_type_needed=(
            BloodTypeEnum(donation_request.blood_type_needed.value)
            if donation_request.blood_type_needed
            else None
        ),
        volume_ml=donation_request.volume_ml,
        urgency=RequestUrgencyEnum(donation_request.urgency.value),
        patient_info=donation_request.patient_info,
        needed_by_date=donation_request.needed_by_date,
        status=RequestStatusEnum(donation_request.status.value),
        created_at=donation_request.created_at,
        updated_at=donation_request.updated_at,
        clinic=ClinicSummary(
            id=clinic.id,
            name=clinic.name,
            city=clinic.city,
            phone=clinic.phone,
        ),
    )


@router.get(
    "/my-requests",
    summary="List my clinic's donation requests",
    response_model=PaginatedDonationRequests,
)
async def list_my_clinic_requests(
    db: Annotated[AsyncSession, Depends(get_db)],
    # TODO: Replace with proper auth dependency when T-204 is implemented
    x_clinic_id: Annotated[UUID, Header(description="Clinic ID (temp auth header)")],
    request_status: Annotated[
        RequestStatusEnum | None, Query(alias="status", description="Filter by status")
    ] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Maximum items per page")] = 20,
    offset: Annotated[int, Query(ge=0, description="Number of items to skip")] = 0,
) -> PaginatedDonationRequests:
    """
    List all donation requests created by the authenticated user's clinic.

    Returns requests sorted by creation date (newest first).
    """
    # Verify clinic exists
    clinic_query = select(Clinic).where(Clinic.id == x_clinic_id)
    clinic_result = await db.execute(clinic_query)
    clinic = clinic_result.scalar_one_or_none()

    if clinic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clinic not found")

    # Build base query
    base_query = (
        select(BloodDonationRequest)
        .options(selectinload(BloodDonationRequest.clinic))
        .where(BloodDonationRequest.clinic_id == x_clinic_id)
    )

    if request_status is not None:
        base_query = base_query.where(
            BloodDonationRequest.status == RequestStatus(request_status.value)
        )

    # Count total matching
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply sorting (urgency first, then creation date)
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
                id=clinic.id,
                name=clinic.name,
                city=clinic.city,
                phone=clinic.phone,
            ),
            response_count=response_counts.get(str(req.id), 0),
            is_compatible=None,
        )
        for req in requests
    ]

    LOG.info(
        "List my clinic requests",
        extra={
            "clinic_id": str(x_clinic_id),
            "total": total,
            "returned": len(items),
            "status_filter": request_status.value if request_status else None,
        },
    )

    return PaginatedDonationRequests(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + len(items)) < total,
    )

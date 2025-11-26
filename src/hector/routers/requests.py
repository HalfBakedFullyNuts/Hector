"""Blood donation request endpoints for browsing and responding."""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import case, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models import BloodDonationRequest, Clinic, DogProfile
from ..models.dog_profile import BloodType
from ..models.donation_request import RequestStatus, RequestUrgency
from ..models.donation_response import DonationResponse, ResponseStatus
from ..schemas import (
    BloodTypeEnum,
    ClinicSummary,
    DogSummary,
    DonationRequestBrowseResponse,
    DonationRequestResponse,
    DonationRequestUpdate,
    DonationResponseCreate,
    DonationResponseDetail,
    DonationResponseOut,
    EligibilityCheck,
    OwnerSummary,
    PaginatedDonationRequests,
    RequestStatusEnum,
    RequestUrgencyEnum,
    ResponseStatusEnum,
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


def _check_dog_eligibility(dog: DogProfile) -> EligibilityCheck:
    """
    Check if a dog is eligible for blood donation.

    Eligibility requirements:
    - Dog profile must be active
    - Weight >= 25kg
    - Age between 1-8 years
    - Last donation > 8 weeks ago (if applicable)
    """
    reasons: list[str] = []

    if not dog.is_active:
        reasons.append("Dog profile is not active")

    if dog.weight_kg < 25:
        reasons.append(f"Dog weight ({dog.weight_kg}kg) is below minimum 25kg")

    age = dog.age_years
    if age < 1:
        reasons.append(f"Dog is too young ({age} years, minimum 1 year)")
    elif age > 8:
        reasons.append(f"Dog is too old ({age} years, maximum 8 years)")

    if dog.last_donation_date:
        from datetime import datetime

        weeks_since = (datetime.now().date() - dog.last_donation_date).days // 7
        if weeks_since < 8:
            reasons.append(f"Last donation was {weeks_since} weeks ago (minimum 8 weeks required)")

    return EligibilityCheck(is_eligible=len(reasons) == 0, reasons=reasons)


@router.post(
    "/{request_id}/respond",
    summary="Respond to a donation request",
    response_model=DonationResponseOut,
    status_code=status.HTTP_201_CREATED,
)
async def respond_to_request(
    request_id: UUID,
    response_data: DonationResponseCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    # TODO: Replace with proper auth dependency when T-204 is implemented
    x_user_id: Annotated[UUID, Header(description="User ID (temp auth header)")],
) -> DonationResponseOut:
    """
    Respond to a blood donation request.

    Dog owners can accept or decline donation requests with their dogs.

    Validations:
    - Request must be OPEN
    - Dog must belong to the authenticated user
    - Dog must be eligible for donation (weight, age, last donation date)
    - Cannot respond twice with the same dog to the same request
    """
    # Verify request exists and is open
    request_query = select(BloodDonationRequest).where(BloodDonationRequest.id == request_id)
    request_result = await db.execute(request_query)
    donation_request = request_result.scalar_one_or_none()

    if donation_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Donation request not found"
        )

    if donation_request.status != RequestStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot respond to request with status {donation_request.status.value}",
        )

    # Verify dog exists and belongs to user
    dog_query = select(DogProfile).where(DogProfile.id == response_data.dog_id)
    dog_result = await db.execute(dog_query)
    dog = dog_result.scalar_one_or_none()

    if dog is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dog profile not found")

    if dog.owner_id != x_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only respond with your own dogs",
        )

    # Check dog eligibility (only for ACCEPTED responses)
    if response_data.status == ResponseStatusEnum.ACCEPTED:
        eligibility = _check_dog_eligibility(dog)
        if not eligibility.is_eligible:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Dog is not eligible for donation",
                    "reasons": eligibility.reasons,
                },
            )

    # Create the response
    donation_response = DonationResponse(
        request_id=request_id,
        dog_id=response_data.dog_id,
        owner_id=x_user_id,
        status=ResponseStatus(response_data.status.value),
        response_message=response_data.response_message,
    )

    db.add(donation_response)

    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already responded to this request with this dog",
        )

    LOG.info(
        "Donation response created",
        extra={
            "response_id": str(donation_response.id),
            "request_id": str(request_id),
            "dog_id": str(response_data.dog_id),
            "status": response_data.status.value,
        },
    )

    return DonationResponseOut(
        id=donation_response.id,
        request_id=donation_response.request_id,
        dog_id=donation_response.dog_id,
        owner_id=donation_response.owner_id,
        status=ResponseStatusEnum(donation_response.status.value),
        response_message=donation_response.response_message,
        created_at=donation_response.created_at,
        updated_at=donation_response.updated_at,
    )


@router.get(
    "/{request_id}/responses",
    summary="List responses to a donation request",
    response_model=list[DonationResponseDetail],
)
async def list_request_responses(
    request_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    # TODO: Replace with proper auth dependency when T-204 is implemented
    x_clinic_id: Annotated[UUID, Header(description="Clinic ID (temp auth header)")],
    response_status: Annotated[
        ResponseStatusEnum | None, Query(alias="status", description="Filter by response status")
    ] = None,
) -> list[DonationResponseDetail]:
    """
    List all responses to a specific donation request.

    Only the clinic that owns the request can view responses.
    Includes dog profile and owner contact information.
    """
    # Verify request exists and belongs to clinic
    request_query = select(BloodDonationRequest).where(BloodDonationRequest.id == request_id)
    request_result = await db.execute(request_query)
    donation_request = request_result.scalar_one_or_none()

    if donation_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Donation request not found"
        )

    if donation_request.clinic_id != x_clinic_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view responses to your own clinic's requests",
        )

    # Build query for responses with related data
    responses_query = (
        select(DonationResponse)
        .options(selectinload(DonationResponse.dog), selectinload(DonationResponse.owner))
        .where(DonationResponse.request_id == request_id)
    )

    if response_status is not None:
        responses_query = responses_query.where(
            DonationResponse.status == ResponseStatus(response_status.value)
        )

    responses_query = responses_query.order_by(DonationResponse.created_at.desc())

    result = await db.execute(responses_query)
    responses = result.scalars().all()

    items = [
        DonationResponseDetail(
            id=resp.id,
            request_id=resp.request_id,
            status=ResponseStatusEnum(resp.status.value),
            response_message=resp.response_message,
            created_at=resp.created_at,
            dog=DogSummary(
                id=resp.dog.id,
                name=resp.dog.name,
                breed=resp.dog.breed,
                blood_type=(
                    BloodTypeEnum(resp.dog.blood_type.value) if resp.dog.blood_type else None
                ),
                weight_kg=resp.dog.weight_kg,
                is_eligible=resp.dog.is_eligible_for_donation,
            ),
            owner=OwnerSummary(
                id=resp.owner.id,
                email=resp.owner.email,
            ),
        )
        for resp in responses
    ]

    LOG.info(
        "List request responses",
        extra={
            "request_id": str(request_id),
            "clinic_id": str(x_clinic_id),
            "count": len(items),
            "status_filter": response_status.value if response_status else None,
        },
    )

    return items


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
    # Query request with clinic
    query = (
        select(BloodDonationRequest)
        .options(selectinload(BloodDonationRequest.clinic))
        .where(BloodDonationRequest.id == request_id)
    )
    result = await db.execute(query)
    req = result.scalar_one_or_none()

    if req is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

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


@router.put(
    "/{request_id}",
    summary="Update a donation request",
    response_model=DonationRequestResponse,
)
async def update_request(
    request_id: UUID,
    request_data: DonationRequestUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    # TODO: Replace with proper auth dependency when T-204 is implemented
    x_clinic_id: Annotated[UUID, Header(description="Clinic ID (temp auth header)")],
) -> DonationRequestResponse:
    """
    Update a donation request.

    Only the clinic that owns the request can update it.
    Only OPEN requests can be updated.
    Only provided fields will be updated.
    """
    query = (
        select(BloodDonationRequest)
        .options(selectinload(BloodDonationRequest.clinic))
        .where(BloodDonationRequest.id == request_id)
    )
    result = await db.execute(query)
    req = result.scalar_one_or_none()

    if req is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    if req.clinic_id != x_clinic_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own clinic's requests",
        )

    if req.status != RequestStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot update request with status {req.status.value}",
        )

    # Update only provided fields
    update_data = request_data.model_dump(exclude_unset=True)

    if "blood_type_needed" in update_data:
        update_data["blood_type_needed"] = _map_blood_type(update_data["blood_type_needed"])

    if "urgency" in update_data:
        update_data["urgency"] = _map_urgency(update_data["urgency"])

    for field, value in update_data.items():
        setattr(req, field, value)

    await db.flush()

    LOG.info(
        "Donation request updated",
        extra={
            "request_id": str(request_id),
            "clinic_id": str(x_clinic_id),
            "fields_updated": list(update_data.keys()),
        },
    )

    return DonationRequestResponse(
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
        updated_at=req.updated_at,
        clinic=ClinicSummary(
            id=req.clinic.id,
            name=req.clinic.name,
            city=req.clinic.city,
            phone=req.clinic.phone,
        ),
    )


@router.post(
    "/{request_id}/cancel",
    summary="Cancel a donation request",
    response_model=DonationRequestResponse,
)
async def cancel_request(
    request_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    # TODO: Replace with proper auth dependency when T-204 is implemented
    x_clinic_id: Annotated[UUID, Header(description="Clinic ID (temp auth header)")],
) -> DonationRequestResponse:
    """
    Cancel a donation request.

    Only the clinic that owns the request can cancel it.
    Only OPEN requests can be cancelled.
    """
    query = (
        select(BloodDonationRequest)
        .options(selectinload(BloodDonationRequest.clinic))
        .where(BloodDonationRequest.id == request_id)
    )
    result = await db.execute(query)
    req = result.scalar_one_or_none()

    if req is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    if req.clinic_id != x_clinic_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only cancel your own clinic's requests",
        )

    if req.status != RequestStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel request with status {req.status.value}",
        )

    req.status = RequestStatus.CANCELLED
    await db.flush()

    LOG.info(
        "Donation request cancelled",
        extra={
            "request_id": str(request_id),
            "clinic_id": str(x_clinic_id),
        },
    )

    return DonationRequestResponse(
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
        updated_at=req.updated_at,
        clinic=ClinicSummary(
            id=req.clinic.id,
            name=req.clinic.name,
            city=req.clinic.city,
            phone=req.clinic.phone,
        ),
    )

"""Blood donation request management endpoints."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from hector.auth.dependencies import CurrentUser, RoleChecker
from hector.database import get_db
from hector.models.clinic import Clinic
from hector.models.dog_profile import BloodType, DogProfile
from hector.models.donation_request import BloodDonationRequest, RequestStatus, RequestUrgency
from hector.models.donation_response import DonationResponse, ResponseStatus
from hector.models.user import User, UserRole
from hector.schemas.donation_request import (
    DonationRequestCreate,
    DonationRequestResponse,
    DonationRequestUpdate,
    DonationRequestWithClinic,
    DonationRequestWithResponseCount,
)
from hector.schemas.donation_response import (
    DonationResponseCreate,
    DonationResponseResponse,
    DonationResponseWithDetails,
)

router = APIRouter(prefix="/requests", tags=["donation_requests"])

# Role checker for clinic staff and admin
clinic_staff_or_admin = RoleChecker([UserRole.CLINIC_STAFF, UserRole.ADMIN])


@router.post(
    "",
    response_model=DonationRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create donation request",
    description="Create a new blood donation request (clinic staff only)",
)
async def create_donation_request(
    request: DonationRequestCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> BloodDonationRequest:
    """
    Create a new blood donation request.

    Args:
        request: Donation request data
        current_user: Current authenticated user (must be clinic_staff)
        db: Database session

    Returns:
        Created donation request

    Raises:
        403: User is not clinic staff or not linked to any clinic
        422: Invalid request data
    """
    # Verify user is clinic staff
    if current_user.role != UserRole.CLINIC_STAFF:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only clinic staff can create donation requests",
        )

    # Get user's clinic (staff must be linked to a clinic)

    stmt = select(User).where(User.id == current_user.id).options(selectinload(User.clinics))
    result = await db.execute(stmt)
    user_with_clinics = result.scalar_one()

    if not user_with_clinics.clinics:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be linked to a clinic to create donation requests",
        )

    # Use the first clinic (staff typically belong to one clinic)
    clinic_id = user_with_clinics.clinics[0].id

    # Create new donation request
    new_request = BloodDonationRequest(
        clinic_id=clinic_id,
        created_by_user_id=current_user.id,
        blood_type_needed=request.blood_type_needed,
        volume_ml=request.volume_ml,
        urgency=request.urgency,
        patient_info=request.patient_info,
        needed_by_date=request.needed_by_date,
        status=RequestStatus.OPEN,
    )

    db.add(new_request)
    await db.commit()
    await db.refresh(new_request)

    return new_request


@router.get(
    "",
    response_model=list[DonationRequestWithClinic],
    status_code=status.HTTP_200_OK,
    summary="List all open donation requests",
    description="List all open donation requests with optional filters",
)
async def list_donation_requests(
    status_filter: RequestStatus | None = Query(
        RequestStatus.OPEN, alias="status", description="Filter by status"
    ),
    blood_type: BloodType | None = Query(None, description="Filter by blood type needed"),
    urgency: RequestUrgency | None = Query(None, description="Filter by urgency level"),
    city: str | None = Query(None, description="Filter by clinic city"),
    limit: int = Query(50, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: AsyncSession = Depends(get_db),
) -> list[BloodDonationRequest]:
    """
    List all donation requests with optional filtering.

    Args:
        status_filter: Filter by request status (default: OPEN)
        blood_type: Optional blood type filter
        urgency: Optional urgency filter
        city: Optional clinic city filter
        limit: Maximum number of results
        offset: Number of results to skip
        db: Database session

    Returns:
        List of donation requests with clinic details

    Raises:
        None (public endpoint)
    """
    # Build query with clinic relationship
    stmt = select(BloodDonationRequest).options(selectinload(BloodDonationRequest.clinic))

    # Apply filters
    if status_filter:
        stmt = stmt.where(BloodDonationRequest.status == status_filter)

    if blood_type:
        stmt = stmt.where(BloodDonationRequest.blood_type_needed == blood_type)

    if urgency:
        stmt = stmt.where(BloodDonationRequest.urgency == urgency)

    if city:
        stmt = stmt.join(Clinic).where(Clinic.city == city)

    # Sort by urgency (CRITICAL first) and then by created_at
    # Custom sorting using CASE statement
    stmt = stmt.order_by(
        func.case(
            (BloodDonationRequest.urgency == RequestUrgency.CRITICAL, 0),
            (BloodDonationRequest.urgency == RequestUrgency.URGENT, 1),
            (BloodDonationRequest.urgency == RequestUrgency.ROUTINE, 2),
        ),
        BloodDonationRequest.created_at,
    )

    # Apply pagination
    stmt = stmt.limit(limit).offset(offset)

    result = await db.execute(stmt)
    requests = result.scalars().all()

    return list(requests)


@router.get(
    "/{request_id}",
    response_model=DonationRequestWithResponseCount,
    status_code=status.HTTP_200_OK,
    summary="Get single donation request",
    description="Get details of a specific donation request (public endpoint)",
)
async def get_donation_request(
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get a single donation request by ID.

    Args:
        request_id: Donation request UUID
        db: Database session

    Returns:
        Donation request with clinic details and response count

    Raises:
        404: Request not found
    """
    # Get request with clinic relationship
    stmt = (
        select(BloodDonationRequest)
        .where(BloodDonationRequest.id == request_id)
        .options(selectinload(BloodDonationRequest.clinic))
    )
    result = await db.execute(stmt)
    donation_request = result.scalar_one_or_none()

    if not donation_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donation request not found",
        )

    # Count responses (will implement when DonationResponse is available)
    # For now, return 0
    response_count = 0

    # Return as dict to include response_count
    return {
        **DonationRequestResponse.model_validate(donation_request).model_dump(),
        "response_count": response_count,
    }


@router.put(
    "/{request_id}",
    response_model=DonationRequestResponse,
    status_code=status.HTTP_200_OK,
    summary="Update donation request",
    description="Update a donation request (staff of creating clinic only)",
)
async def update_donation_request(
    request_id: UUID,
    request: DonationRequestUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> BloodDonationRequest:
    """
    Update a donation request.

    Args:
        request_id: Donation request UUID
        request: Updated request data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated donation request

    Raises:
        401: Invalid or expired token
        403: User is not staff of the creating clinic
        404: Request not found
        422: Invalid request data or request is FULFILLED/CANCELLED
    """
    # Get request with clinic relationship
    stmt = (
        select(BloodDonationRequest)
        .where(BloodDonationRequest.id == request_id)
        .options(selectinload(BloodDonationRequest.clinic).selectinload(Clinic.staff))
    )
    result = await db.execute(stmt)
    donation_request = result.scalar_one_or_none()

    if not donation_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donation request not found",
        )

    # Cannot update if FULFILLED or CANCELLED
    if donation_request.status in [RequestStatus.FULFILLED, RequestStatus.CANCELLED]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Cannot update request with status {donation_request.status}",
        )

    # Check authorization: must be staff of the clinic that created the request
    is_staff = any(staff.id == current_user.id for staff in donation_request.clinic.staff)

    if not is_staff:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be staff of the clinic that created this request to update it",
        )

    # Update fields (only if provided)
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(donation_request, field, value)

    await db.commit()
    await db.refresh(donation_request)

    return donation_request


@router.post(
    "/{request_id}/cancel",
    response_model=DonationRequestResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel donation request",
    description="Cancel a donation request (staff of creating clinic only)",
)
async def cancel_donation_request(
    request_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> BloodDonationRequest:
    """
    Cancel a donation request.

    Args:
        request_id: Donation request UUID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Cancelled donation request

    Raises:
        401: Invalid or expired token
        403: User is not staff of the creating clinic
        404: Request not found
        422: Request is already FULFILLED
    """
    # Get request with clinic relationship
    stmt = (
        select(BloodDonationRequest)
        .where(BloodDonationRequest.id == request_id)
        .options(selectinload(BloodDonationRequest.clinic).selectinload(Clinic.staff))
    )
    result = await db.execute(stmt)
    donation_request = result.scalar_one_or_none()

    if not donation_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donation request not found",
        )

    # Cannot cancel if FULFILLED
    if donation_request.status == RequestStatus.FULFILLED:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot cancel a fulfilled request",
        )

    # Check authorization: must be staff of the clinic that created the request
    is_staff = any(staff.id == current_user.id for staff in donation_request.clinic.staff)

    if not is_staff:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be staff of the clinic that created this request to cancel it",
        )

    # Update status to CANCELLED
    donation_request.status = RequestStatus.CANCELLED

    await db.commit()
    await db.refresh(donation_request)

    return donation_request


@router.get(
    "/my-clinic",
    response_model=list[DonationRequestResponse],
    status_code=status.HTTP_200_OK,
    summary="List my clinic's requests",
    description="List all requests created by my clinic (clinic staff only)",
)
async def list_my_clinic_requests(
    status_filter: RequestStatus | None = Query(
        None, alias="status", description="Filter by status"
    ),
    limit: int = Query(50, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: CurrentUser = Depends(clinic_staff_or_admin),
    db: AsyncSession = Depends(get_db),
) -> list[BloodDonationRequest]:
    """
    List all donation requests created by the current user's clinic.

    Args:
        status_filter: Optional status filter
        limit: Maximum number of results
        offset: Number of results to skip
        current_user: Current authenticated user (must be clinic staff)
        db: Database session

    Returns:
        List of donation requests created by user's clinic

    Raises:
        401: Invalid or expired token
        403: User is not clinic staff or not linked to a clinic
    """
    # Get user's clinics

    stmt = select(User).where(User.id == current_user.id).options(selectinload(User.clinics))
    result = await db.execute(stmt)
    user_with_clinics = result.scalar_one()

    if not user_with_clinics.clinics:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be linked to a clinic to view clinic requests",
        )

    # Get clinic IDs
    clinic_ids = [clinic.id for clinic in user_with_clinics.clinics]

    # Build query for requests
    requests_stmt = select(BloodDonationRequest).where(
        BloodDonationRequest.clinic_id.in_(clinic_ids)
    )

    # Apply status filter if provided
    if status_filter:
        requests_stmt = requests_stmt.where(BloodDonationRequest.status == status_filter)

    # Sort by created_at descending
    requests_stmt = requests_stmt.order_by(BloodDonationRequest.created_at.desc())

    # Apply pagination
    requests_stmt = requests_stmt.limit(limit).offset(offset)

    requests_result = await db.execute(requests_stmt)
    requests = requests_result.scalars().all()

    return list(requests)


# ============================================================================
# DONATION RESPONSE ENDPOINTS (Phase 6)
# ============================================================================


@router.post(
    "/{request_id}/respond",
    response_model=DonationResponseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Respond to donation request",
    description="Create a response to a donation request (dog owners only)",
)
async def respond_to_donation_request(
    request_id: UUID,
    response: DonationResponseCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> DonationResponse:
    """
    Respond to a donation request.

    Args:
        request_id: Donation request UUID
        response: Response data (dog_id, status, message)
        current_user: Current authenticated user (must be dog owner)
        db: Database session

    Returns:
        Created donation response

    Raises:
        400: Request is not OPEN
        403: Dog does not belong to user or dog not eligible
        404: Request or dog not found
        409: Already responded with this dog
        422: Invalid request data
    """
    # Verify user is dog owner
    if current_user.role != UserRole.DOG_OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only dog owners can respond to donation requests",
        )

    # Get the donation request
    stmt = select(BloodDonationRequest).where(BloodDonationRequest.id == request_id)
    result = await db.execute(stmt)
    donation_request = result.scalar_one_or_none()

    if not donation_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donation request not found",
        )

    # Check if request is OPEN
    if donation_request.status != RequestStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot respond to request with status {donation_request.status}",
        )

    # Get the dog profile
    dog_stmt = select(DogProfile).where(DogProfile.id == response.dog_id)
    dog_result = await db.execute(dog_stmt)
    dog = dog_result.scalar_one_or_none()

    if not dog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dog profile not found",
        )

    # Verify dog belongs to current user
    if dog.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This dog does not belong to you",
        )

    # Check if dog is eligible (only for ACCEPTED status)
    if response.status == ResponseStatus.ACCEPTED:
        # Check if dog is active
        if not dog.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Dog is not marked as available for donation",
            )

        # Check eligibility criteria from DogProfile model
        if not dog.is_eligible_for_donation:
            reasons = []
            if dog.weight_kg < 25:
                reasons.append("weight must be at least 25kg")
            age = dog.age_years
            if age < 1 or age > 8:
                reasons.append("age must be between 1-8 years")
            if dog.last_donation_date:
                weeks_since = (datetime.now(UTC).date() - dog.last_donation_date).days // 7
                if weeks_since < 8:
                    reasons.append(f"last donation was only {weeks_since} weeks ago (need 8+)")

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Dog is not eligible for donation: {'; '.join(reasons)}",
            )

    # Check if already responded with this dog
    existing_stmt = select(DonationResponse).where(
        and_(
            DonationResponse.request_id == request_id,
            DonationResponse.dog_id == response.dog_id,
        )
    )
    existing_result = await db.execute(existing_stmt)
    existing_response = existing_result.scalar_one_or_none()

    if existing_response:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already responded to this request with this dog",
        )

    # Create the response
    new_response = DonationResponse(
        request_id=request_id,
        dog_id=response.dog_id,
        owner_id=current_user.id,
        status=response.status,
        response_message=response.response_message,
    )

    db.add(new_response)

    try:
        await db.commit()
        await db.refresh(new_response)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already responded to this request with this dog",
        )

    return new_response


@router.get(
    "/{request_id}/responses",
    response_model=list[DonationResponseWithDetails],
    status_code=status.HTTP_200_OK,
    summary="List responses to request",
    description="List all responses to a donation request (clinic staff only)",
)
async def list_request_responses(
    request_id: UUID,
    current_user: CurrentUser,
    status_filter: ResponseStatus | None = Query(
        None, alias="status", description="Filter by status"
    ),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """
    List all responses to a donation request.

    Args:
        request_id: Donation request UUID
        status_filter: Optional status filter
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of responses with dog profile and owner details

    Raises:
        401: Invalid or expired token
        403: User is not staff of the clinic that created the request
        404: Request not found
    """
    # Get the request with clinic and staff
    stmt = (
        select(BloodDonationRequest)
        .where(BloodDonationRequest.id == request_id)
        .options(selectinload(BloodDonationRequest.clinic).selectinload(Clinic.staff))
    )
    result = await db.execute(stmt)
    donation_request = result.scalar_one_or_none()

    if not donation_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donation request not found",
        )

    # Check authorization: must be staff of the clinic that created the request
    is_staff = any(staff.id == current_user.id for staff in donation_request.clinic.staff)

    if not is_staff and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be staff of the clinic that created this request",
        )

    # Build query for responses
    responses_stmt = (
        select(DonationResponse)
        .where(DonationResponse.request_id == request_id)
        .options(
            selectinload(DonationResponse.dog),
            selectinload(DonationResponse.owner),
        )
    )

    # Apply status filter if provided
    if status_filter:
        responses_stmt = responses_stmt.where(DonationResponse.status == status_filter)

    # Sort by created_at
    responses_stmt = responses_stmt.order_by(DonationResponse.created_at)

    responses_result = await db.execute(responses_stmt)
    responses = responses_result.scalars().all()

    # Format response with details
    result_list = []
    for resp in responses:
        result_list.append(
            {
                **DonationResponseResponse.model_validate(resp).model_dump(),
                "dog": resp.dog,
                "owner_email": resp.owner.email,
            }
        )

    return result_list


@router.get(
    "/my-responses",
    response_model=list[DonationResponseWithDetails],
    status_code=status.HTTP_200_OK,
    summary="List my dogs' responses",
    description="List all responses for authenticated user's dogs",
    tags=["donation_responses"],
)
async def list_my_responses(
    current_user: CurrentUser,
    status_filter: ResponseStatus | None = Query(
        None, alias="status", description="Filter by status"
    ),
    limit: int = Query(50, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """
    List all donation responses for the current user's dogs.

    Args:
        status_filter: Optional status filter
        limit: Maximum number of results
        offset: Number of results to skip
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of responses with request and clinic details

    Raises:
        401: Invalid or expired token
    """
    # Build query for responses
    responses_stmt = (
        select(DonationResponse)
        .where(DonationResponse.owner_id == current_user.id)
        .options(
            selectinload(DonationResponse.dog),
            selectinload(DonationResponse.request).selectinload(BloodDonationRequest.clinic),
        )
    )

    # Apply status filter if provided
    if status_filter:
        responses_stmt = responses_stmt.where(DonationResponse.status == status_filter)

    # Sort by created_at descending
    responses_stmt = responses_stmt.order_by(DonationResponse.created_at.desc())

    # Apply pagination
    responses_stmt = responses_stmt.limit(limit).offset(offset)

    responses_result = await db.execute(responses_stmt)
    responses = responses_result.scalars().all()

    # Format response with details
    result_list = []
    for resp in responses:
        result_list.append(
            {
                **DonationResponseResponse.model_validate(resp).model_dump(),
                "dog": resp.dog,
                "owner_email": current_user.email,
                "request": resp.request,
                "clinic": resp.request.clinic if resp.request else None,
            }
        )

    return result_list


@router.post(
    "/responses/{response_id}/complete",
    response_model=DonationResponseResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark response as completed",
    description="Mark a donation response as completed (clinic staff only)",
    tags=["donation_responses"],
)
async def complete_donation_response(
    response_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> DonationResponse:
    """
    Mark a donation response as completed.

    Args:
        response_id: Donation response UUID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated donation response

    Raises:
        400: Response status is not ACCEPTED
        401: Invalid or expired token
        403: User is not staff of the clinic that owns the request
        404: Response not found
    """
    # Get the response with related data
    stmt = (
        select(DonationResponse)
        .where(DonationResponse.id == response_id)
        .options(
            selectinload(DonationResponse.dog),
            selectinload(DonationResponse.request)
            .selectinload(BloodDonationRequest.clinic)
            .selectinload(Clinic.staff),
        )
    )
    result = await db.execute(stmt)
    donation_response = result.scalar_one_or_none()

    if not donation_response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donation response not found",
        )

    # Check if response status is ACCEPTED
    if donation_response.status != ResponseStatus.ACCEPTED:
        detail_msg = (
            f"Can only complete responses with status ACCEPTED "
            f"(current: {donation_response.status})"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail_msg,
        )

    # Check authorization: must be staff of the clinic that owns the request
    is_staff = any(staff.id == current_user.id for staff in donation_response.request.clinic.staff)

    if not is_staff and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be staff of the clinic that created the request",
        )

    # Update response status
    donation_response.status = ResponseStatus.COMPLETED

    # Update dog's last_donation_date
    donation_response.dog.last_donation_date = datetime.now(UTC).date()

    await db.commit()
    await db.refresh(donation_response)

    return donation_response


@router.get(
    "/compatible",
    response_model=list[DonationRequestWithClinic],
    status_code=status.HTTP_200_OK,
    summary="List compatible donation requests",
    description="List donation requests compatible with a specific dog",
)
async def list_compatible_requests(
    dog_id: UUID = Query(..., description="Dog ID to check compatibility for"),
    limit: int = Query(50, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: CurrentUser | None = None,  # Optional auth
    db: AsyncSession = Depends(get_db),
) -> list[BloodDonationRequest]:
    """
    List donation requests compatible with a specific dog.

    Args:
        dog_id: Dog UUID to check compatibility for
        limit: Maximum number of results
        offset: Number of results to skip
        current_user: Optional authenticated user
        db: Database session

    Returns:
        List of compatible donation requests with clinic details

    Raises:
        404: Dog not found
    """
    # Get the dog profile
    stmt = select(DogProfile).where(DogProfile.id == dog_id)
    result = await db.execute(stmt)
    dog = result.scalar_one_or_none()

    if not dog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dog profile not found",
        )

    # Check eligibility
    if not dog.is_eligible_for_donation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dog is not eligible for donation (check weight, age, and last donation date)",
        )

    # Build query for OPEN requests with clinic relationship
    requests_stmt = (
        select(BloodDonationRequest)
        .where(BloodDonationRequest.status == RequestStatus.OPEN)
        .options(selectinload(BloodDonationRequest.clinic))
    )

    # Apply blood type compatibility filter
    if dog.blood_type:
        # Blood type compatibility rules for canines:
        # - DEA 1.1 negative: universal donor (can donate to all)
        # - DEA 1.1 positive: can only donate to DEA 1.1 positive
        # - If request has no blood_type_needed (None), show all
        if dog.blood_type == BloodType.DEA_1_1_NEGATIVE:
            # Universal donor - compatible with all requests
            pass
        elif dog.blood_type == BloodType.DEA_1_1_POSITIVE:
            # Can only donate to DEA 1.1 positive or requests with no blood type specified
            requests_stmt = requests_stmt.where(
                (BloodDonationRequest.blood_type_needed == BloodType.DEA_1_1_POSITIVE)
                | (BloodDonationRequest.blood_type_needed.is_(None))
            )
        else:
            # For other blood types, match same type or no type specified
            requests_stmt = requests_stmt.where(
                (BloodDonationRequest.blood_type_needed == dog.blood_type)
                | (BloodDonationRequest.blood_type_needed.is_(None))
            )

    # Sort by urgency (CRITICAL first) and then by created_at
    requests_stmt = requests_stmt.order_by(
        func.case(
            (BloodDonationRequest.urgency == RequestUrgency.CRITICAL, 0),
            (BloodDonationRequest.urgency == RequestUrgency.URGENT, 1),
            (BloodDonationRequest.urgency == RequestUrgency.ROUTINE, 2),
        ),
        BloodDonationRequest.created_at,
    )

    # Apply pagination
    requests_stmt = requests_stmt.limit(limit).offset(offset)

    requests_result = await db.execute(requests_stmt)
    requests = requests_result.scalars().all()

    return list(requests)

"""Blood donation request management endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from hector.auth.dependencies import CurrentUser, RoleChecker
from hector.database import get_db
from hector.models.clinic import Clinic
from hector.models.dog_profile import BloodType
from hector.models.donation_request import BloodDonationRequest, RequestStatus, RequestUrgency
from hector.models.user import UserRole
from hector.schemas.donation_request import (
    DonationRequestCreate,
    DonationRequestResponse,
    DonationRequestUpdate,
    DonationRequestWithClinic,
    DonationRequestWithResponseCount,
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
    from hector.models.user import User

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
    from hector.models.user import User

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

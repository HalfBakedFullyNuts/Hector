"""Clinic management endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from hector.auth.dependencies import CurrentUser, RoleChecker
from hector.database import get_db
from hector.models.clinic import Clinic
from hector.models.clinic_staff import clinic_staff_association
from hector.models.user import User, UserRole
from hector.schemas.clinic import ClinicCreate, ClinicResponse, ClinicUpdate
from hector.schemas.donation_request import (
    DonationRequestResponse,
    DonationRequestWithCount,
)
from hector.services.clinic_requests import (
    fetch_clinic_requests_with_counts,
    resolve_clinic_ids,
)

router = APIRouter(prefix="/clinics", tags=["clinics"])

# Role checker for clinic staff and admin
clinic_staff_or_admin = RoleChecker([UserRole.CLINIC_STAFF, UserRole.ADMIN])


@router.post(
    "",
    response_model=ClinicResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create clinic profile",
    description="Create a new clinic profile (clinic staff only)",
)
async def create_clinic(
    request: ClinicCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Clinic:
    """
    Create a new clinic profile.

    Args:
        request: Clinic profile data
        current_user: Current authenticated user (must be clinic_staff)
        db: Database session

    Returns:
        Created clinic profile

    Raises:
        403: User is not clinic staff
        422: Invalid request data
    """
    # Verify user is clinic staff
    if current_user.role != UserRole.CLINIC_STAFF:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only clinic staff can create clinic profiles",
        )

    # Create new clinic
    new_clinic = Clinic(
        name=request.name,
        address=request.address,
        city=request.city,
        postal_code=request.postal_code,
        phone=request.phone,
        email=request.email,
        latitude=request.latitude,
        longitude=request.longitude,
        is_approved=False,  # Requires admin approval
    )

    db.add(new_clinic)
    await db.flush()  # Get the clinic ID

    # Link the creating user to the clinic
    stmt = clinic_staff_association.insert().values(
        user_id=current_user.id,
        clinic_id=new_clinic.id,
    )
    await db.execute(stmt)

    await db.commit()
    await db.refresh(new_clinic)

    return new_clinic


@router.get(
    "/my-requests",
    response_model=list[DonationRequestWithCount],
    status_code=status.HTTP_200_OK,
    summary="List my clinic's donation requests",
    description="List all requests created by my clinic, newest first (T-505)",
)
async def list_my_clinic_requests(
    current_user: CurrentUser,
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: AsyncSession = Depends(get_db),
) -> list[DonationRequestWithCount]:
    """
    List all donation requests created by the current staff member's clinic.

    Args:
        current_user: Authenticated user; must be clinic staff or admin
        status_filter: Optional request status filter
        limit: Maximum number of results
        offset: Number of results to skip
        db: Database session

    Returns:
        Requests belonging to the caller's clinic(s)

    Raises:
        403: Caller is not staff of any clinic
    """
    if current_user.role not in (UserRole.CLINIC_STAFF, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only clinic staff can view their clinic's requests",
        )

    clinic_ids = await resolve_clinic_ids(db, current_user.id)
    assert isinstance(clinic_ids, list)
    if not clinic_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be linked to a clinic to view its requests",
        )

    pairs = await fetch_clinic_requests_with_counts(db, clinic_ids, status_filter, limit, offset)

    results: list[DonationRequestWithCount] = []
    for req, cnt in pairs:
        base = DonationRequestResponse.model_validate(req)
        results.append(DonationRequestWithCount(**base.model_dump(), response_count=cnt))
    return results


@router.get(
    "/{clinic_id}",
    response_model=ClinicResponse,
    status_code=status.HTTP_200_OK,
    summary="Get clinic details",
    description="Get details of a specific clinic (public endpoint)",
)
async def get_clinic(
    clinic_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Clinic:
    """
    Get a single clinic by ID.

    Args:
        clinic_id: Clinic UUID
        db: Database session

    Returns:
        Clinic profile

    Raises:
        404: Clinic not found
    """
    stmt = select(Clinic).where(Clinic.id == clinic_id, Clinic.is_active == True)  # noqa: E712
    result = await db.execute(stmt)
    clinic = result.scalar_one_or_none()

    if not clinic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinic not found",
        )

    return clinic


@router.put(
    "/{clinic_id}",
    response_model=ClinicResponse,
    status_code=status.HTTP_200_OK,
    summary="Update clinic profile",
    description="Update a clinic profile (staff of clinic or admin only)",
)
async def update_clinic(
    clinic_id: UUID,
    request: ClinicUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Clinic:
    """
    Update a clinic profile.

    Args:
        clinic_id: Clinic UUID
        request: Updated clinic data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated clinic profile

    Raises:
        401: Invalid or expired token
        403: User is not staff of this clinic and not admin
        404: Clinic not found
        422: Invalid request data
    """
    # Get clinic with staff relationships
    stmt = select(Clinic).where(Clinic.id == clinic_id).options(selectinload(Clinic.staff))
    result = await db.execute(stmt)
    clinic = result.scalar_one_or_none()

    if not clinic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinic not found",
        )

    # Check authorization: must be staff of this clinic or admin
    is_staff = any(staff.id == current_user.id for staff in clinic.staff)
    is_admin = current_user.role == UserRole.ADMIN

    if not (is_staff or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be staff of this clinic or an admin to update it",
        )

    # Update fields (only if provided)
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(clinic, field, value)

    await db.commit()
    await db.refresh(clinic)

    return clinic


@router.get(
    "",
    response_model=list[ClinicResponse],
    status_code=status.HTTP_200_OK,
    summary="List all clinics",
    description="List all approved clinics (admins see all clinics)",
)
async def list_clinics(
    city: str | None = Query(None, description="Filter by city"),
    limit: int = Query(50, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: User | None = Depends(lambda: None),  # Optional authentication
    db: AsyncSession = Depends(get_db),
) -> list[Clinic]:
    """
    List all clinics with optional filtering.

    Args:
        city: Optional city filter
        limit: Maximum number of results
        offset: Number of results to skip
        current_user: Optional authenticated user (for admin access)
        db: Database session

    Returns:
        List of clinics

    Raises:
        None (public endpoint)
    """
    # Try to get current user if authenticated
    from hector.auth.dependencies import get_current_user

    try:
        # Check if we have an Authorization header

        request = db.info.get("request")
        if request:
            current_user = await get_current_user(request, db)
    except Exception:
        current_user = None

    # Build query (soft-deleted clinics are hidden from everyone)
    stmt = select(Clinic).where(Clinic.is_active == True)  # noqa: E712

    # Filter by approval status (only admins see unapproved clinics)
    if not current_user or current_user.role != UserRole.ADMIN:
        stmt = stmt.where(Clinic.is_approved == True)  # noqa: E712

    # Filter by city if provided
    if city:
        stmt = stmt.where(Clinic.city == city)

    # Sort by name alphabetically
    stmt = stmt.order_by(Clinic.name)

    # Apply pagination
    stmt = stmt.limit(limit).offset(offset)

    result = await db.execute(stmt)
    clinics = result.scalars().all()

    return list(clinics)

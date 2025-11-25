"""Admin endpoints for platform management."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from hector.auth.dependencies import CurrentUser, RoleChecker
from hector.database import get_db
from hector.models.clinic import Clinic
from hector.models.dog_profile import DogProfile
from hector.models.donation_request import BloodDonationRequest, RequestStatus
from hector.models.donation_response import DonationResponse, ResponseStatus
from hector.models.user import User, UserRole
from hector.schemas.admin import (
    ApproveClinicRequest,
    DeleteUserRequest,
    PlatformStatistics,
    RejectClinicRequest,
    ToggleUserActiveRequest,
    UserWithCounts,
)
from hector.schemas.clinic import ClinicResponse

router = APIRouter(prefix="/admin", tags=["admin"])

# Admin-only role checker
admin_only = RoleChecker([UserRole.ADMIN])


@router.get(
    "/users",
    response_model=list[UserWithCounts],
    status_code=status.HTTP_200_OK,
    summary="List all users",
    description="List all users with filters and counts (admin only)",
)
async def list_all_users(
    current_user: CurrentUser = Depends(admin_only),
    role_filter: UserRole | None = Query(None, alias="role", description="Filter by role"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    is_verified: bool | None = Query(None, description="Filter by verified status"),
    email: str | None = Query(None, description="Search by email (partial match)"),
    limit: int = Query(50, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """
    List all users with filtering and pagination.

    Args:
        current_user: Current authenticated admin user
        role_filter: Optional role filter
        is_active: Optional active status filter
        is_verified: Optional verified status filter
        email: Optional email search (partial match)
        limit: Maximum number of results
        offset: Number of results to skip
        db: Database session

    Returns:
        List of users with dog and clinic counts

    Raises:
        403: User is not an admin
    """
    # Build query
    stmt = select(User)

    # Apply filters
    if role_filter:
        stmt = stmt.where(User.role == role_filter)
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)
    if is_verified is not None:
        stmt = stmt.where(User.is_verified == is_verified)
    if email:
        stmt = stmt.where(User.email.ilike(f"%{email}%"))

    # Sort by created_at descending
    stmt = stmt.order_by(User.created_at.desc())

    # Apply pagination
    stmt = stmt.limit(limit).offset(offset)

    result = await db.execute(stmt)
    users = result.scalars().all()

    # Get counts for each user
    user_list = []
    for user in users:
        # Count dogs
        dog_count_stmt = select(func.count(DogProfile.id)).where(DogProfile.owner_id == user.id)
        dog_count_result = await db.execute(dog_count_stmt)
        dog_count = dog_count_result.scalar() or 0

        # Count clinics - load clinics and count
        user_with_clinics_stmt = (
            select(User).where(User.id == user.id).options(selectinload(User.clinics))
        )
        user_with_clinics_result = await db.execute(user_with_clinics_stmt)
        user_with_clinics = user_with_clinics_result.scalar_one()
        clinic_count = len(user_with_clinics.clinics)

        user_list.append(
            {
                "id": str(user.id),
                "email": user.email,
                "role": user.role,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
                "dog_count": dog_count,
                "clinic_count": clinic_count,
            }
        )

    return user_list


@router.post(
    "/users/{user_id}/toggle-active",
    response_model=UserWithCounts,
    status_code=status.HTTP_200_OK,
    summary="Toggle user active status",
    description="Enable or disable a user account (admin only)",
)
async def toggle_user_active(
    user_id: UUID,
    request: ToggleUserActiveRequest,
    current_user: CurrentUser = Depends(admin_only),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Toggle a user's active status.

    Args:
        user_id: User UUID
        request: Optional reason for toggle
        current_user: Current authenticated admin user
        db: Database session

    Returns:
        Updated user with counts

    Raises:
        403: User is not an admin
        404: User not found
    """
    # Get user
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Toggle active status
    user.is_active = not user.is_active

    # TODO: Create audit log entry with reason
    # For now, we'll just log the reason in the commit message
    await db.commit()
    await db.refresh(user)

    # Get counts
    dog_count_stmt = select(func.count(DogProfile.id)).where(DogProfile.owner_id == user.id)
    dog_count_result = await db.execute(dog_count_stmt)
    dog_count = dog_count_result.scalar() or 0

    user_with_clinics_stmt = (
        select(User).where(User.id == user.id).options(selectinload(User.clinics))
    )
    user_with_clinics_result = await db.execute(user_with_clinics_stmt)
    user_with_clinics = user_with_clinics_result.scalar_one()
    clinic_count = len(user_with_clinics.clinics)

    return {
        "id": str(user.id),
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "dog_count": dog_count,
        "clinic_count": clinic_count,
    }


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user account",
    description="Soft delete a user account (admin only)",
)
async def delete_user(
    user_id: UUID,
    request: DeleteUserRequest,
    current_user: CurrentUser = Depends(admin_only),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Soft delete a user account.

    Args:
        user_id: User UUID
        request: Confirmation with user_id and optional reason
        current_user: Current authenticated admin user
        db: Database session

    Returns:
        None (204 No Content)

    Raises:
        400: User ID confirmation mismatch or trying to delete another admin
        403: User is not an admin
        404: User not found
    """
    # Verify user_id confirmation matches
    if str(user_id) != request.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID confirmation does not match",
        )

    # Get user
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Cannot delete other admins
    if user.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete admin users",
        )

    # Soft delete: set is_active to False
    # This preserves all historical data and relationships
    user.is_active = False

    # Also mark all their dogs as inactive
    dogs_stmt = select(DogProfile).where(DogProfile.owner_id == user_id)
    dogs_result = await db.execute(dogs_stmt)
    dogs = dogs_result.scalars().all()

    for dog in dogs:
        dog.is_active = False

    # TODO: Create audit log entry with reason
    await db.commit()


@router.get(
    "/stats",
    response_model=PlatformStatistics,
    status_code=status.HTTP_200_OK,
    summary="View platform statistics",
    description="View platform-wide statistics (admin only)",
)
async def get_platform_statistics(
    current_user: CurrentUser = Depends(admin_only),
    start_date: datetime | None = Query(None, description="Start date for filtering"),
    end_date: datetime | None = Query(None, description="End date for filtering"),
    db: AsyncSession = Depends(get_db),
) -> PlatformStatistics:
    """
    Get platform-wide statistics.

    Args:
        current_user: Current authenticated admin user
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering
        db: Database session

    Returns:
        Platform statistics

    Raises:
        403: User is not an admin
    """
    # Total users
    total_users_stmt = select(func.count(User.id))
    total_users_result = await db.execute(total_users_stmt)
    total_users = total_users_result.scalar() or 0

    # Users by role
    users_by_role = {}
    for role in UserRole:
        role_count_stmt = select(func.count(User.id)).where(User.role == role)
        role_count_result = await db.execute(role_count_stmt)
        users_by_role[role.value] = role_count_result.scalar() or 0

    # Total dogs
    total_dogs_stmt = select(func.count(DogProfile.id))
    total_dogs_result = await db.execute(total_dogs_stmt)
    total_dogs = total_dogs_result.scalar() or 0

    # Total clinics
    total_clinics_stmt = select(func.count(Clinic.id))
    total_clinics_result = await db.execute(total_clinics_stmt)
    total_clinics = total_clinics_result.scalar() or 0

    # Approved clinics
    approved_clinics_stmt = select(func.count(Clinic.id)).where(Clinic.is_approved == True)  # noqa: E712
    approved_clinics_result = await db.execute(approved_clinics_stmt)
    approved_clinics = approved_clinics_result.scalar() or 0

    # Pending clinics
    pending_clinics = total_clinics - approved_clinics

    # Total requests
    total_requests_stmt = select(func.count(BloodDonationRequest.id))
    total_requests_result = await db.execute(total_requests_stmt)
    total_requests = total_requests_result.scalar() or 0

    # Requests by status
    requests_by_status = {}
    for req_status in RequestStatus:
        status_count_stmt = select(func.count(BloodDonationRequest.id)).where(
            BloodDonationRequest.status == req_status
        )
        status_count_result = await db.execute(status_count_stmt)
        requests_by_status[req_status.value] = status_count_result.scalar() or 0

    # Total responses
    total_responses_stmt = select(func.count(DonationResponse.id))
    total_responses_result = await db.execute(total_responses_stmt)
    total_responses = total_responses_result.scalar() or 0

    # Responses by status
    responses_by_status = {}
    for resp_status in ResponseStatus:
        status_count_stmt = select(func.count(DonationResponse.id)).where(
            DonationResponse.status == resp_status
        )
        status_count_result = await db.execute(status_count_stmt)
        responses_by_status[resp_status.value] = status_count_result.scalar() or 0

    # Successful donations this month
    now = datetime.now(UTC)
    first_day_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    successful_donations_stmt = select(func.count(DonationResponse.id)).where(
        and_(
            DonationResponse.status == ResponseStatus.COMPLETED,
            DonationResponse.updated_at >= first_day_of_month,
        )
    )
    successful_donations_result = await db.execute(successful_donations_stmt)
    successful_donations_this_month = successful_donations_result.scalar() or 0

    return PlatformStatistics(
        total_users=total_users,
        users_by_role=users_by_role,
        total_dogs=total_dogs,
        total_clinics=total_clinics,
        approved_clinics=approved_clinics,
        pending_clinics=pending_clinics,
        total_requests=total_requests,
        requests_by_status=requests_by_status,
        total_responses=total_responses,
        responses_by_status=responses_by_status,
        successful_donations_this_month=successful_donations_this_month,
    )


@router.post(
    "/clinics/{clinic_id}/approve",
    response_model=ClinicResponse,
    status_code=status.HTTP_200_OK,
    summary="Approve clinic",
    description="Approve a clinic registration (admin only)",
)
async def approve_clinic(
    clinic_id: UUID,
    request: ApproveClinicRequest,
    current_user: CurrentUser = Depends(admin_only),
    db: AsyncSession = Depends(get_db),
) -> Clinic:
    """
    Approve a clinic registration.

    Args:
        clinic_id: Clinic UUID
        request: Optional approval notes
        current_user: Current authenticated admin user
        db: Database session

    Returns:
        Updated clinic

    Raises:
        403: User is not an admin
        404: Clinic not found
    """
    # Get clinic
    stmt = select(Clinic).where(Clinic.id == clinic_id)
    result = await db.execute(stmt)
    clinic = result.scalar_one_or_none()

    if not clinic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinic not found",
        )

    # Set is_approved to True
    clinic.is_approved = True

    # TODO: Send email notification to clinic staff
    # TODO: Create audit log entry with approval notes

    await db.commit()
    await db.refresh(clinic)

    return clinic


@router.post(
    "/clinics/{clinic_id}/reject",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Reject clinic",
    description="Reject a clinic registration (admin only)",
)
async def reject_clinic(
    clinic_id: UUID,
    request: RejectClinicRequest,
    current_user: CurrentUser = Depends(admin_only),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Reject a clinic registration.

    Args:
        clinic_id: Clinic UUID
        request: Rejection reason
        current_user: Current authenticated admin user
        db: Database session

    Returns:
        None (204 No Content)

    Raises:
        403: User is not an admin
        404: Clinic not found
    """
    # Get clinic
    stmt = select(Clinic).where(Clinic.id == clinic_id)
    result = await db.execute(stmt)
    clinic = result.scalar_one_or_none()

    if not clinic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinic not found",
        )

    # Soft delete: we'll just delete it from the database for now
    # In production, you might want to keep a record of rejected clinics
    await db.delete(clinic)

    # TODO: Send email notification to clinic staff with rejection reason
    # TODO: Create audit log entry with rejection reason

    await db.commit()

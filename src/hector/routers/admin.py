"""Admin endpoints for platform management."""

import logging
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import get_current_active_user, require_admin
from ..database import get_db
from ..models import BloodDonationRequest, Clinic, DogProfile, User
from ..models.donation_request import RequestStatus
from ..models.donation_response import DonationResponse, ResponseStatus
from ..models.user import UserRole

LOG = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


# =============================================================================
# Schemas
# =============================================================================


class UserAdminOut(BaseModel):
    """User output schema for admin views."""

    id: UUID
    email: str
    role: str
    is_active: bool
    is_verified: bool
    created_at: Any  # datetime
    dog_count: int = 0
    clinic_id: UUID | None = None


class PaginatedUsers(BaseModel):
    """Paginated users response."""

    items: list[UserAdminOut]
    total: int
    limit: int
    offset: int
    has_more: bool


class ClinicAdminOut(BaseModel):
    """Clinic output schema for admin views."""

    id: UUID
    name: str
    address: str
    city: str
    email: str
    phone: str
    is_approved: bool
    created_at: Any  # datetime


class PaginatedClinicsAdmin(BaseModel):
    """Paginated clinics response for admin."""

    items: list[ClinicAdminOut]
    total: int
    limit: int
    offset: int
    has_more: bool


class PlatformStats(BaseModel):
    """Platform statistics response."""

    total_users: int
    users_by_role: dict[str, int]
    total_dogs: int
    available_dogs: int
    total_clinics: int
    approved_clinics: int
    pending_clinics: int
    total_requests: int
    requests_by_status: dict[str, int]
    total_responses: int
    completed_donations: int


class ToggleActiveRequest(BaseModel):
    """Request body for toggling user active status."""

    reason: str | None = Field(default=None, description="Optional reason for change")


class ApprovalRequest(BaseModel):
    """Request body for clinic approval/rejection."""

    notes: str | None = Field(default=None, description="Optional notes")


# =============================================================================
# User Management Endpoints (T-700, T-701, T-702)
# =============================================================================


@router.get(
    "/users",
    summary="List all users (admin only)",
    response_model=PaginatedUsers,
    dependencies=[Depends(require_admin)],
)
async def list_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    role: Annotated[str | None, Query(description="Filter by role")] = None,
    is_active: Annotated[bool | None, Query(description="Filter by active status")] = None,
    email_search: Annotated[str | None, Query(description="Search by email")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PaginatedUsers:
    """
    List all users with filtering and pagination.

    Admin only endpoint.
    """
    base_query = select(User)

    if role:
        base_query = base_query.where(User.role == UserRole(role))

    if is_active is not None:
        base_query = base_query.where(User.is_active == is_active)

    if email_search:
        base_query = base_query.where(User.email.ilike(f"%{email_search}%"))

    # Count total
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    base_query = base_query.order_by(User.created_at.desc())
    base_query = base_query.limit(limit).offset(offset)

    result = await db.execute(base_query)
    users = result.scalars().all()

    # Get dog counts for each user
    user_ids = [u.id for u in users]
    dog_counts: dict[str, int] = {}
    if user_ids:
        dog_count_query = (
            select(DogProfile.owner_id, func.count(DogProfile.id))
            .where(DogProfile.owner_id.in_(user_ids))
            .group_by(DogProfile.owner_id)
        )
        dog_count_result = await db.execute(dog_count_query)
        dog_counts = {str(row[0]): row[1] for row in dog_count_result.all()}

    items = [
        UserAdminOut(
            id=u.id,
            email=u.email,
            role=u.role.value,
            is_active=u.is_active,
            is_verified=u.is_verified,
            created_at=u.created_at,
            dog_count=dog_counts.get(str(u.id), 0),
            clinic_id=None,  # TODO: Add clinic association lookup
        )
        for u in users
    ]

    return PaginatedUsers(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + len(items)) < total,
    )


@router.post(
    "/users/{user_id}/toggle-active",
    summary="Enable or disable a user account",
    response_model=UserAdminOut,
    dependencies=[Depends(require_admin)],
)
async def toggle_user_active(
    user_id: UUID,
    request_data: ToggleActiveRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserAdminOut:
    """
    Toggle a user's active status.

    Admin only endpoint. Cannot disable own account.
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot disable your own account",
        )

    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.is_active = not user.is_active
    await db.flush()

    LOG.info(
        "User active status toggled",
        extra={
            "user_id": str(user_id),
            "is_active": user.is_active,
            "toggled_by": str(current_user.id),
            "reason": request_data.reason,
        },
    )

    return UserAdminOut(
        id=user.id,
        email=user.email,
        role=user.role.value,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
    )


@router.delete(
    "/users/{user_id}",
    summary="Soft delete a user account",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
async def delete_user(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> None:
    """
    Soft delete a user account.

    Sets is_active to False. Preserves historical data.
    Cannot delete admins or own account.
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete admin accounts",
        )

    # Soft delete user and their dogs
    user.is_active = False

    # Also deactivate user's dogs
    dog_update_query = select(DogProfile).where(DogProfile.owner_id == user_id)
    dog_result = await db.execute(dog_update_query)
    for dog in dog_result.scalars().all():
        dog.is_active = False

    await db.flush()

    LOG.info(
        "User soft deleted",
        extra={
            "user_id": str(user_id),
            "deleted_by": str(current_user.id),
        },
    )


# =============================================================================
# Platform Statistics (T-703)
# =============================================================================


@router.get(
    "/stats",
    summary="Get platform statistics",
    response_model=PlatformStats,
    dependencies=[Depends(require_admin)],
)
async def get_platform_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlatformStats:
    """
    Get comprehensive platform statistics.

    Admin only endpoint.
    """
    # Total users
    total_users_result = await db.execute(select(func.count(User.id)))
    total_users = total_users_result.scalar() or 0

    # Users by role
    role_counts_query = select(User.role, func.count(User.id)).group_by(User.role)
    role_counts_result = await db.execute(role_counts_query)
    users_by_role = {row[0].value: row[1] for row in role_counts_result.all()}

    # Dogs
    total_dogs_result = await db.execute(
        select(func.count(DogProfile.id)).where(DogProfile.is_active.is_(True))
    )
    total_dogs = total_dogs_result.scalar() or 0

    # Count dogs that are active (available dogs = active dogs for now)
    # Full eligibility check requires property evaluation which can't be done in SQL
    available_dogs = total_dogs  # All active dogs are potentially available

    # Clinics
    total_clinics_result = await db.execute(select(func.count(Clinic.id)))
    total_clinics = total_clinics_result.scalar() or 0

    approved_clinics_result = await db.execute(
        select(func.count(Clinic.id)).where(Clinic.is_approved.is_(True))
    )
    approved_clinics = approved_clinics_result.scalar() or 0
    pending_clinics = total_clinics - approved_clinics

    # Requests
    total_requests_result = await db.execute(select(func.count(BloodDonationRequest.id)))
    total_requests = total_requests_result.scalar() or 0

    request_status_query = select(
        BloodDonationRequest.status, func.count(BloodDonationRequest.id)
    ).group_by(BloodDonationRequest.status)
    request_status_result = await db.execute(request_status_query)
    requests_by_status = {row[0].value: row[1] for row in request_status_result.all()}

    # Responses
    total_responses_result = await db.execute(select(func.count(DonationResponse.id)))
    total_responses = total_responses_result.scalar() or 0

    completed_donations_result = await db.execute(
        select(func.count(DonationResponse.id)).where(
            DonationResponse.status == ResponseStatus.COMPLETED
        )
    )
    completed_donations = completed_donations_result.scalar() or 0

    return PlatformStats(
        total_users=total_users,
        users_by_role=users_by_role,
        total_dogs=total_dogs,
        available_dogs=available_dogs,
        total_clinics=total_clinics,
        approved_clinics=approved_clinics,
        pending_clinics=pending_clinics,
        total_requests=total_requests,
        requests_by_status=requests_by_status,
        total_responses=total_responses,
        completed_donations=completed_donations,
    )


# =============================================================================
# Clinic Approval (T-704)
# =============================================================================


@router.get(
    "/clinics",
    summary="List all clinics for admin",
    response_model=PaginatedClinicsAdmin,
    dependencies=[Depends(require_admin)],
)
async def list_clinics_admin(
    db: Annotated[AsyncSession, Depends(get_db)],
    is_approved: Annotated[bool | None, Query(description="Filter by approval status")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PaginatedClinicsAdmin:
    """
    List all clinics with optional filtering.

    Admin only endpoint. Shows all clinics including unapproved.
    """
    base_query = select(Clinic)

    if is_approved is not None:
        base_query = base_query.where(Clinic.is_approved == is_approved)

    # Count total
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    base_query = base_query.order_by(Clinic.created_at.desc())
    base_query = base_query.limit(limit).offset(offset)

    result = await db.execute(base_query)
    clinics = result.scalars().all()

    items = [
        ClinicAdminOut(
            id=c.id,
            name=c.name,
            address=c.address,
            city=c.city,
            email=c.email,
            phone=c.phone,
            is_approved=c.is_approved,
            created_at=c.created_at,
        )
        for c in clinics
    ]

    return PaginatedClinicsAdmin(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + len(items)) < total,
    )


@router.post(
    "/clinics/{clinic_id}/approve",
    summary="Approve a clinic",
    response_model=ClinicAdminOut,
    dependencies=[Depends(require_admin)],
)
async def approve_clinic(
    clinic_id: UUID,
    request_data: ApprovalRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> ClinicAdminOut:
    """
    Approve a clinic registration.

    Admin only endpoint. Approved clinics can create donation requests.
    """
    query = select(Clinic).where(Clinic.id == clinic_id)
    result = await db.execute(query)
    clinic = result.scalar_one_or_none()

    if clinic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clinic not found")

    if clinic.is_approved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Clinic is already approved",
        )

    clinic.is_approved = True
    await db.flush()

    LOG.info(
        "Clinic approved",
        extra={
            "clinic_id": str(clinic_id),
            "approved_by": str(current_user.id),
            "notes": request_data.notes,
        },
    )

    return ClinicAdminOut(
        id=clinic.id,
        name=clinic.name,
        address=clinic.address,
        city=clinic.city,
        email=clinic.email,
        phone=clinic.phone,
        is_approved=clinic.is_approved,
        created_at=clinic.created_at,
    )


@router.post(
    "/clinics/{clinic_id}/reject",
    summary="Reject a clinic",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
async def reject_clinic(
    clinic_id: UUID,
    request_data: ApprovalRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> None:
    """
    Reject a clinic registration.

    Admin only endpoint. Rejected clinics are soft-deleted.
    """
    query = select(Clinic).where(Clinic.id == clinic_id)
    result = await db.execute(query)
    clinic = result.scalar_one_or_none()

    if clinic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clinic not found")

    # Cancel any open requests from this clinic
    requests_query = select(BloodDonationRequest).where(
        BloodDonationRequest.clinic_id == clinic_id,
        BloodDonationRequest.status == RequestStatus.OPEN,
    )
    requests_result = await db.execute(requests_query)
    for req in requests_result.scalars().all():
        req.status = RequestStatus.CANCELLED

    # Soft delete by setting is_approved to False
    clinic.is_approved = False
    await db.flush()

    LOG.info(
        "Clinic rejected",
        extra={
            "clinic_id": str(clinic_id),
            "rejected_by": str(current_user.id),
            "notes": request_data.notes,
        },
    )

"""Dog profile endpoints for CRUD operations."""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import DogProfile
from ..models.dog_profile import BloodType, DogSex
from ..schemas import BloodTypeEnum
from ..schemas.dog_profile import (
    DogProfileCreate,
    DogProfileOut,
    DogProfileUpdate,
    DogSexEnum,
    PaginatedDogProfiles,
)

LOG = logging.getLogger(__name__)

router = APIRouter(prefix="/dogs", tags=["dogs"])


def _map_blood_type(blood_type: BloodTypeEnum | None) -> BloodType | None:
    """Map schema blood type enum to model enum."""
    if blood_type is None:
        return None
    return BloodType(blood_type.value)


def _map_sex(sex: DogSexEnum) -> DogSex:
    """Map schema sex enum to model enum."""
    return DogSex(sex.value)


def _dog_to_response(dog: DogProfile) -> DogProfileOut:
    """Convert a DogProfile model to response schema."""
    return DogProfileOut(
        id=dog.id,
        owner_id=dog.owner_id,
        name=dog.name,
        breed=dog.breed,
        date_of_birth=dog.date_of_birth,
        weight_kg=dog.weight_kg,
        sex=DogSexEnum(dog.sex.value),
        blood_type=BloodTypeEnum(dog.blood_type.value) if dog.blood_type else None,
        last_donation_date=dog.last_donation_date,
        medical_notes=dog.medical_notes,
        vaccination_status=dog.vaccination_status,
        is_active=dog.is_active,
        is_eligible=dog.is_eligible_for_donation,
        age_years=dog.age_years,
        created_at=dog.created_at,
        updated_at=dog.updated_at,
    )


@router.post(
    "",
    summary="Create a dog profile",
    response_model=DogProfileOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_dog_profile(
    dog_data: DogProfileCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    x_user_id: Annotated[UUID, Header(description="User ID (temp auth header)")],
) -> DogProfileOut:
    """
    Create a new dog profile for the authenticated user.

    The dog profile will be linked to the current user's account.
    Dogs must meet eligibility criteria to donate: weight >= 25kg, age 1-8 years.
    """
    dog = DogProfile(
        owner_id=x_user_id,
        name=dog_data.name,
        breed=dog_data.breed,
        date_of_birth=dog_data.date_of_birth,
        weight_kg=dog_data.weight_kg,
        sex=_map_sex(dog_data.sex),
        blood_type=_map_blood_type(dog_data.blood_type),
        medical_notes=dog_data.medical_notes,
        vaccination_status=dog_data.vaccination_status,
        is_active=True,
    )

    db.add(dog)
    await db.flush()

    LOG.info(
        "Dog profile created",
        extra={
            "dog_id": str(dog.id),
            "owner_id": str(x_user_id),
            "name": dog.name,
        },
    )

    return _dog_to_response(dog)


@router.get(
    "",
    summary="List my dogs",
    response_model=PaginatedDogProfiles,
)
async def list_my_dogs(
    db: Annotated[AsyncSession, Depends(get_db)],
    x_user_id: Annotated[UUID, Header(description="User ID (temp auth header)")],
    limit: Annotated[int, Query(ge=1, le=100, description="Maximum items per page")] = 20,
    offset: Annotated[int, Query(ge=0, description="Number of items to skip")] = 0,
    include_inactive: Annotated[bool, Query(description="Include inactive profiles")] = False,
) -> PaginatedDogProfiles:
    """
    List all dog profiles belonging to the authenticated user.

    By default, only active profiles are returned.
    """
    # Build base query
    base_query = select(DogProfile).where(DogProfile.owner_id == x_user_id)

    if not include_inactive:
        base_query = base_query.where(DogProfile.is_active.is_(True))

    # Count total matching
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply ordering and pagination
    base_query = base_query.order_by(DogProfile.created_at.desc())
    base_query = base_query.limit(limit).offset(offset)

    # Execute query
    result = await db.execute(base_query)
    dogs = result.scalars().all()

    items = [_dog_to_response(dog) for dog in dogs]

    LOG.info(
        "List my dogs",
        extra={
            "owner_id": str(x_user_id),
            "total": total,
            "returned": len(items),
        },
    )

    return PaginatedDogProfiles(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + len(items)) < total,
    )


@router.get(
    "/{dog_id}",
    summary="Get a single dog profile",
    response_model=DogProfileOut,
)
async def get_dog_profile(
    dog_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    x_user_id: Annotated[UUID, Header(description="User ID (temp auth header)")],
) -> DogProfileOut:
    """
    Get details of a specific dog profile.

    Users can only view their own dog profiles.
    """
    query = select(DogProfile).where(DogProfile.id == dog_id)
    result = await db.execute(query)
    dog = result.scalar_one_or_none()

    if dog is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dog profile not found")

    if dog.owner_id != x_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own dog profiles",
        )

    return _dog_to_response(dog)


@router.put(
    "/{dog_id}",
    summary="Update a dog profile",
    response_model=DogProfileOut,
)
async def update_dog_profile(
    dog_id: UUID,
    dog_data: DogProfileUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    x_user_id: Annotated[UUID, Header(description="User ID (temp auth header)")],
) -> DogProfileOut:
    """
    Update a dog profile (partial updates allowed).

    Users can only update their own dog profiles.
    """
    query = select(DogProfile).where(DogProfile.id == dog_id)
    result = await db.execute(query)
    dog = result.scalar_one_or_none()

    if dog is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dog profile not found")

    if dog.owner_id != x_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own dog profiles",
        )

    # Apply updates (only non-None values)
    update_data = dog_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            if field == "blood_type":
                setattr(dog, field, _map_blood_type(value))
            elif field == "sex":
                setattr(dog, field, _map_sex(value))
            else:
                setattr(dog, field, value)

    await db.flush()

    LOG.info(
        "Dog profile updated",
        extra={
            "dog_id": str(dog_id),
            "owner_id": str(x_user_id),
            "updated_fields": list(update_data.keys()),
        },
    )

    return _dog_to_response(dog)


@router.delete(
    "/{dog_id}",
    summary="Delete a dog profile",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_dog_profile(
    dog_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    x_user_id: Annotated[UUID, Header(description="User ID (temp auth header)")],
) -> None:
    """
    Soft-delete a dog profile by setting is_active to False.

    This preserves historical donation responses.
    Users can only delete their own dog profiles.
    """
    query = select(DogProfile).where(DogProfile.id == dog_id)
    result = await db.execute(query)
    dog = result.scalar_one_or_none()

    if dog is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dog profile not found")

    if dog.owner_id != x_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own dog profiles",
        )

    dog.is_active = False
    await db.flush()

    LOG.info(
        "Dog profile deleted (soft)",
        extra={
            "dog_id": str(dog_id),
            "owner_id": str(x_user_id),
        },
    )


@router.post(
    "/{dog_id}/toggle-availability",
    summary="Toggle dog availability for donation",
    response_model=DogProfileOut,
)
async def toggle_dog_availability(
    dog_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    x_user_id: Annotated[UUID, Header(description="User ID (temp auth header)")],
) -> DogProfileOut:
    """
    Toggle a dog's availability for donation.

    This is a convenience endpoint to quickly mark a dog as available or unavailable.
    Note: This toggles the is_active field for now. In a full implementation,
    a separate is_available_for_donation field would be used.
    """
    query = select(DogProfile).where(DogProfile.id == dog_id)
    result = await db.execute(query)
    dog = result.scalar_one_or_none()

    if dog is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dog profile not found")

    if dog.owner_id != x_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own dog profiles",
        )

    dog.is_active = not dog.is_active
    await db.flush()

    LOG.info(
        "Dog availability toggled",
        extra={
            "dog_id": str(dog_id),
            "owner_id": str(x_user_id),
            "new_status": dog.is_active,
        },
    )

    return _dog_to_response(dog)

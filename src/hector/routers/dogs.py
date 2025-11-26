"""Dog profile management endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hector.auth.dependencies import CurrentUser
from hector.database import get_db
from hector.models.dog_profile import DogProfile
from hector.schemas.dog import (
    DogAvailabilityUpdate,
    DogProfileCreate,
    DogProfileResponse,
    DogProfileUpdate,
)

router = APIRouter(prefix="/dogs", tags=["dogs"])


@router.post(
    "",
    response_model=DogProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create dog profile",
    description="Create a new dog profile for the authenticated user",
)
async def create_dog_profile(
    request: DogProfileCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> DogProfile:
    """
    Create a new dog profile.

    Args:
        request: Dog profile data
        current_user: Current authenticated user (owner)
        db: Database session

    Returns:
        Created dog profile

    Raises:
        422: Invalid request data (validation errors)
    """
    # Create new dog profile with auto-set owner_id
    new_dog = DogProfile(
        owner_id=current_user.id,
        name=request.name,
        breed=request.breed,
        date_of_birth=request.date_of_birth,
        weight_kg=request.weight_kg,
        sex=request.sex,
        blood_type=request.blood_type,
        last_donation_date=request.last_donation_date,
        medical_notes=request.medical_notes,
        vaccination_status=request.vaccination_status,
        is_active=True,
    )

    db.add(new_dog)
    await db.commit()
    await db.refresh(new_dog)

    return new_dog


@router.get(
    "",
    response_model=list[DogProfileResponse],
    status_code=status.HTTP_200_OK,
    summary="List my dogs",
    description="Get all dog profiles for the authenticated user",
)
async def list_my_dogs(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[DogProfile]:
    """
    List all dog profiles owned by the current user.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of dog profiles owned by the user (may be empty)

    Raises:
        401: Invalid or expired token
    """
    stmt = select(DogProfile).where(DogProfile.owner_id == current_user.id)
    result = await db.execute(stmt)
    dogs = result.scalars().all()

    return list(dogs)


@router.get(
    "/{dog_id}",
    response_model=DogProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get dog profile",
    description="Get a single dog profile by ID (must be owned by authenticated user)",
)
async def get_dog_profile(
    dog_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> DogProfile:
    """
    Get a single dog profile by ID.

    Args:
        dog_id: Dog profile UUID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Dog profile

    Raises:
        401: Invalid or expired token
        404: Dog not found or not owned by current user
    """
    stmt = select(DogProfile).where(
        DogProfile.id == dog_id,
        DogProfile.owner_id == current_user.id,
    )
    result = await db.execute(stmt)
    dog = result.scalar_one_or_none()

    if not dog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dog profile not found",
        )

    return dog


@router.patch(
    "/{dog_id}",
    response_model=DogProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Update dog profile",
    description="Update a dog profile (must be owned by authenticated user)",
)
async def update_dog_profile(
    dog_id: UUID,
    request: DogProfileUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> DogProfile:
    """
    Update a dog profile.

    Args:
        dog_id: Dog profile UUID
        request: Updated dog profile data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated dog profile

    Raises:
        401: Invalid or expired token
        404: Dog not found or not owned by current user
        422: Invalid request data
    """
    # Get dog profile
    stmt = select(DogProfile).where(
        DogProfile.id == dog_id,
        DogProfile.owner_id == current_user.id,
    )
    result = await db.execute(stmt)
    dog = result.scalar_one_or_none()

    if not dog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dog profile not found",
        )

    # Update fields (only if provided)
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(dog, field, value)

    await db.commit()
    await db.refresh(dog)

    return dog


@router.delete(
    "/{dog_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete dog profile",
    description="Delete a dog profile (must be owned by authenticated user)",
)
async def delete_dog_profile(
    dog_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a dog profile.

    Args:
        dog_id: Dog profile UUID
        current_user: Current authenticated user
        db: Database session

    Returns:
        None (204 No Content)

    Raises:
        401: Invalid or expired token
        404: Dog not found or not owned by current user
    """
    # Get dog profile
    stmt = select(DogProfile).where(
        DogProfile.id == dog_id,
        DogProfile.owner_id == current_user.id,
    )
    result = await db.execute(stmt)
    dog = result.scalar_one_or_none()

    if not dog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dog profile not found",
        )

    # Delete the dog profile
    await db.delete(dog)
    await db.commit()


@router.patch(
    "/{dog_id}/availability",
    response_model=DogProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Update dog availability",
    description="Mark dog as available or unavailable for donation",
)
async def update_dog_availability(
    dog_id: UUID,
    request: DogAvailabilityUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> DogProfile:
    """
    Update dog availability status.

    Args:
        dog_id: Dog profile UUID
        request: Availability update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated dog profile

    Raises:
        401: Invalid or expired token
        404: Dog not found or not owned by current user
        422: Invalid request data
    """
    # Get dog profile
    stmt = select(DogProfile).where(
        DogProfile.id == dog_id,
        DogProfile.owner_id == current_user.id,
    )
    result = await db.execute(stmt)
    dog = result.scalar_one_or_none()

    if not dog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dog profile not found",
        )

    # Update availability
    dog.is_active = request.is_active

    await db.commit()
    await db.refresh(dog)

    return dog

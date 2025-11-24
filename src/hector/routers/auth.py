"""Authentication and user management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from hector.auth.password import hash_password
from hector.database import get_db
from hector.models.user import User
from hector.schemas.auth import UserRegisterRequest, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with email, password, and role",
)
async def register_user(
    request: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Register a new user account.

    Args:
        request: User registration data
        db: Database session

    Returns:
        Created user data (excluding password)

    Raises:
        409: Email already registered
        422: Invalid request data
    """
    # Check if user already exists
    stmt = select(User).where(User.email == request.email)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Hash password
    hashed_password = hash_password(request.password)

    # Create new user
    new_user = User(
        email=request.email,
        hashed_password=hashed_password,
        role=request.role,
        is_active=True,
        is_verified=False,
    )

    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user
    except IntegrityError:
        # Race condition: another request created user with same email
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        ) from None

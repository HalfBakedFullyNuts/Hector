"""Authentication endpoints for user registration and login."""

import logging
import re
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import get_current_active_user
from ..auth.jwt import create_access_token, create_refresh_token, decode_token
from ..auth.password import hash_password, verify_password
from ..database import get_db
from ..models.user import User, UserRole

LOG = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


# =============================================================================
# Schemas
# =============================================================================


class UserRoleEnum(str):
    """User role enumeration for API."""

    CLINIC_STAFF = "clinic_staff"
    DOG_OWNER = "dog_owner"
    ADMIN = "admin"


class UserRegister(BaseModel):
    """Schema for user registration."""

    email: EmailStr = Field(description="User email address")
    password: str = Field(min_length=8, description="User password (min 8 chars)")
    role: str = Field(description="User role (clinic_staff or dog_owner)")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate role is valid."""
        valid_roles = ["clinic_staff", "dog_owner"]
        if v not in valid_roles:
            raise ValueError(f"Role must be one of: {', '.join(valid_roles)}")
        return v


class UserOut(BaseModel):
    """Schema for user output (excludes password)."""

    id: UUID
    email: str
    role: str
    is_active: bool
    is_verified: bool


class TokenResponse(BaseModel):
    """Schema for token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""

    refresh_token: str


# =============================================================================
# Endpoints
# =============================================================================


@router.post(
    "/register",
    summary="Register a new user",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    user_data: UserRegister,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserOut:
    """
    Register a new user account.

    Password requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    """
    # Check if email already exists
    existing_query = select(User).where(User.email == user_data.email)
    existing_result = await db.execute(existing_query)
    if existing_result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Create new user
    user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        role=UserRole(user_data.role),
        is_active=True,
        is_verified=False,
    )

    db.add(user)
    await db.flush()

    LOG.info(
        "User registered",
        extra={
            "user_id": str(user.id),
            "email": user.email,
            "role": user.role.value,
        },
    )

    return UserOut(
        id=user.id,
        email=user.email,
        role=user.role.value,
        is_active=user.is_active,
        is_verified=user.is_verified,
    )


@router.post(
    "/login",
    summary="Login and get access token",
    response_model=TokenResponse,
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """
    Authenticate user and return access and refresh tokens.

    Use email as username in the form.
    """
    # Find user by email
    query = select(User).where(User.email == form_data.username)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if user is None or not verify_password(form_data.password, user.hashed_password):
        LOG.warning("Failed login attempt", extra={"email": form_data.username})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    access_token = create_access_token(user.id, user.email, user.role.value)
    refresh_token = create_refresh_token(user.id)

    LOG.info(
        "User logged in",
        extra={"user_id": str(user.id), "email": user.email},
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.get(
    "/me",
    summary="Get current user profile",
    response_model=UserOut,
)
async def get_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserOut:
    """Get the currently authenticated user's profile."""
    return UserOut(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role.value,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
    )


@router.post(
    "/refresh",
    summary="Refresh access token",
    response_model=TokenResponse,
)
async def refresh_token(
    token_data: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """
    Get a new access token using a valid refresh token.
    """
    payload = decode_token(token_data.refresh_token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Verify user still exists and is active
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    access_token = create_access_token(user.id, user.email, user.role.value)
    new_refresh_token = create_refresh_token(user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
    )

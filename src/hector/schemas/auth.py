"""Authentication and user management schemas."""

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from hector.models.user import UserRole


def validate_password_strength(value: str) -> str:
    """Enforce 8+ chars with uppercase, lowercase, and digit."""
    assert isinstance(value, str)
    if len(value) < 8:
        raise ValueError("Password must be at least 8 characters long")

    if not re.search(r"[A-Z]", value):
        raise ValueError("Password must contain at least one uppercase letter")

    if not re.search(r"[a-z]", value):
        raise ValueError("Password must contain at least one lowercase letter")

    if not re.search(r"\d", value):
        raise ValueError("Password must contain at least one digit")

    return value


class UserRegisterRequest(BaseModel):
    """Request schema for user registration."""

    email: EmailStr = Field(
        ...,
        description="User's email address",
        examples=["user@example.com"],
    )

    password: str = Field(
        ...,
        min_length=8,
        max_length=72,  # bcrypt limit
        description="Password (8+ chars, uppercase, lowercase, digit)",
        examples=["SecurePass123"],
    )

    role: UserRole = Field(
        ...,
        description="User's role in the system",
        examples=[UserRole.DOG_OWNER],
    )

    @field_validator("password")
    @classmethod
    def check_password_strength(cls, value: str) -> str:
        """Delegate to the shared password policy."""
        return validate_password_strength(value)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> EmailStr:
        """Store emails lowercase so uniqueness is case-insensitive."""
        assert isinstance(value, str)
        return value.lower()

    @field_validator("role")
    @classmethod
    def forbid_admin_self_registration(cls, value: UserRole) -> UserRole:
        """Admins are only created via the create-admin CLI (design D4)."""
        assert isinstance(value, UserRole)
        if value is UserRole.ADMIN:
            raise ValueError("ADMIN accounts cannot be self-registered")
        return value


class UserLoginRequest(BaseModel):
    """Request schema for user login."""

    email: EmailStr = Field(
        ...,
        description="User's email address",
        examples=["user@example.com"],
    )

    password: str = Field(
        ...,
        min_length=1,
        max_length=72,  # bcrypt limit
        description="User's password",
        examples=["SecurePass123"],
    )

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> EmailStr:
        """Lowercase emails so login is case-insensitive."""
        assert isinstance(value, str)
        return value.lower()


class TokenRefreshRequest(BaseModel):
    """Request schema for refreshing access token."""

    refresh_token: str = Field(
        ...,
        min_length=1,
        description="JWT refresh token",
    )


class TokenResponse(BaseModel):
    """Response schema for authentication tokens."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")


class UserResponse(BaseModel):
    """Response schema for user data (excludes sensitive fields)."""

    model_config = {"from_attributes": True}

    id: UUID = Field(..., description="User's unique identifier")
    email: EmailStr = Field(..., description="User's email address")
    role: UserRole = Field(..., description="User's role in the system")
    is_active: bool = Field(..., description="Whether the user account is active")
    is_verified: bool = Field(..., description="Whether the email has been verified")
    created_at: datetime = Field(..., description="User creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

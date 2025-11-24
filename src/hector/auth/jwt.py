"""JWT token generation and validation utilities.

This module provides JWT (JSON Web Token) functionality for
user authentication and authorization.
"""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from jose import JWTError, jwt
from pydantic import BaseModel, Field

from hector.config import get_settings


class TokenPayload(BaseModel):
    """JWT token payload schema."""

    sub: str = Field(..., description="Subject (user ID)")
    email: str = Field(..., description="User email")
    role: str = Field(..., description="User role")
    exp: int = Field(..., description="Expiration timestamp")
    iat: int = Field(..., description="Issued at timestamp")
    token_type: str = Field(..., description="Token type (access or refresh)")


class TokenPair(BaseModel):
    """Access and refresh token pair."""

    access_token: str = Field(..., description="Access token")
    refresh_token: str = Field(..., description="Refresh token")
    token_type: str = Field(default="bearer", description="Token type")


def create_access_token(
    user_id: UUID,
    email: str,
    role: str,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a JWT access token.

    Generates a short-lived token for API authentication.
    Default expiration is configured in settings.

    Args:
        user_id: User's unique identifier
        email: User's email address
        role: User's role (clinic_staff, dog_owner, admin)
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string

    Example:
        >>> from uuid import uuid4
        >>> from hector.models.user import UserRole
        >>> token = create_access_token(
        ...     uuid4(),
        ...     "user@example.com",
        ...     UserRole.DOG_OWNER.value
        ... )
        >>> len(token) > 0
        True
    """
    settings = get_settings()

    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)

    now = datetime.now(UTC)
    expire = now + expires_delta

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "token_type": "access",
    }

    token: str = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return token


def create_refresh_token(
    user_id: UUID,
    email: str,
    role: str,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a JWT refresh token.

    Generates a long-lived token for obtaining new access tokens.
    Default expiration is configured in settings.

    Args:
        user_id: User's unique identifier
        email: User's email address
        role: User's role
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    settings = get_settings()

    if expires_delta is None:
        expires_delta = timedelta(days=settings.refresh_token_expire_days)

    now = datetime.now(UTC)
    expire = now + expires_delta

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "token_type": "refresh",
    }

    token: str = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return token


def create_token_pair(user_id: UUID, email: str, role: str) -> TokenPair:
    """
    Create both access and refresh tokens.

    Convenience function for login endpoints.
    Returns both tokens with their type.

    Args:
        user_id: User's unique identifier
        email: User's email address
        role: User's role

    Returns:
        TokenPair with access_token, refresh_token, and token_type
    """
    access_token = create_access_token(user_id, email, role)
    refresh_token = create_refresh_token(user_id, email, role)

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


def verify_token(token: str, expected_type: str = "access") -> TokenPayload | None:
    """
    Verify and decode a JWT token.

    Validates signature, expiration, and token type.
    Returns None if token is invalid or expired.

    Args:
        token: JWT token string to verify
        expected_type: Expected token type (access or refresh)

    Returns:
        TokenPayload if valid, None otherwise

    Example:
        >>> token = create_access_token(uuid4(), "test@example.com", "dog_owner")
        >>> payload = verify_token(token, "access")
        >>> payload is not None
        True
    """
    if not token:
        return None

    settings = get_settings()

    try:
        payload_dict: dict[str, Any] = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        # Validate token type
        token_type = payload_dict.get("token_type")
        if token_type != expected_type:
            return None

        # Parse and validate payload
        payload = TokenPayload(**payload_dict)
        return payload

    except JWTError:
        return None
    except Exception:
        return None


def decode_token_unsafe(token: str) -> dict[str, Any] | None:
    """
    Decode a token without verification (for debugging only).

    WARNING: This does not validate the signature or expiration.
    Never use for authentication decisions in production.

    Args:
        token: JWT token to decode

    Returns:
        Decoded payload dict or None if malformed
    """
    if not token:
        return None

    try:
        payload: dict[str, Any] = jwt.get_unverified_claims(token)
        return payload
    except Exception:
        return None

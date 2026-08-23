"""Authentication and user management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from hector.auth.dependencies import CurrentUser
from hector.auth.jwt import create_token_pair, verify_token
from hector.auth.password import hash_password, verify_password
from hector.config import get_settings
from hector.database import get_db
from hector.models.password_reset_token import PasswordResetToken
from hector.models.user import User
from hector.schemas.auth import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    TokenRefreshRequest,
    TokenResponse,
    UserLocationUpdate,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from hector.services.rate_limit import get_login_limiter

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


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Login user",
    description="Authenticate user and return access and refresh tokens",
)
async def login_user(
    request: UserLoginRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Authenticate user and return JWT tokens.

    Args:
        request: User login credentials
        http_request: Raw request (used to key rate limiting by client IP)
        db: Database session

    Returns:
        Access and refresh tokens

    Raises:
        401: Invalid credentials or inactive account
        429: Too many failed login attempts from this IP
        422: Invalid request data
    """
    limiter = get_login_limiter()
    client_ip = http_request.client.host if http_request.client else "unknown"
    rate_limit_key = f"login:{client_ip}"

    blocked, retry_after = limiter.check(rate_limit_key)
    if blocked:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )

    # Find user by email
    stmt = select(User).where(User.email == request.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    # Check if user exists and password is correct
    if not user or not verify_password(request.password, user.hashed_password):
        limiter.record_failure(rate_limit_key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account disabled",
        )

    # Generate token pair
    token_pair = create_token_pair(
        user_id=user.id,
        email=user.email,
        role=user.role.value,
    )

    limiter.reset(rate_limit_key)

    return TokenResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
        token_type=token_pair.token_type,
    )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user",
    description="Retrieve the currently authenticated user's information",
)
async def get_current_user_info(
    current_user: CurrentUser,
) -> User:
    """
    Get current authenticated user information.

    Args:
        current_user: Current user from JWT token (dependency)

    Returns:
        Current user data (excluding password)

    Raises:
        401: Invalid or expired token
    """
    return current_user


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Use refresh token to obtain new access and refresh tokens",
)
async def refresh_token(
    request: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Refresh access token using a valid refresh token.

    Args:
        request: Refresh token request
        db: Database session

    Returns:
        New access and refresh tokens

    Raises:
        401: Invalid or expired refresh token, or user not found/inactive
        422: Invalid request data
    """
    # Verify and decode refresh token
    payload = verify_token(request.refresh_token, expected_type="refresh")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    stmt = select(User).where(User.id == payload.sub)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate new token pair
    token_pair = create_token_pair(
        user_id=user.id,
        email=user.email,
        role=user.role.value,
    )

    return TokenResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
        token_type=token_pair.token_type,
    )


@router.patch(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update my location",
    description="Store optional coordinates used for proximity matching (T-1004)",
)
async def update_my_location(
    update: UserLocationUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Persist optional latitude/longitude for the authenticated user.

    Args:
        update: Optional coordinate values
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated user data (excluding password)

    Raises:
        401: Invalid or expired token
        422: Coordinates out of range
    """
    assert current_user is not None
    if update.latitude is not None:
        current_user.latitude = update.latitude
    if update.longitude is not None:
        current_user.longitude = update.longitude
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.post(
    "/forgot-password",
    status_code=status.HTTP_200_OK,
    summary="Request password reset",
    description="Send a reset link; always returns 200 to avoid account enumeration",
)
async def forgot_password(
    request: ForgotPasswordRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    Create a single-use reset token and email it when the account exists.

    Args:
        request: Account email
        http_request: Raw request (client IP recorded for audit)
        db: Database session

    Returns:
        Uniform response body regardless of account existence

    Raises:
        422: Invalid request data
    """
    import hashlib
    import secrets as secrets_module
    from datetime import UTC, datetime, timedelta

    stmt = select(User).where(User.email == request.email.lower())
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    message = "If that email exists, a reset link has been sent."
    if user is None:
        return {"message": message}

    raw_token = secrets_module.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    db.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            requested_ip=http_request.client.host if http_request.client else None,
        )
    )
    await db.commit()

    from hector.services.email import send_email

    await send_email(
        db=db,
        recipient=user.email,
        subject="Reset your Hector password",
        body_text=(f"Use this one-time token within 1 hour to reset your password:\n\n{raw_token}"),
        template="password_reset",
        related_type="user",
        related_id=user.id,
    )

    # Log mode exposes the token so flows are testable without SMTP (D5).
    settings = get_settings()
    payload: dict[str, str] = {"message": message}
    if not settings.smtp_host:
        payload["dev_token"] = raw_token
    return payload


@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    summary="Reset password with token",
    description="Consume a valid reset token and set a new password",
)
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    Validate the token and update the account password.

    Args:
        request: Reset token plus new password
        db: Database session

    Returns:
        Confirmation message

    Raises:
        400: Unknown, used, or expired token
        422: Weak new password
    """
    import hashlib
    from datetime import UTC, datetime

    token_hash = hashlib.sha256(request.token.encode()).hexdigest()
    record = await db.scalar(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
    )

    if record is None or record.used_at is not None or record.expires_at <= datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    user = await db.scalar(select(User).where(User.id == record.user_id))
    assert user is not None, "token must reference an existing user"

    user.hashed_password = hash_password(request.new_password)
    record.used_at = datetime.now(UTC)
    await db.commit()

    return {"message": "Password updated."}

"""Authentication dependencies for FastAPI endpoints."""

from collections.abc import Sequence
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hector.auth.jwt import verify_token
from hector.database import get_db
from hector.models.user import User, UserRole

# HTTP Bearer token security scheme
bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.

    Args:
        credentials: HTTP Authorization credentials with Bearer token
        db: Database session

    Returns:
        Current authenticated user

    Raises:
        401: Invalid or expired token, or user not found
    """
    token = credentials.credentials

    # Verify and decode token
    payload = verify_token(token, expected_type="access")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
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

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


# Type alias for annotating dependencies
CurrentUser = Annotated[User, Depends(get_current_user)]


class RoleChecker:
    """
    Dependency class for role-based authorization.

    Usage:
        @router.get("/admin-only", dependencies=[Depends(RoleChecker([UserRole.ADMIN]))])
        async def admin_endpoint(): ...

        # Or with current_user injection:
        @router.get("/staff-only")
        async def staff_endpoint(
            current_user: Annotated[
                User, Depends(RoleChecker([UserRole.CLINIC_STAFF, UserRole.ADMIN]))
            ]
        ): ...
    """

    def __init__(self, allowed_roles: Sequence[UserRole]) -> None:
        """
        Initialize role checker with allowed roles.

        Args:
            allowed_roles: List of roles that are allowed to access the endpoint
        """
        self.allowed_roles = allowed_roles

    async def __call__(self, current_user: CurrentUser) -> User:
        """
        Check if current user has one of the allowed roles.

        Args:
            current_user: Current authenticated user

        Returns:
            Current user if authorized

        Raises:
            403: User does not have required role
        """
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user


def require_role(*roles: UserRole) -> RoleChecker:
    """
    Create a role checker dependency for the specified roles.

    Args:
        *roles: Variable number of roles that are allowed

    Returns:
        RoleChecker dependency

    Example:
        @router.get("/admin", dependencies=[Depends(require_role(UserRole.ADMIN))])
        async def admin_only(): ...

        @router.get(
            "/staff",
            dependencies=[Depends(require_role(UserRole.CLINIC_STAFF, UserRole.ADMIN))],
        )
        async def staff_or_admin(): ...
    """
    return RoleChecker(list(roles))


# Pre-configured role dependencies
RequireAdmin = Annotated[User, Depends(RoleChecker([UserRole.ADMIN]))]
RequireClinicStaff = Annotated[
    User,
    Depends(RoleChecker([UserRole.CLINIC_STAFF, UserRole.ADMIN])),
]
RequireDogOwner = Annotated[User, Depends(RoleChecker([UserRole.DOG_OWNER]))]

"""Tests for role-based authorization."""

from collections.abc import AsyncGenerator

import pytest
from fastapi import APIRouter, Depends
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from hector.app import create_app
from hector.auth import RequireAdmin, RequireClinicStaff, require_role
from hector.auth.dependencies import CurrentUser
from hector.config import Settings
from hector.database import get_db
from hector.models.user import User, UserRole

# Create test router with role-protected endpoints
test_router = APIRouter(prefix="/test", tags=["test"])


@test_router.get("/admin-only")
async def admin_only_endpoint(admin: RequireAdmin) -> dict[str, str]:
    """Endpoint that requires admin role."""
    return {"message": "admin access granted", "email": admin.email}


@test_router.get("/clinic-staff")
async def clinic_staff_endpoint(staff: RequireClinicStaff) -> dict[str, str]:
    """Endpoint that requires clinic staff or admin role."""
    return {"message": "clinic staff access granted", "email": staff.email}


@test_router.get("/dog-owner-only", dependencies=[Depends(require_role(UserRole.DOG_OWNER))])
async def dog_owner_endpoint(current_user: CurrentUser) -> dict[str, str]:
    """Endpoint that requires dog owner role."""
    return {"message": "dog owner access granted", "email": current_user.email}


@test_router.get(
    "/multi-role",
    dependencies=[Depends(require_role(UserRole.DOG_OWNER, UserRole.CLINIC_STAFF))],
)
async def multi_role_endpoint(current_user: CurrentUser) -> dict[str, str]:
    """Endpoint that allows multiple roles."""
    return {"message": "multi-role access granted", "email": current_user.email}


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database session."""
    settings = Settings()
    app = create_app(settings)

    # Add test router
    app.include_router(test_router)

    # Override database dependency
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Clean up override
    app.dependency_overrides.clear()


class TestRoleBasedAuthorization:
    """Tests for role-based authorization."""

    async def test_admin_endpoint_with_admin_user(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """Test admin endpoint with admin user."""
        from hector.auth.jwt import create_access_token
        from hector.auth.password import hash_password

        # Create admin user
        user = User(
            email="admin@example.com",
            hashed_password=hash_password("SecurePass123"),
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        token = create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role.value,
        )

        response = await client.get(
            "/test/admin-only",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "admin access granted"
        assert data["email"] == "admin@example.com"

    async def test_admin_endpoint_with_non_admin_returns_403(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """Test admin endpoint with non-admin user returns 403."""
        from hector.auth.jwt import create_access_token
        from hector.auth.password import hash_password

        # Create dog owner user
        user = User(
            email="owner@example.com",
            hashed_password=hash_password("SecurePass123"),
            role=UserRole.DOG_OWNER,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        token = create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role.value,
        )

        response = await client.get(
            "/test/admin-only",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 403
        data = response.json()
        assert "Insufficient permissions" in data["detail"]

    async def test_clinic_staff_endpoint_with_clinic_staff(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """Test clinic staff endpoint with clinic staff user."""
        from hector.auth.jwt import create_access_token
        from hector.auth.password import hash_password

        user = User(
            email="staff@example.com",
            hashed_password=hash_password("SecurePass123"),
            role=UserRole.CLINIC_STAFF,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        token = create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role.value,
        )

        response = await client.get(
            "/test/clinic-staff",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "clinic staff access granted"

    async def test_clinic_staff_endpoint_with_admin(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """Test clinic staff endpoint allows admin access."""
        from hector.auth.jwt import create_access_token
        from hector.auth.password import hash_password

        user = User(
            email="admin2@example.com",
            hashed_password=hash_password("SecurePass123"),
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        token = create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role.value,
        )

        response = await client.get(
            "/test/clinic-staff",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200

    async def test_clinic_staff_endpoint_with_dog_owner_returns_403(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """Test clinic staff endpoint denies dog owner access."""
        from hector.auth.jwt import create_access_token
        from hector.auth.password import hash_password

        user = User(
            email="owner2@example.com",
            hashed_password=hash_password("SecurePass123"),
            role=UserRole.DOG_OWNER,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        token = create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role.value,
        )

        response = await client.get(
            "/test/clinic-staff",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 403

    async def test_require_role_with_matching_role(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """Test require_role with matching role."""
        from hector.auth.jwt import create_access_token
        from hector.auth.password import hash_password

        user = User(
            email="owner3@example.com",
            hashed_password=hash_password("SecurePass123"),
            role=UserRole.DOG_OWNER,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        token = create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role.value,
        )

        response = await client.get(
            "/test/dog-owner-only",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "dog owner access granted"

    async def test_multi_role_allows_any_listed_role(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """Test multi-role endpoint allows any of the listed roles."""
        from hector.auth.jwt import create_access_token
        from hector.auth.password import hash_password

        # Test with dog owner
        user1 = User(
            email="owner4@example.com",
            hashed_password=hash_password("SecurePass123"),
            role=UserRole.DOG_OWNER,
            is_active=True,
        )
        # Test with clinic staff
        user2 = User(
            email="staff2@example.com",
            hashed_password=hash_password("SecurePass123"),
            role=UserRole.CLINIC_STAFF,
            is_active=True,
        )
        db_session.add(user1)
        db_session.add(user2)
        await db_session.commit()
        await db_session.refresh(user1)
        await db_session.refresh(user2)

        for user in [user1, user2]:
            token = create_access_token(
                user_id=user.id,
                email=user.email,
                role=user.role.value,
            )

            response = await client.get(
                "/test/multi-role",
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200

    async def test_multi_role_denies_unlisted_role(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """Test multi-role endpoint denies roles not in list."""
        from hector.auth.jwt import create_access_token
        from hector.auth.password import hash_password

        # Admin not in allowed roles for multi-role endpoint
        user = User(
            email="admin3@example.com",
            hashed_password=hash_password("SecurePass123"),
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        token = create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role.value,
        )

        response = await client.get(
            "/test/multi-role",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 403

    async def test_role_check_without_authentication_returns_403(
        self,
        client: AsyncClient,
    ) -> None:
        """Test role-protected endpoint without auth returns 403."""
        response = await client.get("/test/admin-only")

        assert response.status_code == 403

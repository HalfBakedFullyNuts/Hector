"""Tests for authentication endpoints."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hector.app import create_app
from hector.config import Settings
from hector.database import get_db
from hector.models.user import User, UserRole


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database session."""
    settings = Settings()
    app = create_app(settings)

    # Override database dependency
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Clean up override
    app.dependency_overrides.clear()


class TestUserRegistration:
    """Tests for POST /auth/register endpoint."""

    async def test_register_user_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """Test successful user registration."""
        payload = {
            "email": "newuser@example.com",
            "password": "SecurePass123",
            "role": "dog_owner",
        }

        response = await client.post("/auth/register", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["role"] == "dog_owner"
        assert data["is_active"] is True
        assert data["is_verified"] is False
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
        assert "password" not in data
        assert "hashed_password" not in data

        # Verify user in database
        stmt = select(User).where(User.email == "newuser@example.com")
        result = await db_session.execute(stmt)
        user = result.scalar_one_or_none()
        assert user is not None
        assert user.email == "newuser@example.com"
        assert user.hashed_password.startswith("$2b$")

    async def test_register_clinic_staff_role(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """Test registration with clinic_staff role."""
        payload = {
            "email": "clinic@example.com",
            "password": "SecurePass123",
            "role": "clinic_staff",
        }

        response = await client.post("/auth/register", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["role"] == "clinic_staff"

    async def test_register_duplicate_email_returns_409(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """Test that duplicate email returns 409 Conflict."""
        # Create first user
        user = User(
            email="existing@example.com",
            hashed_password="$2b$12$hashedpassword",
            role=UserRole.DOG_OWNER,
        )
        db_session.add(user)
        await db_session.commit()

        # Try to register with same email
        payload = {
            "email": "existing@example.com",
            "password": "SecurePass123",
            "role": "dog_owner",
        }

        response = await client.post("/auth/register", json=payload)

        assert response.status_code == 409
        data = response.json()
        assert "already registered" in data["detail"].lower()

    async def test_register_password_too_short_returns_422(
        self,
        client: AsyncClient,
    ) -> None:
        """Test that short password returns 422."""
        payload = {
            "email": "user@example.com",
            "password": "Short1",  # Only 6 characters
            "role": "dog_owner",
        }

        response = await client.post("/auth/register", json=payload)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    async def test_register_password_missing_uppercase_returns_422(
        self,
        client: AsyncClient,
    ) -> None:
        """Test that password without uppercase returns 422."""
        payload = {
            "email": "user@example.com",
            "password": "securepass123",  # No uppercase
            "role": "dog_owner",
        }

        response = await client.post("/auth/register", json=payload)

        assert response.status_code == 422
        data = response.json()
        assert "uppercase" in str(data).lower()

    async def test_register_password_missing_lowercase_returns_422(
        self,
        client: AsyncClient,
    ) -> None:
        """Test that password without lowercase returns 422."""
        payload = {
            "email": "user@example.com",
            "password": "SECUREPASS123",  # No lowercase
            "role": "dog_owner",
        }

        response = await client.post("/auth/register", json=payload)

        assert response.status_code == 422
        data = response.json()
        assert "lowercase" in str(data).lower()

    async def test_register_password_missing_digit_returns_422(
        self,
        client: AsyncClient,
    ) -> None:
        """Test that password without digit returns 422."""
        payload = {
            "email": "user@example.com",
            "password": "SecurePassword",  # No digit
            "role": "dog_owner",
        }

        response = await client.post("/auth/register", json=payload)

        assert response.status_code == 422
        data = response.json()
        assert "digit" in str(data).lower()

    async def test_register_invalid_email_returns_422(
        self,
        client: AsyncClient,
    ) -> None:
        """Test that invalid email returns 422."""
        payload = {
            "email": "not-an-email",
            "password": "SecurePass123",
            "role": "dog_owner",
        }

        response = await client.post("/auth/register", json=payload)

        assert response.status_code == 422

    async def test_register_invalid_role_returns_422(
        self,
        client: AsyncClient,
    ) -> None:
        """Test that invalid role returns 422."""
        payload = {
            "email": "user@example.com",
            "password": "SecurePass123",
            "role": "invalid_role",
        }

        response = await client.post("/auth/register", json=payload)

        assert response.status_code == 422

    async def test_register_missing_email_returns_422(
        self,
        client: AsyncClient,
    ) -> None:
        """Test that missing email returns 422."""
        payload = {
            "password": "SecurePass123",
            "role": "dog_owner",
        }

        response = await client.post("/auth/register", json=payload)

        assert response.status_code == 422

    async def test_register_missing_password_returns_422(
        self,
        client: AsyncClient,
    ) -> None:
        """Test that missing password returns 422."""
        payload = {
            "email": "user@example.com",
            "role": "dog_owner",
        }

        response = await client.post("/auth/register", json=payload)

        assert response.status_code == 422

    async def test_register_missing_role_returns_422(
        self,
        client: AsyncClient,
    ) -> None:
        """Test that missing role returns 422."""
        payload = {
            "email": "user@example.com",
            "password": "SecurePass123",
        }

        response = await client.post("/auth/register", json=payload)

        assert response.status_code == 422

    async def test_register_password_hashing(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """Test that passwords are properly hashed."""
        payload = {
            "email": "hashing@example.com",
            "password": "SecurePass123",
            "role": "dog_owner",
        }

        response = await client.post("/auth/register", json=payload)
        assert response.status_code == 201

        # Check database
        stmt = select(User).where(User.email == "hashing@example.com")
        result = await db_session.execute(stmt)
        user = result.scalar_one()

        # Password should be bcrypt hashed
        assert user.hashed_password != "SecurePass123"
        assert user.hashed_password.startswith("$2b$")
        assert len(user.hashed_password) > 50

    async def test_register_case_sensitive_email(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """Test email case sensitivity handling."""
        # Register user with lowercase email
        payload1 = {
            "email": "test@example.com",
            "password": "SecurePass123",
            "role": "dog_owner",
        }
        response1 = await client.post("/auth/register", json=payload1)
        assert response1.status_code == 201

        # Try to register with different case
        # Note: EmailStr normalizes to lowercase, so this should conflict
        payload2 = {
            "email": "Test@Example.com",
            "password": "SecurePass123",
            "role": "dog_owner",
        }
        response2 = await client.post("/auth/register", json=payload2)

        # Should conflict because EmailStr normalizes
        assert response2.status_code == 409


class TestUserLogin:
    """Tests for POST /auth/login endpoint."""

    async def test_login_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """Test successful user login."""
        from hector.auth.password import hash_password

        # Create a test user
        user = User(
            email="logintest@example.com",
            hashed_password=hash_password("SecurePass123"),
            role=UserRole.DOG_OWNER,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        # Attempt login
        payload = {
            "email": "logintest@example.com",
            "password": "SecurePass123",
        }

        response = await client.post("/auth/login", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0
        assert len(data["refresh_token"]) > 0

    async def test_login_invalid_email(
        self,
        client: AsyncClient,
    ) -> None:
        """Test login with non-existent email."""
        payload = {
            "email": "nonexistent@example.com",
            "password": "SecurePass123",
        }

        response = await client.post("/auth/login", json=payload)

        assert response.status_code == 401
        data = response.json()
        assert "Invalid email or password" in data["detail"]

    async def test_login_wrong_password(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """Test login with incorrect password."""
        from hector.auth.password import hash_password

        # Create a test user
        user = User(
            email="wrongpw@example.com",
            hashed_password=hash_password("CorrectPass123"),
            role=UserRole.DOG_OWNER,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        # Attempt login with wrong password
        payload = {
            "email": "wrongpw@example.com",
            "password": "WrongPass123",
        }

        response = await client.post("/auth/login", json=payload)

        assert response.status_code == 401
        data = response.json()
        assert "Invalid email or password" in data["detail"]

    async def test_login_inactive_account(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """Test login with inactive account."""
        from hector.auth.password import hash_password

        # Create an inactive user
        user = User(
            email="inactive@example.com",
            hashed_password=hash_password("SecurePass123"),
            role=UserRole.DOG_OWNER,
            is_active=False,
        )
        db_session.add(user)
        await db_session.commit()

        # Attempt login
        payload = {
            "email": "inactive@example.com",
            "password": "SecurePass123",
        }

        response = await client.post("/auth/login", json=payload)

        assert response.status_code == 401
        data = response.json()
        assert "inactive" in data["detail"].lower()

    async def test_login_missing_email(
        self,
        client: AsyncClient,
    ) -> None:
        """Test login without email."""
        payload = {
            "password": "SecurePass123",
        }

        response = await client.post("/auth/login", json=payload)

        assert response.status_code == 422

    async def test_login_missing_password(
        self,
        client: AsyncClient,
    ) -> None:
        """Test login without password."""
        payload = {
            "email": "test@example.com",
        }

        response = await client.post("/auth/login", json=payload)

        assert response.status_code == 422

    async def test_login_invalid_email_format(
        self,
        client: AsyncClient,
    ) -> None:
        """Test login with invalid email format."""
        payload = {
            "email": "not-an-email",
            "password": "SecurePass123",
        }

        response = await client.post("/auth/login", json=payload)

        assert response.status_code == 422

    async def test_login_empty_password(
        self,
        client: AsyncClient,
    ) -> None:
        """Test login with empty password."""
        payload = {
            "email": "test@example.com",
            "password": "",
        }

        response = await client.post("/auth/login", json=payload)

        assert response.status_code == 422

    async def test_login_tokens_are_valid_jwt(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """Test that returned tokens are valid JWT format."""
        from hector.auth.password import hash_password

        # Create a test user
        user = User(
            email="jwttest@example.com",
            hashed_password=hash_password("SecurePass123"),
            role=UserRole.CLINIC_STAFF,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        # Login
        payload = {
            "email": "jwttest@example.com",
            "password": "SecurePass123",
        }

        response = await client.post("/auth/login", json=payload)

        assert response.status_code == 200
        data = response.json()

        # JWT tokens should have 3 parts separated by dots
        access_parts = data["access_token"].split(".")
        refresh_parts = data["refresh_token"].split(".")
        assert len(access_parts) == 3
        assert len(refresh_parts) == 3

    async def test_login_case_insensitive_email(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """Test login with different email case."""
        from hector.auth.password import hash_password

        # Create user with lowercase email
        user = User(
            email="casetest@example.com",
            hashed_password=hash_password("SecurePass123"),
            role=UserRole.DOG_OWNER,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        # Login with different case (EmailStr normalizes to lowercase)
        payload = {
            "email": "CaseTest@Example.com",
            "password": "SecurePass123",
        }

        response = await client.post("/auth/login", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    async def test_login_different_roles(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """Test login works for all user roles."""
        from hector.auth.password import hash_password

        roles = [UserRole.DOG_OWNER, UserRole.CLINIC_STAFF, UserRole.ADMIN]

        for idx, role in enumerate(roles):
            user = User(
                email=f"role{idx}@example.com",
                hashed_password=hash_password("SecurePass123"),
                role=role,
                is_active=True,
            )
            db_session.add(user)

        await db_session.commit()

        # Test login for each role
        for idx in range(len(roles)):
            payload = {
                "email": f"role{idx}@example.com",
                "password": "SecurePass123",
            }

            response = await client.post("/auth/login", json=payload)

            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data


class TestGetCurrentUser:
    """Tests for GET /auth/me endpoint."""

    async def test_get_current_user_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """Test getting current user with valid token."""
        from hector.auth.jwt import create_access_token
        from hector.auth.password import hash_password

        # Create a test user
        user = User(
            email="metest@example.com",
            hashed_password=hash_password("SecurePass123"),
            role=UserRole.DOG_OWNER,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Generate access token
        token = create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role.value,
        )

        # Make request with token
        response = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "metest@example.com"
        assert data["role"] == "dog_owner"
        assert data["is_active"] is True
        assert "id" in data
        assert "password" not in data
        assert "hashed_password" not in data

    async def test_get_current_user_missing_token(
        self,
        client: AsyncClient,
    ) -> None:
        """Test GET /me without authentication token."""
        response = await client.get("/auth/me")

        assert response.status_code == 403

    async def test_get_current_user_invalid_token(
        self,
        client: AsyncClient,
    ) -> None:
        """Test GET /me with invalid token."""
        response = await client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid_token_here"},
        )

        assert response.status_code == 401
        data = response.json()
        assert "Invalid or expired token" in data["detail"]

    async def test_get_current_user_malformed_token(
        self,
        client: AsyncClient,
    ) -> None:
        """Test GET /me with malformed token."""
        response = await client.get(
            "/auth/me",
            headers={"Authorization": "Bearer not.a.jwt"},
        )

        assert response.status_code == 401

    async def test_get_current_user_expired_token(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """Test GET /me with expired token."""
        from datetime import timedelta

        from hector.auth.jwt import create_access_token
        from hector.auth.password import hash_password

        # Create a test user
        user = User(
            email="expired@example.com",
            hashed_password=hash_password("SecurePass123"),
            role=UserRole.DOG_OWNER,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Generate expired token (negative expiry)
        token = create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role.value,
            expires_delta=timedelta(seconds=-10),
        )

        # Make request with expired token
        response = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 401
        data = response.json()
        assert "Invalid or expired token" in data["detail"]

    async def test_get_current_user_inactive_account(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """Test GET /me with inactive user account."""
        from hector.auth.jwt import create_access_token
        from hector.auth.password import hash_password

        # Create an inactive user
        user = User(
            email="inactive_me@example.com",
            hashed_password=hash_password("SecurePass123"),
            role=UserRole.DOG_OWNER,
            is_active=False,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Generate token for inactive user
        token = create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role.value,
        )

        # Make request with token
        response = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 401
        data = response.json()
        assert "inactive" in data["detail"].lower()

    async def test_get_current_user_deleted_user(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """Test GET /me with token for deleted user."""
        from uuid import uuid4

        from hector.auth.jwt import create_access_token

        # Create a fake user ID (user doesn't exist)
        fake_user_id = uuid4()

        # Generate token with non-existent user ID
        token = create_access_token(
            user_id=fake_user_id,
            email="deleted@example.com",
            role="dog_owner",
        )

        # Make request with token
        response = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 401
        data = response.json()
        assert "User not found" in data["detail"]

    async def test_get_current_user_wrong_token_type(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """Test GET /me with refresh token instead of access token."""
        from hector.auth.jwt import create_refresh_token
        from hector.auth.password import hash_password

        # Create a test user
        user = User(
            email="wrongtype@example.com",
            hashed_password=hash_password("SecurePass123"),
            role=UserRole.DOG_OWNER,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Generate refresh token (wrong type for /me endpoint)
        token = create_refresh_token(
            user_id=user.id,
            email=user.email,
            role=user.role.value,
        )

        # Make request with wrong token type
        response = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 401
        data = response.json()
        assert "Invalid or expired token" in data["detail"]

    async def test_get_current_user_different_roles(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """Test GET /me works for all user roles."""
        from hector.auth.jwt import create_access_token
        from hector.auth.password import hash_password

        roles = [UserRole.DOG_OWNER, UserRole.CLINIC_STAFF, UserRole.ADMIN]

        for idx, role in enumerate(roles):
            user = User(
                email=f"merole{idx}@example.com",
                hashed_password=hash_password("SecurePass123"),
                role=role,
                is_active=True,
            )
            db_session.add(user)

        await db_session.commit()

        # Test /me for each role
        users = await db_session.execute(select(User))
        for user in users.scalars():
            token = create_access_token(
                user_id=user.id,
                email=user.email,
                role=user.role.value,
            )

            response = await client.get(
                "/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["email"] == user.email
            assert data["role"] == user.role.value

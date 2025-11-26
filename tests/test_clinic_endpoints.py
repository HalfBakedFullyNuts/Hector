"""Tests for clinic management endpoints."""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from hector.auth.jwt import create_access_token
from hector.models.clinic import Clinic
from hector.models.clinic_staff import clinic_staff_association
from hector.models.user import User, UserRole


@pytest.fixture
async def clinic_staff(db_session: AsyncSession) -> User:
    """Create a clinic staff user for testing."""
    user = User(
        email="clinic_staff@example.com",
        hashed_password="hashed_password",
        role=UserRole.CLINIC_STAFF,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def clinic_staff_token(clinic_staff: User) -> str:
    """Create an access token for the clinic staff."""
    return create_access_token(
        user_id=clinic_staff.id,
        email=clinic_staff.email,
        role=clinic_staff.role.value,
    )


@pytest.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create an admin user for testing."""
    user = User(
        email="admin@example.com",
        hashed_password="hashed_password",
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def admin_token(admin_user: User) -> str:
    """Create an access token for the admin."""
    return create_access_token(
        user_id=admin_user.id,
        email=admin_user.email,
        role=admin_user.role.value,
    )


@pytest.fixture
async def dog_owner_user(db_session: AsyncSession) -> User:
    """Create a dog owner user for testing."""
    user = User(
        email="dogowner@example.com",
        hashed_password="hashed_password",
        role=UserRole.DOG_OWNER,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def dog_owner_token(dog_owner_user: User) -> str:
    """Create an access token for the dog owner."""
    return create_access_token(
        user_id=dog_owner_user.id,
        email=dog_owner_user.email,
        role=dog_owner_user.role.value,
    )


@pytest.fixture
async def clinic(db_session: AsyncSession, clinic_staff: User) -> Clinic:
    """Create a clinic for testing."""
    new_clinic = Clinic(
        name="Test Veterinary Hospital",
        address="123 Test Street",
        city="Berlin",
        postal_code="10115",
        phone="+49 30 12345678",
        email="test@clinic.com",
        latitude=52.5200,
        longitude=13.4050,
        is_approved=True,
    )
    db_session.add(new_clinic)
    await db_session.flush()

    # Link clinic staff to clinic
    stmt = clinic_staff_association.insert().values(
        user_id=clinic_staff.id,
        clinic_id=new_clinic.id,
    )
    await db_session.execute(stmt)
    await db_session.commit()
    await db_session.refresh(new_clinic)
    return new_clinic


class TestCreateClinic:
    """Tests for POST /clinics endpoint (T-400)."""

    async def test_create_clinic_success(
        self,
        async_client: AsyncClient,
        clinic_staff_token: str,
    ) -> None:
        """Test successful clinic creation."""
        request_data = {
            "name": "Berlin Veterinary Hospital",
            "address": "456 Main Street",
            "city": "Berlin",
            "postal_code": "10115",
            "phone": "+49 30 98765432",
            "email": "contact@berlinvet.com",
            "latitude": 52.5200,
            "longitude": 13.4050,
        }

        response = await async_client.post(
            "/clinics",
            json=request_data,
            headers={"Authorization": f"Bearer {clinic_staff_token}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Berlin Veterinary Hospital"
        assert data["city"] == "Berlin"
        assert data["phone"] == "+49 30 98765432"
        assert data["is_approved"] is False  # Requires admin approval
        assert "id" in data

    async def test_create_clinic_minimal_fields(
        self,
        async_client: AsyncClient,
        clinic_staff_token: str,
    ) -> None:
        """Test clinic creation with only required fields."""
        request_data = {
            "name": "Simple Clinic",
            "address": "789 Simple St",
            "city": "Munich",
            "postal_code": "80331",
            "phone": "+49 89 12345678",
            "email": "simple@clinic.com",
        }

        response = await async_client.post(
            "/clinics",
            json=request_data,
            headers={"Authorization": f"Bearer {clinic_staff_token}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Simple Clinic"
        assert data["latitude"] is None
        assert data["longitude"] is None

    async def test_create_clinic_dog_owner_forbidden(
        self,
        async_client: AsyncClient,
        dog_owner_token: str,
    ) -> None:
        """Test that dog owners cannot create clinics."""
        request_data = {
            "name": "Forbidden Clinic",
            "address": "123 Forbidden St",
            "city": "Hamburg",
            "postal_code": "20095",
            "phone": "+49 40 12345678",
            "email": "forbidden@clinic.com",
        }

        response = await async_client.post(
            "/clinics",
            json=request_data,
            headers={"Authorization": f"Bearer {dog_owner_token}"},
        )

        assert response.status_code == 403
        assert "Only clinic staff" in response.json()["detail"]

    async def test_create_clinic_invalid_email(
        self,
        async_client: AsyncClient,
        clinic_staff_token: str,
    ) -> None:
        """Test clinic creation with invalid email."""
        request_data = {
            "name": "Invalid Email Clinic",
            "address": "123 Invalid St",
            "city": "Frankfurt",
            "postal_code": "60311",
            "phone": "+49 69 12345678",
            "email": "not-an-email",
        }

        response = await async_client.post(
            "/clinics",
            json=request_data,
            headers={"Authorization": f"Bearer {clinic_staff_token}"},
        )

        assert response.status_code == 422

    async def test_create_clinic_unauthorized(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test clinic creation without authentication."""
        request_data = {
            "name": "Unauthorized Clinic",
            "address": "123 Unauth St",
            "city": "Cologne",
            "postal_code": "50667",
            "phone": "+49 221 12345678",
            "email": "unauth@clinic.com",
        }

        response = await async_client.post("/clinics", json=request_data)
        assert response.status_code == 403


class TestGetClinic:
    """Tests for GET /clinics/{clinic_id} endpoint (T-401)."""

    async def test_get_clinic_success(
        self,
        async_client: AsyncClient,
        clinic: Clinic,
    ) -> None:
        """Test getting a clinic by ID."""
        response = await async_client.get(f"/clinics/{clinic.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(clinic.id)
        assert data["name"] == clinic.name
        assert data["city"] == clinic.city

    async def test_get_clinic_not_found(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test getting a non-existent clinic."""
        non_existent_id = uuid4()
        response = await async_client.get(f"/clinics/{non_existent_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    async def test_get_clinic_public_access(
        self,
        async_client: AsyncClient,
        clinic: Clinic,
    ) -> None:
        """Test that clinic details are publicly accessible."""
        # No authentication header
        response = await async_client.get(f"/clinics/{clinic.id}")

        assert response.status_code == 200


class TestUpdateClinic:
    """Tests for PUT /clinics/{clinic_id} endpoint (T-402)."""

    async def test_update_clinic_by_staff(
        self,
        async_client: AsyncClient,
        clinic_staff_token: str,
        clinic: Clinic,
    ) -> None:
        """Test updating clinic by staff member."""
        update_data = {
            "name": "Updated Clinic Name",
            "phone": "+49 30 99999999",
        }

        response = await async_client.put(
            f"/clinics/{clinic.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {clinic_staff_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Clinic Name"
        assert data["phone"] == "+49 30 99999999"

    async def test_update_clinic_by_admin(
        self,
        async_client: AsyncClient,
        admin_token: str,
        clinic: Clinic,
    ) -> None:
        """Test updating clinic by admin."""
        update_data = {
            "city": "Munich",
        }

        response = await async_client.put(
            f"/clinics/{clinic.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["city"] == "Munich"

    async def test_update_clinic_not_staff_forbidden(
        self,
        async_client: AsyncClient,
        dog_owner_token: str,
        clinic: Clinic,
    ) -> None:
        """Test that non-staff cannot update clinic."""
        update_data = {
            "name": "Hacked Clinic",
        }

        response = await async_client.put(
            f"/clinics/{clinic.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {dog_owner_token}"},
        )

        assert response.status_code == 403
        assert "staff of this clinic" in response.json()["detail"]

    async def test_update_clinic_not_found(
        self,
        async_client: AsyncClient,
        clinic_staff_token: str,
    ) -> None:
        """Test updating non-existent clinic."""
        non_existent_id = uuid4()
        update_data = {"name": "New Name"}

        response = await async_client.put(
            f"/clinics/{non_existent_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {clinic_staff_token}"},
        )

        assert response.status_code == 404


class TestListClinics:
    """Tests for GET /clinics endpoint (T-403)."""

    async def test_list_clinics_shows_approved_only(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        clinic: Clinic,
    ) -> None:
        """Test that only approved clinics are shown to public."""
        # Create an unapproved clinic
        unapproved = Clinic(
            name="Unapproved Clinic",
            address="999 Hidden St",
            city="Berlin",
            postal_code="10115",
            phone="+49 30 00000000",
            email="unapproved@clinic.com",
            is_approved=False,
        )
        db_session.add(unapproved)
        await db_session.commit()

        response = await async_client.get("/clinics")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should only see approved clinic
        clinic_names = [c["name"] for c in data]
        assert clinic.name in clinic_names
        assert "Unapproved Clinic" not in clinic_names

    async def test_list_clinics_filter_by_city(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        clinic: Clinic,
    ) -> None:
        """Test filtering clinics by city."""
        # Create clinic in different city
        other_clinic = Clinic(
            name="Munich Clinic",
            address="123 Munich St",
            city="Munich",
            postal_code="80331",
            phone="+49 89 12345678",
            email="munich@clinic.com",
            is_approved=True,
        )
        db_session.add(other_clinic)
        await db_session.commit()

        response = await async_client.get("/clinics?city=Berlin")

        assert response.status_code == 200
        data = response.json()
        assert all(c["city"] == "Berlin" for c in data)

    async def test_list_clinics_pagination(
        self,
        async_client: AsyncClient,
        clinic: Clinic,
    ) -> None:
        """Test pagination parameters."""
        response = await async_client.get("/clinics?limit=10&offset=0")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10

    async def test_list_clinics_sorted_by_name(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """Test that clinics are sorted alphabetically by name."""
        # Create multiple clinics
        clinics_data = [
            ("Zebra Clinic", "Berlin"),
            ("Alpha Clinic", "Berlin"),
            ("Middle Clinic", "Berlin"),
        ]

        for name, city in clinics_data:
            clinic = Clinic(
                name=name,
                address="123 Test St",
                city=city,
                postal_code="10115",
                phone="+49 30 12345678",
                email=f"{name.lower().replace(' ', '')}@clinic.com",
                is_approved=True,
            )
            db_session.add(clinic)

        await db_session.commit()

        response = await async_client.get("/clinics")

        assert response.status_code == 200
        data = response.json()
        names = [c["name"] for c in data]
        assert names == sorted(names)

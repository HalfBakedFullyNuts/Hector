"""Tests for dog profile endpoints."""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from hector.auth.jwt import create_access_token
from hector.models.dog_profile import BloodType, DogProfile, DogSex
from hector.models.user import User, UserRole


@pytest.fixture
async def dog_owner(db_session: AsyncSession) -> User:
    """Create a dog owner user for testing."""
    user = User(
        email="owner@example.com",
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
def dog_owner_token(dog_owner: User) -> str:
    """Create an access token for the dog owner."""
    return create_access_token(
        user_id=dog_owner.id,
        email=dog_owner.email,
        role=dog_owner.role.value,
    )


@pytest.fixture
async def dog_profile(db_session: AsyncSession, dog_owner: User) -> DogProfile:
    """Create a dog profile for testing."""
    dog = DogProfile(
        owner_id=dog_owner.id,
        name="Max",
        breed="Labrador Retriever",
        date_of_birth=date(2020, 1, 15),
        weight_kg=30.5,
        sex=DogSex.MALE,
        blood_type=BloodType.DEA_1_1_NEGATIVE,
        is_active=True,
    )
    db_session.add(dog)
    await db_session.commit()
    await db_session.refresh(dog)
    return dog


class TestCreateDogProfile:
    """Tests for POST /dogs endpoint (T-300)."""

    async def test_create_dog_profile_success(
        self,
        async_client: AsyncClient,
        dog_owner_token: str,
    ) -> None:
        """Test successful dog profile creation."""
        request_data = {
            "name": "Buddy",
            "breed": "Golden Retriever",
            "date_of_birth": "2021-03-10",
            "weight_kg": 32.0,
            "sex": "MALE",
            "blood_type": "DEA_1_1_POSITIVE",
        }

        response = await async_client.post(
            "/dogs",
            json=request_data,
            headers={"Authorization": f"Bearer {dog_owner_token}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Buddy"
        assert data["breed"] == "Golden Retriever"
        assert data["weight_kg"] == 32.0
        assert data["sex"] == "MALE"
        assert data["blood_type"] == "DEA_1_1_POSITIVE"
        assert data["is_active"] is True
        assert "id" in data
        assert "owner_id" in data

    async def test_create_dog_profile_minimal_fields(
        self,
        async_client: AsyncClient,
        dog_owner_token: str,
    ) -> None:
        """Test dog profile creation with only required fields."""
        request_data = {
            "name": "Rex",
            "date_of_birth": "2022-05-20",
            "weight_kg": 28.0,
            "sex": "MALE",
        }

        response = await async_client.post(
            "/dogs",
            json=request_data,
            headers={"Authorization": f"Bearer {dog_owner_token}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Rex"
        assert data["breed"] is None
        assert data["blood_type"] is None

    async def test_create_dog_profile_weight_too_low(
        self,
        async_client: AsyncClient,
        dog_owner_token: str,
    ) -> None:
        """Test dog profile creation with weight below 25kg."""
        request_data = {
            "name": "Tiny",
            "date_of_birth": "2022-01-01",
            "weight_kg": 20.0,
            "sex": "FEMALE",
        }

        response = await async_client.post(
            "/dogs",
            json=request_data,
            headers={"Authorization": f"Bearer {dog_owner_token}"},
        )

        assert response.status_code == 422

    async def test_create_dog_profile_too_young(
        self,
        async_client: AsyncClient,
        dog_owner_token: str,
    ) -> None:
        """Test dog profile creation with dog under 1 year old."""
        today = date.today()
        six_months_ago = today - timedelta(days=180)

        request_data = {
            "name": "Puppy",
            "date_of_birth": six_months_ago.isoformat(),
            "weight_kg": 30.0,
            "sex": "MALE",
        }

        response = await async_client.post(
            "/dogs",
            json=request_data,
            headers={"Authorization": f"Bearer {dog_owner_token}"},
        )

        assert response.status_code == 422
        assert "at least 1 year old" in response.json()["detail"][0]["msg"]

    async def test_create_dog_profile_too_old(
        self,
        async_client: AsyncClient,
        dog_owner_token: str,
    ) -> None:
        """Test dog profile creation with dog over 8 years old."""
        today = date.today()
        nine_years_ago = today - timedelta(days=9 * 365)

        request_data = {
            "name": "OldDog",
            "date_of_birth": nine_years_ago.isoformat(),
            "weight_kg": 30.0,
            "sex": "MALE",
        }

        response = await async_client.post(
            "/dogs",
            json=request_data,
            headers={"Authorization": f"Bearer {dog_owner_token}"},
        )

        assert response.status_code == 422
        assert "8 years or younger" in response.json()["detail"][0]["msg"]

    async def test_create_dog_profile_unauthorized(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test dog profile creation without authentication."""
        request_data = {
            "name": "NoAuth",
            "date_of_birth": "2021-01-01",
            "weight_kg": 30.0,
            "sex": "MALE",
        }

        response = await async_client.post("/dogs", json=request_data)
        assert response.status_code == 403  # No authorization header


class TestListMyDogs:
    """Tests for GET /dogs endpoint (T-301)."""

    async def test_list_my_dogs_success(
        self,
        async_client: AsyncClient,
        dog_owner_token: str,
        dog_profile: DogProfile,
    ) -> None:
        """Test listing dog profiles for authenticated user."""
        response = await async_client.get(
            "/dogs",
            headers={"Authorization": f"Bearer {dog_owner_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == str(dog_profile.id)
        assert data[0]["name"] == dog_profile.name

    async def test_list_my_dogs_empty(
        self,
        async_client: AsyncClient,
        dog_owner_token: str,
    ) -> None:
        """Test listing dog profiles when user has no dogs."""
        response = await async_client.get(
            "/dogs",
            headers={"Authorization": f"Bearer {dog_owner_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    async def test_list_my_dogs_unauthorized(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test listing dog profiles without authentication."""
        response = await async_client.get("/dogs")
        assert response.status_code == 403


class TestGetDogProfile:
    """Tests for GET /dogs/{dog_id} endpoint (T-302)."""

    async def test_get_dog_profile_success(
        self,
        async_client: AsyncClient,
        dog_owner_token: str,
        dog_profile: DogProfile,
    ) -> None:
        """Test getting a single dog profile."""
        response = await async_client.get(
            f"/dogs/{dog_profile.id}",
            headers={"Authorization": f"Bearer {dog_owner_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(dog_profile.id)
        assert data["name"] == dog_profile.name
        assert data["breed"] == dog_profile.breed

    async def test_get_dog_profile_not_found(
        self,
        async_client: AsyncClient,
        dog_owner_token: str,
    ) -> None:
        """Test getting a non-existent dog profile."""
        non_existent_id = uuid4()
        response = await async_client.get(
            f"/dogs/{non_existent_id}",
            headers={"Authorization": f"Bearer {dog_owner_token}"},
        )

        assert response.status_code == 404

    async def test_get_dog_profile_wrong_owner(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        dog_profile: DogProfile,
    ) -> None:
        """Test getting a dog profile owned by another user."""
        # Create another user
        other_user = User(
            email="other@example.com",
            hashed_password="hashed",
            role=UserRole.DOG_OWNER,
            is_active=True,
        )
        db_session.add(other_user)
        await db_session.commit()
        await db_session.refresh(other_user)

        # Create token for other user
        other_token = create_access_token(
            user_id=other_user.id,
            email=other_user.email,
            role=other_user.role.value,
        )

        # Try to get the first user's dog
        response = await async_client.get(
            f"/dogs/{dog_profile.id}",
            headers={"Authorization": f"Bearer {other_token}"},
        )

        assert response.status_code == 404


class TestUpdateDogProfile:
    """Tests for PATCH /dogs/{dog_id} endpoint (T-303)."""

    async def test_update_dog_profile_success(
        self,
        async_client: AsyncClient,
        dog_owner_token: str,
        dog_profile: DogProfile,
    ) -> None:
        """Test updating a dog profile."""
        update_data = {
            "name": "MaxUpdated",
            "weight_kg": 32.0,
        }

        response = await async_client.patch(
            f"/dogs/{dog_profile.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {dog_owner_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "MaxUpdated"
        assert data["weight_kg"] == 32.0
        assert data["breed"] == dog_profile.breed  # Unchanged

    async def test_update_dog_profile_partial(
        self,
        async_client: AsyncClient,
        dog_owner_token: str,
        dog_profile: DogProfile,
    ) -> None:
        """Test partial update of dog profile."""
        update_data = {"blood_type": "DEA_1_1_POSITIVE"}

        response = await async_client.patch(
            f"/dogs/{dog_profile.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {dog_owner_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["blood_type"] == "DEA_1_1_POSITIVE"
        assert data["name"] == dog_profile.name  # Unchanged

    async def test_update_dog_profile_not_found(
        self,
        async_client: AsyncClient,
        dog_owner_token: str,
    ) -> None:
        """Test updating a non-existent dog profile."""
        non_existent_id = uuid4()
        update_data = {"name": "NewName"}

        response = await async_client.patch(
            f"/dogs/{non_existent_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {dog_owner_token}"},
        )

        assert response.status_code == 404

    async def test_update_dog_profile_invalid_age(
        self,
        async_client: AsyncClient,
        dog_owner_token: str,
        dog_profile: DogProfile,
    ) -> None:
        """Test updating with invalid age."""
        today = date.today()
        too_young = today - timedelta(days=180)

        update_data = {"date_of_birth": too_young.isoformat()}

        response = await async_client.patch(
            f"/dogs/{dog_profile.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {dog_owner_token}"},
        )

        assert response.status_code == 422


class TestDeleteDogProfile:
    """Tests for DELETE /dogs/{dog_id} endpoint (T-304)."""

    async def test_delete_dog_profile_success(
        self,
        async_client: AsyncClient,
        dog_owner_token: str,
        dog_profile: DogProfile,
    ) -> None:
        """Test deleting a dog profile."""
        response = await async_client.delete(
            f"/dogs/{dog_profile.id}",
            headers={"Authorization": f"Bearer {dog_owner_token}"},
        )

        assert response.status_code == 204

        # Verify deletion
        get_response = await async_client.get(
            f"/dogs/{dog_profile.id}",
            headers={"Authorization": f"Bearer {dog_owner_token}"},
        )
        assert get_response.status_code == 404

    async def test_delete_dog_profile_not_found(
        self,
        async_client: AsyncClient,
        dog_owner_token: str,
    ) -> None:
        """Test deleting a non-existent dog profile."""
        non_existent_id = uuid4()

        response = await async_client.delete(
            f"/dogs/{non_existent_id}",
            headers={"Authorization": f"Bearer {dog_owner_token}"},
        )

        assert response.status_code == 404


class TestUpdateDogAvailability:
    """Tests for PATCH /dogs/{dog_id}/availability endpoint (T-305)."""

    async def test_mark_dog_unavailable(
        self,
        async_client: AsyncClient,
        dog_owner_token: str,
        dog_profile: DogProfile,
    ) -> None:
        """Test marking a dog as unavailable."""
        update_data = {"is_active": False}

        response = await async_client.patch(
            f"/dogs/{dog_profile.id}/availability",
            json=update_data,
            headers={"Authorization": f"Bearer {dog_owner_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

    async def test_mark_dog_available(
        self,
        async_client: AsyncClient,
        dog_owner_token: str,
        dog_profile: DogProfile,
        db_session: AsyncSession,
    ) -> None:
        """Test marking a dog as available."""
        # First mark as unavailable
        dog_profile.is_active = False
        await db_session.commit()

        # Then mark as available
        update_data = {"is_active": True}

        response = await async_client.patch(
            f"/dogs/{dog_profile.id}/availability",
            json=update_data,
            headers={"Authorization": f"Bearer {dog_owner_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True

    async def test_update_availability_not_found(
        self,
        async_client: AsyncClient,
        dog_owner_token: str,
    ) -> None:
        """Test updating availability for non-existent dog."""
        non_existent_id = uuid4()
        update_data = {"is_active": False}

        response = await async_client.patch(
            f"/dogs/{non_existent_id}/availability",
            json=update_data,
            headers={"Authorization": f"Bearer {dog_owner_token}"},
        )

        assert response.status_code == 404

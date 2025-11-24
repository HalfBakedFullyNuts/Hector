"""Tests for database models."""

from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from hector.models import (
    BloodDonationRequest,
    Clinic,
    DogProfile,
    DonationResponse,
    User,
)
from hector.models.dog_profile import BloodType, DogSex
from hector.models.donation_request import RequestStatus, RequestUrgency
from hector.models.donation_response import ResponseStatus
from hector.models.user import UserRole


@pytest.mark.asyncio
@pytest.mark.skipif(
    "not config.getoption('--run-db-tests')",
    reason="Model tests require --run-db-tests flag and running PostgreSQL",
)
async def test_user_model_creation(db_session: AsyncSession):
    """Test creating a User model instance."""
    user = User(
        email="test@example.com",
        hashed_password="hashed_password_123",
        role=UserRole.DOG_OWNER,
        is_active=True,
        is_verified=False,
        full_name="Test User",
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.role == UserRole.DOG_OWNER
    assert user.is_active is True
    assert user.created_at is not None
    assert user.updated_at is not None


@pytest.mark.asyncio
@pytest.mark.skipif(
    "not config.getoption('--run-db-tests')",
    reason="Model tests require --run-db-tests flag and running PostgreSQL",
)
async def test_clinic_model_creation(db_session: AsyncSession):
    """Test creating a Clinic model instance."""
    # Create owner user first
    owner = User(
        email="clinic@example.com",
        hashed_password="hashed_password_123",
        role=UserRole.CLINIC_STAFF,
        is_active=True,
        is_verified=True,
    )
    db_session.add(owner)
    await db_session.commit()

    clinic = Clinic(
        owner_id=owner.id,
        name="Test Veterinary Clinic",
        address="123 Main St",
        city="Berlin",
        postal_code="10115",
        country="Germany",
        phone_number="+49 30 12345678",
        email="info@testclinic.de",
        is_approved=True,
        is_active=True,
    )

    db_session.add(clinic)
    await db_session.commit()
    await db_session.refresh(clinic)

    assert clinic.id is not None
    assert clinic.name == "Test Veterinary Clinic"
    assert clinic.city == "Berlin"
    assert clinic.is_approved is True


@pytest.mark.asyncio
@pytest.mark.skipif(
    "not config.getoption('--run-db-tests')",
    reason="Model tests require --run-db-tests flag and running PostgreSQL",
)
async def test_dog_profile_creation_and_eligibility(db_session: AsyncSession):
    """Test creating a DogProfile and checking eligibility."""
    # Create owner user first
    owner = User(
        email="dogowner@example.com",
        hashed_password="hashed_password_123",
        role=UserRole.DOG_OWNER,
        is_active=True,
        is_verified=True,
    )
    db_session.add(owner)
    await db_session.commit()

    # Create eligible dog
    dog = DogProfile(
        owner_id=owner.id,
        name="Max",
        breed="Golden Retriever",
        date_of_birth=date.today() - timedelta(days=365 * 3),  # 3 years old
        weight_kg=30.0,
        sex=DogSex.MALE,
        blood_type=BloodType.DEA_1_1_POSITIVE,
        is_active=True,
    )

    db_session.add(dog)
    await db_session.commit()
    await db_session.refresh(dog)

    assert dog.id is not None
    assert dog.name == "Max"
    assert dog.blood_type == BloodType.DEA_1_1_POSITIVE

    # Test eligibility
    assert dog.age_years == 3
    assert dog.is_eligible_for_donation is True


@pytest.mark.asyncio
@pytest.mark.skipif(
    "not config.getoption('--run-db-tests')",
    reason="Model tests require --run-db-tests flag and running PostgreSQL",
)
async def test_dog_profile_ineligible_weight(db_session: AsyncSession):
    """Test that dog under 25kg is not eligible."""
    owner = User(
        email="dogowner2@example.com",
        hashed_password="hashed_password_123",
        role=UserRole.DOG_OWNER,
        is_active=True,
        is_verified=True,
    )
    db_session.add(owner)
    await db_session.commit()

    dog = DogProfile(
        owner_id=owner.id,
        name="Tiny",
        breed="Chihuahua",
        date_of_birth=date.today() - timedelta(days=365 * 3),
        weight_kg=20.0,  # Under 25kg
        sex=DogSex.FEMALE,
        is_active=True,
    )

    db_session.add(dog)
    await db_session.commit()

    assert dog.is_eligible_for_donation is False


@pytest.mark.asyncio
@pytest.mark.skipif(
    "not config.getoption('--run-db-tests')",
    reason="Model tests require --run-db-tests flag and running PostgreSQL",
)
async def test_blood_donation_request_creation(db_session: AsyncSession):
    """Test creating a BloodDonationRequest."""
    # Create clinic and staff user
    staff_user = User(
        email="staff@clinic.com",
        hashed_password="hashed_password_123",
        role=UserRole.CLINIC_STAFF,
        is_active=True,
        is_verified=True,
    )
    db_session.add(staff_user)
    await db_session.commit()

    clinic = Clinic(
        owner_id=staff_user.id,
        name="Emergency Vet",
        address="456 Emergency Rd",
        city="Munich",
        postal_code="80331",
        country="Germany",
        phone_number="+49 89 12345678",
        email="emergency@vet.de",
        is_approved=True,
        is_active=True,
    )
    db_session.add(clinic)
    await db_session.commit()

    request = BloodDonationRequest(
        clinic_id=clinic.id,
        created_by_user_id=staff_user.id,
        blood_type_needed=BloodType.DEA_1_1_NEGATIVE,
        volume_ml=450,
        urgency=RequestUrgency.CRITICAL,
        status=RequestStatus.OPEN,
        patient_details="Large dog with acute blood loss",
        needed_by_date=datetime.now(UTC) + timedelta(hours=6),
    )

    db_session.add(request)
    await db_session.commit()
    await db_session.refresh(request)

    assert request.id is not None
    assert request.blood_type_needed == BloodType.DEA_1_1_NEGATIVE
    assert request.urgency == RequestUrgency.CRITICAL
    assert request.status == RequestStatus.OPEN


@pytest.mark.asyncio
@pytest.mark.skipif(
    "not config.getoption('--run-db-tests')",
    reason="Model tests require --run-db-tests flag and running PostgreSQL",
)
async def test_donation_response_creation(db_session: AsyncSession):
    """Test creating a DonationResponse."""
    # Create all prerequisite entities
    owner = User(
        email="responder@example.com",
        hashed_password="hashed_password_123",
        role=UserRole.DOG_OWNER,
        is_active=True,
        is_verified=True,
    )
    staff = User(
        email="staff2@clinic.com",
        hashed_password="hashed_password_123",
        role=UserRole.CLINIC_STAFF,
        is_active=True,
        is_verified=True,
    )
    db_session.add_all([owner, staff])
    await db_session.commit()

    clinic = Clinic(
        owner_id=staff.id,
        name="City Vet",
        address="789 City St",
        city="Hamburg",
        postal_code="20095",
        country="Germany",
        phone_number="+49 40 12345678",
        email="city@vet.de",
        is_approved=True,
        is_active=True,
    )
    db_session.add(clinic)
    await db_session.commit()

    dog = DogProfile(
        owner_id=owner.id,
        name="Buddy",
        breed="Labrador",
        date_of_birth=date.today() - timedelta(days=365 * 4),
        weight_kg=32.0,
        sex=DogSex.MALE,
        blood_type=BloodType.DEA_1_1_POSITIVE,
        is_active=True,
    )
    db_session.add(dog)
    await db_session.commit()

    request = BloodDonationRequest(
        clinic_id=clinic.id,
        created_by_user_id=staff.id,
        blood_type_needed=BloodType.DEA_1_1_POSITIVE,
        volume_ml=450,
        urgency=RequestUrgency.URGENT,
        status=RequestStatus.OPEN,
    )
    db_session.add(request)
    await db_session.commit()

    response = DonationResponse(
        request_id=request.id,
        dog_id=dog.id,
        owner_id=owner.id,
        status=ResponseStatus.ACCEPTED,
        response_message="Happy to help! We can come in tomorrow morning.",
    )
    db_session.add(response)
    await db_session.commit()
    await db_session.refresh(response)

    assert response.id is not None
    assert response.status == ResponseStatus.ACCEPTED
    assert response.response_message is not None


@pytest.mark.asyncio
@pytest.mark.skipif(
    "not config.getoption('--run-db-tests')",
    reason="Model tests require --run-db-tests flag and running PostgreSQL",
)
async def test_unique_constraint_request_dog(db_session: AsyncSession):
    """Test that the same dog cannot respond twice to the same request."""
    # Create prerequisite entities
    owner = User(
        email="unique_test@example.com",
        hashed_password="hashed_password_123",
        role=UserRole.DOG_OWNER,
        is_active=True,
        is_verified=True,
    )
    staff = User(
        email="unique_staff@clinic.com",
        hashed_password="hashed_password_123",
        role=UserRole.CLINIC_STAFF,
        is_active=True,
        is_verified=True,
    )
    db_session.add_all([owner, staff])
    await db_session.commit()

    clinic = Clinic(
        owner_id=staff.id,
        name="Unique Vet",
        address="999 Unique St",
        city="Frankfurt",
        postal_code="60311",
        country="Germany",
        phone_number="+49 69 12345678",
        email="unique@vet.de",
        is_approved=True,
        is_active=True,
    )
    db_session.add(clinic)
    await db_session.commit()

    dog = DogProfile(
        owner_id=owner.id,
        name="UniqueD og",
        breed="Beagle",
        date_of_birth=date.today() - timedelta(days=365 * 3),
        weight_kg=28.0,
        sex=DogSex.FEMALE,
        is_active=True,
    )
    db_session.add(dog)
    await db_session.commit()

    request = BloodDonationRequest(
        clinic_id=clinic.id,
        created_by_user_id=staff.id,
        volume_ml=450,
        urgency=RequestUrgency.ROUTINE,
        status=RequestStatus.OPEN,
    )
    db_session.add(request)
    await db_session.commit()

    # First response should succeed
    response1 = DonationResponse(
        request_id=request.id,
        dog_id=dog.id,
        owner_id=owner.id,
        status=ResponseStatus.ACCEPTED,
    )
    db_session.add(response1)
    await db_session.commit()

    # Second response with same dog and request should fail
    response2 = DonationResponse(
        request_id=request.id,
        dog_id=dog.id,
        owner_id=owner.id,
        status=ResponseStatus.DECLINED,
    )
    db_session.add(response2)

    with pytest.raises(Exception):  # SQLAlchemy will raise IntegrityError
        await db_session.commit()

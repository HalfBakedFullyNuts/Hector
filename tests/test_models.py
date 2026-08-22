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


def _make_user(email: str, role: UserRole) -> User:
    """Build a minimal valid user for model tests."""
    assert email and role
    return User(email=email, hashed_password="hashed_password_123", role=role)


def _make_clinic(name: str, city: str) -> Clinic:
    """Build a minimal valid clinic for model tests."""
    assert name and city
    return Clinic(
        name=name,
        address="123 Test St",
        city=city,
        postal_code="10115",
        phone="+49 30 12345678",
        email=f"info@{name.lower().replace(' ', '')}.de",
        is_approved=True,
    )


@pytest.mark.asyncio
async def test_user_model_creation(db_session: AsyncSession):
    """Test creating a User model instance."""
    user = _make_user("test@example.com", UserRole.DOG_OWNER)
    user.is_active = True
    user.is_verified = False

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
async def test_clinic_model_creation(db_session: AsyncSession):
    """Test creating a Clinic model instance."""
    clinic = _make_clinic("Test Veterinary Clinic", "Berlin")

    db_session.add(clinic)
    await db_session.commit()
    await db_session.refresh(clinic)

    assert clinic.id is not None
    assert clinic.name == "Test Veterinary Clinic"
    assert clinic.city == "Berlin"
    assert clinic.is_approved is True
    assert clinic.is_approved is True


@pytest.mark.asyncio
async def test_dog_profile_creation_and_eligibility(db_session: AsyncSession):
    """Test creating a DogProfile and checking eligibility."""
    owner = _make_user("dogowner@example.com", UserRole.DOG_OWNER)
    db_session.add(owner)
    await db_session.commit()

    dog = DogProfile(
        owner_id=owner.id,
        name="Max",
        breed="Golden Retriever",
        date_of_birth=date.today() - timedelta(days=365 * 3),
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

    assert dog.age_years == 3
    assert dog.is_eligible_for_donation is True


@pytest.mark.asyncio
async def test_dog_profile_ineligible_weight(db_session: AsyncSession):
    """Test that dog under 25kg is not eligible."""
    owner = _make_user("dogowner2@example.com", UserRole.DOG_OWNER)
    db_session.add(owner)
    await db_session.commit()

    dog = DogProfile(
        owner_id=owner.id,
        name="Tiny",
        breed="Chihuahua",
        date_of_birth=date.today() - timedelta(days=365 * 3),
        weight_kg=20.0,
        sex=DogSex.FEMALE,
        is_active=True,
    )

    db_session.add(dog)
    await db_session.commit()

    assert dog.is_eligible_for_donation is False


@pytest.mark.asyncio
async def test_blood_donation_request_creation(db_session: AsyncSession):
    """Test creating a BloodDonationRequest."""
    staff_user = _make_user("staff@clinic.com", UserRole.CLINIC_STAFF)
    db_session.add(staff_user)
    await db_session.commit()

    clinic = _make_clinic("Emergency Vet", "Munich")
    db_session.add(clinic)
    await db_session.commit()

    request = BloodDonationRequest(
        clinic_id=clinic.id,
        created_by_user_id=staff_user.id,
        blood_type_needed=BloodType.DEA_1_1_NEGATIVE,
        volume_ml=450,
        urgency=RequestUrgency.CRITICAL,
        status=RequestStatus.OPEN,
        patient_info="Large dog with acute blood loss",
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
async def test_donation_response_creation(db_session: AsyncSession):
    """Test creating a DonationResponse."""
    owner = _make_user("responder@example.com", UserRole.DOG_OWNER)
    staff = _make_user("staff2@clinic.com", UserRole.CLINIC_STAFF)
    db_session.add_all([owner, staff])
    await db_session.commit()

    clinic = _make_clinic("City Vet", "Hamburg")
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
        needed_by_date=datetime.now(UTC) + timedelta(days=7),
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
async def test_unique_constraint_request_dog(db_session: AsyncSession):
    """Test that the same dog cannot respond twice to the same request."""
    owner = _make_user("unique_test@example.com", UserRole.DOG_OWNER)
    staff = _make_user("unique_staff@clinic.com", UserRole.CLINIC_STAFF)
    db_session.add_all([owner, staff])
    await db_session.commit()

    clinic = _make_clinic("Unique Vet", "Frankfurt")
    db_session.add(clinic)
    await db_session.commit()

    dog = DogProfile(
        owner_id=owner.id,
        name="UniqueDog",
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
        needed_by_date=datetime.now(UTC) + timedelta(days=7),
    )
    db_session.add(request)
    await db_session.commit()

    from sqlalchemy.exc import IntegrityError

    response1 = DonationResponse(
        request_id=request.id,
        dog_id=dog.id,
        owner_id=owner.id,
        status=ResponseStatus.ACCEPTED,
    )
    db_session.add(response1)
    await db_session.commit()

    response2 = DonationResponse(
        request_id=request.id,
        dog_id=dog.id,
        owner_id=owner.id,
        status=ResponseStatus.DECLINED,
    )
    db_session.add(response2)

    with pytest.raises(IntegrityError):
        await db_session.commit()

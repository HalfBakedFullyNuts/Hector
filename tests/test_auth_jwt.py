"""Tests for JWT token generation and validation."""

import time
from datetime import timedelta
from uuid import uuid4

from hector.auth.jwt import (
    TokenPayload,
    create_access_token,
    create_refresh_token,
    create_token_pair,
    decode_token_unsafe,
    verify_token,
)
from hector.models.user import UserRole


def test_create_access_token_returns_valid_token():
    """Test that create_access_token returns a JWT token."""
    user_id = uuid4()
    email = "test@example.com"
    role = UserRole.DOG_OWNER.value

    token = create_access_token(user_id, email, role)

    assert isinstance(token, str)
    assert len(token) > 0
    assert token.count(".") == 2  # JWT format: header.payload.signature


def test_create_access_token_with_custom_expiration():
    """Test creating token with custom expiration time."""
    user_id = uuid4()
    email = "test@example.com"
    role = UserRole.CLINIC_STAFF.value
    expires_delta = timedelta(minutes=30)

    token = create_access_token(user_id, email, role, expires_delta)

    payload = verify_token(token, "access")
    assert payload is not None
    assert payload.token_type == "access"


def test_create_refresh_token_returns_valid_token():
    """Test that create_refresh_token returns a JWT token."""
    user_id = uuid4()
    email = "test@example.com"
    role = UserRole.ADMIN.value

    token = create_refresh_token(user_id, email, role)

    assert isinstance(token, str)
    assert len(token) > 0
    assert token.count(".") == 2


def test_create_refresh_token_with_custom_expiration():
    """Test creating refresh token with custom expiration."""
    user_id = uuid4()
    email = "test@example.com"
    role = UserRole.DOG_OWNER.value
    expires_delta = timedelta(days=14)

    token = create_refresh_token(user_id, email, role, expires_delta)

    payload = verify_token(token, "refresh")
    assert payload is not None
    assert payload.token_type == "refresh"


def test_create_token_pair_returns_both_tokens():
    """Test that create_token_pair returns access and refresh tokens."""
    user_id = uuid4()
    email = "test@example.com"
    role = UserRole.CLINIC_STAFF.value

    token_pair = create_token_pair(user_id, email, role)

    assert token_pair.access_token is not None
    assert token_pair.refresh_token is not None
    assert token_pair.token_type == "bearer"
    assert len(token_pair.access_token) > 0
    assert len(token_pair.refresh_token) > 0


def test_verify_token_with_valid_access_token():
    """Test that verify_token validates a valid access token."""
    user_id = uuid4()
    email = "test@example.com"
    role = UserRole.DOG_OWNER.value

    token = create_access_token(user_id, email, role)
    payload = verify_token(token, "access")

    assert payload is not None
    assert isinstance(payload, TokenPayload)
    assert payload.sub == str(user_id)
    assert payload.email == email
    assert payload.role == role
    assert payload.token_type == "access"


def test_verify_token_with_valid_refresh_token():
    """Test that verify_token validates a valid refresh token."""
    user_id = uuid4()
    email = "refresh@example.com"
    role = UserRole.ADMIN.value

    token = create_refresh_token(user_id, email, role)
    payload = verify_token(token, "refresh")

    assert payload is not None
    assert payload.sub == str(user_id)
    assert payload.email == email
    assert payload.token_type == "refresh"


def test_verify_token_rejects_wrong_token_type():
    """Test that verify_token rejects token with wrong type."""
    user_id = uuid4()
    email = "test@example.com"
    role = UserRole.DOG_OWNER.value

    # Create access token but try to verify as refresh
    token = create_access_token(user_id, email, role)
    payload = verify_token(token, "refresh")

    assert payload is None


def test_verify_token_rejects_invalid_token():
    """Test that verify_token rejects invalid tokens."""
    assert verify_token("invalid.token.here", "access") is None
    assert verify_token("", "access") is None
    assert verify_token("not-a-jwt", "access") is None


def test_verify_token_rejects_expired_token():
    """Test that verify_token rejects expired tokens."""
    user_id = uuid4()
    email = "test@example.com"
    role = UserRole.DOG_OWNER.value

    # Create token that expires immediately
    token = create_access_token(user_id, email, role, timedelta(seconds=-1))

    # Token should be expired
    payload = verify_token(token, "access")
    assert payload is None


def test_token_payload_includes_all_required_fields():
    """Test that token payload includes all required fields."""
    user_id = uuid4()
    email = "complete@example.com"
    role = UserRole.CLINIC_STAFF.value

    token = create_access_token(user_id, email, role)
    payload = verify_token(token, "access")

    assert payload is not None
    assert hasattr(payload, "sub")
    assert hasattr(payload, "email")
    assert hasattr(payload, "role")
    assert hasattr(payload, "exp")
    assert hasattr(payload, "iat")
    assert hasattr(payload, "token_type")


def test_token_timestamps_are_valid():
    """Test that issued_at and expiration timestamps are valid."""
    user_id = uuid4()
    email = "time@example.com"
    role = UserRole.DOG_OWNER.value

    before = int(time.time())
    token = create_access_token(user_id, email, role)
    after = int(time.time())

    payload = verify_token(token, "access")
    assert payload is not None

    # Issued at should be between before and after
    assert before <= payload.iat <= after

    # Expiration should be in the future (default 15 minutes)
    assert payload.exp > payload.iat
    assert payload.exp - payload.iat >= 15 * 60  # At least 15 minutes


def test_decode_token_unsafe_returns_payload():
    """Test that decode_token_unsafe decodes without verification."""
    user_id = uuid4()
    email = "unsafe@example.com"
    role = UserRole.ADMIN.value

    token = create_access_token(user_id, email, role)
    payload = decode_token_unsafe(token)

    assert payload is not None
    assert payload["sub"] == str(user_id)
    assert payload["email"] == email
    assert payload["role"] == role


def test_decode_token_unsafe_works_on_expired_token():
    """Test that decode_token_unsafe decodes expired tokens."""
    user_id = uuid4()
    email = "expired@example.com"
    role = UserRole.DOG_OWNER.value

    # Create expired token
    token = create_access_token(user_id, email, role, timedelta(seconds=-1))

    # verify_token should reject it
    assert verify_token(token, "access") is None

    # decode_token_unsafe should still decode it
    payload = decode_token_unsafe(token)
    assert payload is not None
    assert payload["sub"] == str(user_id)


def test_decode_token_unsafe_returns_none_for_invalid():
    """Test that decode_token_unsafe returns None for invalid tokens."""
    assert decode_token_unsafe("") is None
    assert decode_token_unsafe("not-a-token") is None


def test_different_users_get_different_tokens():
    """Test that different users get different tokens."""
    user1_id = uuid4()
    user2_id = uuid4()
    email = "same@example.com"
    role = UserRole.DOG_OWNER.value

    token1 = create_access_token(user1_id, email, role)
    token2 = create_access_token(user2_id, email, role)

    assert token1 != token2

    payload1 = verify_token(token1, "access")
    payload2 = verify_token(token2, "access")

    assert payload1 is not None
    assert payload2 is not None
    assert payload1.sub != payload2.sub


def test_same_user_gets_different_tokens():
    """Test that same user gets different tokens each time (due to iat)."""
    user_id = uuid4()
    email = "repeat@example.com"
    role = UserRole.DOG_OWNER.value

    token1 = create_access_token(user_id, email, role)
    time.sleep(1)  # Ensure different timestamp
    token2 = create_access_token(user_id, email, role)

    assert token1 != token2

    payload1 = verify_token(token1, "access")
    payload2 = verify_token(token2, "access")

    assert payload1 is not None
    assert payload2 is not None
    assert payload1.sub == payload2.sub
    assert payload1.iat != payload2.iat

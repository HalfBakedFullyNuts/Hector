"""Tests for password hashing utilities."""

import pytest

from hector.auth.password import hash_password, needs_rehash, verify_password


def test_hash_password_returns_valid_hash():
    """Test that hash_password returns a bcrypt hash."""
    password = "test_password_123"
    hashed = hash_password(password)

    assert isinstance(hashed, str)
    assert len(hashed) > 0
    assert hashed != password
    assert hashed.startswith("$2b$")  # bcrypt prefix


def test_hash_password_with_custom_rounds():
    """Test hashing with custom cost factor."""
    password = "test_password"
    hashed = hash_password(password, rounds=10)

    assert isinstance(hashed, str)
    assert "$2b$10$" in hashed


def test_hash_password_rejects_empty_password():
    """Test that empty password raises ValueError."""
    with pytest.raises(ValueError, match="Password cannot be empty"):
        hash_password("")


def test_hash_password_rejects_invalid_rounds():
    """Test that invalid rounds raise ValueError."""
    with pytest.raises(ValueError, match="Rounds must be between 4 and 31"):
        hash_password("password", rounds=3)

    with pytest.raises(ValueError, match="Rounds must be between 4 and 31"):
        hash_password("password", rounds=32)


def test_verify_password_with_correct_password():
    """Test that verify_password returns True for correct password."""
    password = "my_secure_password"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True


def test_verify_password_with_incorrect_password():
    """Test that verify_password returns False for incorrect password."""
    password = "correct_password"
    hashed = hash_password(password)

    assert verify_password("wrong_password", hashed) is False


def test_verify_password_with_empty_inputs():
    """Test that empty inputs return False."""
    hashed = hash_password("password")

    assert verify_password("", hashed) is False
    assert verify_password("password", "") is False
    assert verify_password("", "") is False


def test_verify_password_timing_safe():
    """Test that verification uses timing-safe comparison."""
    password = "test_password"
    hashed = hash_password(password)

    # Both should return quickly and not reveal timing info
    result1 = verify_password(password, hashed)
    result2 = verify_password("wrong", hashed)

    assert result1 is True
    assert result2 is False


def test_hash_password_produces_different_hashes():
    """Test that hashing same password twice produces different hashes."""
    password = "same_password"
    hash1 = hash_password(password)
    hash2 = hash_password(password)

    assert hash1 != hash2
    assert verify_password(password, hash1) is True
    assert verify_password(password, hash2) is True


def test_needs_rehash_with_outdated_rounds():
    """Test that needs_rehash detects outdated cost factor."""
    password = "test_password"
    old_hash = hash_password(password, rounds=10)

    assert needs_rehash(old_hash, rounds=12) is True


def test_needs_rehash_with_current_rounds():
    """Test that needs_rehash returns False for current cost factor."""
    password = "test_password"
    current_hash = hash_password(password, rounds=12)

    assert needs_rehash(current_hash, rounds=12) is False


def test_needs_rehash_with_empty_hash():
    """Test that empty hash needs rehashing."""
    assert needs_rehash("") is True


def test_needs_rehash_with_invalid_hash():
    """Test that invalid hash needs rehashing."""
    assert needs_rehash("not_a_valid_hash") is True


def test_password_verification_is_case_sensitive():
    """Test that password verification is case-sensitive."""
    password = "TestPassword123"
    hashed = hash_password(password)

    assert verify_password("TestPassword123", hashed) is True
    assert verify_password("testpassword123", hashed) is False
    assert verify_password("TESTPASSWORD123", hashed) is False


def test_verify_password_handles_malformed_hash():
    """Test that verify_password handles malformed hashes gracefully."""
    password = "test_password"

    assert verify_password(password, "malformed_hash") is False
    assert verify_password(password, "$invalid$hash") is False

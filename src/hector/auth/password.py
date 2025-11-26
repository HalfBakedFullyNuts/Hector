"""Password hashing utilities using bcrypt.

This module provides secure password hashing and verification
using the bcrypt algorithm with configurable cost factor.
"""

import bcrypt


def hash_password(password: str, rounds: int = 12) -> str:
    """
    Hash a plaintext password using bcrypt.

    Generates a secure bcrypt hash of the provided password.
    The cost factor (rounds) determines computational complexity.

    Args:
        password: Plaintext password to hash
        rounds: Bcrypt cost factor (default 12, range 4-31)

    Returns:
        Bcrypt hash string

    Example:
        >>> hashed = hash_password("my_secret_password")
        >>> len(hashed) > 0
        True
    """
    if not password:
        raise ValueError("Password cannot be empty")

    if rounds < 4 or rounds > 31:
        raise ValueError("Rounds must be between 4 and 31")

    # Convert password to bytes and generate salt with specified rounds
    password_bytes: bytes = password.encode("utf-8")
    salt: bytes = bcrypt.gensalt(rounds=rounds)
    hashed: bytes = bcrypt.hashpw(password_bytes, salt)

    # Return as string
    result: str = hashed.decode("utf-8")
    return result


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against a bcrypt hash.

    Uses timing-safe comparison to prevent timing attacks.
    Returns False for any error to avoid revealing information.

    Args:
        plain_password: Plaintext password to verify
        hashed_password: Bcrypt hash to verify against

    Returns:
        True if password matches hash, False otherwise

    Example:
        >>> hashed = hash_password("test_password")
        >>> verify_password("test_password", hashed)
        True
        >>> verify_password("wrong_password", hashed)
        False
    """
    if not plain_password or not hashed_password:
        return False

    try:
        password_bytes: bytes = plain_password.encode("utf-8")
        hash_bytes: bytes = hashed_password.encode("utf-8")
        result: bool = bcrypt.checkpw(password_bytes, hash_bytes)
        return result
    except Exception:
        # Return False for any verification error
        # Prevents information leakage about hash validity
        return False


def needs_rehash(hashed_password: str, rounds: int = 12) -> bool:
    """
    Check if a password hash needs to be regenerated.

    Useful for upgrading hashes when cost factor changes
    or when migrating from deprecated algorithms.

    Args:
        hashed_password: Bcrypt hash to check
        rounds: Target bcrypt cost factor (default 12)

    Returns:
        True if hash should be regenerated, False otherwise

    Example:
        >>> hashed = hash_password("password", rounds=10)
        >>> needs_rehash(hashed, rounds=12)
        True
    """
    if not hashed_password:
        return True

    try:
        # Extract the cost factor from the hash
        # Bcrypt hash format: $2b$<cost>$<salt><hash>
        parts = hashed_password.split("$")

        if len(parts) < 4:
            return True

        current_rounds = int(parts[2])
        return current_rounds < rounds
    except Exception:
        return True

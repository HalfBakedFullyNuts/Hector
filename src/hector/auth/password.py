"""Password hashing utilities using bcrypt."""

from passlib.context import CryptContext  # type: ignore[import-untyped]

# Configure password hashing context
# Using bcrypt with recommended cost factor of 12
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
)


def hash_password(password: str) -> str:
    """
    Hash a plain text password using bcrypt.

    Args:
        password: The plain text password to hash

    Returns:
        The bcrypt hashed password string
    """
    result: str = pwd_context.hash(password)
    return result


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed password.

    Uses timing-safe comparison to prevent timing attacks.

    Args:
        plain_password: The plain text password to verify
        hashed_password: The hashed password to compare against

    Returns:
        True if the password matches, False otherwise
    """
    result: bool = pwd_context.verify(plain_password, hashed_password)
    return result

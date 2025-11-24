"""Authentication and authorization module for Hector.

This module provides:
- Password hashing and verification (bcrypt)
- JWT token generation and validation
- User authentication endpoints
- Role-based authorization
"""

from .jwt import (
    TokenPair,
    TokenPayload,
    create_access_token,
    create_refresh_token,
    create_token_pair,
    decode_token_unsafe,
    verify_token,
)
from .password import hash_password, needs_rehash, verify_password

__all__ = [
    "hash_password",
    "verify_password",
    "needs_rehash",
    "create_access_token",
    "create_refresh_token",
    "create_token_pair",
    "verify_token",
    "decode_token_unsafe",
    "TokenPayload",
    "TokenPair",
]

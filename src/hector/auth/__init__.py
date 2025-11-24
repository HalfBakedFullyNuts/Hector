"""Authentication and authorization module for Hector.

This module provides:
- Password hashing and verification (bcrypt)
- JWT token generation and validation
- User authentication endpoints
- Role-based authorization
"""

from .password import hash_password, needs_rehash, verify_password

__all__ = [
    "hash_password",
    "verify_password",
    "needs_rehash",
]

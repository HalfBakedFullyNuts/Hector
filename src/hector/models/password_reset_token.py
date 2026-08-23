"""Password reset token model for single-use reset links."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class PasswordResetToken(BaseModel):
    """Hashed single-use token with expiry; raw tokens are never stored."""

    __tablename__ = "password_reset_tokens"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="User whose password may be reset with this token",
    )

    token_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
        doc="SHA-256 hex digest of the reset token",
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="Timestamp after which the token is invalid",
    )

    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when the token was consumed",
    )

    requested_ip: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        doc="IP that requested the reset (audit aid)",
    )

    def __repr__(self) -> str:
        """Return string representation of the reset token."""
        return f"<PasswordResetToken(user_id={self.user_id}, used_at={self.used_at})>"

"""Email log model for outbound notification records."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel

if TYPE_CHECKING:
    pass


class EmailLog(BaseModel):
    """Record of every outbound email attempt (sent, logged, or failed)."""

    __tablename__ = "email_log"

    recipient: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        doc="Email address of the recipient",
    )

    subject: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Email subject line",
    )

    body_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Plain-text email body",
    )

    template: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Template identifier used to render this email",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="logged",
        doc="One of: sent, logged (log mode), failed",
    )

    related_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Entity type this email relates to (request/response/user)",
    )

    related_id: Mapped[UUID | None] = mapped_column(
        nullable=True,
        doc="Identifier of the related entity",
    )

    def __repr__(self) -> str:
        """Return string representation of the email log entry."""
        return f"<EmailLog(to={self.recipient}, subject={self.subject!r}, status={self.status})>"

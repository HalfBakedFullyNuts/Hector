"""Audit log model for tracking privileged administrative actions."""

from typing import Any
from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class AuditLog(BaseModel):
    """Immutable record of a privileged action (T-701/T-702/T-704)."""

    __tablename__ = "audit_logs"

    actor_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Admin who performed the action (null if deleted)",
    )

    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Machine-readable action name, e.g. 'user.toggle_active'",
    )

    target_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Entity type the action was performed on",
    )

    target_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        doc="Identifier of the affected entity",
    )

    details: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        doc="Structured context, e.g. {'reason': 'not a clinic'}",
    )

    def __repr__(self) -> str:
        """Return string representation of the audit entry."""
        return f"<AuditLog(action={self.action}, target={self.target_type}:{self.target_id})>"

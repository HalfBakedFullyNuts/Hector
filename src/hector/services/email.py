"""Outbound email service (T-1000).

Default transport is log mode: emails are printed to the log and persisted
to email_log so flows can be tested without an SMTP server. Configure
HECTOR_SMTP_HOST (plus user/password/from) to switch to real SMTP.
"""

import logging
from email.message import EmailMessage
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

import aiosmtplib

from hector.config import Settings, get_settings
from hector.models.email_log import EmailLog

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

LOG = logging.getLogger(__name__)

UNSUBSCRIBE_FOOTER = (
    "\n\n---\nYou receive this because you registered as a donor on Hector. "
    "Unsubscribe: /auth/unsubscribe (not yet available)."
)


class EmailStatus(StrEnum):
    """Lifecycle states recorded in email_log."""

    SENT = "sent"
    LOGGED = "logged"
    FAILED = "failed"


async def send_email(
    db: "AsyncSession",
    recipient: str,
    subject: str,
    body_text: str,
    template: str | None = None,
    related_type: str | None = None,
    related_id: UUID | None = None,
) -> EmailStatus:
    """Deliver an email via SMTP or log mode; always records the attempt."""
    assert recipient and subject and body_text, "recipient/subject/body are required"

    settings = get_settings()
    status = await _deliver(settings, recipient, subject, body_text)

    db.add(
        EmailLog(
            recipient=recipient,
            subject=subject,
            body_text=body_text,
            template=template,
            status=status.value if isinstance(status, EmailStatus) else str(status),
            related_type=related_type,
            related_id=related_id,
        )
    )
    await db.commit()
    return status


async def _deliver(settings: Settings, recipient: str, subject: str, body_text: str) -> EmailStatus:
    """Send over SMTP when configured; otherwise print to the service log."""
    if not settings.smtp_host:
        LOG.info("email [log-mode] to=%s subject=%r\n%s", recipient, subject, body_text)
        return EmailStatus.LOGGED

    message = EmailMessage()
    message["From"] = settings.smtp_from
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body_text)

    try:
        client = aiosmtplib.SMTP(
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            start_tls=settings.smtp_start_tls,
        )
        await client.connect()
        try:
            if settings.smtp_user:
                await client.login(settings.smtp_user, settings.smtp_password or "")
            await client.send_message(message)
        finally:
            await client.quit()
        return EmailStatus.SENT
    except Exception as exc:  # noqa: BLE001 - delivery must never crash requests
        LOG.error("email delivery failed to=%s: %s", recipient, exc)
        return EmailStatus.FAILED

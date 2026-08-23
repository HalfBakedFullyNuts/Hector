"""Tests for the email service (T-1000)."""

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hector.models.email_log import EmailLog
from hector.services.email import EmailStatus, send_email


async def test_log_mode_writes_console_and_db_row(
    db_session: AsyncSession, caplog
) -> None:
    """Default transport logs to the service log and persists an email_log row."""
    import logging as _logging

    with caplog.at_level(_logging.INFO, logger="hector.services.email"):
        status = await send_email(
            db=db_session,
            recipient="owner@example.com",
            subject="Blood donation request in Berlin",
            body_text="A clinic near you needs DEA 1.1 negative blood.",
            template="match_notification",
            related_type="request",
            related_id=uuid4(),
        )

    assert status is EmailStatus.LOGGED
    assert "owner@example.com" in caplog.text

    row = (
        await db_session.execute(select(EmailLog).where(EmailLog.recipient == "owner@example.com"))
    ).scalar_one()
    assert row.status == "logged"
    assert row.template == "match_notification"
    assert row.related_type == "request"


async def test_smtp_mode_sends_and_records(db_session: AsyncSession, monkeypatch) -> None:
    """When SMTP is configured the message is sent via aiosmtplib."""
    sent: dict = {}

    class FakeSMTP:
        def __init__(self, hostname: str, port: int, start_tls: bool) -> None:
            sent["hostname"] = hostname

        async def connect(self) -> None:
            sent["connected"] = True

        async def send_message(self, message) -> None:
            sent["to"] = str(message["To"])
            sent["subject"] = str(message["Subject"])

        async def login(self, user: str, password: str) -> None:
            sent["user"] = user

        async def quit(self) -> None:
            sent["quit"] = True

    from hector.services import email as email_module

    monkeypatch.setattr(email_module, "get_settings", lambda: _smtp_settings())
    monkeypatch.setattr(email_module.aiosmtplib, "SMTP", FakeSMTP)

    status = await send_email(
        db=db_session,
        recipient="clinic@example.com",
        subject="New donor response",
        body_text="Someone accepted!",
        template="response_received",
    )

    assert status is EmailStatus.SENT
    assert sent["connected"] is True
    assert sent["to"] == "clinic@example.com"

    row = (
        await db_session.execute(
            select(EmailLog).where(EmailLog.recipient == "clinic@example.com")
        )
    ).scalar_one()
    assert row.status == "sent"


async def test_failure_recorded_as_failed(db_session: AsyncSession, monkeypatch) -> None:
    """Transport errors are swallowed and recorded as failed rows."""
    from hector.services import email as email_module

    class ExplodingSMTP:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def connect(self) -> None:
            raise ConnectionError("smtp down")

    monkeypatch.setattr(email_module, "get_settings", lambda: _smtp_settings())
    monkeypatch.setattr(email_module.aiosmtplib, "SMTP", ExplodingSMTP)

    status = await send_email(
        db=db_session,
        recipient="x@example.com",
        subject="s",
        body_text="b",
        template="t",
    )

    assert status is EmailStatus.FAILED
    row = (
        await db_session.execute(select(EmailLog).where(EmailLog.recipient == "x@example.com"))
    ).scalar_one()
    assert row.status == "failed"


def _smtp_settings():
    """Settings stub with SMTP enabled."""
    from hector.config import Settings

    return Settings(
        _env_file=None,
        environment="test",
        database_url="postgresql+asyncpg://u:p@localhost/db",
        jwt_secret_key="test-only-signing-key-with-more-than-32-characters",
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_user="mailer",
        smtp_password="mailpass",
        smtp_from="no-reply@hector.local",
    )


def test_email_status_enum_members() -> None:
    """The three lifecycle statuses exist."""
    assert {s.value for s in EmailStatus} == {"sent", "logged", "failed"}

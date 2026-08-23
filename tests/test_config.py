"""Configuration loading tests."""

import pytest

from hector.config import get_settings, reset_settings_cache


@pytest.fixture(autouse=True)
def clear_cache() -> None:
    reset_settings_cache()


def test_get_settings_requires_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    # This test verifies that Settings validation works correctly
    # We directly instantiate Settings with env_file disabled to test validation
    from pydantic import ValidationError

    from hector.config import Settings

    monkeypatch.delenv("HECTOR_ENVIRONMENT", raising=False)
    monkeypatch.delenv("HECTOR_DATABASE_URL", raising=False)

    with pytest.raises(ValidationError) as exc:
        Settings(_env_file=None)  # type: ignore[call-arg]

    # Should fail on missing required fields
    errors = str(exc.value)
    assert "environment" in errors.lower() or "database_url" in errors.lower()


def test_get_settings_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HECTOR_ENVIRONMENT", "test")
    monkeypatch.setenv("HECTOR_PORT", "9001")
    monkeypatch.setenv("HECTOR_DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

    settings = get_settings()

    assert settings.environment == "test"
    assert settings.port == 9001


def test_settings_reject_known_default_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    """The example secret from .env.example must never pass validation."""
    from pydantic import ValidationError

    from hector.config import Settings

    monkeypatch.setenv("HECTOR_ENVIRONMENT", "test")
    monkeypatch.setenv("HECTOR_DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/d")
    monkeypatch.setenv("HECTOR_JWT_SECRET_KEY", "your-secret-key-here-change-in-production")

    with pytest.raises(ValidationError, match="known-default"):
        Settings(_env_file=None)  # type: ignore[call-arg]


def test_settings_asdict_masks_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    """settings_asdict must never expose the raw JWT secret or DB password."""
    from hector.config import Settings, settings_asdict

    monkeypatch.setenv("HECTOR_ENVIRONMENT", "test")
    monkeypatch.setenv("HECTOR_JWT_SECRET_KEY", "super-secret-value-that-must-not-leak-1234")
    monkeypatch.setenv(
        "HECTOR_DATABASE_URL", "postgresql+asyncpg://user:dbpassw0rd@localhost:5433/db"
    )

    data = settings_asdict(Settings(_env_file=None))  # type: ignore[call-arg]

    assert data["jwt_secret_key"] == "***"
    assert "dbpassw0rd" not in str(data)

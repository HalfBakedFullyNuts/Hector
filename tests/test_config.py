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

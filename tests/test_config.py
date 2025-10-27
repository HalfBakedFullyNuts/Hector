"""Configuration loading tests."""

import os

import pytest

from hector.config import get_settings, reset_settings_cache


@pytest.fixture(autouse=True)
def clear_cache() -> None:
    reset_settings_cache()


def test_get_settings_requires_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HECTOR_ENVIRONMENT", raising=False)

    with pytest.raises(RuntimeError) as exc:
        get_settings()

    assert "environment" in str(exc.value)


def test_get_settings_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HECTOR_ENVIRONMENT", "test")
    monkeypatch.setenv("HECTOR_PORT", "9001")

    settings = get_settings()

    assert settings.environment == "test"
    assert settings.port == 9001

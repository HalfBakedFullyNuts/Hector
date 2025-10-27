"""Application settings management."""

from functools import lru_cache
from typing import Any

from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration values sourced from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="HECTOR_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    port: int = Field(8000, ge=1, le=65535, description="Port the HTTP server listens on")
    log_level: str = Field(
        "INFO",
        description="Logging level for the service",
        pattern=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
    )
    environment: str = Field(
        ...,
        description="Deployment environment identifier",
        pattern=r"^[A-Za-z0-9_-]+$",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load settings and cache the result for reuse."""

    try:
        return Settings()
    except ValidationError as exc:  # pragma: no cover - defensive
        errors = ", ".join(
            f"{e['loc'][0]}: {e['msg']}" for e in exc.errors()
        )
        raise RuntimeError(f"Invalid configuration: {errors}") from exc


def reset_settings_cache() -> None:
    """Clear the settings cache (useful for tests)."""

    get_settings.cache_clear()


def settings_asdict(settings: Settings) -> dict[str, Any]:
    """Return settings as a plain dict for logging/debugging."""

    return settings.model_dump()

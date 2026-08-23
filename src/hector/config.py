"""Application settings management."""

from functools import lru_cache
from typing import Any

from pydantic import Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Exact-match secrets that must never be accepted (design D4 / B2).
KNOWN_DEFAULT_SECRETS = frozenset(
    {
        "your-secret-key-here-change-in-production",
        "changeme",
        "secret",
        "my-secret-key",
    }
)

_SENSITIVE_URL_MARKER = ":***@"


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

    # Database settings
    database_url: str = Field(
        ...,
        description="PostgreSQL database connection string",
    )
    db_pool_size: int = Field(5, ge=1, le=50, description="Database connection pool size")
    db_max_overflow: int = Field(
        10, ge=0, le=100, description="Maximum number of connections beyond pool size"
    )
    db_echo: bool = Field(False, description="Echo SQL statements for debugging")

    # JWT Authentication settings
    jwt_secret_key: str = Field(
        ...,
        description="Secret key for signing JWT tokens",
        min_length=32,
    )

    @field_validator("jwt_secret_key")
    @classmethod
    def reject_known_defaults(cls, value: str) -> str:
        """Refuse publicly known default secrets at startup."""
        assert isinstance(value, str)
        if value in KNOWN_DEFAULT_SECRETS:
            raise ValueError(
                "known-default JWT secret rejected; generate one: openssl rand -hex 32"
            )
        return value

    jwt_algorithm: str = Field(
        "HS256",
        description="Algorithm used for JWT signing",
        pattern=r"^(HS256|HS384|HS512|RS256|RS384|RS512)$",
    )
    access_token_expire_minutes: int = Field(
        15,
        ge=1,
        le=1440,
        description="Access token expiration time in minutes",
    )
    refresh_token_expire_days: int = Field(
        7,
        ge=1,
        le=90,
        description="Refresh token expiration time in days",
    )

    # CORS settings
    cors_allowed_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000"],
        description="Allowed origins for CORS requests (comma-separated in env)",
    )
    cors_allow_credentials: bool = Field(
        True,
        description="Allow credentials (cookies, authorization headers) in CORS requests",
    )
    cors_allowed_methods: list[str] = Field(
        default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        description="Allowed HTTP methods for CORS requests",
    )
    cors_allowed_headers: list[str] = Field(
        default_factory=lambda: ["*"],
        description="Allowed headers for CORS requests",
    )

    # Email (T-1000): empty smtp_host selects log mode
    smtp_host: str | None = Field(
        None,
        description="SMTP hostname; when unset emails are logged instead of sent",
    )
    smtp_port: int = Field(
        587,
        ge=1,
        le=65535,
        description="SMTP port",
    )
    smtp_user: str | None = Field(None, description="SMTP username")
    smtp_password: str | None = Field(None, description="SMTP password")
    smtp_from: str = Field(
        "no-reply@hector.local",
        description="From address for outgoing emails",
    )
    smtp_start_tls: bool = Field(True, description="Use STARTTLS when connecting")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load settings and cache the result for reuse."""

    try:
        return Settings()  # type: ignore[call-arg]
    except ValidationError as exc:  # pragma: no cover - defensive
        errors = ", ".join(f"{e['loc'][0]}: {e['msg']}" for e in exc.errors())
        raise RuntimeError(f"Invalid configuration: {errors}") from exc


def reset_settings_cache() -> None:
    """Clear the settings cache (useful for tests)."""

    get_settings.cache_clear()


def settings_asdict(settings: Settings) -> dict[str, Any]:
    """Return settings as a plain dict with secrets masked, safe for logging."""

    data: dict[str, Any] = settings.model_dump()
    data["jwt_secret_key"] = "***"

    database_url = data.get("database_url")
    assert isinstance(database_url, str)
    if "@" in database_url and "://" in database_url:
        scheme_and_rest = database_url.split("://", 1)
        if "@" in scheme_and_rest[1]:
            host_part = scheme_and_rest[1].split("@", 1)[1]
            credentials = scheme_and_rest[1].split("@", 1)[0]
            if ":" in credentials:
                user = credentials.split(":", 1)[0]
                data["database_url"] = (
                    f"{scheme_and_rest[0]}://{user}{_SENSITIVE_URL_MARKER}{host_part}"
                )

    return data

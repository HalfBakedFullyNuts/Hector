"""Smoke tests for the health endpoint."""

import pytest
from httpx import AsyncClient

from hector.app import create_app
from hector.config import Settings, reset_settings_cache


@pytest.fixture()
def test_settings() -> Settings:
    reset_settings_cache()
    return Settings(environment="test", log_level="INFO", port=8100)


@pytest.mark.asyncio()
async def test_health_endpoint_returns_ok(test_settings: Settings) -> None:
    app = create_app(test_settings)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["environment"] == "test"
    assert "version" in payload and isinstance(payload["version"], str)
    assert "request_id" in payload
    assert response.headers["X-Request-ID"] == payload["request_id"]

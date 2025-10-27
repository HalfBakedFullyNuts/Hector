"""Health and status endpoints."""

from typing import Any

from fastapi import APIRouter, Depends

from .. import get_version
from ..config import Settings, get_settings, settings_asdict
from ..middleware import get_request_id


router = APIRouter(prefix="/health", tags=["health"])


def _status_payload(settings: Settings) -> dict[str, Any]:
    return {
        "status": "ok",
        "version": get_version(),
        "environment": settings.environment,
    }


@router.get("", summary="Healthcheck", response_model=dict[str, Any])
async def healthcheck(settings: Settings = Depends(get_settings)) -> dict[str, Any]:
    """Return service health metadata."""

    payload = _status_payload(settings)
    request_id = get_request_id()
    if request_id:
        payload["request_id"] = request_id
    return payload

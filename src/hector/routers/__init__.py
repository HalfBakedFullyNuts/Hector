"""Router registration."""

from fastapi import APIRouter

from . import health, requests


def get_router() -> APIRouter:
    """Aggregate sub-routers into a single router."""

    router = APIRouter()
    router.include_router(health.router)
    router.include_router(requests.router)
    return router


__all__ = ["get_router"]

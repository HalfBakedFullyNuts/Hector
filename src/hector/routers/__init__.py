"""Router registration."""

from fastapi import APIRouter

from . import health


def get_router() -> APIRouter:
    """Aggregate sub-routers into a single router."""

    router = APIRouter()
    router.include_router(health.router)
    return router


__all__ = ["get_router"]

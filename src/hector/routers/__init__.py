"""Router registration."""

from fastapi import APIRouter

from . import auth, dogs, health


def get_router() -> APIRouter:
    """Aggregate sub-routers into a single router."""

    router = APIRouter()
    router.include_router(health.router)
    router.include_router(auth.router)
    router.include_router(dogs.router)
    return router


__all__ = ["get_router"]

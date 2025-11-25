"""Router registration."""

from fastapi import APIRouter

from . import clinics, dogs, health, requests, responses


def get_router() -> APIRouter:
    """Aggregate sub-routers into a single router."""

    router = APIRouter()
    router.include_router(health.router)
    router.include_router(dogs.router)
    router.include_router(clinics.router)
    router.include_router(requests.router)
    router.include_router(responses.router)
    return router


__all__ = ["get_router"]

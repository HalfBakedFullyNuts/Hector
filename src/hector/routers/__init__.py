"""Router registration."""

from fastapi import APIRouter

from . import admin, auth, clinics, dogs, donation_requests, health


def get_router() -> APIRouter:
    """Aggregate sub-routers into a single router."""

    router = APIRouter()
    router.include_router(health.router)
    router.include_router(auth.router)
    router.include_router(dogs.router)
    router.include_router(clinics.router)
    router.include_router(donation_requests.router)
    router.include_router(admin.router)
    return router


__all__ = ["get_router"]

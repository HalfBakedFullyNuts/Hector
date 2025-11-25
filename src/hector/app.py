"""Application factory for the Hector FastAPI service."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import get_version
from .config import Settings, get_settings, settings_asdict
from .logging_config import setup_logging
from .middleware import middleware_stack
from .routers import get_router

LOG = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""

    settings = settings or get_settings()
    setup_logging(settings.log_level)

    app = FastAPI(
        title="Hector Blood Donation Platform",
        description="API for connecting vet clinics with dog blood donors",
        version=get_version(),
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allowed_methods,
        allow_headers=settings.cors_allowed_headers,
    )

    for middleware, kwargs in middleware_stack():
        app.add_middleware(middleware, **kwargs)

    app.include_router(get_router())

    @app.on_event("startup")
    async def _log_startup() -> None:  # pragma: no cover - simple logging hook
        LOG.info("Service starting", extra={"settings": settings_asdict(settings)})

    return app

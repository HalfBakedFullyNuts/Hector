"""Application factory for the Hector FastAPI service."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore[import-untyped]
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import get_version
from .config import Settings, get_settings, settings_asdict
from .logging_config import setup_logging
from .middleware import middleware_stack
from .routers import get_router

LOG = logging.getLogger(__name__)


def _seconds_until_next_run() -> int:
    """Seconds until the next 00:05 UTC daily sweep."""
    now = datetime.now(UTC)
    target = now.replace(hour=0, minute=5, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return max(1, int((target - now).total_seconds()))


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Run the startup sweep and schedule daily expiry jobs (T-1005)."""
    settings: Settings = app.state.settings
    scheduler: AsyncIOScheduler | None = None

    if settings.environment != "test":
        from hector.database import get_session_factory
        from hector.jobs.expire_requests import expire_overdue_requests

        async def _sweep() -> None:
            factory = get_session_factory()
            async with factory() as session:
                await expire_overdue_requests(session)

        try:
            await _sweep()
        except Exception as exc:  # noqa: BLE001 - startup must not crash on sweeps
            LOG.error("startup expiry sweep failed: %s", exc)

        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            _sweep,
            "interval",
            seconds=_seconds_until_next_run(),
            id="expire_requests",
            replace_existing=True,
        )
        scheduler.start()

    yield

    if scheduler is not None:
        scheduler.shutdown(wait=False)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""

    settings = settings or get_settings()
    setup_logging(settings.log_level)

    app = FastAPI(
        title="Hector Blood Donation Platform",
        description="API for connecting vet clinics with dog blood donors",
        version=get_version(),
        lifespan=_lifespan,
    )
    app.state.settings = settings

    # Serve uploaded dog photos (T-1001)
    media_path = Path(settings.media_dir)
    media_path.mkdir(parents=True, exist_ok=True)
    app.mount("/media", StaticFiles(directory=str(media_path)), name="media")

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

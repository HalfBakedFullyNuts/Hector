"""Command-line entry point for running the ASGI server."""

import uvicorn

from .config import get_settings


def run_server() -> None:
    """Start the uvicorn server with current settings."""
    settings = get_settings()
    uvicorn.run(
        "hector.app:create_app",
        factory=True,
        host="0.0.0.0",
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower(),
    )


def main() -> None:
    """Backwards-compatible entry point."""
    run_server()


if __name__ == "__main__":
    main()

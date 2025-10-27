"""Hector FastAPI service package."""

from importlib.metadata import PackageNotFoundError, version


def get_version() -> str:
    """Return the installed package version or a development placeholder."""
    try:
        return version("hector")
    except PackageNotFoundError:
        return "0.1.0-dev"


__all__ = ["get_version"]

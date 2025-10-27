"""Logging configuration helpers."""

import logging
from typing import Final


LOG_FORMAT: Final[str] = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def setup_logging(level: str) -> None:
    """Configure root logging handlers and level."""

    logging.basicConfig(level=level, format=LOG_FORMAT)

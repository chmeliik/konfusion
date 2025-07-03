from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

LOG_FORMAT = "%(asctime)s %(levelname)s %(message)s"


def setup_logging(level: int, modules: Iterable[str]) -> None:
    """Set up logging for the specified modules."""
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(LOG_FORMAT))

    for module in modules:
        logger = logging.getLogger(module)
        logger.setLevel(level)

        if not logger.hasHandlers():
            logger.addHandler(handler)

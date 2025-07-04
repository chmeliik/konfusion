from __future__ import annotations

import datetime
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

LOG_FORMAT = "%(asctime)s [%(levelname)-8s] %(message)s"


class _ISOTimeFormatter(logging.Formatter):
    def formatTime(  # noqa: N802 # blame the stdlib logging module for camelCase
        self,
        record: logging.LogRecord,
        datefmt: str | None = None,
    ) -> str:
        dt = datetime.datetime.fromtimestamp(record.created).astimezone()
        if not datefmt:
            return dt.isoformat(sep=" ", timespec="seconds")
        else:
            return dt.strftime(datefmt)


def setup_logging(level: int, modules: Iterable[str]) -> None:
    """Set up logging for the specified modules."""
    handler = logging.StreamHandler()
    handler.setFormatter(_ISOTimeFormatter(LOG_FORMAT))

    for module in modules:
        logger = logging.getLogger(module)
        logger.setLevel(level)

        if not logger.hasHandlers():
            logger.addHandler(handler)

from __future__ import annotations

import datetime
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable


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


def setup_logging(level: int, additional_modules: Iterable[str] = ()) -> None:
    """Set up logging for default modules and the specified additional modules."""

    for module in ["konfusion", "stamina", *additional_modules]:
        if module == "stamina":
            log_format = (
                "%(asctime)s [%(levelname)-8s] "
                "%(stamina.callable)s raised %(stamina.caused_by)s, "
                "retrying in %(stamina.wait_for)f seconds (retry %(stamina.retry_num)d)"
            )
        else:
            log_format = "%(asctime)s [%(levelname)-8s] %(message)s"

        handler = logging.StreamHandler()
        handler.setFormatter(_ISOTimeFormatter(log_format))

        logger = logging.getLogger(module)
        logger.setLevel(level)

        if not logger.hasHandlers():
            logger.addHandler(handler)

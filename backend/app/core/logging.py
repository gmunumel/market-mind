import logging
from logging import Logger
from typing import Optional

from app.core.config import get_settings

_CONFIGURED = False


def configure_logging(level: Optional[str] = None) -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    log_level = level or get_settings().log_level
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    _CONFIGURED = True


def get_logger(name: Optional[str] = None) -> Logger:
    configure_logging()
    return logging.getLogger(name or "app")

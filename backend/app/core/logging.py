import logging
from logging import Logger

from app.core.config import get_settings

logger: Logger = logging.getLogger("app")


if not logger.handlers:
    settings = get_settings()
    log_level = settings.log_level

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    logger.setLevel(log_level)

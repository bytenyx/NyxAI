import logging
import sys
from typing import Optional

from app.config import get_settings

settings = get_settings()


def setup_logging(level: Optional[str] = None) -> None:
    log_level = level or ("DEBUG" if settings.DEBUG else "INFO")
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    logger = logging.getLogger(name)
    if level:
        logger.setLevel(getattr(logging, level.upper()))
    return logger

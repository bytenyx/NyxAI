import pytest
import logging
from app.utils.logger import get_logger, setup_logging


def test_get_logger_returns_logger():
    logger = get_logger("test")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test"


def test_setup_logging_configures_root_logger():
    setup_logging(level="DEBUG")
    root_logger = logging.getLogger()
    assert root_logger.level == logging.DEBUG

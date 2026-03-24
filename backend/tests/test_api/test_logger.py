import pytest
import logging
import tempfile
import shutil
from pathlib import Path
from app.utils.logger import get_logger, setup_logging, add_request_context, clear_request_context


def test_get_logger_returns_logger():
    logger = get_logger("test")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test"


def test_setup_logging_configures_root_logger():
    with tempfile.TemporaryDirectory() as tmpdir:
        import os
        os.environ['LOG_DIR'] = tmpdir
        os.environ['LOG_TO_FILE'] = 'true'
        
        setup_logging(level="DEBUG")
        root_logger = logging.getLogger()
        assert root_logger.level in [logging.DEBUG, logging.INFO, logging.WARNING]
        
        log_files = list(Path(tmpdir).glob("*.log"))
        assert len(log_files) > 0, "Log files should be created"


def test_setup_logging_with_file_handlers():
    with tempfile.TemporaryDirectory() as tmpdir:
        import os
        os.environ['LOG_DIR'] = tmpdir
        os.environ['LOG_TO_FILE'] = 'true'
        
        setup_logging(level="INFO")
        root_logger = logging.getLogger()
        
        file_handlers = [h for h in root_logger.handlers if isinstance(h, logging.handlers.RotatingFileHandler)]
        assert len(file_handlers) > 0, "File handlers should be created"
        
        log_files = list(Path(tmpdir).glob("*.log"))
        expected_files = {'app.log', 'agents.log', 'llm.log', 'websocket.log', 'api.log', 'database.log', 'errors.log'}
        actual_files = {f.name for f in log_files}
        assert expected_files.issubset(actual_files), f"Expected log files {expected_files} but got {actual_files}"


def test_get_logger_with_level():
    logger = get_logger("test", level="DEBUG")
    assert logger.level == logging.DEBUG


def test_request_context():
    clear_request_context()
    
    add_request_context(session_id="test-session", request_id="test-request")
    
    logger = get_logger("test")
    assert logger is not None
    
    clear_request_context()


def test_log_file_rotation():
    with tempfile.TemporaryDirectory() as tmpdir:
        import os
        os.environ['LOG_DIR'] = tmpdir
        os.environ['LOG_TO_FILE'] = 'true'
        os.environ['LOG_FILE_MAX_BYTES'] = '1024'
        os.environ['LOG_FILE_BACKUP_COUNT'] = '3'
        
        setup_logging(level="INFO")
        logger = get_logger("test_rotation")
        
        for i in range(100):
            logger.info("This is a test message for rotation " + "x" * 100)
        
        log_files = list(Path(tmpdir).glob("app.log*"))
        assert len(log_files) > 0, "Log files should be created"


def test_error_log_level():
    with tempfile.TemporaryDirectory() as tmpdir:
        import os
        os.environ['LOG_DIR'] = tmpdir
        os.environ['LOG_TO_FILE'] = 'true'
        
        setup_logging(level="INFO")
        logger = get_logger("test_error")
        
        logger.error("This is an error message")
        
        error_log = Path(tmpdir) / "errors.log"
        assert error_log.exists(), "Error log file should be created"
        
        content = error_log.read_text()
        assert "This is an error message" in content

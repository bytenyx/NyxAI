"""Utility functions for NyxAI.

This module provides common utilities including logging configuration,
time handling, and helper functions used throughout the application.
"""

import logging
import logging.handlers
import sys
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Generator

import structlog
from structlog.types import EventDict, WrappedLogger

from nyxai.config import LoggingSettings, settings


def _add_timestamp(
    logger: WrappedLogger,  # noqa: ARG001
    method_name: str,  # noqa: ARG001
    event_dict: EventDict,
) -> EventDict:
    """Add ISO format timestamp to log events."""
    event_dict["timestamp"] = datetime.now(UTC).isoformat()
    return event_dict


def _add_log_level(
    logger: WrappedLogger,  # noqa: ARG001
    method_name: str,
    event_dict: EventDict,
) -> EventDict:
    """Add log level to event dict."""
    event_dict["level"] = method_name.upper()
    return event_dict


def _add_caller_info(
    logger: WrappedLogger,  # noqa: ARG001
    method_name: str,  # noqa: ARG001
    event_dict: EventDict,
) -> EventDict:
    """Add caller information to log events."""
    frame = sys._getframe(3)  # noqa: SLF001
    event_dict["module"] = Path(frame.f_code.co_filename).stem
    event_dict["function"] = frame.f_code.co_name
    event_dict["line"] = frame.f_lineno
    return event_dict


def configure_logging(log_settings: LoggingSettings | None = None) -> None:
    """Configure structured logging for the application.

    Args:
        log_settings: Logging configuration. Uses global settings if not provided.

    Example:
        >>> from nyxai.utils import configure_logging
        >>> from nyxai.config import LoggingSettings
        >>> configure_logging(LoggingSettings(level="DEBUG", format="json"))
    """
    log_settings = log_settings or settings.logging

    # Configure standard library logging
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]

    if log_settings.file_path:
        log_settings.file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_settings.file_path,
            maxBytes=log_settings.max_bytes,
            backupCount=log_settings.backup_count,
            encoding="utf-8",
        )
        handlers.append(file_handler)

    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, log_settings.level),
        handlers=handlers,
        force=True,
    )

    # Configure structlog processors
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.stdlib.ExtraAdder(),
    ]

    if log_settings.format == "json":
        format_processor: Any = structlog.processors.JSONRenderer()
    else:
        format_processor = structlog.dev.ConsoleRenderer(colors=sys.stdout.isatty())

    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            format_processor,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance.

    Args:
        name: Logger name. If None, uses the calling module name.

    Returns:
        BoundLogger: Configured structlog logger.

    Example:
        >>> from nyxai.utils import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Application started", version="0.1.0")
    """
    return structlog.get_logger(name)


# Time utilities

def utc_now() -> datetime:
    """Get current UTC datetime.

    Returns:
        datetime: Current time in UTC.
    """
    return datetime.now(UTC)


def format_datetime(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime to string.

    Args:
        dt: Datetime to format.
        fmt: Format string. Defaults to ISO-like format.

    Returns:
        str: Formatted datetime string.
    """
    return dt.strftime(fmt)


def parse_datetime(dt_str: str, fmt: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """Parse datetime string to datetime object.

    Args:
        dt_str: Datetime string to parse.
        fmt: Format string. Defaults to ISO-like format.

    Returns:
        datetime: Parsed datetime in UTC.
    """
    return datetime.strptime(dt_str, fmt).replace(tzinfo=UTC)


def time_ago(dt: datetime) -> str:
    """Convert datetime to human-readable 'time ago' string.

    Args:
        dt: Datetime to convert.

    Returns:
        str: Human-readable time difference (e.g., "2 hours ago").
    """
    now = utc_now()
    diff = now - dt

    if diff < timedelta(minutes=1):
        return "just now"
    if diff < timedelta(hours=1):
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    if diff < timedelta(days=1):
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    if diff < timedelta(days=30):
        days = diff.days
        return f"{days} day{'s' if days != 1 else ''} ago"
    if diff < timedelta(days=365):
        months = diff.days // 30
        return f"{months} month{'s' if months != 1 else ''} ago"

    years = diff.days // 365
    return f"{years} year{'s' if years != 1 else ''} ago"


def truncate_datetime(
    dt: datetime,
    granularity: Literal["second", "minute", "hour", "day"] = "minute",
) -> datetime:
    """Truncate datetime to specified granularity.

    Args:
        dt: Datetime to truncate.
        granularity: Truncation level.

    Returns:
        datetime: Truncated datetime.
    """
    if granularity == "second":
        return dt.replace(microsecond=0)
    if granularity == "minute":
        return dt.replace(second=0, microsecond=0)
    if granularity == "hour":
        return dt.replace(minute=0, second=0, microsecond=0)
    if granularity == "day":
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)

    raise ValueError(f"Invalid granularity: {granularity}")


# Context managers

@contextmanager
def timed_execution(
    logger: structlog.stdlib.BoundLogger | None = None,
    operation: str = "operation",
) -> Generator[None, None, None]:
    """Context manager to time execution of a code block.

    Args:
        logger: Logger to use. If None, no logging is performed.
        operation: Name of the operation being timed.

    Yields:
        None

    Example:
        >>> from nyxai.utils import timed_execution, get_logger
        >>> logger = get_logger(__name__)
        >>> with timed_execution(logger, "data_processing"):
        ...     process_large_dataset()
    """
    start = utc_now()
    try:
        yield
    finally:
        elapsed = (utc_now() - start).total_seconds()
        if logger:
            logger.debug(f"{operation}_completed", elapsed_seconds=elapsed)


# Type conversion utilities

def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert value to integer.

    Args:
        value: Value to convert.
        default: Default value if conversion fails.

    Returns:
        int: Converted integer or default.
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float.

    Args:
        value: Value to convert.
        default: Default value if conversion fails.

    Returns:
        float: Converted float or default.
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_bool(value: Any, default: bool = False) -> bool:
    """Safely convert value to boolean.

    Args:
        value: Value to convert.
        default: Default value if conversion fails.

    Returns:
        bool: Converted boolean or default.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    try:
        return bool(value)
    except (ValueError, TypeError):
        return default


# File utilities

def ensure_dir(path: Path) -> Path:
    """Ensure directory exists, create if not.

    Args:
        path: Directory path.

    Returns:
        Path: The directory path.
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_file(path: Path, encoding: str = "utf-8") -> str:
    """Read file contents safely.

    Args:
        path: File path.
        encoding: File encoding.

    Returns:
        str: File contents.

    Raises:
        FileNotFoundError: If file does not exist.
    """
    return path.read_text(encoding=encoding)


def write_file(path: Path, content: str, encoding: str = "utf-8") -> None:
    """Write content to file safely.

    Args:
        path: File path.
        content: Content to write.
        encoding: File encoding.
    """
    ensure_dir(path.parent)
    path.write_text(content, encoding=encoding)


# String utilities

def slugify(text: str) -> str:
    """Convert text to URL-friendly slug.

    Args:
        text: Text to convert.

    Returns:
        str: URL-friendly slug.
    """
    import re

    # Convert to lowercase and replace spaces with hyphens
    slug = text.lower().strip().replace(" ", "-")
    # Remove non-alphanumeric characters except hyphens
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    # Remove multiple consecutive hyphens
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to maximum length.

    Args:
        text: Text to truncate.
        max_length: Maximum length.
        suffix: Suffix to add if truncated.

    Returns:
        str: Truncated text.
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


# Import Literal for type hints
try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

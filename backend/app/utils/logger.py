import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
from contextvars import ContextVar

from app.config import get_settings

settings = get_settings()

_request_context: ContextVar[dict] = ContextVar('request_context', default={})


def setup_logging(level: Optional[str] = None) -> None:
    log_level = level or ("DEBUG" if settings.DEBUG else settings.LOG_LEVEL)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    root_logger.handlers.clear()
    
    if settings.LOG_TO_CONSOLE:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(logging.Formatter(
            fmt=settings.LOG_FORMAT,
            datefmt=settings.LOG_DATE_FORMAT
        ))
        root_logger.addHandler(console_handler)
    
    if settings.LOG_TO_FILE:
        log_dir = Path(settings.LOG_DIR)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_files = {
            'app': log_dir / 'app.log',
            'agents': log_dir / 'agents.log',
            'llm': log_dir / 'llm.log',
            'websocket': log_dir / 'websocket.log',
            'api': log_dir / 'api.log',
            'database': log_dir / 'database.log',
            'errors': log_dir / 'errors.log',
        }
        
        for name, log_file in log_files.items():
            handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=settings.LOG_FILE_MAX_BYTES,
                backupCount=settings.LOG_FILE_BACKUP_COUNT,
                encoding='utf-8'
            )
            
            if name == 'errors':
                handler.setLevel(logging.ERROR)
            else:
                handler.setLevel(getattr(logging, log_level.upper()))
            
            handler.setFormatter(logging.Formatter(
                fmt=settings.LOG_FORMAT,
                datefmt=settings.LOG_DATE_FORMAT
            ))
            root_logger.addHandler(handler)


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    logger = logging.getLogger(name)
    if level:
        logger.setLevel(getattr(logging, level.upper()))
    return logger


def get_request_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    logger = get_logger(name, level)
    
    class RequestContextAdapter(logging.LoggerAdapter):
        def process(self, msg, kwargs):
            context = _request_context.get()
            if context:
                parts = []
                if 'request_id' in context:
                    parts.append(f"request_id={context['request_id']}")
                if 'session_id' in context:
                    parts.append(f"session_id={context['session_id']}")
                if 'user_id' in context:
                    parts.append(f"user_id={context['user_id']}")
                if parts:
                    msg = f"[{' '.join(parts)}] {msg}"
            return msg, kwargs
    
    return RequestContextAdapter(logger, {})


def add_request_context(**kwargs) -> None:
    current_context = _request_context.get()
    current_context.update(kwargs)
    _request_context.set(current_context)


def clear_request_context() -> None:
    _request_context.set({})

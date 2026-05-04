import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

import structlog

from devflow.utils.config import settings


class TeeLogger:
    """A logger that writes to both console and file."""
    
    def __init__(self, console_file: Any, log_file: Any, log_level: int):
        self.console_file = console_file
        self.log_file = log_file
        self.log_level = log_level
    
    def debug(self, msg: str) -> None:
        self._write("DEBUG", msg)
    
    def info(self, msg: str) -> None:
        self._write("INFO", msg)
    
    def warning(self, msg: str) -> None:
        self._write("WARNING", msg)
    
    def error(self, msg: str) -> None:
        self._write("ERROR", msg)
    
    def exception(self, msg: str) -> None:
        self._write("ERROR", msg)
    
    def _write(self, level: str, msg: str) -> None:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted = f"{timestamp} [{level}] devflow: {msg}\n"
        
        # Write to console
        self.console_file.write(formatted)
        self.console_file.flush()
        
        # Write to file
        self.log_file.write(formatted)
        self.log_file.flush()


def setup_logging() -> None:
    """Configure structured logging for the application."""

    log_level = getattr(logging, settings.log_level.upper())

    # Ensure logs directory exists
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "devflow.log"

    # Create rotating file handler
    rotating_handler = RotatingFileHandler(
        log_file,
        maxBytes=settings.log_max_bytes,
        backupCount=settings.log_backup_count,
        encoding="utf-8"
    )
    rotating_handler.setLevel(log_level)

    # Get the underlying stream for file writing
    file_stream = rotating_handler.stream

    # Create tee logger factory
    console_out = sys.stdout

    def tee_logger_factory(logger_name: str = "") -> TeeLogger:
        return TeeLogger(console_out, file_stream, log_level)

    # Configure structlog with tee logger factory
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.dev.ConsoleRenderer() if settings.debug else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=tee_logger_factory,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


# Pre-configured logger
logger = get_logger("devflow")

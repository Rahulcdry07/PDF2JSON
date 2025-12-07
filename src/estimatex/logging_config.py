"""Structured logging configuration for EstimateX."""

import logging
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import traceback


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def __init__(self, service_name: str = "estimatex", include_trace: bool = True):
        super().__init__()
        self.service_name = service_name
        self.include_trace = include_trace

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "service": self.service_name,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields if present
        if hasattr(record, "extra"):
            log_data.update(record.extra)

        # Add exception info if present
        if record.exc_info and self.include_trace:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info),
            }

        # Add request context if available
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms

        return json.dumps(log_data, default=str)


class HumanReadableFormatter(logging.Formatter):
    """Human-readable formatter for console output."""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def __init__(self, use_colors: bool = True):
        super().__init__()
        self.use_colors = use_colors and sys.stdout.isatty()

    def format(self, record: logging.LogRecord) -> str:
        """Format log record for human reading."""
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")

        # Color the level if enabled
        level = record.levelname
        if self.use_colors and level in self.COLORS:
            level = f"{self.COLORS[level]}{level}{self.RESET}"

        # Build message
        parts = [
            timestamp,
            level,
            f"{record.name}:{record.funcName}:{record.lineno}",
            record.getMessage(),
        ]

        message = " | ".join(parts)

        # Add exception info if present
        if record.exc_info:
            message += "\n" + self.formatException(record.exc_info)

        return message


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "json",
    log_file: Optional[Path] = None,
    service_name: str = "estimatex",
) -> None:
    """
    Setup structured logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Format type ('json' or 'human')
        log_file: Optional file path for logging to file
        service_name: Name of the service for log identification

    Example:
        >>> setup_logging(log_level="INFO", log_format="json")
        >>> logger = logging.getLogger(__name__)
        >>> logger.info("Application started", extra={"version": "1.0.0"})
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))

    if log_format.lower() == "json":
        console_handler.setFormatter(StructuredFormatter(service_name=service_name))
    else:
        console_handler.setFormatter(HumanReadableFormatter(use_colors=True))

    root_logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(StructuredFormatter(service_name=service_name))

        root_logger.addHandler(file_handler)

    # Set levels for noisy libraries
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)


class LoggerAdapter(logging.LoggerAdapter):
    """Logger adapter that adds contextual information to logs."""

    def process(self, msg, kwargs):
        """Add extra context to log records."""
        if "extra" not in kwargs:
            kwargs["extra"] = {}
        kwargs["extra"].update(self.extra)
        return msg, kwargs


def get_logger(name: str, **context) -> logging.Logger:
    """
    Get a logger with optional context.

    Args:
        name: Logger name (usually __name__)
        **context: Additional context to include in all logs

    Returns:
        Logger instance

    Example:
        >>> logger = get_logger(__name__, component="pdf_converter")
        >>> logger.info("Processing PDF", extra={"file": "doc.pdf", "pages": 10})
    """
    base_logger = logging.getLogger(name)

    if context:
        return LoggerAdapter(base_logger, context)

    return base_logger


# Convenience functions for common log patterns
def log_function_call(logger: logging.Logger, func_name: str, **params):
    """Log function entry with parameters."""
    logger.debug(f"Calling {func_name}", extra={"function": func_name, "parameters": params})


def log_performance(logger: logging.Logger, operation: str, duration_ms: float, **metrics):
    """Log performance metrics."""
    logger.info(
        f"{operation} completed",
        extra={"operation": operation, "duration_ms": round(duration_ms, 2), **metrics},
    )


def log_error(logger: logging.Logger, error: Exception, context: Optional[Dict] = None):
    """Log error with context."""
    extra = {"error_type": type(error).__name__}
    if context:
        extra.update(context)

    logger.error(f"Error occurred: {str(error)}", exc_info=True, extra=extra)


# Example usage
if __name__ == "__main__":
    # Setup logging
    setup_logging(log_level="DEBUG", log_format="json")

    # Get logger
    logger = get_logger(__name__, component="example")

    # Log various events
    logger.info("Application started", extra={"version": "1.0.0"})

    log_function_call(logger, "process_pdf", file="document.pdf", pages=10)

    import time

    start = time.time()
    time.sleep(0.1)
    duration = (time.time() - start) * 1000
    log_performance(logger, "PDF conversion", duration, pages_converted=10)

    # Log error
    try:
        raise ValueError("Example error")
    except Exception as e:
        log_error(logger, e, context={"file": "test.pdf"})

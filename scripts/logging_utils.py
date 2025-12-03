#!/usr/bin/env python3
"""
Logging utilities for scripts.

Provides consistent logging setup across all scripts with file and console output.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_script_logging(
    script_name: str,
    log_level: str = 'INFO',
    log_dir: Path = None
) -> logging.Logger:
    """
    Setup logging for scripts with both file and console output.
    
    Args:
        script_name: Name of the script (used for logger name and log filename)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (default: PROJECT_ROOT/data/logs/)
    
    Returns:
        Configured logger instance
    
    Example:
        >>> logger = setup_script_logging('excel_to_pdf')
        >>> logger.info("Starting conversion")
        >>> logger.error("Conversion failed", exc_info=True)
    """
    # Get or create logger
    logger = logging.getLogger(script_name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # Console handler (only warnings and errors to not clutter CLI output)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.WARNING)  # Only show warnings/errors in console
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # File handler (all levels)
    if log_dir is None:
        # Default to PROJECT_ROOT/data/logs/
        project_root = Path(__file__).parents[1]
        log_dir = project_root / 'data' / 'logs'
    
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create log file with date
    log_file = log_dir / f"{script_name}_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)  # Log everything to file
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    # Log startup message
    logger.debug(f"Logging initialized for {script_name}")
    logger.debug(f"Log file: {log_file}")
    logger.debug(f"Log level: {log_level}")
    
    return logger


def log_operation(logger: logging.Logger, operation: str, **kwargs):
    """
    Log an operation with structured data.
    
    Args:
        logger: Logger instance
        operation: Operation name
        **kwargs: Additional context data
    
    Example:
        >>> log_operation(logger, 'conversion', 
        ...              input_file='test.xlsx', 
        ...              sheets=3, 
        ...              duration_ms=1500)
    """
    context = ' | '.join(f"{k}={v}" for k, v in kwargs.items())
    logger.info(f"{operation} | {context}")


def log_progress(logger: logging.Logger, current: int, total: int, item: str = "items"):
    """
    Log progress information.
    
    Args:
        logger: Logger instance
        current: Current item number
        total: Total items
        item: Item description (e.g., "files", "sheets", "rows")
    
    Example:
        >>> log_progress(logger, 5, 10, "sheets")
    """
    percentage = (current / total * 100) if total > 0 else 0
    logger.debug(f"Progress: {current}/{total} {item} ({percentage:.1f}%)")


def log_error_with_context(logger: logging.Logger, error: Exception, context: dict = None):
    """
    Log an error with additional context.
    
    Args:
        logger: Logger instance
        error: Exception that occurred
        context: Additional context information
    
    Example:
        >>> try:
        ...     risky_operation()
        ... except Exception as e:
        ...     log_error_with_context(logger, e, {'file': 'test.xlsx'})
    """
    context_str = ' | '.join(f"{k}={v}" for k, v in (context or {}).items())
    logger.error(f"Error occurred | {context_str} | {type(error).__name__}: {error}", exc_info=True)

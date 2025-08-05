# 389ds-log-analyser - A parser and query tool for 389 Directory Server access logs
# Copyright (C) 2024 Thomas Weiss <weiss@puzzle-itc.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Centralized logging configuration for the 389ds log analyser.

This module provides consistent logging setup across all components of the tool,
with support for different log levels, formatters, and output destinations.
"""

import logging
import logging.handlers
import sys
import os
from typing import Optional, Dict, Any
from pathlib import Path


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output."""
    
    # Color codes for different log levels
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        # Add color to the log level
        if record.levelname in self.COLORS and sys.stderr.isatty():
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
        
        return super().format(record)


def setup_logging(
    debug: bool = False,
    log_file: Optional[str] = None,
    quiet: bool = False,
    verbose: bool = False
) -> None:
    """
    Set up logging configuration for the application.
    
    Args:
        debug: Enable debug logging (most verbose)
        log_file: Optional file path to write logs to
        quiet: Suppress all but error messages
        verbose: Enable verbose output (INFO level)
    """
    # Determine log level based on flags
    if debug:
        console_level = logging.DEBUG
        file_level = logging.DEBUG
    elif quiet:
        console_level = logging.ERROR
        file_level = logging.WARNING
    elif verbose:
        console_level = logging.INFO
        file_level = logging.INFO
    else:
        console_level = logging.WARNING
        file_level = logging.INFO
    
    # Remove any existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Set root logger level to DEBUG to allow all messages through
    root_logger.setLevel(logging.DEBUG)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(console_level)
    
    # Use colored formatter for console if terminal supports it
    if sys.stderr.isatty():
        console_formatter = ColoredFormatter(
            '%(levelname)s: %(message)s'
        )
    else:
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
    
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        try:
            # Ensure log directory exists
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5
            )
            file_handler.setLevel(file_level)
            
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
            
            if debug:
                logging.info(f"Logging to file: {log_file}")
                
        except Exception as e:
            logging.error(f"Failed to set up file logging to {log_file}: {e}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Name of the logger (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_exception(logger: logging.Logger, message: str, exc_info: bool = True) -> None:
    """
    Log an exception with full traceback information.
    
    Args:
        logger: Logger instance to use
        message: Custom message to include
        exc_info: Whether to include exception info
    """
    logger.error(message, exc_info=exc_info)


def log_performance(logger: logging.Logger, operation: str, duration: float, **kwargs: Any) -> None:
    """
    Log performance information for operations.
    
    Args:
        logger: Logger instance to use
        operation: Name of the operation
        duration: Duration in seconds
        **kwargs: Additional context information
    """
    context = " ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.info(f"Performance: {operation} took {duration:.3f}s {context}".strip())


def configure_third_party_loggers() -> None:
    """Configure logging levels for third-party libraries."""
    # Reduce noise from third-party libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('socket').setLevel(logging.WARNING)


class LogContext:
    """Context manager for temporary logging configuration."""
    
    def __init__(self, level: int, logger: Optional[logging.Logger] = None):
        self.level = level
        self.logger = logger or logging.getLogger()
        self.original_level = None
    
    def __enter__(self) -> 'LogContext':
        self.original_level = self.logger.level
        self.logger.setLevel(self.level)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.original_level is not None:
            self.logger.setLevel(self.original_level)


def with_debug_logging(func):
    """Decorator to temporarily enable debug logging for a function."""
    def wrapper(*args, **kwargs):
        with LogContext(logging.DEBUG):
            return func(*args, **kwargs)
    return wrapper


# Default logging setup for when the module is imported
def _default_setup() -> None:
    """Set up default logging configuration."""
    # Only set up if no handlers are configured
    if not logging.getLogger().handlers:
        setup_logging()
        configure_third_party_loggers()


# Initialize default logging when module is imported
_default_setup() 
"""Structured logging for Injekt CLI."""

import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Dict, Any
import json


class StructuredFormatter(logging.Formatter):
    """Formatter that adds structured context to log records."""
    
    def __init__(self, include_context: bool = True):
        """Initialize the formatter.
        
        Args:
            include_context: Whether to include structured context in logs
        """
        super().__init__()
        self.include_context = include_context
    
    def format(self, record: logging.LogRecord) -> str:
        """Format a log record with structured context.
        
        Args:
            record: The log record to format
            
        Returns:
            Formatted log string
        """
        # Base format
        timestamp = datetime.fromtimestamp(record.created).isoformat()
        level = record.levelname
        message = record.getMessage()
        
        # Build the log line
        parts = [f"[{timestamp}]", f"[{level}]", f"[{record.name}]", message]
        
        # Add context if available and enabled
        if self.include_context and hasattr(record, 'context'):
            context_str = json.dumps(record.context)
            parts.append(f"context={context_str}")
        
        # Add exception info if present
        if record.exc_info:
            parts.append("\n" + self.formatException(record.exc_info))
        
        return " ".join(parts)


class ContextAdapter(logging.LoggerAdapter):
    """Logger adapter that adds structured context to log records."""
    
    def __init__(self, logger: logging.Logger, context: Optional[Dict[str, Any]] = None):
        """Initialize the adapter.
        
        Args:
            logger: The underlying logger
            context: Initial context dictionary
        """
        super().__init__(logger, context or {})
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Process the logging call to add context.
        
        Args:
            msg: The log message
            kwargs: Additional keyword arguments
            
        Returns:
            Tuple of (msg, kwargs) with context added
        """
        # Merge context from adapter and call-time extra
        extra = kwargs.get('extra', {})
        if self.extra:
            extra['context'] = {**self.extra, **extra.get('context', {})}
        else:
            extra['context'] = extra.get('context', {})
        
        kwargs['extra'] = extra
        return msg, kwargs
    
    def with_context(self, **context: Any) -> 'ContextAdapter':
        """Create a new adapter with additional context.
        
        Args:
            **context: Additional context key-value pairs
            
        Returns:
            New ContextAdapter with merged context
        """
        merged_context = {**self.extra, **context}
        return ContextAdapter(self.logger, merged_context)


def setup_logging(
    log_dir: Path,
    verbose: bool = False,
    log_to_file: bool = True,
    log_to_console: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5
) -> logging.Logger:
    """Set up structured logging with file rotation.
    
    Args:
        log_dir: Directory where log files will be stored
        verbose: Enable verbose (DEBUG) logging
        log_to_file: Enable file logging
        log_to_console: Enable console logging
        max_bytes: Maximum size of each log file before rotation
        backup_count: Number of backup log files to keep
        
    Returns:
        Configured root logger
    """
    # Determine log level
    log_level = logging.DEBUG if verbose else logging.INFO
    
    # Get root logger
    root_logger = logging.getLogger("injekt")
    root_logger.setLevel(log_level)
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Create formatters
    structured_formatter = StructuredFormatter(include_context=True)
    simple_formatter = logging.Formatter(
        fmt="%(levelname)s: %(message)s"
    )
    
    # Set up file logging
    if log_to_file:
        # Ensure log directory exists
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log file path with timestamp
        log_file = log_dir / "injekt.log"
        
        # Create rotating file handler
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(structured_formatter)
        root_logger.addHandler(file_handler)
    
    # Set up console logging
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.WARNING if not verbose else logging.DEBUG)
        console_handler.setFormatter(simple_formatter)
        root_logger.addHandler(console_handler)
    
    return root_logger


def get_logger(name: str, **context: Any) -> ContextAdapter:
    """Get a logger with optional context.
    
    Args:
        name: Name of the logger (typically __name__)
        **context: Initial context key-value pairs
        
    Returns:
        ContextAdapter with the specified context
    """
    logger = logging.getLogger(f"injekt.{name}")
    return ContextAdapter(logger, context)


def log_operation(
    logger: logging.LoggerAdapter,
    operation: str,
    **context: Any
) -> None:
    """Log an operation with structured context.
    
    Args:
        logger: The logger to use
        operation: Description of the operation
        **context: Additional context key-value pairs
    """
    logger.info(f"Operation: {operation}", extra={'context': context})


def log_error(
    logger: logging.LoggerAdapter,
    error: Exception,
    operation: Optional[str] = None,
    **context: Any
) -> None:
    """Log an error with full context and stack trace.
    
    Args:
        logger: The logger to use
        error: The exception that occurred
        operation: Optional description of the operation that failed
        **context: Additional context key-value pairs
    """
    error_context = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        **context
    }
    
    if operation:
        error_context['operation'] = operation
    
    logger.error(
        f"Error: {error}",
        exc_info=True,
        extra={'context': error_context}
    )

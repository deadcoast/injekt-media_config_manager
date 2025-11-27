"""Core domain models, types, and interfaces."""

from injekt.core.logging import (
    setup_logging,
    get_logger,
    log_operation,
    log_error,
    ContextAdapter,
)
from injekt.core.error_handler import (
    ErrorHandler,
    create_error_handler,
)

__all__ = [
    "setup_logging",
    "get_logger",
    "log_operation",
    "log_error",
    "ContextAdapter",
    "ErrorHandler",
    "create_error_handler",
]

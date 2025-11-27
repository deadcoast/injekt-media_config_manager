# Logging and Error Handling

This document describes the logging and error handling implementation in Injekt CLI.

## Overview

The Injekt CLI includes comprehensive logging and error handling capabilities that provide:

- **Structured logging** with contextual information
- **File logging** with automatic rotation
- **User-friendly error messages** with contextual help
- **Multiple verbosity levels** for different use cases
- **Proper error categorization** with appropriate exit codes

## Logging

### Setup

Logging is configured using the `setup_logging` function:

```python
from injekt.core.logging import setup_logging
from pathlib import Path

# Set up logging with default options
logger = setup_logging(
    log_dir=Path.home() / ".injekt" / "logs",
    verbose=False,
    log_to_file=True,
    log_to_console=True
)
```

### Features

1. **Structured Logging**: All log entries include timestamps, log levels, and optional structured context
2. **File Rotation**: Log files automatically rotate when they reach 10MB, keeping the 5 most recent files
3. **Verbosity Levels**: 
   - Normal mode: INFO level and above
   - Verbose mode: DEBUG level and above
4. **Multiple Outputs**: Logs can be written to both files and console simultaneously

### Usage

```python
from injekt.core.logging import get_logger, log_operation, log_error

# Get a logger with context
logger = get_logger("installer", package="mpv-ultra")

# Log operations
log_operation(logger, "Installing package", version="0.0.2")

# Log errors with full context
try:
    # ... some operation
    pass
except Exception as e:
    log_error(logger, e, operation="install", package="mpv-ultra")
```

### Context Management

The logging system supports structured context that can be added at any level:

```python
# Create logger with initial context
logger = get_logger("installer", user="admin")

# Add more context
logger_with_pkg = logger.with_context(package="mpv-ultra", version="0.0.2")

# All logs from this logger will include the context
logger_with_pkg.info("Starting installation")
```

## Error Handling

### Error Handler

The `ErrorHandler` class provides user-friendly error messages and contextual help:

```python
from injekt.core.error_handler import create_error_handler

# Create error handler
handler = create_error_handler(verbose=True)

# Handle errors
try:
    # ... some operation
    pass
except Exception as e:
    exit_code = handler.handle_error(e, logger=logger)
    sys.exit(exit_code)
```

### Error Types and Exit Codes

| Error Type | Exit Code | Description |
|------------|-----------|-------------|
| `PackageNotFoundError` | 1 | Package does not exist |
| `ValidationError` | 2 | Configuration validation failed |
| `InstallationError` | 3 | Installation operation failed |
| `BackupError` | 4 | Backup operation failed |
| `PathResolutionError` | 5 | Path detection or resolution failed |
| `ConflictError` | 6 | File conflict detected |
| `DependencyError` | 1 | Dependency resolution failed |
| Generic errors | 1 | Other unexpected errors |

### Error Messages

Each error type provides:

1. **Clear error description**: What went wrong
2. **Contextual suggestions**: How to fix the problem
3. **Relevant commands**: Commands that might help
4. **Verbose details**: Full error information in verbose mode

Example error output:

```
Validation Error: Invalid configuration syntax at line 42

The configuration or input failed validation.

Suggestions:
  • Check the configuration file syntax
  • Verify all required fields are present
  • Ensure file paths are valid and accessible
  • Run 'injekt verify <package>' to check installation
```

## Integration with CLI

The logging and error handling are designed to integrate seamlessly with the CLI:

```python
from injekt.core.logging import setup_logging, get_logger
from injekt.core.error_handler import create_error_handler
from injekt.config import InjektConfig

def main():
    # Load config
    config = InjektConfig()
    
    # Set up logging
    setup_logging(
        config.log_dir,
        verbose=config.verbose,
        log_to_file=True,
        log_to_console=True
    )
    
    # Create error handler
    error_handler = create_error_handler(verbose=config.verbose)
    
    # Get logger
    logger = get_logger("cli")
    
    try:
        # Execute CLI commands
        pass
    except Exception as e:
        exit_code = error_handler.handle_error(e, logger=logger)
        sys.exit(exit_code)
```

## Log File Location

By default, log files are stored at:
- **Windows**: `%USERPROFILE%\.injekt\logs\injekt.log`
- **Linux/Mac**: `~/.injekt/logs/injekt.log`

The location can be customized via:
- Configuration file
- Environment variable: `INJEKT_LOG_DIR`
- Command-line option: `--log-dir`

## Best Practices

1. **Always use structured logging**: Include relevant context in log messages
2. **Log at appropriate levels**:
   - DEBUG: Detailed diagnostic information
   - INFO: General informational messages
   - WARNING: Warning messages for potentially problematic situations
   - ERROR: Error messages for failures
3. **Use log_operation for operations**: Provides consistent operation logging
4. **Use log_error for exceptions**: Includes full stack traces and context
5. **Handle errors at the appropriate level**: Let errors bubble up to the CLI layer for consistent handling

## Testing

The logging and error handling implementations include comprehensive tests:

- `tests/test_logging.py`: Tests for logging functionality
- `tests/test_error_handler.py`: Tests for error handling

Run tests with:
```bash
pytest tests/test_logging.py tests/test_error_handler.py -v
```

## Example

See `examples/logging_example.py` for a complete working example of logging and error handling.

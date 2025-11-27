"""Example demonstrating logging and error handling in Injekt CLI."""

from pathlib import Path
import tempfile

from injekt.core.logging import setup_logging, get_logger, log_operation, log_error
from injekt.core.error_handler import create_error_handler
from injekt.core.errors import ValidationError, InstallationError


def main():
    """Demonstrate logging and error handling."""
    
    # Set up logging
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir) / "logs"
        root_logger = setup_logging(
            log_dir,
            verbose=True,
            log_to_console=True,
            log_to_file=True
        )
        
        print(f"Logs will be written to: {log_dir / 'injekt.log'}\n")
        
        # Get a logger with context
        logger = get_logger("example", user="demo_user")
        
        # Log some operations
        print("=== Logging Operations ===")
        log_operation(logger, "Starting installation", package="mpv-ultra")
        logger.info("Processing configuration files")
        logger.debug("Debug information about the process")
        
        # Log with additional context
        logger_with_context = logger.with_context(package="mpv-ultra", version="0.0.2")
        log_operation(logger_with_context, "Installing files")
        
        # Demonstrate error handling
        print("\n=== Error Handling ===")
        error_handler = create_error_handler(verbose=True)
        
        # Handle a validation error
        print("\n1. Handling ValidationError:")
        try:
            raise ValidationError("Invalid configuration syntax at line 42")
        except ValidationError as e:
            log_error(logger, e, operation="validate_config")
            exit_code = error_handler.handle_error(e, logger=logger)
            print(f"Exit code: {exit_code}")
        
        # Handle an installation error
        print("\n2. Handling InstallationError:")
        try:
            raise InstallationError("Failed to copy file: permission denied")
        except InstallationError as e:
            log_error(logger, e, operation="install_package", package="mpv-ultra")
            exit_code = error_handler.handle_error(e, logger=logger)
            print(f"Exit code: {exit_code}")
        
        # Clean up handlers
        for handler in root_logger.handlers[:]:
            handler.close()
            root_logger.removeHandler(handler)
        
        print("\n=== Example Complete ===")
        print(f"Check the log file at: {log_dir / 'injekt.log'}")


if __name__ == "__main__":
    main()

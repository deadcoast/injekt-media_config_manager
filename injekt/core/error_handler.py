"""Error handling with user-friendly messages and contextual help."""

import sys
from typing import Optional, Dict, Callable
from pathlib import Path

from injekt.core.errors import (
    InjektError,
    PackageNotFoundError,
    ValidationError,
    InstallationError,
    BackupError,
    PathResolutionError,
    ConflictError,
    DependencyError,
)
from injekt.core.constants import (
    EXIT_SUCCESS,
    EXIT_GENERAL_ERROR,
    EXIT_VALIDATION_ERROR,
    EXIT_INSTALLATION_ERROR,
    EXIT_BACKUP_ERROR,
    EXIT_PATH_ERROR,
    EXIT_CONFLICT_ERROR,
)


class ErrorHandler:
    """Handles errors with user-friendly messages and contextual help."""
    
    def __init__(self, verbose: bool = False):
        """Initialize the error handler.
        
        Args:
            verbose: Whether to show verbose error information
        """
        self.verbose = verbose
        self._handlers: Dict[type, Callable] = {
            PackageNotFoundError: self._handle_package_not_found,
            ValidationError: self._handle_validation_error,
            InstallationError: self._handle_installation_error,
            BackupError: self._handle_backup_error,
            PathResolutionError: self._handle_path_resolution_error,
            ConflictError: self._handle_conflict_error,
            DependencyError: self._handle_dependency_error,
        }
    
    def handle_error(self, error: Exception, logger=None) -> int:
        """Handle an error and return appropriate exit code.
        
        Args:
            error: The exception to handle
            logger: Optional logger for logging the error
            
        Returns:
            Exit code for the error
        """
        # Log the error if logger provided
        if logger:
            from injekt.core.logging import log_error
            log_error(logger, error)
        
        # Get the appropriate handler
        error_type = type(error)
        handler = self._handlers.get(error_type, self._handle_generic_error)
        
        # Handle the error and get exit code
        exit_code = handler(error)
        
        return exit_code
    
    def _handle_package_not_found(self, error: PackageNotFoundError) -> int:
        """Handle PackageNotFoundError.
        
        Args:
            error: The error to handle
            
        Returns:
            Exit code
        """
        print(f"Error: {error}", file=sys.stderr)
        print("\nThe specified package could not be found.", file=sys.stderr)
        print("\nSuggestions:", file=sys.stderr)
        print("  • Run 'injekt list' to see all available packages", file=sys.stderr)
        print("  • Check the package name for typos", file=sys.stderr)
        print("  • Ensure the assets directory contains package manifests", file=sys.stderr)
        
        if self.verbose:
            print(f"\nFull error: {repr(error)}", file=sys.stderr)
        
        return EXIT_GENERAL_ERROR
    
    def _handle_validation_error(self, error: ValidationError) -> int:
        """Handle ValidationError.
        
        Args:
            error: The error to handle
            
        Returns:
            Exit code
        """
        print(f"Validation Error: {error}", file=sys.stderr)
        print("\nThe configuration or input failed validation.", file=sys.stderr)
        print("\nSuggestions:", file=sys.stderr)
        print("  • Check the configuration file syntax", file=sys.stderr)
        print("  • Verify all required fields are present", file=sys.stderr)
        print("  • Ensure file paths are valid and accessible", file=sys.stderr)
        print("  • Run 'injekt verify <package>' to check installation", file=sys.stderr)
        
        if self.verbose:
            print(f"\nFull error: {repr(error)}", file=sys.stderr)
        
        return EXIT_VALIDATION_ERROR
    
    def _handle_installation_error(self, error: InstallationError) -> int:
        """Handle InstallationError.
        
        Args:
            error: The error to handle
            
        Returns:
            Exit code
        """
        print(f"Installation Error: {error}", file=sys.stderr)
        print("\nThe installation operation failed.", file=sys.stderr)
        print("\nSuggestions:", file=sys.stderr)
        print("  • Check that you have write permissions to the target directory", file=sys.stderr)
        print("  • Ensure sufficient disk space is available", file=sys.stderr)
        print("  • Verify the package files are not corrupted", file=sys.stderr)
        print("  • Try running with --dry-run to preview the operation", file=sys.stderr)
        print("  • Check the log files in ~/.injekt/logs/ for details", file=sys.stderr)
        
        if self.verbose:
            print(f"\nFull error: {repr(error)}", file=sys.stderr)
        
        return EXIT_INSTALLATION_ERROR
    
    def _handle_backup_error(self, error: BackupError) -> int:
        """Handle BackupError.
        
        Args:
            error: The error to handle
            
        Returns:
            Exit code
        """
        print(f"Backup Error: {error}", file=sys.stderr)
        print("\nThe backup operation failed.", file=sys.stderr)
        print("\nSuggestions:", file=sys.stderr)
        print("  • Check that you have write permissions to ~/.injekt/backups/", file=sys.stderr)
        print("  • Ensure sufficient disk space is available", file=sys.stderr)
        print("  • Verify the source files are readable", file=sys.stderr)
        print("  • Try cleaning up old backups with 'injekt backup list'", file=sys.stderr)
        
        if self.verbose:
            print(f"\nFull error: {repr(error)}", file=sys.stderr)
        
        return EXIT_BACKUP_ERROR
    
    def _handle_path_resolution_error(self, error: PathResolutionError) -> int:
        """Handle PathResolutionError.
        
        Args:
            error: The error to handle
            
        Returns:
            Exit code
        """
        print(f"Path Error: {error}", file=sys.stderr)
        print("\nCould not detect or resolve the installation path.", file=sys.stderr)
        print("\nSuggestions:", file=sys.stderr)
        print("  • Ensure the media player (MPV or VLC) is installed", file=sys.stderr)
        print("  • Check standard installation directories:", file=sys.stderr)
        print("    - MPV: %APPDATA%\\mpv", file=sys.stderr)
        print("    - VLC: %APPDATA%\\vlc", file=sys.stderr)
        print("  • Specify a custom path using the --player option", file=sys.stderr)
        print("  • Create the directory manually if it doesn't exist", file=sys.stderr)
        
        if self.verbose:
            print(f"\nFull error: {repr(error)}", file=sys.stderr)
        
        return EXIT_PATH_ERROR
    
    def _handle_conflict_error(self, error: ConflictError) -> int:
        """Handle ConflictError.
        
        Args:
            error: The error to handle
            
        Returns:
            Exit code
        """
        print(f"Conflict Error: {error}", file=sys.stderr)
        print("\nFile conflicts were detected during installation.", file=sys.stderr)
        print("\nSuggestions:", file=sys.stderr)
        print("  • Review the conflicting files listed above", file=sys.stderr)
        print("  • Create a backup before proceeding: 'injekt backup create'", file=sys.stderr)
        print("  • Use --force to overwrite existing files (creates backup)", file=sys.stderr)
        print("  • Uninstall the conflicting package first", file=sys.stderr)
        
        if self.verbose:
            print(f"\nFull error: {repr(error)}", file=sys.stderr)
        
        return EXIT_CONFLICT_ERROR
    
    def _handle_dependency_error(self, error: DependencyError) -> int:
        """Handle DependencyError.
        
        Args:
            error: The error to handle
            
        Returns:
            Exit code
        """
        print(f"Dependency Error: {error}", file=sys.stderr)
        print("\nRequired dependencies are missing or incompatible.", file=sys.stderr)
        print("\nSuggestions:", file=sys.stderr)
        print("  • Install the required dependencies first", file=sys.stderr)
        print("  • Check 'injekt info <package>' for dependency information", file=sys.stderr)
        print("  • Verify all dependency packages are available", file=sys.stderr)
        
        if self.verbose:
            print(f"\nFull error: {repr(error)}", file=sys.stderr)
        
        return EXIT_GENERAL_ERROR
    
    def _handle_generic_error(self, error: Exception) -> int:
        """Handle generic errors.
        
        Args:
            error: The error to handle
            
        Returns:
            Exit code
        """
        print(f"Error: {error}", file=sys.stderr)
        
        if isinstance(error, InjektError):
            print("\nAn unexpected Injekt error occurred.", file=sys.stderr)
        else:
            print("\nAn unexpected error occurred.", file=sys.stderr)
        
        print("\nSuggestions:", file=sys.stderr)
        print("  • Check the log files in ~/.injekt/logs/ for details", file=sys.stderr)
        print("  • Run with --verbose for more information", file=sys.stderr)
        print("  • Run 'injekt --help' for usage information", file=sys.stderr)
        
        if self.verbose:
            import traceback
            print("\nFull traceback:", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
        
        return EXIT_GENERAL_ERROR


def create_error_handler(verbose: bool = False) -> ErrorHandler:
    """Create an error handler instance.
    
    Args:
        verbose: Whether to show verbose error information
        
    Returns:
        ErrorHandler instance
    """
    return ErrorHandler(verbose=verbose)

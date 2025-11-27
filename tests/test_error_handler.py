"""Tests for error handler functionality."""

import pytest
from io import StringIO
import sys

from injekt.core.error_handler import ErrorHandler, create_error_handler
from injekt.core.errors import (
    PackageNotFoundError,
    ValidationError,
    InstallationError,
    BackupError,
    PathResolutionError,
    ConflictError,
    DependencyError,
    InjektError,
)
from injekt.core.constants import (
    EXIT_GENERAL_ERROR,
    EXIT_VALIDATION_ERROR,
    EXIT_INSTALLATION_ERROR,
    EXIT_BACKUP_ERROR,
    EXIT_PATH_ERROR,
    EXIT_CONFLICT_ERROR,
)


class TestErrorHandler:
    """Tests for ErrorHandler class."""
    
    def test_create_error_handler(self):
        """Test creating an error handler."""
        handler = create_error_handler()
        
        assert isinstance(handler, ErrorHandler)
        assert handler.verbose is False
    
    def test_create_error_handler_verbose(self):
        """Test creating a verbose error handler."""
        handler = create_error_handler(verbose=True)
        
        assert handler.verbose is True
    
    def test_handle_package_not_found_error(self, capsys):
        """Test handling PackageNotFoundError."""
        handler = ErrorHandler()
        error = PackageNotFoundError("Package 'test-pkg' not found")
        
        exit_code = handler.handle_error(error)
        
        assert exit_code == EXIT_GENERAL_ERROR
        captured = capsys.readouterr()
        assert "Package 'test-pkg' not found" in captured.err
        assert "injekt list" in captured.err
    
    def test_handle_validation_error(self, capsys):
        """Test handling ValidationError."""
        handler = ErrorHandler()
        error = ValidationError("Invalid configuration")
        
        exit_code = handler.handle_error(error)
        
        assert exit_code == EXIT_VALIDATION_ERROR
        captured = capsys.readouterr()
        assert "Invalid configuration" in captured.err
        assert "injekt verify" in captured.err
    
    def test_handle_installation_error(self, capsys):
        """Test handling InstallationError."""
        handler = ErrorHandler()
        error = InstallationError("Installation failed")
        
        exit_code = handler.handle_error(error)
        
        assert exit_code == EXIT_INSTALLATION_ERROR
        captured = capsys.readouterr()
        assert "Installation failed" in captured.err
        assert "write permissions" in captured.err
    
    def test_handle_backup_error(self, capsys):
        """Test handling BackupError."""
        handler = ErrorHandler()
        error = BackupError("Backup failed")
        
        exit_code = handler.handle_error(error)
        
        assert exit_code == EXIT_BACKUP_ERROR
        captured = capsys.readouterr()
        assert "Backup failed" in captured.err
        assert "backups" in captured.err
    
    def test_handle_path_resolution_error(self, capsys):
        """Test handling PathResolutionError."""
        handler = ErrorHandler()
        error = PathResolutionError("Path not found")
        
        exit_code = handler.handle_error(error)
        
        assert exit_code == EXIT_PATH_ERROR
        captured = capsys.readouterr()
        assert "Path not found" in captured.err
        assert "APPDATA" in captured.err
    
    def test_handle_conflict_error(self, capsys):
        """Test handling ConflictError."""
        handler = ErrorHandler()
        error = ConflictError("File conflict detected")
        
        exit_code = handler.handle_error(error)
        
        assert exit_code == EXIT_CONFLICT_ERROR
        captured = capsys.readouterr()
        assert "File conflict detected" in captured.err
        assert "backup" in captured.err
    
    def test_handle_dependency_error(self, capsys):
        """Test handling DependencyError."""
        handler = ErrorHandler()
        error = DependencyError("Missing dependency")
        
        exit_code = handler.handle_error(error)
        
        assert exit_code == EXIT_GENERAL_ERROR
        captured = capsys.readouterr()
        assert "Missing dependency" in captured.err
        assert "dependencies" in captured.err
    
    def test_handle_generic_injekt_error(self, capsys):
        """Test handling generic InjektError."""
        handler = ErrorHandler()
        error = InjektError("Generic error")
        
        exit_code = handler.handle_error(error)
        
        assert exit_code == EXIT_GENERAL_ERROR
        captured = capsys.readouterr()
        assert "Generic error" in captured.err
        assert "unexpected Injekt error" in captured.err
    
    def test_handle_generic_exception(self, capsys):
        """Test handling generic Exception."""
        handler = ErrorHandler()
        error = ValueError("Generic exception")
        
        exit_code = handler.handle_error(error)
        
        assert exit_code == EXIT_GENERAL_ERROR
        captured = capsys.readouterr()
        assert "Generic exception" in captured.err
        assert "unexpected error" in captured.err
    
    def test_verbose_mode_shows_full_error(self, capsys):
        """Test that verbose mode shows full error details."""
        handler = ErrorHandler(verbose=True)
        error = ValidationError("Test error")
        
        exit_code = handler.handle_error(error)
        
        captured = capsys.readouterr()
        assert "Full error:" in captured.err
        assert "ValidationError" in captured.err
    
    def test_verbose_mode_shows_traceback_for_generic_errors(self, capsys):
        """Test that verbose mode shows traceback for generic errors."""
        handler = ErrorHandler(verbose=True)
        error = ValueError("Test error")
        
        exit_code = handler.handle_error(error)
        
        captured = capsys.readouterr()
        assert "Full traceback:" in captured.err
    
    def test_handle_error_with_logger(self, capsys):
        """Test handling error with logger."""
        from injekt.core.logging import get_logger
        
        handler = ErrorHandler()
        logger = get_logger("test")
        error = ValidationError("Test error")
        
        exit_code = handler.handle_error(error, logger=logger)
        
        assert exit_code == EXIT_VALIDATION_ERROR
        captured = capsys.readouterr()
        assert "Test error" in captured.err


class TestErrorMessages:
    """Tests for error message content and suggestions."""
    
    def test_package_not_found_suggestions(self, capsys):
        """Test PackageNotFoundError provides helpful suggestions."""
        handler = ErrorHandler()
        error = PackageNotFoundError("Package not found")
        
        handler.handle_error(error)
        
        captured = capsys.readouterr()
        assert "Suggestions:" in captured.err
        assert "injekt list" in captured.err
        assert "typos" in captured.err
        assert "assets directory" in captured.err
    
    def test_validation_error_suggestions(self, capsys):
        """Test ValidationError provides helpful suggestions."""
        handler = ErrorHandler()
        error = ValidationError("Validation failed")
        
        handler.handle_error(error)
        
        captured = capsys.readouterr()
        assert "Suggestions:" in captured.err
        assert "syntax" in captured.err
        assert "injekt verify" in captured.err
    
    def test_installation_error_suggestions(self, capsys):
        """Test InstallationError provides helpful suggestions."""
        handler = ErrorHandler()
        error = InstallationError("Installation failed")
        
        handler.handle_error(error)
        
        captured = capsys.readouterr()
        assert "Suggestions:" in captured.err
        assert "permissions" in captured.err
        assert "disk space" in captured.err
        assert "--dry-run" in captured.err
        assert "logs" in captured.err
    
    def test_backup_error_suggestions(self, capsys):
        """Test BackupError provides helpful suggestions."""
        handler = ErrorHandler()
        error = BackupError("Backup failed")
        
        handler.handle_error(error)
        
        captured = capsys.readouterr()
        assert "Suggestions:" in captured.err
        assert "permissions" in captured.err
        assert "disk space" in captured.err
        assert "backups" in captured.err
    
    def test_path_resolution_error_suggestions(self, capsys):
        """Test PathResolutionError provides helpful suggestions."""
        handler = ErrorHandler()
        error = PathResolutionError("Path not found")
        
        handler.handle_error(error)
        
        captured = capsys.readouterr()
        assert "Suggestions:" in captured.err
        assert "MPV" in captured.err or "VLC" in captured.err
        assert "APPDATA" in captured.err
        assert "--player" in captured.err
    
    def test_conflict_error_suggestions(self, capsys):
        """Test ConflictError provides helpful suggestions."""
        handler = ErrorHandler()
        error = ConflictError("Conflict detected")
        
        handler.handle_error(error)
        
        captured = capsys.readouterr()
        assert "Suggestions:" in captured.err
        assert "backup" in captured.err
        assert "--force" in captured.err
        assert "Uninstall" in captured.err
    
    def test_dependency_error_suggestions(self, capsys):
        """Test DependencyError provides helpful suggestions."""
        handler = ErrorHandler()
        error = DependencyError("Missing dependency")
        
        handler.handle_error(error)
        
        captured = capsys.readouterr()
        assert "Suggestions:" in captured.err
        assert "dependencies" in captured.err
        assert "injekt info" in captured.err

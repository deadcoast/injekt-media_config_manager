"""Tests for logging functionality."""

import logging
import tempfile
from pathlib import Path
import pytest

from injekt.core.logging import (
    setup_logging,
    get_logger,
    log_operation,
    log_error,
    StructuredFormatter,
    ContextAdapter,
)


class TestStructuredFormatter:
    """Tests for StructuredFormatter."""
    
    def test_format_basic_message(self):
        """Test formatting a basic log message."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        
        assert "INFO" in formatted
        assert "test" in formatted
        assert "Test message" in formatted
    
    def test_format_with_context(self):
        """Test formatting with structured context."""
        formatter = StructuredFormatter(include_context=True)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.context = {"operation": "install", "package": "test-pkg"}
        
        formatted = formatter.format(record)
        
        assert "Test message" in formatted
        assert "context=" in formatted
        assert "operation" in formatted
        assert "install" in formatted
    
    def test_format_without_context(self):
        """Test formatting without context when disabled."""
        formatter = StructuredFormatter(include_context=False)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.context = {"operation": "install"}
        
        formatted = formatter.format(record)
        
        assert "Test message" in formatted
        assert "context=" not in formatted


class TestContextAdapter:
    """Tests for ContextAdapter."""
    
    def test_adapter_with_initial_context(self):
        """Test adapter with initial context."""
        logger = logging.getLogger("test")
        adapter = ContextAdapter(logger, {"user": "test_user"})
        
        assert adapter.extra == {"user": "test_user"}
    
    def test_adapter_without_initial_context(self):
        """Test adapter without initial context."""
        logger = logging.getLogger("test")
        adapter = ContextAdapter(logger)
        
        assert adapter.extra == {}
    
    def test_with_context_creates_new_adapter(self):
        """Test that with_context creates a new adapter with merged context."""
        logger = logging.getLogger("test")
        adapter1 = ContextAdapter(logger, {"user": "test_user"})
        adapter2 = adapter1.with_context(operation="install")
        
        assert adapter1.extra == {"user": "test_user"}
        assert adapter2.extra == {"user": "test_user", "operation": "install"}
    
    def test_process_adds_context_to_extra(self):
        """Test that process adds context to extra kwargs."""
        logger = logging.getLogger("test")
        adapter = ContextAdapter(logger, {"user": "test_user"})
        
        msg, kwargs = adapter.process("Test", {})
        
        assert "extra" in kwargs
        assert "context" in kwargs["extra"]
        assert kwargs["extra"]["context"] == {"user": "test_user"}


class TestSetupLogging:
    """Tests for setup_logging function."""
    
    def test_setup_logging_creates_log_directory(self):
        """Test that setup_logging creates the log directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"
            
            logger = setup_logging(log_dir, log_to_console=False)
            
            try:
                assert log_dir.exists()
                assert log_dir.is_dir()
            finally:
                # Close all handlers to release file locks
                for handler in logger.handlers[:]:
                    handler.close()
                    logger.removeHandler(handler)
    
    def test_setup_logging_creates_log_file(self):
        """Test that setup_logging creates a log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"
            
            logger = setup_logging(log_dir, log_to_console=False)
            
            try:
                log_file = log_dir / "injekt.log"
                assert log_file.exists()
            finally:
                # Close all handlers to release file locks
                for handler in logger.handlers[:]:
                    handler.close()
                    logger.removeHandler(handler)
    
    def test_setup_logging_verbose_mode(self):
        """Test that verbose mode sets DEBUG level."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"
            
            logger = setup_logging(log_dir, verbose=True, log_to_console=False)
            
            try:
                assert logger.level == logging.DEBUG
            finally:
                # Close all handlers to release file locks
                for handler in logger.handlers[:]:
                    handler.close()
                    logger.removeHandler(handler)
    
    def test_setup_logging_normal_mode(self):
        """Test that normal mode sets INFO level."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"
            
            logger = setup_logging(log_dir, verbose=False, log_to_console=False)
            
            try:
                assert logger.level == logging.INFO
            finally:
                # Close all handlers to release file locks
                for handler in logger.handlers[:]:
                    handler.close()
                    logger.removeHandler(handler)
    
    def test_setup_logging_file_only(self):
        """Test setup with file logging only."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"
            
            logger = setup_logging(
                log_dir,
                log_to_file=True,
                log_to_console=False
            )
            
            try:
                # Should have one handler (file)
                assert len(logger.handlers) == 1
            finally:
                # Close all handlers to release file locks
                for handler in logger.handlers[:]:
                    handler.close()
                    logger.removeHandler(handler)
    
    def test_setup_logging_console_only(self):
        """Test setup with console logging only."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"
            
            logger = setup_logging(
                log_dir,
                log_to_file=False,
                log_to_console=True
            )
            
            # Should have one handler (console)
            assert len(logger.handlers) == 1
    
    def test_setup_logging_both_handlers(self):
        """Test setup with both file and console logging."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"
            
            logger = setup_logging(
                log_dir,
                log_to_file=True,
                log_to_console=True
            )
            
            try:
                # Should have two handlers
                assert len(logger.handlers) == 2
            finally:
                # Close all handlers to release file locks
                for handler in logger.handlers[:]:
                    handler.close()
                    logger.removeHandler(handler)


class TestGetLogger:
    """Tests for get_logger function."""
    
    def test_get_logger_returns_adapter(self):
        """Test that get_logger returns a ContextAdapter."""
        logger = get_logger("test")
        
        assert isinstance(logger, ContextAdapter)
    
    def test_get_logger_with_context(self):
        """Test get_logger with initial context."""
        logger = get_logger("test", user="test_user", operation="install")
        
        assert logger.extra == {"user": "test_user", "operation": "install"}
    
    def test_get_logger_name_prefix(self):
        """Test that logger name has injekt prefix."""
        logger = get_logger("test")
        
        assert logger.logger.name == "injekt.test"


class TestLogOperation:
    """Tests for log_operation function."""
    
    def test_log_operation_logs_info(self, caplog):
        """Test that log_operation logs at INFO level."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"
            root_logger = setup_logging(log_dir, log_to_console=False)
            
            try:
                logger = get_logger("test")
                
                with caplog.at_level(logging.INFO):
                    log_operation(logger, "install package", package="test-pkg")
                
                assert "Operation: install package" in caplog.text
            finally:
                # Close all handlers to release file locks
                for handler in root_logger.handlers[:]:
                    handler.close()
                    root_logger.removeHandler(handler)


class TestLogError:
    """Tests for log_error function."""
    
    def test_log_error_logs_exception(self, caplog):
        """Test that log_error logs exception with stack trace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"
            root_logger = setup_logging(log_dir, log_to_console=False)
            
            try:
                logger = get_logger("test")
                error = ValueError("Test error")
                
                with caplog.at_level(logging.ERROR):
                    log_error(logger, error, operation="install")
                
                assert "Error: Test error" in caplog.text
            finally:
                # Close all handlers to release file locks
                for handler in root_logger.handlers[:]:
                    handler.close()
                    root_logger.removeHandler(handler)
    
    def test_log_error_includes_context(self, caplog):
        """Test that log_error includes context."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"
            root_logger = setup_logging(log_dir, log_to_console=False)
            
            try:
                logger = get_logger("test")
                error = ValueError("Test error")
                
                with caplog.at_level(logging.ERROR):
                    log_error(logger, error, operation="install", package="test-pkg")
                
                assert "Error: Test error" in caplog.text
            finally:
                # Close all handlers to release file locks
                for handler in root_logger.handlers[:]:
                    handler.close()
                    root_logger.removeHandler(handler)

"""Tests for the install command."""

import pytest
from pathlib import Path
from io import StringIO
from datetime import datetime

from injekt.cli.commands import InstallCommand
from injekt.cli.output import OutputFormatter
from injekt.cli.input import InputHandler
from injekt.business.package_repository import PackageRepository
from injekt.business.installer import Installer
from injekt.io.path_resolver import WindowsPathResolver
from injekt.core.models import Package, PlayerType, ProfileType, InstallationState
from injekt.core.result import Success, Failure
from injekt.core.errors import PackageNotFoundError
from rich.console import Console


@pytest.fixture
def mock_package():
    """Create a mock package for testing."""
    return Package(
        name="test-package",
        description="Test package",
        player=PlayerType.MPV,
        version="1.0.0",
        files=[],
        dependencies=[],
        profile=ProfileType.DEFAULT
    )


@pytest.fixture
def output_buffer():
    """Create a string buffer for capturing output."""
    return StringIO()


@pytest.fixture
def console(output_buffer):
    """Create a console that writes to the buffer."""
    return Console(file=output_buffer, force_terminal=True, width=120)


@pytest.fixture
def output_formatter(console):
    """Create an output formatter with the test console."""
    return OutputFormatter(output_format="text", console=console)


@pytest.fixture
def input_handler(console):
    """Create an input handler with the test console."""
    return InputHandler(console=console)


def test_install_command_validates_package_exists(
    mock_package,
    output_formatter,
    input_handler,
    tmp_path,
    output_buffer
):
    """Test that install command validates package exists."""
    # Create mocks
    from injekt.io.config_parser import ConfigParser
    from injekt.business.backup_manager import BackupManager
    from injekt.io.backup_storage import BackupStorage
    from injekt.io.file_operations import FileOperations
    from injekt.business.validator import ConfigValidatorImpl
    
    assets_dir = tmp_path / "assets"
    state_file = tmp_path / "state.json"
    backup_dir = tmp_path / "backups"
    
    config_parser = ConfigParser()
    backup_storage = BackupStorage(backup_dir)
    backup_manager = BackupManager(backup_storage)
    file_ops = FileOperations()
    validator = ConfigValidatorImpl()
    
    repo = PackageRepository(assets_dir, state_file, config_parser)
    repo.get_package = lambda name: Failure(PackageNotFoundError(f"Package not found: {name}"))
    
    installer = Installer(file_ops, backup_manager, validator, config_parser, state_file)
    path_resolver = WindowsPathResolver()
    
    command = InstallCommand(
        repo,
        installer,
        path_resolver,
        output_formatter,
        input_handler,
        dry_run=True
    )
    
    exit_code = command.execute("nonexistent-package")
    
    assert exit_code == 1
    output = output_buffer.getvalue()
    assert "not found" in output.lower() or "error" in output.lower()


def test_install_command_dry_run_mode(
    mock_package,
    output_formatter,
    input_handler,
    tmp_path,
    output_buffer,
    monkeypatch
):
    """Test that install command respects dry-run mode."""
    from injekt.io.config_parser import ConfigParser
    from injekt.business.backup_manager import BackupManager
    from injekt.io.backup_storage import BackupStorage
    from injekt.io.file_operations import FileOperations
    from injekt.business.validator import ConfigValidatorImpl
    
    assets_dir = tmp_path / "assets"
    state_file = tmp_path / "state.json"
    backup_dir = tmp_path / "backups"
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    
    config_parser = ConfigParser()
    backup_storage = BackupStorage(backup_dir)
    backup_manager = BackupManager(backup_storage)
    file_ops = FileOperations()
    validator = ConfigValidatorImpl()
    
    repo = PackageRepository(assets_dir, state_file, config_parser)
    repo.get_package = lambda name: Success(mock_package)
    
    installer = Installer(file_ops, backup_manager, validator, config_parser, state_file)
    path_resolver = WindowsPathResolver()
    
    # Mock path resolver to return target_dir
    path_resolver.detect_player_directory = lambda player: Success(target_dir)
    
    # Mock input handler to always confirm
    input_handler.prompt_for_confirmation = lambda prompt, default=False: True
    
    command = InstallCommand(
        repo,
        installer,
        path_resolver,
        output_formatter,
        input_handler,
        dry_run=True
    )
    
    exit_code = command.execute("test-package")
    
    assert exit_code == 0
    output = output_buffer.getvalue()
    assert "DRY RUN" in output or "dry" in output.lower()

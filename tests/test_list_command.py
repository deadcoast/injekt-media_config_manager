"""Tests for the list command."""

import pytest
from pathlib import Path
from io import StringIO

from injekt.cli.commands import ListCommand
from injekt.cli.output import OutputFormatter
from injekt.business.package_repository import PackageRepository
from injekt.core.models import Package, PlayerType, ProfileType, PackageFile, FileType
from injekt.core.result import Success, Failure
from injekt.core.errors import PackageNotFoundError
from injekt.io.config_parser import ConfigParser
from rich.console import Console


@pytest.fixture
def mock_packages():
    """Create mock packages for testing."""
    return [
        Package(
            name="mpv-ultra",
            description="Optimized MPV configuration",
            player=PlayerType.MPV,
            version="1.0.0",
            files=[],
            dependencies=[],
            profile=ProfileType.QUALITY
        ),
        Package(
            name="vlc-basic",
            description="Basic VLC configuration",
            player=PlayerType.VLC,
            version="0.5.0",
            files=[],
            dependencies=[],
            profile=ProfileType.DEFAULT
        )
    ]


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
def package_repository(tmp_path, mock_packages):
    """Create a package repository with mock data."""
    assets_dir = tmp_path / "assets"
    state_file = tmp_path / "state.json"
    config_parser = ConfigParser()
    
    repo = PackageRepository(assets_dir, state_file, config_parser)
    
    # Mock the list_packages method
    repo.list_packages = lambda: Success(mock_packages)
    repo.get_installed_packages = lambda: Success([mock_packages[0]])  # First package is installed
    
    return repo


def test_list_command_displays_packages(package_repository, output_formatter, output_buffer):
    """Test that list command displays all packages."""
    command = ListCommand(package_repository, output_formatter)
    
    exit_code = command.execute()
    
    assert exit_code == 0
    output = output_buffer.getvalue()
    
    # Check that package names are displayed
    assert "mpv-ultra" in output
    assert "vlc-basic" in output
    
    # Check that descriptions are displayed
    assert "Optimized MPV configuration" in output
    assert "Basic VLC configuration" in output
    
    # Check that player types are displayed
    assert "MPV" in output
    assert "VLC" in output
    
    # Check that versions are displayed
    assert "1.0.0" in output
    assert "0.5.0" in output


def test_list_command_indicates_installed_packages(package_repository, output_formatter, output_buffer):
    """Test that list command indicates which packages are installed."""
    command = ListCommand(package_repository, output_formatter)
    
    exit_code = command.execute()
    
    assert exit_code == 0
    output = output_buffer.getvalue()
    
    # Check that installed status is shown
    assert "Installed" in output


def test_list_command_handles_empty_package_list(output_formatter, tmp_path, output_buffer):
    """Test that list command handles empty package list gracefully."""
    assets_dir = tmp_path / "assets"
    state_file = tmp_path / "state.json"
    config_parser = ConfigParser()
    
    repo = PackageRepository(assets_dir, state_file, config_parser)
    repo.list_packages = lambda: Success([])
    
    command = ListCommand(repo, output_formatter)
    
    exit_code = command.execute()
    
    assert exit_code == 0
    output = output_buffer.getvalue()
    
    # Check that helpful message is displayed
    assert "No packages found" in output or "empty" in output.lower()


def test_list_command_handles_repository_error(output_formatter, tmp_path, output_buffer):
    """Test that list command handles repository errors."""
    assets_dir = tmp_path / "assets"
    state_file = tmp_path / "state.json"
    config_parser = ConfigParser()
    
    repo = PackageRepository(assets_dir, state_file, config_parser)
    repo.list_packages = lambda: Failure(PackageNotFoundError("Assets directory not found"))
    
    command = ListCommand(repo, output_formatter)
    
    exit_code = command.execute()
    
    assert exit_code == 1
    output = output_buffer.getvalue()
    
    # Check that error is displayed
    assert "Failed to list packages" in output or "error" in output.lower()

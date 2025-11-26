"""Tests for Installer."""

import pytest
import json
from pathlib import Path

from injekt.business.installer import Installer
from injekt.business.backup_manager import BackupManager
from injekt.business.validator import ConfigValidatorImpl
from injekt.io.file_operations import FileOperations
from injekt.io.backup_storage import BackupStorage
from injekt.io.config_parser import ConfigParser
from injekt.core.models import Package, PackageFile, PlayerType, ProfileType, FileType
from injekt.core.result import Success, Failure


@pytest.fixture
def temp_setup(tmp_path):
    """Create temporary directories and files for testing."""
    # Create directories
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir()
    
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    
    state_file = tmp_path / "state.json"
    
    # Create a test config file
    config_file = assets_dir / "test.conf"
    config_file.write_text("# Test config\nvo=gpu\n")
    
    return {
        'assets': assets_dir,
        'backup': backup_dir,
        'target': target_dir,
        'state': state_file,
        'config': config_file
    }


@pytest.fixture
def installer(temp_setup):
    """Create an Installer instance."""
    file_ops = FileOperations(dry_run=False)
    backup_storage = BackupStorage(temp_setup['backup'])
    backup_manager = BackupManager(backup_storage)
    validator = ConfigValidatorImpl()
    config_parser = ConfigParser()
    
    return Installer(
        file_ops=file_ops,
        backup_manager=backup_manager,
        validator=validator,
        config_parser=config_parser,
        state_file=temp_setup['state']
    )


@pytest.fixture
def sample_package(temp_setup):
    """Create a sample package."""
    return Package(
        name="test-package",
        description="Test package",
        player=PlayerType.MPV,
        version="1.0.0",
        files=[
            PackageFile(
                source_path=temp_setup['config'],
                target_path=Path("test.conf"),
                file_type=FileType.CONFIG,
                required=True
            )
        ],
        dependencies=[],
        profile=ProfileType.DEFAULT
    )


def test_install_package_success(installer, sample_package, temp_setup):
    """Test successful package installation."""
    result = installer.install_package(
        sample_package,
        temp_setup['target'],
        dry_run=False
    )
    
    assert isinstance(result, Success)
    installation = result.value
    assert installation.package.name == "test-package"
    assert len(installation.installed_files) == 1
    
    # Verify file was installed
    installed_file = temp_setup['target'] / "test.conf"
    assert installed_file.exists()


def test_install_package_dry_run(installer, sample_package, temp_setup):
    """Test package installation in dry-run mode."""
    result = installer.install_package(
        sample_package,
        temp_setup['target'],
        dry_run=True
    )
    
    assert isinstance(result, Success)
    
    # Verify file was NOT installed
    installed_file = temp_setup['target'] / "test.conf"
    assert not installed_file.exists()


def test_uninstall_package_success(installer, sample_package, temp_setup):
    """Test successful package uninstallation."""
    # First install the package
    install_result = installer.install_package(
        sample_package,
        temp_setup['target'],
        dry_run=False
    )
    assert isinstance(install_result, Success)
    
    # Verify file exists
    installed_file = temp_setup['target'] / "test.conf"
    assert installed_file.exists()
    
    # Uninstall
    uninstall_result = installer.uninstall_package("test-package", dry_run=False)
    assert isinstance(uninstall_result, Success)
    
    # Verify file was removed
    assert not installed_file.exists()


def test_verify_installation_success(installer, sample_package, temp_setup):
    """Test verification of installed package."""
    # Install package
    install_result = installer.install_package(
        sample_package,
        temp_setup['target'],
        dry_run=False
    )
    assert isinstance(install_result, Success)
    
    # Verify
    verify_result = installer.verify_installation(sample_package)
    assert isinstance(verify_result, Success)
    issues = verify_result.value
    assert len(issues) == 0


def test_verify_installation_not_installed(installer, sample_package):
    """Test verification when package is not installed."""
    verify_result = installer.verify_installation(sample_package)
    assert isinstance(verify_result, Success)
    issues = verify_result.value
    assert len(issues) > 0
    assert "not installed" in issues[0].lower()

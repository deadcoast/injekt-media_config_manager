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


def test_install_package_creates_backup(installer, sample_package, temp_setup):
    """Test that installation creates a backup when files exist."""
    # Create an existing file
    existing_file = temp_setup['target'] / "test.conf"
    existing_file.parent.mkdir(parents=True, exist_ok=True)
    existing_file.write_text("# Existing config\n")
    
    # Install package
    result = installer.install_package(
        sample_package,
        temp_setup['target'],
        dry_run=False
    )
    
    assert isinstance(result, Success)
    installation = result.value
    
    # Verify backup was created
    assert installation.backup_dir is not None
    assert installation.backup_dir.exists()


def test_install_package_validation_failure(temp_setup):
    """Test that installation fails when validation fails."""
    # Create an invalid config file
    invalid_config = temp_setup['assets'] / "invalid.conf"
    invalid_config.write_text("this is not valid syntax!!!\n")
    
    # Create package with invalid file
    invalid_package = Package(
        name="invalid-package",
        description="Invalid package",
        player=PlayerType.MPV,
        version="1.0.0",
        files=[
            PackageFile(
                source_path=invalid_config,
                target_path=Path("invalid.conf"),
                file_type=FileType.CONFIG,
                required=True
            )
        ],
        dependencies=[],
        profile=ProfileType.DEFAULT
    )
    
    file_ops = FileOperations(dry_run=False)
    backup_storage = BackupStorage(temp_setup['backup'])
    backup_manager = BackupManager(backup_storage)
    validator = ConfigValidatorImpl()
    config_parser = ConfigParser()
    
    installer = Installer(
        file_ops=file_ops,
        backup_manager=backup_manager,
        validator=validator,
        config_parser=config_parser,
        state_file=temp_setup['state']
    )
    
    # Install should fail due to validation
    result = installer.install_package(
        invalid_package,
        temp_setup['target'],
        dry_run=False
    )
    
    assert isinstance(result, Failure)


def test_install_package_conflict_detection(temp_setup):
    """Test that file conflicts are detected when file is from another package."""
    # Create two packages that try to install to the same file
    config1 = temp_setup['assets'] / "config1.conf"
    config1.write_text("# Config 1\nvo=gpu\n")
    
    package1 = Package(
        name="package1",
        description="Package 1",
        player=PlayerType.MPV,
        version="1.0.0",
        files=[
            PackageFile(
                source_path=config1,
                target_path=Path("shared.conf"),
                file_type=FileType.CONFIG,
                required=True
            )
        ],
        dependencies=[],
        profile=ProfileType.DEFAULT
    )
    
    config2 = temp_setup['assets'] / "config2.conf"
    config2.write_text("# Config 2\nvo=gpu\n")
    
    package2 = Package(
        name="package2",
        description="Package 2",
        player=PlayerType.MPV,
        version="1.0.0",
        files=[
            PackageFile(
                source_path=config2,
                target_path=Path("shared.conf"),  # Same target file
                file_type=FileType.CONFIG,
                required=True
            )
        ],
        dependencies=[],
        profile=ProfileType.DEFAULT
    )
    
    file_ops = FileOperations(dry_run=False)
    backup_storage = BackupStorage(temp_setup['backup'])
    backup_manager = BackupManager(backup_storage)
    validator = ConfigValidatorImpl()
    config_parser = ConfigParser()
    
    installer = Installer(
        file_ops=file_ops,
        backup_manager=backup_manager,
        validator=validator,
        config_parser=config_parser,
        state_file=temp_setup['state']
    )
    
    # Install first package
    result1 = installer.install_package(
        package1,
        temp_setup['target'],
        dry_run=False
    )
    assert isinstance(result1, Success)
    
    # Try to install second package - should detect conflict
    result2 = installer.install_package(
        package2,
        temp_setup['target'],
        dry_run=False
    )
    
    # Should fail with conflict error
    assert isinstance(result2, Failure)
    assert "conflict" in str(result2.error).lower()


def test_install_package_rollback_on_failure(temp_setup):
    """Test that installation rolls back on failure."""
    # Create a package with multiple files, one of which will fail
    config1 = temp_setup['assets'] / "config1.conf"
    config1.write_text("# Config 1\nvo=gpu\n")
    
    # Create a package where the second file doesn't exist
    package = Package(
        name="rollback-test",
        description="Test rollback",
        player=PlayerType.MPV,
        version="1.0.0",
        files=[
            PackageFile(
                source_path=config1,
                target_path=Path("config1.conf"),
                file_type=FileType.CONFIG,
                required=True
            ),
            PackageFile(
                source_path=temp_setup['assets'] / "nonexistent.conf",
                target_path=Path("config2.conf"),
                file_type=FileType.CONFIG,
                required=True
            )
        ],
        dependencies=[],
        profile=ProfileType.DEFAULT
    )
    
    file_ops = FileOperations(dry_run=False)
    backup_storage = BackupStorage(temp_setup['backup'])
    backup_manager = BackupManager(backup_storage)
    validator = ConfigValidatorImpl()
    config_parser = ConfigParser()
    
    installer = Installer(
        file_ops=file_ops,
        backup_manager=backup_manager,
        validator=validator,
        config_parser=config_parser,
        state_file=temp_setup['state']
    )
    
    # Install should fail
    result = installer.install_package(
        package,
        temp_setup['target'],
        dry_run=False
    )
    
    assert isinstance(result, Failure)
    
    # Verify that the first file was NOT installed (rolled back)
    installed_file = temp_setup['target'] / "config1.conf"
    assert not installed_file.exists()


def test_uninstall_package_not_installed(installer):
    """Test uninstalling a package that is not installed."""
    result = installer.uninstall_package("nonexistent-package", dry_run=False)
    assert isinstance(result, Failure)
    assert "not installed" in str(result.error).lower()


def test_uninstall_package_dry_run(installer, sample_package, temp_setup):
    """Test uninstalling in dry-run mode."""
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
    
    # Uninstall in dry-run mode
    uninstall_result = installer.uninstall_package("test-package", dry_run=True)
    assert isinstance(uninstall_result, Success)
    
    # Verify file still exists (not actually removed)
    assert installed_file.exists()


def test_verify_installation_missing_files(installer, sample_package, temp_setup):
    """Test verification when installed files are missing."""
    # Install package
    install_result = installer.install_package(
        sample_package,
        temp_setup['target'],
        dry_run=False
    )
    assert isinstance(install_result, Success)
    
    # Delete the installed file
    installed_file = temp_setup['target'] / "test.conf"
    installed_file.unlink()
    
    # Verify should report missing file
    verify_result = installer.verify_installation(sample_package)
    assert isinstance(verify_result, Success)
    issues = verify_result.value
    assert len(issues) > 0
    assert "missing" in issues[0].lower()


def test_install_package_updates_state_file(installer, sample_package, temp_setup):
    """Test that installation updates the state file."""
    # Install package
    result = installer.install_package(
        sample_package,
        temp_setup['target'],
        dry_run=False
    )
    assert isinstance(result, Success)
    
    # Verify state file was created and contains the installation
    assert temp_setup['state'].exists()
    
    # Parse state file
    config_parser = ConfigParser()
    state_result = config_parser.parse_installation_state(temp_setup['state'])
    assert isinstance(state_result, Success)
    
    installations = state_result.value
    assert len(installations) == 1
    assert installations[0].package.name == "test-package"


def test_install_package_reinstall_same_package(installer, sample_package, temp_setup):
    """Test that reinstalling the same package works (no conflict)."""
    # Install package first time
    result1 = installer.install_package(
        sample_package,
        temp_setup['target'],
        dry_run=False
    )
    assert isinstance(result1, Success)
    
    # Install same package again (update/reinstall)
    result2 = installer.install_package(
        sample_package,
        temp_setup['target'],
        dry_run=False
    )
    assert isinstance(result2, Success)
    
    # Verify file exists
    installed_file = temp_setup['target'] / "test.conf"
    assert installed_file.exists()

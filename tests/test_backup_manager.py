"""Tests for BackupManager."""

import pytest
from pathlib import Path
from datetime import datetime

from injekt.business.backup_manager import BackupManager
from injekt.io.backup_storage import BackupStorage
from injekt.core.models import Package, PackageFile, PlayerType, ProfileType, FileType
from injekt.core.result import Success, Failure


@pytest.fixture
def temp_backup_dir(tmp_path):
    """Create a temporary backup directory."""
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    return backup_dir


@pytest.fixture
def backup_storage(temp_backup_dir):
    """Create a BackupStorage instance."""
    return BackupStorage(temp_backup_dir)


@pytest.fixture
def backup_manager(backup_storage):
    """Create a BackupManager instance."""
    return BackupManager(backup_storage)


@pytest.fixture
def sample_package(tmp_path):
    """Create a sample package for testing."""
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    
    package = Package(
        name="test-package",
        description="Test package",
        player=PlayerType.MPV,
        version="1.0.0",
        files=[
            PackageFile(
                source_path=source_dir / "config.conf",
                target_path=Path("config.conf"),
                file_type=FileType.CONFIG,
                required=True
            ),
            PackageFile(
                source_path=source_dir / "script.lua",
                target_path=Path("scripts/script.lua"),
                file_type=FileType.PLUGIN_LUA,
                required=False
            )
        ],
        dependencies=[],
        profile=ProfileType.DEFAULT
    )
    
    return package


@pytest.fixture
def target_dir_with_files(tmp_path):
    """Create a target directory with test files."""
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    
    # Create test files
    (target_dir / "config.conf").write_text("# Config file")
    
    scripts_dir = target_dir / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "script.lua").write_text("-- Lua script")
    
    return target_dir


def test_create_backup_success(backup_manager, sample_package, target_dir_with_files):
    """Test creating a backup successfully."""
    result = backup_manager.create_backup(sample_package, target_dir_with_files)
    
    assert isinstance(result, Success)
    backup = result.value
    assert backup.package_name == "test-package"
    assert len(backup.files) == 2
    assert backup.backup_dir.exists()


def test_create_backup_empty_directory(backup_manager, sample_package, tmp_path):
    """Test creating a backup when target directory is empty."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    
    result = backup_manager.create_backup(sample_package, empty_dir)
    
    # Should succeed with empty backup
    assert isinstance(result, Success)
    backup = result.value
    assert len(backup.files) == 0


def test_list_backups_empty(backup_manager):
    """Test listing backups when none exist."""
    result = backup_manager.list_backups()
    
    assert isinstance(result, Success)
    backups = result.value
    assert len(backups) == 0


def test_list_backups_with_backups(backup_manager, sample_package, target_dir_with_files):
    """Test listing backups after creating some."""
    # Create two backups
    backup_manager.create_backup(sample_package, target_dir_with_files)
    backup_manager.create_backup(sample_package, target_dir_with_files)
    
    result = backup_manager.list_backups()
    
    assert isinstance(result, Success)
    backups = result.value
    assert len(backups) == 2
    # Should be sorted by timestamp (newest first)
    assert backups[0].timestamp >= backups[1].timestamp


def test_cleanup_old_backups(backup_manager, sample_package, target_dir_with_files):
    """Test cleaning up old backups."""
    # Create 7 backups
    for _ in range(7):
        backup_manager.create_backup(sample_package, target_dir_with_files)
    
    # Cleanup, keeping only 5
    result = backup_manager.cleanup_old_backups(keep_count=5)
    
    assert isinstance(result, Success)
    deleted_count = result.value
    assert deleted_count == 2
    
    # Verify only 5 remain
    list_result = backup_manager.list_backups()
    assert isinstance(list_result, Success)
    assert len(list_result.value) == 5


def test_cleanup_old_backups_fewer_than_keep_count(backup_manager, sample_package, target_dir_with_files):
    """Test cleanup when there are fewer backups than keep_count."""
    # Create 3 backups
    for _ in range(3):
        backup_manager.create_backup(sample_package, target_dir_with_files)
    
    # Try to cleanup, keeping 5
    result = backup_manager.cleanup_old_backups(keep_count=5)
    
    assert isinstance(result, Success)
    deleted_count = result.value
    assert deleted_count == 0
    
    # Verify all 3 remain
    list_result = backup_manager.list_backups()
    assert isinstance(list_result, Success)
    assert len(list_result.value) == 3

"""Property-based tests for backup storage.

Feature: injekt-cli, Property 5: Backup rotation
Validates: Requirements 5.5
"""

import tempfile
import time
from pathlib import Path
from hypothesis import given, strategies as st, settings

from injekt.io.backup_storage import BackupStorage
from injekt.core.result import Success


@given(
    num_backups=st.integers(min_value=6, max_value=20),
    keep_count=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=100, deadline=None)
def test_backup_rotation(num_backups, keep_count):
    """
    Feature: injekt-cli, Property 5: Backup rotation
    Validates: Requirements 5.5
    
    For any backup operation, when more than keep_count backups exist, 
    only the keep_count most recent backups should remain.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        backup_root = tmpdir_path / "backups"
        source_dir = tmpdir_path / "source"
        source_dir.mkdir()
        
        # Create a test file
        test_file = source_dir / "test.conf"
        test_file.write_text("test content")
        
        # Create backup storage
        storage = BackupStorage(backup_root)
        
        # Create multiple backups
        package_name = "test-package"
        for i in range(num_backups):
            # Small delay to ensure different timestamps
            if i > 0:
                time.sleep(0.01)
            
            result = storage.create_backup(
                package_name=package_name,
                source_files=[test_file],
                source_dir=source_dir
            )
            assert isinstance(result, Success), f"Failed to create backup {i}"
        
        # List backups before cleanup
        list_result = storage.list_backups(package_name)
        assert isinstance(list_result, Success), "Failed to list backups"
        backups_before = list_result.value
        assert len(backups_before) == num_backups, f"Should have {num_backups} backups"
        
        # Cleanup old backups
        cleanup_result = storage.cleanup_old_backups(package_name, keep_count)
        assert isinstance(cleanup_result, Success), "Failed to cleanup backups"
        
        deleted_count = cleanup_result.value
        expected_deleted = num_backups - keep_count
        assert deleted_count == expected_deleted, \
            f"Should delete {expected_deleted} backups, deleted {deleted_count}"
        
        # List backups after cleanup
        list_result = storage.list_backups(package_name)
        assert isinstance(list_result, Success), "Failed to list backups after cleanup"
        backups_after = list_result.value
        
        # Should have exactly keep_count backups remaining
        assert len(backups_after) == keep_count, \
            f"Should have {keep_count} backups after cleanup, have {len(backups_after)}"
        
        # The remaining backups should be the most recent ones
        # (backups are sorted newest first)
        expected_remaining = backups_before[:keep_count]
        remaining_ids = {b.backup_id for b in backups_after}
        expected_ids = {b.backup_id for b in expected_remaining}
        
        assert remaining_ids == expected_ids, \
            "Should keep the most recent backups"


@given(
    num_backups=st.integers(min_value=1, max_value=5),
    keep_count=st.integers(min_value=5, max_value=10)
)
@settings(max_examples=100)
def test_backup_rotation_no_deletion_when_under_limit(num_backups, keep_count):
    """
    Feature: injekt-cli, Property 5: Backup rotation
    Validates: Requirements 5.5
    
    For any backup operation, when fewer than keep_count backups exist,
    no backups should be deleted.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        backup_root = tmpdir_path / "backups"
        source_dir = tmpdir_path / "source"
        source_dir.mkdir()
        
        # Create a test file
        test_file = source_dir / "test.conf"
        test_file.write_text("test content")
        
        # Create backup storage
        storage = BackupStorage(backup_root)
        
        # Create backups (fewer than keep_count)
        package_name = "test-package"
        for i in range(num_backups):
            if i > 0:
                time.sleep(0.01)
            
            result = storage.create_backup(
                package_name=package_name,
                source_files=[test_file],
                source_dir=source_dir
            )
            assert isinstance(result, Success), f"Failed to create backup {i}"
        
        # Cleanup old backups
        cleanup_result = storage.cleanup_old_backups(package_name, keep_count)
        assert isinstance(cleanup_result, Success), "Failed to cleanup backups"
        
        deleted_count = cleanup_result.value
        
        # Should not delete any backups
        assert deleted_count == 0, \
            f"Should not delete any backups when under limit, deleted {deleted_count}"
        
        # List backups after cleanup
        list_result = storage.list_backups(package_name)
        assert isinstance(list_result, Success), "Failed to list backups after cleanup"
        backups_after = list_result.value
        
        # Should still have all backups
        assert len(backups_after) == num_backups, \
            f"Should have {num_backups} backups, have {len(backups_after)}"


@given(
    num_backups=st.integers(min_value=10, max_value=20)
)
@settings(max_examples=100, deadline=None)
def test_backup_rotation_keeps_exactly_five(num_backups):
    """
    Feature: injekt-cli, Property 5: Backup rotation
    Validates: Requirements 5.5
    
    For any backup operation with default keep_count (5), when more than 5 backups exist,
    exactly 5 backups should remain.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        backup_root = tmpdir_path / "backups"
        source_dir = tmpdir_path / "source"
        source_dir.mkdir()
        
        # Create a test file
        test_file = source_dir / "test.conf"
        test_file.write_text("test content")
        
        # Create backup storage
        storage = BackupStorage(backup_root)
        
        # Create multiple backups
        package_name = "test-package"
        for i in range(num_backups):
            if i > 0:
                time.sleep(0.01)
            
            result = storage.create_backup(
                package_name=package_name,
                source_files=[test_file],
                source_dir=source_dir
            )
            assert isinstance(result, Success), f"Failed to create backup {i}"
        
        # Cleanup with default keep_count (5)
        cleanup_result = storage.cleanup_old_backups(package_name)
        assert isinstance(cleanup_result, Success), "Failed to cleanup backups"
        
        # List backups after cleanup
        list_result = storage.list_backups(package_name)
        assert isinstance(list_result, Success), "Failed to list backups after cleanup"
        backups_after = list_result.value
        
        # Should have exactly 5 backups
        assert len(backups_after) == 5, \
            f"Should have exactly 5 backups after cleanup, have {len(backups_after)}"

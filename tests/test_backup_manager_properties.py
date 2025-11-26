"""Property-based tests for BackupManager.

Feature: injekt-cli, Property 2: Installation creates backup
Validates: Requirements 2.4, 5.1, 5.2
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from hypothesis import given, strategies as st, settings

from injekt.business.backup_manager import BackupManager
from injekt.io.backup_storage import BackupStorage
from injekt.core.models import Package, PackageFile, PlayerType, ProfileType, FileType
from injekt.core.result import Success


def create_temp_dirs():
    """Create temporary directories for testing."""
    temp_base = Path(tempfile.mkdtemp())
    
    backup_dir = temp_base / "backups"
    backup_dir.mkdir()
    
    target_dir = temp_base / "target"
    target_dir.mkdir()
    
    source_dir = temp_base / "source"
    source_dir.mkdir()
    
    return {
        'base': temp_base,
        'backup': backup_dir,
        'target': target_dir,
        'source': source_dir
    }


def cleanup_temp_dirs(temp_dirs):
    """Clean up temporary directories."""
    if temp_dirs['base'].exists():
        shutil.rmtree(temp_dirs['base'])


@settings(max_examples=100)
@given(
    num_files=st.integers(min_value=1, max_value=10)
)
def test_property_backup_creation_with_existing_files(num_files):
    """
    **Feature: injekt-cli, Property 2: Installation creates backup**
    **Validates: Requirements 2.4, 5.1, 5.2**
    
    Property: For any package installation where existing configs are present,
    a backup should be created before any files are modified.
    
    This test verifies that:
    1. When files exist in the target directory
    2. And we create a backup for a package
    3. Then a backup is successfully created
    4. And the backup contains all existing files
    """
    temp_dirs = create_temp_dirs()
    try:
        backup_storage = BackupStorage(temp_dirs['backup'])
        backup_manager = BackupManager(backup_storage)
        
        # Create a package with random files
        package_files = []
        created_files = []
        
        for i in range(num_files):
            target_path = Path(f"file_{i}.conf")
            package_file = PackageFile(
                source_path=temp_dirs['source'] / f"source_{i}.conf",
                target_path=target_path,
                file_type=FileType.CONFIG,
                required=True
            )
            package_files.append(package_file)
            
            # Create the file in target directory
            file_path = temp_dirs['target'] / target_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(f"Content {i}")
            created_files.append(target_path)
        
        package = Package(
            name="test-package",
            description="Test package",
            player=PlayerType.MPV,
            version="1.0.0",
            files=package_files,
            dependencies=[],
            profile=ProfileType.DEFAULT
        )
        
        # Create backup
        result = backup_manager.create_backup(package, temp_dirs['target'])
        
        # Verify backup was created successfully
        assert isinstance(result, Success), f"Backup creation failed: {result}"
        
        backup = result.value
        
        # Verify backup contains all files
        assert backup.package_name == "test-package"
        assert len(backup.files) == num_files
        
        # Verify all files are in the backup
        backup_file_names = {f.name for f in backup.files}
        created_file_names = {f.name for f in created_files}
        assert backup_file_names == created_file_names
        
        # Verify backup directory exists
        assert backup.backup_dir.exists()
        
        # Verify files were actually copied to backup
        for file_path in backup.files:
            backup_file = backup.backup_dir / file_path
            assert backup_file.exists(), f"Backup file does not exist: {backup_file}"
    finally:
        cleanup_temp_dirs(temp_dirs)


@settings(max_examples=100)
@given(
    num_files=st.integers(min_value=1, max_value=10),
    num_existing=st.integers(min_value=0, max_value=10)
)
def test_property_backup_only_existing_files(num_files, num_existing):
    """
    **Feature: injekt-cli, Property 2: Installation creates backup**
    **Validates: Requirements 2.4, 5.1, 5.2**
    
    Property: Backups should only include files that actually exist in the target directory.
    
    This test verifies that:
    1. When a package has N files defined
    2. But only M files exist in the target directory (M <= N)
    3. Then the backup contains exactly M files
    """
    temp_dirs = create_temp_dirs()
    try:
        # Ensure num_existing doesn't exceed num_files
        num_existing = min(num_existing, num_files)
        
        backup_storage = BackupStorage(temp_dirs['backup'])
        backup_manager = BackupManager(backup_storage)
        
        # Create a package with num_files files
        package_files = []
        
        for i in range(num_files):
            target_path = Path(f"file_{i}.conf")
            package_file = PackageFile(
                source_path=temp_dirs['source'] / f"source_{i}.conf",
                target_path=target_path,
                file_type=FileType.CONFIG,
                required=True
            )
            package_files.append(package_file)
            
            # Only create num_existing files in target directory
            if i < num_existing:
                file_path = temp_dirs['target'] / target_path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(f"Content {i}")
        
        package = Package(
            name="test-package",
            description="Test package",
            player=PlayerType.MPV,
            version="1.0.0",
            files=package_files,
            dependencies=[],
            profile=ProfileType.DEFAULT
        )
        
        # Create backup
        result = backup_manager.create_backup(package, temp_dirs['target'])
        
        # Verify backup was created successfully
        assert isinstance(result, Success)
        
        backup = result.value
        
        # Verify backup contains only existing files
        assert len(backup.files) == num_existing
    finally:
        cleanup_temp_dirs(temp_dirs)


@settings(max_examples=100)
@given(
    package_name=st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), min_codepoint=65, max_codepoint=122),
        min_size=1,
        max_size=30
    )
)
def test_property_backup_metadata_correctness(package_name):
    """
    **Feature: injekt-cli, Property 2: Installation creates backup**
    **Validates: Requirements 2.4, 5.1, 5.2**
    
    Property: Backup metadata should correctly reflect the package being backed up.
    
    This test verifies that:
    1. For any package name
    2. When a backup is created
    3. Then the backup metadata contains the correct package name
    4. And the backup has a valid timestamp
    5. And the backup has a unique ID
    """
    temp_dirs = create_temp_dirs()
    try:
        backup_storage = BackupStorage(temp_dirs['backup'])
        backup_manager = BackupManager(backup_storage)
        
        # Create a simple package
        package = Package(
            name=package_name,
            description="Test package",
            player=PlayerType.MPV,
            version="1.0.0",
            files=[
                PackageFile(
                    source_path=temp_dirs['source'] / "test.conf",
                    target_path=Path("test.conf"),
                    file_type=FileType.CONFIG,
                    required=True
                )
            ],
            dependencies=[],
            profile=ProfileType.DEFAULT
        )
        
        # Create a file in target
        (temp_dirs['target'] / "test.conf").write_text("test content")
        
        # Create backup
        result = backup_manager.create_backup(package, temp_dirs['target'])
        
        assert isinstance(result, Success)
        backup = result.value
        
        # Verify metadata
        assert backup.package_name == package_name
        assert backup.timestamp is not None
        assert backup.backup_id is not None
        assert package_name in backup.backup_id  # Backup ID should contain package name
    finally:
        cleanup_temp_dirs(temp_dirs)



@settings(max_examples=100)
@given(
    num_files=st.integers(min_value=1, max_value=10),
    file_content=st.text(
        alphabet=st.characters(min_codepoint=32, max_codepoint=126),
        min_size=1,
        max_size=100
    )
)
def test_property_rollback_round_trip(num_files, file_content):
    """
    **Feature: injekt-cli, Property 6: Rollback round-trip**
    **Validates: Requirements 6.2**
    
    Property: For any configuration state, creating a backup and then restoring it
    should result in the same file contents.
    
    This test verifies that:
    1. When files exist in a target directory
    2. And we create a backup
    3. And we modify the files
    4. And we restore the backup
    5. Then the files should have their original content
    """
    temp_dirs = create_temp_dirs()
    try:
        backup_storage = BackupStorage(temp_dirs['backup'])
        backup_manager = BackupManager(backup_storage)
        
        # Create original files with specific content
        package_files = []
        original_contents = {}
        
        for i in range(num_files):
            target_path = Path(f"file_{i}.conf")
            package_file = PackageFile(
                source_path=temp_dirs['source'] / f"source_{i}.conf",
                target_path=target_path,
                file_type=FileType.CONFIG,
                required=True
            )
            package_files.append(package_file)
            
            # Create the file in target directory with original content
            file_path = temp_dirs['target'] / target_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            original_content = f"{file_content}_{i}"
            file_path.write_text(original_content)
            original_contents[target_path] = original_content
        
        package = Package(
            name="test-package",
            description="Test package",
            player=PlayerType.MPV,
            version="1.0.0",
            files=package_files,
            dependencies=[],
            profile=ProfileType.DEFAULT
        )
        
        # Create backup
        backup_result = backup_manager.create_backup(package, temp_dirs['target'])
        assert isinstance(backup_result, Success)
        backup = backup_result.value
        
        # Modify the files
        for target_path in original_contents.keys():
            file_path = temp_dirs['target'] / target_path
            file_path.write_text("MODIFIED CONTENT")
        
        # Verify files were modified
        for target_path in original_contents.keys():
            file_path = temp_dirs['target'] / target_path
            assert file_path.read_text() == "MODIFIED CONTENT"
        
        # Restore backup
        restore_result = backup_manager.restore_backup(backup.backup_id)
        assert isinstance(restore_result, Success)
        
        # Verify files have original content
        for target_path, original_content in original_contents.items():
            file_path = temp_dirs['target'] / target_path
            assert file_path.exists(), f"File should exist after restore: {file_path}"
            restored_content = file_path.read_text()
            assert restored_content == original_content, \
                f"Content mismatch for {target_path}: expected '{original_content}', got '{restored_content}'"
    finally:
        cleanup_temp_dirs(temp_dirs)

"""Property-based tests for Installer.

Feature: injekt-cli, Property 12: Conflict detection
Validates: Requirements 13.1
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from hypothesis import given, strategies as st, settings

from injekt.business.installer import Installer
from injekt.business.backup_manager import BackupManager
from injekt.business.validator import ConfigValidatorImpl
from injekt.io.file_operations import FileOperations
from injekt.io.backup_storage import BackupStorage
from injekt.io.config_parser import ConfigParser
from injekt.core.models import Package, PackageFile, PlayerType, ProfileType, FileType
from injekt.core.result import Success, Failure
from injekt.core.errors import ConflictError


def create_temp_dirs():
    """Create temporary directories for testing."""
    temp_base = Path(tempfile.mkdtemp())
    
    backup_dir = temp_base / "backups"
    backup_dir.mkdir()
    
    target_dir = temp_base / "target"
    target_dir.mkdir()
    
    source_dir = temp_base / "source"
    source_dir.mkdir()
    
    state_file = temp_base / "state.json"
    
    return {
        'base': temp_base,
        'backup': backup_dir,
        'target': target_dir,
        'source': source_dir,
        'state': state_file
    }


def cleanup_temp_dirs(temp_dirs):
    """Clean up temporary directories."""
    if temp_dirs['base'].exists():
        shutil.rmtree(temp_dirs['base'])


def create_installer(temp_dirs):
    """Create an Installer instance."""
    file_ops = FileOperations(dry_run=False)
    backup_storage = BackupStorage(temp_dirs['backup'])
    backup_manager = BackupManager(backup_storage)
    validator = ConfigValidatorImpl()
    config_parser = ConfigParser()
    
    return Installer(
        file_ops=file_ops,
        backup_manager=backup_manager,
        validator=validator,
        config_parser=config_parser,
        state_file=temp_dirs['state']
    )


@settings(max_examples=100)
@given(
    num_files=st.integers(min_value=1, max_value=10),
    num_conflicting=st.integers(min_value=1, max_value=10)
)
def test_property_conflict_detection_different_packages(num_files, num_conflicting):
    """
    **Feature: injekt-cli, Property 12: Conflict detection**
    **Validates: Requirements 13.1**
    
    Property: For any installation where target files already exist from a different package,
    conflicts should be detected and reported before modification.
    
    This test verifies that:
    1. When package A is installed
    2. And package B tries to install files to the same paths
    3. Then conflicts are detected
    4. And the installation fails with a ConflictError
    5. And the conflicting file paths are reported
    """
    temp_dirs = create_temp_dirs()
    try:
        # Ensure num_conflicting doesn't exceed num_files
        num_conflicting = min(num_conflicting, num_files)
        
        installer = create_installer(temp_dirs)
        
        # Create package A with files
        package_a_files = []
        for i in range(num_files):
            source_path = temp_dirs['source'] / f"package_a_{i}.conf"
            source_path.write_text(f"# Package A config {i}\nvo=gpu\n")
            
            package_file = PackageFile(
                source_path=source_path,
                target_path=Path(f"file_{i}.conf"),
                file_type=FileType.CONFIG,
                required=True
            )
            package_a_files.append(package_file)
        
        package_a = Package(
            name="package-a",
            description="Package A",
            player=PlayerType.MPV,
            version="1.0.0",
            files=package_a_files,
            dependencies=[],
            profile=ProfileType.DEFAULT
        )
        
        # Install package A
        result_a = installer.install_package(package_a, temp_dirs['target'], dry_run=False)
        assert isinstance(result_a, Success), f"Package A installation failed: {result_a}"
        
        # Create package B with some overlapping files
        package_b_files = []
        for i in range(num_files):
            source_path = temp_dirs['source'] / f"package_b_{i}.conf"
            source_path.write_text(f"# Package B config {i}\nvo=gpu\n")
            
            # First num_conflicting files conflict with package A
            if i < num_conflicting:
                target_path = Path(f"file_{i}.conf")  # Same as package A
            else:
                target_path = Path(f"unique_b_{i}.conf")  # Unique to package B
            
            package_file = PackageFile(
                source_path=source_path,
                target_path=target_path,
                file_type=FileType.CONFIG,
                required=True
            )
            package_b_files.append(package_file)
        
        package_b = Package(
            name="package-b",
            description="Package B",
            player=PlayerType.MPV,
            version="1.0.0",
            files=package_b_files,
            dependencies=[],
            profile=ProfileType.DEFAULT
        )
        
        # Try to install package B - should detect conflicts
        result_b = installer.install_package(package_b, temp_dirs['target'], dry_run=False)
        
        # Verify conflict was detected
        assert isinstance(result_b, Failure), \
            f"Expected conflict detection to fail, but got success"
        
        assert isinstance(result_b.error, ConflictError), \
            f"Expected ConflictError, got {type(result_b.error).__name__}"
        
        # Verify error message contains "conflict"
        error_message = str(result_b.error).lower()
        assert "conflict" in error_message, \
            f"Error message should mention 'conflict': {result_b.error}"
        
        # Verify conflicting file paths are mentioned in the error
        for i in range(num_conflicting):
            conflicting_file = f"file_{i}.conf"
            assert conflicting_file in str(result_b.error), \
                f"Conflicting file '{conflicting_file}' should be in error message"
    
    finally:
        cleanup_temp_dirs(temp_dirs)


@settings(max_examples=100)
@given(
    num_files=st.integers(min_value=1, max_value=10)
)
def test_property_no_conflict_same_package_reinstall(num_files):
    """
    **Feature: injekt-cli, Property 12: Conflict detection**
    **Validates: Requirements 13.1**
    
    Property: Reinstalling the same package should NOT be detected as a conflict.
    
    This test verifies that:
    1. When a package is installed
    2. And the same package is installed again (update/reinstall)
    3. Then no conflicts are detected
    4. And the installation succeeds
    """
    temp_dirs = create_temp_dirs()
    try:
        installer = create_installer(temp_dirs)
        
        # Create package with files
        package_files = []
        for i in range(num_files):
            source_path = temp_dirs['source'] / f"config_{i}.conf"
            source_path.write_text(f"# Config {i}\nvo=gpu\n")
            
            package_file = PackageFile(
                source_path=source_path,
                target_path=Path(f"file_{i}.conf"),
                file_type=FileType.CONFIG,
                required=True
            )
            package_files.append(package_file)
        
        package = Package(
            name="test-package",
            description="Test package",
            player=PlayerType.MPV,
            version="1.0.0",
            files=package_files,
            dependencies=[],
            profile=ProfileType.DEFAULT
        )
        
        # Install package first time
        result1 = installer.install_package(package, temp_dirs['target'], dry_run=False)
        assert isinstance(result1, Success), f"First installation failed: {result1}"
        
        # Install same package again (reinstall/update)
        result2 = installer.install_package(package, temp_dirs['target'], dry_run=False)
        
        # Should succeed without conflict
        assert isinstance(result2, Success), \
            f"Reinstalling same package should not conflict, but got: {result2}"
    
    finally:
        cleanup_temp_dirs(temp_dirs)


@settings(max_examples=100)
@given(
    num_files=st.integers(min_value=1, max_value=10)
)
def test_property_no_conflict_untracked_files(num_files):
    """
    **Feature: injekt-cli, Property 12: Conflict detection**
    **Validates: Requirements 13.1**
    
    Property: Files that exist but are not tracked by any package should NOT be
    detected as conflicts (they will be backed up per Requirement 2.4).
    
    This test verifies that:
    1. When untracked files exist in the target directory
    2. And a package tries to install to those paths
    3. Then no conflicts are detected
    4. And the installation succeeds (with backup per Requirement 2.4)
    """
    temp_dirs = create_temp_dirs()
    try:
        installer = create_installer(temp_dirs)
        
        # Create untracked files in target directory
        for i in range(num_files):
            untracked_file = temp_dirs['target'] / f"file_{i}.conf"
            untracked_file.write_text(f"# Untracked file {i}\n")
        
        # Create package that will overwrite these untracked files
        package_files = []
        for i in range(num_files):
            source_path = temp_dirs['source'] / f"config_{i}.conf"
            source_path.write_text(f"# New config {i}\nvo=gpu\n")
            
            package_file = PackageFile(
                source_path=source_path,
                target_path=Path(f"file_{i}.conf"),
                file_type=FileType.CONFIG,
                required=True
            )
            package_files.append(package_file)
        
        package = Package(
            name="test-package",
            description="Test package",
            player=PlayerType.MPV,
            version="1.0.0",
            files=package_files,
            dependencies=[],
            profile=ProfileType.DEFAULT
        )
        
        # Install package - should succeed despite existing untracked files
        result = installer.install_package(package, temp_dirs['target'], dry_run=False)
        
        # Should succeed without conflict (untracked files are backed up, not conflicts)
        assert isinstance(result, Success), \
            f"Installing over untracked files should succeed with backup, but got: {result}"
        
        # Verify backup was created
        assert result.value.backup_dir is not None, \
            "Backup should be created when overwriting existing files"
    
    finally:
        cleanup_temp_dirs(temp_dirs)


@settings(max_examples=100)
@given(
    num_package_a_files=st.integers(min_value=1, max_value=5),
    num_package_b_files=st.integers(min_value=1, max_value=5),
    num_overlapping=st.integers(min_value=0, max_value=5)
)
def test_property_conflict_detection_partial_overlap(
    num_package_a_files,
    num_package_b_files,
    num_overlapping
):
    """
    **Feature: injekt-cli, Property 12: Conflict detection**
    **Validates: Requirements 13.1**
    
    Property: When packages have partial file overlap, only the overlapping files
    should be reported as conflicts.
    
    This test verifies that:
    1. When package A is installed with N files
    2. And package B tries to install M files, K of which overlap with A
    3. Then exactly K conflicts are detected
    4. And the error message lists all K conflicting files
    """
    temp_dirs = create_temp_dirs()
    try:
        # Ensure num_overlapping doesn't exceed either package's file count
        num_overlapping = min(num_overlapping, num_package_a_files, num_package_b_files)
        
        installer = create_installer(temp_dirs)
        
        # Create package A
        package_a_files = []
        for i in range(num_package_a_files):
            source_path = temp_dirs['source'] / f"package_a_{i}.conf"
            source_path.write_text(f"# Package A config {i}\nvo=gpu\n")
            
            package_file = PackageFile(
                source_path=source_path,
                target_path=Path(f"file_{i}.conf"),
                file_type=FileType.CONFIG,
                required=True
            )
            package_a_files.append(package_file)
        
        package_a = Package(
            name="package-a",
            description="Package A",
            player=PlayerType.MPV,
            version="1.0.0",
            files=package_a_files,
            dependencies=[],
            profile=ProfileType.DEFAULT
        )
        
        # Install package A
        result_a = installer.install_package(package_a, temp_dirs['target'], dry_run=False)
        assert isinstance(result_a, Success)
        
        # Create package B with partial overlap
        package_b_files = []
        expected_conflicts = []
        
        for i in range(num_package_b_files):
            source_path = temp_dirs['source'] / f"package_b_{i}.conf"
            source_path.write_text(f"# Package B config {i}\nvo=gpu\n")
            
            # First num_overlapping files overlap with package A
            if i < num_overlapping:
                target_path = Path(f"file_{i}.conf")  # Overlaps with package A
                expected_conflicts.append(str(temp_dirs['target'] / target_path))
            else:
                target_path = Path(f"unique_b_{i}.conf")  # Unique to package B
            
            package_file = PackageFile(
                source_path=source_path,
                target_path=target_path,
                file_type=FileType.CONFIG,
                required=True
            )
            package_b_files.append(package_file)
        
        package_b = Package(
            name="package-b",
            description="Package B",
            player=PlayerType.MPV,
            version="1.0.0",
            files=package_b_files,
            dependencies=[],
            profile=ProfileType.DEFAULT
        )
        
        # Try to install package B
        result_b = installer.install_package(package_b, temp_dirs['target'], dry_run=False)
        
        if num_overlapping > 0:
            # Should detect conflicts
            assert isinstance(result_b, Failure), \
                f"Expected conflict detection when {num_overlapping} files overlap"
            
            assert isinstance(result_b.error, ConflictError)
            
            # Verify all conflicting files are mentioned
            error_str = str(result_b.error)
            for conflict_path in expected_conflicts:
                # Check if the filename is in the error (path separators may vary)
                filename = Path(conflict_path).name
                assert filename in error_str, \
                    f"Conflicting file '{filename}' should be in error message"
        else:
            # No overlap, should succeed
            assert isinstance(result_b, Success), \
                f"Expected success when no files overlap, but got: {result_b}"
    
    finally:
        cleanup_temp_dirs(temp_dirs)


@settings(max_examples=100)
@given(
    num_files=st.integers(min_value=2, max_value=10),
    fail_at_index=st.integers(min_value=1, max_value=9)
)
def test_property_atomic_installation(num_files, fail_at_index):
    """
    **Feature: injekt-cli, Property 20: Atomic installation**
    **Validates: Requirements 5.3**
    
    Property: For any installation operation, if any step fails, all changes should be rolled back.
    
    This test verifies that:
    1. When a package has multiple files to install
    2. And one of the files fails to copy (e.g., source doesn't exist)
    3. Then the installation fails
    4. And all previously installed files are rolled back (removed)
    5. And the target directory is left in its original state
    """
    temp_dirs = create_temp_dirs()
    try:
        # Ensure fail_at_index is within bounds
        fail_at_index = min(fail_at_index, num_files - 1)
        
        installer = create_installer(temp_dirs)
        
        # Create some existing files in target to verify they're not affected
        existing_file = temp_dirs['target'] / "existing.conf"
        existing_file.write_text("# Existing file\n")
        existing_content = existing_file.read_text()
        
        # Create package with multiple files, one of which will fail
        package_files = []
        for i in range(num_files):
            if i == fail_at_index:
                # This file doesn't exist - will cause failure
                source_path = temp_dirs['source'] / f"nonexistent_{i}.conf"
            else:
                # Valid file
                source_path = temp_dirs['source'] / f"config_{i}.conf"
                source_path.write_text(f"# Config {i}\nvo=gpu\n")
            
            package_file = PackageFile(
                source_path=source_path,
                target_path=Path(f"file_{i}.conf"),
                file_type=FileType.CONFIG,
                required=True
            )
            package_files.append(package_file)
        
        package = Package(
            name="atomic-test-package",
            description="Test atomic installation",
            player=PlayerType.MPV,
            version="1.0.0",
            files=package_files,
            dependencies=[],
            profile=ProfileType.DEFAULT
        )
        
        # Try to install - should fail
        result = installer.install_package(package, temp_dirs['target'], dry_run=False)
        
        # Verify installation failed
        assert isinstance(result, Failure), \
            f"Expected installation to fail when file {fail_at_index} doesn't exist"
        
        # Verify rollback: no files from the package should exist
        for i in range(num_files):
            target_file = temp_dirs['target'] / f"file_{i}.conf"
            assert not target_file.exists(), \
                f"File {i} should have been rolled back but still exists at {target_file}"
        
        # Verify existing files are untouched
        assert existing_file.exists(), \
            "Existing file should not be affected by failed installation"
        assert existing_file.read_text() == existing_content, \
            "Existing file content should not be modified"
        
        # Verify state file doesn't contain the failed installation
        config_parser = ConfigParser()
        state_result = config_parser.parse_installation_state(temp_dirs['state'])
        
        if isinstance(state_result, Success):
            installations = state_result.value
            package_names = [inst.package.name for inst in installations]
            assert "atomic-test-package" not in package_names, \
                "Failed installation should not be recorded in state file"
    
    finally:
        cleanup_temp_dirs(temp_dirs)


@settings(max_examples=100)
@given(
    num_files=st.integers(min_value=2, max_value=8)
)
def test_property_atomic_installation_validation_failure(num_files):
    """
    **Feature: injekt-cli, Property 20: Atomic installation**
    **Validates: Requirements 5.3**
    
    Property: For any installation operation, if validation fails, no files should be installed.
    
    This test verifies that:
    1. When a package has multiple files
    2. And one file fails validation
    3. Then the installation fails before any files are copied
    4. And no files are installed to the target directory
    """
    temp_dirs = create_temp_dirs()
    try:
        installer = create_installer(temp_dirs)
        
        # Create some existing files in target to verify they're not affected
        existing_file = temp_dirs['target'] / "existing.conf"
        existing_file.write_text("# Existing file\n")
        existing_content = existing_file.read_text()
        
        # Create package with one invalid file
        package_files = []
        for i in range(num_files):
            source_path = temp_dirs['source'] / f"config_{i}.conf"
            
            if i == 0:
                # First file is invalid
                source_path.write_text("this is not valid config syntax!!!\n")
            else:
                # Other files are valid
                source_path.write_text(f"# Config {i}\nvo=gpu\n")
            
            package_file = PackageFile(
                source_path=source_path,
                target_path=Path(f"file_{i}.conf"),
                file_type=FileType.CONFIG,
                required=True
            )
            package_files.append(package_file)
        
        package = Package(
            name="validation-fail-package",
            description="Test validation failure",
            player=PlayerType.MPV,
            version="1.0.0",
            files=package_files,
            dependencies=[],
            profile=ProfileType.DEFAULT
        )
        
        # Try to install - should fail validation
        result = installer.install_package(package, temp_dirs['target'], dry_run=False)
        
        # Verify installation failed
        assert isinstance(result, Failure), \
            "Expected installation to fail due to validation error"
        
        # Verify no files were installed (atomic: validation happens before any copying)
        for i in range(num_files):
            target_file = temp_dirs['target'] / f"file_{i}.conf"
            assert not target_file.exists(), \
                f"File {i} should not exist after validation failure"
        
        # Verify existing files are untouched
        assert existing_file.exists(), \
            "Existing file should not be affected by failed installation"
        assert existing_file.read_text() == existing_content, \
            "Existing file content should not be modified"
    
    finally:
        cleanup_temp_dirs(temp_dirs)


@settings(max_examples=100)
@given(
    num_files=st.integers(min_value=1, max_value=10)
)
def test_property_uninstall_inverse(num_files):
    """
    **Feature: injekt-cli, Property 11: Uninstall inverse**
    **Validates: Requirements 11.1, 11.3**
    
    Property: For any package, installing and then uninstalling should remove all files
    that were installed (excluding user-created files).
    
    This test verifies that:
    1. When a package is installed
    2. And then the same package is uninstalled
    3. Then all files that were installed by the package are removed
    4. And no files from the package remain in the target directory
    5. And user-created files (not part of the package) are preserved
    """
    temp_dirs = create_temp_dirs()
    try:
        installer = create_installer(temp_dirs)
        
        # Create a user-created file that should be preserved
        user_file = temp_dirs['target'] / "user_created.conf"
        user_file.write_text("# User created file\n")
        user_file_content = user_file.read_text()
        
        # Create package with multiple files
        package_files = []
        for i in range(num_files):
            source_path = temp_dirs['source'] / f"config_{i}.conf"
            source_path.write_text(f"# Config {i}\nvo=gpu\n")
            
            package_file = PackageFile(
                source_path=source_path,
                target_path=Path(f"package_file_{i}.conf"),
                file_type=FileType.CONFIG,
                required=True
            )
            package_files.append(package_file)
        
        package = Package(
            name="uninstall-test-package",
            description="Test uninstall inverse",
            player=PlayerType.MPV,
            version="1.0.0",
            files=package_files,
            dependencies=[],
            profile=ProfileType.DEFAULT
        )
        
        # Step 1: Install the package
        install_result = installer.install_package(package, temp_dirs['target'], dry_run=False)
        assert isinstance(install_result, Success), \
            f"Installation should succeed, but got: {install_result}"
        
        # Verify all package files were installed
        for i in range(num_files):
            package_file_path = temp_dirs['target'] / f"package_file_{i}.conf"
            assert package_file_path.exists(), \
                f"Package file {i} should exist after installation"
        
        # Verify user file still exists
        assert user_file.exists(), \
            "User-created file should not be affected by installation"
        
        # Step 2: Uninstall the package
        uninstall_result = installer.uninstall_package("uninstall-test-package", dry_run=False)
        assert isinstance(uninstall_result, Success), \
            f"Uninstallation should succeed, but got: {uninstall_result}"
        
        # Step 3: Verify all package files were removed
        for i in range(num_files):
            package_file_path = temp_dirs['target'] / f"package_file_{i}.conf"
            assert not package_file_path.exists(), \
                f"Package file {i} should be removed after uninstallation"
        
        # Step 4: Verify user-created file is preserved
        assert user_file.exists(), \
            "User-created file should be preserved after uninstallation"
        assert user_file.read_text() == user_file_content, \
            "User-created file content should not be modified"
        
        # Step 5: Verify package is no longer in state file
        config_parser = ConfigParser()
        state_result = config_parser.parse_installation_state(temp_dirs['state'])
        
        if isinstance(state_result, Success):
            installations = state_result.value
            package_names = [inst.package.name for inst in installations]
            assert "uninstall-test-package" not in package_names, \
                "Uninstalled package should not be in state file"
    
    finally:
        cleanup_temp_dirs(temp_dirs)

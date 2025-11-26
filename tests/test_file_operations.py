"""Property-based tests for file operations.

Feature: injekt-cli, Property 13: Dry-run immutability
Validates: Requirements 14.4
"""

import tempfile
import shutil
from pathlib import Path
from hypothesis import given, strategies as st, settings

from injekt.io.file_operations import FileOperations


def get_directory_state(directory: Path) -> set:
    """Get the state of a directory as a set of relative paths."""
    if not directory.exists():
        return set()
    
    files = set()
    for item in directory.rglob("*"):
        if item.is_file():
            files.add(item.relative_to(directory))
    return files


@given(
    filename=st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        whitelist_characters='_-.'
    )).filter(lambda x: x not in ('.', '..')),
    content=st.binary(min_size=0, max_size=1000)
)
@settings(max_examples=100)
def test_dry_run_copy_immutability(filename, content):
    """
    Feature: injekt-cli, Property 13: Dry-run immutability
    Validates: Requirements 14.4
    
    For any file copy operation in dry-run mode, no files on disk should be modified.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        source_dir = tmpdir_path / "source"
        dest_dir = tmpdir_path / "dest"
        source_dir.mkdir()
        dest_dir.mkdir()
        
        # Create source file
        source_file = source_dir / filename
        source_file.write_bytes(content)
        
        # Get initial state
        initial_state = get_directory_state(tmpdir_path)
        
        # Perform dry-run copy
        file_ops = FileOperations(dry_run=True)
        dest_file = dest_dir / filename
        file_ops.copy_file(source_file, dest_file)
        
        # Get final state
        final_state = get_directory_state(tmpdir_path)
        
        # Assert no changes
        assert initial_state == final_state, "Dry-run copy modified file system"


@given(
    filename=st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        whitelist_characters='_-.'
    )).filter(lambda x: x not in ('.', '..')),
    content=st.binary(min_size=0, max_size=1000)
)
@settings(max_examples=100)
def test_dry_run_move_immutability(filename, content):
    """
    Feature: injekt-cli, Property 13: Dry-run immutability
    Validates: Requirements 14.4
    
    For any file move operation in dry-run mode, no files on disk should be modified.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        source_dir = tmpdir_path / "source"
        dest_dir = tmpdir_path / "dest"
        source_dir.mkdir()
        dest_dir.mkdir()
        
        # Create source file
        source_file = source_dir / filename
        source_file.write_bytes(content)
        
        # Get initial state
        initial_state = get_directory_state(tmpdir_path)
        
        # Perform dry-run move
        file_ops = FileOperations(dry_run=True)
        dest_file = dest_dir / filename
        file_ops.move_file(source_file, dest_file)
        
        # Get final state
        final_state = get_directory_state(tmpdir_path)
        
        # Assert no changes
        assert initial_state == final_state, "Dry-run move modified file system"


@given(
    filename=st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        whitelist_characters='_-.'
    )).filter(lambda x: x not in ('.', '..')),
    content=st.binary(min_size=0, max_size=1000)
)
@settings(max_examples=100)
def test_dry_run_delete_immutability(filename, content):
    """
    Feature: injekt-cli, Property 13: Dry-run immutability
    Validates: Requirements 14.4
    
    For any file delete operation in dry-run mode, no files on disk should be modified.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create file
        file_path = tmpdir_path / filename
        file_path.write_bytes(content)
        
        # Get initial state
        initial_state = get_directory_state(tmpdir_path)
        
        # Perform dry-run delete
        file_ops = FileOperations(dry_run=True)
        file_ops.delete_file(file_path)
        
        # Get final state
        final_state = get_directory_state(tmpdir_path)
        
        # Assert no changes
        assert initial_state == final_state, "Dry-run delete modified file system"


@given(
    dirname=st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        whitelist_characters='_-'
    ))
)
@settings(max_examples=100)
def test_dry_run_create_directory_immutability(dirname):
    """
    Feature: injekt-cli, Property 13: Dry-run immutability
    Validates: Requirements 14.4
    
    For any directory creation in dry-run mode, no files on disk should be modified.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Get initial state
        initial_state = get_directory_state(tmpdir_path)
        
        # Perform dry-run directory creation
        file_ops = FileOperations(dry_run=True)
        new_dir = tmpdir_path / dirname
        file_ops.create_directory(new_dir)
        
        # Get final state
        final_state = get_directory_state(tmpdir_path)
        
        # Assert no changes
        assert initial_state == final_state, "Dry-run create_directory modified file system"

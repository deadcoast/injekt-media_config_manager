"""File system operations with error handling."""

import shutil
from pathlib import Path
from typing import List, Optional

from injekt.core.errors import InjektError
from injekt.core.result import Result, Success, Failure


class FileOperationError(InjektError):
    """File operation failed."""
    pass


class FileOperations:
    """Handles file system operations with proper error handling."""
    
    def __init__(self, dry_run: bool = False):
        """Initialize file operations.
        
        Args:
            dry_run: If True, simulate operations without modifying files
        """
        self.dry_run = dry_run
    
    def copy_file(self, source: Path, destination: Path) -> Result[Path]:
        """Copy a file from source to destination.
        
        Args:
            source: Source file path
            destination: Destination file path
            
        Returns:
            Result containing destination path on success
        """
        try:
            if not source.exists():
                return Failure(FileOperationError(f"Source file does not exist: {source}"))
            
            if not source.is_file():
                return Failure(FileOperationError(f"Source is not a file: {source}"))
            
            if self.dry_run:
                return Success(destination)
            
            # Create parent directory if it doesn't exist
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(source, destination)
            return Success(destination)
            
        except PermissionError as e:
            return Failure(FileOperationError(f"Permission denied: {e}"))
        except OSError as e:
            return Failure(FileOperationError(f"Failed to copy file: {e}"))
    
    def move_file(self, source: Path, destination: Path) -> Result[Path]:
        """Move a file from source to destination.
        
        Args:
            source: Source file path
            destination: Destination file path
            
        Returns:
            Result containing destination path on success
        """
        try:
            if not source.exists():
                return Failure(FileOperationError(f"Source file does not exist: {source}"))
            
            if not source.is_file():
                return Failure(FileOperationError(f"Source is not a file: {source}"))
            
            if self.dry_run:
                return Success(destination)
            
            # Create parent directory if it doesn't exist
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(source), str(destination))
            return Success(destination)
            
        except PermissionError as e:
            return Failure(FileOperationError(f"Permission denied: {e}"))
        except OSError as e:
            return Failure(FileOperationError(f"Failed to move file: {e}"))
    
    def delete_file(self, path: Path) -> Result[None]:
        """Delete a file.
        
        Args:
            path: File path to delete
            
        Returns:
            Result indicating success or failure
        """
        try:
            if not path.exists():
                return Success(None)
            
            if not path.is_file():
                return Failure(FileOperationError(f"Path is not a file: {path}"))
            
            if self.dry_run:
                return Success(None)
            
            path.unlink()
            return Success(None)
            
        except PermissionError as e:
            return Failure(FileOperationError(f"Permission denied: {e}"))
        except OSError as e:
            return Failure(FileOperationError(f"Failed to delete file: {e}"))
    
    def create_directory(self, path: Path, mode: int = 0o755) -> Result[Path]:
        """Create a directory with specified permissions.
        
        Args:
            path: Directory path to create
            mode: Permission mode (default: 0o755)
            
        Returns:
            Result containing directory path on success
        """
        try:
            if self.dry_run:
                return Success(path)
            
            path.mkdir(parents=True, exist_ok=True, mode=mode)
            return Success(path)
            
        except PermissionError as e:
            return Failure(FileOperationError(f"Permission denied: {e}"))
        except OSError as e:
            return Failure(FileOperationError(f"Failed to create directory: {e}"))
    
    def file_exists(self, path: Path) -> bool:
        """Check if a file exists.
        
        Args:
            path: File path to check
            
        Returns:
            True if file exists, False otherwise
        """
        return path.exists() and path.is_file()
    
    def directory_exists(self, path: Path) -> bool:
        """Check if a directory exists.
        
        Args:
            path: Directory path to check
            
        Returns:
            True if directory exists, False otherwise
        """
        return path.exists() and path.is_dir()
    
    def is_readable(self, path: Path) -> bool:
        """Check if a path is readable.
        
        Args:
            path: Path to check
            
        Returns:
            True if readable, False otherwise
        """
        try:
            return path.exists() and path.stat().st_mode & 0o444
        except (OSError, PermissionError):
            return False
    
    def is_writable(self, path: Path) -> bool:
        """Check if a path is writable.
        
        Args:
            path: Path to check
            
        Returns:
            True if writable, False otherwise
        """
        try:
            if path.exists():
                return path.stat().st_mode & 0o222
            else:
                # Check if parent directory is writable
                return path.parent.exists() and path.parent.stat().st_mode & 0o222
        except (OSError, PermissionError):
            return False
    
    def copy_directory(self, source: Path, destination: Path) -> Result[Path]:
        """Copy a directory recursively.
        
        Args:
            source: Source directory path
            destination: Destination directory path
            
        Returns:
            Result containing destination path on success
        """
        try:
            if not source.exists():
                return Failure(FileOperationError(f"Source directory does not exist: {source}"))
            
            if not source.is_dir():
                return Failure(FileOperationError(f"Source is not a directory: {source}"))
            
            if self.dry_run:
                return Success(destination)
            
            shutil.copytree(source, destination, dirs_exist_ok=True)
            return Success(destination)
            
        except PermissionError as e:
            return Failure(FileOperationError(f"Permission denied: {e}"))
        except OSError as e:
            return Failure(FileOperationError(f"Failed to copy directory: {e}"))
    
    def delete_directory(self, path: Path, recursive: bool = False) -> Result[None]:
        """Delete a directory.
        
        Args:
            path: Directory path to delete
            recursive: If True, delete non-empty directories
            
        Returns:
            Result indicating success or failure
        """
        try:
            if not path.exists():
                return Success(None)
            
            if not path.is_dir():
                return Failure(FileOperationError(f"Path is not a directory: {path}"))
            
            if self.dry_run:
                return Success(None)
            
            if recursive:
                shutil.rmtree(path)
            else:
                path.rmdir()
            
            return Success(None)
            
        except PermissionError as e:
            return Failure(FileOperationError(f"Permission denied: {e}"))
        except OSError as e:
            return Failure(FileOperationError(f"Failed to delete directory: {e}"))
    
    def list_files(self, directory: Path, pattern: str = "*") -> Result[List[Path]]:
        """List files in a directory matching a pattern.
        
        Args:
            directory: Directory to list files from
            pattern: Glob pattern to match (default: "*")
            
        Returns:
            Result containing list of file paths
        """
        try:
            if not directory.exists():
                return Failure(FileOperationError(f"Directory does not exist: {directory}"))
            
            if not directory.is_dir():
                return Failure(FileOperationError(f"Path is not a directory: {directory}"))
            
            files = [f for f in directory.glob(pattern) if f.is_file()]
            return Success(files)
            
        except PermissionError as e:
            return Failure(FileOperationError(f"Permission denied: {e}"))
        except OSError as e:
            return Failure(FileOperationError(f"Failed to list files: {e}"))

"""Backup storage and management."""

import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from injekt.core.models import Backup, Package
from injekt.core.errors import BackupError
from injekt.core.result import Result, Success, Failure
from injekt.io.config_parser import ConfigParser


class BackupStorage:
    """Manages backup creation, storage, and retrieval."""
    
    def __init__(self, backup_root: Path):
        """Initialize backup storage.
        
        Args:
            backup_root: Root directory for storing backups
        """
        self.backup_root = backup_root
        self.parser = ConfigParser()
    
    def create_backup(
        self,
        package_name: str,
        source_files: List[Path],
        source_dir: Path,
        target_dir: Optional[Path] = None
    ) -> Result[Backup]:
        """Create a backup of files.
        
        Args:
            package_name: Name of the package being backed up
            source_files: List of files to backup
            source_dir: Base directory containing the files
            target_dir: Optional target directory for restoration
            
        Returns:
            Result containing Backup object
        """
        try:
            # Create backup ID with timestamp (including microseconds for uniqueness)
            timestamp = datetime.now()
            backup_id = f"{package_name}_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}"
            
            # Create backup directory
            backup_dir = self.backup_root / backup_id
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy files to backup
            backed_up_files = []
            for file_path in source_files:
                if not file_path.exists():
                    continue
                
                # Calculate relative path from source_dir
                try:
                    rel_path = file_path.relative_to(source_dir)
                except ValueError:
                    # File is not relative to source_dir, use just the name
                    rel_path = file_path.name
                
                # Create destination path
                dest_path = backup_dir / rel_path
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file
                shutil.copy2(file_path, dest_path)
                backed_up_files.append(rel_path)
            
            # Create backup object
            backup = Backup(
                backup_id=backup_id,
                timestamp=timestamp,
                package_name=package_name,
                backup_dir=backup_dir,
                files=backed_up_files,
                target_dir=target_dir or source_dir
            )
            
            # Write metadata
            metadata_path = backup_dir / "metadata.json"
            write_result = self.parser.write_backup_metadata(metadata_path, backup)
            if isinstance(write_result, Failure):
                return write_result
            
            return Success(backup)
            
        except Exception as e:
            return Failure(BackupError(f"Failed to create backup: {e}"))
    
    def list_backups(self, package_name: Optional[str] = None) -> Result[List[Backup]]:
        """List all available backups.
        
        Args:
            package_name: Optional filter by package name
            
        Returns:
            Result containing list of Backup objects
        """
        try:
            if not self.backup_root.exists():
                return Success([])
            
            backups = []
            
            # Iterate through backup directories
            for backup_dir in self.backup_root.iterdir():
                if not backup_dir.is_dir():
                    continue
                
                # Check if metadata exists
                metadata_path = backup_dir / "metadata.json"
                if not metadata_path.exists():
                    continue
                
                # Parse metadata
                result = self.parser.parse_backup_metadata(metadata_path)
                if isinstance(result, Failure):
                    continue
                
                backup = result.value
                
                # Filter by package name if specified
                if package_name and backup.package_name != package_name:
                    continue
                
                backups.append(backup)
            
            # Sort by timestamp (newest first)
            backups.sort(key=lambda b: b.timestamp, reverse=True)
            
            return Success(backups)
            
        except Exception as e:
            return Failure(BackupError(f"Failed to list backups: {e}"))
    
    def get_backup(self, backup_id: str) -> Result[Backup]:
        """Get a specific backup by ID.
        
        Args:
            backup_id: The backup ID
            
        Returns:
            Result containing Backup object
        """
        try:
            backup_dir = self.backup_root / backup_id
            
            if not backup_dir.exists():
                return Failure(BackupError(f"Backup does not exist: {backup_id}"))
            
            metadata_path = backup_dir / "metadata.json"
            return self.parser.parse_backup_metadata(metadata_path)
            
        except Exception as e:
            return Failure(BackupError(f"Failed to get backup: {e}"))
    
    def restore_backup(self, backup_id: str, target_dir: Path) -> Result[List[Path]]:
        """Restore files from a backup.
        
        Args:
            backup_id: The backup ID to restore
            target_dir: Directory to restore files to
            
        Returns:
            Result containing list of restored file paths
        """
        try:
            # Get backup
            backup_result = self.get_backup(backup_id)
            if isinstance(backup_result, Failure):
                return backup_result
            
            backup = backup_result.value
            
            # Restore files
            restored_files = []
            for rel_path in backup.files:
                source_path = backup.backup_dir / rel_path
                dest_path = target_dir / rel_path
                
                if not source_path.exists():
                    continue
                
                # Create parent directory
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file
                shutil.copy2(source_path, dest_path)
                restored_files.append(dest_path)
            
            return Success(restored_files)
            
        except Exception as e:
            return Failure(BackupError(f"Failed to restore backup: {e}"))
    
    def delete_backup(self, backup_id: str) -> Result[None]:
        """Delete a backup.
        
        Args:
            backup_id: The backup ID to delete
            
        Returns:
            Result indicating success or failure
        """
        try:
            backup_dir = self.backup_root / backup_id
            
            if not backup_dir.exists():
                return Success(None)
            
            shutil.rmtree(backup_dir)
            return Success(None)
            
        except Exception as e:
            return Failure(BackupError(f"Failed to delete backup: {e}"))
    
    def cleanup_old_backups(
        self,
        package_name: Optional[str] = None,
        keep_count: int = 5
    ) -> Result[int]:
        """Remove old backups, keeping only the most recent.
        
        Args:
            package_name: Optional filter by package name
            keep_count: Number of backups to keep (default: 5)
            
        Returns:
            Result containing number of backups deleted
        """
        try:
            # List backups
            list_result = self.list_backups(package_name)
            if isinstance(list_result, Failure):
                return list_result
            
            backups = list_result.value
            
            # If we have fewer backups than keep_count, nothing to do
            if len(backups) <= keep_count:
                return Success(0)
            
            # Delete old backups
            backups_to_delete = backups[keep_count:]
            deleted_count = 0
            
            for backup in backups_to_delete:
                delete_result = self.delete_backup(backup.backup_id)
                if isinstance(delete_result, Success):
                    deleted_count += 1
            
            return Success(deleted_count)
            
        except Exception as e:
            return Failure(BackupError(f"Failed to cleanup old backups: {e}"))

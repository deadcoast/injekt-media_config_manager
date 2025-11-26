"""Backup manager implementation for managing configuration backups."""

from pathlib import Path
from typing import List

from injekt.core.interfaces import BackupManager as BackupManagerInterface
from injekt.core.models import Package, Backup
from injekt.core.result import Result, Success, Failure
from injekt.core.errors import BackupError
from injekt.io.backup_storage import BackupStorage


class BackupManager(BackupManagerInterface):
    """Manages backup operations for configuration packages."""
    
    def __init__(self, backup_storage: BackupStorage):
        """Initialize the backup manager.
        
        Args:
            backup_storage: Storage backend for backups
        """
        self.backup_storage = backup_storage
    
    def create_backup(self, package: Package, target_dir: Path) -> Result[Backup]:
        """Create a backup of current configuration.
        
        Args:
            package: Package being backed up
            target_dir: Directory containing files to backup
            
        Returns:
            Result containing Backup object or error
        """
        try:
            # Collect files that exist in target directory
            files_to_backup = []
            
            for package_file in package.files:
                target_path = target_dir / package_file.target_path
                if target_path.exists():
                    files_to_backup.append(target_path)
            
            # If no files exist, still create backup (empty backup is valid)
            return self.backup_storage.create_backup(
                package_name=package.name,
                source_files=files_to_backup,
                source_dir=target_dir,
                target_dir=target_dir
            )
            
        except Exception as e:
            return Failure(BackupError(f"Failed to create backup: {e}"))
    
    def list_backups(self) -> Result[List[Backup]]:
        """List all available backups.
        
        Returns:
            Result containing list of Backup objects or error
        """
        return self.backup_storage.list_backups()
    
    def restore_backup(self, backup_id: str) -> Result[None]:
        """Restore a backup.
        
        Args:
            backup_id: ID of the backup to restore
            
        Returns:
            Result indicating success or error
        """
        try:
            # Get the backup to find its target directory
            backup_result = self.backup_storage.get_backup(backup_id)
            if isinstance(backup_result, Failure):
                return backup_result
            
            backup = backup_result.value
            
            # Check if target directory is available
            if not backup.target_dir:
                return Failure(BackupError(
                    "Backup does not contain target directory information"
                ))
            
            # Restore the backup
            restore_result = self.backup_storage.restore_backup(
                backup_id,
                backup.target_dir
            )
            
            if isinstance(restore_result, Failure):
                return restore_result
            
            return Success(None)
            
        except Exception as e:
            return Failure(BackupError(f"Failed to restore backup: {e}"))
    
    def cleanup_old_backups(self, keep_count: int = 5) -> Result[int]:
        """Remove old backups, keeping only the most recent.
        
        Args:
            keep_count: Number of backups to keep (default: 5)
            
        Returns:
            Result containing number of backups deleted or error
        """
        return self.backup_storage.cleanup_old_backups(
            package_name=None,
            keep_count=keep_count
        )

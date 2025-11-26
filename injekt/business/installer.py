"""Installer implementation for managing package installations."""

from pathlib import Path
from typing import List
from datetime import datetime

from injekt.core.interfaces import Installer as InstallerInterface
from injekt.core.models import Package, InstallationState
from injekt.core.result import Result, Success, Failure
from injekt.core.errors import InstallationError, ConflictError, ValidationError
from injekt.io.file_operations import FileOperations
from injekt.io.config_parser import ConfigParser
from injekt.business.backup_manager import BackupManager
from injekt.business.validator import ConfigValidatorImpl


class Installer(InstallerInterface):
    """Manages package installation, uninstallation, and verification."""
    
    def __init__(
        self,
        file_ops: FileOperations,
        backup_manager: BackupManager,
        validator: ConfigValidatorImpl,
        config_parser: ConfigParser,
        state_file: Path
    ):
        """Initialize the installer.
        
        Args:
            file_ops: File operations handler
            backup_manager: Backup manager for creating backups
            validator: Configuration validator
            config_parser: Configuration parser
            state_file: Path to installation state file
        """
        self.file_ops = file_ops
        self.backup_manager = backup_manager
        self.validator = validator
        self.config_parser = config_parser
        self.state_file = state_file
    
    def install_package(
        self,
        package: Package,
        target_dir: Path,
        dry_run: bool = False
    ) -> Result[InstallationState]:
        """Install a configuration package.
        
        Args:
            package: Package to install
            target_dir: Target directory for installation
            dry_run: If True, simulate without making changes
            
        Returns:
            Result containing InstallationState or error
        """
        try:
            # Set dry-run mode
            original_dry_run = self.file_ops.dry_run
            self.file_ops.dry_run = dry_run
            
            # Step 1: Validate all package files
            validation_result = self._validate_package_files(package)
            if isinstance(validation_result, Failure):
                self.file_ops.dry_run = original_dry_run
                return validation_result
            
            # Step 2: Check for file conflicts
            conflicts = self._detect_conflicts(package, target_dir)
            if conflicts:
                self.file_ops.dry_run = original_dry_run
                conflict_list = "\n".join(str(c) for c in conflicts)
                return Failure(ConflictError(
                    f"File conflicts detected:\n{conflict_list}"
                ))
            
            # Step 3: Create backup (if not dry-run)
            backup_dir = None
            if not dry_run:
                backup_result = self.backup_manager.create_backup(package, target_dir)
                if isinstance(backup_result, Failure):
                    self.file_ops.dry_run = original_dry_run
                    return backup_result
                backup_dir = backup_result.value.backup_dir
            
            # Step 4: Install files
            installed_files = []
            try:
                for package_file in package.files:
                    # Skip non-required files if source doesn't exist
                    if not package_file.required and not package_file.source_path.exists():
                        continue
                    
                    dest_path = target_dir / package_file.target_path
                    
                    copy_result = self.file_ops.copy_file(
                        package_file.source_path,
                        dest_path
                    )
                    
                    if isinstance(copy_result, Failure):
                        # Rollback on failure
                        if not dry_run:
                            self._rollback_installation(installed_files)
                        self.file_ops.dry_run = original_dry_run
                        return copy_result
                    
                    installed_files.append(dest_path)
            
            except Exception as e:
                # Rollback on any exception
                if not dry_run:
                    self._rollback_installation(installed_files)
                self.file_ops.dry_run = original_dry_run
                return Failure(InstallationError(f"Installation failed: {e}"))
            
            # Step 5: Create installation state
            installation_state = InstallationState(
                package=package,
                target_dir=target_dir,
                backup_dir=backup_dir,
                installed_files=installed_files,
                timestamp=datetime.now()
            )
            
            # Step 6: Update state file (if not dry-run)
            if not dry_run:
                update_result = self._update_state_file(installation_state)
                if isinstance(update_result, Failure):
                    self._rollback_installation(installed_files)
                    self.file_ops.dry_run = original_dry_run
                    return update_result
            
            self.file_ops.dry_run = original_dry_run
            return Success(installation_state)
            
        except Exception as e:
            self.file_ops.dry_run = original_dry_run
            return Failure(InstallationError(f"Installation failed: {e}"))
    
    def uninstall_package(
        self,
        package_name: str,
        dry_run: bool = False
    ) -> Result[List[Path]]:
        """Uninstall a configuration package.
        
        Args:
            package_name: Name of package to uninstall
            dry_run: If True, simulate without making changes
            
        Returns:
            Result containing list of removed file paths or error
        """
        try:
            # Set dry-run mode
            original_dry_run = self.file_ops.dry_run
            self.file_ops.dry_run = dry_run
            
            # Get installation state
            state_result = self.config_parser.parse_installation_state(self.state_file)
            if isinstance(state_result, Failure):
                self.file_ops.dry_run = original_dry_run
                return state_result
            
            # Find the installation
            installation = None
            for inst in state_result.value:
                if inst.package.name == package_name:
                    installation = inst
                    break
            
            if not installation:
                self.file_ops.dry_run = original_dry_run
                return Failure(InstallationError(
                    f"Package not installed: {package_name}"
                ))
            
            # Create backup before uninstall (if not dry-run)
            if not dry_run:
                backup_result = self.backup_manager.create_backup(
                    installation.package,
                    installation.target_dir
                )
                if isinstance(backup_result, Failure):
                    self.file_ops.dry_run = original_dry_run
                    return backup_result
            
            # Remove installed files
            removed_files = []
            for file_path in installation.installed_files:
                if file_path.exists():
                    delete_result = self.file_ops.delete_file(file_path)
                    if isinstance(delete_result, Success):
                        removed_files.append(file_path)
            
            # Remove empty directories
            if not dry_run:
                self._remove_empty_directories(installation.target_dir)
            
            # Update state file (if not dry-run)
            if not dry_run:
                remaining_installations = [
                    inst for inst in state_result.value
                    if inst.package.name != package_name
                ]
                write_result = self.config_parser.write_installation_state(
                    self.state_file,
                    remaining_installations
                )
                if isinstance(write_result, Failure):
                    self.file_ops.dry_run = original_dry_run
                    return write_result
            
            self.file_ops.dry_run = original_dry_run
            return Success(removed_files)
            
        except Exception as e:
            self.file_ops.dry_run = original_dry_run
            return Failure(InstallationError(f"Uninstallation failed: {e}"))
    
    def verify_installation(self, package: Package) -> Result[List[str]]:
        """Verify package installation.
        
        Args:
            package: Package to verify
            
        Returns:
            Result containing list of issues (empty if all OK) or error
        """
        try:
            # Get installation state
            state_result = self.config_parser.parse_installation_state(self.state_file)
            if isinstance(state_result, Failure):
                return state_result
            
            # Find the installation
            installation = None
            for inst in state_result.value:
                if inst.package.name == package.name:
                    installation = inst
                    break
            
            if not installation:
                return Success([f"Package not installed: {package.name}"])
            
            issues = []
            
            # Check all required files exist
            for package_file in package.files:
                if not package_file.required:
                    continue
                
                file_path = installation.target_dir / package_file.target_path
                
                if not file_path.exists():
                    issues.append(f"Missing required file: {file_path}")
                elif not self.file_ops.is_readable(file_path):
                    issues.append(f"File not readable: {file_path}")
            
            return Success(issues)
            
        except Exception as e:
            return Failure(InstallationError(f"Verification failed: {e}"))
    
    def _validate_package_files(self, package: Package) -> Result[None]:
        """Validate all package files before installation.
        
        Args:
            package: Package to validate
            
        Returns:
            Result indicating success or validation error
        """
        for package_file in package.files:
            # Skip validation for non-required files that don't exist
            if not package_file.required and not package_file.source_path.exists():
                continue
            
            # Check source file exists
            if not package_file.source_path.exists():
                return Failure(ValidationError(
                    f"Source file does not exist: {package_file.source_path}"
                ))
            
            # Validate based on file type
            validation_result = self.validator.validate_file_by_type(
                package_file.source_path,
                package_file.file_type,
                package.player
            )
            
            if isinstance(validation_result, Failure):
                return validation_result
        
        return Success(None)
    
    def _detect_conflicts(self, package: Package, target_dir: Path) -> List[Path]:
        """Detect file conflicts before installation.
        
        Args:
            package: Package to check
            target_dir: Target installation directory
            
        Returns:
            List of conflicting file paths
        """
        conflicts = []
        
        for package_file in package.files:
            dest_path = target_dir / package_file.target_path
            
            # Check if file already exists
            if dest_path.exists():
                # Check if it's from a different package
                # For now, we'll consider any existing file a conflict
                # In a real implementation, we'd check the installation state
                conflicts.append(dest_path)
        
        return conflicts
    
    def _rollback_installation(self, installed_files: List[Path]) -> None:
        """Rollback installation by removing installed files.
        
        Args:
            installed_files: List of files that were installed
        """
        for file_path in installed_files:
            try:
                if file_path.exists():
                    self.file_ops.delete_file(file_path)
            except Exception:
                # Best effort rollback
                pass
    
    def _remove_empty_directories(self, base_dir: Path) -> None:
        """Remove empty directories under base directory.
        
        Args:
            base_dir: Base directory to check
        """
        try:
            for dirpath in sorted(base_dir.rglob("*"), reverse=True):
                if dirpath.is_dir() and not any(dirpath.iterdir()):
                    try:
                        dirpath.rmdir()
                    except Exception:
                        # Ignore errors
                        pass
        except Exception:
            # Ignore errors
            pass
    
    def _update_state_file(self, installation: InstallationState) -> Result[None]:
        """Update installation state file.
        
        Args:
            installation: Installation state to add
            
        Returns:
            Result indicating success or error
        """
        # Read current state
        state_result = self.config_parser.parse_installation_state(self.state_file)
        if isinstance(state_result, Failure):
            # If file doesn't exist, start with empty list
            installations = []
        else:
            installations = state_result.value
        
        # Remove any existing installation of the same package
        installations = [
            inst for inst in installations
            if inst.package.name != installation.package.name
        ]
        
        # Add new installation
        installations.append(installation)
        
        # Write state
        return self.config_parser.write_installation_state(
            self.state_file,
            installations
        )

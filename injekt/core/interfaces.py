"""Protocol definitions for business logic interfaces."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from .models import Package, PlayerType, InstallationState, Backup
from .result import Result


class PackageRepository(ABC):
    """Interface for package storage and retrieval."""
    
    @abstractmethod
    def list_packages(self) -> Result[List[Package]]:
        """List all available packages."""
        ...
    
    @abstractmethod
    def get_package(self, name: str) -> Result[Package]:
        """Get a specific package by name."""
        ...
    
    @abstractmethod
    def get_installed_packages(self) -> Result[List[Package]]:
        """Get list of installed packages."""
        ...


class PathResolver(ABC):
    """Interface for resolving installation paths."""
    
    @abstractmethod
    def detect_player_directory(self, player: PlayerType) -> Result[Path]:
        """Detect installation directory for a player."""
        ...
    
    @abstractmethod
    def get_config_directory(self, player: PlayerType) -> Result[Path]:
        """Get configuration directory for a player."""
        ...
    
    @abstractmethod
    def normalize_path(self, path: Path) -> Path:
        """Normalize a path for the current platform."""
        ...


class ConfigValidator(ABC):
    """Interface for configuration validation."""
    
    @abstractmethod
    def validate_config_file(self, path: Path, player: PlayerType) -> Result[None]:
        """Validate a configuration file."""
        ...
    
    @abstractmethod
    def validate_plugin(self, path: Path) -> Result[None]:
        """Validate a plugin file."""
        ...
    
    @abstractmethod
    def validate_shader(self, path: Path) -> Result[None]:
        """Validate a shader file."""
        ...


class BackupManager(ABC):
    """Interface for backup operations."""
    
    @abstractmethod
    def create_backup(self, package: Package, target_dir: Path) -> Result[Backup]:
        """Create a backup of current configuration."""
        ...
    
    @abstractmethod
    def list_backups(self) -> Result[List[Backup]]:
        """List all available backups."""
        ...
    
    @abstractmethod
    def restore_backup(self, backup_id: str) -> Result[None]:
        """Restore a backup."""
        ...
    
    @abstractmethod
    def cleanup_old_backups(self, keep_count: int = 5) -> Result[int]:
        """Remove old backups, keeping only the most recent."""
        ...


class Installer(ABC):
    """Interface for installation operations."""
    
    @abstractmethod
    def install_package(
        self,
        package: Package,
        target_dir: Path,
        dry_run: bool = False
    ) -> Result[InstallationState]:
        """Install a configuration package."""
        ...
    
    @abstractmethod
    def uninstall_package(
        self,
        package_name: str,
        dry_run: bool = False
    ) -> Result[List[Path]]:
        """Uninstall a configuration package."""
        ...
    
    @abstractmethod
    def verify_installation(self, package: Package) -> Result[List[str]]:
        """Verify package installation."""
        ...

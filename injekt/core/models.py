"""Core domain models and enums."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional


class PlayerType(Enum):
    """Supported media players."""
    MPV = "mpv"
    VLC = "vlc"


class ProfileType(Enum):
    """Configuration profiles."""
    PERFORMANCE = "performance"
    QUALITY = "quality"
    CINEMATIC = "cinematic"
    DEFAULT = "default"


class FileType(Enum):
    """Types of configuration files."""
    CONFIG = "config"
    PLUGIN_LUA = "plugin_lua"
    PLUGIN_JS = "plugin_js"
    SHADER = "shader"
    SCRIPT_OPT = "script_opt"


@dataclass(frozen=True)
class PackageFile:
    """Represents a file in a configuration package."""
    source_path: Path
    target_path: Path
    file_type: FileType
    required: bool = True


@dataclass(frozen=True)
class Package:
    """Represents a configuration package."""
    name: str
    description: str
    player: PlayerType
    version: str
    files: List[PackageFile]
    dependencies: List[str]
    profile: ProfileType
    
    def get_files_by_type(self, file_type: FileType) -> List[PackageFile]:
        """Get all files of a specific type."""
        return [f for f in self.files if f.file_type == file_type]


@dataclass
class InstallationState:
    """Tracks installation state."""
    package: Package
    target_dir: Path
    backup_dir: Optional[Path]
    installed_files: List[Path]
    timestamp: datetime


@dataclass
class Backup:
    """Represents a configuration backup."""
    backup_id: str
    timestamp: datetime
    package_name: str
    backup_dir: Path
    files: List[Path]
    target_dir: Optional[Path] = None  # Directory where files should be restored

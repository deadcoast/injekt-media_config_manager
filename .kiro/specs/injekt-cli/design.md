# Design Document: Injekt CLI - Video Media Config Manager

## Overview

Injekt is a professional command-line application for managing video media player configurations. It follows the standardized CLI architecture template with clear separation between CLI, business logic, and I/O layers.

### Core Principles

1. **Safety First** - All operations create backups before modifications
2. **Validation Early** - Validate configurations before installation
3. **Clear Feedback** - Provide detailed progress and error information
4. **Idempotent Operations** - Running the same operation twice produces the same result
5. **Atomic Operations** - Operations either complete fully or rollback completely

### Key Features

- Install and manage MPV and VLC configurations
- Plugin and shader management
- Configuration profiles (performance, quality, cinematic)
- Backup and rollback capabilities
- Dry-run mode for safe previews
- Interactive and automated modes
- Configuration validation and verification
- Import/export configurations

## Architecture

### Layered Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     CLI Layer                           │
│  - Command handlers (install, list, rollback, etc.)     │
│  - Input validation and prompts                         │
│  - Output formatting (text, JSON, table)                │
│  - Interactive mode                                     │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                  Business Logic Layer                   │
│  - Package management                                   │
│  - Installation orchestration                           │
│  - Backup/rollback management                           │
│  - Configuration validation                             │
│  - Profile management                                   │
│  - Dependency resolution                                │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                      I/O Layer                          │
│  - File system operations                               │
│  - Configuration file parsing                           │
│  - Path detection and resolution                        │
│  - Backup storage                                       │
└─────────────────────────────────────────────────────────┘
```

### Module Structure

```
injekt/
├── core/
│   ├── __init__.py
│   ├── interfaces.py      # Protocol definitions
│   ├── result.py          # Result types
│   ├── validation.py      # Input validation
│   ├── errors.py          # Exception hierarchy
│   └── constants.py       # Named constants
├── io/
│   ├── __init__.py
│   ├── file_operations.py # File system operations
│   ├── config_parser.py   # Config file parsing
│   ├── path_resolver.py   # Path detection
│   └── backup_storage.py  # Backup management
├── business/
│   ├── __init__.py
│   ├── package_manager.py # Package operations
│   ├── installer.py       # Installation logic
│   ├── validator.py       # Config validation
│   ├── profile_manager.py # Profile management
│   └── dependency_resolver.py # Dependency resolution
├── cli/
│   ├── __init__.py
│   ├── commands.py        # Command handlers
│   ├── output.py          # Output formatting
│   ├── input.py           # Input handling
│   └── app.py             # CLI framework (Typer)
└── config.py              # Configuration management
```

## Components and Interfaces

### Core Domain Models

```python
# injekt/core/models.py

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Dict, Optional

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
```

### Business Logic Interfaces

```python
# injekt/core/interfaces.py

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
```

## Data Models

### Package Manifest Format

Packages are defined using JSON manifest files:

```json
{
  "name": "mpv-ultra-5090",
  "description": "Optimized MPV configuration for RTX 5090 + QD-OLED",
  "player": "mpv",
  "version": "0.0.2",
  "profile": "quality",
  "dependencies": [],
  "files": [
    {
      "source": "mpv.conf",
      "target": "mpv.conf",
      "type": "config",
      "required": true
    },
    {
      "source": "input.conf",
      "target": "input.conf",
      "type": "config",
      "required": true
    },
    {
      "source": "shaders/fsr2.glsl",
      "target": "shaders/fsr2.glsl",
      "type": "shader",
      "required": false
    },
    {
      "source": "scripts/rtx-vsr-toggle.lua",
      "target": "scripts/rtx-vsr-toggle.lua",
      "type": "plugin_lua",
      "required": false
    }
  ]
}
```

### Installation State Tracking

Installation state is persisted to track what's installed:

```json
{
  "installations": [
    {
      "package_name": "mpv-ultra-5090",
      "version": "0.0.2",
      "installed_at": "2025-11-26T10:30:00Z",
      "target_dir": "C:\\Users\\ryanf\\AppData\\Roaming\\mpv",
      "files": [
        "mpv.conf",
        "input.conf",
        "shaders/fsr2.glsl",
        "scripts/rtx-vsr-toggle.lua"
      ]
    }
  ]
}
```

### Backup Metadata

Backups include metadata for easy restoration:

```json
{
  "backup_id": "mpv-ultra-5090_20251126_103000",
  "package_name": "mpv-ultra-5090",
  "timestamp": "2025-11-26T10:30:00Z",
  "backup_dir": "C:\\Users\\ryanf\\.injekt\\backups\\mpv-ultra-5090_20251126_103000",
  "files": [
    "mpv.conf",
    "input.conf"
  ]
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Package Listing Completeness
*For any* set of available packages, listing packages should return all packages with their name, description, player type, and version
**Validates: Requirements 1.1, 1.2, 1.4**

### Property 2: Installation Creates Backup
*For any* package installation where existing configs are present, a backup should be created before any files are modified
**Validates: Requirements 2.4, 5.1, 5.2**

### Property 3: Path Detection Consistency
*For any* player type, detecting the installation directory should check all standard paths for that player
**Validates: Requirements 3.1, 3.2**

### Property 4: Validation Before Installation
*For any* package, installation should only proceed if all required files pass validation
**Validates: Requirements 4.1, 4.2, 4.3, 4.5**

### Property 5: Backup Rotation
*For any* backup operation, when more than 5 backups exist, only the 5 most recent backups should remain
**Validates: Requirements 5.5**

### Property 6: Rollback Round-Trip
*For any* configuration state, creating a backup and then restoring it should result in the same file contents
**Validates: Requirements 6.2**

### Property 7: Plugin Path Routing
*For any* plugin file, installation should place it in the correct subdirectory based on its file type (Lua → scripts/, JS → scripts/, etc.)
**Validates: Requirements 7.1**

### Property 8: Shader Reference Validation
*For any* configuration file that references shaders, all referenced shader files should exist after installation
**Validates: Requirements 8.2**

### Property 9: Profile Backup Safety
*For any* profile switch operation, a backup of the current configuration should be created before applying the new profile
**Validates: Requirements 9.2**

### Property 10: Installation Verification Completeness
*For any* installed package, verification should check that all required files exist and have correct permissions
**Validates: Requirements 10.1, 10.2**

### Property 11: Uninstall Inverse
*For any* package, installing and then uninstalling should remove all files that were installed (excluding user-created files)
**Validates: Requirements 11.1, 11.3**

### Property 12: Conflict Detection
*For any* installation where target files already exist, conflicts should be detected and reported before modification
**Validates: Requirements 13.1**

### Property 13: Dry-Run Immutability
*For any* operation in dry-run mode, no files on disk should be modified
**Validates: Requirements 14.4**

### Property 14: Report Completeness
*For any* installed configuration, generating a report should include all packages, plugins, shaders, and the active profile
**Validates: Requirements 15.1, 15.2, 15.3, 15.4**

### Property 15: Update Preserves Customizations
*For any* package update, user-specific customizations should remain unchanged after the update
**Validates: Requirements 16.4**

### Property 16: Export-Import Round-Trip
*For any* configuration, exporting and then importing should preserve all config files, plugins, and shaders
**Validates: Requirements 18.1, 18.2**

### Property 17: Path Normalization
*For any* Windows path, normalization should convert forward slashes to backslashes and expand environment variables
**Validates: Requirements 23.1, 23.2**

### Property 18: Config Merge Precedence
*For any* configuration merge, settings should follow the precedence order: user > profile > default
**Validates: Requirements 24.2**

### Property 19: Validation Error Reporting
*For any* validation failure, the error report should include the file name and specific error details
**Validates: Requirements 4.4**

### Property 20: Atomic Installation
*For any* installation operation, if any step fails, all changes should be rolled back
**Validates: Requirements 5.3**

## Error Handling

### Error Hierarchy

```python
# injekt/core/errors.py

class InjektError(Exception):
    """Base exception for Injekt CLI."""
    pass

class PackageNotFoundError(InjektError):
    """Package does not exist."""
    pass

class ValidationError(InjektError):
    """Configuration validation failed."""
    pass

class InstallationError(InjektError):
    """Installation operation failed."""
    pass

class BackupError(InjektError):
    """Backup operation failed."""
    pass

class PathResolutionError(InjektError):
    """Path detection or resolution failed."""
    pass

class ConflictError(InjektError):
    """File conflict detected."""
    pass

class DependencyError(InjektError):
    """Dependency resolution failed."""
    pass
```

### Error Recovery Strategy

1. **Validation Errors**: Report and abort before making changes
2. **Installation Errors**: Rollback partial changes, restore from backup
3. **Backup Errors**: Abort operation, do not proceed without backup
4. **Path Errors**: Prompt user for manual path or offer to create
5. **Conflict Errors**: Offer resolution options (skip, overwrite, abort)

## Testing Strategy

### Unit Testing

Unit tests will cover:
- Package parsing and validation
- Path resolution logic
- Configuration file validation
- Backup creation and restoration
- File conflict detection
- Profile management

### Property-Based Testing

Property-based tests will use **Hypothesis** (Python PBT library) to verify:
- Correctness properties defined above
- Edge cases with random inputs
- Round-trip properties (backup/restore, export/import)
- Invariants (dry-run doesn't modify state)

Each property-based test will:
- Run a minimum of 100 iterations
- Use smart generators for realistic test data
- Be tagged with the property number from this design document
- Use the format: `# Feature: injekt-cli, Property X: <property_text>`

### Integration Testing

Integration tests will verify:
- Complete installation workflows
- Backup and rollback scenarios
- Multi-package installations
- Profile switching
- Interactive mode flows

### Test Data Strategy

Test data will include:
- Sample MPV and VLC configurations
- Valid and invalid config files
- Plugin files with various dependencies
- Shader files with correct and incorrect syntax
- Package manifests with various configurations

## Performance Considerations

- **Lazy Loading**: Load package manifests only when needed
- **Parallel Operations**: Copy multiple files concurrently where safe
- **Caching**: Cache path detection results
- **Incremental Backups**: Only backup changed files when possible
- **Progress Indicators**: Show progress for long operations

## Security Considerations

- **Path Validation**: Validate all paths to prevent directory traversal
- **Permission Checks**: Verify write permissions before operations
- **Backup Integrity**: Verify backup completeness before proceeding
- **Safe Defaults**: Default to safe options (backup, dry-run)
- **Input Sanitization**: Sanitize all user inputs

## Configuration Management

### Application Configuration

```python
# injekt/config.py

@dataclass
class InjektConfig:
    """Application configuration."""
    assets_dir: Path
    backup_dir: Path
    state_file: Path
    max_backups: int = 5
    default_player: PlayerType = PlayerType.MPV
    verbose: bool = False
    dry_run: bool = False
    output_format: str = "text"
```

### Configuration Locations

- **Assets**: `<project_root>/assets/`
- **Backups**: `~/.injekt/backups/`
- **State**: `~/.injekt/state.json`
- **Logs**: `~/.injekt/logs/`

## CLI Commands

### Command Structure

```
injekt list                          # List available packages
injekt install <package>             # Install a package
injekt uninstall <package>           # Uninstall a package
injekt verify <package>              # Verify installation
injekt rollback                      # Rollback to previous config
injekt profile list                  # List available profiles
injekt profile switch <profile>      # Switch to a profile
injekt backup list                   # List backups
injekt backup create                 # Create manual backup
injekt report                        # Generate configuration report
injekt info <package>                # Show package details
injekt update <package>              # Update a package
injekt export <output_dir>           # Export current config
injekt import <input_dir>            # Import a config
```

### Global Options

- `--verbose, -v`: Enable verbose output
- `--dry-run, -n`: Simulate without making changes
- `--format, -f`: Output format (text, json, table)
- `--player, -p`: Target player (mpv, vlc)
- `--yes, -y`: Auto-confirm prompts

## Implementation Notes

### Phase 1: Core Infrastructure
- Result types and error hierarchy
- File operations and path resolution
- Package manifest parsing
- Basic CLI framework

### Phase 2: Installation Logic
- Package installation
- Backup creation
- Validation logic
- Conflict detection

### Phase 3: Advanced Features
- Rollback functionality
- Profile management
- Plugin and shader handling
- Dependency resolution

### Phase 4: User Experience
- Interactive mode
- Progress indicators
- Rich output formatting
- Comprehensive help

### Phase 5: Testing & Polish
- Property-based tests
- Integration tests
- Documentation
- Error message refinement

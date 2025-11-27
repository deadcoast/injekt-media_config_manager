"""Configuration file parsing for packages, installation state, and backups."""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from injekt.core.models import (
    Package, PackageFile, PlayerType, ProfileType, FileType,
    InstallationState, Backup
)
from injekt.core.errors import ValidationError
from injekt.core.result import Result, Success, Failure


class ConfigParser:
    """Parses configuration files for packages, state, and backups."""
    
    def parse_package_manifest(self, manifest_path: Path) -> Result[Package]:
        """Parse a package manifest JSON file.
        
        Args:
            manifest_path: Path to the manifest.json file
            
        Returns:
            Result containing the parsed Package or error
        """
        try:
            if not manifest_path.exists():
                return Failure(ValidationError(f"Manifest file does not exist: {manifest_path}"))
            
            with open(manifest_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate required fields
            required_fields = ['name', 'description', 'player', 'version', 'files']
            for field in required_fields:
                if field not in data:
                    return Failure(ValidationError(f"Missing required field in manifest: {field}"))
            
            # Parse player type
            try:
                player = PlayerType(data['player'])
            except ValueError:
                return Failure(ValidationError(f"Invalid player type: {data['player']}"))
            
            # Parse profile type
            profile_str = data.get('profile', 'default')
            try:
                profile = ProfileType(profile_str)
            except ValueError:
                return Failure(ValidationError(f"Invalid profile type: {profile_str}"))
            
            # Parse files
            files_result = self._parse_package_files(data['files'], manifest_path.parent)
            if isinstance(files_result, Failure):
                return files_result
            
            package = Package(
                name=data['name'],
                description=data['description'],
                player=player,
                version=data['version'],
                files=files_result.value,
                dependencies=data.get('dependencies', []),
                profile=profile
            )
            
            return Success(package)
            
        except json.JSONDecodeError as e:
            return Failure(ValidationError(f"Invalid JSON in manifest: {e}"))
        except Exception as e:
            return Failure(ValidationError(f"Failed to parse manifest: {e}"))
    
    def _parse_package_files(self, files_data: List[Dict[str, Any]], base_path: Path) -> Result[List[PackageFile]]:
        """Parse package files from manifest data.
        
        Args:
            files_data: List of file dictionaries from manifest
            base_path: Base path for resolving relative paths
            
        Returns:
            Result containing list of PackageFile objects
        """
        try:
            package_files = []
            
            for file_data in files_data:
                # Validate required fields
                if 'source' not in file_data or 'target' not in file_data or 'type' not in file_data:
                    return Failure(ValidationError(f"File entry missing required fields: {file_data}"))
                
                # Parse file type
                try:
                    file_type = FileType(file_data['type'])
                except ValueError:
                    return Failure(ValidationError(f"Invalid file type: {file_data['type']}"))
                
                # Create PackageFile
                package_file = PackageFile(
                    source_path=base_path / file_data['source'],
                    target_path=Path(file_data['target']),
                    file_type=file_type,
                    required=file_data.get('required', True)
                )
                
                package_files.append(package_file)
            
            return Success(package_files)
            
        except Exception as e:
            return Failure(ValidationError(f"Failed to parse package files: {e}"))
    
    def parse_installation_state(self, state_path: Path) -> Result[List[InstallationState]]:
        """Parse installation state from JSON file.
        
        Args:
            state_path: Path to the state.json file
            
        Returns:
            Result containing list of InstallationState objects
        """
        try:
            if not state_path.exists():
                # Empty state is valid
                return Success([])
            
            with open(state_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            installations = []
            
            for install_data in data.get('installations', []):
                # For now, we'll create a minimal Package object
                # In a real implementation, we'd need to reconstruct the full package
                package = Package(
                    name=install_data['package_name'],
                    description="",
                    player=PlayerType.MPV,  # Would need to be stored
                    version=install_data['version'],
                    files=[],
                    dependencies=[],
                    profile=ProfileType.DEFAULT
                )
                
                installation = InstallationState(
                    package=package,
                    target_dir=Path(install_data['target_dir']),
                    backup_dir=Path(install_data['backup_dir']) if install_data.get('backup_dir') else None,
                    installed_files=[Path(f) for f in install_data['files']],
                    timestamp=datetime.fromisoformat(install_data['installed_at'])
                )
                
                installations.append(installation)
            
            return Success(installations)
            
        except json.JSONDecodeError as e:
            return Failure(ValidationError(f"Invalid JSON in state file: {e}"))
        except Exception as e:
            return Failure(ValidationError(f"Failed to parse installation state: {e}"))
    
    def write_installation_state(self, state_path: Path, installations: List[InstallationState]) -> Result[None]:
        """Write installation state to JSON file.
        
        Args:
            state_path: Path to the state.json file
            installations: List of InstallationState objects to write
            
        Returns:
            Result indicating success or failure
        """
        try:
            # Ensure parent directory exists
            state_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'installations': [
                    {
                        'package_name': install.package.name,
                        'version': install.package.version,
                        'installed_at': install.timestamp.isoformat(),
                        'target_dir': str(install.target_dir),
                        'backup_dir': str(install.backup_dir) if install.backup_dir else None,
                        'files': [str(f) for f in install.installed_files]
                    }
                    for install in installations
                ]
            }
            
            with open(state_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            return Success(None)
            
        except Exception as e:
            return Failure(ValidationError(f"Failed to write installation state: {e}"))
    
    def parse_backup_metadata(self, metadata_path: Path) -> Result[Backup]:
        """Parse backup metadata from JSON file.
        
        Args:
            metadata_path: Path to the backup metadata.json file
            
        Returns:
            Result containing Backup object
        """
        try:
            if not metadata_path.exists():
                return Failure(ValidationError(f"Backup metadata does not exist: {metadata_path}"))
            
            with open(metadata_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            backup = Backup(
                backup_id=data['backup_id'],
                timestamp=datetime.fromisoformat(data['timestamp']),
                package_name=data['package_name'],
                backup_dir=Path(data['backup_dir']),
                files=[Path(f) for f in data['files']],
                target_dir=Path(data['target_dir']) if 'target_dir' in data else None
            )
            
            return Success(backup)
            
        except json.JSONDecodeError as e:
            return Failure(ValidationError(f"Invalid JSON in backup metadata: {e}"))
        except Exception as e:
            return Failure(ValidationError(f"Failed to parse backup metadata: {e}"))
    
    def write_backup_metadata(self, metadata_path: Path, backup: Backup) -> Result[None]:
        """Write backup metadata to JSON file.
        
        Args:
            metadata_path: Path to the backup metadata.json file
            backup: Backup object to write
            
        Returns:
            Result indicating success or failure
        """
        try:
            # Ensure parent directory exists
            metadata_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'backup_id': backup.backup_id,
                'timestamp': backup.timestamp.isoformat(),
                'package_name': backup.package_name,
                'backup_dir': str(backup.backup_dir),
                'files': [str(f) for f in backup.files],
                'target_dir': str(backup.target_dir) if backup.target_dir else None
            }
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            return Success(None)
            
        except Exception as e:
            return Failure(ValidationError(f"Failed to write backup metadata: {e}"))

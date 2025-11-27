"""Profile manager implementation for managing configuration profiles."""

from pathlib import Path
from typing import List, Optional

from injekt.core.models import ProfileType, Package, PlayerType
from injekt.core.result import Result, Success, Failure
from injekt.core.errors import InjektError
from injekt.core.interfaces import PackageRepository, BackupManager, Installer


class ProfileError(InjektError):
    """Profile operation failed."""
    pass


class ProfileManager:
    """Manages configuration profiles for media players."""
    
    def __init__(
        self,
        package_repository: PackageRepository,
        backup_manager: BackupManager,
        installer: Installer,
        state_file: Path
    ):
        """Initialize the profile manager.
        
        Args:
            package_repository: Repository for accessing packages
            backup_manager: Manager for backup operations
            installer: Installer for package operations
            state_file: Path to state file for tracking active profile
        """
        self.package_repository = package_repository
        self.backup_manager = backup_manager
        self.installer = installer
        self.state_file = state_file
    
    def list_profiles(self) -> Result[List[ProfileType]]:
        """List all available profiles.
        
        Returns:
            Result containing list of available ProfileType values
        """
        try:
            # Return all profile types
            profiles = list(ProfileType)
            return Success(profiles)
        except Exception as e:
            return Failure(ProfileError(f"Failed to list profiles: {e}"))
    
    def switch_profile(
        self,
        profile: ProfileType,
        player: PlayerType,
        target_dir: Path,
        dry_run: bool = False
    ) -> Result[Package]:
        """Switch to a different configuration profile.
        
        This operation:
        1. Creates a backup of the current configuration
        2. Finds a package matching the requested profile and player
        3. Installs the profile package
        4. Updates the active profile in state
        
        Args:
            profile: Profile to switch to
            player: Player type (MPV, VLC)
            target_dir: Target directory for installation
            dry_run: If True, simulate without making changes
            
        Returns:
            Result containing the installed Package or error
        """
        try:
            # Find a package matching the profile and player
            packages_result = self.package_repository.list_packages()
            if isinstance(packages_result, Failure):
                return packages_result
            
            # Filter packages by profile and player
            matching_packages = [
                pkg for pkg in packages_result.value
                if pkg.profile == profile and pkg.player == player
            ]
            
            if not matching_packages:
                return Failure(ProfileError(
                    f"No package found for profile '{profile.value}' and player '{player.value}'"
                ))
            
            # Use the first matching package
            package = matching_packages[0]
            
            if dry_run:
                # In dry-run mode, just return the package that would be installed
                return Success(package)
            
            # Create backup of current configuration before switching
            backup_result = self.backup_manager.create_backup(package, target_dir)
            if isinstance(backup_result, Failure):
                return Failure(ProfileError(
                    f"Failed to create backup before profile switch: {backup_result.error}"
                ))
            
            # Install the profile package
            install_result = self.installer.install_package(package, target_dir, dry_run=False)
            if isinstance(install_result, Failure):
                return Failure(ProfileError(
                    f"Failed to install profile package: {install_result.error}"
                ))
            
            # Update active profile in state
            update_result = self._update_active_profile(profile, player)
            if isinstance(update_result, Failure):
                # Profile was installed but state update failed - log but don't fail
                # The installation was successful
                pass
            
            return Success(package)
            
        except Exception as e:
            return Failure(ProfileError(f"Failed to switch profile: {e}"))
    
    def get_active_profile(self, player: PlayerType) -> Result[Optional[ProfileType]]:
        """Get the currently active profile for a player.
        
        Args:
            player: Player type to get active profile for
            
        Returns:
            Result containing the active ProfileType or None if not set
        """
        try:
            # Read state file to get active profile
            import json
            
            if not self.state_file.exists():
                # No state file means no active profile
                return Success(None)
            
            with open(self.state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Get active profiles section
            active_profiles = data.get('active_profiles', {})
            profile_str = active_profiles.get(player.value)
            
            if profile_str:
                try:
                    profile = ProfileType(profile_str)
                    return Success(profile)
                except ValueError:
                    return Failure(ProfileError(f"Invalid profile type in state: {profile_str}"))
            
            return Success(None)
            
        except json.JSONDecodeError as e:
            return Failure(ProfileError(f"Invalid JSON in state file: {e}"))
        except Exception as e:
            return Failure(ProfileError(f"Failed to get active profile: {e}"))
    
    def _update_active_profile(self, profile: ProfileType, player: PlayerType) -> Result[None]:
        """Update the active profile in the state file.
        
        Args:
            profile: Profile to set as active
            player: Player type
            
        Returns:
            Result indicating success or failure
        """
        try:
            import json
            
            # Read existing state or create new
            if self.state_file.exists():
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {'installations': []}
            
            # Update active profiles section
            if 'active_profiles' not in data:
                data['active_profiles'] = {}
            
            data['active_profiles'][player.value] = profile.value
            
            # Write back to file
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            return Success(None)
            
        except Exception as e:
            return Failure(ProfileError(f"Failed to update active profile: {e}"))


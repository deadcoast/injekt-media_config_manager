"""Command implementations for the CLI."""

from pathlib import Path
from typing import Optional, List

from injekt.core.result import Result, Success, Failure
from injekt.core.models import Package
from injekt.core.errors import ConflictError
from injekt.business.package_repository import PackageRepository
from injekt.business.installer import Installer
from injekt.io.path_resolver import WindowsPathResolver
from injekt.cli.output import OutputFormatter
from injekt.cli.input import InputHandler


class ListCommand:
    """Command to list available configuration packages."""
    
    def __init__(
        self,
        package_repository: PackageRepository,
        output_formatter: OutputFormatter
    ):
        """
        Initialize the list command.
        
        Args:
            package_repository: Repository for package operations
            output_formatter: Formatter for output display
        """
        self.package_repository = package_repository
        self.output_formatter = output_formatter
    
    def execute(self) -> int:
        """
        Execute the list command to display all available packages.
        
        Returns:
            Exit code (0 for success, 1 for error)
        """
        # Get all available packages
        packages_result = self.package_repository.list_packages()
        
        if isinstance(packages_result, Failure):
            self.output_formatter.format_error(
                f"Failed to list packages: {packages_result.error}"
            )
            return 1
        
        packages = packages_result.value
        
        # Handle empty package list
        if not packages:
            self.output_formatter.format_warning(
                "No packages found. The assets directory is empty."
            )
            return 0
        
        # Get installed packages to mark them
        installed_result = self.package_repository.get_installed_packages()
        installed_names = []
        
        if isinstance(installed_result, Success):
            installed_names = [pkg.name for pkg in installed_result.value]
        
        # Display packages with name, description, player, version, and installation status
        self.output_formatter.format_package_list(packages, installed_names)
        
        return 0



class InstallCommand:
    """Command to install a configuration package."""
    
    def __init__(
        self,
        package_repository: PackageRepository,
        installer: Installer,
        path_resolver: WindowsPathResolver,
        output_formatter: OutputFormatter,
        input_handler: InputHandler,
        dry_run: bool = False
    ):
        """
        Initialize the install command.
        
        Args:
            package_repository: Repository for package operations
            installer: Installer for package installation
            path_resolver: Path resolver for detecting directories
            output_formatter: Formatter for output display
            input_handler: Handler for user input
            dry_run: If True, simulate without making changes
        """
        self.package_repository = package_repository
        self.installer = installer
        self.path_resolver = path_resolver
        self.output_formatter = output_formatter
        self.input_handler = input_handler
        self.dry_run = dry_run
    
    def execute(self, package_name: str) -> int:
        """
        Execute the install command for a package.
        
        Args:
            package_name: Name of the package to install
            
        Returns:
            Exit code (0 for success, 1 for error)
        """
        # Step 1: Validate package exists
        package_result = self.package_repository.get_package(package_name)
        
        if isinstance(package_result, Failure):
            self.output_formatter.format_error(
                f"Package not found: {package_name}"
            )
            return 1
        
        package = package_result.value
        
        # Step 2: Detect target directory with user prompts
        target_dir_result = self._detect_target_directory(package)
        
        if isinstance(target_dir_result, Failure):
            self.output_formatter.format_error(
                f"Failed to detect target directory: {target_dir_result.error}"
            )
            return 1
        
        target_dir = target_dir_result.value
        
        # Step 3: Install package (which includes backup creation and conflict handling)
        install_result = self.installer.install_package(
            package,
            target_dir,
            dry_run=self.dry_run
        )
        
        if isinstance(install_result, Failure):
            # Handle file conflicts specially
            if isinstance(install_result.error, ConflictError):
                self.output_formatter.format_error(str(install_result.error))
                
                # Offer conflict resolution options
                if self._handle_conflicts(package, target_dir):
                    # User chose to proceed, retry installation
                    return self.execute(package_name)
                else:
                    return 1
            else:
                self.output_formatter.format_error(
                    f"Installation failed: {install_result.error}"
                )
                return 1
        
        installation_state = install_result.value
        
        # Step 4: Display installation summary
        self._display_installation_summary(package, installation_state)
        
        return 0
    
    def _detect_target_directory(self, package: Package) -> Result[Path]:
        """
        Detect target directory for installation with user prompts.
        
        Args:
            package: Package to install
            
        Returns:
            Result containing target directory path
        """
        # Try automatic detection
        detect_result = self.path_resolver.detect_player_directory(package.player)
        
        if isinstance(detect_result, Success):
            # Found automatically, confirm with user
            detected_path = detect_result.value
            
            if self.input_handler.prompt_for_confirmation(
                f"Install to detected directory: {detected_path}?",
                default=True
            ):
                return Success(detected_path)
        
        # Detection failed or user declined, prompt for custom path
        self.output_formatter.format_warning(
            f"Could not automatically detect {package.player.value} directory."
        )
        
        if self.input_handler.prompt_for_confirmation(
            "Would you like to specify a custom path?",
            default=True
        ):
            custom_path = self.input_handler.prompt_for_path(
                f"Enter {package.player.value} configuration directory",
                must_exist=False
            )
            
            # Offer to create if doesn't exist
            if not custom_path.exists():
                if self.input_handler.prompt_for_confirmation(
                    f"Directory does not exist. Create it?",
                    default=True
                ):
                    try:
                        custom_path.mkdir(parents=True, exist_ok=True)
                        return Success(custom_path)
                    except Exception as e:
                        return Failure(Exception(f"Failed to create directory: {e}"))
                else:
                    return Failure(Exception("Installation cancelled by user"))
            
            return Success(custom_path)
        else:
            return Failure(Exception("Installation cancelled by user"))
    
    def _handle_conflicts(self, package: Package, target_dir: Path) -> bool:
        """
        Handle file conflicts by prompting user for resolution.
        
        Args:
            package: Package being installed
            target_dir: Target installation directory
            
        Returns:
            True if user wants to proceed, False to abort
        """
        self.output_formatter.format_warning(
            "File conflicts detected. These files are managed by other packages."
        )
        
        choice = self.input_handler.prompt_for_choice(
            "How would you like to proceed?",
            choices=["Abort installation", "Skip conflicting files", "Overwrite (backup first)"],
            default="Abort installation"
        )
        
        if choice == "Abort installation":
            return False
        elif choice == "Skip conflicting files":
            # TODO: Implement skip logic
            self.output_formatter.format_warning(
                "Skip functionality not yet implemented. Aborting."
            )
            return False
        elif choice == "Overwrite (backup first)":
            # TODO: Implement overwrite with backup
            self.output_formatter.format_warning(
                "Overwrite functionality not yet implemented. Aborting."
            )
            return False
        
        return False
    
    def _display_installation_summary(self, package: Package, installation_state) -> None:
        """
        Display summary of installation.
        
        Args:
            package: Package that was installed
            installation_state: Installation state result
        """
        if self.dry_run:
            self.output_formatter.format_success(
                f"[DRY RUN] Would install package: {package.name}"
            )
        else:
            self.output_formatter.format_success(
                f"Successfully installed package: {package.name}"
            )
        
        # Display installed files
        self.output_formatter.console.print("\n[bold]Installed files:[/bold]")
        for file_path in installation_state.installed_files:
            self.output_formatter.console.print(f"  • {file_path}")
        
        # Display backup location if created
        if installation_state.backup_dir:
            self.output_formatter.console.print(
                f"\n[bold]Backup created at:[/bold] {installation_state.backup_dir}"
            )



class VerifyCommand:
    """Command to verify package installation."""
    
    def __init__(
        self,
        package_repository: PackageRepository,
        installer: Installer,
        output_formatter: OutputFormatter
    ):
        """
        Initialize the verify command.
        
        Args:
            package_repository: Repository for package operations
            installer: Installer for verification operations
            output_formatter: Formatter for output display
        """
        self.package_repository = package_repository
        self.installer = installer
        self.output_formatter = output_formatter
    
    def execute(self, package_name: str) -> int:
        """
        Execute the verify command for a package.
        
        Args:
            package_name: Name of the package to verify
            
        Returns:
            Exit code (0 for success, 1 for error)
        """
        # Get the package
        package_result = self.package_repository.get_package(package_name)
        
        if isinstance(package_result, Failure):
            self.output_formatter.format_error(
                f"Package not found: {package_name}"
            )
            return 1
        
        package = package_result.value
        
        # Verify installation
        verify_result = self.installer.verify_installation(package)
        
        if isinstance(verify_result, Failure):
            self.output_formatter.format_error(
                f"Verification failed: {verify_result.error}"
            )
            return 1
        
        issues = verify_result.value
        
        if not issues:
            self.output_formatter.format_success(
                f"Package '{package_name}' is correctly installed"
            )
            return 0
        else:
            self.output_formatter.format_error(
                f"Found {len(issues)} issue(s) with package '{package_name}':"
            )
            for issue in issues:
                self.output_formatter.console.print(f"  • {issue}")
            
            # Provide suggestions
            self.output_formatter.console.print(
                "\n[bold]Suggestions:[/bold]"
            )
            self.output_formatter.console.print(
                "  • Try reinstalling the package"
            )
            self.output_formatter.console.print(
                "  • Check file permissions"
            )
            
            return 1



class RollbackCommand:
    """Command to rollback to a previous configuration."""
    
    def __init__(
        self,
        backup_manager,
        output_formatter: OutputFormatter,
        input_handler: InputHandler
    ):
        """
        Initialize the rollback command.
        
        Args:
            backup_manager: Backup manager for backup operations
            output_formatter: Formatter for output display
            input_handler: Handler for user input
        """
        self.backup_manager = backup_manager
        self.output_formatter = output_formatter
        self.input_handler = input_handler
    
    def execute(self) -> int:
        """
        Execute the rollback command.
        
        Returns:
            Exit code (0 for success, 1 for error)
        """
        # List available backups
        backups_result = self.backup_manager.list_backups()
        
        if isinstance(backups_result, Failure):
            self.output_formatter.format_error(
                f"Failed to list backups: {backups_result.error}"
            )
            return 1
        
        backups = backups_result.value
        
        if not backups:
            self.output_formatter.format_warning(
                "No backups available"
            )
            return 0
        
        # Display backups
        self.output_formatter.console.print("\n[bold]Available backups:[/bold]")
        backup_choices = []
        for backup in backups:
            choice_str = f"{backup.backup_id} ({backup.timestamp.strftime('%Y-%m-%d %H:%M:%S')})"
            backup_choices.append(choice_str)
            self.output_formatter.console.print(f"  • {choice_str}")
        
        # Prompt user to select backup
        selected = self.input_handler.prompt_for_choice(
            "\nSelect backup to restore",
            choices=backup_choices
        )
        
        # Extract backup_id from selection
        backup_id = selected.split(" (")[0]
        
        # Confirm restoration
        if not self.input_handler.prompt_for_confirmation(
            f"Restore backup '{backup_id}'? This will create a backup of the current state first.",
            default=False
        ):
            self.output_formatter.format_warning("Rollback cancelled")
            return 0
        
        # Restore backup
        restore_result = self.backup_manager.restore_backup(backup_id)
        
        if isinstance(restore_result, Failure):
            self.output_formatter.format_error(
                f"Failed to restore backup: {restore_result.error}"
            )
            return 1
        
        self.output_formatter.format_success(
            f"Successfully restored backup: {backup_id}"
        )
        
        return 0


class UninstallCommand:
    """Command to uninstall a package."""
    
    def __init__(
        self,
        installer: Installer,
        output_formatter: OutputFormatter,
        input_handler: InputHandler,
        dry_run: bool = False
    ):
        """
        Initialize the uninstall command.
        
        Args:
            installer: Installer for uninstallation operations
            output_formatter: Formatter for output display
            input_handler: Handler for user input
            dry_run: If True, simulate without making changes
        """
        self.installer = installer
        self.output_formatter = output_formatter
        self.input_handler = input_handler
        self.dry_run = dry_run
    
    def execute(self, package_name: str) -> int:
        """
        Execute the uninstall command.
        
        Args:
            package_name: Name of package to uninstall
            
        Returns:
            Exit code (0 for success, 1 for error)
        """
        # Confirm uninstallation
        if not self.dry_run:
            if not self.input_handler.prompt_for_confirmation(
                f"Uninstall package '{package_name}'? A backup will be created first.",
                default=False
            ):
                self.output_formatter.format_warning("Uninstall cancelled")
                return 0
        
        # Uninstall package
        uninstall_result = self.installer.uninstall_package(
            package_name,
            dry_run=self.dry_run
        )
        
        if isinstance(uninstall_result, Failure):
            self.output_formatter.format_error(
                f"Uninstall failed: {uninstall_result.error}"
            )
            return 1
        
        removed_files = uninstall_result.value
        
        if self.dry_run:
            self.output_formatter.format_success(
                f"[DRY RUN] Would uninstall package: {package_name}"
            )
        else:
            self.output_formatter.format_success(
                f"Successfully uninstalled package: {package_name}"
            )
        
        # Display removed files
        if removed_files:
            self.output_formatter.console.print("\n[bold]Removed files:[/bold]")
            for file_path in removed_files:
                self.output_formatter.console.print(f"  • {file_path}")
        
        return 0


class InfoCommand:
    """Command to display package information."""
    
    def __init__(
        self,
        package_repository: PackageRepository,
        output_formatter: OutputFormatter
    ):
        """
        Initialize the info command.
        
        Args:
            package_repository: Repository for package operations
            output_formatter: Formatter for output display
        """
        self.package_repository = package_repository
        self.output_formatter = output_formatter
    
    def execute(self, package_name: str) -> int:
        """
        Execute the info command.
        
        Args:
            package_name: Name of package to display info for
            
        Returns:
            Exit code (0 for success, 1 for error)
        """
        # Get package
        package_result = self.package_repository.get_package(package_name)
        
        if isinstance(package_result, Failure):
            self.output_formatter.format_error(
                f"Package not found: {package_name}"
            )
            return 1
        
        package = package_result.value
        
        # Display package information
        self.output_formatter.console.print(f"\n[bold cyan]{package.name}[/bold cyan]")
        self.output_formatter.console.print(f"[bold]Description:[/bold] {package.description}")
        self.output_formatter.console.print(f"[bold]Player:[/bold] {package.player.value.upper()}")
        self.output_formatter.console.print(f"[bold]Version:[/bold] {package.version}")
        self.output_formatter.console.print(f"[bold]Profile:[/bold] {package.profile.value}")
        
        # Display dependencies
        if package.dependencies:
            self.output_formatter.console.print(f"\n[bold]Dependencies:[/bold]")
            for dep in package.dependencies:
                self.output_formatter.console.print(f"  • {dep}")
        else:
            self.output_formatter.console.print(f"\n[bold]Dependencies:[/bold] None")
        
        # Display files
        self.output_formatter.console.print(f"\n[bold]Files ({len(package.files)}):[/bold]")
        for pkg_file in package.files:
            required_str = "" if pkg_file.required else " (optional)"
            self.output_formatter.console.print(
                f"  • {pkg_file.target_path} [{pkg_file.file_type.value}]{required_str}"
            )
        
        return 0


class ReportCommand:
    """Command to generate configuration report."""
    
    def __init__(
        self,
        package_repository: PackageRepository,
        output_formatter: OutputFormatter
    ):
        """
        Initialize the report command.
        
        Args:
            package_repository: Repository for package operations
            output_formatter: Formatter for output display
        """
        self.package_repository = package_repository
        self.output_formatter = output_formatter
    
    def execute(self) -> int:
        """
        Execute the report command.
        
        Returns:
            Exit code (0 for success, 1 for error)
        """
        # Get installed packages
        installed_result = self.package_repository.get_installed_packages()
        
        if isinstance(installed_result, Failure):
            self.output_formatter.format_error(
                f"Failed to get installed packages: {installed_result.error}"
            )
            return 1
        
        installed_packages = installed_result.value
        
        if not installed_packages:
            self.output_formatter.format_warning(
                "No packages installed"
            )
            return 0
        
        # Display report
        self.output_formatter.console.print("\n[bold cyan]Configuration Report[/bold cyan]\n")
        
        self.output_formatter.console.print(f"[bold]Installed Packages ({len(installed_packages)}):[/bold]")
        for pkg in installed_packages:
            self.output_formatter.console.print(
                f"  • {pkg.name} v{pkg.version} ({pkg.player.value.upper()}) - {pkg.profile.value}"
            )
        
        # Count plugins and shaders
        total_plugins = 0
        total_shaders = 0
        total_configs = 0
        
        from injekt.core.models import FileType
        
        for pkg in installed_packages:
            for file in pkg.files:
                if file.file_type in [FileType.PLUGIN_LUA, FileType.PLUGIN_JS]:
                    total_plugins += 1
                elif file.file_type == FileType.SHADER:
                    total_shaders += 1
                elif file.file_type == FileType.CONFIG:
                    total_configs += 1
        
        self.output_formatter.console.print(f"\n[bold]Summary:[/bold]")
        self.output_formatter.console.print(f"  • Configuration files: {total_configs}")
        self.output_formatter.console.print(f"  • Plugins: {total_plugins}")
        self.output_formatter.console.print(f"  • Shaders: {total_shaders}")
        
        return 0



class ProfileListCommand:
    """Command to list available profiles."""
    
    def __init__(
        self,
        profile_manager,
        output_formatter: OutputFormatter
    ):
        """
        Initialize the profile list command.
        
        Args:
            profile_manager: Profile manager for profile operations
            output_formatter: Formatter for output display
        """
        self.profile_manager = profile_manager
        self.output_formatter = output_formatter
    
    def execute(self) -> int:
        """
        Execute the profile list command.
        
        Returns:
            Exit code (0 for success, 1 for error)
        """
        # List profiles
        profiles_result = self.profile_manager.list_profiles()
        
        if isinstance(profiles_result, Failure):
            self.output_formatter.format_error(
                f"Failed to list profiles: {profiles_result.error}"
            )
            return 1
        
        profiles = profiles_result.value
        
        # Get active profile
        active_result = self.profile_manager.get_active_profile()
        active_profile = active_result.value if isinstance(active_result, Success) else None
        
        # Display profiles
        self.output_formatter.console.print("\n[bold]Available Profiles:[/bold]")
        for profile in profiles:
            active_marker = " [green](active)[/green]" if profile == active_profile else ""
            self.output_formatter.console.print(f"  • {profile}{active_marker}")
        
        return 0


class ProfileSwitchCommand:
    """Command to switch configuration profile."""
    
    def __init__(
        self,
        profile_manager,
        output_formatter: OutputFormatter,
        input_handler: InputHandler
    ):
        """
        Initialize the profile switch command.
        
        Args:
            profile_manager: Profile manager for profile operations
            output_formatter: Formatter for output display
            input_handler: Handler for user input
        """
        self.profile_manager = profile_manager
        self.output_formatter = output_formatter
        self.input_handler = input_handler
    
    def execute(self, profile_name: str) -> int:
        """
        Execute the profile switch command.
        
        Args:
            profile_name: Name of profile to switch to
            
        Returns:
            Exit code (0 for success, 1 for error)
        """
        # Confirm switch
        if not self.input_handler.prompt_for_confirmation(
            f"Switch to profile '{profile_name}'? Current configuration will be backed up.",
            default=True
        ):
            self.output_formatter.format_warning("Profile switch cancelled")
            return 0
        
        # Switch profile
        switch_result = self.profile_manager.switch_profile(profile_name)
        
        if isinstance(switch_result, Failure):
            self.output_formatter.format_error(
                f"Failed to switch profile: {switch_result.error}"
            )
            return 1
        
        self.output_formatter.format_success(
            f"Successfully switched to profile: {profile_name}"
        )
        
        return 0


class UpdateCommand:
    """Command to update an installed package."""
    
    def __init__(
        self,
        package_repository: PackageRepository,
        installer: Installer,
        output_formatter: OutputFormatter,
        input_handler: InputHandler,
        dry_run: bool = False
    ):
        """
        Initialize the update command.
        
        Args:
            package_repository: Repository for package operations
            installer: Installer for installation operations
            output_formatter: Formatter for output display
            input_handler: Handler for user input
            dry_run: If True, simulate without making changes
        """
        self.package_repository = package_repository
        self.installer = installer
        self.output_formatter = output_formatter
        self.input_handler = input_handler
        self.dry_run = dry_run
    
    def execute(self, package_name: str) -> int:
        """
        Execute the update command.
        
        Args:
            package_name: Name of package to update
            
        Returns:
            Exit code (0 for success, 1 for error)
        """
        # Get available package
        available_result = self.package_repository.get_package(package_name)
        
        if isinstance(available_result, Failure):
            self.output_formatter.format_error(
                f"Package not found: {package_name}"
            )
            return 1
        
        available_package = available_result.value
        
        # Get installed packages
        installed_result = self.package_repository.get_installed_packages()
        
        if isinstance(installed_result, Failure):
            self.output_formatter.format_error(
                f"Failed to get installed packages: {installed_result.error}"
            )
            return 1
        
        # Find installed version
        installed_package = None
        for pkg in installed_result.value:
            if pkg.name == package_name:
                installed_package = pkg
                break
        
        if not installed_package:
            self.output_formatter.format_error(
                f"Package not installed: {package_name}"
            )
            return 1
        
        # Compare versions
        if installed_package.version == available_package.version:
            self.output_formatter.format_success(
                f"Package '{package_name}' is already up to date (v{installed_package.version})"
            )
            return 0
        
        # Display changes
        self.output_formatter.console.print(
            f"\n[bold]Update available:[/bold] {installed_package.version} → {available_package.version}"
        )
        
        # Confirm update
        if not self.dry_run:
            if not self.input_handler.prompt_for_confirmation(
                "Proceed with update? Current configuration will be backed up.",
                default=True
            ):
                self.output_formatter.format_warning("Update cancelled")
                return 0
        
        # Update is essentially a reinstall
        # The installer will handle backup and preserve customizations
        self.output_formatter.format_warning(
            "Note: Update will reinstall the package. User customizations in non-package files will be preserved."
        )
        
        # For now, just inform the user to use install command
        self.output_formatter.console.print(
            "\nTo update, use: injekt install " + package_name
        )
        
        return 0


class ExportCommand:
    """Command to export current configuration."""
    
    def __init__(
        self,
        package_repository: PackageRepository,
        output_formatter: OutputFormatter,
        input_handler: InputHandler
    ):
        """
        Initialize the export command.
        
        Args:
            package_repository: Repository for package operations
            output_formatter: Formatter for output display
            input_handler: Handler for user input
        """
        self.package_repository = package_repository
        self.output_formatter = output_formatter
        self.input_handler = input_handler
    
    def execute(self, output_dir: Optional[Path] = None) -> int:
        """
        Execute the export command.
        
        Args:
            output_dir: Optional output directory for export
            
        Returns:
            Exit code (0 for success, 1 for error)
        """
        # Get installed packages
        installed_result = self.package_repository.get_installed_packages()
        
        if isinstance(installed_result, Failure):
            self.output_formatter.format_error(
                f"Failed to get installed packages: {installed_result.error}"
            )
            return 1
        
        installed_packages = installed_result.value
        
        if not installed_packages:
            self.output_formatter.format_warning(
                "No packages installed to export"
            )
            return 0
        
        # Prompt for output directory if not provided
        if output_dir is None:
            output_dir = self.input_handler.prompt_for_path(
                "Enter export directory",
                must_exist=False
            )
        
        # Create export directory
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.output_formatter.format_error(
                f"Failed to create export directory: {e}"
            )
            return 1
        
        self.output_formatter.format_warning(
            "Export functionality not fully implemented yet. "
            "This would copy all config files, plugins, and shaders to the export directory."
        )
        
        return 0


class ImportCommand:
    """Command to import a configuration package."""
    
    def __init__(
        self,
        package_repository: PackageRepository,
        output_formatter: OutputFormatter,
        input_handler: InputHandler
    ):
        """
        Initialize the import command.
        
        Args:
            package_repository: Repository for package operations
            output_formatter: Formatter for output display
            input_handler: Handler for user input
        """
        self.package_repository = package_repository
        self.output_formatter = output_formatter
        self.input_handler = input_handler
    
    def execute(self, input_dir: Path) -> int:
        """
        Execute the import command.
        
        Args:
            input_dir: Directory containing configuration to import
            
        Returns:
            Exit code (0 for success, 1 for error)
        """
        # Validate input directory exists
        if not input_dir.exists():
            self.output_formatter.format_error(
                f"Import directory does not exist: {input_dir}"
            )
            return 1
        
        if not input_dir.is_dir():
            self.output_formatter.format_error(
                f"Import path is not a directory: {input_dir}"
            )
            return 1
        
        self.output_formatter.format_warning(
            "Import functionality not fully implemented yet. "
            "This would validate the structure and create a new package entry."
        )
        
        return 0

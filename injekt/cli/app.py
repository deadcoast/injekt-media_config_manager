"""Main Typer CLI application for Injekt."""

from pathlib import Path
from typing import Optional
import typer
from rich.console import Console

from injekt.core.models import PlayerType
from injekt.io.config_parser import ConfigParser
from injekt.io.path_resolver import WindowsPathResolver
from injekt.io.file_operations import FileOperations
from injekt.io.backup_storage import BackupStorage
from injekt.business.package_repository import PackageRepository
from injekt.business.installer import Installer
from injekt.business.backup_manager import BackupManager
from injekt.business.validator import ConfigValidatorImpl
from injekt.business.profile_manager import ProfileManager
from injekt.cli.output import OutputFormatter
from injekt.cli.input import InputHandler
from injekt.cli.commands import (
    ListCommand,
    InstallCommand,
    VerifyCommand,
    RollbackCommand,
    UninstallCommand,
    InfoCommand,
    ReportCommand,
    ProfileListCommand,
    ProfileSwitchCommand,
    UpdateCommand,
    ExportCommand,
    ImportCommand
)
from injekt.cli.interactive import InteractiveMode

# Create the main Typer app
app = typer.Typer(
    name="injekt",
    help="Video Media Player Configuration Manager",
    add_completion=False
)

# Global state for options
class GlobalState:
    """Global state for CLI options."""
    verbose: bool = False
    dry_run: bool = False
    output_format: str = "text"
    player: Optional[PlayerType] = None

state = GlobalState()


def version_callback(value: bool):
    """Display version information."""
    if value:
        console = Console()
        console.print("[bold cyan]Injekt CLI[/bold cyan] version [green]0.1.0[/green]")
        raise typer.Exit()


@app.callback()
def main_callback(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output with detailed logging"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-n",
        help="Simulate operations without making any changes to disk"
    ),
    output_format: str = typer.Option(
        "text",
        "--format",
        "-f",
        help="Output format: text (default), json, or table"
    ),
    player: Optional[str] = typer.Option(
        None,
        "--player",
        "-p",
        help="Target player: mpv or vlc (auto-detected if not specified)"
    ),
    version: bool = typer.Option(
        False,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show version information and exit"
    )
):
    """
    Injekt CLI - Video Media Player Configuration Manager
    
    Manage and install optimized configurations for MPV and VLC media players.
    Automates deployment of configuration files, plugins, and shaders with
    backup and rollback capabilities.
    
    Global Options:
        --verbose, -v     Show detailed output and logging
        --dry-run, -n     Preview changes without modifying files
        --format, -f      Choose output format (text, json, table)
        --player, -p      Specify target player (mpv, vlc)
        --version         Display version information
    
    Quick Start:
        1. List available packages:    injekt list
        2. View package details:       injekt info <package-name>
        3. Install a package:          injekt install <package-name>
        4. Verify installation:        injekt verify <package-name>
    
    For interactive guided setup:
        injekt interactive
    
    For help on a specific command:
        injekt <command> --help
    
    Examples:
        injekt list
        injekt install mpv-ultra-5090
        injekt verify mpv-ultra-5090
        injekt rollback
        injekt report --format json
    """
    state.verbose = verbose
    state.dry_run = dry_run
    state.output_format = output_format
    
    if player:
        try:
            state.player = PlayerType(player.lower())
        except ValueError:
            console = Console()
            console.print(f"[red]Error:[/red] Invalid player: {player}. Must be 'mpv' or 'vlc'")
            raise typer.Exit(1)


def get_dependencies():
    """Create and return all dependencies for commands."""
    # Determine paths
    assets_dir = Path("assets")
    injekt_dir = Path.home() / ".injekt"
    backup_dir = injekt_dir / "backups"
    state_file = injekt_dir / "state.json"
    
    # Ensure directories exist
    injekt_dir.mkdir(parents=True, exist_ok=True)
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Create I/O layer dependencies
    config_parser = ConfigParser()
    path_resolver = WindowsPathResolver()
    file_operations = FileOperations()
    backup_storage = BackupStorage(backup_dir)
    
    # Create business layer dependencies
    package_repository = PackageRepository(assets_dir, state_file, config_parser)
    backup_manager = BackupManager(backup_storage)
    validator = ConfigValidatorImpl()
    
    # Create installer with all dependencies
    installer = Installer(
        file_ops=file_operations,
        backup_manager=backup_manager,
        validator=validator,
        config_parser=config_parser,
        state_file=state_file
    )
    
    # Create profile manager
    profile_manager = ProfileManager(
        package_repository=package_repository,
        backup_manager=backup_manager,
        installer=installer,
        state_file=state_file
    )
    
    # Create CLI layer dependencies
    output_formatter = OutputFormatter(output_format=state.output_format)
    input_handler = InputHandler()
    
    return {
        "package_repository": package_repository,
        "installer": installer,
        "path_resolver": path_resolver,
        "backup_manager": backup_manager,
        "profile_manager": profile_manager,
        "output_formatter": output_formatter,
        "input_handler": input_handler
    }


@app.command()
def list():
    """
    List all available configuration packages.
    
    Displays all packages in the assets directory with their name, description,
    target player, version, and installation status.
    
    Examples:
        injekt list
        injekt list --format json
        injekt list -v
    
    Common use cases:
        - Browse available configurations before installation
        - Check which packages are already installed
        - View package versions and compatibility
    """
    deps = get_dependencies()
    
    command = ListCommand(
        package_repository=deps["package_repository"],
        output_formatter=deps["output_formatter"]
    )
    
    exit_code = command.execute()
    raise typer.Exit(exit_code)


@app.command()
def install(
    package_name: str = typer.Argument(..., help="Name of the package to install")
):
    """
    Install a configuration package.
    
    Installs the specified package to the detected player directory. Creates
    a backup of existing configurations before installation. Validates all
    files before copying.
    
    Examples:
        injekt install mpv-ultra-5090
        injekt install vlc-config --dry-run
        injekt install mpv-ultra-5090 -v
    
    Common use cases:
        - Install optimized configurations for your media player
        - Preview installation with --dry-run before committing
        - Upgrade to a new configuration profile
    
    The command will:
        1. Validate the package exists
        2. Detect or prompt for the target directory
        3. Create a backup of existing configs
        4. Validate all configuration files
        5. Copy files to the target directory
        6. Display installation summary
    """
    deps = get_dependencies()
    
    command = InstallCommand(
        package_repository=deps["package_repository"],
        installer=deps["installer"],
        path_resolver=deps["path_resolver"],
        output_formatter=deps["output_formatter"],
        input_handler=deps["input_handler"],
        dry_run=state.dry_run
    )
    
    exit_code = command.execute(package_name)
    raise typer.Exit(exit_code)


@app.command()
def verify(
    package_name: str = typer.Argument(..., help="Name of the package to verify")
):
    """
    Verify package installation.
    
    Checks that all required files exist, have correct permissions, and
    validates configuration file syntax.
    
    Examples:
        injekt verify mpv-ultra-5090
        injekt verify vlc-config -v
    
    Common use cases:
        - Troubleshoot installation issues
        - Confirm package integrity after manual changes
        - Validate configuration after system updates
    
    The command checks:
        - All required files exist in target directories
        - File permissions are correct
        - Configuration file syntax is valid
        - Plugin dependencies are satisfied
    """
    deps = get_dependencies()
    
    command = VerifyCommand(
        package_repository=deps["package_repository"],
        installer=deps["installer"],
        output_formatter=deps["output_formatter"]
    )
    
    exit_code = command.execute(package_name)
    raise typer.Exit(exit_code)


@app.command()
def rollback():
    """
    Rollback to a previous configuration.
    
    Lists available backups and restores the selected one. Creates a backup
    of the current state before rollback for safety.
    
    Examples:
        injekt rollback
        injekt rollback -v
    
    Common use cases:
        - Undo a problematic installation
        - Restore previous working configuration
        - Recover from configuration errors
    
    The command will:
        1. List all available backups with timestamps
        2. Prompt you to select a backup
        3. Create a backup of current state
        4. Restore files from the selected backup
        5. Display restored files
    """
    deps = get_dependencies()
    
    command = RollbackCommand(
        backup_manager=deps["backup_manager"],
        output_formatter=deps["output_formatter"],
        input_handler=deps["input_handler"]
    )
    
    exit_code = command.execute()
    raise typer.Exit(exit_code)


@app.command()
def uninstall(
    package_name: str = typer.Argument(..., help="Name of the package to uninstall")
):
    """
    Uninstall a configuration package.
    
    Removes all files installed by the package. Creates a backup before
    uninstallation. Preserves user-created files not part of the package.
    
    Examples:
        injekt uninstall mpv-ultra-5090
        injekt uninstall vlc-config --dry-run
        injekt uninstall mpv-ultra-5090 -y
    
    Common use cases:
        - Remove unwanted configurations
        - Clean up before installing a different package
        - Return to default player settings
    
    The command will:
        1. Confirm uninstallation (unless -y flag is used)
        2. Create a backup of current state
        3. Remove all package files
        4. Clean up empty directories
        5. Display removed files
    """
    deps = get_dependencies()
    
    command = UninstallCommand(
        installer=deps["installer"],
        output_formatter=deps["output_formatter"],
        input_handler=deps["input_handler"],
        dry_run=state.dry_run
    )
    
    exit_code = command.execute(package_name)
    raise typer.Exit(exit_code)


@app.command()
def info(
    package_name: str = typer.Argument(..., help="Name of the package to show info for")
):
    """
    Display detailed package information.
    
    Shows comprehensive details about a package including description,
    target player, version, profile, dependencies, and all included files.
    
    Examples:
        injekt info mpv-ultra-5090
        injekt info vlc-config
        injekt info mpv-ultra-5090 --format json
    
    Common use cases:
        - Review package contents before installation
        - Check package compatibility and requirements
        - Understand what files will be installed
        - View package dependencies
    
    Displays:
        - Package name and description
        - Target player and version
        - Configuration profile type
        - Dependencies (if any)
        - Complete file list with types
    """
    deps = get_dependencies()
    
    command = InfoCommand(
        package_repository=deps["package_repository"],
        output_formatter=deps["output_formatter"]
    )
    
    exit_code = command.execute(package_name)
    raise typer.Exit(exit_code)


@app.command()
def report():
    """
    Generate a configuration report.
    
    Creates a comprehensive report of your current configuration including
    all installed packages, plugins, shaders, and active profile.
    
    Examples:
        injekt report
        injekt report --format json
        injekt report -f json > config-report.json
    
    Common use cases:
        - Document your current setup
        - Share configuration details for troubleshooting
        - Track installed packages and versions
        - Export configuration inventory
    
    The report includes:
        - All installed packages with versions
        - Active configuration files
        - Installed plugins (Lua and JavaScript)
        - Installed shaders
        - Current active profile
        - Summary statistics
    """
    deps = get_dependencies()
    
    command = ReportCommand(
        package_repository=deps["package_repository"],
        output_formatter=deps["output_formatter"]
    )
    
    exit_code = command.execute()
    raise typer.Exit(exit_code)


@app.command()
def update(
    package_name: str = typer.Argument(..., help="Name of the package to update")
):
    """
    Update an installed package.
    
    Compares installed version with available version and updates if newer
    version is available. Creates backup before updating and preserves
    user customizations.
    
    Examples:
        injekt update mpv-ultra-5090
        injekt update vlc-config --dry-run
        injekt update mpv-ultra-5090 -v
    
    Common use cases:
        - Get latest optimizations and bug fixes
        - Upgrade to new configuration versions
        - Preview updates with --dry-run
    
    The command will:
        1. Check for available updates
        2. Display version changes
        3. Confirm update with user
        4. Create backup of current configuration
        5. Install updated package
        6. Preserve user customizations where possible
    """
    deps = get_dependencies()
    
    command = UpdateCommand(
        package_repository=deps["package_repository"],
        installer=deps["installer"],
        output_formatter=deps["output_formatter"],
        input_handler=deps["input_handler"],
        dry_run=state.dry_run
    )
    
    exit_code = command.execute(package_name)
    raise typer.Exit(exit_code)


@app.command()
def export(
    output_dir: Optional[Path] = typer.Argument(
        None,
        help="Directory to export configuration to"
    )
):
    """
    Export current configuration.
    
    Copies all active configuration files, plugins, and shaders to an
    export directory. Creates a manifest file for easy re-import.
    
    Examples:
        injekt export ./my-config-backup
        injekt export ~/Desktop/mpv-export
        injekt export
    
    Common use cases:
        - Backup your configuration
        - Share your setup with others
        - Transfer configuration to another machine
        - Create a portable configuration package
    
    The export includes:
        - All active configuration files
        - Installed plugins (Lua and JavaScript)
        - Installed shaders
        - Package manifest for re-import
        - Optional zip compression
    """
    deps = get_dependencies()
    
    command = ExportCommand(
        package_repository=deps["package_repository"],
        output_formatter=deps["output_formatter"],
        input_handler=deps["input_handler"]
    )
    
    exit_code = command.execute(output_dir)
    raise typer.Exit(exit_code)


@app.command()
def import_config(
    input_dir: Path = typer.Argument(..., help="Directory containing configuration to import")
):
    """
    Import a configuration package.
    
    Validates and imports a configuration from a directory. Creates a new
    package entry that can be installed like any other package.
    
    Examples:
        injekt import ./my-custom-config
        injekt import ~/Downloads/shared-mpv-config
        injekt import ./exported-config -v
    
    Common use cases:
        - Import configurations from others
        - Restore exported configurations
        - Add custom configuration packages
        - Migrate configurations from another machine
    
    The command will:
        1. Validate directory structure
        2. Check for required manifest file
        3. Prompt for package name and description
        4. Create new package entry
        5. Make package available for installation
    """
    deps = get_dependencies()
    
    command = ImportCommand(
        package_repository=deps["package_repository"],
        output_formatter=deps["output_formatter"],
        input_handler=deps["input_handler"]
    )
    
    exit_code = command.execute(input_dir)
    raise typer.Exit(exit_code)


# Create profile subcommand group
profile_app = typer.Typer(help="Manage configuration profiles")
app.add_typer(profile_app, name="profile")


@profile_app.command("list")
def profile_list():
    """
    List available configuration profiles.
    
    Displays all available profiles (performance, quality, cinematic, etc.)
    and indicates which profile is currently active.
    
    Examples:
        injekt profile list
        injekt profile list -v
    
    Common use cases:
        - Browse available profiles
        - Check which profile is active
        - Discover optimization options
    
    Profiles typically include:
        - performance: Optimized for speed and low latency
        - quality: Optimized for maximum visual quality
        - cinematic: Optimized for movie watching
        - default: Balanced general-purpose settings
    """
    deps = get_dependencies()
    
    command = ProfileListCommand(
        profile_manager=deps["profile_manager"],
        output_formatter=deps["output_formatter"]
    )
    
    exit_code = command.execute()
    raise typer.Exit(exit_code)


@profile_app.command("switch")
def profile_switch(
    profile_name: str = typer.Argument(..., help="Name of the profile to switch to")
):
    """
    Switch to a different configuration profile.
    
    Changes the active configuration profile. Creates a backup of the
    current configuration before switching.
    
    Examples:
        injekt profile switch performance
        injekt profile switch quality
        injekt profile switch cinematic -v
    
    Common use cases:
        - Switch between performance and quality modes
        - Optimize for different content types
        - Test different configuration profiles
    
    The command will:
        1. Confirm profile switch
        2. Create backup of current configuration
        3. Apply new profile settings
        4. Display success message
    """
    deps = get_dependencies()
    
    command = ProfileSwitchCommand(
        profile_manager=deps["profile_manager"],
        output_formatter=deps["output_formatter"],
        input_handler=deps["input_handler"]
    )
    
    exit_code = command.execute(profile_name)
    raise typer.Exit(exit_code)


@app.command()
def interactive():
    """
    Start interactive mode with step-by-step wizards.
    
    Launches an interactive menu system that guides you through all
    available operations with prompts and validation.
    
    Examples:
        injekt interactive
        injekt interactive -v
    
    Common use cases:
        - First-time setup and configuration
        - Guided installation process
        - Explore features without memorizing commands
        - Step-by-step troubleshooting
    
    Interactive mode provides:
        - Menu-driven interface
        - Input validation and helpful prompts
        - Confirmation before destructive operations
        - Contextual help and suggestions
        - Easy navigation between operations
    """
    deps = get_dependencies()
    
    # Create all command instances
    commands = {
        "list": ListCommand(
            package_repository=deps["package_repository"],
            output_formatter=deps["output_formatter"]
        ),
        "install": InstallCommand(
            package_repository=deps["package_repository"],
            installer=deps["installer"],
            path_resolver=deps["path_resolver"],
            output_formatter=deps["output_formatter"],
            input_handler=deps["input_handler"],
            dry_run=state.dry_run
        ),
        "verify": VerifyCommand(
            package_repository=deps["package_repository"],
            installer=deps["installer"],
            output_formatter=deps["output_formatter"]
        ),
        "rollback": RollbackCommand(
            backup_manager=deps["backup_manager"],
            output_formatter=deps["output_formatter"],
            input_handler=deps["input_handler"]
        ),
        "uninstall": UninstallCommand(
            installer=deps["installer"],
            output_formatter=deps["output_formatter"],
            input_handler=deps["input_handler"],
            dry_run=state.dry_run
        ),
        "info": InfoCommand(
            package_repository=deps["package_repository"],
            output_formatter=deps["output_formatter"]
        ),
        "report": ReportCommand(
            package_repository=deps["package_repository"],
            output_formatter=deps["output_formatter"]
        ),
        "profile_list": ProfileListCommand(
            profile_manager=deps["profile_manager"],
            output_formatter=deps["output_formatter"]
        ),
        "profile_switch": ProfileSwitchCommand(
            profile_manager=deps["profile_manager"],
            output_formatter=deps["output_formatter"],
            input_handler=deps["input_handler"]
        ),
        "update": UpdateCommand(
            package_repository=deps["package_repository"],
            installer=deps["installer"],
            output_formatter=deps["output_formatter"],
            input_handler=deps["input_handler"],
            dry_run=state.dry_run
        ),
        "export": ExportCommand(
            package_repository=deps["package_repository"],
            output_formatter=deps["output_formatter"],
            input_handler=deps["input_handler"]
        ),
        "import": ImportCommand(
            package_repository=deps["package_repository"],
            output_formatter=deps["output_formatter"],
            input_handler=deps["input_handler"]
        )
    }
    
    # Create and run interactive mode
    interactive_mode = InteractiveMode(
        input_handler=deps["input_handler"],
        output_formatter=deps["output_formatter"],
        commands=commands
    )
    
    exit_code = interactive_mode.run()
    raise typer.Exit(exit_code)


def main():
    """Main entry point for the CLI application."""
    app()


if __name__ == "__main__":
    main()

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
        help="Enable verbose output"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-n",
        help="Simulate operations without making changes"
    ),
    output_format: str = typer.Option(
        "text",
        "--format",
        "-f",
        help="Output format (text, json, table)"
    ),
    player: Optional[str] = typer.Option(
        None,
        "--player",
        "-p",
        help="Target player (mpv, vlc)"
    ),
    version: bool = typer.Option(
        False,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit"
    )
):
    """
    Injekt CLI - Video Media Player Configuration Manager
    
    Manage and install optimized configurations for MPV and VLC media players.
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
    """List all available configuration packages."""
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
    """Install a configuration package."""
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
    """Verify package installation."""
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
    """Rollback to a previous configuration."""
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
    """Uninstall a configuration package."""
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
    """Display detailed package information."""
    deps = get_dependencies()
    
    command = InfoCommand(
        package_repository=deps["package_repository"],
        output_formatter=deps["output_formatter"]
    )
    
    exit_code = command.execute(package_name)
    raise typer.Exit(exit_code)


@app.command()
def report():
    """Generate a configuration report."""
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
    """Update an installed package."""
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
    """Export current configuration."""
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
    """Import a configuration package."""
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
    """List available configuration profiles."""
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
    """Switch to a different configuration profile."""
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
    """Start interactive mode with step-by-step wizards."""
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

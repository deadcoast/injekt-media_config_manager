"""Interactive mode for the Injekt CLI."""

from typing import Optional, Dict, Callable
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from injekt.cli.input import InputHandler
from injekt.cli.output import OutputFormatter
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


class InteractiveMode:
    """Interactive mode with menu system and step-by-step wizards."""
    
    def __init__(
        self,
        input_handler: InputHandler,
        output_formatter: OutputFormatter,
        commands: Dict[str, Callable]
    ):
        """
        Initialize interactive mode.
        
        Args:
            input_handler: Handler for user input
            output_formatter: Formatter for output display
            commands: Dictionary mapping action names to command instances
        """
        self.input_handler = input_handler
        self.output_formatter = output_formatter
        self.commands = commands
        self.console = output_formatter.console
    
    def run(self) -> int:
        """
        Run the interactive mode main loop.
        
        Returns:
            Exit code (0 for success, 1 for error)
        """
        self._display_welcome()
        
        while True:
            # Display main menu
            action = self._display_main_menu()
            
            if action == "Exit":
                self.output_formatter.format_success("Goodbye!")
                return 0
            
            # Execute selected action
            try:
                exit_code = self._execute_action(action)
                
                if exit_code != 0:
                    self.output_formatter.format_warning(
                        f"Action '{action}' completed with errors"
                    )
                
                # Pause before returning to menu
                self.console.print()
                self.input_handler.prompt_for_confirmation(
                    "Press Enter to continue",
                    default=True
                )
                
            except KeyboardInterrupt:
                self.console.print("\n")
                if self.input_handler.prompt_for_confirmation(
                    "Return to main menu?",
                    default=True
                ):
                    continue
                else:
                    self.output_formatter.format_success("Goodbye!")
                    return 0
            except Exception as e:
                self.output_formatter.format_error(f"Unexpected error: {e}")
                self.input_handler.prompt_for_confirmation(
                    "Press Enter to continue",
                    default=True
                )
    
    def _display_welcome(self) -> None:
        """Display welcome message."""
        welcome_text = Text()
        welcome_text.append("Welcome to ", style="bold")
        welcome_text.append("Injekt CLI", style="bold cyan")
        welcome_text.append(" Interactive Mode\n\n", style="bold")
        welcome_text.append(
            "Manage video player configurations with ease.\n"
            "Select an action from the menu below."
        )
        
        panel = Panel(
            welcome_text,
            title="[bold cyan]Injekt CLI[/bold cyan]",
            border_style="cyan"
        )
        self.console.print(panel)
        self.console.print()
    
    def _display_main_menu(self) -> str:
        """
        Display main menu and get user selection.
        
        Returns:
            Selected action name
        """
        actions = [
            "List packages",
            "Install package",
            "Uninstall package",
            "Verify installation",
            "Show package info",
            "Generate report",
            "Rollback configuration",
            "Update package",
            "Manage profiles",
            "Export configuration",
            "Import configuration",
            "Exit"
        ]
        
        self.console.print("[bold cyan]Main Menu[/bold cyan]")
        self.console.print()
        
        choice = self.input_handler.prompt_for_choice(
            "What would you like to do?",
            choices=actions
        )
        
        self.console.print()
        return choice
    
    def _execute_action(self, action: str) -> int:
        """
        Execute the selected action with step-by-step prompts.
        
        Args:
            action: Action name to execute
            
        Returns:
            Exit code from the action
        """
        if action == "List packages":
            return self._action_list_packages()
        
        elif action == "Install package":
            return self._action_install_package()
        
        elif action == "Uninstall package":
            return self._action_uninstall_package()
        
        elif action == "Verify installation":
            return self._action_verify_installation()
        
        elif action == "Show package info":
            return self._action_show_package_info()
        
        elif action == "Generate report":
            return self._action_generate_report()
        
        elif action == "Rollback configuration":
            return self._action_rollback()
        
        elif action == "Update package":
            return self._action_update_package()
        
        elif action == "Manage profiles":
            return self._action_manage_profiles()
        
        elif action == "Export configuration":
            return self._action_export_configuration()
        
        elif action == "Import configuration":
            return self._action_import_configuration()
        
        else:
            self.output_formatter.format_error(f"Unknown action: {action}")
            return 1
    
    def _action_list_packages(self) -> int:
        """Execute list packages action."""
        self.console.print("[bold]Listing available packages...[/bold]\n")
        
        list_command = self.commands.get("list")
        if not list_command:
            self.output_formatter.format_error("List command not available")
            return 1
        
        return list_command.execute()
    
    def _action_install_package(self) -> int:
        """Execute install package action with step-by-step prompts."""
        self.console.print("[bold]Install Package Wizard[/bold]\n")
        
        # Step 1: Get package name
        package_name = self.input_handler.prompt_for_input(
            "Enter package name to install",
            validator=lambda x: len(x.strip()) > 0,
            error_message="Package name cannot be empty"
        )
        
        # Step 2: Confirm installation
        self.console.print(f"\n[bold]Summary:[/bold]")
        self.console.print(f"  Package: {package_name}")
        self.console.print()
        
        if not self.input_handler.prompt_for_confirmation(
            "Proceed with installation?",
            default=True
        ):
            self.output_formatter.format_warning("Installation cancelled")
            return 0
        
        # Step 3: Execute installation
        self.console.print()
        install_command = self.commands.get("install")
        if not install_command:
            self.output_formatter.format_error("Install command not available")
            return 1
        
        return install_command.execute(package_name)
    
    def _action_uninstall_package(self) -> int:
        """Execute uninstall package action with step-by-step prompts."""
        self.console.print("[bold]Uninstall Package Wizard[/bold]\n")
        
        # Step 1: Get package name
        package_name = self.input_handler.prompt_for_input(
            "Enter package name to uninstall",
            validator=lambda x: len(x.strip()) > 0,
            error_message="Package name cannot be empty"
        )
        
        # Step 2: Confirm uninstallation
        self.console.print(f"\n[bold]Summary:[/bold]")
        self.console.print(f"  Package: {package_name}")
        self.console.print(f"  Action: Uninstall (backup will be created)")
        self.console.print()
        
        if not self.input_handler.prompt_for_confirmation(
            "Proceed with uninstallation?",
            default=False
        ):
            self.output_formatter.format_warning("Uninstallation cancelled")
            return 0
        
        # Step 3: Execute uninstallation
        self.console.print()
        uninstall_command = self.commands.get("uninstall")
        if not uninstall_command:
            self.output_formatter.format_error("Uninstall command not available")
            return 1
        
        return uninstall_command.execute(package_name)
    
    def _action_verify_installation(self) -> int:
        """Execute verify installation action with step-by-step prompts."""
        self.console.print("[bold]Verify Installation Wizard[/bold]\n")
        
        # Step 1: Get package name
        package_name = self.input_handler.prompt_for_input(
            "Enter package name to verify",
            validator=lambda x: len(x.strip()) > 0,
            error_message="Package name cannot be empty"
        )
        
        # Step 2: Execute verification
        self.console.print()
        verify_command = self.commands.get("verify")
        if not verify_command:
            self.output_formatter.format_error("Verify command not available")
            return 1
        
        return verify_command.execute(package_name)
    
    def _action_show_package_info(self) -> int:
        """Execute show package info action with step-by-step prompts."""
        self.console.print("[bold]Package Information Wizard[/bold]\n")
        
        # Step 1: Get package name
        package_name = self.input_handler.prompt_for_input(
            "Enter package name",
            validator=lambda x: len(x.strip()) > 0,
            error_message="Package name cannot be empty"
        )
        
        # Step 2: Display info
        self.console.print()
        info_command = self.commands.get("info")
        if not info_command:
            self.output_formatter.format_error("Info command not available")
            return 1
        
        return info_command.execute(package_name)
    
    def _action_generate_report(self) -> int:
        """Execute generate report action."""
        self.console.print("[bold]Generating configuration report...[/bold]\n")
        
        report_command = self.commands.get("report")
        if not report_command:
            self.output_formatter.format_error("Report command not available")
            return 1
        
        return report_command.execute()
    
    def _action_rollback(self) -> int:
        """Execute rollback action."""
        self.console.print("[bold]Rollback Configuration Wizard[/bold]\n")
        
        rollback_command = self.commands.get("rollback")
        if not rollback_command:
            self.output_formatter.format_error("Rollback command not available")
            return 1
        
        return rollback_command.execute()
    
    def _action_update_package(self) -> int:
        """Execute update package action with step-by-step prompts."""
        self.console.print("[bold]Update Package Wizard[/bold]\n")
        
        # Step 1: Get package name
        package_name = self.input_handler.prompt_for_input(
            "Enter package name to update",
            validator=lambda x: len(x.strip()) > 0,
            error_message="Package name cannot be empty"
        )
        
        # Step 2: Execute update
        self.console.print()
        update_command = self.commands.get("update")
        if not update_command:
            self.output_formatter.format_error("Update command not available")
            return 1
        
        return update_command.execute(package_name)
    
    def _action_manage_profiles(self) -> int:
        """Execute manage profiles action with submenu."""
        self.console.print("[bold]Profile Management[/bold]\n")
        
        profile_actions = [
            "List profiles",
            "Switch profile",
            "Back to main menu"
        ]
        
        choice = self.input_handler.prompt_for_choice(
            "What would you like to do?",
            choices=profile_actions
        )
        
        self.console.print()
        
        if choice == "List profiles":
            profile_list_command = self.commands.get("profile_list")
            if not profile_list_command:
                self.output_formatter.format_error("Profile list command not available")
                return 1
            return profile_list_command.execute()
        
        elif choice == "Switch profile":
            # Get profile name
            profile_name = self.input_handler.prompt_for_input(
                "Enter profile name",
                validator=lambda x: len(x.strip()) > 0,
                error_message="Profile name cannot be empty"
            )
            
            self.console.print()
            profile_switch_command = self.commands.get("profile_switch")
            if not profile_switch_command:
                self.output_formatter.format_error("Profile switch command not available")
                return 1
            return profile_switch_command.execute(profile_name)
        
        else:  # Back to main menu
            return 0
    
    def _action_export_configuration(self) -> int:
        """Execute export configuration action with step-by-step prompts."""
        self.console.print("[bold]Export Configuration Wizard[/bold]\n")
        
        # Step 1: Get output directory
        output_dir = self.input_handler.prompt_for_path(
            "Enter export directory path",
            must_exist=False
        )
        
        # Step 2: Confirm export
        self.console.print(f"\n[bold]Summary:[/bold]")
        self.console.print(f"  Export to: {output_dir}")
        self.console.print()
        
        if not self.input_handler.prompt_for_confirmation(
            "Proceed with export?",
            default=True
        ):
            self.output_formatter.format_warning("Export cancelled")
            return 0
        
        # Step 3: Execute export
        self.console.print()
        export_command = self.commands.get("export")
        if not export_command:
            self.output_formatter.format_error("Export command not available")
            return 1
        
        return export_command.execute(output_dir)
    
    def _action_import_configuration(self) -> int:
        """Execute import configuration action with step-by-step prompts."""
        self.console.print("[bold]Import Configuration Wizard[/bold]\n")
        
        # Step 1: Get input directory
        input_dir = self.input_handler.prompt_for_path(
            "Enter directory containing configuration to import",
            must_exist=True,
            must_be_dir=True
        )
        
        # Step 2: Confirm import
        self.console.print(f"\n[bold]Summary:[/bold]")
        self.console.print(f"  Import from: {input_dir}")
        self.console.print()
        
        if not self.input_handler.prompt_for_confirmation(
            "Proceed with import?",
            default=True
        ):
            self.output_formatter.format_warning("Import cancelled")
            return 0
        
        # Step 3: Execute import
        self.console.print()
        import_command = self.commands.get("import")
        if not import_command:
            self.output_formatter.format_error("Import command not available")
            return 1
        
        return import_command.execute(input_dir)

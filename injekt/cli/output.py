"""Output formatting for CLI using Rich."""

import json
from typing import Any, List, Dict, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from injekt.core.result import Result, Success, Failure
from injekt.core.models import Package, PlayerType


class OutputFormatter:
    """Formats output for the CLI using Rich library."""
    
    def __init__(self, output_format: str = "text", console: Optional[Console] = None):
        """
        Initialize the output formatter.
        
        Args:
            output_format: Output format ("text", "json")
            console: Rich console instance (creates new one if None)
        """
        self.output_format = output_format
        self.console = console or Console()
    
    def format_result(self, result: Result, success_message: Optional[str] = None) -> None:
        """
        Format and display an operation result.
        
        Args:
            result: The result to format
            success_message: Optional custom success message
        """
        if isinstance(result, Success):
            if success_message:
                self.format_success(success_message)
            elif result.value is not None:
                self.format_success(str(result.value))
        elif isinstance(result, Failure):
            self.format_error(str(result.error))
    
    def format_success(self, message: str) -> None:
        """
        Format and display a success message.
        
        Args:
            message: Success message to display
        """
        if self.output_format == "json":
            self._print_json({"status": "success", "message": message})
        else:
            self.console.print(f"[green]✓[/green] {message}")
    
    def format_error(self, message: str) -> None:
        """
        Format and display an error message.
        
        Args:
            message: Error message to display
        """
        if self.output_format == "json":
            self._print_json({"status": "error", "message": message})
        else:
            self.console.print(f"[red]✗[/red] {message}", style="red")
    
    def format_warning(self, message: str) -> None:
        """
        Format and display a warning message.
        
        Args:
            message: Warning message to display
        """
        if self.output_format == "json":
            self._print_json({"status": "warning", "message": message})
        else:
            self.console.print(f"[yellow]⚠[/yellow] {message}", style="yellow")
    
    def format_table(
        self,
        data: List[Dict[str, Any]],
        columns: List[str],
        title: Optional[str] = None
    ) -> None:
        """
        Format and display data as a table.
        
        Args:
            data: List of dictionaries containing row data
            columns: List of column names to display
            title: Optional table title
        """
        if self.output_format == "json":
            self._print_json({"data": data})
        else:
            table = Table(title=title, show_header=True, header_style="bold cyan")
            
            # Add columns
            for column in columns:
                table.add_column(column)
            
            # Add rows
            for row in data:
                table.add_row(*[str(row.get(col, "")) for col in columns])
            
            self.console.print(table)
    
    def format_package_list(
        self,
        packages: List[Package],
        installed_packages: Optional[List[str]] = None
    ) -> None:
        """
        Format and display a list of packages.
        
        Args:
            packages: List of packages to display
            installed_packages: Optional list of installed package names
        """
        installed_set = set(installed_packages or [])
        
        if self.output_format == "json":
            package_data = [
                {
                    "name": pkg.name,
                    "description": pkg.description,
                    "player": pkg.player.value,
                    "version": pkg.version,
                    "installed": pkg.name in installed_set
                }
                for pkg in packages
            ]
            self._print_json({"packages": package_data})
        else:
            table = Table(
                title="Available Packages",
                show_header=True,
                header_style="bold cyan"
            )
            
            table.add_column("Name", style="cyan")
            table.add_column("Description")
            table.add_column("Player", style="magenta")
            table.add_column("Version", style="green")
            table.add_column("Status")
            
            for pkg in packages:
                status = "[green]Installed[/green]" if pkg.name in installed_set else ""
                table.add_row(
                    pkg.name,
                    pkg.description,
                    pkg.player.value.upper(),
                    pkg.version,
                    status
                )
            
            self.console.print(table)
    
    def format_info(self, title: str, content: Dict[str, Any]) -> None:
        """
        Format and display information as a panel.
        
        Args:
            title: Panel title
            content: Dictionary of information to display
        """
        if self.output_format == "json":
            self._print_json(content)
        else:
            text = Text()
            for key, value in content.items():
                text.append(f"{key}: ", style="bold")
                text.append(f"{value}\n")
            
            panel = Panel(text, title=title, border_style="cyan")
            self.console.print(panel)
    
    def _print_json(self, data: Any) -> None:
        """
        Print data as formatted JSON.
        
        Args:
            data: Data to print as JSON
        """
        self.console.print(json.dumps(data, indent=2, default=str))

"""Input handling for CLI using Rich prompts."""

from pathlib import Path
from typing import Optional, List, Callable, Any
from rich.console import Console
from rich.prompt import Prompt, Confirm


class InputHandler:
    """Handles user input for the CLI using Rich prompts."""
    
    def __init__(self, console: Optional[Console] = None):
        """
        Initialize the input handler.
        
        Args:
            console: Rich console instance (creates new one if None)
        """
        self.console = console or Console()
    
    def prompt_for_input(
        self,
        prompt: str,
        default: Optional[str] = None,
        validator: Optional[Callable[[str], bool]] = None,
        error_message: str = "Invalid input. Please try again."
    ) -> str:
        """
        Prompt user for text input with optional validation.
        
        Args:
            prompt: The prompt message to display
            default: Optional default value
            validator: Optional validation function that returns True if valid
            error_message: Error message to display on validation failure
            
        Returns:
            The validated user input
        """
        while True:
            value = Prompt.ask(prompt, default=default, console=self.console)
            
            if validator is None or validator(value):
                return value
            
            self.console.print(f"[red]{error_message}[/red]")
    
    def prompt_for_confirmation(
        self,
        prompt: str,
        default: bool = False
    ) -> bool:
        """
        Prompt user for yes/no confirmation.
        
        Args:
            prompt: The prompt message to display
            default: Default value if user just presses Enter
            
        Returns:
            True if user confirms, False otherwise
        """
        return Confirm.ask(prompt, default=default, console=self.console)
    
    def prompt_for_path(
        self,
        prompt: str,
        must_exist: bool = False,
        must_be_dir: bool = False,
        must_be_file: bool = False,
        default: Optional[str] = None
    ) -> Path:
        """
        Prompt user for a file system path with validation.
        
        Args:
            prompt: The prompt message to display
            must_exist: If True, path must exist
            must_be_dir: If True, path must be a directory
            must_be_file: If True, path must be a file
            default: Optional default path
            
        Returns:
            The validated Path object
        """
        def validate_path(path_str: str) -> bool:
            """Validate the path based on requirements."""
            try:
                path = Path(path_str).expanduser().resolve()
                
                if must_exist and not path.exists():
                    self.console.print(f"[red]Path does not exist: {path}[/red]")
                    return False
                
                if must_be_dir and path.exists() and not path.is_dir():
                    self.console.print(f"[red]Path is not a directory: {path}[/red]")
                    return False
                
                if must_be_file and path.exists() and not path.is_file():
                    self.console.print(f"[red]Path is not a file: {path}[/red]")
                    return False
                
                return True
            except Exception as e:
                self.console.print(f"[red]Invalid path: {e}[/red]")
                return False
        
        while True:
            path_str = Prompt.ask(prompt, default=default, console=self.console)
            if validate_path(path_str):
                return Path(path_str).expanduser().resolve()
    
    def prompt_for_choice(
        self,
        prompt: str,
        choices: List[str],
        default: Optional[str] = None
    ) -> str:
        """
        Prompt user to select from a list of choices.
        
        Args:
            prompt: The prompt message to display
            choices: List of valid choices
            default: Optional default choice
            
        Returns:
            The selected choice
        """
        # Display choices
        self.console.print(f"\n{prompt}")
        for i, choice in enumerate(choices, 1):
            self.console.print(f"  {i}. {choice}")
        
        # Validate that input is either a number or matches a choice
        def validate_choice(value: str) -> bool:
            """Validate the choice input."""
            # Check if it's a number
            if value.isdigit():
                index = int(value) - 1
                if 0 <= index < len(choices):
                    return True
            
            # Check if it matches a choice exactly
            if value in choices:
                return True
            
            self.console.print(
                f"[red]Invalid choice. Please enter a number (1-{len(choices)}) "
                f"or one of: {', '.join(choices)}[/red]"
            )
            return False
        
        while True:
            value = Prompt.ask(
                "Enter your choice",
                default=default,
                console=self.console
            )
            
            if validate_choice(value):
                # If it's a number, return the corresponding choice
                if value.isdigit():
                    return choices[int(value) - 1]
                # Otherwise return the value itself
                return value

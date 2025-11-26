# Design Document: Professional CLI Architecture Standard

## Overview

This design document specifies a standardized architecture for building professional command-line interface (CLI) applications. It provides reusable patterns, interfaces, and structures that ensure consistency, maintainability, and testability across all CLI projects.

### Core Principles

1. **Separation of Concerns** - Clear boundaries between CLI, business logic, and I/O
2. **Dependency Injection** - All dependencies injected, enabling testing and flexibility
3. **Fail Fast** - Invalid data causes immediate exceptions, not silent failures
4. **Single Responsibility** - Each class has one reason to change
5. **Open/Closed** - Open for extension, closed for modification
6. **Interface Segregation** - Clients depend only on interfaces they use
7. **Dependency Inversion** - Depend on abstractions, not concretions

### Standard Module Structure

```
<app_name>/
├── core/
│   ├── __init__.py
│   ├── interfaces.py      # All interface definitions
│   ├── result.py          # Result types
│   ├── validation.py      # Input validation
│   ├── errors.py          # Exception hierarchy
│   └── constants.py       # Named constants
├── io/
│   ├── __init__.py
│   └── <io_operations>.py # I/O abstractions (file, network, db, etc.)
├── business/
│   ├── __init__.py
│   └── <domain_logic>.py  # Business logic modules
├── cli/
│   ├── __init__.py
│   ├── commands.py        # Command handlers
│   ├── output.py          # Output formatting
│   ├── input.py           # Input handling
│   └── app.py             # CLI framework configuration
└── config.py              # Configuration management
```

## Architecture

### Layered Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     CLI Layer                           │
│  - Command handlers                                     │
│  - Input validation                                     │
│  - Output formatting                                    │
│  - User interaction                                     │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                  Business Logic Layer                   │
│  - Domain operations                                    │
│  - Business rules                                       │
│  - Data transformations                                 │
│  - Workflow orchestration                               │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                      I/O Layer                          │
│  - File operations                                      │
│  - Network operations                                   │
│  - Database operations                                  │
│  - External service integration                         │
└─────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### Core Interfaces Template

```python
# <app_name>/core/interfaces.py

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Protocol, TypeVar, Generic
from .result import Result

T = TypeVar('T')

class BusinessOperation(Protocol[T]):
    """Interface for business operations."""
    
    def execute(self, *args, **kwargs) -> Result[T]:
        """Execute the business operation."""
        ...


class IOOperation(Protocol[T]):
    """Interface for I/O operations."""
    
    def read(self, *args, **kwargs) -> Result[T]:
        """Read data from external source."""
        ...
    
    def write(self, data: T, *args, **kwargs) -> Result[None]:
        """Write data to external destination."""
        ...


class Validator(Protocol[T]):
    """Interface for input validation."""
    
    def validate(self, value: any) -> Result[T]:
        """Validate and convert input value."""
        ...


class Formatter(Protocol[T]):
    """Interface for output formatting."""
    
    def format(self, data: T) -> str:
        """Format data for display."""
        ...
```

### Result Types Template

```python
# <app_name>/core/result.py

from dataclasses import dataclass
from typing import Generic, TypeVar, Union
from .errors import AppError

T = TypeVar('T')

@dataclass(frozen=True)
class Success(Generic[T]):
    """Successful operation result."""
    value: T
    
    def is_success(self) -> bool:
        return True
    
    def is_failure(self) -> bool:
        return False
    
    def unwrap(self) -> T:
        return self.value
    
    def unwrap_or(self, default: T) -> T:
        return self.value
    
    def map(self, func):
        """Transform the success value."""
        return Success(func(self.value))


@dataclass(frozen=True)
class Failure(Generic[T]):
    """Failed operation result."""
    error: AppError
    
    def is_success(self) -> bool:
        return False
    
    def is_failure(self) -> bool:
        return True
    
    def unwrap(self) -> T:
        raise self.error
    
    def unwrap_or(self, default: T) -> T:
        return default
    
    def map(self, func):
        """Pass through failure unchanged."""
        return self


Result = Union[Success[T], Failure[T]]


@dataclass
class OperationResult:
    """Result of a CLI operation."""
    success: bool
    message: str
    data: dict[str, any] | None = None
    errors: list[AppError] | None = None
    warnings: list[AppError] | None = None
    
    @property
    def has_errors(self) -> bool:
        """Check if operation had errors."""
        return self.errors is not None and len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        """Check if operation had warnings."""
        return self.warnings is not None and len(self.warnings) > 0
```

### Error Hierarchy Template

```python
# <app_name>/core/errors.py

class AppError(Exception):
    """Base exception for all application errors."""
    
    def __init__(self, message: str, context: dict[str, any] | None = None):
        super().__init__(message)
        self.message = message
        self.context = context or {}
    
    def __str__(self) -> str:
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{self.message} ({context_str})"
        return self.message


class ValidationError(AppError):
    """Input validation failed."""
    pass


class ConfigurationError(AppError):
    """Configuration is invalid."""
    pass


class OperationError(AppError):
    """Operation failed."""
    pass


class IOError(AppError):
    """I/O operation failed."""
    pass


class BusinessLogicError(AppError):
    """Business logic constraint violated."""
    pass
```

### Constants Template

```python
# <app_name>/core/constants.py

from enum import Enum

# Exit codes
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_INVALID_INPUT = 2
EXIT_USER_CANCELLED = 130
EXIT_CONFIG_ERROR = 3

# Default limits
MAX_ITEMS_DISPLAY = 100
DEFAULT_TIMEOUT_SECONDS = 30

# Configuration keys
CONFIG_KEY_VERBOSE = "verbose"
CONFIG_KEY_DRY_RUN = "dry_run"
CONFIG_KEY_OUTPUT_FORMAT = "output_format"

class OperationStatus(Enum):
    """Status of an operation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ErrorSeverity(Enum):
    """Severity level of an error."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class OutputFormat(Enum):
    """Output format options."""
    TEXT = "text"
    JSON = "json"
    TABLE = "table"
    CSV = "csv"
```

### Validation Module Template

```python
# <app_name>/core/validation.py

from pathlib import Path
from typing import TypeVar, Callable
from .result import Result, Success, Failure
from .errors import ValidationError

T = TypeVar('T')

def validate_not_empty(value: str, field_name: str) -> Result[str]:
    """Validate string is not empty."""
    if not value or not value.strip():
        return Failure(ValidationError(
            f"{field_name} cannot be empty",
            context={"field": field_name}
        ))
    return Success(value.strip())


def validate_path_exists(path: Path, field_name: str) -> Result[Path]:
    """Validate path exists."""
    if not path.exists():
        return Failure(ValidationError(
            f"{field_name} does not exist",
            context={"field": field_name, "path": str(path)}
        ))
    return Success(path)


def validate_in_range(value: int, min_val: int, max_val: int, field_name: str) -> Result[int]:
    """Validate value is within range."""
    if value < min_val or value > max_val:
        return Failure(ValidationError(
            f"{field_name} must be between {min_val} and {max_val}",
            context={"field": field_name, "value": value, "min": min_val, "max": max_val}
        ))
    return Success(value)


def validate_one_of(value: str, options: list[str], field_name: str) -> Result[str]:
    """Validate value is one of allowed options."""
    if value not in options:
        return Failure(ValidationError(
            f"{field_name} must be one of: {', '.join(options)}",
            context={"field": field_name, "value": value, "options": options}
        ))
    return Success(value)


def chain_validators(*validators: Callable[[T], Result[T]]) -> Callable[[T], Result[T]]:
    """Chain multiple validators together."""
    def validate(value: T) -> Result[T]:
        result = Success(value)
        for validator in validators:
            if result.is_failure():
                return result
            result = validator(result.unwrap())
        return result
    return validate
```

## CLI Layer Components

### Command Handler Template

```python
# <app_name>/cli/commands.py

from dataclasses import dataclass
from typing import Protocol
from ..core.result import Result, OperationResult
from ..core.errors import AppError
from ..business.<domain> import <BusinessOperation>
from .output import OutputFormatter
from .input import InputHandler


class Command(Protocol):
    """Interface for CLI commands."""
    
    def execute(self) -> OperationResult:
        """Execute the command."""
        ...


@dataclass
class BaseCommand:
    """Base class for commands with common functionality."""
    output_formatter: OutputFormatter
    input_handler: InputHandler
    verbose: bool = False
    dry_run: bool = False
    
    def handle_error(self, error: AppError) -> OperationResult:
        """Handle command error consistently."""
        return OperationResult(
            success=False,
            message=str(error),
            errors=[error]
        )
    
    def handle_success(self, message: str, data: dict | None = None) -> OperationResult:
        """Handle command success consistently."""
        return OperationResult(
            success=True,
            message=message,
            data=data
        )


class ExampleCommand(BaseCommand):
    """Example command implementation."""
    
    def __init__(
        self,
        business_operation: <BusinessOperation>,
        output_formatter: OutputFormatter,
        input_handler: InputHandler,
        verbose: bool = False,
        dry_run: bool = False,
    ):
        super().__init__(output_formatter, input_handler, verbose, dry_run)
        self.business_operation = business_operation
    
    def execute(self) -> OperationResult:
        """Execute the example command."""
        try:
            # Get and validate input
            input_result = self.input_handler.prompt_for_input("Enter value")
            if input_result.is_failure():
                return self.handle_error(input_result.error)
            
            # Execute business logic
            if self.dry_run:
                return self.handle_success("Dry run: would execute operation")
            
            result = self.business_operation.execute(input_result.unwrap())
            
            if result.is_failure():
                return self.handle_error(result.error)
            
            # Format and return success
            return self.handle_success(
                "Operation completed successfully",
                data={"result": result.unwrap()}
            )
        
        except Exception as e:
            return self.handle_error(AppError(f"Unexpected error: {e}"))
```

### Output Formatter Template

```python
# <app_name>/cli/output.py

from typing import Protocol
from rich.console import Console
from rich.table import Table
import json
from ..core.result import OperationResult
from ..core.errors import AppError
from ..core.constants import OutputFormat


class OutputFormatter:
    """Handles output formatting for CLI."""
    
    def __init__(self, console: Console, format: OutputFormat = OutputFormat.TEXT):
        self.console = console
        self.format = format
    
    def format_result(self, result: OperationResult) -> None:
        """Format and display operation result."""
        if result.success:
            self.format_success(result.message, result.data)
        else:
            self.format_error(result.message, result.errors)
        
        if result.has_warnings:
            for warning in result.warnings:
                self.format_warning(str(warning))
    
    def format_success(self, message: str, data: dict | None = None) -> None:
        """Format success message."""
        if self.format == OutputFormat.JSON:
            self.console.print(json.dumps({"status": "success", "message": message, "data": data}))
        else:
            self.console.print(f"[green]✓[/green] {message}")
            if data and self.format == OutputFormat.TEXT:
                self._format_data_text(data)
    
    def format_error(self, message: str, errors: list[AppError] | None = None) -> None:
        """Format error message."""
        if self.format == OutputFormat.JSON:
            error_data = [{"message": str(e), "context": e.context} for e in (errors or [])]
            self.console.print(json.dumps({"status": "error", "message": message, "errors": error_data}))
        else:
            self.console.print(f"[red]✗[/red] {message}", style="bold red")
            if errors:
                for error in errors:
                    self.console.print(f"  • {error}")
    
    def format_warning(self, message: str) -> None:
        """Format warning message."""
        if self.format == OutputFormat.JSON:
            self.console.print(json.dumps({"status": "warning", "message": message}))
        else:
            self.console.print(f"[yellow]⚠[/yellow] {message}")
    
    def format_info(self, message: str) -> None:
        """Format info message."""
        if self.format == OutputFormat.JSON:
            self.console.print(json.dumps({"status": "info", "message": message}))
        else:
            self.console.print(f"[blue]ℹ[/blue] {message}")
    
    def format_table(self, headers: list[str], rows: list[list[str]]) -> None:
        """Format data as table."""
        if self.format == OutputFormat.JSON:
            data = [dict(zip(headers, row)) for row in rows]
            self.console.print(json.dumps(data))
        elif self.format == OutputFormat.CSV:
            import csv
            import sys
            writer = csv.writer(sys.stdout)
            writer.writerow(headers)
            writer.writerows(rows)
        else:
            table = Table()
            for header in headers:
                table.add_column(header)
            for row in rows:
                table.add_row(*row)
            self.console.print(table)
    
    def _format_data_text(self, data: dict) -> None:
        """Format data dictionary as text."""
        for key, value in data.items():
            self.console.print(f"  {key}: {value}")
```

### Input Handler Template

```python
# <app_name>/cli/input.py

from pathlib import Path
from typing import Callable
from rich.console import Console
from rich.prompt import Prompt, Confirm
from ..core.result import Result, Success, Failure
from ..core.validation import validate_not_empty
from ..core.errors import ValidationError


class InputHandler:
    """Handles user input for CLI."""
    
    def __init__(self, console: Console):
        self.console = console
    
    def prompt_for_input(
        self,
        prompt: str,
        default: str | None = None,
        validator: Callable[[str], Result[str]] | None = None
    ) -> Result[str]:
        """Prompt user for input with optional validation."""
        while True:
            try:
                value = Prompt.ask(prompt, default=default, console=self.console)
                
                if validator:
                    result = validator(value)
                    if result.is_failure():
                        self.console.print(f"[red]{result.error}[/red]")
                        continue
                    return result
                
                return Success(value)
            
            except KeyboardInterrupt:
                return Failure(ValidationError("Input cancelled by user"))
    
    def prompt_for_confirmation(
        self,
        prompt: str,
        default: bool = False
    ) -> bool:
        """Prompt user for yes/no confirmation."""
        try:
            return Confirm.ask(prompt, default=default, console=self.console)
        except KeyboardInterrupt:
            return False
    
    def prompt_for_path(
        self,
        prompt: str,
        must_exist: bool = False,
        default: Path | None = None
    ) -> Result[Path]:
        """Prompt user for file/directory path."""
        def validate_path(value: str) -> Result[Path]:
            path = Path(value)
            if must_exist and not path.exists():
                return Failure(ValidationError(
                    f"Path does not exist: {value}",
                    context={"path": value}
                ))
            return Success(path)
        
        default_str = str(default) if default else None
        result = self.prompt_for_input(prompt, default=default_str, validator=validate_path)
        
        if result.is_success():
            return Success(Path(result.unwrap()))
        return result
    
    def prompt_for_choice(
        self,
        prompt: str,
        choices: list[str],
        default: str | None = None
    ) -> Result[str]:
        """Prompt user to select from choices."""
        choices_str = "/".join(choices)
        full_prompt = f"{prompt} [{choices_str}]"
        
        def validate_choice(value: str) -> Result[str]:
            if value not in choices:
                return Failure(ValidationError(
                    f"Invalid choice. Must be one of: {', '.join(choices)}",
                    context={"value": value, "choices": choices}
                ))
            return Success(value)
        
        return self.prompt_for_input(full_prompt, default=default, validator=validate_choice)
```

### CLI Application Template

```python
# <app_name>/cli/app.py

import typer
from rich.console import Console
from typing import Optional
from ..core.constants import EXIT_SUCCESS, EXIT_ERROR, EXIT_INVALID_INPUT, OutputFormat
from ..core.errors import ValidationError, ConfigurationError
from .commands import ExampleCommand
from .output import OutputFormatter
from .input import InputHandler
from ..business.<domain> import <BusinessOperation>
from ..io.<io_operations> import <IOOperations>

app = typer.Typer(
    name="<app_name>",
    help="<Application description>",
    add_completion=False,
)

# Global state for dependency injection
console = Console()


def version_callback(value: bool):
    """Display version information."""
    if value:
        console.print("<app_name> version 1.0.0")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
):
    """
    <Application name> - <Brief description>
    """
    pass


@app.command()
def example(
    input_value: str = typer.Argument(..., help="Input value for operation"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Simulate without making changes"),
    output_format: str = typer.Option("text", "--format", "-f", help="Output format (text/json/table)"),
):
    """
    Example command that demonstrates the CLI pattern.
    
    This command shows how to:
    - Accept arguments and options
    - Inject dependencies
    - Execute business logic
    - Handle errors
    - Format output
    """
    try:
        # Parse output format
        try:
            fmt = OutputFormat(output_format)
        except ValueError:
            console.print(f"[red]Invalid output format: {output_format}[/red]")
            raise typer.Exit(EXIT_INVALID_INPUT)
        
        # Create dependencies
        output_formatter = OutputFormatter(console, fmt)
        input_handler = InputHandler(console)
        io_operations = <IOOperations>()
        business_operation = <BusinessOperation>(io_operations)
        
        # Create and execute command
        command = ExampleCommand(
            business_operation=business_operation,
            output_formatter=output_formatter,
            input_handler=input_handler,
            verbose=verbose,
            dry_run=dry_run,
        )
        
        result = command.execute()
        
        # Display result
        output_formatter.format_result(result)
        
        # Exit with appropriate code
        raise typer.Exit(EXIT_SUCCESS if result.success else EXIT_ERROR)
    
    except ValidationError as e:
        console.print(f"[red]Validation error: {e}[/red]")
        raise typer.Exit(EXIT_INVALID_INPUT)
    
    except ConfigurationError as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        raise typer.Exit(EXIT_ERROR)
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        raise typer.Exit(130)
    
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        if verbose:
            console.print_exception()
        raise typer.Exit(EXIT_ERROR)


if __name__ == "__main__":
    app()
```

## Business Logic Layer Template

```python
# <app_name>/business/<domain>.py

from dataclasses import dataclass
from typing import Protocol
from ..core.result import Result, Success, Failure
from ..core.errors import BusinessLogicError
from ..io.<io_operations> import <IOOperations>


class <BusinessOperation>:
    """Business logic for <domain operation>."""
    
    def __init__(self, io_operations: <IOOperations>):
        self.io_operations = io_operations
    
    def execute(self, input_data: any) -> Result[any]:
        """
        Execute the business operation.
        
        Args:
            input_data: Input data for the operation
        
        Returns:
            Result containing output data or error
        """
        try:
            # Validate business rules
            validation_result = self._validate_business_rules(input_data)
            if validation_result.is_failure():
                return validation_result
            
            # Perform I/O operations
            io_result = self.io_operations.read(input_data)
            if io_result.is_failure():
                return io_result
            
            # Transform data according to business logic
            transformed_data = self._transform_data(io_result.unwrap())
            
            # Write results
            write_result = self.io_operations.write(transformed_data)
            if write_result.is_failure():
                return write_result
            
            return Success(transformed_data)
        
        except Exception as e:
            return Failure(BusinessLogicError(
                f"Business operation failed: {e}",
                context={"input": input_data}
            ))
    
    def _validate_business_rules(self, data: any) -> Result[None]:
        """Validate business rules."""
        # Implement business rule validation
        return Success(None)
    
    def _transform_data(self, data: any) -> any:
        """Transform data according to business logic."""
        # Implement data transformation
        return data
```

## I/O Layer Template

```python
# <app_name>/io/<io_operations>.py

from pathlib import Path
from typing import Protocol
from ..core.result import Result, Success, Failure
from ..core.errors import IOError


class <IOOperations>:
    """I/O operations for <resource type>."""
    
    def read(self, source: any) -> Result[any]:
        """
        Read data from source.
        
        Args:
            source: Source to read from
        
        Returns:
            Result containing data or error
        """
        try:
            # Implement read operation
            data = self._perform_read(source)
            return Success(data)
        
        except FileNotFoundError as e:
            return Failure(IOError(
                f"Source not found: {source}",
                context={"source": str(source), "error": str(e)}
            ))
        
        except PermissionError as e:
            return Failure(IOError(
                f"Permission denied: {source}",
                context={"source": str(source), "error": str(e)}
            ))
        
        except Exception as e:
            return Failure(IOError(
                f"Read operation failed: {e}",
                context={"source": str(source), "error": str(e)}
            ))
    
    def write(self, data: any, destination: any = None) -> Result[None]:
        """
        Write data to destination.
        
        Args:
            data: Data to write
            destination: Destination to write to
        
        Returns:
            Result indicating success or error
        """
        try:
            # Implement write operation
            self._perform_write(data, destination)
            return Success(None)
        
        except PermissionError as e:
            return Failure(IOError(
                f"Permission denied: {destination}",
                context={"destination": str(destination), "error": str(e)}
            ))
        
        except Exception as e:
            return Failure(IOError(
                f"Write operation failed: {e}",
                context={"destination": str(destination), "error": str(e)}
            ))
    
    def _perform_read(self, source: any) -> any:
        """Perform the actual read operation."""
        # Implement specific read logic
        raise NotImplementedError
    
    def _perform_write(self, data: any, destination: any) -> None:
        """Perform the actual write operation."""
        # Implement specific write logic
        raise NotImplementedError
```

## Configuration Management Template

```python
# <app_name>/config.py

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import os
import json
from .core.result import Result, Success, Failure
from .core.errors import ConfigurationError


@dataclass
class AppConfig:
    """Application configuration."""
    verbose: bool = False
    dry_run: bool = False
    output_format: str = "text"
    # Add application-specific config fields
    
    @classmethod
    def from_file(cls, path: Path) -> Result['AppConfig']:
        """Load configuration from file."""
        try:
            if not path.exists():
                return Success(cls())  # Use defaults
            
            with open(path, 'r') as f:
                data = json.load(f)
            
            # Validate configuration
            validation_result = cls._validate_config(data)
            if validation_result.is_failure():
                return validation_result
            
            return Success(cls(**data))
        
        except json.JSONDecodeError as e:
            return Failure(ConfigurationError(
                f"Invalid JSON in config file: {e}",
                context={"path": str(path)}
            ))
        
        except Exception as e:
            return Failure(ConfigurationError(
                f"Failed to load config: {e}",
                context={"path": str(path)}
            ))
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        """Load configuration from environment variables."""
        return cls(
            verbose=os.getenv('APP_VERBOSE', 'false').lower() == 'true',
            dry_run=os.getenv('APP_DRY_RUN', 'false').lower() == 'true',
            output_format=os.getenv('APP_OUTPUT_FORMAT', 'text'),
        )
    
    @classmethod
    def merge(cls, *configs: 'AppConfig') -> 'AppConfig':
        """Merge multiple configurations (later configs override earlier)."""
        result = cls()
        for config in configs:
            for field in result.__dataclass_fields__:
                value = getattr(config, field)
                if value is not None:
                    setattr(result, field, value)
        return result
    
    @staticmethod
    def _validate_config(data: dict) -> Result[None]:
        """Validate configuration data."""
        # Implement configuration validation
        valid_formats = ['text', 'json', 'table', 'csv']
        if 'output_format' in data and data['output_format'] not in valid_formats:
            return Failure(ConfigurationError(
                f"Invalid output format: {data['output_format']}",
                context={"valid_formats": valid_formats}
            ))
        
        return Success(None)
```

## Testing Strategy

### Unit Testing Template

```python
# tests/test_<module>.py

import pytest
from unittest.mock import Mock, MagicMock
from <app_name>.business.<domain> import <BusinessOperation>
from <app_name>.core.result import Success, Failure
from <app_name>.core.errors import BusinessLogicError


class Test<BusinessOperation>:
    """Unit tests for <BusinessOperation>."""
    
    @pytest.fixture
    def mock_io_operations(self):
        """Create mock I/O operations."""
        return Mock()
    
    @pytest.fixture
    def business_operation(self, mock_io_operations):
        """Create business operation with mocked dependencies."""
        return <BusinessOperation>(mock_io_operations)
    
    def test_execute_success(self, business_operation, mock_io_operations):
        """Test successful execution."""
        # Arrange
        mock_io_operations.read.return_value = Success("test data")
        mock_io_operations.write.return_value = Success(None)
        
        # Act
        result = business_operation.execute("input")
        
        # Assert
        assert result.is_success()
        assert mock_io_operations.read.called
        assert mock_io_operations.write.called
    
    def test_execute_io_failure(self, business_operation, mock_io_operations):
        """Test execution with I/O failure."""
        # Arrange
        error = IOError("Read failed")
        mock_io_operations.read.return_value = Failure(error)
        
        # Act
        result = business_operation.execute("input")
        
        # Assert
        assert result.is_failure()
        assert result.error == error
    
    def test_execute_validation_failure(self, business_operation):
        """Test execution with validation failure."""
        # Act
        result = business_operation.execute(None)  # Invalid input
        
        # Assert
        assert result.is_failure()
        assert isinstance(result.error, BusinessLogicError)
```

### Integration Testing Template

```python
# tests/integration/test_<feature>_integration.py

import pytest
from pathlib import Path
import tempfile
import shutil
from <app_name>.cli.app import app
from typer.testing import CliRunner


class Test<Feature>Integration:
    """Integration tests for <feature>."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()
    
    def test_command_success(self, runner, temp_dir):
        """Test successful command execution."""
        # Arrange
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        
        # Act
        result = runner.invoke(app, ["example", str(test_file)])
        
        # Assert
        assert result.exit_code == 0
        assert "success" in result.stdout.lower()
    
    def test_command_with_invalid_input(self, runner):
        """Test command with invalid input."""
        # Act
        result = runner.invoke(app, ["example", "nonexistent.txt"])
        
        # Assert
        assert result.exit_code != 0
        assert "error" in result.stdout.lower()
    
    def test_command_dry_run(self, runner, temp_dir):
        """Test command in dry-run mode."""
        # Arrange
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        
        # Act
        result = runner.invoke(app, ["example", str(test_file), "--dry-run"])
        
        # Assert
        assert result.exit_code == 0
        assert "dry run" in result.stdout.lower()
    
    def test_command_verbose_output(self, runner, temp_dir):
        """Test command with verbose output."""
        # Arrange
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        
        # Act
        result = runner.invoke(app, ["example", str(test_file), "--verbose"])
        
        # Assert
        assert result.exit_code == 0
        # Verify verbose output contains additional details
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Layer Separation
*For any* CLI command, it should not directly access I/O operations; it should call business logic
**Validates: Requirements 2.1, 2.2, 2.3**

### Property 2: Error Propagation
*For any* invalid input, the system should raise an exception immediately, not return partial results
**Validates: Requirements 3.1, 3.2, 3.3**

### Property 3: Type Consistency
*For any* function with type hints, mypy should report zero type errors
**Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**

### Property 4: Dependency Injection
*For any* component with dependencies, those dependencies should be injected via constructor
**Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**

### Property 5: Configuration Validation
*For any* configuration file, loading should validate all fields before use
**Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5**

### Property 6: Result Type Usage
*For any* operation that can fail, it should return a Result type, not raise exceptions
**Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5**

### Property 7: Exit Code Consistency
*For any* CLI execution, the exit code should match the operation outcome
**Validates: Requirements 17.1, 17.2, 17.3, 17.4, 17.5**

### Property 8: Code Duplication Elimination
*For any* two functions in the codebase, if they perform the same operation, they should call a shared implementation
**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5**

## Error Handling Strategy

### Error Classification

1. **CRITICAL** - Prevents operation from completing
   - Configuration errors
   - Invalid input
   - I/O failures

2. **WARNING** - Doesn't prevent operation
   - Deprecated feature usage
   - Non-critical validation failures
   - Performance warnings

3. **INFO** - Informational only
   - Operation progress
   - Debug information

### Error Recovery

- **CRITICAL**: Display error, provide guidance, exit with error code
- **WARNING**: Display warning, continue operation
- **INFO**: Display info if verbose mode enabled

### Error Context

All errors include:
- Error message
- Context dictionary with relevant details
- Stack trace (in debug/verbose mode)

## Performance Considerations

- Use generators for large data sets
- Implement progress indicators for long operations
- Cache expensive computations
- Use async I/O where appropriate
- Profile critical paths

## Security Considerations

- Validate all user input
- Sanitize file paths
- Check permissions before operations
- Don't expose sensitive data in errors
- Use secure defaults

## Documentation Standards

### Module Docstrings
```python
"""
Module description.

This module provides <functionality>.

Example:
    >>> from <app_name>.<module> import <Class>
    >>> obj = <Class>()
    >>> result = obj.method()
"""
```

### Class Docstrings
```python
class Example:
    """
    Brief description.
    
    Longer description explaining the class purpose,
    responsibilities, and usage patterns.
    
    Attributes:
        attr1: Description of attribute
        attr2: Description of attribute
    
    Example:
        >>> example = Example(attr1="value")
        >>> result = example.method()
    """
```

### Function Docstrings
```python
def function(param1: str, param2: int) -> Result[str]:
    """
    Brief description.
    
    Longer description explaining what the function does,
    any important behavior, and edge cases.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        Result containing string or error
    
    Raises:
        ValidationError: When input is invalid
        ConfigurationError: When configuration is missing
    
    Example:
        >>> result = function("test", 42)
        >>> if result.is_success():
        ...     print(result.unwrap())
    """
```

## Migration Guide

### Adapting This Template

1. **Replace placeholders**:
   - `<app_name>` → Your application name
   - `<domain>` → Your domain/feature name
   - `<BusinessOperation>` → Your business operation class name
   - `<IOOperations>` → Your I/O operations class name

2. **Add domain-specific modules**:
   - Create business logic modules in `business/`
   - Create I/O modules in `io/`
   - Add domain-specific errors to `core/errors.py`
   - Add domain-specific constants to `core/constants.py`

3. **Implement commands**:
   - Create command classes in `cli/commands.py`
   - Add Typer command functions in `cli/app.py`
   - Inject dependencies appropriately

4. **Add tests**:
   - Unit tests for each module
   - Integration tests for workflows
   - Property-based tests for correctness

5. **Configure tooling**:
   - Set up mypy configuration
   - Set up ruff/pylint configuration
   - Set up black configuration
   - Set up pre-commit hooks
   - Set up CI/CD pipeline

## Future Extensions

- Plugin system for extensibility
- Configuration profiles
- Shell completion
- Interactive mode
- Batch processing
- Parallel execution
- Remote operations
- Caching layer

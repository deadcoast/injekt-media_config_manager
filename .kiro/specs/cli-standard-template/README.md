# Professional CLI Architecture Standard Template

## Overview

This is a **reusable template** for building professional command-line interface (CLI) applications with industry-standard architecture, based on the architectural-unification spec from the scrubb project.

**Purpose**: Use this template as a foundation for any new CLI project to ensure consistency, maintainability, and professional code standards.

## What This Template Provides

### 1. **Standardized Architecture**
- **3-Layer Architecture**: CLI → Business Logic → I/O
- **Clear Separation of Concerns**: Each layer has distinct responsibilities
- **Dependency Injection**: All components are testable in isolation
- **Protocol-Based Interfaces**: Flexible, extensible design

### 2. **Core Components**
- **Result Types**: Explicit success/failure handling (no exceptions for control flow)
- **Error Hierarchy**: Structured error types with context
- **Validation Module**: Reusable validation functions
- **Constants**: Named constants for exit codes, formats, etc.

### 3. **CLI Layer**
- **Command Pattern**: Consistent command structure
- **Input Handling**: Prompts, validation, confirmation
- **Output Formatting**: Multiple formats (text, JSON, table, CSV)
- **Verbosity Control**: Quiet, normal, verbose, debug modes

### 4. **Business Logic Layer**
- **Pure Business Logic**: No I/O, no CLI dependencies
- **Testable**: Easy to unit test with mocked dependencies
- **Reusable**: Can be used from CLI, API, or other interfaces

### 5. **I/O Layer**
- **Abstracted I/O**: File, network, database operations
- **Result-Based**: All operations return Result types
- **Error Handling**: Specific error types with context

### 6. **Testing Standards**
- **Unit Tests**: Test each component in isolation
- **Integration Tests**: Test complete workflows
- **Property-Based Tests**: Verify correctness properties
- **High Coverage**: >80% code coverage target

### 7. **Quality Standards**
- **Type Hints**: Full type coverage, mypy compliant
- **Documentation**: Comprehensive docstrings
- **Code Quality**: Linting, formatting, security checks
- **CI/CD Ready**: Pre-commit hooks, GitHub Actions

## How to Use This Template

### Step 1: Copy the Template Structure

```bash
# Create your new project
mkdir my-cli-app
cd my-cli-app

# Copy the template structure
<app_name>/
├── core/
│   ├── __init__.py
│   ├── interfaces.py
│   ├── result.py
│   ├── validation.py
│   ├── errors.py
│   └── constants.py
├── io/
│   ├── __init__.py
│   └── <io_operations>.py
├── business/
│   ├── __init__.py
│   └── <domain_logic>.py
├── cli/
│   ├── __init__.py
│   ├── commands.py
│   ├── output.py
│   ├── input.py
│   └── app.py
└── config.py
```

### Step 2: Replace Placeholders

Search and replace these placeholders throughout the template:

- `<app_name>` → Your application name (e.g., `myapp`)
- `<domain>` → Your domain/feature name (e.g., `tasks`, `files`, `users`)
- `<BusinessOperation>` → Your business operation class (e.g., `TaskManager`, `FileProcessor`)
- `<IOOperations>` → Your I/O operations class (e.g., `FileOperations`, `DatabaseOperations`)

### Step 3: Implement Your Domain Logic

1. **Define your domain models** in `business/<domain>.py`
2. **Implement business operations** following the template pattern
3. **Create I/O operations** in `io/<io_operations>.py`
4. **Add domain-specific errors** to `core/errors.py`
5. **Add domain-specific constants** to `core/constants.py`

### Step 4: Create CLI Commands

1. **Implement command classes** in `cli/commands.py`
2. **Add Typer command functions** in `cli/app.py`
3. **Inject dependencies** into commands
4. **Use OutputFormatter** for consistent output
5. **Use InputHandler** for user input

### Step 5: Add Tests

1. **Unit tests** for business logic (mock I/O)
2. **Unit tests** for I/O operations (use test doubles)
3. **Unit tests** for CLI commands (mock business logic)
4. **Integration tests** for complete workflows
5. **Property-based tests** for correctness properties

### Step 6: Configure Tooling

1. **mypy**: Type checking configuration
2. **ruff/pylint**: Linting configuration
3. **black**: Code formatting
4. **bandit**: Security scanning
5. **pre-commit**: Git hooks
6. **GitHub Actions**: CI/CD pipeline

## Example: Building a Task Manager CLI

### 1. Define Domain Model

```python
# myapp/business/tasks.py

from dataclasses import dataclass
from datetime import datetime
from ..core.result import Result, Success, Failure
from ..core.errors import BusinessLogicError
from ..io.task_storage import TaskStorage

@dataclass
class Task:
    id: str
    title: str
    completed: bool
    created_at: datetime

class TaskManager:
    def __init__(self, storage: TaskStorage):
        self.storage = storage
    
    def create_task(self, title: str) -> Result[Task]:
        if not title.strip():
            return Failure(BusinessLogicError("Task title cannot be empty"))
        
        task = Task(
            id=self._generate_id(),
            title=title.strip(),
            completed=False,
            created_at=datetime.now()
        )
        
        result = self.storage.save(task)
        if result.is_failure():
            return result
        
        return Success(task)
```

### 2. Implement I/O Operations

```python
# myapp/io/task_storage.py

from pathlib import Path
import json
from ..core.result import Result, Success, Failure
from ..core.errors import IOError
from ..business.tasks import Task

class TaskStorage:
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
    
    def save(self, task: Task) -> Result[None]:
        try:
            tasks = self._load_all()
            tasks[task.id] = task
            self._save_all(tasks)
            return Success(None)
        except Exception as e:
            return Failure(IOError(f"Failed to save task: {e}"))
```

### 3. Create CLI Command

```python
# myapp/cli/commands.py

from ..business.tasks import TaskManager
from .output import OutputFormatter
from .input import InputHandler

class CreateTaskCommand(BaseCommand):
    def __init__(
        self,
        task_manager: TaskManager,
        output_formatter: OutputFormatter,
        input_handler: InputHandler,
    ):
        super().__init__(output_formatter, input_handler)
        self.task_manager = task_manager
    
    def execute(self) -> OperationResult:
        # Get task title from user
        title_result = self.input_handler.prompt_for_input("Task title")
        if title_result.is_failure():
            return self.handle_error(title_result.error)
        
        # Create task
        result = self.task_manager.create_task(title_result.unwrap())
        
        if result.is_failure():
            return self.handle_error(result.error)
        
        task = result.unwrap()
        return self.handle_success(
            f"Created task: {task.title}",
            data={"id": task.id, "title": task.title}
        )
```

### 4. Wire Up in CLI App

```python
# myapp/cli/app.py

@app.command()
def create(
    title: Optional[str] = typer.Option(None, "--title", "-t", help="Task title"),
):
    """Create a new task."""
    output_formatter = OutputFormatter(console)
    input_handler = InputHandler(console)
    storage = TaskStorage(Path.home() / ".myapp" / "tasks.json")
    task_manager = TaskManager(storage)
    
    command = CreateTaskCommand(task_manager, output_formatter, input_handler)
    result = command.execute()
    
    output_formatter.format_result(result)
    raise typer.Exit(EXIT_SUCCESS if result.success else EXIT_ERROR)
```

## Key Principles to Follow

### 1. **Separation of Concerns**
- CLI layer handles user interaction only
- Business logic layer contains domain logic only
- I/O layer handles external operations only

### 2. **Dependency Injection**
- Pass dependencies via constructor
- Never create dependencies inside classes
- Makes testing easy

### 3. **Result Types**
- Use Result[T] for operations that can fail
- Don't use exceptions for control flow
- Exceptions are for unexpected errors only

### 4. **Fail Fast**
- Validate at boundaries (CLI layer)
- Raise exceptions for invalid data
- Don't continue with partial data

### 5. **Type Safety**
- Add type hints to everything
- Run mypy with strict mode
- Fix all type errors

### 6. **Testing**
- Unit test each layer independently
- Mock dependencies in tests
- Integration test complete workflows
- Aim for >80% coverage

### 7. **Documentation**
- Add docstrings to all public APIs
- Include examples in docstrings
- Document exceptions that can be raised
- Keep documentation up to date

## Benefits of This Template

1. **Consistency**: All CLIs follow the same patterns
2. **Maintainability**: Clear structure, easy to understand
3. **Testability**: Every component can be tested in isolation
4. **Extensibility**: Easy to add new features
5. **Professional**: Industry-standard architecture
6. **Type Safe**: Full type coverage, mypy compliant
7. **Error Handling**: Structured, informative errors
8. **User Friendly**: Consistent UX across commands

## Common Patterns

### Pattern 1: Command with Confirmation

```python
def execute(self) -> OperationResult:
    # Show what will be done
    self.output_formatter.format_info("This will delete all tasks")
    
    # Ask for confirmation
    if not self.input_handler.prompt_for_confirmation("Continue?"):
        return self.handle_success("Operation cancelled")
    
    # Execute operation
    result = self.task_manager.delete_all()
    ...
```

### Pattern 2: Command with Progress

```python
def execute(self) -> OperationResult:
    with self.output_formatter.console.status("Processing..."):
        result = self.task_manager.process_all()
    ...
```

### Pattern 3: Command with Dry-Run

```python
def execute(self) -> OperationResult:
    if self.dry_run:
        # Simulate operation
        plan = self.task_manager.plan_operation()
        self.output_formatter.format_info(f"Would process {len(plan.items)} items")
        return self.handle_success("Dry run complete")
    
    # Execute for real
    result = self.task_manager.execute_operation()
    ...
```

## Next Steps

1. **Read the requirements.md** - Understand all requirements
2. **Read the design.md** - Study the architecture and patterns
3. **Copy the template** - Start your new CLI project
4. **Implement your domain** - Add your business logic
5. **Add tests** - Ensure correctness
6. **Configure tooling** - Set up quality gates
7. **Build and iterate** - Follow the patterns

## Questions?

This template is based on the architectural-unification spec from the scrubb project, which underwent comprehensive refactoring to eliminate technical debt and establish professional standards.

For more details, see:
- `requirements.md` - Complete requirements specification
- `design.md` - Detailed architecture and code templates

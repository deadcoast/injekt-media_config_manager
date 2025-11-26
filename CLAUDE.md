# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Injekt CLI** - A command-line application for managing and installing video media player configurations (MPV and VLC). The application automates deployment of optimized configuration files, plugins, and shaders with backup/rollback capabilities.

## Commands

### Installation & Development Setup
```bash
# Install in development mode
pip install -e .

# Install with testing dependencies
pip install -e ".[test]"
```

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_validator.py

# Run property-based tests
pytest tests/test_validator_properties.py
pytest tests/test_backup_manager_properties.py

# Run tests with verbose output
pytest -v
```

### CLI Usage
```bash
# View available commands
injekt --help

# List available configuration packages
injekt list

# Install a package
injekt install <package-name>

# Verify installation
injekt verify <package-name>

# Rollback to previous configuration
injekt rollback
```

## Architecture

The codebase follows a **layered architecture** with strict separation of concerns:

```
┌─────────────────────────────────────┐
│         CLI Layer (cli/)            │  Command handlers, user interaction
├─────────────────────────────────────┤
│    Business Logic Layer (business/) │  Package management, installation logic
├─────────────────────────────────────┤
│         I/O Layer (io/)             │  File operations, path resolution
├─────────────────────────────────────┤
│       Core Domain (core/)           │  Models, interfaces, result types
└─────────────────────────────────────┘
```

### Layer Responsibilities

- **core/**: Domain models (`Package`, `Backup`, `InstallationState`), enums (`PlayerType`, `ProfileType`, `FileType`), protocol interfaces (`PackageRepository`, `PathResolver`, `ConfigValidator`, `BackupManager`, `Installer`), and the `Result` type for error handling
- **io/**: File system operations, configuration file parsing, path detection/resolution, backup storage
- **business/**: Package management, installation orchestration, configuration validation, backup/rollback management, dependency resolution
- **cli/**: Command handlers, input validation, output formatting (text/JSON/table), interactive mode (planned)

### Result Type Pattern

All operations return a `Result[T]` type (defined in `core/result.py`):
- `Success[T]` - Contains the successful result value
- `Failure` - Contains an exception describing the error

Use `is_success()` and `is_failure()` helpers to check results. This pattern ensures explicit error handling and avoids exceptions as control flow.

### Core Domain Models

Key immutable domain models:
- **Package**: Configuration package with name, description, player type, version, files, dependencies, and profile
- **PackageFile**: Individual file in a package with source/target paths, file type, and required flag
- **Backup**: Backup snapshot with ID, timestamp, package name, backup directory, and file list
- **InstallationState**: Tracks installed package state including target directory and installed files

## Key Design Principles

1. **Safety First**: All operations create backups before modifications
2. **Validation Early**: Validate configurations before installation
3. **Atomic Operations**: Operations either complete fully or rollback completely
4. **Idempotent Operations**: Running the same operation twice produces the same result
5. **Clear Feedback**: Provide detailed progress and error information

## Property-Based Testing

The project uses **Hypothesis** for property-based testing to verify correctness properties. Property-based tests are identified by:
- Format: `# Feature: injekt-cli, Property X: <property_text>`
- Located in `tests/test_*_properties.py` files
- Run minimum 100 iterations per test
- Validate requirements from design document

Examples of properties being tested:
- Property 19: Validation error reporting must include file name and line numbers
- Backup/restore round-trip properties
- Dry-run immutability (no disk modifications)
- Installation verification completeness

## Project Structure

```
injekt/
├── core/              # Core domain layer
│   ├── models.py      # Domain models (Package, Backup, InstallationState)
│   ├── interfaces.py  # Protocol definitions for business logic
│   ├── result.py      # Result[T] type for error handling
│   ├── errors.py      # Exception hierarchy (InjektError, ValidationError, etc.)
│   └── constants.py   # Named constants
├── io/                # I/O layer
│   ├── file_operations.py
│   ├── config_parser.py
│   ├── path_resolver.py
│   └── backup_storage.py
├── business/          # Business logic layer
│   ├── package_repository.py
│   ├── validator.py
│   └── backup_manager.py
└── cli/               # CLI layer (under development)
    └── __init__.py
```

## Configuration Assets

Configuration packages are stored in `assets/` organized by player:
- `assets/mpv/` - MPV player configurations, plugins, shaders
- `assets/vlc/` - VLC player configurations

Each package should include:
- Configuration files (e.g., `mpv.conf`, `input.conf`)
- Plugins (Lua scripts in `plugins/lua/`, JS scripts in `plugins/js/`)
- Shaders (GLSL files in `shaders/`)
- Manifest file (JSON describing the package)

## Detailed Design Documentation

For comprehensive architecture details, see `.kiro/specs/injekt-cli/`:
- `design.md` - Complete architecture, interfaces, data models, correctness properties
- `requirements.md` - Full requirements with acceptance criteria

## Testing Strategy

- **Unit Tests**: Cover individual components (validators, parsers, file operations)
- **Property-Based Tests**: Verify correctness properties using Hypothesis
- **Integration Tests**: (Planned) End-to-end installation workflows
- All new business logic should include both unit tests and property-based tests

## Error Handling

Custom exception hierarchy in `core/errors.py`:
- `InjektError` - Base exception
- `PackageNotFoundError`, `ValidationError`, `InstallationError`, `BackupError`, `PathResolutionError`, `ConflictError`, `DependencyError`

Error recovery strategy:
- Validation errors: Report and abort before making changes
- Installation errors: Rollback partial changes, restore from backup
- Backup errors: Abort operation (never proceed without backup)

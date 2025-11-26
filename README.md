# Injekt CLI - Video Media Config Manager

A command-line interface application for managing and installing video media player configurations.

## Installation

```bash
pip install -e .
```

For development with testing dependencies:

```bash
pip install -e ".[test]"
```

## Usage

```bash
injekt --help
```

## Development

This project uses:
- **typer** for CLI framework
- **rich** for beautiful terminal output
- **hypothesis** for property-based testing
- **pytest** for unit testing

## Project Structure

```
injekt/
├── core/          # Core domain models, types, and interfaces
├── io/            # I/O layer for file operations
├── business/      # Business logic layer
└── cli/           # CLI layer for commands
```

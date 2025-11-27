# Injekt CLI - Video Media Config Manager

A professional command-line tool for managing and installing optimized video media player configurations. Injekt automates the deployment of configuration files, plugins, and shaders for MPV and VLC media players with built-in backup and rollback capabilities.

## Features

- 🚀 **One-Command Installation** - Install optimized configurations with a single command
- 🔍 **Auto-Detection** - Automatically finds player installation directories
- 💾 **Safe Backups** - Creates backups before any changes
- ⏮️ **Easy Rollback** - Restore previous configurations instantly
- ✅ **Validation** - Validates configurations before installation
- 🎨 **Multiple Profiles** - Switch between performance, quality, and cinematic profiles
- 📦 **Plugin Management** - Install and manage Lua and JavaScript plugins
- 🎬 **Shader Support** - Deploy GLSL shaders for video enhancement
- 🔄 **Import/Export** - Share and backup your configurations
- 🎯 **Dry-Run Mode** - Preview changes before applying them

## Installation

### From Source (Recommended: UV)

```bash
# Clone the repository
git clone https://github.com/deadcoast/injekt-media_config_manager.git
cd injekt-cli

# Install with UV (recommended)
uv pip install -e .

# Or install with testing dependencies
uv pip install -e ".[test]"
```

### Alternative: Using pip

```bash
# Install in development mode
pip install -e .

# Or with testing dependencies
pip install -e ".[test]"
```

### Requirements

- Python 3.10 or higher
- [UV](https://docs.astral.sh/uv/) (recommended) or pip
- Windows (currently supported platform)
- MPV or VLC media player installed

## Quick Start

1. **List available packages:**
   ```bash
   injekt list
   ```

2. **View package details:**
   ```bash
   injekt info mpv-ultra-5090
   ```

3. **Install a package:**
   ```bash
   injekt install mpv-ultra-5090
   ```

4. **Verify installation:**
   ```bash
   injekt verify mpv-ultra-5090
   ```

5. **Generate a report:**
   ```bash
   injekt report
   ```

## Commands

### Package Management

#### `injekt list`
List all available configuration packages with installation status.

```bash
injekt list
injekt list --format json
```

#### `injekt install <package-name>`
Install a configuration package to your media player.

```bash
injekt install mpv-ultra-5090
injekt install vlc-config --dry-run
injekt install mpv-ultra-5090 -v
```

**What it does:**
- Validates package exists
- Detects or prompts for target directory
- Creates backup of existing configs
- Validates all configuration files
- Copies files to target directory
- Displays installation summary

#### `injekt uninstall <package-name>`
Remove an installed package.

```bash
injekt uninstall mpv-ultra-5090
injekt uninstall vlc-config --dry-run
```

**What it does:**
- Confirms uninstallation
- Creates backup before removal
- Removes all package files
- Cleans up empty directories
- Preserves user-created files

#### `injekt info <package-name>`
Display detailed information about a package.

```bash
injekt info mpv-ultra-5090
injekt info vlc-config --format json
```

**Shows:**
- Package description and purpose
- Target player and version
- Configuration profile type
- Dependencies
- Complete file list with types

#### `injekt update <package-name>`
Update an installed package to the latest version.

```bash
injekt update mpv-ultra-5090
injekt update vlc-config --dry-run
```

**What it does:**
- Checks for available updates
- Displays version changes
- Creates backup before updating
- Preserves user customizations

### Verification and Troubleshooting

#### `injekt verify <package-name>`
Verify package installation integrity.

```bash
injekt verify mpv-ultra-5090
injekt verify vlc-config -v
```

**Checks:**
- All required files exist
- File permissions are correct
- Configuration syntax is valid
- Plugin dependencies are satisfied

#### `injekt report`
Generate a comprehensive configuration report.

```bash
injekt report
injekt report --format json
injekt report -f json > config-report.json
```

**Includes:**
- All installed packages with versions
- Active configuration files
- Installed plugins and shaders
- Current active profile
- Summary statistics

### Backup and Rollback

#### `injekt rollback`
Restore a previous configuration from backup.

```bash
injekt rollback
```

**What it does:**
- Lists all available backups with timestamps
- Prompts you to select a backup
- Creates backup of current state
- Restores files from selected backup

### Profile Management

#### `injekt profile list`
List available configuration profiles.

```bash
injekt profile list
```

**Profiles:**
- **performance** - Optimized for speed and low latency
- **quality** - Optimized for maximum visual quality
- **cinematic** - Optimized for movie watching
- **default** - Balanced general-purpose settings

#### `injekt profile switch <profile-name>`
Switch to a different configuration profile.

```bash
injekt profile switch performance
injekt profile switch quality
injekt profile switch cinematic
```

### Import and Export

#### `injekt export [output-dir]`
Export your current configuration.

```bash
injekt export ./my-config-backup
injekt export ~/Desktop/mpv-export
injekt export
```

**Exports:**
- All active configuration files
- Installed plugins
- Installed shaders
- Package manifest

#### `injekt import <input-dir>`
Import a configuration package.

```bash
injekt import ./my-custom-config
injekt import ~/Downloads/shared-mpv-config
```

**What it does:**
- Validates directory structure
- Checks for required manifest
- Prompts for package details
- Creates new package entry

### Interactive Mode

#### `injekt interactive`
Launch interactive mode with guided wizards.

```bash
injekt interactive
```

**Features:**
- Menu-driven interface
- Input validation and prompts
- Confirmation before operations
- Contextual help
- Easy navigation

## Global Options

All commands support these global options:

- `--verbose, -v` - Enable verbose output with detailed logging
- `--dry-run, -n` - Simulate operations without making changes
- `--format, -f` - Output format: text (default), json, or table
- `--player, -p` - Target player: mpv or vlc (auto-detected if not specified)
- `--version` - Show version information and exit

### Examples

```bash
# Verbose output
injekt install mpv-ultra-5090 -v

# Dry-run mode (preview changes)
injekt install mpv-ultra-5090 --dry-run

# JSON output
injekt list --format json

# Specify target player
injekt install vlc-config --player vlc
```

## Configuration

### Application Directories

Injekt uses the following directories:

- **Assets**: `<project-root>/assets/` - Package definitions
- **Backups**: `~/.injekt/backups/` - Configuration backups
- **State**: `~/.injekt/state.json` - Installation state tracking
- **Logs**: `~/.injekt/logs/` - Application logs

### Player Directories

Default player configuration directories:

- **MPV**: `%APPDATA%\mpv` (Windows)
- **VLC**: `%APPDATA%\vlc` (Windows)

## Package Structure

Packages are defined using JSON manifest files:

```json
{
  "name": "mpv-ultra-5090",
  "description": "Optimized MPV configuration for RTX 5090 + QD-OLED",
  "player": "mpv",
  "version": "0.0.2",
  "profile": "quality",
  "dependencies": [],
  "files": [
    {
      "source": "mpv.conf",
      "target": "mpv.conf",
      "type": "config",
      "required": true
    },
    {
      "source": "scripts/plugin.lua",
      "target": "scripts/plugin.lua",
      "type": "plugin_lua",
      "required": false
    }
  ]
}
```

## Troubleshooting

### Package Not Found

**Problem:** `Package not found: <package-name>`

**Solutions:**
- Check package name spelling with `injekt list`
- Ensure package exists in `assets/packages/` directory
- Verify manifest.json file is present and valid

### Target Directory Not Detected

**Problem:** Cannot automatically detect player directory

**Solutions:**
- Ensure the player is installed
- Specify custom path when prompted
- Use `--player` flag to specify target player
- Check that player config directory exists

### Installation Failed

**Problem:** Installation fails with validation errors

**Solutions:**
- Run `injekt verify <package-name>` to see specific issues
- Check file permissions in target directory
- Ensure no other process is using config files
- Try with `--verbose` flag for detailed error information

### Configuration Not Working

**Problem:** Player doesn't use installed configuration

**Solutions:**
- Verify installation: `injekt verify <package-name>`
- Check player is reading from correct directory
- Restart the media player
- Check for syntax errors in config files
- Review player logs for error messages

### Backup/Rollback Issues

**Problem:** Cannot restore backup

**Solutions:**
- List available backups: `injekt rollback`
- Check backup directory: `~/.injekt/backups/`
- Ensure sufficient disk space
- Verify backup files are not corrupted

### Permission Errors

**Problem:** Permission denied when installing

**Solutions:**
- Run terminal as administrator (Windows)
- Check target directory permissions
- Ensure no files are read-only
- Close media player before installation

### Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `Package not found` | Invalid package name | Check with `injekt list` |
| `Target directory not found` | Player not installed | Install player or specify custom path |
| `Validation failed` | Invalid config syntax | Check config file syntax |
| `Backup failed` | Insufficient disk space | Free up disk space |
| `File conflict detected` | Files managed by another package | Choose resolution option |

## Development

### Project Structure

```
injekt/
├── core/          # Core domain models, types, and interfaces
│   ├── constants.py
│   ├── errors.py
│   ├── interfaces.py
│   ├── models.py
│   └── result.py
├── io/            # I/O layer for file operations
│   ├── backup_storage.py
│   ├── config_parser.py
│   ├── file_operations.py
│   └── path_resolver.py
├── business/      # Business logic layer
│   ├── backup_manager.py
│   ├── installer.py
│   ├── package_repository.py
│   ├── profile_manager.py
│   └── validator.py
└── cli/           # CLI layer for commands
    ├── app.py
    ├── commands.py
    ├── input.py
    ├── interactive.py
    └── output.py
```

### Technologies

- **typer** - CLI framework with automatic help generation
- **rich** - Beautiful terminal output and formatting
- **hypothesis** - Property-based testing for correctness
- **pytest** - Unit testing framework

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=injekt

# Run specific test file
pytest tests/test_installer.py

# Run property-based tests
pytest tests/test_installer_properties.py

# Verbose output
pytest -v
```

### Code Quality

```bash
# Type checking
mypy injekt/

# Linting
flake8 injekt/

# Format code
black injekt/
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

[Add license information here]

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing documentation
- Review troubleshooting section

## Acknowledgments

Built with:
- [Typer](https://typer.tiangolo.com/) - CLI framework
- [Rich](https://rich.readthedocs.io/) - Terminal formatting
- [Hypothesis](https://hypothesis.readthedocs.io/) - Property-based testing

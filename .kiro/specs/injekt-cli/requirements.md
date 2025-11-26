# Requirements Document: Injekt CLI - Video Media Config Manager

## Introduction

Injekt is a command-line interface application for managing and installing (injecting) video media player configurations. It automates the deployment of optimized configuration files, plugins, and shaders for video players like MPV and VLC, ensuring users can quickly set up professional-grade video playback environments.

The application eliminates manual configuration by:
- Automatically detecting target installation directories
- Validating configuration files before deployment
- Managing plugins and dependencies
- Providing rollback capabilities
- Supporting multiple video player platforms

## Glossary

- **Injekt CLI**: The command-line application for managing video media configurations
- **Config Package**: A collection of configuration files, plugins, and assets for a specific video player
- **Target Directory**: The destination directory where configurations will be installed
- **MPV**: A free, open-source, and cross-platform media player
- **VLC**: A free and open-source portable cross-platform media player
- **Plugin**: An extension script (Lua, JavaScript) that adds functionality to a media player
- **Shader**: A GLSL shader file used for video processing and enhancement
- **Injection**: The process of copying and installing configuration files to target directories
- **Backup**: A snapshot of existing configurations before injection
- **Rollback**: The process of restoring previous configurations from backup
- **Config Profile**: A named set of configurations (e.g., "performance", "quality", "cinematic")
- **Validation**: The process of checking configuration files for correctness before installation

## Requirements

### Requirement 1: List Available Configurations

**User Story:** As a user, I want to see all available configuration packages, so that I can choose which ones to install.

#### Acceptance Criteria

1. WHEN the user runs the list command THEN the CLI SHALL display all available config packages with names and descriptions
2. WHEN displaying packages THEN the CLI SHALL show the target player (MPV, VLC) for each package
3. WHEN displaying packages THEN the CLI SHALL indicate which packages are currently installed
4. WHEN displaying packages THEN the CLI SHALL show the version or last modified date of each package
5. WHEN no packages are available THEN the CLI SHALL display a helpful message indicating the assets directory is empty

### Requirement 2: Install Configuration Package

**User Story:** As a user, I want to install a configuration package, so that my video player is optimized without manual setup.

#### Acceptance Criteria

1. WHEN the user specifies a package to install THEN the CLI SHALL validate the package exists before proceeding
2. WHEN installing a package THEN the CLI SHALL detect the correct target directory for the player
3. WHEN the target directory does not exist THEN the CLI SHALL create it with appropriate permissions
4. WHEN existing configurations are present THEN the CLI SHALL create a backup before overwriting
5. WHEN installation completes THEN the CLI SHALL display a summary of installed files and their locations

### Requirement 3: Detect Target Directories

**User Story:** As a user, I want the CLI to automatically find installation directories, so that I don't need to specify paths manually.

#### Acceptance Criteria

1. WHEN detecting MPV directories THEN the CLI SHALL check standard Windows paths including %APPDATA%\mpv
2. WHEN detecting VLC directories THEN the CLI SHALL check standard Windows paths including %APPDATA%\vlc
3. WHEN multiple installation locations exist THEN the CLI SHALL prompt the user to select one
4. WHEN no installation directory is found THEN the CLI SHALL provide the expected path and offer to create it
5. WHEN the user provides a custom path THEN the CLI SHALL validate it exists and is writable

### Requirement 4: Validate Configuration Files

**User Story:** As a developer, I want configurations validated before installation, so that invalid configs don't break the player.

#### Acceptance Criteria

1. WHEN validating MPV configs THEN the CLI SHALL check mpv.conf syntax for common errors
2. WHEN validating plugin files THEN the CLI SHALL verify required dependencies are present
3. WHEN validating shader files THEN the CLI SHALL check file extensions and basic GLSL syntax
4. WHEN validation fails THEN the CLI SHALL report specific errors with file names and line numbers
5. WHEN validation succeeds THEN the CLI SHALL proceed with installation

### Requirement 5: Backup Existing Configurations

**User Story:** As a user, I want my existing configs backed up, so that I can restore them if needed.

#### Acceptance Criteria

1. WHEN installing a package THEN the CLI SHALL create a timestamped backup directory
2. WHEN backing up THEN the CLI SHALL copy all existing config files to the backup location
3. WHEN backup fails THEN the CLI SHALL abort installation and report the error
4. WHEN backup succeeds THEN the CLI SHALL log the backup location
5. WHEN the backup directory is full THEN the CLI SHALL remove old backups keeping only the most recent 5

### Requirement 6: Rollback Configuration

**User Story:** As a user, I want to rollback to previous configurations, so that I can undo problematic changes.

#### Acceptance Criteria

1. WHEN the user requests rollback THEN the CLI SHALL list available backups with timestamps
2. WHEN the user selects a backup THEN the CLI SHALL restore all files from that backup
3. WHEN restoring THEN the CLI SHALL create a backup of the current state before rollback
4. WHEN rollback completes THEN the CLI SHALL display which files were restored
5. WHEN no backups exist THEN the CLI SHALL inform the user and exit gracefully

### Requirement 7: Install Plugins

**User Story:** As a user, I want to install player plugins, so that I can extend functionality without manual file management.

#### Acceptance Criteria

1. WHEN installing plugins THEN the CLI SHALL copy plugin files to the correct subdirectory (scripts/ for Lua, etc.)
2. WHEN plugin dependencies exist THEN the CLI SHALL verify they are available or installable
3. WHEN plugins require configuration THEN the CLI SHALL copy default config files to script-opts/
4. WHEN plugins conflict with existing ones THEN the CLI SHALL warn the user and offer to skip or overwrite
5. WHEN plugin installation completes THEN the CLI SHALL list installed plugins and their locations

### Requirement 8: Install Shaders

**User Story:** As a user, I want to install video shaders, so that I can enhance video quality.

#### Acceptance Criteria

1. WHEN installing shaders THEN the CLI SHALL copy shader files to the shaders/ subdirectory
2. WHEN shader references exist in config files THEN the CLI SHALL verify the shader files are present
3. WHEN shaders have dependencies THEN the CLI SHALL install all required shader files
4. WHEN shader installation completes THEN the CLI SHALL update config files to reference the shaders
5. WHEN shaders are already installed THEN the CLI SHALL skip or update based on version

### Requirement 9: Support Multiple Profiles

**User Story:** As a user, I want to switch between configuration profiles, so that I can optimize for different use cases.

#### Acceptance Criteria

1. WHEN listing profiles THEN the CLI SHALL show all available profiles (performance, quality, cinematic, etc.)
2. WHEN switching profiles THEN the CLI SHALL backup the current configuration
3. WHEN applying a profile THEN the CLI SHALL install the profile-specific config files
4. WHEN a profile is active THEN the CLI SHALL indicate which profile is currently in use
5. WHEN switching profiles THEN the CLI SHALL preserve user-specific customizations where possible

### Requirement 10: Verify Installation

**User Story:** As a user, I want to verify my installation, so that I know everything is configured correctly.

#### Acceptance Criteria

1. WHEN verifying installation THEN the CLI SHALL check all expected files exist in target directories
2. WHEN verifying THEN the CLI SHALL validate file permissions are correct
3. WHEN verifying THEN the CLI SHALL check config file syntax
4. WHEN verification finds issues THEN the CLI SHALL report each problem with suggested fixes
5. WHEN verification succeeds THEN the CLI SHALL display a success message with installation summary

### Requirement 11: Uninstall Configuration Package

**User Story:** As a user, I want to uninstall configurations, so that I can return to default settings.

#### Acceptance Criteria

1. WHEN uninstalling THEN the CLI SHALL remove all files that were installed by the package
2. WHEN uninstalling THEN the CLI SHALL create a backup before removing files
3. WHEN uninstalling THEN the CLI SHALL preserve user-created files not part of the package
4. WHEN uninstalling THEN the CLI SHALL remove empty directories created during installation
5. WHEN uninstall completes THEN the CLI SHALL display which files were removed

### Requirement 12: Display Configuration Info

**User Story:** As a user, I want to view configuration details, so that I understand what will be installed.

#### Acceptance Criteria

1. WHEN displaying info THEN the CLI SHALL show the package description and purpose
2. WHEN displaying info THEN the CLI SHALL list all files included in the package
3. WHEN displaying info THEN the CLI SHALL show target installation paths
4. WHEN displaying info THEN the CLI SHALL display any prerequisites or dependencies
5. WHEN displaying info THEN the CLI SHALL show configuration options and their effects

### Requirement 13: Handle File Conflicts

**User Story:** As a user, I want to be notified of file conflicts, so that I can decide how to handle them.

#### Acceptance Criteria

1. WHEN a file conflict is detected THEN the CLI SHALL display the conflicting file path
2. WHEN conflicts exist THEN the CLI SHALL offer options: skip, overwrite, backup, or abort
3. WHEN the user chooses to overwrite THEN the CLI SHALL backup the existing file first
4. WHEN the user chooses to skip THEN the CLI SHALL continue with remaining files
5. WHEN the user chooses to abort THEN the CLI SHALL exit without making changes

### Requirement 14: Support Dry-Run Mode

**User Story:** As a user, I want to preview installation actions, so that I can verify before making changes.

#### Acceptance Criteria

1. WHEN dry-run mode is enabled THEN the CLI SHALL simulate all installation steps
2. WHEN in dry-run THEN the CLI SHALL display which files would be copied and where
3. WHEN in dry-run THEN the CLI SHALL show which backups would be created
4. WHEN in dry-run THEN the CLI SHALL not modify any files on disk
5. WHEN dry-run completes THEN the CLI SHALL summarize what would have been done

### Requirement 15: Generate Configuration Report

**User Story:** As a user, I want to generate a configuration report, so that I can document my setup.

#### Acceptance Criteria

1. WHEN generating a report THEN the CLI SHALL list all installed packages and versions
2. WHEN generating a report THEN the CLI SHALL include all active configuration files
3. WHEN generating a report THEN the CLI SHALL list installed plugins and shaders
4. WHEN generating a report THEN the CLI SHALL show the current active profile
5. WHEN generating a report THEN the CLI SHALL support output formats (text, JSON, markdown)

### Requirement 16: Update Configuration Package

**User Story:** As a user, I want to update installed packages, so that I have the latest optimizations.

#### Acceptance Criteria

1. WHEN checking for updates THEN the CLI SHALL compare installed versions with available versions
2. WHEN updates are available THEN the CLI SHALL display what has changed
3. WHEN updating THEN the CLI SHALL backup current configurations before applying updates
4. WHEN updating THEN the CLI SHALL preserve user customizations where possible
5. WHEN update completes THEN the CLI SHALL display a summary of changes

### Requirement 17: Import Custom Configurations

**User Story:** As a user, I want to import my own configurations, so that I can share or reuse them.

#### Acceptance Criteria

1. WHEN importing THEN the CLI SHALL accept a directory path containing config files
2. WHEN importing THEN the CLI SHALL validate the structure matches expected format
3. WHEN importing THEN the CLI SHALL create a new package entry for the imported configs
4. WHEN importing THEN the CLI SHALL assign a name and description to the package
5. WHEN import completes THEN the CLI SHALL make the package available for installation

### Requirement 18: Export Configuration Package

**User Story:** As a user, I want to export my current configuration, so that I can back it up or share it.

#### Acceptance Criteria

1. WHEN exporting THEN the CLI SHALL copy all active config files to an export directory
2. WHEN exporting THEN the CLI SHALL include plugins and shaders in the export
3. WHEN exporting THEN the CLI SHALL create a manifest file describing the package
4. WHEN exporting THEN the CLI SHALL support compression (zip) for easy sharing
5. WHEN export completes THEN the CLI SHALL display the export location

### Requirement 19: Validate Player Installation

**User Story:** As a user, I want to verify the player is installed, so that I know configs can be applied.

#### Acceptance Criteria

1. WHEN validating player THEN the CLI SHALL check if the player executable exists
2. WHEN validating player THEN the CLI SHALL verify the player version is compatible
3. WHEN player is not found THEN the CLI SHALL provide download links and installation instructions
4. WHEN player version is incompatible THEN the CLI SHALL warn about potential issues
5. WHEN validation succeeds THEN the CLI SHALL display player version and installation path

### Requirement 20: Support Configuration Templates

**User Story:** As a developer, I want to use configuration templates, so that I can create new packages easily.

#### Acceptance Criteria

1. WHEN creating from template THEN the CLI SHALL provide a list of available templates
2. WHEN using a template THEN the CLI SHALL generate a new package structure
3. WHEN generating THEN the CLI SHALL prompt for package-specific values (name, description, etc.)
4. WHEN template generation completes THEN the CLI SHALL create all necessary directories and files
5. WHEN template is invalid THEN the CLI SHALL report errors and abort generation

### Requirement 21: Log Operations

**User Story:** As a user troubleshooting issues, I want detailed operation logs, so that I can diagnose problems.

#### Acceptance Criteria

1. WHEN operations execute THEN the CLI SHALL log all file operations with timestamps
2. WHEN errors occur THEN the CLI SHALL log error details including stack traces
3. WHEN verbose mode is enabled THEN the CLI SHALL log detailed progress information
4. WHEN operations complete THEN the CLI SHALL write logs to a file in the user's config directory
5. WHEN log files grow large THEN the CLI SHALL rotate logs keeping only recent entries

### Requirement 22: Support Interactive Mode

**User Story:** As a user, I want an interactive installation wizard, so that I can be guided through setup.

#### Acceptance Criteria

1. WHEN interactive mode starts THEN the CLI SHALL present a menu of available actions
2. WHEN selecting an action THEN the CLI SHALL prompt for required inputs step-by-step
3. WHEN inputs are invalid THEN the CLI SHALL display errors and re-prompt
4. WHEN confirming actions THEN the CLI SHALL display a summary before executing
5. WHEN operations complete THEN the CLI SHALL return to the main menu or exit based on user choice

### Requirement 23: Handle Path Normalization

**User Story:** As a developer, I want paths normalized correctly, so that configs work across different systems.

#### Acceptance Criteria

1. WHEN processing Windows paths THEN the CLI SHALL convert forward slashes to backslashes
2. WHEN processing paths THEN the CLI SHALL expand environment variables (%APPDATA%, etc.)
3. WHEN processing relative paths THEN the CLI SHALL resolve them to absolute paths
4. WHEN paths contain spaces THEN the CLI SHALL handle them correctly without escaping issues
5. WHEN paths are invalid THEN the CLI SHALL report clear error messages

### Requirement 24: Support Configuration Merging

**User Story:** As a user, I want to merge configurations, so that I can combine settings from multiple sources.

#### Acceptance Criteria

1. WHEN merging configs THEN the CLI SHALL combine settings from multiple config files
2. WHEN conflicts exist THEN the CLI SHALL use a clear precedence order (user > profile > default)
3. WHEN merging THEN the CLI SHALL preserve comments and formatting where possible
4. WHEN merge completes THEN the CLI SHALL display which settings were merged
5. WHEN merge conflicts occur THEN the CLI SHALL prompt the user to resolve them

### Requirement 25: Provide Help and Documentation

**User Story:** As a user, I want comprehensive help, so that I can use the CLI effectively.

#### Acceptance Criteria

1. WHEN requesting help THEN the CLI SHALL display command usage and examples
2. WHEN requesting help for a command THEN the CLI SHALL show all available options and arguments
3. WHEN displaying help THEN the CLI SHALL include common use cases and workflows
4. WHEN errors occur THEN the CLI SHALL suggest relevant help commands
5. WHEN displaying help THEN the CLI SHALL format output for readability with colors and sections

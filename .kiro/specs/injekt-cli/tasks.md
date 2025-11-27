# Implementation Plan: Injekt CLI

- [x] 1. Set up project structure and core infrastructure





  - Create directory structure (core/, io/, business/, cli/)
  - Set up Python package with pyproject.toml
  - Install dependencies (typer, rich, hypothesis for testing)
  - Create __init__.py files for all modules
  - _Requirements: All requirements (foundation)_

- [x] 1.1 Implement core types and constants


  - Create Result types (Success, Failure) in core/result.py
  - Create error hierarchy in core/errors.py
  - Define constants (exit codes, paths, limits) in core/constants.py
  - Create enums (PlayerType, ProfileType, FileType) in core/models.py
  - _Requirements: 2.1, 3.1, 4.1_

- [x] 1.2 Implement domain models

  - Create PackageFile dataclass
  - Create Package dataclass with methods
  - Create InstallationState dataclass
  - Create Backup dataclass
  - _Requirements: 2.1, 5.1, 6.1_

- [x] 1.3 Define core interfaces


  - Create PackageRepository protocol
  - Create PathResolver protocol
  - Create ConfigValidator protocol
  - Create BackupManager protocol
  - Create Installer protocol
  - _Requirements: 2.1, 3.1, 4.1, 5.1_

- [x] 2. Implement I/O layer




  - Create file operations module
  - Create path resolver module
  - Create config parser module
  - Create backup storage module
  - _Requirements: 2.2, 2.3, 3.1, 5.1_

- [x] 2.1 Implement file operations


  - Create FileOperations class with copy, move, delete methods
  - Implement directory creation with permissions
  - Implement file existence and permission checks
  - Add error handling for I/O failures
  - _Requirements: 2.3, 10.2_

- [x] 2.2 Write property test for file operations


  - **Property 13: Dry-run immutability**
  - **Validates: Requirements 14.4**

- [x] 2.3 Implement path resolver


  - Create PathResolver class
  - Implement detect_player_directory for MPV
  - Implement detect_player_directory for VLC
  - Implement path normalization for Windows
  - Implement environment variable expansion
  - _Requirements: 3.1, 3.2, 23.1, 23.2_

- [x] 2.4 Write property test for path normalization


  - **Property 17: Path normalization**
  - **Validates: Requirements 23.1, 23.2**

- [x] 2.5 Implement config parser


  - Create ConfigParser class
  - Implement JSON manifest parsing
  - Implement package manifest validation
  - Implement installation state parsing
  - Implement backup metadata parsing
  - _Requirements: 1.1, 2.1, 5.1_

- [x] 2.6 Write property test for manifest parsing


  - **Property 1: Package listing completeness**
  - **Validates: Requirements 1.1, 1.2, 1.4**

- [x] 2.7 Implement backup storage


  - Create BackupStorage class
  - Implement backup directory creation with timestamps
  - Implement backup metadata persistence
  - Implement backup listing and retrieval
  - Implement old backup cleanup
  - _Requirements: 5.1, 5.2, 5.5, 6.1_

- [x] 2.8 Write property test for backup rotation


  - **Property 5: Backup rotation**
  - **Validates: Requirements 5.5**

- [x] 3. Implement validation layer





  - Create configuration validators
  - Create plugin validators
  - Create shader validators
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 3.1 Implement config validator


  - Create ConfigValidator class
  - Implement MPV config syntax validation
  - Implement VLC config syntax validation
  - Implement validation error reporting with line numbers
  - _Requirements: 4.1, 4.4_

- [x] 3.2 Write property test for validation error reporting


  - **Property 19: Validation error reporting**
  - **Validates: Requirements 4.4**

- [x] 3.3 Implement plugin validator

  - Implement Lua plugin validation
  - Implement JavaScript plugin validation
  - Implement dependency checking
  - _Requirements: 4.2_

- [x] 3.4 Implement shader validator

  - Implement GLSL shader file validation
  - Implement shader extension checking
  - Implement basic syntax validation
  - _Requirements: 4.3_

- [x] 3.5 Write property test for validation before installation


  - **Property 4: Validation before installation**
  - **Validates: Requirements 4.1, 4.2, 4.3, 4.5**

- [-] 4. Implement business logic layer


  - Create package manager
  - Create installer
  - Create backup manager
  - Create profile manager
  - _Requirements: 2.1, 5.1, 9.1_

- [x] 4.1 Implement package repository


  - Create PackageRepository class
  - Implement list_packages from assets directory
  - Implement get_package by name
  - Implement get_installed_packages from state file
  - _Requirements: 1.1, 2.1_

- [x] 4.2 Implement backup manager


  - Create BackupManager class
  - Implement create_backup with file copying
  - Implement list_backups from backup directory
  - Implement restore_backup with file restoration
  - Implement cleanup_old_backups keeping 5 most recent
  - _Requirements: 5.1, 5.2, 5.5, 6.1, 6.2_

- [x] 4.3 Write property test for backup creation


  - **Property 2: Installation creates backup**
  - **Validates: Requirements 2.4, 5.1, 5.2**



- [x] 4.4 Write property test for rollback round-trip





  - **Property 6: Rollback round-trip**



  - **Validates: Requirements 6.2**

- [x] 4.5 Implement installer




  - Create Installer class
  - Implement install_package with validation
  - Implement file conflict detection
  - Implement atomic installation with rollback on failure
  - Implement uninstall_package
  - Implement verify_installation
  - _Requirements: 2.1, 2.2, 2.5, 10.1, 11.1_

- [ ] 4.6 Write property test for conflict detection
  - **Property 12: Conflict detection**
  - **Validates: Requirements 13.1**

- [ ] 4.7 Write property test for atomic installation
  - **Property 20: Atomic installation**
  - **Validates: Requirements 5.3**

- [ ] 4.8 Write property test for uninstall inverse
  - **Property 11: Uninstall inverse**
  - **Validates: Requirements 11.1, 11.3**

- [ ] 4.9 Implement plugin installer
  - Create PluginInstaller class
  - Implement plugin path routing by file type
  - Implement plugin dependency resolution
  - Implement script-opts config file copying
  - _Requirements: 7.1, 7.2, 7.3_

- [ ] 4.10 Write property test for plugin path routing
  - **Property 7: Plugin path routing**
  - **Validates: Requirements 7.1**

- [ ] 4.11 Implement shader installer
  - Create ShaderInstaller class
  - Implement shader file copying to shaders/ directory
  - Implement shader reference validation
  - Implement shader dependency resolution
  - _Requirements: 8.1, 8.2, 8.3_

- [ ] 4.12 Write property test for shader reference validation
  - **Property 8: Shader reference validation**
  - **Validates: Requirements 8.2**

- [ ] 4.13 Implement profile manager
  - Create ProfileManager class
  - Implement list_profiles
  - Implement switch_profile with backup
  - Implement get_active_profile
  - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [ ] 4.14 Write property test for profile backup safety
  - **Property 9: Profile backup safety**
  - **Validates: Requirements 9.2**

- [ ] 5. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Implement CLI layer - output and input
  - Create output formatter
  - Create input handler
  - _Requirements: 15.5, 22.1_

- [ ] 6.1 Implement output formatter
  - Create OutputFormatter class using Rich
  - Implement format_result for OperationResult
  - Implement format_success, format_error, format_warning
  - Implement format_table for package listings
  - Implement JSON output format
  - _Requirements: 1.1, 15.5_

- [ ] 6.2 Implement input handler
  - Create InputHandler class using Rich prompts
  - Implement prompt_for_input with validation
  - Implement prompt_for_confirmation
  - Implement prompt_for_path
  - Implement prompt_for_choice
  - _Requirements: 3.3, 13.2, 22.2_

- [ ] 7. Implement CLI commands
  - Create command classes
  - Wire up Typer CLI application
  - _Requirements: All requirements_

- [ ] 7.1 Implement list command
  - Create ListCommand class
  - Implement execute to list all packages
  - Display package name, description, player, version
  - Indicate installed packages
  - Handle empty package list
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [ ] 7.2 Implement install command
  - Create InstallCommand class
  - Implement execute with package validation
  - Implement path detection with user prompts
  - Implement backup creation before installation
  - Implement file conflict handling
  - Display installation summary
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ] 7.3 Implement verify command
  - Create VerifyCommand class
  - Implement execute to check file existence
  - Check file permissions
  - Validate config syntax
  - Report issues with suggestions
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ] 7.4 Write property test for installation verification
  - **Property 10: Installation verification completeness**
  - **Validates: Requirements 10.1, 10.2**

- [ ] 7.5 Implement rollback command
  - Create RollbackCommand class
  - Implement execute to list backups
  - Prompt user to select backup
  - Create backup before rollback
  - Restore selected backup
  - Display restored files
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 7.6 Implement uninstall command
  - Create UninstallCommand class
  - Implement execute to remove package files
  - Create backup before uninstall
  - Preserve user-created files
  - Remove empty directories
  - Display removed files
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [ ] 7.7 Implement info command
  - Create InfoCommand class
  - Display package description and purpose
  - List all files in package
  - Show target installation paths
  - Display prerequisites and dependencies
  - Show configuration options
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [ ] 7.8 Implement profile commands
  - Create ProfileListCommand class
  - Create ProfileSwitchCommand class
  - Implement profile listing
  - Implement profile switching with backup
  - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [ ] 7.9 Implement report command
  - Create ReportCommand class
  - List all installed packages and versions
  - Include active configuration files
  - List installed plugins and shaders
  - Show current active profile
  - Support multiple output formats
  - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_

- [ ] 7.10 Write property test for report completeness
  - **Property 14: Report completeness**
  - **Validates: Requirements 15.1, 15.2, 15.3, 15.4**

- [ ] 7.11 Implement update command
  - Create UpdateCommand class
  - Compare installed vs available versions
  - Display changes
  - Backup before update
  - Preserve user customizations
  - Display update summary
  - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5_

- [ ] 7.12 Write property test for update preserves customizations
  - **Property 15: Update preserves customizations**
  - **Validates: Requirements 16.4**

- [ ] 7.13 Implement export command
  - Create ExportCommand class
  - Copy all active config files
  - Include plugins and shaders
  - Create manifest file
  - Support zip compression
  - Display export location
  - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5_

- [ ] 7.14 Implement import command
  - Create ImportCommand class
  - Accept directory path
  - Validate structure
  - Create package entry
  - Assign name and description
  - Make package available
  - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5_

- [ ] 7.15 Write property test for export-import round-trip
  - **Property 16: Export-import round-trip**
  - **Validates: Requirements 18.1, 18.2**

- [ ] 8. Implement CLI application
  - Create main Typer app
  - Wire up all commands
  - Add global options
  - Implement version callback
  - _Requirements: All requirements_

- [ ] 8.1 Create Typer application
  - Create app.py with Typer app
  - Add version callback
  - Add global options (verbose, dry-run, format, player)
  - Configure dependency injection for commands
  - _Requirements: 14.1, 14.2, 14.3, 14.4_

- [ ] 8.2 Wire up list command
  - Add list command to Typer app
  - Inject dependencies (PackageRepository, OutputFormatter)
  - Handle errors and display results
  - _Requirements: 1.1_

- [ ] 8.3 Wire up install command
  - Add install command to Typer app
  - Inject dependencies (Installer, PathResolver, BackupManager, etc.)
  - Support dry-run mode
  - Handle errors and display results
  - _Requirements: 2.1_

- [ ] 8.4 Wire up remaining commands
  - Add verify, rollback, uninstall, info commands
  - Add profile list and profile switch commands
  - Add report, update, export, import commands
  - Inject appropriate dependencies for each
  - _Requirements: All requirements_

- [ ] 9. Implement configuration management
  - Create application config
  - Implement config loading from file and environment
  - _Requirements: 7.1, 7.2, 7.3_

- [ ] 9.1 Create application configuration
  - Create InjektConfig dataclass
  - Implement from_file class method
  - Implement from_env class method
  - Implement config validation
  - Implement config merging
  - _Requirements: 7.1, 7.2, 7.3, 24.1, 24.2_

- [ ] 9.2 Write property test for config merge precedence
  - **Property 18: Config merge precedence**
  - **Validates: Requirements 24.2**

- [ ] 10. Implement logging and error handling
  - Set up structured logging
  - Implement error handlers
  - _Requirements: 21.1, 21.2, 21.3_

- [ ] 10.1 Set up logging
  - Configure Python logging module
  - Implement file logging to ~/.injekt/logs/
  - Implement log rotation
  - Add structured logging with context
  - Support verbosity levels
  - _Requirements: 21.1, 21.2, 21.3, 21.4, 21.5_

- [ ] 10.2 Implement error handlers
  - Create error handler for each error type
  - Implement user-friendly error messages
  - Add contextual help suggestions
  - Log errors with stack traces
  - _Requirements: 3.4, 25.4_

- [ ] 11. Create sample package manifests
  - Create MPV ultra config package manifest
  - Create VLC config package manifest
  - Create plugin packages
  - _Requirements: 1.1, 2.1_

- [ ] 11.1 Create MPV ultra package
  - Create manifest.json for mpv-ultra-5090
  - Reference existing config files in docs/mpv-config/
  - Reference existing plugins in assets/mpv/plugins/
  - Define file mappings and types
  - _Requirements: 1.1, 2.1_

- [ ] 11.2 Create VLC package
  - Create manifest.json for vlc-config
  - Reference existing config in docs/vlc-config/
  - Define file mappings
  - _Requirements: 1.1, 2.1_

- [ ] 12. Implement interactive mode
  - Create interactive menu system
  - Implement step-by-step wizards
  - _Requirements: 22.1, 22.2, 22.3, 22.4, 22.5_

- [ ] 12.1 Create interactive mode
  - Create InteractiveMode class
  - Implement main menu with action selection
  - Implement step-by-step input prompts
  - Implement input validation with re-prompting
  - Implement confirmation with summary
  - Implement menu loop or exit
  - _Requirements: 22.1, 22.2, 22.3, 22.4, 22.5_

- [ ] 13. Add help and documentation
  - Implement comprehensive help text
  - Add command examples
  - Create README
  - _Requirements: 25.1, 25.2, 25.3, 25.4_

- [ ] 13.1 Add help text to commands
  - Add docstrings to all commands
  - Add usage examples to help text
  - Add common use cases
  - Implement contextual help suggestions
  - _Requirements: 25.1, 25.2, 25.3, 25.4_

- [ ] 13.2 Create README
  - Document installation instructions
  - Document all commands with examples
  - Document configuration options
  - Add troubleshooting section
  - _Requirements: 25.1, 25.2, 25.3_

- [ ] 14. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 15. Create entry point and packaging
  - Create __main__.py entry point
  - Configure pyproject.toml for packaging
  - Test CLI installation
  - _Requirements: All requirements_

- [ ] 15.1 Create entry point
  - Create __main__.py that calls app()
  - Configure console_scripts in pyproject.toml
  - Test running with `python -m injekt`
  - Test running with `injekt` after install
  - _Requirements: All requirements_

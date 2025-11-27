"""Plugin installer implementation for managing plugin installations."""

from pathlib import Path
from typing import List, Dict, Set
from injekt.core.models import Package, PackageFile, FileType
from injekt.core.result import Result, Success, Failure
from injekt.core.errors import InstallationError, DependencyError
from injekt.io.file_operations import FileOperations


class PluginInstaller:
    """Manages plugin installation with path routing and dependency resolution."""
    
    # Plugin file type to subdirectory mapping
    PLUGIN_PATH_MAP = {
        FileType.PLUGIN_LUA: "scripts",
        FileType.PLUGIN_JS: "scripts",
        FileType.SCRIPT_OPT: "script-opts"
    }
    
    def __init__(self, file_ops: FileOperations):
        """Initialize the plugin installer.
        
        Args:
            file_ops: File operations handler
        """
        self.file_ops = file_ops
    
    def get_plugin_target_path(
        self,
        plugin_file: PackageFile,
        target_dir: Path
    ) -> Path:
        """Route plugin file to correct subdirectory based on file type.
        
        Args:
            plugin_file: Plugin file to route
            target_dir: Base target directory
            
        Returns:
            Full target path for the plugin file
        """
        # Get the subdirectory for this plugin type
        subdir = self.PLUGIN_PATH_MAP.get(plugin_file.file_type)
        
        if subdir is None:
            # Not a plugin file, return original target path
            return target_dir / plugin_file.target_path
        
        # Extract just the filename from target_path
        filename = Path(plugin_file.target_path).name
        
        # Route to correct subdirectory
        return target_dir / subdir / filename
    
    def resolve_plugin_dependencies(
        self,
        package: Package
    ) -> Result[List[str]]:
        """Resolve plugin dependencies for a package.
        
        Args:
            package: Package containing plugins
            
        Returns:
            Result containing list of missing dependencies or error
        """
        try:
            # Get all plugin files from the package
            plugin_files = (
                package.get_files_by_type(FileType.PLUGIN_LUA) +
                package.get_files_by_type(FileType.PLUGIN_JS)
            )
            
            missing_dependencies = []
            
            # Check each plugin's dependencies
            for plugin_file in plugin_files:
                # Parse dependencies from plugin file
                deps = self._parse_plugin_dependencies(plugin_file.source_path)
                
                # Check if dependencies are available
                for dep in deps:
                    if not self._is_dependency_available(dep, package):
                        missing_dependencies.append(
                            f"{plugin_file.source_path.name} requires: {dep}"
                        )
            
            return Success(missing_dependencies)
            
        except Exception as e:
            return Failure(DependencyError(
                f"Failed to resolve plugin dependencies: {e}"
            ))
    
    def install_plugin_configs(
        self,
        package: Package,
        target_dir: Path,
        dry_run: bool = False
    ) -> Result[List[Path]]:
        """Install script-opts configuration files for plugins.
        
        Args:
            package: Package containing plugin configs
            target_dir: Target directory for installation
            dry_run: If True, simulate without making changes
            
        Returns:
            Result containing list of installed config paths or error
        """
        try:
            # Set dry-run mode
            original_dry_run = self.file_ops.dry_run
            self.file_ops.dry_run = dry_run
            
            # Get all script-opt files
            script_opt_files = package.get_files_by_type(FileType.SCRIPT_OPT)
            
            installed_configs = []
            
            for config_file in script_opt_files:
                # Skip non-required files if source doesn't exist
                if not config_file.required and not config_file.source_path.exists():
                    continue
                
                # Route to script-opts directory
                dest_path = self.get_plugin_target_path(config_file, target_dir)
                
                # Copy the config file
                copy_result = self.file_ops.copy_file(
                    config_file.source_path,
                    dest_path
                )
                
                if isinstance(copy_result, Failure):
                    self.file_ops.dry_run = original_dry_run
                    return copy_result
                
                installed_configs.append(dest_path)
            
            self.file_ops.dry_run = original_dry_run
            return Success(installed_configs)
            
        except Exception as e:
            self.file_ops.dry_run = original_dry_run
            return Failure(InstallationError(
                f"Failed to install plugin configs: {e}"
            ))
    
    def _parse_plugin_dependencies(self, plugin_path: Path) -> List[str]:
        """Parse dependencies from a plugin file.
        
        Args:
            plugin_path: Path to plugin file
            
        Returns:
            List of dependency names
        """
        dependencies = []
        
        try:
            if not plugin_path.exists():
                return dependencies
            
            content = plugin_path.read_text(encoding='utf-8')
            
            # Parse Lua dependencies
            if plugin_path.suffix == '.lua':
                # Look for require statements
                for line in content.split('\n'):
                    line = line.strip()
                    if line.startswith('require') or 'require(' in line:
                        # Extract module name from require('module') or require "module"
                        if "require('" in line or 'require("' in line:
                            start = line.find("'") if "'" in line else line.find('"')
                            if start != -1:
                                end = line.find("'", start + 1) if "'" in line else line.find('"', start + 1)
                                if end != -1:
                                    dep = line[start + 1:end]
                                    dependencies.append(dep)
            
            # Parse JavaScript dependencies
            elif plugin_path.suffix == '.js':
                # Look for require or import statements
                for line in content.split('\n'):
                    line = line.strip()
                    # Handle var x = require('module') pattern
                    if 'require(' in line:
                        # Extract module name
                        start_idx = line.find('require(')
                        if start_idx != -1:
                            # Find the opening quote after require(
                            substr = line[start_idx + 8:]  # After 'require('
                            start = 0
                            if substr.startswith("'") or substr.startswith('"'):
                                quote_char = substr[0]
                                end = substr.find(quote_char, 1)
                                if end != -1:
                                    dep = substr[1:end]
                                    dependencies.append(dep)
                    elif line.startswith('import '):
                        # Handle import statements
                        if 'from' in line:
                            parts = line.split('from')
                            if len(parts) > 1:
                                dep = parts[1].strip().strip("'\"").rstrip(';')
                                dependencies.append(dep)
        
        except Exception:
            # If we can't parse, return empty list
            pass
        
        return dependencies
    
    def _is_dependency_available(
        self,
        dependency: str,
        package: Package
    ) -> bool:
        """Check if a dependency is available in the package.
        
        Args:
            dependency: Dependency name to check
            package: Package to search in
            
        Returns:
            True if dependency is available, False otherwise
        """
        # Check if dependency is in package dependencies list
        if dependency in package.dependencies:
            return True
        
        # Check if dependency is a plugin file in the package
        plugin_files = (
            package.get_files_by_type(FileType.PLUGIN_LUA) +
            package.get_files_by_type(FileType.PLUGIN_JS)
        )
        
        for plugin_file in plugin_files:
            # Check if filename matches dependency
            filename = plugin_file.source_path.stem
            if filename == dependency or plugin_file.source_path.name == dependency:
                return True
        
        # For now, assume system dependencies are available
        # In a real implementation, we'd check system paths
        return True

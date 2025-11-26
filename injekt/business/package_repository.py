"""Package repository implementation for managing configuration packages."""

from pathlib import Path
from typing import List

from injekt.core.interfaces import PackageRepository as PackageRepositoryInterface
from injekt.core.models import Package
from injekt.core.result import Result, Success, Failure
from injekt.core.errors import PackageNotFoundError
from injekt.io.config_parser import ConfigParser


class PackageRepository(PackageRepositoryInterface):
    """Manages configuration packages from assets directory and installation state."""
    
    def __init__(self, assets_dir: Path, state_file: Path, config_parser: ConfigParser):
        """Initialize the package repository.
        
        Args:
            assets_dir: Directory containing package manifests
            state_file: Path to installation state file
            config_parser: Parser for configuration files
        """
        self.assets_dir = assets_dir
        self.state_file = state_file
        self.config_parser = config_parser
    
    def list_packages(self) -> Result[List[Package]]:
        """List all available packages from the assets directory.
        
        Returns:
            Result containing list of available packages or error
        """
        try:
            if not self.assets_dir.exists():
                return Failure(PackageNotFoundError(f"Assets directory does not exist: {self.assets_dir}"))
            
            packages = []
            
            # Search for manifest.json files in the assets directory
            for manifest_path in self.assets_dir.rglob("manifest.json"):
                result = self.config_parser.parse_package_manifest(manifest_path)
                
                if isinstance(result, Success):
                    packages.append(result.value)
                # Silently skip invalid manifests during listing
            
            return Success(packages)
            
        except Exception as e:
            return Failure(PackageNotFoundError(f"Failed to list packages: {e}"))
    
    def get_package(self, name: str) -> Result[Package]:
        """Get a specific package by name.
        
        Args:
            name: Name of the package to retrieve
            
        Returns:
            Result containing the package or error if not found
        """
        # List all packages and find the one with matching name
        list_result = self.list_packages()
        
        if isinstance(list_result, Failure):
            return list_result
        
        for package in list_result.value:
            if package.name == name:
                return Success(package)
        
        return Failure(PackageNotFoundError(f"Package not found: {name}"))
    
    def get_installed_packages(self) -> Result[List[Package]]:
        """Get list of installed packages from state file.
        
        Returns:
            Result containing list of installed packages or error
        """
        # Parse installation state
        state_result = self.config_parser.parse_installation_state(self.state_file)
        
        if isinstance(state_result, Failure):
            return state_result
        
        # Extract packages from installation states
        packages = [install.package for install in state_result.value]
        
        return Success(packages)

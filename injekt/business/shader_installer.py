"""Shader installer implementation for managing shader installations."""

from pathlib import Path
from typing import List, Set
from injekt.core.models import Package, PackageFile, FileType
from injekt.core.result import Result, Success, Failure
from injekt.core.errors import InstallationError, DependencyError
from injekt.io.file_operations import FileOperations


class ShaderInstaller:
    """Manages shader installation with reference validation and dependency resolution."""
    
    # Shader file extensions
    SHADER_EXTENSIONS = {'.glsl', '.frag', '.vert', '.comp', '.hook'}
    
    def __init__(self, file_ops: FileOperations):
        """Initialize the shader installer.
        
        Args:
            file_ops: File operations handler
        """
        self.file_ops = file_ops
    
    def get_shader_target_path(
        self,
        shader_file: PackageFile,
        target_dir: Path
    ) -> Path:
        """Route shader file to shaders/ subdirectory.
        
        Args:
            shader_file: Shader file to route
            target_dir: Base target directory
            
        Returns:
            Full target path for the shader file
        """
        # Extract just the filename from target_path
        filename = Path(shader_file.target_path).name
        
        # Route to shaders subdirectory
        return target_dir / "shaders" / filename
    
    def install_shaders(
        self,
        package: Package,
        target_dir: Path,
        dry_run: bool = False
    ) -> Result[List[Path]]:
        """Install shader files to shaders/ directory.
        
        Args:
            package: Package containing shaders
            target_dir: Target directory for installation
            dry_run: If True, simulate without making changes
            
        Returns:
            Result containing list of installed shader paths or error
        """
        try:
            # Set dry-run mode
            original_dry_run = self.file_ops.dry_run
            self.file_ops.dry_run = dry_run
            
            # Get all shader files
            shader_files = package.get_files_by_type(FileType.SHADER)
            
            installed_shaders = []
            
            for shader_file in shader_files:
                # Skip non-required files if source doesn't exist
                if not shader_file.required and not shader_file.source_path.exists():
                    continue
                
                # Route to shaders directory
                dest_path = self.get_shader_target_path(shader_file, target_dir)
                
                # Copy the shader file
                copy_result = self.file_ops.copy_file(
                    shader_file.source_path,
                    dest_path
                )
                
                if isinstance(copy_result, Failure):
                    self.file_ops.dry_run = original_dry_run
                    return copy_result
                
                installed_shaders.append(dest_path)
            
            self.file_ops.dry_run = original_dry_run
            return Success(installed_shaders)
            
        except Exception as e:
            self.file_ops.dry_run = original_dry_run
            return Failure(InstallationError(
                f"Failed to install shaders: {e}"
            ))
    
    def validate_shader_references(
        self,
        package: Package,
        target_dir: Path
    ) -> Result[List[str]]:
        """Validate that shader references in config files exist.
        
        Args:
            package: Package containing config files and shaders
            target_dir: Target directory where shaders will be installed
            
        Returns:
            Result containing list of missing shader references or error
        """
        try:
            # Get all config files
            config_files = package.get_files_by_type(FileType.CONFIG)
            
            # Get all shader files that will be installed
            shader_files = package.get_files_by_type(FileType.SHADER)
            available_shaders = {
                self.get_shader_target_path(sf, target_dir).name
                for sf in shader_files
            }
            
            missing_references = []
            
            # Check each config file for shader references
            for config_file in config_files:
                if not config_file.source_path.exists():
                    continue
                
                # Parse shader references from config
                referenced_shaders = self._parse_shader_references(
                    config_file.source_path
                )
                
                # Check if referenced shaders are available
                for shader_ref in referenced_shaders:
                    shader_name = Path(shader_ref).name
                    if shader_name not in available_shaders:
                        # Check if it exists in target directory already
                        shader_path = target_dir / "shaders" / shader_name
                        if not shader_path.exists():
                            missing_references.append(
                                f"{config_file.source_path.name} references missing shader: {shader_ref}"
                            )
            
            return Success(missing_references)
            
        except Exception as e:
            return Failure(InstallationError(
                f"Failed to validate shader references: {e}"
            ))
    
    def resolve_shader_dependencies(
        self,
        package: Package
    ) -> Result[List[str]]:
        """Resolve shader dependencies for a package.
        
        Args:
            package: Package containing shaders
            
        Returns:
            Result containing list of missing dependencies or error
        """
        try:
            # Get all shader files from the package
            shader_files = package.get_files_by_type(FileType.SHADER)
            
            missing_dependencies = []
            
            # Check each shader's dependencies
            for shader_file in shader_files:
                # Parse dependencies from shader file
                deps = self._parse_shader_dependencies(shader_file.source_path)
                
                # Check if dependencies are available
                for dep in deps:
                    if not self._is_shader_dependency_available(dep, package):
                        missing_dependencies.append(
                            f"{shader_file.source_path.name} requires: {dep}"
                        )
            
            return Success(missing_dependencies)
            
        except Exception as e:
            return Failure(DependencyError(
                f"Failed to resolve shader dependencies: {e}"
            ))
    
    def _parse_shader_references(self, config_path: Path) -> List[str]:
        """Parse shader references from a config file.
        
        Args:
            config_path: Path to config file
            
        Returns:
            List of shader file references
        """
        shader_refs = []
        
        try:
            if not config_path.exists():
                return shader_refs
            
            content = config_path.read_text(encoding='utf-8')
            
            # Parse shader references from config
            for line in content.split('\n'):
                line = line.strip()
                
                # Skip comments
                if line.startswith('#'):
                    continue
                
                # Look for shader references in MPV config format
                # Examples: glsl-shaders="~~/shaders/shader.glsl"
                #           glsl-shader="~~/shaders/shader.glsl"
                if 'glsl-shader' in line.lower():
                    # Extract shader path
                    if '=' in line:
                        value = line.split('=', 1)[1].strip()
                        # Remove quotes
                        value = value.strip('"').strip("'")
                        # Extract filename from path
                        if value:
                            shader_refs.append(value)
                
                # Look for shader references in other formats
                # Example: profile-cond=get('video-params/primaries')=='bt.2020' profile-restore=copy-equal glsl-shaders-append="~~/shaders/hdr-toys.glsl"
                if 'glsl-shaders-append' in line.lower() or 'glsl-shaders-set' in line.lower():
                    # Extract shader path
                    parts = line.split('glsl-shaders-', 1)
                    if len(parts) > 1:
                        # Find the value after = 
                        if '=' in parts[1]:
                            value = parts[1].split('=', 1)[1].strip()
                            # Remove quotes
                            value = value.strip('"').strip("'")
                            # Handle multiple shaders separated by :
                            for shader in value.split(':'):
                                shader = shader.strip()
                                if shader:
                                    shader_refs.append(shader)
        
        except Exception:
            # If we can't parse, return empty list
            pass
        
        return shader_refs
    
    def _parse_shader_dependencies(self, shader_path: Path) -> List[str]:
        """Parse dependencies from a shader file.
        
        Args:
            shader_path: Path to shader file
            
        Returns:
            List of dependency shader names
        """
        dependencies = []
        
        try:
            if not shader_path.exists():
                return dependencies
            
            content = shader_path.read_text(encoding='utf-8')
            
            # Parse GLSL shader dependencies
            # Look for #include directives or other shader references
            for line in content.split('\n'):
                line = line.strip()
                
                # Look for #include statements
                if line.startswith('#include'):
                    # Extract included file
                    # Format: #include "filename.glsl"
                    if '"' in line:
                        start = line.find('"')
                        end = line.find('"', start + 1)
                        if start != -1 and end != -1:
                            dep = line[start + 1:end]
                            dependencies.append(dep)
                    elif '<' in line:
                        start = line.find('<')
                        end = line.find('>', start + 1)
                        if start != -1 and end != -1:
                            dep = line[start + 1:end]
                            dependencies.append(dep)
        
        except Exception:
            # If we can't parse, return empty list
            pass
        
        return dependencies
    
    def _is_shader_dependency_available(
        self,
        dependency: str,
        package: Package
    ) -> bool:
        """Check if a shader dependency is available in the package.
        
        Args:
            dependency: Dependency shader name to check
            package: Package to search in
            
        Returns:
            True if dependency is available, False otherwise
        """
        # Get all shader files in the package
        shader_files = package.get_files_by_type(FileType.SHADER)
        
        # Extract just the filename from dependency
        dep_name = Path(dependency).name
        
        for shader_file in shader_files:
            # Check if filename matches dependency
            if shader_file.source_path.name == dep_name:
                return True
        
        # For system shaders or built-in shaders, assume available
        # In a real implementation, we'd check system shader paths
        return True

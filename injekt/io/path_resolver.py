"""Path resolution and detection for player installations."""

import os
from pathlib import Path
from typing import List, Optional

from injekt.core.models import PlayerType
from injekt.core.errors import PathResolutionError
from injekt.core.result import Result, Success, Failure
from injekt.core.constants import MPV_PATHS, VLC_PATHS


class WindowsPathResolver:
    """Resolves and normalizes paths for Windows systems."""
    
    def detect_player_directory(self, player: PlayerType) -> Result[Path]:
        """Detect installation directory for a player.
        
        Args:
            player: The player type to detect
            
        Returns:
            Result containing the detected path or error
        """
        paths = self._get_standard_paths(player)
        
        for path in paths:
            expanded_path = self._expand_path(path)
            if expanded_path.exists() and expanded_path.is_dir():
                return Success(self.normalize_path(expanded_path))
        
        # No path found
        error_msg = f"Could not detect {player.value} installation directory. Checked: {', '.join(str(p) for p in paths)}"
        return Failure(PathResolutionError(error_msg))
    
    def get_config_directory(self, player: PlayerType) -> Result[Path]:
        """Get configuration directory for a player.
        
        For most players, this is the same as the installation directory.
        
        Args:
            player: The player type
            
        Returns:
            Result containing the config directory path
        """
        return self.detect_player_directory(player)
    
    def normalize_path(self, path: Path) -> Path:
        """Normalize a path for Windows.
        
        - Converts forward slashes to backslashes
        - Expands environment variables
        - Resolves to absolute path
        
        Args:
            path: Path to normalize
            
        Returns:
            Normalized path
        """
        # Convert to string for manipulation
        path_str = str(path)
        
        # Expand environment variables
        path_str = os.path.expandvars(path_str)
        
        # Convert to Path object
        normalized = Path(path_str)
        
        # Resolve to absolute path
        try:
            normalized = normalized.resolve()
        except (OSError, RuntimeError):
            # If resolve fails, just use absolute
            normalized = normalized.absolute()
        
        return normalized
    
    def _get_standard_paths(self, player: PlayerType) -> List[Path]:
        """Get standard installation paths for a player.
        
        Args:
            player: The player type
            
        Returns:
            List of standard paths to check
        """
        if player == PlayerType.MPV:
            return MPV_PATHS
        elif player == PlayerType.VLC:
            return VLC_PATHS
        else:
            return []
    
    def _expand_path(self, path: Path) -> Path:
        """Expand environment variables in a path.
        
        Args:
            path: Path potentially containing environment variables
            
        Returns:
            Expanded path
        """
        return Path(os.path.expandvars(str(path)))
    
    def validate_path_writable(self, path: Path) -> Result[None]:
        """Validate that a path is writable.
        
        Args:
            path: Path to validate
            
        Returns:
            Result indicating success or failure
        """
        try:
            if not path.exists():
                # Check if parent is writable
                if not path.parent.exists():
                    return Failure(PathResolutionError(f"Parent directory does not exist: {path.parent}"))
                
                if not os.access(path.parent, os.W_OK):
                    return Failure(PathResolutionError(f"Parent directory is not writable: {path.parent}"))
            else:
                if not os.access(path, os.W_OK):
                    return Failure(PathResolutionError(f"Path is not writable: {path}"))
            
            return Success(None)
            
        except (OSError, PermissionError) as e:
            return Failure(PathResolutionError(f"Failed to validate path: {e}"))
    
    def find_player_executable(self, player: PlayerType) -> Result[Path]:
        """Find the player executable.
        
        Args:
            player: The player type
            
        Returns:
            Result containing the executable path
        """
        executable_name = f"{player.value}.exe"
        
        # Check in detected installation directory
        install_result = self.detect_player_directory(player)
        if isinstance(install_result, Success):
            exe_path = install_result.value / executable_name
            if exe_path.exists():
                return Success(exe_path)
        
        # Check in PATH
        path_env = os.environ.get("PATH", "")
        for path_dir in path_env.split(os.pathsep):
            exe_path = Path(path_dir) / executable_name
            if exe_path.exists():
                return Success(exe_path)
        
        return Failure(PathResolutionError(f"Could not find {executable_name}"))

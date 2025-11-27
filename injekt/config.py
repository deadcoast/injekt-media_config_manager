"""Application configuration management."""

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, Dict, Any

from injekt.core.constants import (
    DEFAULT_ASSETS_DIR,
    DEFAULT_BACKUP_DIR,
    DEFAULT_STATE_FILE,
    DEFAULT_LOG_DIR,
    MAX_BACKUPS,
)
from injekt.core.models import PlayerType
from injekt.core.errors import ValidationError


@dataclass
class InjektConfig:
    """Application configuration."""
    assets_dir: Path = DEFAULT_ASSETS_DIR
    backup_dir: Path = DEFAULT_BACKUP_DIR
    state_file: Path = DEFAULT_STATE_FILE
    log_dir: Path = DEFAULT_LOG_DIR
    max_backups: int = MAX_BACKUPS
    default_player: PlayerType = PlayerType.MPV
    verbose: bool = False
    dry_run: bool = False
    output_format: str = "text"
    
    @classmethod
    def from_file(cls, config_path: Path) -> "InjektConfig":
        """Load configuration from a JSON file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            InjektConfig instance with values from file
            
        Raises:
            ValidationError: If the config file is invalid
        """
        if not config_path.exists():
            raise ValidationError(f"Config file not found: {config_path}")
        
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON in config file: {e}")
        except Exception as e:
            raise ValidationError(f"Failed to read config file: {e}")
        
        return cls._from_dict(data)
    
    @classmethod
    def from_env(cls) -> "InjektConfig":
        """Load configuration from environment variables.
        
        Environment variables:
            INJEKT_ASSETS_DIR: Assets directory path
            INJEKT_BACKUP_DIR: Backup directory path
            INJEKT_STATE_FILE: State file path
            INJEKT_LOG_DIR: Log directory path
            INJEKT_MAX_BACKUPS: Maximum number of backups to keep
            INJEKT_DEFAULT_PLAYER: Default player (mpv or vlc)
            INJEKT_VERBOSE: Enable verbose output (true/false)
            INJEKT_DRY_RUN: Enable dry-run mode (true/false)
            INJEKT_OUTPUT_FORMAT: Output format (text, json, table)
            
        Returns:
            InjektConfig instance with values from environment
        """
        config_dict: Dict[str, Any] = {}
        
        if assets_dir := os.getenv("INJEKT_ASSETS_DIR"):
            config_dict["assets_dir"] = Path(assets_dir)
        
        if backup_dir := os.getenv("INJEKT_BACKUP_DIR"):
            config_dict["backup_dir"] = Path(backup_dir)
        
        if state_file := os.getenv("INJEKT_STATE_FILE"):
            config_dict["state_file"] = Path(state_file)
        
        if log_dir := os.getenv("INJEKT_LOG_DIR"):
            config_dict["log_dir"] = Path(log_dir)
        
        if max_backups := os.getenv("INJEKT_MAX_BACKUPS"):
            try:
                config_dict["max_backups"] = int(max_backups)
            except ValueError:
                raise ValidationError(f"Invalid INJEKT_MAX_BACKUPS value: {max_backups}")
        
        if default_player := os.getenv("INJEKT_DEFAULT_PLAYER"):
            try:
                config_dict["default_player"] = PlayerType(default_player.lower())
            except ValueError:
                raise ValidationError(f"Invalid INJEKT_DEFAULT_PLAYER value: {default_player}")
        
        if verbose := os.getenv("INJEKT_VERBOSE"):
            config_dict["verbose"] = verbose.lower() in ("true", "1", "yes")
        
        if dry_run := os.getenv("INJEKT_DRY_RUN"):
            config_dict["dry_run"] = dry_run.lower() in ("true", "1", "yes")
        
        if output_format := os.getenv("INJEKT_OUTPUT_FORMAT"):
            config_dict["output_format"] = output_format
        
        return cls(**config_dict)
    
    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> "InjektConfig":
        """Create config from dictionary with validation.
        
        Args:
            data: Dictionary with configuration values
            
        Returns:
            InjektConfig instance
            
        Raises:
            ValidationError: If data is invalid
        """
        config_dict: Dict[str, Any] = {}
        
        if "assets_dir" in data:
            config_dict["assets_dir"] = Path(data["assets_dir"])
        
        if "backup_dir" in data:
            config_dict["backup_dir"] = Path(data["backup_dir"])
        
        if "state_file" in data:
            config_dict["state_file"] = Path(data["state_file"])
        
        if "log_dir" in data:
            config_dict["log_dir"] = Path(data["log_dir"])
        
        if "max_backups" in data:
            if not isinstance(data["max_backups"], int) or data["max_backups"] < 0:
                raise ValidationError(f"max_backups must be a non-negative integer")
            config_dict["max_backups"] = data["max_backups"]
        
        if "default_player" in data:
            try:
                config_dict["default_player"] = PlayerType(data["default_player"])
            except ValueError:
                raise ValidationError(f"Invalid default_player value: {data['default_player']}")
        
        if "verbose" in data:
            if not isinstance(data["verbose"], bool):
                raise ValidationError("verbose must be a boolean")
            config_dict["verbose"] = data["verbose"]
        
        if "dry_run" in data:
            if not isinstance(data["dry_run"], bool):
                raise ValidationError("dry_run must be a boolean")
            config_dict["dry_run"] = data["dry_run"]
        
        if "output_format" in data:
            if data["output_format"] not in ("text", "json", "table"):
                raise ValidationError(f"Invalid output_format: {data['output_format']}")
            config_dict["output_format"] = data["output_format"]
        
        return cls(**config_dict)
    
    def validate(self) -> None:
        """Validate configuration values.
        
        Raises:
            ValidationError: If configuration is invalid
        """
        if self.max_backups < 0:
            raise ValidationError("max_backups must be non-negative")
        
        if self.output_format not in ("text", "json", "table"):
            raise ValidationError(f"Invalid output_format: {self.output_format}")
        
        # Validate paths are absolute or can be resolved
        if not self.assets_dir.is_absolute():
            # Relative paths are allowed for assets_dir
            pass
        
        # Ensure backup, state, and log directories are absolute
        if not self.backup_dir.is_absolute():
            raise ValidationError("backup_dir must be an absolute path")
        
        if not self.state_file.is_absolute():
            raise ValidationError("state_file must be an absolute path")
        
        if not self.log_dir.is_absolute():
            raise ValidationError("log_dir must be an absolute path")
    
    def merge(self, other: "InjektConfig") -> "InjektConfig":
        """Merge this config with another, with other taking precedence.
        
        This implements the precedence order: user > profile > default
        where 'other' represents the higher precedence config.
        
        Args:
            other: Config to merge with (higher precedence)
            
        Returns:
            New InjektConfig with merged values
        """
        # Start with current config values
        merged_dict = asdict(self)
        
        # Override with non-default values from other
        other_dict = asdict(other)
        defaults = asdict(InjektConfig())
        
        for key, value in other_dict.items():
            # Special handling for Path objects
            if isinstance(value, Path):
                if value != defaults.get(key):
                    merged_dict[key] = value
            # Special handling for PlayerType enum
            elif isinstance(value, PlayerType):
                if value != defaults.get(key):
                    merged_dict[key] = value
            # For other types, check if different from default
            elif value != defaults.get(key):
                merged_dict[key] = value
        
        # Convert back to InjektConfig
        return InjektConfig(**merged_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for serialization.
        
        Returns:
            Dictionary representation of config
        """
        data = asdict(self)
        # Convert Path objects to strings
        data["assets_dir"] = str(data["assets_dir"])
        data["backup_dir"] = str(data["backup_dir"])
        data["state_file"] = str(data["state_file"])
        data["log_dir"] = str(data["log_dir"])
        # Convert PlayerType to string
        data["default_player"] = data["default_player"].value
        return data
    
    def save(self, config_path: Path) -> None:
        """Save configuration to a JSON file.
        
        Args:
            config_path: Path where to save the configuration
            
        Raises:
            ValidationError: If unable to save config
        """
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
        except Exception as e:
            raise ValidationError(f"Failed to save config file: {e}")

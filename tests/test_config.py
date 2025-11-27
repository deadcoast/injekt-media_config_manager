"""Unit tests for configuration management."""

import json
import os
import pytest
from pathlib import Path
from injekt.config import InjektConfig
from injekt.core.models import PlayerType
from injekt.core.errors import ValidationError
from injekt.core.constants import (
    DEFAULT_ASSETS_DIR,
    DEFAULT_BACKUP_DIR,
    DEFAULT_STATE_FILE,
    DEFAULT_LOG_DIR,
    MAX_BACKUPS,
)


def test_default_config():
    """Test default configuration values."""
    config = InjektConfig()
    
    assert config.assets_dir == DEFAULT_ASSETS_DIR
    assert config.backup_dir == DEFAULT_BACKUP_DIR
    assert config.state_file == DEFAULT_STATE_FILE
    assert config.log_dir == DEFAULT_LOG_DIR
    assert config.max_backups == MAX_BACKUPS
    assert config.default_player == PlayerType.MPV
    assert config.verbose is False
    assert config.dry_run is False
    assert config.output_format == "text"


def test_from_file_valid(tmp_path):
    """Test loading config from valid JSON file."""
    config_file = tmp_path / "config.json"
    config_data = {
        "assets_dir": "custom_assets",
        "backup_dir": str(tmp_path / "backups"),
        "state_file": str(tmp_path / "state.json"),
        "log_dir": str(tmp_path / "logs"),
        "max_backups": 10,
        "default_player": "vlc",
        "verbose": True,
        "dry_run": False,
        "output_format": "json"
    }
    
    with open(config_file, 'w') as f:
        json.dump(config_data, f)
    
    config = InjektConfig.from_file(config_file)
    
    assert config.assets_dir == Path("custom_assets")
    assert config.backup_dir == tmp_path / "backups"
    assert config.state_file == tmp_path / "state.json"
    assert config.log_dir == tmp_path / "logs"
    assert config.max_backups == 10
    assert config.default_player == PlayerType.VLC
    assert config.verbose is True
    assert config.dry_run is False
    assert config.output_format == "json"


def test_from_file_not_found():
    """Test loading config from non-existent file."""
    with pytest.raises(ValidationError, match="Config file not found"):
        InjektConfig.from_file(Path("nonexistent.json"))


def test_from_file_invalid_json(tmp_path):
    """Test loading config from invalid JSON file."""
    config_file = tmp_path / "config.json"
    with open(config_file, 'w') as f:
        f.write("{ invalid json }")
    
    with pytest.raises(ValidationError, match="Invalid JSON"):
        InjektConfig.from_file(config_file)


def test_from_env_empty():
    """Test loading config from environment with no variables set."""
    # Clear any existing env vars
    env_vars = [
        "INJEKT_ASSETS_DIR", "INJEKT_BACKUP_DIR", "INJEKT_STATE_FILE",
        "INJEKT_LOG_DIR", "INJEKT_MAX_BACKUPS", "INJEKT_DEFAULT_PLAYER",
        "INJEKT_VERBOSE", "INJEKT_DRY_RUN", "INJEKT_OUTPUT_FORMAT"
    ]
    for var in env_vars:
        os.environ.pop(var, None)
    
    config = InjektConfig.from_env()
    
    # Should have default values
    assert config.assets_dir == DEFAULT_ASSETS_DIR
    assert config.max_backups == MAX_BACKUPS


def test_from_env_with_values(tmp_path):
    """Test loading config from environment variables."""
    os.environ["INJEKT_ASSETS_DIR"] = "env_assets"
    os.environ["INJEKT_BACKUP_DIR"] = str(tmp_path / "backups")
    os.environ["INJEKT_STATE_FILE"] = str(tmp_path / "state.json")
    os.environ["INJEKT_LOG_DIR"] = str(tmp_path / "logs")
    os.environ["INJEKT_MAX_BACKUPS"] = "15"
    os.environ["INJEKT_DEFAULT_PLAYER"] = "vlc"
    os.environ["INJEKT_VERBOSE"] = "true"
    os.environ["INJEKT_DRY_RUN"] = "1"
    os.environ["INJEKT_OUTPUT_FORMAT"] = "table"
    
    try:
        config = InjektConfig.from_env()
        
        assert config.assets_dir == Path("env_assets")
        assert config.backup_dir == tmp_path / "backups"
        assert config.state_file == tmp_path / "state.json"
        assert config.log_dir == tmp_path / "logs"
        assert config.max_backups == 15
        assert config.default_player == PlayerType.VLC
        assert config.verbose is True
        assert config.dry_run is True
        assert config.output_format == "table"
    finally:
        # Clean up
        for var in ["INJEKT_ASSETS_DIR", "INJEKT_BACKUP_DIR", "INJEKT_STATE_FILE",
                    "INJEKT_LOG_DIR", "INJEKT_MAX_BACKUPS", "INJEKT_DEFAULT_PLAYER",
                    "INJEKT_VERBOSE", "INJEKT_DRY_RUN", "INJEKT_OUTPUT_FORMAT"]:
            os.environ.pop(var, None)


def test_from_env_invalid_max_backups():
    """Test loading config with invalid max_backups from env."""
    os.environ["INJEKT_MAX_BACKUPS"] = "not_a_number"
    
    try:
        with pytest.raises(ValidationError, match="Invalid INJEKT_MAX_BACKUPS"):
            InjektConfig.from_env()
    finally:
        os.environ.pop("INJEKT_MAX_BACKUPS", None)


def test_from_env_invalid_player():
    """Test loading config with invalid player from env."""
    os.environ["INJEKT_DEFAULT_PLAYER"] = "invalid_player"
    
    try:
        with pytest.raises(ValidationError, match="Invalid INJEKT_DEFAULT_PLAYER"):
            InjektConfig.from_env()
    finally:
        os.environ.pop("INJEKT_DEFAULT_PLAYER", None)


def test_validate_valid_config(tmp_path):
    """Test validation of valid config."""
    config = InjektConfig(
        backup_dir=tmp_path / "backups",
        state_file=tmp_path / "state.json",
        log_dir=tmp_path / "logs"
    )
    
    # Should not raise
    config.validate()


def test_validate_negative_max_backups():
    """Test validation fails for negative max_backups."""
    config = InjektConfig(max_backups=-1)
    
    with pytest.raises(ValidationError, match="max_backups must be non-negative"):
        config.validate()


def test_validate_invalid_output_format():
    """Test validation fails for invalid output format."""
    config = InjektConfig(output_format="invalid")
    
    with pytest.raises(ValidationError, match="Invalid output_format"):
        config.validate()


def test_validate_relative_backup_dir():
    """Test validation fails for relative backup_dir."""
    config = InjektConfig(backup_dir=Path("relative/path"))
    
    with pytest.raises(ValidationError, match="backup_dir must be an absolute path"):
        config.validate()


def test_merge_configs(tmp_path):
    """Test merging two configs with precedence."""
    base_config = InjektConfig(
        assets_dir=Path("base_assets"),
        max_backups=5,
        verbose=False
    )
    
    override_config = InjektConfig(
        assets_dir=Path("override_assets"),
        verbose=True,
        output_format="json"
    )
    
    merged = base_config.merge(override_config)
    
    # Override values should take precedence
    assert merged.assets_dir == Path("override_assets")
    assert merged.verbose is True
    assert merged.output_format == "json"
    # Non-overridden values should remain
    assert merged.max_backups == 5


def test_to_dict():
    """Test converting config to dictionary."""
    config = InjektConfig(
        assets_dir=Path("test_assets"),
        max_backups=10,
        default_player=PlayerType.VLC
    )
    
    data = config.to_dict()
    
    assert data["assets_dir"] == "test_assets"
    assert data["max_backups"] == 10
    assert data["default_player"] == "vlc"
    assert isinstance(data["assets_dir"], str)


def test_save_and_load(tmp_path):
    """Test saving and loading config."""
    config_file = tmp_path / "config.json"
    
    original = InjektConfig(
        assets_dir=Path("test_assets"),
        backup_dir=tmp_path / "backups",
        state_file=tmp_path / "state.json",
        log_dir=tmp_path / "logs",
        max_backups=10,
        default_player=PlayerType.VLC,
        verbose=True,
        output_format="json"
    )
    
    original.save(config_file)
    loaded = InjektConfig.from_file(config_file)
    
    assert loaded.assets_dir == original.assets_dir
    assert loaded.backup_dir == original.backup_dir
    assert loaded.max_backups == original.max_backups
    assert loaded.default_player == original.default_player
    assert loaded.verbose == original.verbose
    assert loaded.output_format == original.output_format

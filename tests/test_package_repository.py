"""Tests for PackageRepository."""

import json
import pytest
from pathlib import Path
from datetime import datetime

from injekt.business.package_repository import PackageRepository
from injekt.io.config_parser import ConfigParser
from injekt.core.models import PlayerType, ProfileType, FileType
from injekt.core.result import Success, Failure


@pytest.fixture
def temp_assets_dir(tmp_path):
    """Create a temporary assets directory with test packages."""
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir()
    
    # Create a test MPV package
    mpv_dir = assets_dir / "mpv-test"
    mpv_dir.mkdir()
    
    manifest = {
        "name": "mpv-test",
        "description": "Test MPV configuration",
        "player": "mpv",
        "version": "1.0.0",
        "profile": "default",
        "dependencies": [],
        "files": [
            {
                "source": "mpv.conf",
                "target": "mpv.conf",
                "type": "config",
                "required": True
            }
        ]
    }
    
    with open(mpv_dir / "manifest.json", "w") as f:
        json.dump(manifest, f)
    
    # Create the referenced config file
    (mpv_dir / "mpv.conf").write_text("# Test config")
    
    # Create a second package
    vlc_dir = assets_dir / "vlc-test"
    vlc_dir.mkdir()
    
    manifest2 = {
        "name": "vlc-test",
        "description": "Test VLC configuration",
        "player": "vlc",
        "version": "2.0.0",
        "profile": "quality",
        "dependencies": [],
        "files": [
            {
                "source": "vlcrc",
                "target": "vlcrc",
                "type": "config",
                "required": True
            }
        ]
    }
    
    with open(vlc_dir / "manifest.json", "w") as f:
        json.dump(manifest2, f)
    
    (vlc_dir / "vlcrc").write_text("# VLC config")
    
    return assets_dir


@pytest.fixture
def temp_state_file(tmp_path):
    """Create a temporary state file."""
    state_file = tmp_path / "state.json"
    
    state_data = {
        "installations": [
            {
                "package_name": "mpv-test",
                "version": "1.0.0",
                "installed_at": "2025-11-26T10:00:00",
                "target_dir": "/home/user/.config/mpv",
                "backup_dir": "/home/user/.injekt/backups/backup1",
                "files": ["mpv.conf"]
            }
        ]
    }
    
    with open(state_file, "w") as f:
        json.dump(state_data, f)
    
    return state_file


def test_list_packages_success(temp_assets_dir, tmp_path):
    """Test listing packages from assets directory."""
    state_file = tmp_path / "state.json"
    parser = ConfigParser()
    repo = PackageRepository(temp_assets_dir, state_file, parser)
    
    result = repo.list_packages()
    
    assert isinstance(result, Success)
    packages = result.value
    assert len(packages) == 2
    
    package_names = {p.name for p in packages}
    assert "mpv-test" in package_names
    assert "vlc-test" in package_names


def test_list_packages_nonexistent_directory(tmp_path):
    """Test listing packages when assets directory doesn't exist."""
    assets_dir = tmp_path / "nonexistent"
    state_file = tmp_path / "state.json"
    parser = ConfigParser()
    repo = PackageRepository(assets_dir, state_file, parser)
    
    result = repo.list_packages()
    
    assert isinstance(result, Failure)


def test_get_package_success(temp_assets_dir, tmp_path):
    """Test getting a specific package by name."""
    state_file = tmp_path / "state.json"
    parser = ConfigParser()
    repo = PackageRepository(temp_assets_dir, state_file, parser)
    
    result = repo.get_package("mpv-test")
    
    assert isinstance(result, Success)
    package = result.value
    assert package.name == "mpv-test"
    assert package.description == "Test MPV configuration"
    assert package.player == PlayerType.MPV
    assert package.version == "1.0.0"


def test_get_package_not_found(temp_assets_dir, tmp_path):
    """Test getting a package that doesn't exist."""
    state_file = tmp_path / "state.json"
    parser = ConfigParser()
    repo = PackageRepository(temp_assets_dir, state_file, parser)
    
    result = repo.get_package("nonexistent-package")
    
    assert isinstance(result, Failure)


def test_get_installed_packages_success(temp_assets_dir, temp_state_file):
    """Test getting installed packages from state file."""
    parser = ConfigParser()
    repo = PackageRepository(temp_assets_dir, temp_state_file, parser)
    
    result = repo.get_installed_packages()
    
    assert isinstance(result, Success)
    packages = result.value
    assert len(packages) == 1
    assert packages[0].name == "mpv-test"


def test_get_installed_packages_empty_state(temp_assets_dir, tmp_path):
    """Test getting installed packages when state file doesn't exist."""
    state_file = tmp_path / "state.json"
    parser = ConfigParser()
    repo = PackageRepository(temp_assets_dir, state_file, parser)
    
    result = repo.get_installed_packages()
    
    assert isinstance(result, Success)
    packages = result.value
    assert len(packages) == 0

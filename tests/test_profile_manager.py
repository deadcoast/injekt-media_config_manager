"""Unit tests for ProfileManager."""

import json
import pytest
from pathlib import Path
from datetime import datetime

from injekt.business.profile_manager import ProfileManager, ProfileError
from injekt.core.models import (
    Package, PackageFile, PlayerType, ProfileType, FileType, Backup
)
from injekt.core.result import Success, Failure
from injekt.core.errors import PackageNotFoundError


class MockPackageRepository:
    """Mock package repository for testing."""
    
    def __init__(self, packages=None):
        self.packages = packages or []
    
    def list_packages(self):
        return Success(self.packages)
    
    def get_package(self, name):
        for pkg in self.packages:
            if pkg.name == name:
                return Success(pkg)
        return Failure(PackageNotFoundError(f"Package not found: {name}"))
    
    def get_installed_packages(self):
        return Success([])


class MockBackupManager:
    """Mock backup manager for testing."""
    
    def __init__(self, should_fail=False):
        self.should_fail = should_fail
        self.backups_created = []
    
    def create_backup(self, package, target_dir):
        if self.should_fail:
            return Failure(ProfileError("Backup failed"))
        
        backup = Backup(
            backup_id=f"{package.name}_backup",
            timestamp=datetime.now(),
            package_name=package.name,
            backup_dir=Path("/tmp/backup"),
            files=[],
            target_dir=target_dir
        )
        self.backups_created.append(backup)
        return Success(backup)
    
    def list_backups(self):
        return Success(self.backups_created)
    
    def restore_backup(self, backup_id):
        return Success(None)
    
    def cleanup_old_backups(self, keep_count=5):
        return Success(0)


class MockInstaller:
    """Mock installer for testing."""
    
    def __init__(self, should_fail=False):
        self.should_fail = should_fail
        self.installed_packages = []
    
    def install_package(self, package, target_dir, dry_run=False):
        if self.should_fail:
            return Failure(ProfileError("Installation failed"))
        
        self.installed_packages.append(package)
        from injekt.core.models import InstallationState
        state = InstallationState(
            package=package,
            target_dir=target_dir,
            backup_dir=None,
            installed_files=[],
            timestamp=datetime.now()
        )
        return Success(state)
    
    def uninstall_package(self, package_name, dry_run=False):
        return Success([])
    
    def verify_installation(self, package):
        return Success([])


def create_test_package(name, profile, player):
    """Helper to create a test package."""
    return Package(
        name=name,
        description=f"Test {profile.value} package",
        player=player,
        version="1.0.0",
        files=[
            PackageFile(
                source_path=Path(f"/source/{name}.conf"),
                target_path=Path(f"{name}.conf"),
                file_type=FileType.CONFIG,
                required=True
            )
        ],
        dependencies=[],
        profile=profile
    )


def test_list_profiles():
    """Test listing all available profiles."""
    repo = MockPackageRepository()
    backup_mgr = MockBackupManager()
    installer = MockInstaller()
    state_file = Path("/tmp/state.json")
    
    manager = ProfileManager(repo, backup_mgr, installer, state_file)
    
    result = manager.list_profiles()
    
    assert isinstance(result, Success)
    profiles = result.value
    assert ProfileType.PERFORMANCE in profiles
    assert ProfileType.QUALITY in profiles
    assert ProfileType.CINEMATIC in profiles
    assert ProfileType.DEFAULT in profiles


def test_switch_profile_success(tmp_path):
    """Test successfully switching to a different profile."""
    # Create test packages
    packages = [
        create_test_package("mpv-performance", ProfileType.PERFORMANCE, PlayerType.MPV),
        create_test_package("mpv-quality", ProfileType.QUALITY, PlayerType.MPV),
    ]
    
    repo = MockPackageRepository(packages)
    backup_mgr = MockBackupManager()
    installer = MockInstaller()
    state_file = tmp_path / "state.json"
    
    manager = ProfileManager(repo, backup_mgr, installer, state_file)
    
    target_dir = tmp_path / "mpv"
    target_dir.mkdir()
    
    result = manager.switch_profile(
        ProfileType.PERFORMANCE,
        PlayerType.MPV,
        target_dir
    )
    
    assert isinstance(result, Success)
    assert result.value.name == "mpv-performance"
    assert len(backup_mgr.backups_created) == 1
    assert len(installer.installed_packages) == 1


def test_switch_profile_no_matching_package(tmp_path):
    """Test switching to a profile with no matching package."""
    # Create packages for different player
    packages = [
        create_test_package("vlc-quality", ProfileType.QUALITY, PlayerType.VLC),
    ]
    
    repo = MockPackageRepository(packages)
    backup_mgr = MockBackupManager()
    installer = MockInstaller()
    state_file = tmp_path / "state.json"
    
    manager = ProfileManager(repo, backup_mgr, installer, state_file)
    
    target_dir = tmp_path / "mpv"
    target_dir.mkdir()
    
    result = manager.switch_profile(
        ProfileType.PERFORMANCE,
        PlayerType.MPV,
        target_dir
    )
    
    assert isinstance(result, Failure)
    assert "No package found" in str(result.error)


def test_switch_profile_backup_fails(tmp_path):
    """Test profile switch when backup creation fails."""
    packages = [
        create_test_package("mpv-quality", ProfileType.QUALITY, PlayerType.MPV),
    ]
    
    repo = MockPackageRepository(packages)
    backup_mgr = MockBackupManager(should_fail=True)
    installer = MockInstaller()
    state_file = tmp_path / "state.json"
    
    manager = ProfileManager(repo, backup_mgr, installer, state_file)
    
    target_dir = tmp_path / "mpv"
    target_dir.mkdir()
    
    result = manager.switch_profile(
        ProfileType.QUALITY,
        PlayerType.MPV,
        target_dir
    )
    
    assert isinstance(result, Failure)
    assert "backup" in str(result.error).lower()


def test_switch_profile_installation_fails(tmp_path):
    """Test profile switch when installation fails."""
    packages = [
        create_test_package("mpv-quality", ProfileType.QUALITY, PlayerType.MPV),
    ]
    
    repo = MockPackageRepository(packages)
    backup_mgr = MockBackupManager()
    installer = MockInstaller(should_fail=True)
    state_file = tmp_path / "state.json"
    
    manager = ProfileManager(repo, backup_mgr, installer, state_file)
    
    target_dir = tmp_path / "mpv"
    target_dir.mkdir()
    
    result = manager.switch_profile(
        ProfileType.QUALITY,
        PlayerType.MPV,
        target_dir
    )
    
    assert isinstance(result, Failure)
    assert "install" in str(result.error).lower()


def test_switch_profile_dry_run(tmp_path):
    """Test profile switch in dry-run mode."""
    packages = [
        create_test_package("mpv-cinematic", ProfileType.CINEMATIC, PlayerType.MPV),
    ]
    
    repo = MockPackageRepository(packages)
    backup_mgr = MockBackupManager()
    installer = MockInstaller()
    state_file = tmp_path / "state.json"
    
    manager = ProfileManager(repo, backup_mgr, installer, state_file)
    
    target_dir = tmp_path / "mpv"
    target_dir.mkdir()
    
    result = manager.switch_profile(
        ProfileType.CINEMATIC,
        PlayerType.MPV,
        target_dir,
        dry_run=True
    )
    
    assert isinstance(result, Success)
    assert result.value.name == "mpv-cinematic"
    # In dry-run, no backup or installation should occur
    assert len(backup_mgr.backups_created) == 0
    assert len(installer.installed_packages) == 0


def test_get_active_profile_no_state_file(tmp_path):
    """Test getting active profile when no state file exists."""
    repo = MockPackageRepository()
    backup_mgr = MockBackupManager()
    installer = MockInstaller()
    state_file = tmp_path / "state.json"
    
    manager = ProfileManager(repo, backup_mgr, installer, state_file)
    
    result = manager.get_active_profile(PlayerType.MPV)
    
    assert isinstance(result, Success)
    assert result.value is None


def test_get_active_profile_with_state(tmp_path):
    """Test getting active profile from state file."""
    repo = MockPackageRepository()
    backup_mgr = MockBackupManager()
    installer = MockInstaller()
    state_file = tmp_path / "state.json"
    
    # Create state file with active profile
    state_data = {
        'installations': [],
        'active_profiles': {
            'mpv': 'quality',
            'vlc': 'performance'
        }
    }
    state_file.parent.mkdir(parents=True, exist_ok=True)
    with open(state_file, 'w') as f:
        json.dump(state_data, f)
    
    manager = ProfileManager(repo, backup_mgr, installer, state_file)
    
    result = manager.get_active_profile(PlayerType.MPV)
    
    assert isinstance(result, Success)
    assert result.value == ProfileType.QUALITY


def test_get_active_profile_player_not_set(tmp_path):
    """Test getting active profile for player with no profile set."""
    repo = MockPackageRepository()
    backup_mgr = MockBackupManager()
    installer = MockInstaller()
    state_file = tmp_path / "state.json"
    
    # Create state file with active profile for different player
    state_data = {
        'installations': [],
        'active_profiles': {
            'vlc': 'performance'
        }
    }
    state_file.parent.mkdir(parents=True, exist_ok=True)
    with open(state_file, 'w') as f:
        json.dump(state_data, f)
    
    manager = ProfileManager(repo, backup_mgr, installer, state_file)
    
    result = manager.get_active_profile(PlayerType.MPV)
    
    assert isinstance(result, Success)
    assert result.value is None


def test_update_active_profile(tmp_path):
    """Test updating active profile in state file."""
    packages = [
        create_test_package("mpv-quality", ProfileType.QUALITY, PlayerType.MPV),
    ]
    
    repo = MockPackageRepository(packages)
    backup_mgr = MockBackupManager()
    installer = MockInstaller()
    state_file = tmp_path / "state.json"
    
    manager = ProfileManager(repo, backup_mgr, installer, state_file)
    
    target_dir = tmp_path / "mpv"
    target_dir.mkdir()
    
    # Switch profile
    result = manager.switch_profile(
        ProfileType.QUALITY,
        PlayerType.MPV,
        target_dir
    )
    
    assert isinstance(result, Success)
    
    # Verify state file was updated
    assert state_file.exists()
    with open(state_file, 'r') as f:
        data = json.load(f)
    
    assert 'active_profiles' in data
    assert data['active_profiles']['mpv'] == 'quality'


def test_switch_profile_preserves_existing_state(tmp_path):
    """Test that switching profile preserves existing installation state."""
    packages = [
        create_test_package("mpv-performance", ProfileType.PERFORMANCE, PlayerType.MPV),
    ]
    
    repo = MockPackageRepository(packages)
    backup_mgr = MockBackupManager()
    installer = MockInstaller()
    state_file = tmp_path / "state.json"
    
    # Create existing state file
    existing_state = {
        'installations': [
            {
                'package_name': 'existing-package',
                'version': '1.0.0',
                'installed_at': '2025-01-01T00:00:00',
                'target_dir': '/tmp/test',
                'files': ['test.conf']
            }
        ],
        'active_profiles': {
            'vlc': 'cinematic'
        }
    }
    state_file.parent.mkdir(parents=True, exist_ok=True)
    with open(state_file, 'w') as f:
        json.dump(existing_state, f)
    
    manager = ProfileManager(repo, backup_mgr, installer, state_file)
    
    target_dir = tmp_path / "mpv"
    target_dir.mkdir()
    
    # Switch profile
    result = manager.switch_profile(
        ProfileType.PERFORMANCE,
        PlayerType.MPV,
        target_dir
    )
    
    assert isinstance(result, Success)
    
    # Verify existing state was preserved
    with open(state_file, 'r') as f:
        data = json.load(f)
    
    assert len(data['installations']) == 1
    assert data['installations'][0]['package_name'] == 'existing-package'
    assert data['active_profiles']['vlc'] == 'cinematic'
    assert data['active_profiles']['mpv'] == 'performance'


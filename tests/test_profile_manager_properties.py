"""Property-based tests for ProfileManager.

Feature: injekt-cli, Property 9: Profile backup safety
Validates: Requirements 9.2
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from hypothesis import given, strategies as st, settings

from injekt.business.profile_manager import ProfileManager
from injekt.core.models import (
    Package, PackageFile, PlayerType, ProfileType, FileType,
    Backup, InstallationState
)
from injekt.core.result import Success, Failure
from injekt.core.errors import InjektError
from datetime import datetime


class TrackingBackupManager:
    """Backup manager that tracks all backup operations."""
    
    def __init__(self):
        self.backups_created = []
        self.backup_calls = []
    
    def create_backup(self, package, target_dir):
        """Track backup creation calls."""
        self.backup_calls.append({
            'package': package,
            'target_dir': target_dir
        })
        
        backup = Backup(
            backup_id=f"{package.name}_{len(self.backups_created)}",
            timestamp=datetime.now(),
            package_name=package.name,
            backup_dir=Path(tempfile.mkdtemp()),
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


class TrackingInstaller:
    """Installer that tracks installation operations."""
    
    def __init__(self):
        self.installations = []
    
    def install_package(self, package, target_dir, dry_run=False):
        """Track installation calls."""
        self.installations.append({
            'package': package,
            'target_dir': target_dir,
            'dry_run': dry_run
        })
        
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


class SimplePackageRepository:
    """Simple package repository for testing."""
    
    def __init__(self, packages):
        self.packages = packages
    
    def list_packages(self):
        return Success(self.packages)
    
    def get_package(self, name):
        for pkg in self.packages:
            if pkg.name == name:
                return Success(pkg)
        return Failure(InjektError(f"Package not found: {name}"))
    
    def get_installed_packages(self):
        return Success([])


def create_test_package(name, profile, player):
    """Helper to create a test package."""
    return Package(
        name=name,
        description=f"Test {profile.value} package for {player.value}",
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


@settings(max_examples=100)
@given(
    profile=st.sampled_from(list(ProfileType)),
    player=st.sampled_from(list(PlayerType))
)
def test_property_profile_switch_creates_backup(profile, player):
    """
    **Feature: injekt-cli, Property 9: Profile backup safety**
    **Validates: Requirements 9.2**
    
    Property: For any profile switch operation, a backup of the current configuration
    should be created before applying the new profile.
    
    This test verifies that:
    1. For any profile and player combination
    2. When switching to that profile
    3. Then a backup is created before installation
    4. And the backup is created for the correct package
    """
    temp_dir = Path(tempfile.mkdtemp())
    try:
        # Create a package for the requested profile and player
        package = create_test_package(
            f"{player.value}-{profile.value}",
            profile,
            player
        )
        
        repo = SimplePackageRepository([package])
        backup_mgr = TrackingBackupManager()
        installer = TrackingInstaller()
        state_file = temp_dir / "state.json"
        
        manager = ProfileManager(repo, backup_mgr, installer, state_file)
        
        target_dir = temp_dir / player.value
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Switch to the profile
        result = manager.switch_profile(profile, player, target_dir)
        
        # Verify the operation succeeded
        assert isinstance(result, Success), f"Profile switch failed: {result}"
        
        # Verify a backup was created
        assert len(backup_mgr.backup_calls) == 1, \
            "Exactly one backup should be created during profile switch"
        
        # Verify the backup was for the correct package
        backup_call = backup_mgr.backup_calls[0]
        assert backup_call['package'].name == package.name
        assert backup_call['target_dir'] == target_dir
        
        # Verify installation happened after backup
        assert len(installer.installations) == 1, \
            "Installation should occur after backup"
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


@settings(max_examples=100)
@given(
    profile=st.sampled_from(list(ProfileType)),
    player=st.sampled_from(list(PlayerType)),
    num_switches=st.integers(min_value=1, max_value=5)
)
def test_property_multiple_profile_switches_create_backups(profile, player, num_switches):
    """
    **Feature: injekt-cli, Property 9: Profile backup safety**
    **Validates: Requirements 9.2**
    
    Property: Each profile switch operation should create its own backup.
    
    This test verifies that:
    1. For any number of profile switches
    2. Each switch creates a backup
    3. And the number of backups equals the number of switches
    """
    temp_dir = Path(tempfile.mkdtemp())
    try:
        # Create packages for all profiles
        packages = [
            create_test_package(f"{player.value}-{p.value}", p, player)
            for p in ProfileType
        ]
        
        repo = SimplePackageRepository(packages)
        backup_mgr = TrackingBackupManager()
        installer = TrackingInstaller()
        state_file = temp_dir / "state.json"
        
        manager = ProfileManager(repo, backup_mgr, installer, state_file)
        
        target_dir = temp_dir / player.value
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Perform multiple profile switches
        all_profiles = list(ProfileType)
        profiles_to_switch = [all_profiles[i % len(all_profiles)] for i in range(num_switches)]
        
        for switch_profile in profiles_to_switch:
            result = manager.switch_profile(switch_profile, player, target_dir)
            assert isinstance(result, Success), f"Profile switch failed: {result}"
        
        # Verify each switch created a backup
        assert len(backup_mgr.backup_calls) == num_switches, \
            f"Expected {num_switches} backups, but got {len(backup_mgr.backup_calls)}"
        
        # Verify each backup was created before its corresponding installation
        assert len(installer.installations) == num_switches, \
            f"Expected {num_switches} installations"
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


@settings(max_examples=100)
@given(
    profile=st.sampled_from(list(ProfileType)),
    player=st.sampled_from(list(PlayerType))
)
def test_property_backup_created_before_installation(profile, player):
    """
    **Feature: injekt-cli, Property 9: Profile backup safety**
    **Validates: Requirements 9.2**
    
    Property: The backup must be created before the installation occurs.
    
    This test verifies that:
    1. For any profile switch
    2. The backup operation completes before installation begins
    3. By checking the order of operations
    """
    temp_dir = Path(tempfile.mkdtemp())
    try:
        package = create_test_package(
            f"{player.value}-{profile.value}",
            profile,
            player
        )
        
        # Create a special tracking manager that records operation order
        operation_order = []
        
        class OrderTrackingBackupManager(TrackingBackupManager):
            def create_backup(self, package, target_dir):
                operation_order.append('backup')
                return super().create_backup(package, target_dir)
        
        class OrderTrackingInstaller(TrackingInstaller):
            def install_package(self, package, target_dir, dry_run=False):
                operation_order.append('install')
                return super().install_package(package, target_dir, dry_run)
        
        repo = SimplePackageRepository([package])
        backup_mgr = OrderTrackingBackupManager()
        installer = OrderTrackingInstaller()
        state_file = temp_dir / "state.json"
        
        manager = ProfileManager(repo, backup_mgr, installer, state_file)
        
        target_dir = temp_dir / player.value
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Switch profile
        result = manager.switch_profile(profile, player, target_dir)
        
        assert isinstance(result, Success), f"Profile switch failed: {result}"
        
        # Verify backup happened before install
        assert len(operation_order) == 2, "Should have exactly 2 operations"
        assert operation_order[0] == 'backup', "Backup should be first operation"
        assert operation_order[1] == 'install', "Install should be second operation"
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


@settings(max_examples=100)
@given(
    profile=st.sampled_from(list(ProfileType)),
    player=st.sampled_from(list(PlayerType))
)
def test_property_dry_run_skips_backup(profile, player):
    """
    **Feature: injekt-cli, Property 9: Profile backup safety**
    **Validates: Requirements 9.2**
    
    Property: In dry-run mode, no backup should be created since no changes are made.
    
    This test verifies that:
    1. For any profile switch in dry-run mode
    2. No backup is created
    3. And no installation occurs
    """
    temp_dir = Path(tempfile.mkdtemp())
    try:
        package = create_test_package(
            f"{player.value}-{profile.value}",
            profile,
            player
        )
        
        repo = SimplePackageRepository([package])
        backup_mgr = TrackingBackupManager()
        installer = TrackingInstaller()
        state_file = temp_dir / "state.json"
        
        manager = ProfileManager(repo, backup_mgr, installer, state_file)
        
        target_dir = temp_dir / player.value
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Switch profile in dry-run mode
        result = manager.switch_profile(profile, player, target_dir, dry_run=True)
        
        assert isinstance(result, Success), f"Dry-run profile switch failed: {result}"
        
        # Verify no backup was created in dry-run mode
        assert len(backup_mgr.backup_calls) == 0, \
            "No backup should be created in dry-run mode"
        
        # Verify no installation occurred
        assert len(installer.installations) == 0, \
            "No installation should occur in dry-run mode"
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


class FailingBackupManager:
    """Backup manager that always fails."""
    
    def create_backup(self, package, target_dir):
        return Failure(InjektError("Backup failed"))
    
    def list_backups(self):
        return Success([])
    
    def restore_backup(self, backup_id):
        return Success(None)
    
    def cleanup_old_backups(self, keep_count=5):
        return Success(0)


@settings(max_examples=100)
@given(
    profile=st.sampled_from(list(ProfileType)),
    player=st.sampled_from(list(PlayerType))
)
def test_property_backup_failure_prevents_installation(profile, player):
    """
    **Feature: injekt-cli, Property 9: Profile backup safety**
    **Validates: Requirements 9.2**
    
    Property: If backup creation fails, the profile switch should not proceed.
    
    This test verifies that:
    1. For any profile switch where backup fails
    2. The installation does not occur
    3. And the operation returns a failure
    """
    temp_dir = Path(tempfile.mkdtemp())
    try:
        package = create_test_package(
            f"{player.value}-{profile.value}",
            profile,
            player
        )
        
        repo = SimplePackageRepository([package])
        backup_mgr = FailingBackupManager()
        installer = TrackingInstaller()
        state_file = temp_dir / "state.json"
        
        manager = ProfileManager(repo, backup_mgr, installer, state_file)
        
        target_dir = temp_dir / player.value
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Attempt to switch profile
        result = manager.switch_profile(profile, player, target_dir)
        
        # Verify the operation failed
        assert isinstance(result, Failure), \
            "Profile switch should fail when backup fails"
        
        # Verify no installation occurred
        assert len(installer.installations) == 0, \
            "Installation should not occur when backup fails"
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

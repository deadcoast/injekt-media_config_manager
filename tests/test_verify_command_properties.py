"""Property-based tests for verify command."""

import pytest
import tempfile
import shutil
from hypothesis import given, strategies as st, settings
from pathlib import Path
from datetime import datetime

from injekt.cli.commands import VerifyCommand
from injekt.cli.output import OutputFormatter
from injekt.business.package_repository import PackageRepository
from injekt.business.installer import Installer
from injekt.core.models import Package, PackageFile, PlayerType, ProfileType, FileType, InstallationState
from injekt.core.result import Success
from injekt.io.config_parser import ConfigParser
from injekt.business.backup_manager import BackupManager
from injekt.io.backup_storage import BackupStorage
from injekt.io.file_operations import FileOperations
from injekt.business.validator import ConfigValidatorImpl
from rich.console import Console
from io import StringIO


# **Feature: injekt-cli, Property 10: Installation verification completeness**
# **Validates: Requirements 10.1, 10.2**
@given(
    package_name=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_')),
    num_files=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=100)
def test_property_verification_checks_all_required_files(package_name, num_files):
    """
    Property: For any installed package, verification should check that all required files exist.
    
    This property ensures that the verify command checks every required file in a package.
    """
    # Create temporary directory
    tmp_path = Path(tempfile.mkdtemp())
    
    try:
        # Create package with required files
        files = []
        for i in range(num_files):
            source_path = tmp_path / "source" / f"file{i}.conf"
            target_path = Path(f"file{i}.conf")
            files.append(PackageFile(
                source_path=source_path,
                target_path=target_path,
                file_type=FileType.CONFIG,
                required=True
            ))
        
        package = Package(
            name=package_name,
            description="Test package",
            player=PlayerType.MPV,
            version="1.0.0",
            files=files,
            dependencies=[],
            profile=ProfileType.DEFAULT
        )
        
        # Set up components
        assets_dir = tmp_path / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        state_file = tmp_path / "state.json"
        backup_dir = tmp_path / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        target_dir = tmp_path / "target"
        target_dir.mkdir(parents=True, exist_ok=True)
        
        config_parser = ConfigParser()
        backup_storage = BackupStorage(backup_dir)
        backup_manager = BackupManager(backup_storage)
        file_ops = FileOperations()
        validator = ConfigValidatorImpl()
        
        repo = PackageRepository(assets_dir, state_file, config_parser)
        repo.get_package = lambda name: Success(package)
        
        installer = Installer(file_ops, backup_manager, validator, config_parser, state_file)
        
        # Create installation state with all files
        installation_state = InstallationState(
            package=package,
            target_dir=target_dir,
            backup_dir=None,
            installed_files=[target_dir / f.target_path for f in files],
            timestamp=datetime.now()
        )
        
        # Write installation state
        config_parser.write_installation_state(state_file, [installation_state])
        
        # Create some files but not all (to trigger issues)
        for i in range(num_files // 2):  # Only create half the files
            file_path = target_dir / f"file{i}.conf"
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text("test content")
        
        # Set up output
        output_buffer = StringIO()
        console = Console(file=output_buffer, force_terminal=False, width=120)
        output_formatter = OutputFormatter(output_format="text", console=console)
        
        # Create verify command
        command = VerifyCommand(repo, installer, output_formatter)
        
        # Execute verification
        exit_code = command.execute(package_name)
        
        # Property: If not all required files exist, verification should report issues
        if num_files > num_files // 2:  # If we didn't create all files
            # Should find issues
            verify_result = installer.verify_installation(package)
            assert isinstance(verify_result, Success)
            issues = verify_result.value
            
            # Should have at least one issue for missing files
            assert len(issues) > 0, "Verification should detect missing required files"
            
            # Should report the missing files
            missing_count = num_files - (num_files // 2)
            assert len(issues) >= missing_count, f"Should report at least {missing_count} missing files"
    
    finally:
        # Clean up temporary directory
        shutil.rmtree(tmp_path, ignore_errors=True)

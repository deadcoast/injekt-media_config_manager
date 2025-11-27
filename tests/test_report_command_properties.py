"""Property-based tests for report command."""

import pytest
import tempfile
import shutil
from hypothesis import given, strategies as st, settings
from pathlib import Path
from datetime import datetime
from io import StringIO

from injekt.cli.commands import ReportCommand
from injekt.cli.output import OutputFormatter
from injekt.business.package_repository import PackageRepository
from injekt.core.models import Package, PackageFile, PlayerType, ProfileType, FileType, InstallationState
from injekt.core.result import Success
from injekt.io.config_parser import ConfigParser
from rich.console import Console


# **Feature: injekt-cli, Property 14: Report completeness**
# **Validates: Requirements 15.1, 15.2, 15.3, 15.4**
@given(
    num_packages=st.integers(min_value=1, max_value=3)
)
@settings(max_examples=50)
def test_property_report_includes_all_installed_packages(num_packages):
    """
    Property: For any installed configuration, generating a report should include all packages.
    
    This property ensures that the report command lists every installed package.
    """
    tmp_path = Path(tempfile.mkdtemp())
    
    try:
        # Create packages
        packages = []
        for i in range(num_packages):
            package = Package(
                name=f"package-{i}",
                description=f"Test package {i}",
                player=PlayerType.MPV,
                version=f"1.{i}.0",
                files=[],
                dependencies=[],
                profile=ProfileType.DEFAULT
            )
            packages.append(package)
        
        # Set up components
        assets_dir = tmp_path / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        state_file = tmp_path / "state.json"
        
        config_parser = ConfigParser()
        
        repo = PackageRepository(assets_dir, state_file, config_parser)
        repo.get_installed_packages = lambda: Success(packages)
        
        # Set up output
        output_buffer = StringIO()
        console = Console(file=output_buffer, force_terminal=False, width=120)
        output_formatter = OutputFormatter(output_format="text", console=console)
        
        # Create report command
        command = ReportCommand(repo, output_formatter)
        
        # Execute report
        exit_code = command.execute()
        
        # Property: Report should include all installed packages
        assert exit_code == 0
        output = output_buffer.getvalue()
        
        # Check that all package names appear in the report
        for package in packages:
            assert package.name in output, f"Report should include package {package.name}"
            assert package.version in output, f"Report should include version {package.version}"
    
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)

"""Tests for OutputFormatter."""

import json
from io import StringIO
from rich.console import Console

from injekt.cli.output import OutputFormatter
from injekt.core.result import Success, Failure
from injekt.core.models import Package, PlayerType, ProfileType, PackageFile, FileType
from injekt.core.errors import InjektError
from pathlib import Path


def test_format_success_text():
    """Test formatting success message in text mode."""
    output = StringIO()
    console = Console(file=output, force_terminal=True, width=80)
    formatter = OutputFormatter(output_format="text", console=console)
    
    formatter.format_success("Operation completed")
    
    result = output.getvalue()
    assert "Operation completed" in result


def test_format_error_text():
    """Test formatting error message in text mode."""
    output = StringIO()
    console = Console(file=output, force_terminal=True, width=80)
    formatter = OutputFormatter(output_format="text", console=console)
    
    formatter.format_error("Something went wrong")
    
    result = output.getvalue()
    assert "Something went wrong" in result


def test_format_warning_text():
    """Test formatting warning message in text mode."""
    output = StringIO()
    console = Console(file=output, force_terminal=True, width=80)
    formatter = OutputFormatter(output_format="text", console=console)
    
    formatter.format_warning("This is a warning")
    
    result = output.getvalue()
    assert "This is a warning" in result


def test_format_success_json():
    """Test formatting success message in JSON mode."""
    output = StringIO()
    console = Console(file=output, force_terminal=False, width=80)
    formatter = OutputFormatter(output_format="json", console=console)
    
    formatter.format_success("Operation completed")
    
    result = output.getvalue()
    data = json.loads(result)
    assert data["status"] == "success"
    assert data["message"] == "Operation completed"


def test_format_error_json():
    """Test formatting error message in JSON mode."""
    output = StringIO()
    console = Console(file=output, force_terminal=False, width=80)
    formatter = OutputFormatter(output_format="json", console=console)
    
    formatter.format_error("Something went wrong")
    
    result = output.getvalue()
    data = json.loads(result)
    assert data["status"] == "error"
    assert data["message"] == "Something went wrong"


def test_format_result_success():
    """Test formatting a Success result."""
    output = StringIO()
    console = Console(file=output, force_terminal=True, width=80)
    formatter = OutputFormatter(output_format="text", console=console)
    
    result = Success("Test value")
    formatter.format_result(result, success_message="Custom success")
    
    output_text = output.getvalue()
    assert "Custom success" in output_text


def test_format_result_failure():
    """Test formatting a Failure result."""
    output = StringIO()
    console = Console(file=output, force_terminal=True, width=80)
    formatter = OutputFormatter(output_format="text", console=console)
    
    result = Failure(InjektError("Test error"))
    formatter.format_result(result)
    
    output_text = output.getvalue()
    assert "Test error" in output_text


def test_format_table_text():
    """Test formatting table in text mode."""
    output = StringIO()
    console = Console(file=output, force_terminal=True, width=120)
    formatter = OutputFormatter(output_format="text", console=console)
    
    data = [
        {"name": "pkg1", "version": "1.0"},
        {"name": "pkg2", "version": "2.0"}
    ]
    formatter.format_table(data, columns=["name", "version"], title="Packages")
    
    result = output.getvalue()
    assert "pkg1" in result
    assert "pkg2" in result


def test_format_table_json():
    """Test formatting table in JSON mode."""
    output = StringIO()
    console = Console(file=output, force_terminal=False, width=80)
    formatter = OutputFormatter(output_format="json", console=console)
    
    data = [
        {"name": "pkg1", "version": "1.0"},
        {"name": "pkg2", "version": "2.0"}
    ]
    formatter.format_table(data, columns=["name", "version"])
    
    result = output.getvalue()
    parsed = json.loads(result)
    assert len(parsed["data"]) == 2
    assert parsed["data"][0]["name"] == "pkg1"


def test_format_package_list_text():
    """Test formatting package list in text mode."""
    output = StringIO()
    console = Console(file=output, force_terminal=True, width=120)
    formatter = OutputFormatter(output_format="text", console=console)
    
    packages = [
        Package(
            name="test-pkg",
            description="Test package",
            player=PlayerType.MPV,
            version="1.0",
            files=[],
            dependencies=[],
            profile=ProfileType.DEFAULT
        )
    ]
    
    formatter.format_package_list(packages, installed_packages=["test-pkg"])
    
    result = output.getvalue()
    assert "test-pkg" in result
    assert "Test package" in result


def test_format_package_list_json():
    """Test formatting package list in JSON mode."""
    output = StringIO()
    console = Console(file=output, force_terminal=False, width=80)
    formatter = OutputFormatter(output_format="json", console=console)
    
    packages = [
        Package(
            name="test-pkg",
            description="Test package",
            player=PlayerType.MPV,
            version="1.0",
            files=[],
            dependencies=[],
            profile=ProfileType.DEFAULT
        )
    ]
    
    formatter.format_package_list(packages, installed_packages=["test-pkg"])
    
    result = output.getvalue()
    parsed = json.loads(result)
    assert len(parsed["packages"]) == 1
    assert parsed["packages"][0]["name"] == "test-pkg"
    assert parsed["packages"][0]["installed"] is True


def test_format_info_text():
    """Test formatting info panel in text mode."""
    output = StringIO()
    console = Console(file=output, force_terminal=True, width=80)
    formatter = OutputFormatter(output_format="text", console=console)
    
    info = {"Name": "test-pkg", "Version": "1.0"}
    formatter.format_info("Package Info", info)
    
    result = output.getvalue()
    assert "test-pkg" in result
    assert "1.0" in result


def test_format_info_json():
    """Test formatting info in JSON mode."""
    output = StringIO()
    console = Console(file=output, force_terminal=False, width=80)
    formatter = OutputFormatter(output_format="json", console=console)
    
    info = {"Name": "test-pkg", "Version": "1.0"}
    formatter.format_info("Package Info", info)
    
    result = output.getvalue()
    parsed = json.loads(result)
    assert parsed["Name"] == "test-pkg"
    assert parsed["Version"] == "1.0"

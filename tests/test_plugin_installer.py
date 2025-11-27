"""Unit tests for PluginInstaller."""

import pytest
from pathlib import Path
from injekt.business.plugin_installer import PluginInstaller
from injekt.core.models import Package, PackageFile, FileType, PlayerType, ProfileType
from injekt.io.file_operations import FileOperations
from injekt.core.result import Success, Failure


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for testing."""
    return tmp_path


@pytest.fixture
def file_ops(temp_dir):
    """Create FileOperations instance."""
    return FileOperations()


@pytest.fixture
def plugin_installer(file_ops):
    """Create PluginInstaller instance."""
    return PluginInstaller(file_ops)


@pytest.fixture
def sample_plugin_files(temp_dir):
    """Create sample plugin files for testing."""
    # Create source directory
    source_dir = temp_dir / "source"
    source_dir.mkdir()
    
    # Create Lua plugin
    lua_plugin = source_dir / "test.lua"
    lua_plugin.write_text("-- Test Lua plugin\nrequire('mp.utils')\n")
    
    # Create JS plugin
    js_plugin = source_dir / "test.js"
    js_plugin.write_text("// Test JS plugin\nvar mp = require('mp');\n")
    
    # Create script-opt config
    script_opt = source_dir / "test.conf"
    script_opt.write_text("option=value\n")
    
    return {
        'lua': lua_plugin,
        'js': js_plugin,
        'conf': script_opt,
        'source_dir': source_dir
    }


def test_get_plugin_target_path_lua(plugin_installer, temp_dir):
    """Test routing Lua plugin to scripts/ directory."""
    plugin_file = PackageFile(
        source_path=Path("test.lua"),
        target_path=Path("test.lua"),
        file_type=FileType.PLUGIN_LUA,
        required=True
    )
    
    target_path = plugin_installer.get_plugin_target_path(plugin_file, temp_dir)
    
    assert target_path == temp_dir / "scripts" / "test.lua"


def test_get_plugin_target_path_js(plugin_installer, temp_dir):
    """Test routing JS plugin to scripts/ directory."""
    plugin_file = PackageFile(
        source_path=Path("test.js"),
        target_path=Path("test.js"),
        file_type=FileType.PLUGIN_JS,
        required=True
    )
    
    target_path = plugin_installer.get_plugin_target_path(plugin_file, temp_dir)
    
    assert target_path == temp_dir / "scripts" / "test.js"


def test_get_plugin_target_path_script_opt(plugin_installer, temp_dir):
    """Test routing script-opt config to script-opts/ directory."""
    config_file = PackageFile(
        source_path=Path("test.conf"),
        target_path=Path("test.conf"),
        file_type=FileType.SCRIPT_OPT,
        required=True
    )
    
    target_path = plugin_installer.get_plugin_target_path(config_file, temp_dir)
    
    assert target_path == temp_dir / "script-opts" / "test.conf"


def test_get_plugin_target_path_non_plugin(plugin_installer, temp_dir):
    """Test that non-plugin files use original target path."""
    config_file = PackageFile(
        source_path=Path("mpv.conf"),
        target_path=Path("mpv.conf"),
        file_type=FileType.CONFIG,
        required=True
    )
    
    target_path = plugin_installer.get_plugin_target_path(config_file, temp_dir)
    
    assert target_path == temp_dir / "mpv.conf"


def test_get_plugin_target_path_with_subdirectory(plugin_installer, temp_dir):
    """Test routing plugin with subdirectory in target path."""
    plugin_file = PackageFile(
        source_path=Path("plugins/test.lua"),
        target_path=Path("plugins/test.lua"),
        file_type=FileType.PLUGIN_LUA,
        required=True
    )
    
    target_path = plugin_installer.get_plugin_target_path(plugin_file, temp_dir)
    
    # Should extract just the filename and route to scripts/
    assert target_path == temp_dir / "scripts" / "test.lua"


def test_resolve_plugin_dependencies_no_plugins(plugin_installer):
    """Test dependency resolution with no plugins."""
    package = Package(
        name="test-package",
        description="Test",
        player=PlayerType.MPV,
        version="1.0",
        files=[],
        dependencies=[],
        profile=ProfileType.DEFAULT
    )
    
    result = plugin_installer.resolve_plugin_dependencies(package)
    
    assert isinstance(result, Success)
    assert result.value == []


def test_resolve_plugin_dependencies_with_available_deps(plugin_installer, sample_plugin_files):
    """Test dependency resolution when dependencies are available."""
    package = Package(
        name="test-package",
        description="Test",
        player=PlayerType.MPV,
        version="1.0",
        files=[
            PackageFile(
                source_path=sample_plugin_files['lua'],
                target_path=Path("test.lua"),
                file_type=FileType.PLUGIN_LUA,
                required=True
            )
        ],
        dependencies=['mp.utils'],  # Dependency is listed
        profile=ProfileType.DEFAULT
    )
    
    result = plugin_installer.resolve_plugin_dependencies(package)
    
    assert isinstance(result, Success)
    # Should have no missing dependencies since mp.utils is in package.dependencies
    assert result.value == []


def test_install_plugin_configs_empty_package(plugin_installer, temp_dir):
    """Test installing plugin configs with no script-opt files."""
    package = Package(
        name="test-package",
        description="Test",
        player=PlayerType.MPV,
        version="1.0",
        files=[],
        dependencies=[],
        profile=ProfileType.DEFAULT
    )
    
    result = plugin_installer.install_plugin_configs(package, temp_dir)
    
    assert isinstance(result, Success)
    assert result.value == []


def test_install_plugin_configs_with_configs(plugin_installer, temp_dir, sample_plugin_files):
    """Test installing script-opt configuration files."""
    target_dir = temp_dir / "target"
    target_dir.mkdir()
    
    package = Package(
        name="test-package",
        description="Test",
        player=PlayerType.MPV,
        version="1.0",
        files=[
            PackageFile(
                source_path=sample_plugin_files['conf'],
                target_path=Path("test.conf"),
                file_type=FileType.SCRIPT_OPT,
                required=True
            )
        ],
        dependencies=[],
        profile=ProfileType.DEFAULT
    )
    
    result = plugin_installer.install_plugin_configs(package, target_dir)
    
    assert isinstance(result, Success)
    assert len(result.value) == 1
    
    # Check that file was copied to script-opts/
    installed_path = target_dir / "script-opts" / "test.conf"
    assert installed_path.exists()
    assert installed_path.read_text() == "option=value\n"


def test_install_plugin_configs_dry_run(plugin_installer, temp_dir, sample_plugin_files):
    """Test installing plugin configs in dry-run mode."""
    target_dir = temp_dir / "target"
    target_dir.mkdir()
    
    package = Package(
        name="test-package",
        description="Test",
        player=PlayerType.MPV,
        version="1.0",
        files=[
            PackageFile(
                source_path=sample_plugin_files['conf'],
                target_path=Path("test.conf"),
                file_type=FileType.SCRIPT_OPT,
                required=True
            )
        ],
        dependencies=[],
        profile=ProfileType.DEFAULT
    )
    
    result = plugin_installer.install_plugin_configs(package, target_dir, dry_run=True)
    
    assert isinstance(result, Success)
    
    # In dry-run mode, file should not be created
    installed_path = target_dir / "script-opts" / "test.conf"
    assert not installed_path.exists()


def test_install_plugin_configs_skip_non_required_missing(plugin_installer, temp_dir):
    """Test that non-required missing files are skipped."""
    package = Package(
        name="test-package",
        description="Test",
        player=PlayerType.MPV,
        version="1.0",
        files=[
            PackageFile(
                source_path=Path("nonexistent.conf"),
                target_path=Path("nonexistent.conf"),
                file_type=FileType.SCRIPT_OPT,
                required=False  # Not required
            )
        ],
        dependencies=[],
        profile=ProfileType.DEFAULT
    )
    
    result = plugin_installer.install_plugin_configs(package, temp_dir)
    
    # Should succeed and skip the missing file
    assert isinstance(result, Success)
    assert result.value == []


def test_parse_plugin_dependencies_lua(plugin_installer, sample_plugin_files):
    """Test parsing dependencies from Lua plugin."""
    deps = plugin_installer._parse_plugin_dependencies(sample_plugin_files['lua'])
    
    assert 'mp.utils' in deps


def test_parse_plugin_dependencies_js(plugin_installer, sample_plugin_files):
    """Test parsing dependencies from JS plugin."""
    deps = plugin_installer._parse_plugin_dependencies(sample_plugin_files['js'])
    
    assert 'mp' in deps


def test_parse_plugin_dependencies_nonexistent(plugin_installer):
    """Test parsing dependencies from nonexistent file."""
    deps = plugin_installer._parse_plugin_dependencies(Path("nonexistent.lua"))
    
    assert deps == []

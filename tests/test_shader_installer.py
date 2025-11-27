"""Unit tests for ShaderInstaller."""

import pytest
from pathlib import Path
from injekt.business.shader_installer import ShaderInstaller
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
def shader_installer(file_ops):
    """Create ShaderInstaller instance."""
    return ShaderInstaller(file_ops)


@pytest.fixture
def sample_shader_files(temp_dir):
    """Create sample shader files for testing."""
    # Create source directory
    source_dir = temp_dir / "source"
    source_dir.mkdir()
    
    # Create GLSL shader
    shader1 = source_dir / "test.glsl"
    shader1.write_text('// Test shader\n#include "common.glsl"\nvoid main() {}\n')
    
    # Create another shader
    shader2 = source_dir / "common.glsl"
    shader2.write_text('// Common shader functions\nvoid helper() {}\n')
    
    # Create config file with shader references
    config = source_dir / "mpv.conf"
    config.write_text('glsl-shaders="~~/shaders/test.glsl"\nglsl-shaders-append="~~/shaders/common.glsl"\n')
    
    return {
        'shader1': shader1,
        'shader2': shader2,
        'config': config,
        'source_dir': source_dir
    }


def test_get_shader_target_path(shader_installer, temp_dir):
    """Test routing shader to shaders/ directory."""
    shader_file = PackageFile(
        source_path=Path("test.glsl"),
        target_path=Path("test.glsl"),
        file_type=FileType.SHADER,
        required=True
    )
    
    target_path = shader_installer.get_shader_target_path(shader_file, temp_dir)
    
    assert target_path == temp_dir / "shaders" / "test.glsl"


def test_get_shader_target_path_with_subdirectory(shader_installer, temp_dir):
    """Test routing shader with subdirectory in target path."""
    shader_file = PackageFile(
        source_path=Path("shaders/test.glsl"),
        target_path=Path("shaders/test.glsl"),
        file_type=FileType.SHADER,
        required=True
    )
    
    target_path = shader_installer.get_shader_target_path(shader_file, temp_dir)
    
    # Should extract just the filename and route to shaders/
    assert target_path == temp_dir / "shaders" / "test.glsl"


def test_install_shaders_empty_package(shader_installer, temp_dir):
    """Test installing shaders with no shader files."""
    package = Package(
        name="test-package",
        description="Test",
        player=PlayerType.MPV,
        version="1.0",
        files=[],
        dependencies=[],
        profile=ProfileType.DEFAULT
    )
    
    result = shader_installer.install_shaders(package, temp_dir)
    
    assert isinstance(result, Success)
    assert result.value == []


def test_install_shaders_with_shaders(shader_installer, temp_dir, sample_shader_files):
    """Test installing shader files."""
    target_dir = temp_dir / "target"
    target_dir.mkdir()
    
    package = Package(
        name="test-package",
        description="Test",
        player=PlayerType.MPV,
        version="1.0",
        files=[
            PackageFile(
                source_path=sample_shader_files['shader1'],
                target_path=Path("test.glsl"),
                file_type=FileType.SHADER,
                required=True
            ),
            PackageFile(
                source_path=sample_shader_files['shader2'],
                target_path=Path("common.glsl"),
                file_type=FileType.SHADER,
                required=True
            )
        ],
        dependencies=[],
        profile=ProfileType.DEFAULT
    )
    
    result = shader_installer.install_shaders(package, target_dir)
    
    assert isinstance(result, Success)
    assert len(result.value) == 2
    
    # Check that files were copied to shaders/
    shader1_path = target_dir / "shaders" / "test.glsl"
    shader2_path = target_dir / "shaders" / "common.glsl"
    assert shader1_path.exists()
    assert shader2_path.exists()
    assert '#include "common.glsl"' in shader1_path.read_text()


def test_install_shaders_dry_run(shader_installer, temp_dir, sample_shader_files):
    """Test installing shaders in dry-run mode."""
    target_dir = temp_dir / "target"
    target_dir.mkdir()
    
    package = Package(
        name="test-package",
        description="Test",
        player=PlayerType.MPV,
        version="1.0",
        files=[
            PackageFile(
                source_path=sample_shader_files['shader1'],
                target_path=Path("test.glsl"),
                file_type=FileType.SHADER,
                required=True
            )
        ],
        dependencies=[],
        profile=ProfileType.DEFAULT
    )
    
    result = shader_installer.install_shaders(package, target_dir, dry_run=True)
    
    assert isinstance(result, Success)
    
    # In dry-run mode, file should not be created
    shader_path = target_dir / "shaders" / "test.glsl"
    assert not shader_path.exists()


def test_install_shaders_skip_non_required_missing(shader_installer, temp_dir):
    """Test that non-required missing shader files are skipped."""
    package = Package(
        name="test-package",
        description="Test",
        player=PlayerType.MPV,
        version="1.0",
        files=[
            PackageFile(
                source_path=Path("nonexistent.glsl"),
                target_path=Path("nonexistent.glsl"),
                file_type=FileType.SHADER,
                required=False  # Not required
            )
        ],
        dependencies=[],
        profile=ProfileType.DEFAULT
    )
    
    result = shader_installer.install_shaders(package, temp_dir)
    
    # Should succeed and skip the missing file
    assert isinstance(result, Success)
    assert result.value == []


def test_validate_shader_references_no_references(shader_installer, temp_dir):
    """Test validating shader references with no config files."""
    package = Package(
        name="test-package",
        description="Test",
        player=PlayerType.MPV,
        version="1.0",
        files=[],
        dependencies=[],
        profile=ProfileType.DEFAULT
    )
    
    result = shader_installer.validate_shader_references(package, temp_dir)
    
    assert isinstance(result, Success)
    assert result.value == []


def test_validate_shader_references_all_present(shader_installer, temp_dir, sample_shader_files):
    """Test validating shader references when all shaders are present."""
    package = Package(
        name="test-package",
        description="Test",
        player=PlayerType.MPV,
        version="1.0",
        files=[
            PackageFile(
                source_path=sample_shader_files['config'],
                target_path=Path("mpv.conf"),
                file_type=FileType.CONFIG,
                required=True
            ),
            PackageFile(
                source_path=sample_shader_files['shader1'],
                target_path=Path("test.glsl"),
                file_type=FileType.SHADER,
                required=True
            ),
            PackageFile(
                source_path=sample_shader_files['shader2'],
                target_path=Path("common.glsl"),
                file_type=FileType.SHADER,
                required=True
            )
        ],
        dependencies=[],
        profile=ProfileType.DEFAULT
    )
    
    result = shader_installer.validate_shader_references(package, temp_dir)
    
    assert isinstance(result, Success)
    # All referenced shaders are present in package
    assert result.value == []


def test_validate_shader_references_missing(shader_installer, temp_dir, sample_shader_files):
    """Test validating shader references when shaders are missing."""
    package = Package(
        name="test-package",
        description="Test",
        player=PlayerType.MPV,
        version="1.0",
        files=[
            PackageFile(
                source_path=sample_shader_files['config'],
                target_path=Path("mpv.conf"),
                file_type=FileType.CONFIG,
                required=True
            )
            # No shader files included
        ],
        dependencies=[],
        profile=ProfileType.DEFAULT
    )
    
    result = shader_installer.validate_shader_references(package, temp_dir)
    
    assert isinstance(result, Success)
    # Should report missing shader references
    assert len(result.value) > 0
    assert any('test.glsl' in msg for msg in result.value)


def test_resolve_shader_dependencies_no_shaders(shader_installer):
    """Test dependency resolution with no shaders."""
    package = Package(
        name="test-package",
        description="Test",
        player=PlayerType.MPV,
        version="1.0",
        files=[],
        dependencies=[],
        profile=ProfileType.DEFAULT
    )
    
    result = shader_installer.resolve_shader_dependencies(package)
    
    assert isinstance(result, Success)
    assert result.value == []


def test_resolve_shader_dependencies_with_available_deps(shader_installer, sample_shader_files):
    """Test dependency resolution when dependencies are available."""
    package = Package(
        name="test-package",
        description="Test",
        player=PlayerType.MPV,
        version="1.0",
        files=[
            PackageFile(
                source_path=sample_shader_files['shader1'],
                target_path=Path("test.glsl"),
                file_type=FileType.SHADER,
                required=True
            ),
            PackageFile(
                source_path=sample_shader_files['shader2'],
                target_path=Path("common.glsl"),
                file_type=FileType.SHADER,
                required=True
            )
        ],
        dependencies=[],
        profile=ProfileType.DEFAULT
    )
    
    result = shader_installer.resolve_shader_dependencies(package)
    
    assert isinstance(result, Success)
    # common.glsl is included in the package, so no missing dependencies
    assert result.value == []


def test_parse_shader_references(shader_installer, sample_shader_files):
    """Test parsing shader references from config file."""
    refs = shader_installer._parse_shader_references(sample_shader_files['config'])
    
    assert len(refs) >= 2
    assert any('test.glsl' in ref for ref in refs)
    assert any('common.glsl' in ref for ref in refs)


def test_parse_shader_references_nonexistent(shader_installer):
    """Test parsing shader references from nonexistent file."""
    refs = shader_installer._parse_shader_references(Path("nonexistent.conf"))
    
    assert refs == []


def test_parse_shader_dependencies(shader_installer, sample_shader_files):
    """Test parsing dependencies from shader file."""
    deps = shader_installer._parse_shader_dependencies(sample_shader_files['shader1'])
    
    assert 'common.glsl' in deps


def test_parse_shader_dependencies_nonexistent(shader_installer):
    """Test parsing dependencies from nonexistent file."""
    deps = shader_installer._parse_shader_dependencies(Path("nonexistent.glsl"))
    
    assert deps == []

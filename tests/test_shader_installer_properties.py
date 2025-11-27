"""Property-based tests for ShaderInstaller.

Feature: injekt-cli, Property 8: Shader reference validation
Validates: Requirements 8.2
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from hypothesis import given, strategies as st, settings

from injekt.business.shader_installer import ShaderInstaller
from injekt.io.file_operations import FileOperations
from injekt.core.models import Package, PackageFile, PlayerType, ProfileType, FileType
from injekt.core.result import Success, Failure


def create_temp_dirs():
    """Create temporary directories for testing."""
    temp_base = Path(tempfile.mkdtemp())
    
    target_dir = temp_base / "target"
    target_dir.mkdir()
    
    source_dir = temp_base / "source"
    source_dir.mkdir()
    
    return {
        'base': temp_base,
        'target': target_dir,
        'source': source_dir
    }


def cleanup_temp_dirs(temp_dirs):
    """Clean up temporary directories."""
    if temp_dirs['base'].exists():
        shutil.rmtree(temp_dirs['base'])


def create_shader_installer():
    """Create a ShaderInstaller instance."""
    file_ops = FileOperations(dry_run=False)
    return ShaderInstaller(file_ops)


# Strategy for generating valid shader names
shader_name_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_'),
    min_size=3,
    max_size=20
).filter(lambda x: x and x[0].isalpha())


@settings(max_examples=100)
@given(
    num_shaders=st.integers(min_value=1, max_value=10),
    num_configs=st.integers(min_value=1, max_value=5)
)
def test_property_shader_reference_validation_all_present(num_shaders, num_configs):
    """
    **Feature: injekt-cli, Property 8: Shader reference validation**
    **Validates: Requirements 8.2**
    
    Property: For any configuration file that references shaders, all referenced
    shader files should exist after installation.
    
    This test verifies that:
    1. When a package contains config files that reference shaders
    2. And all referenced shaders are included in the package
    3. Then validation succeeds (no missing references)
    4. And installation completes successfully
    """
    temp_dirs = create_temp_dirs()
    try:
        shader_installer = create_shader_installer()
        
        # Create shader files
        shader_files = []
        shader_names = []
        
        for i in range(num_shaders):
            shader_name = f"shader_{i}.glsl"
            shader_names.append(shader_name)
            
            source_path = temp_dirs['source'] / shader_name
            source_path.write_text(f"// Shader {i}\nvoid main() {{}}\n")
            
            shader_file = PackageFile(
                source_path=source_path,
                target_path=Path(shader_name),
                file_type=FileType.SHADER,
                required=True
            )
            shader_files.append(shader_file)
        
        # Create config files that reference these shaders
        config_files = []
        
        for i in range(num_configs):
            config_name = f"config_{i}.conf"
            source_path = temp_dirs['source'] / config_name
            
            # Reference some shaders in this config
            # Each config references at least one shader
            num_refs = min(i + 1, num_shaders)
            config_content = f"# Config {i}\n"
            
            for j in range(num_refs):
                shader_ref = shader_names[j % num_shaders]
                config_content += f'glsl-shaders="~~/shaders/{shader_ref}"\n'
            
            source_path.write_text(config_content)
            
            config_file = PackageFile(
                source_path=source_path,
                target_path=Path(config_name),
                file_type=FileType.CONFIG,
                required=True
            )
            config_files.append(config_file)
        
        # Create package with both configs and shaders
        package = Package(
            name="shader-validation-test",
            description="Test shader reference validation",
            player=PlayerType.MPV,
            version="1.0.0",
            files=config_files + shader_files,
            dependencies=[],
            profile=ProfileType.DEFAULT
        )
        
        # Validate shader references - should succeed
        validation_result = shader_installer.validate_shader_references(
            package,
            temp_dirs['target']
        )
        
        assert isinstance(validation_result, Success), \
            f"Validation should succeed when all shaders are present, but got: {validation_result}"
        
        # Should have no missing references
        missing_refs = validation_result.value
        assert len(missing_refs) == 0, \
            f"Expected no missing references, but found: {missing_refs}"
        
        # Install shaders and verify they exist
        install_result = shader_installer.install_shaders(
            package,
            temp_dirs['target'],
            dry_run=False
        )
        
        assert isinstance(install_result, Success), \
            f"Installation should succeed, but got: {install_result}"
        
        # Verify all referenced shaders exist after installation
        for shader_name in shader_names:
            shader_path = temp_dirs['target'] / "shaders" / shader_name
            assert shader_path.exists(), \
                f"Referenced shader {shader_name} should exist after installation"
    
    finally:
        cleanup_temp_dirs(temp_dirs)


@settings(max_examples=100)
@given(
    num_present_shaders=st.integers(min_value=0, max_value=5),
    num_missing_shaders=st.integers(min_value=1, max_value=5)
)
def test_property_shader_reference_validation_missing_shaders(
    num_present_shaders,
    num_missing_shaders
):
    """
    **Feature: injekt-cli, Property 8: Shader reference validation**
    **Validates: Requirements 8.2**
    
    Property: For any configuration file that references shaders, validation should
    detect and report missing shader files.
    
    This test verifies that:
    1. When a package contains config files that reference shaders
    2. And some referenced shaders are NOT included in the package
    3. Then validation detects the missing shaders
    4. And reports all missing shader references
    """
    temp_dirs = create_temp_dirs()
    try:
        shader_installer = create_shader_installer()
        
        # Create shader files that ARE present
        present_shader_files = []
        present_shader_names = []
        
        for i in range(num_present_shaders):
            shader_name = f"present_shader_{i}.glsl"
            present_shader_names.append(shader_name)
            
            source_path = temp_dirs['source'] / shader_name
            source_path.write_text(f"// Present shader {i}\nvoid main() {{}}\n")
            
            shader_file = PackageFile(
                source_path=source_path,
                target_path=Path(shader_name),
                file_type=FileType.SHADER,
                required=True
            )
            present_shader_files.append(shader_file)
        
        # Create config that references MISSING shaders
        missing_shader_names = []
        config_content = "# Config with missing shader references\n"
        
        for i in range(num_missing_shaders):
            shader_name = f"missing_shader_{i}.glsl"
            missing_shader_names.append(shader_name)
            config_content += f'glsl-shaders="~~/shaders/{shader_name}"\n'
        
        # Also reference some present shaders if any
        for shader_name in present_shader_names[:min(2, len(present_shader_names))]:
            config_content += f'glsl-shaders-append="~~/shaders/{shader_name}"\n'
        
        config_path = temp_dirs['source'] / "config.conf"
        config_path.write_text(config_content)
        
        config_file = PackageFile(
            source_path=config_path,
            target_path=Path("config.conf"),
            file_type=FileType.CONFIG,
            required=True
        )
        
        # Create package with config and only present shaders (missing shaders not included)
        package = Package(
            name="missing-shader-test",
            description="Test missing shader detection",
            player=PlayerType.MPV,
            version="1.0.0",
            files=[config_file] + present_shader_files,
            dependencies=[],
            profile=ProfileType.DEFAULT
        )
        
        # Validate shader references - should detect missing shaders
        validation_result = shader_installer.validate_shader_references(
            package,
            temp_dirs['target']
        )
        
        assert isinstance(validation_result, Success), \
            f"Validation should return Success with missing references list, but got: {validation_result}"
        
        # Should report missing references
        missing_refs = validation_result.value
        assert len(missing_refs) > 0, \
            f"Expected to find {num_missing_shaders} missing shader references, but found none"
        
        # Verify all missing shaders are reported
        for missing_shader in missing_shader_names:
            # Check if any missing reference mentions this shader
            found = any(missing_shader in ref for ref in missing_refs)
            assert found, \
                f"Missing shader '{missing_shader}' should be reported in: {missing_refs}"
    
    finally:
        cleanup_temp_dirs(temp_dirs)


@settings(max_examples=100)
@given(
    num_shaders=st.integers(min_value=1, max_value=8),
    num_configs=st.integers(min_value=1, max_value=4)
)
def test_property_shader_reference_validation_multiple_configs(num_shaders, num_configs):
    """
    **Feature: injekt-cli, Property 8: Shader reference validation**
    **Validates: Requirements 8.2**
    
    Property: For any set of configuration files, validation should check shader
    references across all config files.
    
    This test verifies that:
    1. When a package contains multiple config files
    2. And each config references different shaders
    3. Then validation checks all configs
    4. And reports missing shaders from any config file
    """
    temp_dirs = create_temp_dirs()
    try:
        shader_installer = create_shader_installer()
        
        # Create some shaders (but not all that will be referenced)
        present_shader_files = []
        present_shader_names = []
        
        # Only create half the shaders
        num_present = max(1, num_shaders // 2)
        
        for i in range(num_present):
            shader_name = f"shader_{i}.glsl"
            present_shader_names.append(shader_name)
            
            source_path = temp_dirs['source'] / shader_name
            source_path.write_text(f"// Shader {i}\nvoid main() {{}}\n")
            
            shader_file = PackageFile(
                source_path=source_path,
                target_path=Path(shader_name),
                file_type=FileType.SHADER,
                required=True
            )
            present_shader_files.append(shader_file)
        
        # Create multiple config files, each referencing different shaders
        config_files = []
        all_referenced_shaders = set()
        
        for i in range(num_configs):
            config_name = f"config_{i}.conf"
            source_path = temp_dirs['source'] / config_name
            
            config_content = f"# Config {i}\n"
            
            # Each config references different shaders
            start_idx = i * 2
            end_idx = min(start_idx + 3, num_shaders)
            
            for j in range(start_idx, end_idx):
                shader_name = f"shader_{j}.glsl"
                all_referenced_shaders.add(shader_name)
                config_content += f'glsl-shaders-append="~~/shaders/{shader_name}"\n'
            
            source_path.write_text(config_content)
            
            config_file = PackageFile(
                source_path=source_path,
                target_path=Path(config_name),
                file_type=FileType.CONFIG,
                required=True
            )
            config_files.append(config_file)
        
        # Create package
        package = Package(
            name="multi-config-test",
            description="Test multiple config validation",
            player=PlayerType.MPV,
            version="1.0.0",
            files=config_files + present_shader_files,
            dependencies=[],
            profile=ProfileType.DEFAULT
        )
        
        # Validate shader references
        validation_result = shader_installer.validate_shader_references(
            package,
            temp_dirs['target']
        )
        
        assert isinstance(validation_result, Success), \
            f"Validation should return Success, but got: {validation_result}"
        
        missing_refs = validation_result.value
        
        # Determine which shaders are actually missing
        missing_shaders = all_referenced_shaders - set(present_shader_names)
        
        if len(missing_shaders) > 0:
            # Should report missing shaders
            assert len(missing_refs) > 0, \
                f"Expected to find missing shader references for {missing_shaders}"
            
            # Verify each missing shader is reported
            for missing_shader in missing_shaders:
                found = any(missing_shader in ref for ref in missing_refs)
                assert found, \
                    f"Missing shader '{missing_shader}' should be reported"
        else:
            # All shaders present, no missing references
            assert len(missing_refs) == 0, \
                f"Expected no missing references when all shaders present, but found: {missing_refs}"
    
    finally:
        cleanup_temp_dirs(temp_dirs)


@settings(max_examples=100)
@given(
    num_shaders=st.integers(min_value=1, max_value=10)
)
def test_property_shader_reference_validation_after_installation(num_shaders):
    """
    **Feature: injekt-cli, Property 8: Shader reference validation**
    **Validates: Requirements 8.2**
    
    Property: After installation, all shader files referenced in config files should
    exist in the target directory.
    
    This test verifies that:
    1. When a package with shader references is installed
    2. Then all referenced shaders exist in the shaders/ directory
    3. And the shader files are accessible at the referenced paths
    """
    temp_dirs = create_temp_dirs()
    try:
        shader_installer = create_shader_installer()
        
        # Create shader files
        shader_files = []
        shader_names = []
        
        for i in range(num_shaders):
            shader_name = f"shader_{i}.glsl"
            shader_names.append(shader_name)
            
            source_path = temp_dirs['source'] / shader_name
            source_path.write_text(f"// Shader {i}\nvoid main() {{}}\n")
            
            shader_file = PackageFile(
                source_path=source_path,
                target_path=Path(shader_name),
                file_type=FileType.SHADER,
                required=True
            )
            shader_files.append(shader_file)
        
        # Create config that references all shaders
        config_content = "# Config with shader references\n"
        for shader_name in shader_names:
            config_content += f'glsl-shaders-append="~~/shaders/{shader_name}"\n'
        
        config_path = temp_dirs['source'] / "config.conf"
        config_path.write_text(config_content)
        
        config_file = PackageFile(
            source_path=config_path,
            target_path=Path("config.conf"),
            file_type=FileType.CONFIG,
            required=True
        )
        
        # Create package
        package = Package(
            name="post-install-test",
            description="Test shader existence after installation",
            player=PlayerType.MPV,
            version="1.0.0",
            files=[config_file] + shader_files,
            dependencies=[],
            profile=ProfileType.DEFAULT
        )
        
        # Install shaders
        install_result = shader_installer.install_shaders(
            package,
            temp_dirs['target'],
            dry_run=False
        )
        
        assert isinstance(install_result, Success), \
            f"Installation should succeed, but got: {install_result}"
        
        # Verify all referenced shaders exist after installation
        for shader_name in shader_names:
            shader_path = temp_dirs['target'] / "shaders" / shader_name
            assert shader_path.exists(), \
                f"Referenced shader {shader_name} should exist at {shader_path} after installation"
            
            # Verify shader file is readable and has content
            content = shader_path.read_text()
            assert len(content) > 0, \
                f"Shader {shader_name} should have content"
            assert "void main()" in content, \
                f"Shader {shader_name} should contain valid shader code"
    
    finally:
        cleanup_temp_dirs(temp_dirs)


@settings(max_examples=100)
@given(
    num_shaders=st.integers(min_value=1, max_value=8)
)
def test_property_shader_reference_validation_existing_shaders(num_shaders):
    """
    **Feature: injekt-cli, Property 8: Shader reference validation**
    **Validates: Requirements 8.2**
    
    Property: Validation should accept shader references if the shaders already exist
    in the target directory (from previous installations).
    
    This test verifies that:
    1. When shaders already exist in the target directory
    2. And a config references those existing shaders
    3. Then validation succeeds (no missing references)
    4. Even if the shaders are not in the current package
    """
    temp_dirs = create_temp_dirs()
    try:
        shader_installer = create_shader_installer()
        
        # Pre-install some shaders in the target directory
        shaders_dir = temp_dirs['target'] / "shaders"
        shaders_dir.mkdir(parents=True)
        
        existing_shader_names = []
        for i in range(num_shaders):
            shader_name = f"existing_shader_{i}.glsl"
            existing_shader_names.append(shader_name)
            
            shader_path = shaders_dir / shader_name
            shader_path.write_text(f"// Existing shader {i}\nvoid main() {{}}\n")
        
        # Create config that references these existing shaders
        config_content = "# Config referencing existing shaders\n"
        for shader_name in existing_shader_names:
            config_content += f'glsl-shaders="~~/shaders/{shader_name}"\n'
        
        config_path = temp_dirs['source'] / "config.conf"
        config_path.write_text(config_content)
        
        config_file = PackageFile(
            source_path=config_path,
            target_path=Path("config.conf"),
            file_type=FileType.CONFIG,
            required=True
        )
        
        # Create package with only config (no shaders)
        package = Package(
            name="existing-shader-test",
            description="Test validation with existing shaders",
            player=PlayerType.MPV,
            version="1.0.0",
            files=[config_file],
            dependencies=[],
            profile=ProfileType.DEFAULT
        )
        
        # Validate shader references - should succeed because shaders exist
        validation_result = shader_installer.validate_shader_references(
            package,
            temp_dirs['target']
        )
        
        assert isinstance(validation_result, Success), \
            f"Validation should succeed when shaders exist in target, but got: {validation_result}"
        
        # Should have no missing references
        missing_refs = validation_result.value
        assert len(missing_refs) == 0, \
            f"Expected no missing references when shaders exist in target, but found: {missing_refs}"
    
    finally:
        cleanup_temp_dirs(temp_dirs)

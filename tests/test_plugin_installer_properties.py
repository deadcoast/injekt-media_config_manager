"""Property-based tests for PluginInstaller.

Feature: injekt-cli, Property 7: Plugin path routing
Validates: Requirements 7.1
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from hypothesis import given, strategies as st, settings

from injekt.business.plugin_installer import PluginInstaller
from injekt.io.file_operations import FileOperations
from injekt.core.models import PackageFile, FileType


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


def create_plugin_installer():
    """Create a PluginInstaller instance."""
    file_ops = FileOperations(dry_run=False)
    return PluginInstaller(file_ops)


# Strategy for generating valid plugin filenames
plugin_filenames = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), min_codepoint=65, max_codepoint=122),
    min_size=1,
    max_size=20
).map(lambda s: s.replace(' ', '_'))


@settings(max_examples=100)
@given(
    filename=plugin_filenames,
    file_type=st.sampled_from([FileType.PLUGIN_LUA, FileType.PLUGIN_JS, FileType.SCRIPT_OPT])
)
def test_property_plugin_path_routing_correct_subdirectory(filename, file_type):
    """
    **Feature: injekt-cli, Property 7: Plugin path routing**
    **Validates: Requirements 7.1**
    
    Property: For any plugin file, installation should place it in the correct subdirectory
    based on its file type (Lua → scripts/, JS → scripts/, script-opt → script-opts/).
    
    This test verifies that:
    1. For any plugin file with a given file type
    2. The get_plugin_target_path method routes it to the correct subdirectory
    3. Lua plugins go to scripts/
    4. JS plugins go to scripts/
    5. Script-opt configs go to script-opts/
    """
    temp_dirs = create_temp_dirs()
    try:
        plugin_installer = create_plugin_installer()
        
        # Determine the correct file extension based on file type
        if file_type == FileType.PLUGIN_LUA:
            extension = ".lua"
            expected_subdir = "scripts"
        elif file_type == FileType.PLUGIN_JS:
            extension = ".js"
            expected_subdir = "scripts"
        elif file_type == FileType.SCRIPT_OPT:
            extension = ".conf"
            expected_subdir = "script-opts"
        
        # Create a plugin file
        full_filename = f"{filename}{extension}"
        source_path = temp_dirs['source'] / full_filename
        
        plugin_file = PackageFile(
            source_path=source_path,
            target_path=Path(full_filename),
            file_type=file_type,
            required=True
        )
        
        # Get the target path
        target_path = plugin_installer.get_plugin_target_path(
            plugin_file,
            temp_dirs['target']
        )
        
        # Verify the path is routed to the correct subdirectory
        assert target_path.parent.name == expected_subdir, \
            f"Plugin type {file_type} should be routed to {expected_subdir}/, " \
            f"but got {target_path.parent.name}/"
        
        # Verify the filename is preserved
        assert target_path.name == full_filename, \
            f"Filename should be preserved as {full_filename}, but got {target_path.name}"
        
        # Verify the full path structure
        expected_path = temp_dirs['target'] / expected_subdir / full_filename
        assert target_path == expected_path, \
            f"Expected path {expected_path}, but got {target_path}"
    
    finally:
        cleanup_temp_dirs(temp_dirs)


@settings(max_examples=100)
@given(
    filename=plugin_filenames,
    subdirectory=st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), min_codepoint=65, max_codepoint=122),
        min_size=1,
        max_size=15
    ).map(lambda s: s.replace(' ', '_')),
    file_type=st.sampled_from([FileType.PLUGIN_LUA, FileType.PLUGIN_JS, FileType.SCRIPT_OPT])
)
def test_property_plugin_path_routing_extracts_filename(filename, subdirectory, file_type):
    """
    **Feature: injekt-cli, Property 7: Plugin path routing**
    **Validates: Requirements 7.1**
    
    Property: For any plugin file with a subdirectory in its target_path,
    only the filename should be extracted and routed to the correct plugin subdirectory.
    
    This test verifies that:
    1. When a plugin file has a target_path like "plugins/subdir/file.lua"
    2. Only the filename "file.lua" is extracted
    3. And it's routed to the correct subdirectory (e.g., "scripts/file.lua")
    4. The original subdirectory structure is not preserved
    """
    temp_dirs = create_temp_dirs()
    try:
        plugin_installer = create_plugin_installer()
        
        # Determine the correct file extension and expected subdirectory
        if file_type == FileType.PLUGIN_LUA:
            extension = ".lua"
            expected_subdir = "scripts"
        elif file_type == FileType.PLUGIN_JS:
            extension = ".js"
            expected_subdir = "scripts"
        elif file_type == FileType.SCRIPT_OPT:
            extension = ".conf"
            expected_subdir = "script-opts"
        
        # Create a plugin file with subdirectory in target_path
        full_filename = f"{filename}{extension}"
        source_path = temp_dirs['source'] / full_filename
        target_path_with_subdir = Path(subdirectory) / full_filename
        
        plugin_file = PackageFile(
            source_path=source_path,
            target_path=target_path_with_subdir,
            file_type=file_type,
            required=True
        )
        
        # Get the target path
        target_path = plugin_installer.get_plugin_target_path(
            plugin_file,
            temp_dirs['target']
        )
        
        # Verify the path is routed to the correct subdirectory
        assert target_path.parent.name == expected_subdir, \
            f"Plugin should be routed to {expected_subdir}/, but got {target_path.parent.name}/"
        
        # Verify only the filename is used (subdirectory is not preserved)
        assert target_path.name == full_filename, \
            f"Only filename {full_filename} should be used, but got {target_path.name}"
        
        # Verify the full path structure
        expected_path = temp_dirs['target'] / expected_subdir / full_filename
        assert target_path == expected_path, \
            f"Expected path {expected_path}, but got {target_path}"
        
        # Verify the original subdirectory path structure is NOT preserved
        # (i.e., the subdirectory should not appear as a parent directory)
        path_parts = target_path.parts
        # The path should be: temp_dir / target / expected_subdir / filename
        # It should NOT be: temp_dir / target / subdirectory / expected_subdir / filename
        # or: temp_dir / target / expected_subdir / subdirectory / filename
        if subdirectory != expected_subdir:
            # Only check if subdirectory is different from expected_subdir
            # to avoid false positives when they happen to be the same
            for i, part in enumerate(path_parts):
                if part == expected_subdir:
                    # Check that subdirectory doesn't appear after expected_subdir
                    remaining_parts = path_parts[i+1:]
                    assert subdirectory not in remaining_parts, \
                        f"Original subdirectory '{subdirectory}' should not appear in path structure"
                    break
    
    finally:
        cleanup_temp_dirs(temp_dirs)


@settings(max_examples=100)
@given(
    filename=plugin_filenames,
    file_type=st.sampled_from([FileType.CONFIG, FileType.SHADER])
)
def test_property_plugin_path_routing_non_plugin_files(filename, file_type):
    """
    **Feature: injekt-cli, Property 7: Plugin path routing**
    **Validates: Requirements 7.1**
    
    Property: For any non-plugin file (CONFIG, SHADER), the original target_path
    should be preserved without routing to plugin subdirectories.
    
    This test verifies that:
    1. When a file is not a plugin type (CONFIG or SHADER)
    2. The get_plugin_target_path method preserves the original target_path
    3. No routing to scripts/ or script-opts/ occurs
    """
    temp_dirs = create_temp_dirs()
    try:
        plugin_installer = create_plugin_installer()
        
        # Determine the correct file extension
        if file_type == FileType.CONFIG:
            extension = ".conf"
        elif file_type == FileType.SHADER:
            extension = ".glsl"
        
        # Create a non-plugin file
        full_filename = f"{filename}{extension}"
        source_path = temp_dirs['source'] / full_filename
        original_target_path = Path(full_filename)
        
        non_plugin_file = PackageFile(
            source_path=source_path,
            target_path=original_target_path,
            file_type=file_type,
            required=True
        )
        
        # Get the target path
        target_path = plugin_installer.get_plugin_target_path(
            non_plugin_file,
            temp_dirs['target']
        )
        
        # Verify the path is NOT routed to plugin subdirectories
        assert "scripts" not in str(target_path), \
            f"Non-plugin file should not be routed to scripts/, but got {target_path}"
        assert "script-opts" not in str(target_path), \
            f"Non-plugin file should not be routed to script-opts/, but got {target_path}"
        
        # Verify the original target_path is preserved
        expected_path = temp_dirs['target'] / original_target_path
        assert target_path == expected_path, \
            f"Expected original path {expected_path}, but got {target_path}"
    
    finally:
        cleanup_temp_dirs(temp_dirs)


@settings(max_examples=100)
@given(
    num_lua_plugins=st.integers(min_value=0, max_value=5),
    num_js_plugins=st.integers(min_value=0, max_value=5),
    num_script_opts=st.integers(min_value=0, max_value=5),
    num_configs=st.integers(min_value=0, max_value=5)
)
def test_property_plugin_path_routing_multiple_files(
    num_lua_plugins,
    num_js_plugins,
    num_script_opts,
    num_configs
):
    """
    **Feature: injekt-cli, Property 7: Plugin path routing**
    **Validates: Requirements 7.1**
    
    Property: For any collection of files with mixed types, each file should be
    routed to its correct subdirectory based on its file type.
    
    This test verifies that:
    1. When multiple files of different types are processed
    2. Each file is routed to the correct subdirectory
    3. Lua plugins → scripts/
    4. JS plugins → scripts/
    5. Script-opts → script-opts/
    6. Configs → original path (no routing)
    """
    temp_dirs = create_temp_dirs()
    try:
        plugin_installer = create_plugin_installer()
        
        # Track expected paths for each file type
        expected_lua_paths = []
        expected_js_paths = []
        expected_script_opt_paths = []
        expected_config_paths = []
        
        # Create Lua plugins
        for i in range(num_lua_plugins):
            filename = f"lua_plugin_{i}.lua"
            plugin_file = PackageFile(
                source_path=temp_dirs['source'] / filename,
                target_path=Path(filename),
                file_type=FileType.PLUGIN_LUA,
                required=True
            )
            
            target_path = plugin_installer.get_plugin_target_path(
                plugin_file,
                temp_dirs['target']
            )
            expected_lua_paths.append(target_path)
            
            # Verify routing
            assert target_path.parent.name == "scripts", \
                f"Lua plugin should be in scripts/, but got {target_path.parent.name}/"
        
        # Create JS plugins
        for i in range(num_js_plugins):
            filename = f"js_plugin_{i}.js"
            plugin_file = PackageFile(
                source_path=temp_dirs['source'] / filename,
                target_path=Path(filename),
                file_type=FileType.PLUGIN_JS,
                required=True
            )
            
            target_path = plugin_installer.get_plugin_target_path(
                plugin_file,
                temp_dirs['target']
            )
            expected_js_paths.append(target_path)
            
            # Verify routing
            assert target_path.parent.name == "scripts", \
                f"JS plugin should be in scripts/, but got {target_path.parent.name}/"
        
        # Create script-opt configs
        for i in range(num_script_opts):
            filename = f"script_opt_{i}.conf"
            config_file = PackageFile(
                source_path=temp_dirs['source'] / filename,
                target_path=Path(filename),
                file_type=FileType.SCRIPT_OPT,
                required=True
            )
            
            target_path = plugin_installer.get_plugin_target_path(
                config_file,
                temp_dirs['target']
            )
            expected_script_opt_paths.append(target_path)
            
            # Verify routing
            assert target_path.parent.name == "script-opts", \
                f"Script-opt should be in script-opts/, but got {target_path.parent.name}/"
        
        # Create config files (non-plugin)
        for i in range(num_configs):
            filename = f"config_{i}.conf"
            config_file = PackageFile(
                source_path=temp_dirs['source'] / filename,
                target_path=Path(filename),
                file_type=FileType.CONFIG,
                required=True
            )
            
            target_path = plugin_installer.get_plugin_target_path(
                config_file,
                temp_dirs['target']
            )
            expected_config_paths.append(target_path)
            
            # Verify no routing (should be at target root)
            assert target_path.parent == temp_dirs['target'], \
                f"Config should be at target root, but got {target_path.parent}/"
        
        # Verify all paths are unique (no collisions)
        all_paths = (
            expected_lua_paths +
            expected_js_paths +
            expected_script_opt_paths +
            expected_config_paths
        )
        
        if len(all_paths) > 0:
            unique_paths = set(str(p) for p in all_paths)
            assert len(unique_paths) == len(all_paths), \
                "All routed paths should be unique (no collisions)"
    
    finally:
        cleanup_temp_dirs(temp_dirs)


@settings(max_examples=100)
@given(
    filename=plugin_filenames
)
def test_property_plugin_path_routing_consistency(filename):
    """
    **Feature: injekt-cli, Property 7: Plugin path routing**
    **Validates: Requirements 7.1**
    
    Property: For any plugin file, calling get_plugin_target_path multiple times
    with the same inputs should always return the same path (deterministic).
    
    This test verifies that:
    1. When get_plugin_target_path is called multiple times
    2. With the same plugin file and target directory
    3. The returned path is always identical
    4. The routing is deterministic and consistent
    """
    temp_dirs = create_temp_dirs()
    try:
        plugin_installer = create_plugin_installer()
        
        # Test with each plugin type
        for file_type in [FileType.PLUGIN_LUA, FileType.PLUGIN_JS, FileType.SCRIPT_OPT]:
            if file_type == FileType.PLUGIN_LUA:
                extension = ".lua"
            elif file_type == FileType.PLUGIN_JS:
                extension = ".js"
            else:
                extension = ".conf"
            
            full_filename = f"{filename}{extension}"
            
            plugin_file = PackageFile(
                source_path=temp_dirs['source'] / full_filename,
                target_path=Path(full_filename),
                file_type=file_type,
                required=True
            )
            
            # Call get_plugin_target_path multiple times
            path1 = plugin_installer.get_plugin_target_path(
                plugin_file,
                temp_dirs['target']
            )
            path2 = plugin_installer.get_plugin_target_path(
                plugin_file,
                temp_dirs['target']
            )
            path3 = plugin_installer.get_plugin_target_path(
                plugin_file,
                temp_dirs['target']
            )
            
            # Verify all paths are identical
            assert path1 == path2 == path3, \
                f"get_plugin_target_path should be deterministic, but got different paths: " \
                f"{path1}, {path2}, {path3}"
    
    finally:
        cleanup_temp_dirs(temp_dirs)

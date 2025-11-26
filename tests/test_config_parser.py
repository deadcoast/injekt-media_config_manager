"""Property-based tests for config parser.

Feature: injekt-cli, Property 1: Package listing completeness
Validates: Requirements 1.1, 1.2, 1.4
"""

import json
import tempfile
from pathlib import Path
from hypothesis import given, strategies as st, settings

from injekt.io.config_parser import ConfigParser
from injekt.core.result import Success


# Strategy for generating valid player types
player_types = st.sampled_from(['mpv', 'vlc'])

# Strategy for generating valid profile types
profile_types = st.sampled_from(['performance', 'quality', 'cinematic', 'default'])

# Strategy for generating valid file types
file_types = st.sampled_from(['config', 'plugin_lua', 'plugin_js', 'shader', 'script_opt'])


@st.composite
def package_manifest(draw):
    """Generate a valid package manifest."""
    name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        whitelist_characters='_-'
    )))
    
    description = draw(st.text(min_size=1, max_size=200))
    
    player = draw(player_types)
    
    version = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(
        whitelist_categories=('Nd',),
        whitelist_characters='.'
    )))
    
    profile = draw(profile_types)
    
    # Generate files
    num_files = draw(st.integers(min_value=1, max_value=10))
    files = []
    for _ in range(num_files):
        file_name = draw(st.text(min_size=1, max_size=30, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='_-.'
        )))
        file_type = draw(file_types)
        required = draw(st.booleans())
        
        files.append({
            'source': file_name,
            'target': file_name,
            'type': file_type,
            'required': required
        })
    
    dependencies = draw(st.lists(st.text(min_size=1, max_size=30), max_size=5))
    
    return {
        'name': name,
        'description': description,
        'player': player,
        'version': version,
        'profile': profile,
        'files': files,
        'dependencies': dependencies
    }


@given(manifest_data=package_manifest())
@settings(max_examples=100)
def test_package_listing_completeness(manifest_data):
    """
    Feature: injekt-cli, Property 1: Package listing completeness
    Validates: Requirements 1.1, 1.2, 1.4
    
    For any set of available packages, listing packages should return all packages 
    with their name, description, player type, and version.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Write manifest file
        manifest_path = tmpdir_path / "manifest.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest_data, f)
        
        # Create dummy source files so they exist
        for file_entry in manifest_data['files']:
            source_file = tmpdir_path / file_entry['source']
            source_file.parent.mkdir(parents=True, exist_ok=True)
            source_file.touch()
        
        # Parse manifest
        parser = ConfigParser()
        result = parser.parse_package_manifest(manifest_path)
        
        # Should succeed
        assert isinstance(result, Success), f"Failed to parse valid manifest: {result}"
        
        package = result.value
        
        # Verify all required fields are present
        assert package.name == manifest_data['name'], "Package name should match"
        assert package.description == manifest_data['description'], "Package description should match"
        assert package.player.value == manifest_data['player'], "Package player should match"
        assert package.version == manifest_data['version'], "Package version should match"
        
        # Verify files are parsed
        assert len(package.files) == len(manifest_data['files']), "All files should be parsed"
        
        # Verify each file has correct properties
        for i, file_entry in enumerate(manifest_data['files']):
            pkg_file = package.files[i]
            assert pkg_file.file_type.value == file_entry['type'], f"File type should match for file {i}"
            assert pkg_file.required == file_entry['required'], f"Required flag should match for file {i}"


@given(
    name=st.text(min_size=1, max_size=50),
    description=st.text(min_size=1, max_size=200),
    player=player_types,
    version=st.text(min_size=1, max_size=20)
)
@settings(max_examples=100)
def test_package_parsing_preserves_metadata(name, description, player, version):
    """
    Feature: injekt-cli, Property 1: Package listing completeness
    Validates: Requirements 1.1, 1.2, 1.4
    
    For any package manifest, parsing should preserve all metadata fields.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create minimal valid manifest
        manifest_data = {
            'name': name,
            'description': description,
            'player': player,
            'version': version,
            'files': [
                {
                    'source': 'test.conf',
                    'target': 'test.conf',
                    'type': 'config',
                    'required': True
                }
            ],
            'dependencies': []
        }
        
        # Write manifest file
        manifest_path = tmpdir_path / "manifest.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest_data, f)
        
        # Create dummy source file
        (tmpdir_path / 'test.conf').touch()
        
        # Parse manifest
        parser = ConfigParser()
        result = parser.parse_package_manifest(manifest_path)
        
        # Should succeed
        assert isinstance(result, Success), f"Failed to parse valid manifest: {result}"
        
        package = result.value
        
        # All metadata should be preserved
        assert package.name == name, "Name should be preserved"
        assert package.description == description, "Description should be preserved"
        assert package.player.value == player, "Player should be preserved"
        assert package.version == version, "Version should be preserved"

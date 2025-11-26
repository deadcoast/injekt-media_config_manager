"""Tests for configuration validator."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from injekt.business.validator import ConfigValidatorImpl
from injekt.core.models import PlayerType
from injekt.core.result import is_success, is_failure
from injekt.core.errors import ValidationError


@pytest.fixture
def validator():
    """Create a validator instance."""
    return ConfigValidatorImpl()


@pytest.fixture
def temp_dir():
    """Create a temporary directory."""
    with TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestConfigValidation:
    """Tests for config file validation."""
    
    def test_validate_valid_mpv_config(self, validator, temp_dir):
        """Test validation of valid MPV config."""
        config_file = temp_dir / "mpv.conf"
        config_file.write_text("""# MPV Configuration
vo=gpu-next
gpu-api=vulkan
scale=ewa_lanczos
hwdec=no
fullscreen=yes
""")
        
        result = validator.validate_config_file(config_file, PlayerType.MPV)
        assert is_success(result)
    
    def test_validate_invalid_mpv_config_syntax(self, validator, temp_dir):
        """Test validation of invalid MPV config syntax."""
        config_file = temp_dir / "mpv.conf"
        config_file.write_text("""vo=gpu-next
this is invalid syntax
scale=ewa_lanczos
""")
        
        result = validator.validate_config_file(config_file, PlayerType.MPV)
        assert is_failure(result)
        assert "Line 2" in str(result.error)
    
    def test_validate_valid_vlc_config(self, validator, temp_dir):
        """Test validation of valid VLC config."""
        config_file = temp_dir / "vlcrc"
        config_file.write_text("""# VLC Configuration
video-output=direct3d11
fullscreen=0
avcodec-hw=none
swscale-mode=2
""")
        
        result = validator.validate_config_file(config_file, PlayerType.VLC)
        assert is_success(result)
    
    def test_validate_invalid_vlc_config_syntax(self, validator, temp_dir):
        """Test validation of invalid VLC config syntax."""
        config_file = temp_dir / "vlcrc"
        config_file.write_text("""video-output=direct3d11
invalid line without equals
fullscreen=0
""")
        
        result = validator.validate_config_file(config_file, PlayerType.VLC)
        assert is_failure(result)
        assert "Line 2" in str(result.error)
    
    def test_validate_nonexistent_config(self, validator, temp_dir):
        """Test validation of nonexistent config file."""
        config_file = temp_dir / "nonexistent.conf"
        
        result = validator.validate_config_file(config_file, PlayerType.MPV)
        assert is_failure(result)
        assert "does not exist" in str(result.error)
    
    def test_validate_config_with_comments(self, validator, temp_dir):
        """Test validation of config with comments."""
        config_file = temp_dir / "mpv.conf"
        config_file.write_text("""# This is a comment
vo=gpu-next
# Another comment
scale=ewa_lanczos
""")
        
        result = validator.validate_config_file(config_file, PlayerType.MPV)
        assert is_success(result)
    
    def test_validate_config_with_empty_lines(self, validator, temp_dir):
        """Test validation of config with empty lines."""
        config_file = temp_dir / "mpv.conf"
        config_file.write_text("""vo=gpu-next

scale=ewa_lanczos

hwdec=no
""")
        
        result = validator.validate_config_file(config_file, PlayerType.MPV)
        assert is_success(result)


class TestPluginValidation:
    """Tests for plugin file validation."""
    
    def test_validate_valid_lua_plugin(self, validator, temp_dir):
        """Test validation of valid Lua plugin."""
        plugin_file = temp_dir / "test.lua"
        plugin_file.write_text("""local msg = require 'mp.msg'

function test_function()
    mp.osd_message("Test", 1.5)
end

mp.register_script_message("test", test_function)
""")
        
        result = validator.validate_plugin(plugin_file)
        assert is_success(result)
    
    def test_validate_valid_js_plugin(self, validator, temp_dir):
        """Test validation of valid JS plugin."""
        plugin_file = temp_dir / "test.js"
        plugin_file.write_text("""'use strict';

var msg = mp.msg;

function testFunction() {
    mp.osd_message("Test", 1.5);
}

mp.register_script_message("test", testFunction);
""")
        
        result = validator.validate_plugin(plugin_file)
        assert is_success(result)
    
    def test_validate_nonexistent_plugin(self, validator, temp_dir):
        """Test validation of nonexistent plugin."""
        plugin_file = temp_dir / "nonexistent.lua"
        
        result = validator.validate_plugin(plugin_file)
        assert is_failure(result)
        assert "does not exist" in str(result.error)
    
    def test_validate_invalid_plugin_extension(self, validator, temp_dir):
        """Test validation of plugin with invalid extension."""
        plugin_file = temp_dir / "test.txt"
        plugin_file.write_text("some content")
        
        result = validator.validate_plugin(plugin_file)
        assert is_failure(result)
        assert "Unknown plugin type" in str(result.error)


class TestShaderValidation:
    """Tests for shader file validation."""
    
    def test_validate_valid_shader(self, validator, temp_dir):
        """Test validation of valid shader."""
        shader_file = temp_dir / "test.glsl"
        shader_file.write_text("""#version 330

uniform sampler2D texture;
in vec2 texcoord;
out vec4 fragColor;

void main() {
    fragColor = texture(texture, texcoord);
}
""")
        
        result = validator.validate_shader(shader_file)
        assert is_success(result)
    
    def test_validate_shader_with_pragma(self, validator, temp_dir):
        """Test validation of shader with pragma version."""
        shader_file = temp_dir / "test.glsl"
        shader_file.write_text("""#pragma version 330

void main() {
    gl_FragColor = vec4(1.0);
}
""")
        
        result = validator.validate_shader(shader_file)
        assert is_success(result)
    
    def test_validate_shader_invalid_extension(self, validator, temp_dir):
        """Test validation of shader with invalid extension."""
        shader_file = temp_dir / "test.txt"
        shader_file.write_text("void main() {}")
        
        result = validator.validate_shader(shader_file)
        assert is_failure(result)
        assert "Invalid shader extension" in str(result.error)
    
    def test_validate_shader_unbalanced_braces(self, validator, temp_dir):
        """Test validation of shader with unbalanced braces."""
        shader_file = temp_dir / "test.glsl"
        shader_file.write_text("""void main() {
    vec4 color = vec4(1.0);
""")
        
        result = validator.validate_shader(shader_file)
        assert is_failure(result)
        assert "Unbalanced braces" in str(result.error)
    
    def test_validate_nonexistent_shader(self, validator, temp_dir):
        """Test validation of nonexistent shader."""
        shader_file = temp_dir / "nonexistent.glsl"
        
        result = validator.validate_shader(shader_file)
        assert is_failure(result)
        assert "does not exist" in str(result.error)

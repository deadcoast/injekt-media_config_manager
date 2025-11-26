"""Property-based tests for configuration validator.

Feature: injekt-cli, Property 19: Validation error reporting
Validates: Requirements 4.4
"""

from pathlib import Path
from tempfile import TemporaryDirectory
from hypothesis import given, strategies as st, settings

from injekt.business.validator import ConfigValidatorImpl
from injekt.core.models import PlayerType
from injekt.core.result import is_failure, is_success


# Strategy for generating invalid config lines
# Use printable ASCII to avoid encoding issues
invalid_config_lines = st.one_of(
    st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=1, max_size=50).filter(
        lambda x: '=' not in x and not x.strip().startswith('#') and x.strip()
    ),
    st.just("this is invalid"),
    st.just("no equals sign here"),
    st.just("multiple === equals"),
)


@settings(max_examples=100)
@given(
    invalid_line=invalid_config_lines,
    line_position=st.integers(min_value=1, max_value=10)
)
def test_property_validation_error_reporting_mpv(invalid_line, line_position):
    """
    Feature: injekt-cli, Property 19: Validation error reporting
    
    For any validation failure, the error report should include the file name 
    and specific error details (line numbers).
    
    Validates: Requirements 4.4
    """
    validator = ConfigValidatorImpl()
    
    with TemporaryDirectory() as tmpdir:
        temp_dir = Path(tmpdir)
        
        # Generate a config with an invalid line at a specific position
        valid_lines = ["vo=gpu-next", "scale=ewa_lanczos", "hwdec=no"]
        
        # Insert invalid line at the specified position
        lines = valid_lines[:line_position] + [invalid_line] + valid_lines[line_position:]
        
        config_file = temp_dir / "test_mpv.conf"
        config_file.write_text('\n'.join(lines))
        
        result = validator.validate_config_file(config_file, PlayerType.MPV)
        
        # Property: validation failures must include file name and line number
        if is_failure(result):
            error_msg = str(result.error)
            
            # Check that error message includes the file name
            assert str(config_file) in error_msg or config_file.name in error_msg, \
                f"Error message should include file name. Got: {error_msg}"
            
            # Check that error message includes line number information
            assert "Line" in error_msg, \
                f"Error message should include line number. Got: {error_msg}"
            
            # Check that the line number is present
            assert any(str(i) in error_msg for i in range(1, len(lines) + 1)), \
                f"Error message should include a line number. Got: {error_msg}"


@settings(max_examples=100)
@given(
    invalid_line=invalid_config_lines,
    line_position=st.integers(min_value=1, max_value=10)
)
def test_property_validation_error_reporting_vlc(invalid_line, line_position):
    """
    Feature: injekt-cli, Property 19: Validation error reporting
    
    For any validation failure, the error report should include the file name 
    and specific error details (line numbers) for VLC configs.
    
    Validates: Requirements 4.4
    """
    validator = ConfigValidatorImpl()
    
    with TemporaryDirectory() as tmpdir:
        temp_dir = Path(tmpdir)
        
        # Generate a config with an invalid line at a specific position
        valid_lines = ["video-output=direct3d11", "fullscreen=0", "avcodec-hw=none"]
        
        # Insert invalid line at the specified position
        lines = valid_lines[:line_position] + [invalid_line] + valid_lines[line_position:]
        
        config_file = temp_dir / "test_vlcrc"
        config_file.write_text('\n'.join(lines))
        
        result = validator.validate_config_file(config_file, PlayerType.VLC)
        
        # Property: validation failures must include file name and line number
        if is_failure(result):
            error_msg = str(result.error)
            
            # Check that error message includes the file name
            assert str(config_file) in error_msg or config_file.name in error_msg, \
                f"Error message should include file name. Got: {error_msg}"
            
            # Check that error message includes line number information
            assert "Line" in error_msg, \
                f"Error message should include line number. Got: {error_msg}"
            
            # Check that the line number is present
            assert any(str(i) in error_msg for i in range(1, len(lines) + 1)), \
                f"Error message should include a line number. Got: {error_msg}"


@settings(max_examples=100)
@given(
    num_errors=st.integers(min_value=1, max_value=5)
)
def test_property_multiple_validation_errors_reported(num_errors):
    """
    Feature: injekt-cli, Property 19: Validation error reporting
    
    For any validation with multiple failures, all errors should be reported
    with their respective line numbers.
    
    Validates: Requirements 4.4
    """
    validator = ConfigValidatorImpl()
    
    with TemporaryDirectory() as tmpdir:
        temp_dir = Path(tmpdir)
        
        # Generate a config with multiple invalid lines
        lines = []
        invalid_line_numbers = []
        
        for i in range(num_errors * 2):
            if i % 2 == 0:
                lines.append("vo=gpu-next")
            else:
                lines.append("this is invalid")
                invalid_line_numbers.append(i + 1)
        
        config_file = temp_dir / "multi_error.conf"
        config_file.write_text('\n'.join(lines))
        
        result = validator.validate_config_file(config_file, PlayerType.MPV)
        
        # Property: all validation errors must be reported
        if is_failure(result):
            error_msg = str(result.error)
            
            # Check that error message includes the file name
            assert str(config_file) in error_msg or config_file.name in error_msg
            
            # Check that all invalid line numbers are mentioned
            for line_num in invalid_line_numbers:
                assert f"Line {line_num}" in error_msg or str(line_num) in error_msg, \
                    f"Error message should include line {line_num}. Got: {error_msg}"



@settings(max_examples=100)
@given(
    num_valid_files=st.integers(min_value=1, max_value=5),
    num_invalid_files=st.integers(min_value=0, max_value=3),
    player=st.sampled_from([PlayerType.MPV, PlayerType.VLC])
)
def test_property_validation_before_installation(num_valid_files, num_invalid_files, player):
    """
    Feature: injekt-cli, Property 4: Validation before installation
    
    For any package, installation should only proceed if all required files pass validation.
    This test verifies that the validator correctly identifies invalid files.
    
    Validates: Requirements 4.1, 4.2, 4.3, 4.5
    """
    validator = ConfigValidatorImpl()
    
    with TemporaryDirectory() as tmpdir:
        temp_dir = Path(tmpdir)
        
        # Create valid config files
        valid_files = []
        for i in range(num_valid_files):
            if player == PlayerType.MPV:
                config_file = temp_dir / f"valid_{i}.conf"
                config_file.write_text("vo=gpu-next\nscale=ewa_lanczos\n")
            else:
                config_file = temp_dir / f"valid_{i}.conf"
                config_file.write_text("video-output=direct3d11\nfullscreen=0\n")
            valid_files.append(config_file)
        
        # Create invalid config files
        invalid_files = []
        for i in range(num_invalid_files):
            config_file = temp_dir / f"invalid_{i}.conf"
            config_file.write_text("this is invalid\nno equals sign\n")
            invalid_files.append(config_file)
        
        # Property: All valid files should pass validation
        for valid_file in valid_files:
            result = validator.validate_config_file(valid_file, player)
            assert is_success(result), \
                f"Valid file {valid_file} should pass validation"
        
        # Property: All invalid files should fail validation
        for invalid_file in invalid_files:
            result = validator.validate_config_file(invalid_file, player)
            assert is_failure(result), \
                f"Invalid file {invalid_file} should fail validation"


@settings(max_examples=100)
@given(
    plugin_type=st.sampled_from(['.lua', '.js']),
    has_mp_api=st.booleans()
)
def test_property_plugin_validation_before_installation(plugin_type, has_mp_api):
    """
    Feature: injekt-cli, Property 4: Validation before installation
    
    For any plugin file, validation should check basic syntax and structure.
    
    Validates: Requirements 4.2, 4.5
    """
    validator = ConfigValidatorImpl()
    
    with TemporaryDirectory() as tmpdir:
        temp_dir = Path(tmpdir)
        
        plugin_file = temp_dir / f"test{plugin_type}"
        
        if plugin_type == '.lua':
            if has_mp_api:
                content = """local msg = require 'mp.msg'
function test()
    mp.osd_message("Test", 1.5)
end
mp.register_script_message("test", test)
"""
            else:
                content = """function test()
    print("Test")
end
"""
        else:  # .js
            if has_mp_api:
                content = """'use strict';
var msg = mp.msg;
function test() {
    mp.osd_message("Test", 1.5);
}
"""
            else:
                content = """'use strict';
function test() {
    console.log("Test");
}
"""
        
        plugin_file.write_text(content)
        
        # Property: Plugin validation should succeed for well-formed files
        result = validator.validate_plugin(plugin_file)
        assert is_success(result), \
            f"Well-formed plugin {plugin_file} should pass validation"


@settings(max_examples=100)
@given(
    has_version=st.booleans(),
    has_keywords=st.booleans(),
    balanced_braces=st.booleans()
)
def test_property_shader_validation_before_installation(has_version, has_keywords, balanced_braces):
    """
    Feature: injekt-cli, Property 4: Validation before installation
    
    For any shader file, validation should check GLSL syntax basics.
    
    Validates: Requirements 4.3, 4.5
    """
    validator = ConfigValidatorImpl()
    
    with TemporaryDirectory() as tmpdir:
        temp_dir = Path(tmpdir)
        
        shader_file = temp_dir / "test.glsl"
        
        content_parts = []
        
        if has_version:
            content_parts.append("#version 330")
        
        if has_keywords:
            content_parts.append("uniform sampler2D texture;")
            content_parts.append("in vec2 texcoord;")
            content_parts.append("out vec4 fragColor;")
            content_parts.append("void main() {")
            if balanced_braces:
                content_parts.append("    fragColor = texture(texture, texcoord);")
                content_parts.append("}")
            else:
                content_parts.append("    fragColor = texture(texture, texcoord);")
                # Missing closing brace
        else:
            content_parts.append("// Empty shader")
        
        content = '\n'.join(content_parts)
        shader_file.write_text(content)
        
        result = validator.validate_shader(shader_file)
        
        # Property: Shader validation should fail if missing keywords or unbalanced braces
        if not has_keywords:
            assert is_failure(result), \
                "Shader without GLSL keywords should fail validation"
        elif not balanced_braces:
            assert is_failure(result), \
                "Shader with unbalanced braces should fail validation"
        else:
            # Should pass if has keywords and balanced braces
            assert is_success(result), \
                "Shader with keywords and balanced braces should pass validation"

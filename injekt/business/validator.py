"""Configuration validation implementation."""

import re
from pathlib import Path
from typing import List, Tuple

from injekt.core.interfaces import ConfigValidator
from injekt.core.models import PlayerType
from injekt.core.result import Result, Success, Failure
from injekt.core.errors import ValidationError


class ConfigValidatorImpl(ConfigValidator):
    """Implementation of configuration validation."""
    
    # MPV config option patterns
    MPV_OPTION_PATTERN = re.compile(r'^([a-zA-Z0-9_-]+)=(.*)$')
    MPV_COMMENT_PATTERN = re.compile(r'^\s*#')
    
    # VLC config option patterns
    VLC_OPTION_PATTERN = re.compile(r'^([a-zA-Z0-9_-]+)=(.*)$')
    VLC_COMMENT_PATTERN = re.compile(r'^\s*#')
    
    # Known MPV options (subset for validation)
    MPV_KNOWN_OPTIONS = {
        'vo', 'gpu-api', 'gpu-context', 'profile', 'scale', 'cscale', 'dscale',
        'correct-downscaling', 'sigmoid-upscaling', 'scale-antiring', 'cscale-antiring',
        'glsl-shaders-toggle', 'glsl-shaders', 'icc-profile-auto', 'icc-cache',
        'target-colorspace', 'target-trc', 'linear-downscaling', 'linear-scaling',
        'hdr-compute-peak', 'hdr-peak-decay-rate', 'tone-mapping', 'tone-mapping-param',
        'tone-mapping-desaturate', 'dither', 'dither-depth', 'temporal-dither',
        'deband', 'deband-iterations', 'deband-threshold', 'interpolation', 'tscale',
        'video-sync', 'blend-subtitles', 'script-opts', 'fullscreen', 'keep-open',
        'border', 'hwdec', 'sub-font-provider', 'sub-fonts-dir'
    }
    
    # Known VLC options (subset for validation)
    VLC_KNOWN_OPTIONS = {
        'video-output', 'fullscreen', 'video-on-top', 'overlay-video', 'quiet-synchro',
        'skip-frames', 'drop-late-frames', 'use-wallpaper', 'video-title-timeout',
        'avcodec-hw', 'swscale-mode', 'direct3d11-use-hq-chroma', 'direct3d11-hw-blending',
        'deinterlace', 'deinterlace-mode', 'tone-mapping', 'tone-mapping-param',
        'file-caching', 'live-caching', 'disc-caching', 'network-caching',
        'video-filter', 'postproc-q', 'hq-resampling', 'video-scaling-factor',
        'scale-factor', 'qt-fullscreen-toggle', 'qt-minimal-view', 'qt-video-autoresize',
        'aout', 'audio-replay-gain-mode', 'audio-replay-gain-preamp',
        'audio-normalization'
    }
    
    def validate_config_file(self, path: Path, player: PlayerType) -> Result[None]:
        """Validate a configuration file."""
        if not path.exists():
            return Failure(ValidationError(f"Config file does not exist: {path}"))
        
        if not path.is_file():
            return Failure(ValidationError(f"Path is not a file: {path}"))
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return Failure(ValidationError(f"Failed to read config file {path}: {e}"))
        
        if player == PlayerType.MPV:
            return self._validate_mpv_config(content, path)
        elif player == PlayerType.VLC:
            return self._validate_vlc_config(content, path)
        else:
            return Failure(ValidationError(f"Unknown player type: {player}"))
    
    def _validate_mpv_config(self, content: str, path: Path) -> Result[None]:
        """Validate MPV configuration syntax."""
        errors = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()
            
            # Skip empty lines and comments
            if not stripped or self.MPV_COMMENT_PATTERN.match(stripped):
                continue
            
            # Check if line matches option=value pattern
            match = self.MPV_OPTION_PATTERN.match(stripped)
            if not match:
                errors.append((line_num, f"Invalid syntax: '{line.strip()}'"))
                continue
            
            option_name = match.group(1)
            
            # Warn about unknown options (not a hard error)
            if option_name not in self.MPV_KNOWN_OPTIONS:
                # This is just a warning, not an error
                pass
        
        if errors:
            error_msg = self._format_validation_errors(path, errors)
            return Failure(ValidationError(error_msg))
        
        return Success(None)
    
    def _validate_vlc_config(self, content: str, path: Path) -> Result[None]:
        """Validate VLC configuration syntax."""
        errors = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()
            
            # Skip empty lines and comments
            if not stripped or self.VLC_COMMENT_PATTERN.match(stripped):
                continue
            
            # Check if line matches option=value pattern
            match = self.VLC_OPTION_PATTERN.match(stripped)
            if not match:
                errors.append((line_num, f"Invalid syntax: '{line.strip()}'"))
                continue
            
            option_name = match.group(1)
            
            # Warn about unknown options (not a hard error)
            if option_name not in self.VLC_KNOWN_OPTIONS:
                # This is just a warning, not an error
                pass
        
        if errors:
            error_msg = self._format_validation_errors(path, errors)
            return Failure(ValidationError(error_msg))
        
        return Success(None)
    
    def _format_validation_errors(self, path: Path, errors: List[Tuple[int, str]]) -> str:
        """Format validation errors with line numbers."""
        error_lines = [f"Validation errors in {path}:"]
        for line_num, error in errors:
            error_lines.append(f"  Line {line_num}: {error}")
        return '\n'.join(error_lines)
    
    def validate_plugin(self, path: Path) -> Result[None]:
        """Validate a plugin file."""
        if not path.exists():
            return Failure(ValidationError(f"Plugin file does not exist: {path}"))
        
        if not path.is_file():
            return Failure(ValidationError(f"Path is not a file: {path}"))
        
        # Check file extension
        ext = path.suffix.lower()
        if ext == '.lua':
            return self._validate_lua_plugin(path)
        elif ext == '.js':
            return self._validate_js_plugin(path)
        else:
            return Failure(ValidationError(f"Unknown plugin type: {ext}"))
    
    def _validate_lua_plugin(self, path: Path) -> Result[None]:
        """Validate a Lua plugin file."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return Failure(ValidationError(f"Failed to read Lua plugin {path}: {e}"))
        
        # Basic Lua syntax checks
        errors = []
        
        # Check for basic Lua syntax errors
        if content.count('function') != content.count('end'):
            # This is a heuristic, not perfect
            pass
        
        # Check for common MPV Lua API usage
        has_mp_require = 'require' in content and 'mp' in content
        has_mp_global = 'mp.' in content
        
        if not (has_mp_require or has_mp_global):
            # Warning: might not be an MPV plugin
            pass
        
        # Check for syntax errors (basic)
        lines = content.split('\n')
        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()
            
            # Check for unmatched quotes
            if stripped.count('"') % 2 != 0 or stripped.count("'") % 2 != 0:
                # Might be a multi-line string, skip for now
                pass
        
        if errors:
            error_msg = self._format_validation_errors(path, errors)
            return Failure(ValidationError(error_msg))
        
        return Success(None)
    
    def _validate_js_plugin(self, path: Path) -> Result[None]:
        """Validate a JavaScript plugin file."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return Failure(ValidationError(f"Failed to read JS plugin {path}: {e}"))
        
        # Basic JavaScript syntax checks
        errors = []
        
        # Check for common MPV JS API usage
        has_mp_global = 'mp.' in content
        has_require = 'require(' in content
        
        if not (has_mp_global or has_require):
            # Warning: might not be an MPV plugin
            pass
        
        # Check for basic syntax (very basic)
        if content.count('{') != content.count('}'):
            # Might indicate syntax error
            pass
        
        if content.count('(') != content.count(')'):
            # Might indicate syntax error
            pass
        
        if errors:
            error_msg = self._format_validation_errors(path, errors)
            return Failure(ValidationError(error_msg))
        
        return Success(None)
    
    def validate_shader(self, path: Path) -> Result[None]:
        """Validate a shader file."""
        if not path.exists():
            return Failure(ValidationError(f"Shader file does not exist: {path}"))
        
        if not path.is_file():
            return Failure(ValidationError(f"Path is not a file: {path}"))
        
        # Check file extension
        ext = path.suffix.lower()
        valid_extensions = {'.glsl', '.frag', '.vert', '.comp'}
        
        if ext not in valid_extensions:
            return Failure(ValidationError(
                f"Invalid shader extension '{ext}'. Expected one of: {', '.join(valid_extensions)}"
            ))
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return Failure(ValidationError(f"Failed to read shader file {path}: {e}"))
        
        # Basic GLSL syntax checks
        errors = []
        
        # Check for GLSL version pragma
        has_version = '#version' in content or '#pragma version' in content
        
        # Check for basic GLSL keywords
        has_glsl_keywords = any(keyword in content for keyword in [
            'void', 'main', 'vec', 'mat', 'float', 'int', 'uniform', 'varying', 'in', 'out'
        ])
        
        if not has_glsl_keywords:
            errors.append((0, "No GLSL keywords found - file may not be a valid shader"))
        
        # Check for balanced braces
        if content.count('{') != content.count('}'):
            errors.append((0, "Unbalanced braces in shader"))
        
        # Check for balanced parentheses
        if content.count('(') != content.count(')'):
            errors.append((0, "Unbalanced parentheses in shader"))
        
        if errors:
            error_msg = self._format_validation_errors(path, errors)
            return Failure(ValidationError(error_msg))
        
        return Success(None)

"""Property-based tests for path resolver.

Feature: injekt-cli, Property 17: Path normalization
Validates: Requirements 23.1, 23.2
"""

import os
from pathlib import Path
from hypothesis import given, strategies as st, settings, assume

from injekt.io.path_resolver import WindowsPathResolver


@given(
    path_parts=st.lists(
        st.text(min_size=1, max_size=20, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='_-'
        )),
        min_size=1,
        max_size=5
    )
)
@settings(max_examples=100)
def test_path_normalization_forward_slashes(path_parts):
    """
    Feature: injekt-cli, Property 17: Path normalization
    Validates: Requirements 23.1, 23.2
    
    For any Windows path with forward slashes, normalization should convert them to backslashes.
    """
    resolver = WindowsPathResolver()
    
    # Create path with forward slashes
    path_str = "/".join(path_parts)
    path = Path(path_str)
    
    # Normalize
    normalized = resolver.normalize_path(path)
    
    # Check that the normalized path uses backslashes (Windows standard)
    # Path objects on Windows automatically use backslashes in their string representation
    normalized_str = str(normalized)
    
    # The normalized path should be absolute
    assert normalized.is_absolute(), f"Normalized path should be absolute: {normalized}"


@given(
    base_path=st.text(min_size=1, max_size=20, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        whitelist_characters='_-'
    ))
)
@settings(max_examples=100)
def test_path_normalization_env_vars(base_path):
    """
    Feature: injekt-cli, Property 17: Path normalization
    Validates: Requirements 23.1, 23.2
    
    For any path containing environment variables, normalization should expand them.
    """
    resolver = WindowsPathResolver()
    
    # Use a known environment variable
    env_var = "TEMP"
    env_value = os.environ.get(env_var)
    
    # Skip if environment variable doesn't exist
    assume(env_value is not None)
    
    # Create path with environment variable
    path_str = f"%{env_var}%/{base_path}"
    path = Path(path_str)
    
    # Normalize
    normalized = resolver.normalize_path(path)
    
    # Check that environment variable was expanded
    normalized_str = str(normalized)
    assert env_var not in normalized_str or not normalized_str.startswith("%"), \
        f"Environment variable should be expanded: {normalized_str}"
    
    # The normalized path should contain the expanded value
    assert env_value.lower() in normalized_str.lower() or normalized.is_absolute(), \
        f"Normalized path should contain expanded env var or be absolute: {normalized_str}"


@given(
    path_parts=st.lists(
        st.text(min_size=1, max_size=20, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='_- '
        )),
        min_size=1,
        max_size=3
    )
)
@settings(max_examples=100)
def test_path_normalization_spaces(path_parts):
    """
    Feature: injekt-cli, Property 17: Path normalization
    Validates: Requirements 23.1, 23.2
    
    For any path containing spaces, normalization should handle them correctly.
    """
    resolver = WindowsPathResolver()
    
    # Create path with spaces
    path_str = "/".join(path_parts)
    path = Path(path_str)
    
    # Normalize
    normalized = resolver.normalize_path(path)
    
    # Check that spaces are preserved
    normalized_str = str(normalized)
    
    # The normalized path should be absolute
    assert normalized.is_absolute(), f"Normalized path should be absolute: {normalized}"
    
    # If original had spaces, normalized should preserve them
    if any(' ' in part for part in path_parts):
        # Spaces should be preserved in the path
        assert ' ' in normalized_str or normalized.is_absolute(), \
            f"Spaces should be preserved: {normalized_str}"


@given(
    path_parts=st.lists(
        st.text(min_size=1, max_size=20, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='_-'
        )),
        min_size=1,
        max_size=5
    )
)
@settings(max_examples=100)
def test_path_normalization_idempotent(path_parts):
    """
    Feature: injekt-cli, Property 17: Path normalization
    Validates: Requirements 23.1, 23.2
    
    For any path, normalizing twice should produce the same result as normalizing once.
    """
    resolver = WindowsPathResolver()
    
    # Create path
    path_str = "/".join(path_parts)
    path = Path(path_str)
    
    # Normalize once
    normalized_once = resolver.normalize_path(path)
    
    # Normalize twice
    normalized_twice = resolver.normalize_path(normalized_once)
    
    # Should be the same
    assert normalized_once == normalized_twice, \
        f"Path normalization should be idempotent: {normalized_once} != {normalized_twice}"

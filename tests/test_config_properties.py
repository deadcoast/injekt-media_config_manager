"""Property-based tests for configuration management."""

from pathlib import Path
from hypothesis import given, strategies as st
from injekt.config import InjektConfig
from injekt.core.models import PlayerType


# Strategies for generating config values
player_strategy = st.sampled_from([PlayerType.MPV, PlayerType.VLC])
bool_strategy = st.booleans()
output_format_strategy = st.sampled_from(["text", "json", "table"])
max_backups_strategy = st.integers(min_value=0, max_value=100)
path_strategy = st.builds(
    lambda p: Path(p),
    st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), min_codepoint=65, max_codepoint=122),
        min_size=1,
        max_size=20
    )
)
absolute_path_strategy = st.builds(
    lambda parts: Path("/").joinpath(*parts) if parts else Path("/tmp"),
    st.lists(
        st.text(
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), min_codepoint=65, max_codepoint=122),
            min_size=1,
            max_size=10
        ),
        min_size=1,
        max_size=5
    )
)


def config_strategy():
    """Strategy for generating InjektConfig instances."""
    return st.builds(
        InjektConfig,
        assets_dir=path_strategy,
        backup_dir=absolute_path_strategy,
        state_file=absolute_path_strategy,
        log_dir=absolute_path_strategy,
        max_backups=max_backups_strategy,
        default_player=player_strategy,
        verbose=bool_strategy,
        dry_run=bool_strategy,
        output_format=output_format_strategy
    )


@given(
    base=config_strategy(),
    override=config_strategy()
)
def test_config_merge_precedence(base, override):
    """
    Feature: injekt-cli, Property 18: Config merge precedence
    
    For any configuration merge, settings should follow the precedence order:
    user > profile > default, where 'override' represents higher precedence.
    
    Validates: Requirements 24.2
    """
    # Get default config for comparison
    default = InjektConfig()
    
    # Merge base with override (override has higher precedence)
    merged = base.merge(override)
    
    # For each field, if override differs from default, merged should use override's value
    # Otherwise, merged should use base's value
    
    if override.assets_dir != default.assets_dir:
        assert merged.assets_dir == override.assets_dir, \
            f"Expected merged.assets_dir to be {override.assets_dir}, got {merged.assets_dir}"
    else:
        assert merged.assets_dir == base.assets_dir, \
            f"Expected merged.assets_dir to be {base.assets_dir}, got {merged.assets_dir}"
    
    if override.backup_dir != default.backup_dir:
        assert merged.backup_dir == override.backup_dir, \
            f"Expected merged.backup_dir to be {override.backup_dir}, got {merged.backup_dir}"
    else:
        assert merged.backup_dir == base.backup_dir, \
            f"Expected merged.backup_dir to be {base.backup_dir}, got {merged.backup_dir}"
    
    if override.state_file != default.state_file:
        assert merged.state_file == override.state_file, \
            f"Expected merged.state_file to be {override.state_file}, got {merged.state_file}"
    else:
        assert merged.state_file == base.state_file, \
            f"Expected merged.state_file to be {base.state_file}, got {merged.state_file}"
    
    if override.log_dir != default.log_dir:
        assert merged.log_dir == override.log_dir, \
            f"Expected merged.log_dir to be {override.log_dir}, got {merged.log_dir}"
    else:
        assert merged.log_dir == base.log_dir, \
            f"Expected merged.log_dir to be {base.log_dir}, got {merged.log_dir}"
    
    if override.max_backups != default.max_backups:
        assert merged.max_backups == override.max_backups, \
            f"Expected merged.max_backups to be {override.max_backups}, got {merged.max_backups}"
    else:
        assert merged.max_backups == base.max_backups, \
            f"Expected merged.max_backups to be {base.max_backups}, got {merged.max_backups}"
    
    if override.default_player != default.default_player:
        assert merged.default_player == override.default_player, \
            f"Expected merged.default_player to be {override.default_player}, got {merged.default_player}"
    else:
        assert merged.default_player == base.default_player, \
            f"Expected merged.default_player to be {base.default_player}, got {merged.default_player}"
    
    if override.verbose != default.verbose:
        assert merged.verbose == override.verbose, \
            f"Expected merged.verbose to be {override.verbose}, got {merged.verbose}"
    else:
        assert merged.verbose == base.verbose, \
            f"Expected merged.verbose to be {base.verbose}, got {merged.verbose}"
    
    if override.dry_run != default.dry_run:
        assert merged.dry_run == override.dry_run, \
            f"Expected merged.dry_run to be {override.dry_run}, got {merged.dry_run}"
    else:
        assert merged.dry_run == base.dry_run, \
            f"Expected merged.dry_run to be {base.dry_run}, got {merged.dry_run}"
    
    if override.output_format != default.output_format:
        assert merged.output_format == override.output_format, \
            f"Expected merged.output_format to be {override.output_format}, got {merged.output_format}"
    else:
        assert merged.output_format == base.output_format, \
            f"Expected merged.output_format to be {base.output_format}, got {merged.output_format}"


@given(config=config_strategy())
def test_merge_with_default_is_identity(config):
    """
    Merging a config with default config should return the original config.
    
    This tests that when override has all default values, the base config
    is preserved.
    """
    default = InjektConfig()
    merged = config.merge(default)
    
    # Since default has all default values, merged should equal config
    assert merged.assets_dir == config.assets_dir
    assert merged.backup_dir == config.backup_dir
    assert merged.state_file == config.state_file
    assert merged.log_dir == config.log_dir
    assert merged.max_backups == config.max_backups
    assert merged.default_player == config.default_player
    assert merged.verbose == config.verbose
    assert merged.dry_run == config.dry_run
    assert merged.output_format == config.output_format


@given(config=config_strategy())
def test_merge_is_not_mutating(config):
    """
    Merging configs should not mutate the original configs.
    """
    default = InjektConfig()
    
    # Store original values
    original_assets = config.assets_dir
    original_backups = config.max_backups
    original_verbose = config.verbose
    
    # Perform merge
    merged = config.merge(default)
    
    # Original should be unchanged
    assert config.assets_dir == original_assets
    assert config.max_backups == original_backups
    assert config.verbose == original_verbose

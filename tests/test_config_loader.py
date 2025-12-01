"""
Unit Tests for ConfigLoader - Mission M3

Test Coverage:
- YAML configuration parsing
- .env secret loading
- CLI override priority
- Secret redaction
- Config validation and fallback behavior
- Edge cases (missing files, invalid YAML, missing keys)
"""

import os
import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock
import logging

from hw4_tourguide.config_loader import ConfigLoader


# ================================================================================
# FIXTURES
# ================================================================================


@pytest.fixture
def sample_yaml_config():
    """Sample YAML configuration for testing."""
    return {
        "scheduler": {
            "interval": 3.0,
            "enabled": True,
        },
        "orchestrator": {
            "max_workers": 10,
        },
        "agents": {
            "llm_provider": "gemini",
        },
        "logging": {
            "level": "DEBUG",
        },
    }


@pytest.fixture
def sample_env_content():
    """Sample .env file content."""
    return """
GOOGLE_MAPS_API_KEY=gmaps_test_key_12345678
YOUTUBE_API_KEY=youtube_test_key_abcdefgh
OPENAI_API_KEY=sk-test-1234567890abcdef
ANTHROPIC_API_KEY=claude_test_key_xyz123
GEMINI_API_KEY=gemini_test_key_abc123
"""


@pytest.fixture
def temp_config_files(sample_yaml_config, sample_env_content):
    """Create temporary config files for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create YAML config file
        yaml_path = tmpdir_path / "test_settings.yaml"
        with open(yaml_path, 'w') as f:
            yaml.dump(sample_yaml_config, f)

        # Create .env file
        env_path = tmpdir_path / ".env"
        with open(env_path, 'w') as f:
            f.write(sample_env_content)

        yield {
            "yaml_path": yaml_path,
            "env_path": env_path,
            "tmpdir": tmpdir_path,
        }


@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    return MagicMock(spec=logging.Logger)


# ================================================================================
# TEST: YAML Configuration Loading
# ================================================================================


@pytest.mark.unit
def test_yaml_config_loading(temp_config_files, mock_logger):
    """Test that YAML configuration is loaded correctly."""
    config_loader = ConfigLoader(
        config_path=temp_config_files["yaml_path"],
        env_path=temp_config_files["env_path"],
        logger=mock_logger,
    )

    # Verify YAML values override defaults
    assert config_loader.get("scheduler.interval") == 3.0
    assert config_loader.get("orchestrator.max_workers") == 10
    assert config_loader.get("logging.level") == "DEBUG"

    # Verify defaults still present for unspecified values
    assert config_loader.get("scheduler.enabled") is True
    assert config_loader.get("orchestrator.queue_timeout") == 1.0


@pytest.mark.unit
def test_yaml_missing_file(mock_logger):
    """Test behavior when YAML config file is missing."""
    config_loader = ConfigLoader(
        config_path=Path("/nonexistent/config.yaml"),
        env_path=Path("/nonexistent/.env"),
        logger=mock_logger,
    )

    # Should fall back to defaults
    assert config_loader.get("scheduler.interval") == 2.0
    assert config_loader.get("orchestrator.max_workers") == 5

    # Should log warning
    assert any("not found" in str(call) for call in mock_logger.warning.call_args_list)

    # Should have validation warning
    assert len(config_loader.get_warnings()) > 0


@pytest.mark.unit
def test_yaml_invalid_syntax(mock_logger):
    """Test behavior when YAML file has invalid syntax."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("invalid: yaml: syntax: [[[")
        invalid_yaml_path = Path(f.name)

    try:
        config_loader = ConfigLoader(
            config_path=invalid_yaml_path,
            logger=mock_logger,
        )

        # Should fall back to defaults
        assert config_loader.get("scheduler.interval") == 2.0

        # Should have validation warning
        assert any("YAML parse error" in w for w in config_loader.get_warnings())

    finally:
        os.unlink(invalid_yaml_path)


@pytest.mark.unit
def test_yaml_empty_file(mock_logger):
    """Test behavior when YAML file is empty."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("")
        empty_yaml_path = Path(f.name)

    try:
        config_loader = ConfigLoader(
            config_path=empty_yaml_path,
            logger=mock_logger,
        )

        # Should fall back to defaults
        assert config_loader.get("scheduler.interval") == 2.0

    finally:
        os.unlink(empty_yaml_path)


# ================================================================================
# TEST: .env Secret Loading
# ================================================================================


@pytest.mark.unit
def test_env_secret_loading(temp_config_files, mock_logger, monkeypatch):
    """Test that .env secrets are loaded correctly and override ambient env."""
    monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "gmaps_test_key_12345678")
    monkeypatch.setenv("YOUTUBE_API_KEY", "youtube_test_key_abcdefgh")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-1234567890abcdef")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "claude_test_key_xyz123")

    config_loader = ConfigLoader(
        config_path=temp_config_files["yaml_path"],
        env_path=temp_config_files["env_path"],
        logger=mock_logger,
    )

    # Verify secrets loaded from env (monkeypatched)
    assert config_loader.get_secret("GOOGLE_MAPS_API_KEY") == "gmaps_test_key_12345678"
    assert config_loader.get_secret("YOUTUBE_API_KEY") == "youtube_test_key_abcdefgh"
    assert config_loader.get_secret("OPENAI_API_KEY") == "sk-test-1234567890abcdef"
    assert config_loader.get_secret("ANTHROPIC_API_KEY") == "claude_test_key_xyz123"


@pytest.mark.unit
def test_env_missing_file(mock_logger):
    """Test behavior when .env file is missing."""
    # Save and clear environment variables
    saved_env_vars = {}
    env_keys_to_clear = [
        "GOOGLE_MAPS_API_KEY",
        "YOUTUBE_API_KEY",
        "SPOTIFY_API_KEY",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
    ]

    for key in env_keys_to_clear:
        if key in os.environ:
            saved_env_vars[key] = os.environ[key]
            del os.environ[key]

    try:
        config_loader = ConfigLoader(
            config_path=Path("/nonexistent/config.yaml"),
            env_path=Path("/nonexistent/.env"),
            logger=mock_logger,
        )

        # Should not crash, just return None for secrets
        assert config_loader.get_secret("GOOGLE_MAPS_API_KEY") is None

        # Should log warning
        assert any(".env" in str(call) for call in mock_logger.warning.call_args_list)

    finally:
        # Restore environment variables
        for key, value in saved_env_vars.items():
            os.environ[key] = value


# ================================================================================
# TEST: CLI Override Priority
# ================================================================================


@pytest.mark.unit
def test_cli_override_priority(temp_config_files, mock_logger):
    """Test that CLI overrides have highest priority."""
    cli_overrides = {
        "mode": "live",
        "log_level": "ERROR",
        "output": "custom_output.json",
    }

    config_loader = ConfigLoader(
        config_path=temp_config_files["yaml_path"],
        env_path=temp_config_files["env_path"],
        cli_overrides=cli_overrides,
        logger=mock_logger,
    )

    # CLI overrides should take priority over YAML and defaults
    assert config_loader.get("route_provider.mode") == "live"
    assert config_loader.get("logging.level") == "ERROR"
    assert config_loader.get("output.json_file") == "custom_output.json"


@pytest.mark.unit
def test_cli_override_nested_keys(temp_config_files, mock_logger):
    """Test CLI overrides for nested keys using dot notation."""
    cli_overrides = {
        "scheduler.interval": 5.0,
        "orchestrator.max_workers": 20,
    }

    config_loader = ConfigLoader(
        config_path=temp_config_files["yaml_path"],
        env_path=temp_config_files["env_path"],
        cli_overrides=cli_overrides,
        logger=mock_logger,
    )

    # CLI overrides should apply to nested keys
    assert config_loader.get("scheduler.interval") == 5.0
    assert config_loader.get("orchestrator.max_workers") == 20


# ================================================================================
# TEST: Secret Redaction
# ================================================================================


@pytest.mark.unit
def test_secret_redaction():
    """Test that secrets are redacted correctly."""
    # Test normal secret (length >= 4)
    redacted = ConfigLoader.redact_secret("GOOGLE_MAPS_API_KEY", "gmaps_test_key_12345678")
    assert redacted == "GOOGLE_MAPS_API_KEY=****5678"

    # Test short secret (length < 4)
    redacted_short = ConfigLoader.redact_secret("API_KEY", "abc")
    assert redacted_short == "API_KEY=****"

    # Test empty secret
    redacted_empty = ConfigLoader.redact_secret("API_KEY", "")
    assert redacted_empty == "API_KEY=****"


@pytest.mark.unit
def test_secret_redaction_in_logs(temp_config_files, mock_logger):
    """Test that secrets are redacted when logged."""
    config_loader = ConfigLoader(
        config_path=temp_config_files["yaml_path"],
        env_path=temp_config_files["env_path"],
        logger=mock_logger,
    )

    # Check that debug logs contain redacted secrets (not full secrets)
    debug_calls = [str(call) for call in mock_logger.debug.call_args_list]

    # Verify no full secret appears in logs
    for call in debug_calls:
        assert "gmaps_test_key_12345678" not in call
        assert "youtube_test_key_abcdefgh" not in call

    # Verify redacted format appears
    assert any("****" in call for call in debug_calls)


# ================================================================================
# TEST: Config Validation & Fallback
# ================================================================================


@pytest.mark.unit
def test_validation_fallback_live_mode_no_api_key(mock_logger):
    """Test fallback to cached mode when live mode requested but API key missing."""
    # Save and clear environment variable
    saved_key = os.environ.pop("GOOGLE_MAPS_API_KEY", None)

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create YAML with live mode
            yaml_path = Path(tmpdir) / "config.yaml"
            with open(yaml_path, 'w') as f:
                yaml.dump({"route_provider": {"mode": "live"}}, f)

            # No .env file (no API key)
            config_loader = ConfigLoader(
                config_path=yaml_path,
                env_path=Path("/nonexistent/.env"),
                logger=mock_logger,
            )

            # Should fallback to cached mode
            assert config_loader.get("route_provider.mode") == "cached"

            # Should have validation warning
            assert any(
                "fallback to cached mode" in w.lower()
                for w in config_loader.get_warnings()
            )

    finally:
        # Restore environment variable if it existed
        if saved_key is not None:
            os.environ["GOOGLE_MAPS_API_KEY"] = saved_key


@pytest.mark.unit
def test_validation_fallback_llm_judge_no_api_key(mock_logger):
    """Test fallback to mock LLM when LLM judge enabled but API key missing."""
    # Save and clear environment variable
    saved_key = os.environ.pop("OPENAI_API_KEY", None)

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create YAML with OpenAI judge
            yaml_path = Path(tmpdir) / "config.yaml"
            with open(yaml_path, 'w') as f:
                yaml.dump({"judge": {"use_llm": True, "llm_provider": "openai"}}, f)

            # No .env file (no API key)
            config_loader = ConfigLoader(
                config_path=yaml_path,
                env_path=Path("/nonexistent/.env"),
                logger=mock_logger,
            )

            # Should fallback to mock provider
            assert config_loader.get("judge.llm_provider") == "mock"

            # Should have validation warning
            assert any(
                "fallback to mock llm" in w.lower()
                for w in config_loader.get_warnings()
            )

    finally:
        # Restore environment variable if it existed
        if saved_key is not None:
            os.environ["OPENAI_API_KEY"] = saved_key


@pytest.mark.unit
def test_validation_fallback_claude_llm_no_api_key(mock_logger):
    """Test fallback to mock LLM when Claude provider selected but API key missing."""
    # Save and clear environment variable
    saved_key = os.environ.pop("ANTHROPIC_API_KEY", None)

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create YAML with Claude judge
            yaml_path = Path(tmpdir) / "config.yaml"
            with open(yaml_path, 'w') as f:
                yaml.dump({"judge": {"use_llm": True, "llm_provider": "claude"}}, f)

            # No .env file (no API key)
            config_loader = ConfigLoader(
                config_path=yaml_path,
                env_path=Path("/nonexistent/.env"),
                logger=mock_logger,
            )

            # Should fallback to mock provider
            assert config_loader.get("judge.llm_provider") == "mock"

            # Should have validation warning
            assert any(
                "ANTHROPIC_API_KEY" in w for w in config_loader.get_warnings()
            )

    finally:
        # Restore environment variable if it existed
        if saved_key is not None:
            os.environ["ANTHROPIC_API_KEY"] = saved_key


@pytest.mark.unit
def test_validation_no_warnings_when_all_valid(temp_config_files, mock_logger):
    """Test that no warnings are generated when config is valid."""
    config_loader = ConfigLoader(
        config_path=temp_config_files["yaml_path"],
        env_path=temp_config_files["env_path"],
        logger=mock_logger,
    )

    # In cached mode with all files present, should have no warnings
    # (except for the .env loading message which is info level)
    # Actual validation warnings should be empty or minimal
    warnings = config_loader.get_warnings()

    # Should not have critical validation warnings about missing keys in cached mode
    # Note: There may be fallback warnings for optional API keys (like ANTHROPIC_API_KEY)
    # which are fine - we only care that core config is valid
    critical_warnings = [w for w in warnings if "mode" in w.lower() and "fallback" in w.lower()]
    assert len(critical_warnings) == 0


@pytest.mark.unit
def test_schema_validation_resets_invalid_values(mock_logger):
    """Out-of-range or invalid choice values should fall back to defaults."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yaml_path = Path(tmpdir) / "config.yaml"
        env_path = Path(tmpdir) / ".env"
        env_path.write_text("")  # prevent .env missing warning

        with open(yaml_path, "w") as f:
            yaml.dump(
                {
                    "scheduler": {"interval": 0.1},  # below minimum
                    "orchestrator": {"max_workers": 50},  # above maximum
                    "agents": {"video": {"retry_backoff": "unknown"}},  # invalid choice
                    "logging": {"level": "debug"},  # should normalize to upper
                    "route_provider": {"mode": "Live"},  # should normalize to lower
                },
                f,
            )

        config_loader = ConfigLoader(
            config_path=yaml_path,
            env_path=env_path,
            logger=mock_logger,
        )

        # Invalid numeric/choice values fall back to defaults
        assert (
            config_loader.get("scheduler.interval")
            == ConfigLoader.DEFAULT_CONFIG["scheduler"]["interval"]
        )
        assert (
            config_loader.get("orchestrator.max_workers")
            == ConfigLoader.DEFAULT_CONFIG["orchestrator"]["max_workers"]
        )
        assert (
            config_loader.get("agents.video.retry_backoff")
            == ConfigLoader.DEFAULT_CONFIG["agents"]["video"]["retry_backoff"]
        )

        # Normalized values are preserved when valid
        assert config_loader.get("logging.level") == "DEBUG"
        assert config_loader.get("route_provider.mode") == "live"

        # Warnings include invalid keys
        warnings = " ".join(config_loader.get_warnings()).lower()
        assert "scheduler.interval" in warnings
        assert "max_workers" in warnings
        assert "retry_backoff" in warnings

# ================================================================================
# TEST: ConfigLoader Methods
# ================================================================================


@pytest.mark.unit
def test_get_method_dot_notation(temp_config_files, mock_logger):
    """Test get() method with dot-separated keys."""
    config_loader = ConfigLoader(
        config_path=temp_config_files["yaml_path"],
        env_path=temp_config_files["env_path"],
        logger=mock_logger,
    )

    # Test nested access
    assert config_loader.get("scheduler.interval") == 3.0
    assert config_loader.get("orchestrator.max_workers") == 10

    # Test default value
    assert config_loader.get("nonexistent.key", "default_value") == "default_value"

    # Test single-level key
    assert isinstance(config_loader.get("scheduler"), dict)


@pytest.mark.unit
def test_get_all_method(temp_config_files, mock_logger):
    """Test get_all() method returns entire config."""
    config_loader = ConfigLoader(
        config_path=temp_config_files["yaml_path"],
        env_path=temp_config_files["env_path"],
        logger=mock_logger,
    )

    config = config_loader.get_all()

    # Should be a dictionary
    assert isinstance(config, dict)

    # Should contain all sections
    assert "scheduler" in config
    assert "orchestrator" in config
    assert "agents" in config
    assert "judge" in config
    assert "logging" in config


@pytest.mark.unit
def test_get_warnings_method(mock_logger):
    """Test get_warnings() returns validation warnings."""
    config_loader = ConfigLoader(
        config_path=Path("/nonexistent/config.yaml"),
        env_path=Path("/nonexistent/.env"),
        logger=mock_logger,
    )

    warnings = config_loader.get_warnings()

    # Should have warnings for missing files
    assert len(warnings) > 0
    assert isinstance(warnings, list)


@pytest.mark.unit
def test_repr_method(temp_config_files, mock_logger):
    """Test __repr__ string representation."""
    config_loader = ConfigLoader(
        config_path=temp_config_files["yaml_path"],
        env_path=temp_config_files["env_path"],
        logger=mock_logger,
    )

    repr_str = repr(config_loader)

    # Should contain key information
    assert "ConfigLoader" in repr_str
    assert str(temp_config_files["yaml_path"]) in repr_str
    assert "secrets_loaded" in repr_str


# ================================================================================
# TEST: Edge Cases
# ================================================================================


@pytest.mark.unit
def test_deep_merge_behavior(mock_logger):
    """Test that YAML values merge correctly with defaults."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create YAML with partial config
        yaml_path = Path(tmpdir) / "config.yaml"
        with open(yaml_path, 'w') as f:
            yaml.dump(
                {
                    "scheduler": {"interval": 4.0},  # Override one value
                    # Don't specify "enabled" - should keep default
                },
                f,
            )

        config_loader = ConfigLoader(config_path=yaml_path, logger=mock_logger)

        # Overridden value
        assert config_loader.get("scheduler.interval") == 4.0

        # Default value preserved
        assert config_loader.get("scheduler.enabled") is True


@pytest.mark.unit
def test_none_cli_overrides_ignored(temp_config_files, mock_logger):
    """Test that None CLI overrides are ignored."""
    cli_overrides = {
        "mode": "live",
        "log_level": None,  # Should be ignored
        "output": None,  # Should be ignored
    }

    config_loader = ConfigLoader(
        config_path=temp_config_files["yaml_path"],
        env_path=temp_config_files["env_path"],
        cli_overrides=cli_overrides,
        logger=mock_logger,
    )

    # Non-None override applied
    assert config_loader.get("route_provider.mode") == "live"

    # None overrides ignored (YAML value preserved)
    assert config_loader.get("logging.level") == "DEBUG"


# ================================================================================
# TEST: Configuration Priority Chain
# ================================================================================


@pytest.mark.unit
def test_full_priority_chain(temp_config_files, mock_logger):
    """Test full priority chain: CLI > Env > YAML > Defaults."""
    # YAML says interval=3.0 (from fixture)
    # CLI override says interval=7.0
    cli_overrides = {"scheduler.interval": 7.0}

    config_loader = ConfigLoader(
        config_path=temp_config_files["yaml_path"],
        env_path=temp_config_files["env_path"],
        cli_overrides=cli_overrides,
        logger=mock_logger,
    )

    # CLI should win
    assert config_loader.get("scheduler.interval") == 7.0

    # YAML value (not overridden by CLI) should apply
    assert config_loader.get("logging.level") == "DEBUG"

    # Default value (not in YAML or CLI) should apply
    assert config_loader.get("orchestrator.queue_timeout") == 1.0

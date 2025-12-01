"""
Configuration & Security Layer - ConfigLoader

Mission M3: Centralized config loader with YAML, CLI overrides, .env secrets, and validation.

Features:
- YAML configuration file parsing
- .env secret loading with redaction
- CLI argument override priority
- Config validation with fallback to cached/mock mode
- Secret masking in logs (****...last4chars)
"""

import os
import re
import yaml
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from importlib import resources
from dotenv import load_dotenv


class ConfigLoader:
    """
    Centralized configuration loader with multi-source priority.

    Priority (highest to lowest):
    1. CLI arguments (passed via override_dict)
    2. Environment variables (.env file)
    3. YAML configuration file (CWD config/settings.yaml or packaged default)
    4. Hardcoded defaults
    """

    # Default configuration (fallback)
    DEFAULT_CONFIG = {
        "scheduler": {
            "interval": 2.0,
            "enabled": True,
        },
        "orchestrator": {
            "max_workers": 5,
            "queue_timeout": 1.0,
            "shutdown_timeout": 30.0,
        },
        "agents": {
            "video": {"name": "VideoAgent", "enabled": True, "search_limit": 3, "timeout": 10.0, "retry_attempts": 3, "retry_backoff": "exponential"},
            "song": {"name": "SongAgent", "enabled": True, "search_limit": 3, "timeout": 10.0, "retry_attempts": 3, "retry_backoff": "exponential"},
            "knowledge": {"name": "KnowledgeAgent", "enabled": True, "search_limit": 3, "timeout": 10.0, "retry_attempts": 3, "retry_backoff": "exponential"},
        },
        "judge": {
            "scoring_mode": "heuristic",
            "use_llm": False,
            "llm_provider": "mock",
            "llm_timeout": 30.0,
            "llm_fallback": True,
        },
        "logging": {
            "level": "INFO",
            "file": "logs/system.log",
            "error_file": "logs/errors.log",
            "max_file_size_mb": 10,
            "backup_count": 5,
            "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(event_tag)s | %(message)s",
            "console_enabled": True,
        },
        "output": {
            "json_file": "output/final_route.json",
            "markdown_file": "output/summary.md",
            "csv_file": "output/tour_export.csv",
            "checkpoint_dir": "output/checkpoints",
            "checkpoints_enabled": True,
            "checkpoint_retention_days": 7,
        },
        "route_provider": {
            "mode": "cached",
            "cache_dir": "data/routes",
            "api_retry_attempts": 3,
            "api_timeout": 20.0,
        },
        "circuit_breaker": {
            "enabled": True,
            "failure_threshold": 5,
            "timeout": 60.0,
        },
        "metrics": {
            "enabled": True,
            "file": "logs/metrics.json",
            "update_interval": 5.0,
        },
    }

    # Validation schema (type, bounds, and choices) derived from settings.yaml comments
    SCHEMA_RULES: Dict[str, Dict[str, Any]] = {
        "scheduler.interval": {"type": (int, float), "min": 0.5, "max": 10.0},
        "scheduler.enabled": {"type": bool},
        "orchestrator.max_workers": {"type": int, "min": 1, "max": 20},
        "orchestrator.queue_timeout": {"type": (int, float), "min": 0.1, "max": 5.0},
        "orchestrator.shutdown_timeout": {"type": (int, float), "min": 5.0, "max": 120.0},
        "agents.video.search_limit": {"type": int, "min": 1, "max": 10},
        "agents.video.timeout": {"type": (int, float), "min": 5.0, "max": 30.0},
        "agents.video.retry_attempts": {"type": int, "min": 1, "max": 5},
        "agents.video.retry_backoff": {"type": str, "choices": ["exponential", "linear"], "normalize": "lower"},
        "agents.song.search_limit": {"type": int, "min": 1, "max": 10},
        "agents.song.timeout": {"type": (int, float), "min": 5.0, "max": 30.0},
        "agents.song.retry_attempts": {"type": int, "min": 1, "max": 5},
        "agents.song.retry_backoff": {"type": str, "choices": ["exponential", "linear"], "normalize": "lower"},
        "agents.knowledge.search_limit": {"type": int, "min": 1, "max": 10},
        "agents.knowledge.timeout": {"type": (int, float), "min": 5.0, "max": 30.0},
        "agents.knowledge.retry_attempts": {"type": int, "min": 1, "max": 5},
        "agents.knowledge.retry_backoff": {"type": str, "choices": ["exponential", "linear"], "normalize": "lower"},
        "judge.scoring_mode": {"type": str, "choices": ["heuristic", "llm", "hybrid"], "normalize": "lower"},
        "judge.use_llm": {"type": bool},
        "judge.llm_provider": {"type": str, "choices": ["ollama", "openai", "claude", "gemini", "mock", "auto"], "normalize": "lower"},
        "judge.llm_timeout": {"type": (int, float), "min": 10.0, "max": 60.0},
        "agents.llm_provider": {"type": str, "choices": ["ollama", "openai", "claude", "gemini", "mock", "auto"], "normalize": "lower"},
        "logging.level": {"type": str, "choices": ["DEBUG", "INFO", "WARNING", "ERROR"], "normalize": "upper"},
        "output.checkpoint_retention_days": {"type": int, "min": 0, "max": 30},
        "route_provider.mode": {"type": str, "choices": ["live", "cached"], "normalize": "lower"},
        "route_provider.api_retry_attempts": {"type": int, "min": 1, "max": 5},
        "route_provider.api_timeout": {"type": (int, float), "min": 5.0, "max": 30.0},
        "circuit_breaker.failure_threshold": {"type": int, "min": 3, "max": 10},
        "circuit_breaker.timeout": {"type": (int, float), "min": 30.0, "max": 300.0},
        "metrics.update_interval": {"type": (int, float), "min": 1.0, "max": 30.0},
    }

    # Secret keys that should be redacted in logs
    SECRET_KEYS = [
        "GOOGLE_MAPS_API_KEY",
        "YOUTUBE_API_KEY",
        "SPOTIFY_API_KEY",
        "SPOTIFY_CLIENT_ID",
        "SPOTIFY_CLIENT_SECRET",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GEMINI_API_KEY",
        "api_key",
        "secret",
        "password",
        "token",
    ]

    def __init__(
        self,
        config_path: Optional[Path] = None,
        env_path: Optional[Path] = None,
        cli_overrides: Optional[Dict[str, Any]] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize ConfigLoader.

        Args:
            config_path: Path to YAML config file (default: config/settings.yaml)
            env_path: Path to .env file (default: .env)
            cli_overrides: Dictionary of CLI argument overrides
            logger: Logger instance for config loading events
        """
        self.config_path = config_path or Path("config/settings.yaml")
        self.env_path = env_path or Path(".env")
        self.cli_overrides = cli_overrides or {}
        self.logger = logger or logging.getLogger(__name__)

        self.config: Dict[str, Any] = {}
        self.secrets: Dict[str, str] = {}
        self.validation_warnings: list[str] = []

        # Load configuration from all sources
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from all sources with priority."""
        # Start with defaults
        self.config = self._deep_copy_dict(self.DEFAULT_CONFIG)

        # Load YAML config file
        self._load_yaml()

        # Load .env secrets
        self._load_env()

        # Apply CLI overrides
        self._apply_cli_overrides()

        # Validate configuration
        self._validate_config()

    def _load_yaml(self) -> None:
        """Load YAML configuration file."""
        config_file_path = self.config_path

        # If explicit path not found, try finding the packaged default
        if not config_file_path.exists():
            try:
                # Try to find 'settings.yaml' inside 'hw4_tourguide.config' package
                with resources.path("hw4_tourguide.config", "settings.yaml") as packaged_path:
                    if packaged_path.exists():
                        self.logger.info(f"Local config not found. Using packaged default: {packaged_path}")
                        config_file_path = packaged_path
            except Exception:
                pass

        if not config_file_path.exists():
            self.logger.warning(
                f"Config file not found: {self.config_path} (and no packaged default). Using defaults."
            )
            self.validation_warnings.append(f"Config file missing: {self.config_path}")
            return

        try:
            with open(config_file_path, 'r') as f:
                yaml_config = yaml.safe_load(f)

            if yaml_config:
                self._deep_merge(self.config, yaml_config)
                self.logger.info(f"Loaded config from: {config_file_path}")
            else:
                self.logger.warning(f"Empty config file: {config_file_path}")

        except yaml.YAMLError as e:
            self.logger.error(f"YAML parse error in {config_file_path}: {e}")
            self.validation_warnings.append(f"YAML parse error: {e}")
        except Exception as e:
            self.logger.error(f"Failed to load config file {config_file_path}: {e}")
            self.validation_warnings.append(f"Config load error: {e}")

    def _load_env(self) -> None:
        """Load .env file and extract secrets."""
        if self.env_path.exists():
            load_dotenv(dotenv_path=self.env_path, override=True)
            self.logger.info(f"Loaded .env from: {self.env_path}")
        else:
            self.logger.warning(
                f".env file not found: {self.env_path}. API calls may fail."
            )
            self.validation_warnings.append(f".env file missing: {self.env_path}")

        # Extract secrets from environment
        for key in self.SECRET_KEYS:
            value = os.getenv(key)
            if value:
                self.secrets[key] = value
                self.logger.debug(f"Loaded secret: {self._redact_secret(key, value)}")

    def _apply_cli_overrides(self) -> None:
        """Apply CLI argument overrides to config."""
        if not self.cli_overrides:
            return

        for key, value in self.cli_overrides.items():
            if value is not None:
                # Map CLI args to config structure
                if key == "mode":
                    self.config["route_provider"]["mode"] = value
                elif key == "log_level":
                    self.config["logging"]["level"] = value
                elif key == "output":
                    self.config["output"]["json_file"] = value
                else:
                    # For nested keys like "scheduler.interval", split and set
                    self._set_nested(self.config, key, value)

        if self.cli_overrides:
            self.logger.info(f"Applied CLI overrides: {len(self.cli_overrides)} args")

    def _validate_config(self) -> None:
        """
        Validate configuration and apply fallback strategies.

        If required API keys are missing, fallback to cached/mock mode.
        """
        # Check for required API keys based on mode
        mode = self.config.get("route_provider", {}).get("mode", "cached")

        if mode == "live":
            # Live mode requires Google Maps API key
            if not self.secrets.get("GOOGLE_MAPS_API_KEY"):
                self.logger.warning(
                    "GOOGLE_MAPS_API_KEY missing. Falling back to cached mode."
                )
                self.config["route_provider"]["mode"] = "cached"
                self.validation_warnings.append(
                    "Missing GOOGLE_MAPS_API_KEY: fallback to cached mode"
                )

        # Check for LLM judge requirements
        if self.config.get("judge", {}).get("use_llm", False):
            llm_provider = self.config["judge"]["llm_provider"]

            if llm_provider == "openai" and not self.secrets.get("OPENAI_API_KEY"):
                self.logger.warning(
                    "OPENAI_API_KEY missing. Falling back to mock LLM provider."
                )
                self.config["judge"]["llm_provider"] = "mock"
                self.validation_warnings.append(
                    "Missing OPENAI_API_KEY: fallback to mock LLM"
                )

            elif llm_provider == "claude" and not self.secrets.get("ANTHROPIC_API_KEY"):
                self.logger.warning(
                    "ANTHROPIC_API_KEY missing. Falling back to mock LLM provider."
                )
                self.config["judge"]["llm_provider"] = "mock"
                self.validation_warnings.append(
                    "Missing ANTHROPIC_API_KEY: fallback to mock LLM"
                )

        # Enforce schema ranges/types/choices (falls back to defaults on violation)
        self._validate_schema_rules()

        # Log validation summary
        if self.validation_warnings:
            self.logger.warning(
                f"Config validation warnings: {len(self.validation_warnings)}"
            )
            for warning in self.validation_warnings:
                self.logger.warning(f"  - {warning}")
        else:
            self.logger.info("Config validation passed with no warnings")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key path.

        Args:
            key: Dot-separated key path (e.g., "scheduler.interval")
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_secret(self, key: str) -> Optional[str]:
        """
        Get secret value by key.

        Args:
            key: Secret key name (e.g., "GOOGLE_MAPS_API_KEY")

        Returns:
            Secret value or None if not found
        """
        return self.secrets.get(key)

    def get_all(self) -> Dict[str, Any]:
        """Get entire configuration dictionary."""
        return self.config

    def get_warnings(self) -> list[str]:
        """Get list of validation warnings."""
        return self.validation_warnings

    @staticmethod
    def redact_secret(key: str, value: str) -> str:
        """
        Redact secret for safe logging.

        Args:
            key: Secret key name
            value: Secret value

        Returns:
            Redacted string: "KEY=****...last4chars"
        """
        if not value or len(value) < 4:
            return f"{key}=****"

        return f"{key}=****{value[-4:]}"

    def _redact_secret(self, key: str, value: str) -> str:
        """Instance method wrapper for redact_secret."""
        return self.redact_secret(key, value)

    @staticmethod
    def _deep_copy_dict(d: Dict[str, Any]) -> Dict[str, Any]:
        """Deep copy a dictionary."""
        result = {}
        for key, value in d.items():
            if isinstance(value, dict):
                result[key] = ConfigLoader._deep_copy_dict(value)
            else:
                result[key] = value
        return result

    @staticmethod
    def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """
        Deep merge override dict into base dict (modifies base in place).

        Args:
            base: Base dictionary (modified in place)
            override: Override dictionary
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                ConfigLoader._deep_merge(base[key], value)
            else:
                base[key] = value

    @staticmethod
    def _set_nested(d: Dict[str, Any], key: str, value: Any) -> None:
        """
        Set nested dictionary value using dot-separated key path.

        Args:
            d: Dictionary to modify
            key: Dot-separated key path (e.g., "scheduler.interval")
            value: Value to set
        """
        keys = key.split(".")
        for k in keys[:-1]:
            if k not in d:
                d[k] = {}
            d = d[k]
        d[keys[-1]] = value

    def _get_default_value(self, key: str) -> Any:
        """Retrieve default value for a dot-separated key path."""
        keys = key.split(".")
        value: Any = self.DEFAULT_CONFIG
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None
        return value

    def _validate_schema_rules(self) -> None:
        """Validate config against SCHEMA_RULES and reset invalid values to defaults."""
        for key, rule in self.SCHEMA_RULES.items():
            current_value = self.get(key)
            default_value = self._get_default_value(key)
            normalized_value = self._normalize_value(current_value, rule)

            if not self._is_value_valid(normalized_value, rule):
                self.validation_warnings.append(
                    f"Invalid value for {key}: {current_value} (fallback to default {default_value})"
                )
                self._set_nested(self.config, key, default_value)
            else:
                # Write back normalized value (e.g., upper/lower casing)
                self._set_nested(self.config, key, normalized_value)

    @staticmethod
    def _normalize_value(value: Any, rule: Dict[str, Any]) -> Any:
        """Normalize string casing according to schema rule."""
        if value is None:
            return value

        normalize = rule.get("normalize")
        if normalize == "upper" and isinstance(value, str):
            return value.upper()
        if normalize == "lower" and isinstance(value, str):
            return value.lower()
        return value

    @staticmethod
    def _is_value_valid(value: Any, rule: Dict[str, Any]) -> bool:
        """Check value against type, bounds, and choice constraints."""
        expected_type: Tuple[type, ...] = rule.get("type", tuple())

        if expected_type and not isinstance(value, expected_type):
            return False

        if "choices" in rule and value not in rule["choices"]:
            return False

        if isinstance(value, (int, float)):
            min_val = rule.get("min")
            max_val = rule.get("max")
            if min_val is not None and value < min_val:
                return False
            if max_val is not None and value > max_val:
                return False

        return True

    def __repr__(self) -> str:
        """String representation of ConfigLoader."""
        return (
            f"ConfigLoader(config_path={self.config_path}, "
            f"secrets_loaded={len(self.secrets)}, "
            f"warnings={len(self.validation_warnings)})"
        )

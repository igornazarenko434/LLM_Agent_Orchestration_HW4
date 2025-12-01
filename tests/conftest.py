"""
Pytest configuration and shared fixtures (Mission M4.1).

Provides reusable config, logger, and sample route data to keep tests
focused on behavior rather than boilerplate setup.
"""

import json
import logging
import tempfile
from pathlib import Path
from typing import Dict, Any

import pytest

from hw4_tourguide.config_loader import ConfigLoader
from hw4_tourguide.logger import setup_logging, get_logger


@pytest.fixture(scope="session")
def temp_dirs(tmp_path_factory: pytest.TempPathFactory) -> Dict[str, Path]:
    """Session-wide temporary directories for logs/output/config."""
    base = tmp_path_factory.mktemp("hw4_tourguide")
    return {
        "base": base,
        "logs": base / "logs",
        "output": base / "output",
        "config": base / "config",
        "data": base / "data",
    }


@pytest.fixture
def sample_route() -> Dict[str, Any]:
    """Minimal stub route data for orchestrator/agent tests."""
    return {
        "transaction_id": "test_tid_123",
        "steps": [
            {"step_number": 1, "location_name": "Start", "coordinates": {"lat": 0, "lng": 0}, "instructions": "Head north"},
            {"step_number": 2, "location_name": "End", "coordinates": {"lat": 1, "lng": 1}, "instructions": "Arrive"},
        ],
        "metadata": {"distance": "1 km", "duration": "2 mins"},
    }


@pytest.fixture
def sample_config_file(temp_dirs: Dict[str, Path]) -> Path:
    """Write a minimal settings.yaml to a temp location."""
    config_path = temp_dirs["config"] / "settings.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_content = {
        "scheduler": {"interval": 2.0, "enabled": True},
        "orchestrator": {"max_workers": 2, "queue_timeout": 0.5, "shutdown_timeout": 5.0},
        "logging": {"level": "DEBUG", "file": str(temp_dirs["logs"] / "system.log"), "error_file": str(temp_dirs["logs"] / "errors.log"), "console_enabled": False},
        "output": {"json_file": str(temp_dirs["output"] / "final.json"), "checkpoints_enabled": False},
    }
    temp_dirs["logs"].mkdir(parents=True, exist_ok=True)
    temp_dirs["output"].mkdir(parents=True, exist_ok=True)
    import yaml
    config_path.write_text(yaml.dump(config_content))
    return config_path


@pytest.fixture
def configured_logger(temp_dirs: Dict[str, Path]) -> logging.Logger:
    """Set up logging to temporary files for tests."""
    config = {
        "level": "INFO",
        "file": temp_dirs["logs"] / "system.log",
        "error_file": temp_dirs["logs"] / "errors.log",
        "max_file_size_mb": 1,
        "backup_count": 2,
        "format": "%(levelname)s | %(name)s | %(event_tag)s | %(message)s",
        "console_enabled": False,
    }
    return setup_logging(config)


@pytest.fixture
def config_loader(sample_config_file: Path, configured_logger: logging.Logger) -> ConfigLoader:
    """ConfigLoader bound to the temporary settings and logger."""
    return ConfigLoader(config_path=sample_config_file, logger=configured_logger)


@pytest.fixture
def tmp_json_file() -> Path:
    """Create a temporary JSON file helper."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        path = Path(f.name)
    yield path
    try:
        path.unlink()
    except FileNotFoundError:
        pass


@pytest.fixture
def write_json(tmp_json_file: Path):
    """Helper to write JSON content to a temporary file."""
    def _writer(payload: Dict[str, Any]) -> Path:
        tmp_json_file.write_text(json.dumps(payload))
        return tmp_json_file
    return _writer


# Marker shortcuts
def pytest_configure(config):
    config.addinivalue_line("markers", "unit: Unit tests (fast, isolated)")
    config.addinivalue_line("markers", "integration: Integration tests (slower, multiple components)")
    config.addinivalue_line("markers", "concurrency: Concurrency and threading tests")
    config.addinivalue_line("markers", "resilience: Resilience and retry logic tests")

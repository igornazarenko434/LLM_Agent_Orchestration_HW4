"""
Tests for logging infrastructure (Mission M3.2).
"""

import logging
import pytest
from pathlib import Path
from hw4_tourguide.logger import setup_logging, get_logger


@pytest.mark.unit
def test_logging_writes_event_tags(tmp_path: Path):
    log_dir = tmp_path / "logs"
    config = {
        "level": "INFO",
        "file": log_dir / "system.log",
        "error_file": log_dir / "errors.log",
        "max_file_size_mb": 1,
        "backup_count": 2,
        "format": "%(levelname)s | %(name)s | %(event_tag)s | %(message)s",
        "console_enabled": False,
    }

    setup_logging(config)
    logger = get_logger("test")
    adapter = logging.LoggerAdapter(logger, extra={"event_tag": "Scheduler"})
    adapter.info("hello world")

    # Event tag should be present in system log
    contents = (log_dir / "system.log").read_text()
    assert "Scheduler" in contents
    assert "hello world" in contents


@pytest.mark.unit
def test_error_handler_captures_only_errors(tmp_path: Path):
    log_dir = tmp_path / "logs"
    config = {
        "level": "INFO",
        "file": log_dir / "system.log",
        "error_file": log_dir / "errors.log",
        "max_file_size_mb": 1,
        "backup_count": 2,
        "format": "%(levelname)s | %(name)s | %(event_tag)s | %(message)s",
        "console_enabled": False,
    }

    setup_logging(config)
    logger = get_logger("test")
    adapter = logging.LoggerAdapter(logger, extra={"event_tag": "Error"})

    adapter.error("boom")
    adapter.info("info message")

    system_text = (log_dir / "system.log").read_text()
    error_text = (log_dir / "errors.log").read_text()

    assert "boom" in system_text
    assert "boom" in error_text  # error handler captures errors
    assert "info message" in system_text
    assert "info message" not in error_text  # error handler should not contain INFO


@pytest.mark.unit
def test_default_event_tag_when_missing(tmp_path: Path):
    log_dir = tmp_path / "logs"
    config = {
        "level": "INFO",
        "file": log_dir / "system.log",
        "error_file": log_dir / "errors.log",
        "max_file_size_mb": 1,
        "backup_count": 2,
        "format": "%(levelname)s | %(name)s | %(event_tag)s | %(message)s",
        "console_enabled": False,
    }

    setup_logging(config)
    logger = get_logger("test_no_extra")
    logger.info("no tag provided")

    system_text = (log_dir / "system.log").read_text()
    assert "no tag provided" in system_text
    # Default event tag should appear
    assert "General" in system_text

"""
Sample integration-style test to exercise shared fixtures (Mission M4.1).
"""

import logging
import pytest

from hw4_tourguide.logger import get_logger


@pytest.mark.unit
def test_logger_fixture_sets_event_tag(configured_logger: logging.Logger):
    adapter = logging.LoggerAdapter(get_logger("sample"), extra={"event_tag": "Test"})
    adapter.info("framework smoke")

    # Verify log file written by configured_logger fixture
    handlers = configured_logger.handlers
    assert handlers, "Logger should have handlers configured"
    log_paths = [h.baseFilename for h in handlers if hasattr(h, "baseFilename")]
    assert log_paths, "Handlers should write to files"

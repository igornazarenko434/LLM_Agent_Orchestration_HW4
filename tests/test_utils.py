"""
Utility-focused tests for helper methods embedded in ConfigLoader (Mission M4.2).
Even though helpers are internal, we verify behavior to lock in config semantics.
"""

import pytest
from hw4_tourguide.config_loader import ConfigLoader


@pytest.mark.unit
def test_set_nested_creates_missing_parents():
    data = {}
    ConfigLoader._set_nested(data, "a.b.c", 123)
    assert data == {"a": {"b": {"c": 123}}}


@pytest.mark.unit
def test_deep_merge_preserves_and_overrides():
    base = {"x": {"y": 1}, "k": 2}
    override = {"x": {"z": 3}, "k": 5}
    ConfigLoader._deep_merge(base, override)
    assert base["x"]["y"] == 1  # preserved
    assert base["x"]["z"] == 3  # added
    assert base["k"] == 5       # overridden


@pytest.mark.unit
def test_get_default_value_reads_nested_defaults():
    loader = ConfigLoader()
    assert loader._get_default_value("scheduler.interval") == 2.0
    assert loader._get_default_value("logging.level") == "INFO"

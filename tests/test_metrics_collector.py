import json
import time
from pathlib import Path
import pytest

from hw4_tourguide.tools.metrics_collector import MetricsCollector


@pytest.mark.unit
def test_metrics_collector_records_and_flushes(tmp_path):
    MetricsCollector.reset()
    path = tmp_path / "metrics.json"
    m = MetricsCollector(path=str(path), update_interval=0.1)
    m.increment_counter("api_calls.youtube", 2)
    m.record_latency("agent.video.search_ms", 100.0)
    m.record_latency("agent.video.search_ms", 200.0)
    m.set_gauge("queue.depth", 3)
    m.flush()

    data = json.loads(path.read_text())
    assert data["counters"]["api_calls.youtube"] == 2
    assert data["latencies"]["agent.video.search_ms"]["avg"] == 150.0
    assert data["gauges"]["queue.depth"] == 3


@pytest.mark.unit
def test_metrics_collector_auto_flush(tmp_path):
    MetricsCollector.reset()
    path = tmp_path / "metrics_auto.json"
    m = MetricsCollector(path=str(path), update_interval=0.1)
    m.increment_counter("api_calls.spotify", 1)
    time.sleep(0.3)
    m.stop()
    data = json.loads(path.read_text())
    assert data["counters"]["api_calls.spotify"] == 1

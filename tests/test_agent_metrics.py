import json
from pathlib import Path
import pytest

from hw4_tourguide.agents.video_agent import VideoAgent
from hw4_tourguide.agents.song_agent import SongAgent
from hw4_tourguide.agents.knowledge_agent import KnowledgeAgent
from hw4_tourguide.file_interface import CheckpointWriter
from hw4_tourguide.tools.metrics_collector import MetricsCollector
from hw4_tourguide.tools.circuit_breaker import CircuitBreaker


class StubClient:
    def __init__(self, prefix: str):
        self.prefix = prefix
        self.provider_name = prefix

    def search_videos(self, query, limit, location=None, radius_km=None):
        return [{"id": f"{self.prefix}_1", "title": "t", "view_count": 1, "source": self.prefix}]

    def fetch_video(self, video_id):
        return {"id": video_id, "title": "t", "source": self.prefix}

    def search_tracks(self, query, limit):
        return [{"id": f"{self.prefix}_1", "title": "t", "popularity": 1, "source": self.prefix}]

    def fetch_track(self, track_id):
        return {"id": track_id, "title": "t", "source": self.prefix}

    def search_articles(self, query, limit):
        return [{"id": f"{self.prefix}_1", "title": "t", "source": self.prefix}]

    def fetch_article(self, article_id):
        return {"id": article_id, "title": "t", "url": "https://example.com", "source": self.prefix}


@pytest.mark.unit
def test_agent_metrics_and_breaker(tmp_path):
    MetricsCollector.reset()
    metrics_path = tmp_path / "metrics.json"
    metrics = MetricsCollector(path=str(metrics_path), update_interval=0.1)
    cb = CircuitBreaker("test", failure_threshold=5, timeout=0.1)
    writer = CheckpointWriter(base_dir=tmp_path / "ck")
    task = {
        "transaction_id": "tid",
        "step_number": 1,
        "location_name": "Test",
        "search_hint": "hint",
        "route_context": "ctx",
    }

    v = VideoAgent(config={"search_limit": 1, "retry_attempts": 1, "timeout": 1.0}, checkpoint_writer=writer, client=StubClient("yt"), circuit_breaker=cb, metrics=metrics)
    s = SongAgent(config={"search_limit": 1, "retry_attempts": 1, "timeout": 1.0, "use_secondary_source": False}, checkpoint_writer=writer, client=StubClient("spotify"), circuit_breaker=cb, metrics=metrics)
    k = KnowledgeAgent(config={"search_limit": 1, "retry_attempts": 1, "timeout": 1.0}, checkpoint_writer=writer, client=StubClient("wiki"), circuit_breaker=cb, metrics=metrics)

    v.run(task)
    s.run(task)
    k.run(task)
    metrics.flush()
    data = json.loads(metrics_path.read_text())
    assert data["counters"]["api_calls.youtube"] >= 2  # search + fetch
    assert data["counters"]["api_calls.spotify"] >= 2
    assert data["counters"]["api_calls.wikipedia"] >= 2
    assert "agent.video.search_ms" in data["latencies"]
    assert "agent.song.search_ms" in data["latencies"]
    assert "agent.knowledge.search_ms" in data["latencies"]

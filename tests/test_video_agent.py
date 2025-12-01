from typing import Any, Dict, List
import pytest
from hw4_tourguide.agents.video_agent import VideoAgent
from hw4_tourguide.file_interface import CheckpointWriter


class StubVideoClient:
    def __init__(self, fail_once: bool = False):
        self.fail_once = fail_once
        self.search_calls = 0
        self.fetch_calls = 0

    def search_videos(self, query: str, limit: int, **kwargs) -> List[Dict[str, Any]]:
        self.search_calls += 1
        if self.fail_once and self.search_calls == 1:
            raise RuntimeError("search boom")
        
        # Simulate dynamic results based on query
        if "Tel Aviv beach" in query:
            return [
                {"id": "v3", "title": f"Top 10 Tel Aviv Beaches - {query}", "url": "https://example.com/v3", "view_count": 1000, "published_at": "2024-01-01"},
                {"id": "v4", "title": f"Hidden Gems near Tel Aviv - {query}", "url": "https://example.com/v4", "view_count": 500, "published_at": "2023-01-01"},
            ][:limit]
        elif "Tel Aviv" in query:
            return [
                {"id": "v1", "title": f"Exploring Tel Aviv - {query}", "url": "https://example.com/v1", "view_count": 100, "published_at": "2025-01-01"},
                {"id": "v2", "title": f"Tel Aviv City Guide - {query}", "url": "https://example.com/v2", "view_count": 50, "published_at": "2024-06-01"},
            ][:limit]
        else:
            return [
                {"id": f"v{i}", "title": f"General Video {i} for {query}", "url": f"https://example.com/v{i}", "view_count": 10 - i}
                for i in range(limit)
            ]

    def fetch_video(self, video_id: str, **kwargs):
        self.fetch_calls += 1
        return {"id": video_id, "title": "Video 1", "url": "https://example.com/v1"}


@pytest.mark.unit
def test_video_agent_search_fetch_with_checkpoint(tmp_path):
    ck_dir = tmp_path / "ck"
    writer = CheckpointWriter(base_dir=ck_dir)
    client = StubVideoClient()
    agent = VideoAgent(
        config={"retry_attempts": 1, "search_limit": 3, "use_geosearch": False},
        checkpoint_writer=writer,
        metrics=None,
        circuit_breaker=None,
        client=client,
    )
    # Task designed to generate multiple query variants
    task = {"transaction_id": "tid789", "location_name": "Tel Aviv", "address": "Tel Aviv", "search_hint": "beach", "route_context": "walking tour", "step_number": 1}
    result = agent.run(task)
    assert result["status"] == "ok"
    # Expect multi-query search to increase search_calls
    assert client.search_calls > 1
    assert result["metadata"]["id"] == "v1"
    assert (ck_dir / "tid789" / "02_agent_search_video_step_1.json").exists()
    assert (ck_dir / "tid789" / "03_agent_fetch_video_step_1.json").exists()
    assert client.fetch_calls == 1


@pytest.mark.unit
def test_video_agent_retries_on_failure(tmp_path):
    ck_dir = tmp_path / "ck"
    writer = CheckpointWriter(base_dir=ck_dir)
    client = StubVideoClient(fail_once=True)
    agent = VideoAgent(
        config={"retry_attempts": 2, "search_limit": 2, "retry_backoff": "linear"},
        checkpoint_writer=writer,
        metrics=None,
        circuit_breaker=None,
        client=client,
    )
    task = {"transaction_id": "vid999", "location_name": "Haifa"}
    result = agent.run(task)
    assert result["status"] == "ok"
    assert client.search_calls == 3  # Query 1 (fail+retry) + Query 2 (success) = 3 calls

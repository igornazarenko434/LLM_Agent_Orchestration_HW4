from typing import Any, Dict, List
import pytest
from hw4_tourguide.agents.song_agent import SongAgent
from hw4_tourguide.file_interface import CheckpointWriter


class StubSongClient:
    def __init__(self, fail_once: bool = False):
        self.fail_once = fail_once
        self.search_calls = 0
        self.fetch_calls = 0

    def search_tracks(self, query: str, limit: int, **kwargs) -> List[Dict[str, Any]]:
        self.search_calls += 1
        if self.fail_once and self.search_calls == 1:
            raise RuntimeError("search boom")
        return [
            {"id": "t1", "title": f"{query} mellow", "popularity": 50, "published_at": "2023-01-01"},
            {"id": "t2", "title": f"{query} upbeat", "popularity": 90, "published_at": "2024-01-01"},
        ][:limit]

    def fetch_track(self, track_id: str, **kwargs) -> Dict[str, Any]:
        self.fetch_calls += 1
        return {"id": track_id, "title": f"title-{track_id}", "url": f"https://example.com/{track_id}"}


@pytest.mark.unit
def test_song_agent_search_fetch_with_checkpoint(tmp_path):
    ck_dir = tmp_path / "ck"
    writer = CheckpointWriter(base_dir=ck_dir)
    client = StubSongClient()
    agent = SongAgent(
        config={"retry_attempts": 1, "search_limit": 3},
        checkpoint_writer=writer,
        metrics=None,
        circuit_breaker=None,
        client=client,
    )
    task = {"transaction_id": "song123", "location_name": "Cambridge", "search_hint": "MIT", "route_context": "tour", "step_number": 1}
    result = agent.run(task)
    assert result["status"] == "ok"
    # Ranking should pick popularity 90 candidate (t2)
    assert result["metadata"]["id"] == "t2"
    assert (ck_dir / "song123" / "02_agent_search_song_step_1.json").exists()
    assert (ck_dir / "song123" / "03_agent_fetch_song_step_1.json").exists()
    assert client.fetch_calls == 1


@pytest.mark.unit
def test_song_agent_retries_on_failure(tmp_path):
    ck_dir = tmp_path / "ck"
    writer = CheckpointWriter(base_dir=ck_dir)
    client = StubSongClient(fail_once=True)
    agent = SongAgent(
        config={"retry_attempts": 2, "search_limit": 2, "retry_backoff": "linear"},
        checkpoint_writer=writer,
        metrics=None,
        circuit_breaker=None,
        client=client,
    )
    task = {"transaction_id": "song999", "location_name": "Haifa"}
    result = agent.run(task)
    assert result["status"] == "ok"
    assert client.search_calls == 3  # Query 1 (fail+retry) + Query 2 (success) = 3 calls

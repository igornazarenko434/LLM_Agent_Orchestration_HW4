import pytest
from hw4_tourguide.agents.video_agent import VideoAgent
from hw4_tourguide.file_interface import CheckpointWriter


class StubDurClient:
    def __init__(self):
        self.provider_name = "youtube"

    def search_videos(self, query, limit, location=None, radius_km=None):
        return [
            {"id": "short", "title": "s", "url": "http://y/s", "view_count": 5, "duration_seconds": 50},
            {"id": "long", "title": "l", "url": "http://y/l", "view_count": 100, "duration_seconds": 5000},
        ]

    def fetch_video(self, video_id):
        return {"id": video_id, "title": "t", "url": f"http://y/{video_id}", "duration_seconds": 50 if video_id == "short" else 5000}


@pytest.mark.unit
def test_video_duration_filter(tmp_path):
    client = StubDurClient()
    agent = VideoAgent(
        config={"retry_attempts": 1, "search_limit": 2, "min_duration_seconds": 30, "max_duration_seconds": 300},
        checkpoint_writer=CheckpointWriter(base_dir=tmp_path),
        metrics=None,
        circuit_breaker=None,
        client=client,
    )
    task = {"transaction_id": "tid", "location_name": "Loc"}
    result = agent.run(task)
    # Should select "short" and filter out "long"
    assert result["metadata"]["id"] == "short"

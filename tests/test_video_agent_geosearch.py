import pytest
from hw4_tourguide.agents.video_agent import VideoAgent
from hw4_tourguide.file_interface import CheckpointWriter


class StubGeoClient:
    def __init__(self):
        self.calls = []
        self.provider_name = "youtube"

    def search_videos(self, query: str, limit: int, location=None, radius_km=None, **kwargs):
        self.calls.append((location, radius_km))
        return [{"id": "vid1", "title": query, "url": "http://y/vid1", "view_count": 10, "published_at": "2024", "duration_seconds": 100}]

    def fetch_video(self, video_id: str, **kwargs):
        return {"id": video_id, "title": "t", "url": "http://y/vid1", "duration_seconds": 100}


@pytest.mark.unit
def test_video_geosearch_params(tmp_path):
    client = StubGeoClient()
    agent = VideoAgent(
        config={"retry_attempts": 1, "search_limit": 1, "use_geosearch": True, "geosearch_radius_km": 5},
        checkpoint_writer=CheckpointWriter(base_dir=tmp_path),
        metrics=None,
        circuit_breaker=None,
        client=client,
    )
    task = {
        "transaction_id": "tid",
        "location_name": "Loc",
        "coordinates": {"lat": 1.0, "lng": 2.0},
        "instructions": "turn left",
    }
    agent.run(task)
    assert client.calls
    loc, radius = client.calls[0]
    assert loc == {"lat": 1.0, "lng": 2.0}
    assert radius == 5

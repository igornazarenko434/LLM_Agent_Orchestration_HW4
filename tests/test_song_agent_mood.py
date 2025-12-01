import pytest
from hw4_tourguide.agents.song_agent import SongAgent
from hw4_tourguide.file_interface import CheckpointWriter


class StubSongMoodClient:
    def __init__(self):
        self.provider_name = "spotify"
        self.calls = []

    def search_tracks(self, query: str, limit: int):
        self.calls.append(query)
        return [{"id": "t1", "title": query, "popularity": 10, "source": "spotify"}]

    def fetch_track(self, track_id: str):
        return {"id": track_id, "title": "t", "url": "http://s/t"}


@pytest.mark.unit
def test_song_mood_mapping(tmp_path):
    client = StubSongMoodClient()
    agent = SongAgent(
        config={"retry_attempts": 1, "search_limit": 1, "infer_song_mood": True},
        checkpoint_writer=CheckpointWriter(base_dir=tmp_path),
        metrics=None,
        circuit_breaker=None,
        client=client,
    )
    task = {"transaction_id": "tid", "location_name": "Beach", "search_hint": "relaxing coastal drive", "instructions": "enjoy the view"}
    agent.run(task)
    # Expect original query plus at least one mood query
    assert len(client.calls) >= 2

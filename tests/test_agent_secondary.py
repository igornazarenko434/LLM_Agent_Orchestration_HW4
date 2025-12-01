import pytest
from hw4_tourguide.agents.song_agent import SongAgent
from hw4_tourguide.agents.knowledge_agent import KnowledgeAgent
from hw4_tourguide.file_interface import CheckpointWriter


class CountingClient:
    def __init__(self, provider_name):
        self.provider_name = provider_name
        self.calls = 0

    def search_tracks(self, query, limit):
        self.calls += 1
        return [{"id": f"{self.provider_name}_track", "title": query}]

    def fetch_track(self, track_id):
        return {"id": track_id, "title": "t"}

    def search_articles(self, query, limit):
        self.calls += 1
        return [{"id": f"{self.provider_name}_article", "title": query, "url": "https://example.com"}]

    def fetch_article(self, article_id):
        return {"id": article_id, "title": "t", "url": "https://example.com"}


@pytest.mark.unit
def test_song_secondary_search_called(tmp_path):
    primary = CountingClient("primary")
    secondary = CountingClient("secondary")
    agent = SongAgent(
        config={"retry_attempts": 1, "search_limit": 1, "use_secondary_source": True},
        checkpoint_writer=CheckpointWriter(base_dir=tmp_path),
        metrics=None,
        circuit_breaker=None,
        client=primary,
        secondary_client=secondary,
    )
    task = {"transaction_id": "tid", "location_name": "Loc"}
    agent.run(task)
    # Primary called for each of the 2 queries generated ("Haifa", "Haifa music")
    assert primary.calls == 2
    # Secondary called for each query
    assert secondary.calls == 2


@pytest.mark.unit
def test_knowledge_secondary_search_called(tmp_path):
    # KnowledgeAgent calls secondary if use_secondary_source is True
    primary = CountingClient("primary")
    secondary = CountingClient("secondary")
    agent = KnowledgeAgent(
        config={"use_secondary_source": True, "retry_attempts": 1},
        client=primary,
        secondary_client=secondary,
    )
    task = {"location_name": "Haifa"}
    agent.run(task)
    # Primary called for each of the 2 queries generated
    assert primary.calls == 2
    # Secondary called for each query (since KnowledgeAgent calls both if configured)
    assert secondary.calls == 2

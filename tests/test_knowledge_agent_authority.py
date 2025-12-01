import pytest
from hw4_tourguide.agents.knowledge_agent import KnowledgeAgent
from hw4_tourguide.file_interface import CheckpointWriter


class StubKnowledgeAuthorityClient:
    def __init__(self):
        self.provider_name = "wikipedia"
        self.calls = 0

    def search_articles(self, query, limit):
        self.calls += 1
        return [
            {"id": "a1", "title": "Local Blog", "url": "https://example.com/blog", "published_at": None},
            {"id": "a2", "title": "Gov Doc", "url": "https://state.gov/doc", "published_at": "2024"},
        ]

    def fetch_article(self, article_id):
        return {"id": article_id, "title": f"t-{article_id}", "url": f"https://example.com/{article_id}"}


@pytest.mark.unit
def test_authority_boost(tmp_path):
    primary = StubKnowledgeAuthorityClient()
    agent = KnowledgeAgent(
        config={"retry_attempts": 1, "search_limit": 2, "use_secondary_source": False, "boost_authority_domains": True},
        checkpoint_writer=CheckpointWriter(base_dir=tmp_path),
        metrics=None,
        circuit_breaker=None,
        client=primary,
    )
    task = {"transaction_id": "tid", "location_name": "Loc"}
    result = agent.run(task)
    # Gov domain should be preferred
    assert result["metadata"]["id"] == "a2"

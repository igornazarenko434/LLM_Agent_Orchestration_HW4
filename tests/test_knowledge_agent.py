from typing import Any, Dict, List
import pytest
from hw4_tourguide.agents.knowledge_agent import KnowledgeAgent
from hw4_tourguide.file_interface import CheckpointWriter


class StubKnowledgeClient:
    def __init__(self, fail_once: bool = False):
        self.fail_once = fail_once
        self.search_calls = 0
        self.fetch_calls = 0

    def search_articles(self, query: str, limit: int, **kwargs) -> List[Dict[str, Any]]:
        self.search_calls += 1
        if self.fail_once and self.search_calls == 1:
            raise RuntimeError("search boom")
        return [
            {"id": "a1", "title": f"{query} blog", "url": "https://example.com/blog"},
            {"id": "a2", "title": f"{query} wiki", "url": "https://en.wikipedia.org/wiki/Test"},
        ][:limit]

    def fetch_article(self, article_id: str, **kwargs) -> Dict[str, Any]:
        self.fetch_calls += 1
        return {"id": article_id, "title": f"title-{article_id}", "url": f"https://example.com/{article_id}"}


@pytest.mark.unit
def test_knowledge_agent_search_fetch_with_checkpoint(tmp_path):
    ck_dir = tmp_path / "ck"
    writer = CheckpointWriter(base_dir=ck_dir)
    client = StubKnowledgeClient()
    agent = KnowledgeAgent(
        config={"retry_attempts": 1, "search_limit": 3},
        checkpoint_writer=writer,
        metrics=None,
        circuit_breaker=None,
        client=client,
    )
    task = {"transaction_id": "know123", "location_name": "Jerusalem", "search_hint": "history", "route_context": "tour", "step_number": 1}
    result = agent.run(task)
    assert result["status"] == "ok"
    # Ranking should favor authoritative wikipedia URL => a2
    assert result["metadata"]["id"] == "a2"
    assert (ck_dir / "know123" / "02_agent_search_knowledge_step_1.json").exists()
    assert (ck_dir / "know123" / "03_agent_fetch_knowledge_step_1.json").exists()
    assert client.fetch_calls == 1


@pytest.mark.unit
def test_knowledge_agent_retries_on_failure(tmp_path):
    ck_dir = tmp_path / "ck"
    writer = CheckpointWriter(base_dir=ck_dir)
    client = StubKnowledgeClient(fail_once=True)
    agent = KnowledgeAgent(
        config={"retry_attempts": 2, "search_limit": 2, "retry_backoff": "linear"},
        checkpoint_writer=writer,
        metrics=None,
        circuit_breaker=None,
        client=client,
    )
    task = {"transaction_id": "know999", "location_name": "Haifa"}
    result = agent.run(task)
    assert result["status"] == "ok"
    assert client.search_calls == 3  # Query 1 (fail+retry) + Query 2 (success) = 3 calls

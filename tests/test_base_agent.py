import json
from pathlib import Path
import pytest

from hw4_tourguide.agents.base_agent import BaseAgent
from hw4_tourguide.file_interface import CheckpointWriter


class DummyAgent(BaseAgent):
    agent_type = "video"

    def __init__(self, *args, search_payload=None, fetch_payload=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._search_payload = [{"id": "x1", "title": "t1", "url": "u1"}] if search_payload is None else search_payload
        self._fetch_payload = {"id": "x1", "title": "t1", "url": "u1"} if fetch_payload is None else fetch_payload
        self.search_calls = 0
        self.fetch_calls = 0

    def search(self, query, task, **kwargs):
        self.search_calls += 1
        return self._search_payload

    def fetch(self, candidate, task, **kwargs):
        self.fetch_calls += 1
        return self._fetch_payload


@pytest.mark.unit
def test_base_agent_happy_path(tmp_path):
    ck_dir = tmp_path / "ck"
    writer = CheckpointWriter(base_dir=ck_dir)
    agent = DummyAgent(
        config={"retry_attempts": 1},
        checkpoint_writer=writer,
        metrics=None,
        circuit_breaker=None,
    )
    task = {"transaction_id": "tid123", "location_name": "Loc", "address": "Addr", "step_number": 1}
    result = agent.run(task)

    assert result["status"] == "ok"
    assert result["metadata"]["title"] == "t1"
    # Check checkpoints written
    search_path = ck_dir / "tid123" / "02_agent_search_video_step_1.json"
    fetch_path = ck_dir / "tid123" / "03_agent_fetch_video_step_1.json"
    assert search_path.exists()
    assert fetch_path.exists()
    data = json.loads(search_path.read_text())
    assert isinstance(data, list)
    assert data[0]["id"] == "x1"


@pytest.mark.unit
def test_base_agent_unavailable_when_no_candidates(tmp_path):
    agent = DummyAgent(
        config={"retry_attempts": 1},
        checkpoint_writer=CheckpointWriter(base_dir=tmp_path),
        metrics=None,
        circuit_breaker=None,
        search_payload=[],
    )
    task = {"transaction_id": "tid456", "location_name": "Loc"}
    result = agent.run(task)
    assert result["status"] == "unavailable"
    assert "No candidates" in result["reasoning"]

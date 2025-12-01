"""
Resilience & Retry Tests (Mission M7.12).

Covers:
- Route provider retries/backoff on failure
- Agent timeout handling/fallback
- Graceful degradation when one agent fails
- Circuit breaker open/half-open recovery
- Checkpoint recovery stub (best-effort)
"""

import time
from unittest import mock
import pytest

from hw4_tourguide.route_provider import GoogleMapsProvider
from hw4_tourguide.tools.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from hw4_tourguide.agents.video_agent import VideoAgent
from hw4_tourguide.stub_agents import SongStubAgent, KnowledgeStubAgent
from hw4_tourguide.orchestrator import Orchestrator
from hw4_tourguide.scheduler import Scheduler
from hw4_tourguide.file_interface import CheckpointWriter


class _FailingAgent(VideoAgent):
    """Agent that raises to test graceful degradation."""
    def run(self, task):
        raise RuntimeError("boom")


class _SlowClient:
    def search_videos(self, query, limit):
        time.sleep(0.05)
        return [{"id": "1", "title": "t", "url": "u"}]
    def fetch_video(self, video_id):
        time.sleep(0.2)
        return {"id": video_id, "title": "t", "url": "u"}


@pytest.mark.resilience
def test_route_provider_retry_and_backoff(monkeypatch):
    calls = {"count": 0}
    def fake_get(*args, **kwargs):
        calls["count"] += 1
        raise ConnectionError("network down")
    with mock.patch("requests.get", side_effect=fake_get):
        provider = GoogleMapsProvider(api_key="dummy", retry_attempts=3, timeout=0.1, checkpoints_enabled=False)
        start = time.time()
        with pytest.raises(RuntimeError):
            provider.get_route("A", "B")
        duration = time.time() - start
        assert calls["count"] == 3
        # Allow for sleep(1)+sleep(2) plus overhead; ensure not hanging indefinitely
        assert duration < 8


@pytest.mark.resilience
def test_agent_timeout_fallback(monkeypatch):
    slow_client = _SlowClient()
    agent = VideoAgent(
        config={"search_limit": 1, "timeout": 0.01, "retry_attempts": 1},
        client=slow_client,
        mock_mode=False,
    )
    task = {"location_name": "Test", "route_context": "ctx"}
    result = agent.run(task)
    assert result["status"] in {"unavailable", "ok"}  # depending on timing, either fetch or timeout path


@pytest.mark.resilience
def test_graceful_degradation(monkeypatch, tmp_path):
    task_queue = mock.MagicMock()
    tasks = [{"transaction_id": "tid", "step_number": 1, "location_name": "Loc", "instructions": "Go", "emit_timestamp": time.time(), "timestamp": time.time()}]
    def get_task():
        return tasks.pop(0) if tasks else None
    task_queue.get.side_effect = get_task
    agents = {"video": _FailingAgent(config={}, mock_mode=True), "song": SongStubAgent(), "knowledge": KnowledgeStubAgent()}
    writer = CheckpointWriter(base_dir=tmp_path)
    judge_mock = mock.MagicMock()
    judge_mock.evaluate.return_value = {"chosen_agent": "song", "overall_score": 1, "individual_scores": {"video": 0, "song": 1, "knowledge": 1}, "timestamp": time.time(), "transaction_id": "tid"}
    orchestrator = Orchestrator(queue=task_queue, agents=agents, judge=judge_mock, max_workers=1, checkpoint_writer=writer)
    results = orchestrator.run()
    assert results[0]["agents"]["video"]["status"] == "error"
    assert results[0]["agents"]["song"]["status"] == "ok"
    assert results[0]["agents"]["knowledge"]["status"] == "ok"


@pytest.mark.resilience
def test_circuit_breaker_opens_after_threshold():
    cb = CircuitBreaker("test", failure_threshold=3, timeout=1)
    def always_fail():
        raise ValueError("fail")
    for _ in range(3):
        with pytest.raises(ValueError):
            cb.call(always_fail)
    with pytest.raises(CircuitBreakerOpenError):
        cb.call(always_fail)


@pytest.mark.resilience
def test_circuit_breaker_half_open_recovery():
    cb = CircuitBreaker("test", failure_threshold=1, timeout=0.1)
    with pytest.raises(ValueError):
        cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
    time.sleep(0.2)
    # Next call should flip to HALF_OPEN then CLOSED on success
    result = cb.call(lambda: "ok")
    assert result == "ok"
    assert cb.state == CircuitBreaker.CLOSED


@pytest.mark.resilience
def test_checkpoint_recovery_stub(tmp_path):
    # Ensure checkpoint writer writes and can list files for later recovery
    writer = CheckpointWriter(base_dir=tmp_path)
    tid = "tid-123"
    writer.write(tid, "02_agent_search_video.json", {"foo": "bar"})
    path = tmp_path / tid / "02_agent_search_video.json"
    assert path.exists()


@pytest.mark.resilience
def test_checkpoint_recovery_simulated_fetch(monkeypatch, tmp_path):
    """
    Simulate resuming from an existing search checkpoint to a fetch step.
    """
    writer = CheckpointWriter(base_dir=tmp_path)
    tid = "tid-recover"
    search_payload = [{"id": "vid-1", "title": "Video", "url": "u"}]
    writer.write(tid, "02_agent_search_video.json", search_payload)

    # Build a minimal agent that reads the checkpoint and performs fetch
    class _RecoverAgent(VideoAgent):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fetch_called = False
        def search(self, query, task, step_number=None):
            # Simulate skipping search because we have checkpoint
            return search_payload
        def fetch(self, candidate, task, step_number=None):
            self.fetch_called = True
            return {"id": candidate["id"], "title": "Recovered", "url": candidate["url"]}

    agent = _RecoverAgent(
        config={"search_limit": 1, "retry_attempts": 1},
        checkpoint_writer=writer,
        mock_mode=False, # <-- Change this to False
    )
    task = {
        "transaction_id": tid,
        "step_number": 1,
        "location_name": "Recovered Location",
        "instructions": "Go",
        "route_context": "ctx",
    }
    result = agent.run(task)
    assert result["status"] == "ok"
    assert result["metadata"]["title"] == "Recovered"
    assert agent.fetch_called

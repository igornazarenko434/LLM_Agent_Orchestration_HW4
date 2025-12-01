"""
Tests for LLM-backed query generation (Mission M7.15).
"""

import json
import pytest

from hw4_tourguide.agents.base_agent import BaseAgent
from hw4_tourguide.agents.video_agent import VideoAgent
from hw4_tourguide.agents.song_agent import SongAgent
from hw4_tourguide.agents.knowledge_agent import KnowledgeAgent
from hw4_tourguide.tools.llm_client import LLMClient, LLMError


class _FakeLLM(LLMClient):
    def __init__(self, response_text: str):
        super().__init__(timeout=1.0, max_retries=1, backoff="linear")
        self._response_text = response_text

    def _call(self, prompt: str):
        return {"text": self._response_text, "usage": {"prompt_tokens": len(prompt) // 4, "completion_tokens": 5}}


class _RaisingLLM(LLMClient):
    def __init__(self):
        super().__init__(timeout=0.1, max_retries=1)

    def _call(self, prompt: str):
        raise LLMError("boom")


class _DummyAgent(BaseAgent):
    agent_type = "video"

    def search(self, query, task):
        return []

    def fetch(self, candidate, task):
        return {}


class _FakeMetrics:
    def __init__(self):
        self.counters = {}
        self.latencies = {}

    def increment_counter(self, name: str):
        self.counters[name] = self.counters.get(name, 0) + 1

    def record_latency(self, name: str, duration_ms: float):
        self.latencies[name] = duration_ms


@pytest.mark.unit
def test_build_queries_with_llm_success():
    llm = _FakeLLM(response_text=json.dumps({"queries": ["MIT campus", "Cambridge tour"], "reasoning": "ok"}))
    agent = _DummyAgent(
        config={"use_llm_for_queries": True, "search_limit": 2},
        llm_client=llm,
    )
    task = {"location_name": "MIT", "search_hint": "campus tour", "route_context": "Boston university tour"}
    queries = agent._build_queries(task)
    assert queries == ["MIT campus", "Cambridge tour"]


@pytest.mark.unit
def test_build_queries_llm_fallback_to_heuristic():
    llm = _RaisingLLM()
    metrics = _FakeMetrics()
    agent = _DummyAgent(
        config={"use_llm_for_queries": True, "search_limit": 3},
        llm_client=llm,
        metrics=metrics,
    )
    task = {"location_name": "MIT", "search_hint": "campus tour", "route_context": "Boston university tour"}
    queries = agent._build_queries(task)
    # Heuristic path should still include location and hint
    assert any("MIT" in q for q in queries)
    assert any("walking tour" in q for q in queries)
    assert metrics.counters.get("llm_fallback.query_generation") == 1


@pytest.mark.unit
def test_build_queries_disabled_via_config():
    llm = _FakeLLM(response_text=json.dumps({"queries": ["should", "not", "use"], "reasoning": "ignored"}))
    agent = _DummyAgent(
        config={"use_llm_for_queries": False, "search_limit": 2},
        llm_client=llm,
    )
    task = {"location_name": "MIT", "search_hint": "campus tour", "route_context": "Boston university tour"}
    queries = agent._build_queries(task)
    assert any("MIT" in q for q in queries)
    # ensure LLM path skipped by checking heuristics not equal to provided list length
    assert queries != ["should", "not"]


@pytest.mark.unit
def test_build_queries_llm_malformed_json():
    llm = _FakeLLM(response_text="not-json")
    agent = _DummyAgent(
        config={"use_llm_for_queries": True, "search_limit": 2},
        llm_client=llm,
    )
    task = {"location_name": "MIT", "search_hint": "campus tour"}
    queries = agent._build_queries(task)
    assert any("MIT" in q for q in queries)


@pytest.mark.unit
def test_build_queries_no_llm_client():
    agent = _DummyAgent(
        config={"use_llm_for_queries": True, "search_limit": 2},
        llm_client=None,
    )
    task = {"location_name": "MIT", "search_hint": "campus tour"}
    queries = agent._build_queries(task)
    assert any("MIT" in q for q in queries)


@pytest.mark.unit
def test_build_queries_llm_returns_list_of_strings():
    llm = _FakeLLM(response_text=json.dumps(["query1", "query2"]))
    agent = _DummyAgent(
        config={"use_llm_for_queries": True, "search_limit": 2},
        llm_client=llm,
    )
    task = {"location_name": "MIT"}
    queries = agent._build_queries(task)
    assert queries == ["query1", "query2"]


@pytest.mark.unit
def test_build_queries_records_metrics_and_latency():
    llm = _FakeLLM(response_text=json.dumps({"queries": ["A", "B"], "reasoning": "ok"}))
    metrics = _FakeMetrics()
    agent = _DummyAgent(
        config={"use_llm_for_queries": True, "search_limit": 2},
        llm_client=llm,
        metrics=metrics,
    )
    task = {"location_name": "MIT", "search_hint": "campus tour", "transaction_id": "tid-123"}
    _ = agent._build_queries(task)
    assert metrics.counters.get("llm_calls.query_generation") == 1
    assert "llm.query_generation_ms" in metrics.latencies or any(
        k.startswith("agent.video.llm_query_ms") for k in metrics.latencies
    )


@pytest.mark.unit
def test_video_agent_uses_llm_queries():
    llm = _FakeLLM(response_text=json.dumps({"queries": ["video q1", "video q2"], "reasoning": "ok"}))
    agent = VideoAgent(
        config={"use_llm_for_queries": True, "search_limit": 2, "timeout": 1.0},
        llm_client=llm,
    )
    task = {"location_name": "MIT", "search_hint": "campus", "route_context": "Boston tour"}
    queries = agent._build_queries(task)
    assert queries == ["video q1", "video q2"]


@pytest.mark.unit
def test_song_agent_uses_llm_queries():
    llm = _FakeLLM(response_text=json.dumps({"queries": ["song q1"], "reasoning": "ok"}))
    agent = SongAgent(
        config={"use_llm_for_queries": True, "search_limit": 1, "timeout": 1.0},
        llm_client=llm,
    )
    task = {"location_name": "Nashville", "search_hint": "music"}
    queries = agent._build_queries(task)
    assert queries == ["song q1"]


@pytest.mark.unit
def test_knowledge_agent_uses_llm_queries():
    llm = _FakeLLM(response_text=json.dumps({"queries": ["knowledge q1"], "reasoning": "ok"}))
    agent = KnowledgeAgent(
        config={"use_llm_for_queries": True, "search_limit": 1, "timeout": 1.0},
        llm_client=llm,
    )
    task = {"location_name": "Grand Canyon", "search_hint": "geology"}
    queries = agent._build_queries(task)
    assert queries == ["knowledge q1"]

import time
from queue import Queue
from pathlib import Path
import pytest

from hw4_tourguide.orchestrator import Orchestrator
from hw4_tourguide.file_interface import CheckpointWriter


class DummyAgent:
    def __init__(self, name, delay=0.0, fail=False, record=None):
        self.name = name
        self.delay = delay
        self.fail = fail
        self.record = record if record is not None else []

    def run(self, task):
        start = time.time()
        if self.delay:
            time.sleep(self.delay)
        if self.fail:
            raise RuntimeError(f"{self.name} failed")
        self.record.append(start)
        return {"agent_type": self.name, "status": "ok", "metadata": {}, "timestamp": task.get("timestamp")}


class DummyJudge:
    def __init__(self):
        self.calls = 0

    def evaluate(self, task, agent_results):
        self.calls += 1
        return {"transaction_id": task.get("transaction_id"), "overall_score": 80}


def build_queue(tasks):
    q = Queue()
    for t in tasks:
        q.put(t)
    q.put(None)
    return q


@pytest.mark.unit
def test_orchestrator_dispatches_and_handles_agent_failure(tmp_path: Path):
    tasks = [
        {"transaction_id": "tid", "step_number": 1, "location_name": "A", "coordinates": {"lat": 0, "lng": 0}, "instructions": "go", "timestamp": time.time()},
    ]
    q = build_queue(tasks)
    agents = {
        "ok": DummyAgent("ok"),
        "fail": DummyAgent("fail", fail=True),
    }
    judge = DummyJudge()
    cw = CheckpointWriter(base_dir=tmp_path, retention_days=0)
    orch = Orchestrator(queue=q, agents=agents, judge=judge, max_workers=2, checkpoint_writer=cw)
    results = orch.run()
    assert len(results) == 1
    agent_outputs = results[0]["agents"]
    assert agent_outputs["ok"]["status"] == "ok"
    assert agent_outputs["fail"]["status"] == "error"
    checkpoint = tmp_path / "tid" / "04_judge_decision_step_1.json"
    assert checkpoint.exists()
    assert judge.calls == 1


@pytest.mark.unit
def test_orchestrator_runs_agents_concurrently():
    tasks = [
        {"transaction_id": "tid2", "step_number": 1, "location_name": "A", "coordinates": {"lat": 0, "lng": 0}, "instructions": "go", "timestamp": time.time()},
    ]
    q = build_queue(tasks)
    record = []
    agents = {
        "a1": DummyAgent("a1", delay=0.05, record=record),
        "a2": DummyAgent("a2", delay=0.05, record=record),
    }
    judge = DummyJudge()
    orch = Orchestrator(queue=q, agents=agents, judge=judge, max_workers=1)
    start = time.time()
    orch.run()
    elapsed = time.time() - start
    # parallel agent execution should take roughly one delay, not two
    assert elapsed < 0.09
    assert len(record) == 2


@pytest.mark.unit
def test_orchestrator_consumes_multiple_tasks():
    tasks = [
        {"transaction_id": "tid3", "step_number": 1, "location_name": "A", "coordinates": {"lat": 0, "lng": 0}, "instructions": "go", "timestamp": time.time()},
        {"transaction_id": "tid3", "step_number": 2, "location_name": "B", "coordinates": {"lat": 1, "lng": 1}, "instructions": "go", "timestamp": time.time()},
    ]
    q = build_queue(tasks)
    agents = {"ok": DummyAgent("ok")}
    judge = DummyJudge()
    orch = Orchestrator(queue=q, agents=agents, judge=judge, max_workers=2)
    results = orch.run()
    assert [r["step_number"] for r in results] == [1, 2]
    assert judge.calls == 2

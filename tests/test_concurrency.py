import time
from queue import Queue
from pathlib import Path
import pytest

from hw4_tourguide.scheduler import Scheduler
from hw4_tourguide.orchestrator import Orchestrator
from hw4_tourguide.file_interface import CheckpointWriter


class RecordingAgent:
    def __init__(self, name: str, delay: float, records: dict):
        self.name = name
        self.delay = delay
        self.records = records

    def run(self, task):
        start = time.time()
        time.sleep(self.delay)
        end = time.time()
        self.records[self.name] = (start, end)
        return {
            "agent_type": self.name,
            "status": "ok",
            "metadata": {"title": f"{self.name} content"},
            "timestamp": task.get("timestamp"),
        }


class StubJudge:
    def evaluate(self, task, agent_results):
        return {"transaction_id": task.get("transaction_id"), "overall_score": 80, "chosen_agent": "video"}


@pytest.mark.concurrency
@pytest.mark.slow
def test_agents_run_concurrently(tmp_path: Path):
    # Two tasks, but we care about concurrency of agents within a task
    tasks = [
        {"transaction_id": "tid-conc", "step_number": 1, "location_name": "A", "instructions": "go", "timestamp": time.time()},
    ]
    q = Queue()
    # Scheduler emits tasks and sentinel
    scheduler = Scheduler(tasks=tasks, interval=0.01, queue=q, checkpoints_enabled=False, metrics=None)
    scheduler.start()

    records = {}
    agents = {
        "video": RecordingAgent("video", delay=0.1, records=records),
        "song": RecordingAgent("song", delay=0.1, records=records),
        "knowledge": RecordingAgent("knowledge", delay=0.1, records=records),
    }
    judge = StubJudge()
    cw = CheckpointWriter(base_dir=tmp_path, retention_days=0)
    orch = Orchestrator(queue=q, agents=agents, judge=judge, max_workers=2, checkpoint_writer=cw)

    results = orch.run()
    scheduler.join(timeout=1.0)

    # Ensure all agents ran
    assert set(records.keys()) == {"video", "song", "knowledge"}
    # Check overlap: video and song should overlap given same delay and parallel executor
    v_start, v_end = records["video"]
    s_start, s_end = records["song"]
    assert v_start < s_end and s_start < v_end  # overlapping execution windows

    # Check judge checkpoint was written
    ck = tmp_path / "tid-conc" / "04_judge_decision_step_1.json"
    assert ck.exists()
    assert results and results[0]["agents"]["video"]["status"] == "ok"

import time
from queue import Queue
from pathlib import Path
import pytest

from hw4_tourguide.scheduler import Scheduler


@pytest.mark.unit
def test_scheduler_emits_with_interval(monkeypatch):
    tasks = [
        {"transaction_id": "tid", "step_number": 1, "location_name": "A", "coordinates": {"lat": 0, "lng": 0}, "instructions": "go", "timestamp": time.time()},
        {"transaction_id": "tid", "step_number": 2, "location_name": "B", "coordinates": {"lat": 1, "lng": 1}, "instructions": "go", "timestamp": time.time()},
    ]
    sleep_calls = {"count": 0}

    def fake_sleep(duration):
        sleep_calls["count"] += 1

    monkeypatch.setattr(time, "sleep", fake_sleep)
    q: Queue = Queue()
    scheduler = Scheduler(tasks=tasks, interval=0.05, queue=q, checkpoints_enabled=False)
    scheduler.start()
    received = []
    while True:
        item = q.get(timeout=1)
        if item is None:
            break
        received.append(item)
    scheduler.join()
    assert [item["step_number"] for item in received] == [1, 2]
    assert sleep_calls["count"] == len(tasks)
    # emit_timestamp should be set
    assert all("emit_timestamp" in item for item in received)


@pytest.mark.unit
def test_scheduler_writes_checkpoint(tmp_path: Path):
    tasks = [
        {"transaction_id": "tid123", "step_number": 1, "location_name": "A", "coordinates": {"lat": 0, "lng": 0}, "instructions": "go", "timestamp": time.time()},
    ]
    q: Queue = Queue()
    scheduler = Scheduler(
        tasks=tasks,
        interval=0.01,
        queue=q,
        checkpoints_enabled=True,
        checkpoint_dir=tmp_path,
    )
    scheduler.start()
    while q.get(timeout=1) is not None:
        pass
    scheduler.join()
    checkpoint = tmp_path / "tid123" / "01_scheduler_queue.json"
    assert checkpoint.exists()


@pytest.mark.unit
def test_scheduler_handles_stop_gracefully(tmp_path: Path):
    tasks = [
        {"transaction_id": "tid_stop", "step_number": 1, "location_name": "A", "coordinates": {"lat": 0, "lng": 0}, "instructions": "go", "timestamp": time.time()},
        {"transaction_id": "tid_stop", "step_number": 2, "location_name": "B", "coordinates": {"lat": 1, "lng": 1}, "instructions": "go", "timestamp": time.time()},
    ]
    q: Queue = Queue()
    scheduler = Scheduler(tasks=tasks, interval=0.1, queue=q, checkpoints_enabled=False)
    scheduler.start()
    time.sleep(0.02)
    scheduler.stop()
    seen = []
    while True:
        item = q.get(timeout=1)
        if item is None:
            break
        seen.append(item["step_number"])
    scheduler.join()
    # It should emit at least the first task and always the sentinel; no deadlock
    assert 1 in seen


@pytest.mark.unit
def test_scheduler_handles_empty_task_list(tmp_path: Path):
    q: Queue = Queue()
    scheduler = Scheduler(tasks=[], interval=0.01, queue=q, checkpoints_enabled=True, checkpoint_dir=tmp_path)
    scheduler.start()
    assert q.get(timeout=1) is None  # sentinel arrives
    scheduler.join()
    checkpoint = tmp_path / "unknown_tid" / "01_scheduler_queue.json"
    assert checkpoint.exists()

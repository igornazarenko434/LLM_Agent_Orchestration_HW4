"""
Scheduler thread (Mission M7.2).
Emits tasks into a queue at configured intervals. Writes checkpoint of emitted tasks
and records optional metrics. Scheduler is a pure timer; it assumes tasks are already
shaped per task schema.
"""

import json
import threading
import time
from pathlib import Path
from queue import Queue
from typing import Dict, Any, List, Optional

from hw4_tourguide.logger import get_logger


class Scheduler(threading.Thread):
    def __init__(
        self,
        tasks: List[Dict[str, Any]],
        interval: float,
        queue: Queue,
        checkpoints_enabled: bool = True,
        checkpoint_dir: Path = Path("output/checkpoints"),
        metrics: Optional[Any] = None,
    ):
        super().__init__(daemon=True)
        self.tasks = tasks
        self.interval = interval
        self.queue = queue
        self.logger = get_logger("scheduler")
        self._stop_event = threading.Event()
        self.checkpoints_enabled = checkpoints_enabled
        self.checkpoint_dir = checkpoint_dir
        self.metrics = metrics

    def run(self) -> None:
        emitted: List[Dict[str, Any]] = []
        total = len(self.tasks)
        for task in self.tasks:
            if self._stop_event.is_set():
                break
            task["emit_timestamp"] = time.time()
            self.queue.put(task)
            emitted.append(task)
            tid = task.get("transaction_id", "unknown_tid")

            # Calculate timing details
            if len(emitted) > 1:
                actual_time = task["emit_timestamp"] - emitted[0]["emit_timestamp"]
                expected_time = (len(emitted) - 1) * self.interval
                delay = actual_time - expected_time
            else:
                actual_time = 0.0
                delay = 0.0

            self.logger.info(
                f"Scheduler_Emit | Step {task['step_number']}/{total}: {task['location_name']} | "
                f"TID: {tid} | Queue Depth: {self.queue.qsize()} | "
                f"Time: {actual_time:.3f}s | Delay: {'+' if delay >= 0 else ''}{delay:.3f}s | "
                f"thread={threading.current_thread().name}",
                extra={"event_tag": "Scheduler_Emit", "transaction_id": tid, "queue_depth": self.queue.qsize(), "delay_s": delay, "actual_time_s": actual_time}
            )
            self._record_metrics(queue_depth=self.queue.qsize(), emitted=True)
            time.sleep(self.interval)
        # Sentinel to signal completion
        self.queue.put(None)
        self._write_checkpoint(emitted)

    def stop(self) -> None:
        self._stop_event.set()

    def _write_checkpoint(self, emitted: List[Dict[str, Any]]) -> None:
        if not self.checkpoints_enabled:
            return
        tid = emitted[0].get("transaction_id", "unknown_tid") if emitted else "unknown_tid"
        path = self.checkpoint_dir / tid / "01_scheduler_queue.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(emitted, indent=2))
        self.logger.info(f"Wrote checkpoint {path}", extra={"event_tag": "Scheduler"})

    def _record_metrics(self, queue_depth: int, emitted: bool) -> None:
        if not self.metrics:
            return
        try:
            if emitted:
                self.metrics.increment_counter("scheduler.tasks_emitted")
            self.metrics.set_gauge("queue.depth", queue_depth)
        except Exception:
            # Metrics failures should not break scheduling
            pass

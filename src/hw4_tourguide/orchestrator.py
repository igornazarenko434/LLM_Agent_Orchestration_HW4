"""
Orchestrator (Mission M7.3).
Consumes queued tasks, dispatches workers, runs agents concurrently per task,
calls judge, aggregates results, and optionally writes checkpoints/metrics.
"""

import time
import threading
from concurrent.futures import ThreadPoolExecutor, Future
from queue import Queue
from typing import Dict, Any, List, Optional

from hw4_tourguide.logger import get_logger
from hw4_tourguide.file_interface import CheckpointWriter
from hw4_tourguide.validators import Validator


class Orchestrator:
    def __init__(
        self,
        queue: Queue,
        agents: Dict[str, Any],
        judge: Any,
        max_workers: int = 5,
        checkpoint_writer: Optional[CheckpointWriter] = None,
        metrics: Optional[Any] = None,
    ):
        self.queue = queue
        self.agents = agents
        self.judge = judge
        self.max_workers = max_workers
        self.checkpoint_writer = checkpoint_writer
        self.metrics = metrics
        self.logger = get_logger("orchestrator")
        self.validator = Validator()

        # Log orchestrator initialization
        self.logger.info(
            f"Orchestrator_Init | ThreadPool: {self.max_workers} workers | "
            f"Agents: {len(self.agents)} ({', '.join(self.agents.keys())})",
            extra={"event_tag": "Orchestrator_Init", "max_workers": self.max_workers, "agent_count": len(self.agents)}
        )

    def run(self) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        futures: List[Future] = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            while True:
                task = self.queue.get()
                if task is None:
                    break
                tid = task.get("transaction_id", "unknown_tid")
                step = task.get("step_number", "?")
                queue_depth = self.queue.qsize()
                self.logger.info(
                    f"Orchestrator_Task_Start | TID: {tid} | Step {step} | Queue Depth: {queue_depth} | "
                    f"thread={threading.current_thread().name}",
                    extra={"event_tag": "Orchestrator_Task_Start", "transaction_id": tid, "queue_depth": queue_depth}
                )
                self._record_metrics(queue_depth=queue_depth)
                futures.append(executor.submit(self._process_task, task))

            for future in futures:
                try:
                    result = future.result()
                    results.append(result)
                except Exception as exc:  # pragma: no cover
                    self.logger.error(
                        f"Worker failed: {exc}",
                        extra={"event_tag": "Error"},
                    )
        return results

    def _process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        agent_outputs: Dict[str, Any] = {}
        start = time.time()
        transaction_id = task.get("transaction_id", "unknown_tid")

        self.logger.info(
            f"Orchestrator_Agents_Dispatch | TID: {transaction_id} | Dispatching {len(self.agents)} agents in parallel",
            extra={"event_tag": "Orchestrator_Agents_Dispatch", "transaction_id": transaction_id, "agent_count": len(self.agents)}
        )

        with ThreadPoolExecutor(max_workers=len(self.agents)) as agent_executor:
            future_map = {
                agent_executor.submit(agent.run, task): name
                for name, agent in self.agents.items()
            }
            for future in future_map:
                name = future_map[future]
                try:
                    agent_outputs[name] = future.result()
                except Exception as exc:  # pragma: no cover - defensive fallback
                    self.logger.error(
                        f"Agent {name} failed: {exc}",
                        extra={"event_tag": "Error"},
                    )
                    agent_outputs[name] = {
                        "agent_type": name,
                        "status": "error",
                        "metadata": {},
                        "reasoning": f"Agent {name} failed",
                        "timestamp": task.get("timestamp"),
                        "error": str(exc),
                    }

        # Log agent completion summary
        agent_time_ms = (time.time() - start) * 1000
        successful_agents = sum(1 for r in agent_outputs.values() if r.get("status") == "ok")
        self.logger.info(
            f"Orchestrator_Agents_Complete | TID: {transaction_id} | All agents finished | "
            f"Success: {successful_agents}/{len(self.agents)} | Time: {agent_time_ms:.0f}ms",
            extra={"event_tag": "Orchestrator_Agents_Complete", "transaction_id": transaction_id, "agent_time_ms": agent_time_ms, "successful_agents": successful_agents}
        )

        agent_results_list = list(agent_outputs.values())
        # Validate agent results (best-effort; drop malformed)
        agent_results_list = self.validator.validate_agent_results(agent_results_list)
        judge_decision = self.judge.evaluate(task, agent_results_list)
        # Validate judge decision (best-effort logging)
        judge_decision = self.validator.validate_judge_decision(judge_decision)
        result = {
            "transaction_id": transaction_id,
            "step_number": task.get("step_number"),
            "location": task.get("location_name"),
            "instructions": task.get("instructions"),
            "agents": agent_outputs,
            "judge": judge_decision,
            "timestamp": task.get("timestamp"),
            "emit_timestamp": task.get("emit_timestamp"),
        }

        if self.checkpoint_writer:
            try:
                self.checkpoint_writer.write(
                    transaction_id, f"04_judge_decision_step_{task.get('step_number')}.json", result
                )
            except Exception:  # pragma: no cover
                self.logger.warning(
                    "Failed to write judge checkpoint",
                    extra={"event_tag": "Error"},
                )

        # Log overall task completion
        total_time_ms = (time.time() - start) * 1000
        queue_depth = self.queue.qsize()
        self.logger.info(
            f"Orchestrator_Task_Complete | TID: {transaction_id} | Step {task.get('step_number')} | "
            f"Total Time: {total_time_ms:.0f}ms | Queue Depth: {queue_depth}",
            extra={"event_tag": "Orchestrator_Task_Complete", "transaction_id": transaction_id, "task_time_ms": total_time_ms, "queue_depth": queue_depth}
        )

        self._record_metrics(queue_depth=queue_depth, latency=time.time() - start)
        return result

    def _record_metrics(self, queue_depth: int, latency: Optional[float] = None) -> None:
        if not self.metrics:
            return
        try:
            self.metrics.set_gauge("queue.depth", queue_depth)
            if latency is not None:
                self.metrics.record_latency("orchestrator.task_ms", latency * 1000)
        except Exception:
            pass

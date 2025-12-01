"""
MetricsCollector (Mission M7.7f).
Thread-safe counters, latencies, and gauges with periodic flush to JSON.
"""

import json
import threading
import time
from collections import defaultdict
from typing import Dict, Any, List


class MetricsCollector:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, path: str = "logs/metrics.json", update_interval: float = 5.0) -> None:
        if hasattr(self, "_initialized") and self._initialized:
            return
        self.path = path
        self.update_interval = update_interval
        self.counters: Dict[str, int] = defaultdict(int)
        self.latencies: Dict[str, List[float]] = defaultdict(list)
        self.gauges: Dict[str, Any] = {}
        self._data_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._auto_flush, daemon=True)
        self._thread.start()
        self._initialized = True

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton (used in tests)."""
        with cls._lock:
            if cls._instance is not None:
                try:
                    cls._instance.stop()
                except Exception:
                    pass
            cls._instance = None

    def increment_counter(self, name: str, value: int = 1) -> None:
        with self._data_lock:
            self.counters[name] += value

    def record_latency(self, name: str, duration_ms: float) -> None:
        with self._data_lock:
            self.latencies[name].append(duration_ms)

    def set_gauge(self, name: str, value: Any) -> None:
        with self._data_lock:
            self.gauges[name] = value

    def get_all(self) -> Dict[str, Any]:
        with self._data_lock:
            return {
                "counters": dict(self.counters),
                "latencies": {
                    k: {"values": v, "avg": sum(v) / len(v) if v else 0.0}
                    for k, v in self.latencies.items()
                },
                "gauges": dict(self.gauges),
            }

    def flush(self) -> None:
        data = self.get_all()
        try:
            with open(self.path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self.flush()

    def _auto_flush(self) -> None:
        while not self._stop_event.is_set():
            time.sleep(self.update_interval)
            self.flush()

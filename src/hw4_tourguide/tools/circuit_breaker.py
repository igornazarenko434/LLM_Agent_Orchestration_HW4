"""
Circuit breaker utility (Mission M7.7e).
Protects external API calls with a 3-state machine: CLOSED, OPEN, HALF_OPEN.
"""

import threading
import time
from typing import Callable, Any

from hw4_tourguide.logger import get_logger


class CircuitBreakerOpenError(RuntimeError):
    """Raised when circuit is OPEN and calls are blocked."""


class CircuitBreaker:
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        time_func: Callable[[], float] = time.monotonic,
    ) -> None:
        self.name = name
        self.failure_threshold = max(1, failure_threshold)
        self.timeout = max(0.1, timeout)
        self._time = time_func

        self.state = self.CLOSED
        self.failure_count = 0
        self.opened_at: float | None = None
        self._lock = threading.Lock()
        self.logger = get_logger(f"cb.{name}")

    def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        with self._lock:
            now = self._time()
            if self.state == self.OPEN:
                if (self.opened_at is not None) and (now - self.opened_at) >= self.timeout:
                    self.state = self.HALF_OPEN
                    self.logger.info(
                        f"HALF_OPEN | API: {self.name} | Attempting recovery",
                        extra={"event_tag": "CircuitBreaker"},
                    )
                else:
                    raise CircuitBreakerOpenError(f"Circuit open for {self.name}")

        try:
            result = func(*args, **kwargs)
        except Exception as exc:
            self._record_failure(exc)
            raise

        self._record_success()
        return result

    def _record_failure(self, exc: Exception) -> None:
        with self._lock:
            self.failure_count += 1
            now = self._time()
            if self.state in (self.CLOSED, self.HALF_OPEN) and self.failure_count >= self.failure_threshold:
                self.state = self.OPEN
                self.opened_at = now
                self.logger.warning(
                    f"OPEN | API: {self.name} | Reason: {self.failure_count} consecutive failures ({exc})",
                    extra={"event_tag": "CircuitBreaker"},
                )
            elif self.state == self.HALF_OPEN:
                # Immediately re-open on failure in half-open
                self.state = self.OPEN
                self.opened_at = now
                self.logger.warning(
                    f"OPEN | API: {self.name} | Reason: half-open failure ({exc})",
                    extra={"event_tag": "CircuitBreaker"},
                )

    def _record_success(self) -> None:
        with self._lock:
            if self.state in (self.CLOSED, self.HALF_OPEN):
                if self.state == self.HALF_OPEN:
                    self.logger.info(
                        f"CLOSED | API: {self.name} | Recovery successful",
                        extra={"event_tag": "CircuitBreaker"},
                    )
                self.state = self.CLOSED
                self.failure_count = 0
                self.opened_at = None

    def is_open(self) -> bool:
        with self._lock:
            if self.state == self.OPEN and self.opened_at:
                if (self._time() - self.opened_at) >= self.timeout:
                    # Ready to try half-open on next call
                    return False
            return self.state == self.OPEN

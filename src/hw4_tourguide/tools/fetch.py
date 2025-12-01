"""
FetchTool module (Mission M7.7c).
Provides thin wrappers around provider clients for the fetch phase with
timeout enforcement and structured logging. Agents remain responsible for
retries/backoff/circuit breaker/metrics.
"""

import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from typing import Any, Dict, Optional

from hw4_tourguide.logger import get_logger


class FetchTool:
    def __init__(self, timeout: float = 10.0, logger_name: str = "fetch") -> None:
        self.timeout = timeout
        self.logger = get_logger(logger_name)

    def fetch_video(self, client: Any, video_id: str, step_number: Optional[int] = None) -> Dict[str, Any]:
        def _call():
            try:
                return client.fetch_video(video_id=video_id, step_number=step_number)
            except TypeError:
                return client.fetch_video(video_id=video_id)

        return self._run_with_timeout(
            _call,
            provider="video",
            identifier=video_id,
            step_number=step_number
        )

    def fetch_track(self, client: Any, track_id: str, step_number: Optional[int] = None) -> Dict[str, Any]:
        def _call():
            try:
                return client.fetch_track(track_id=track_id, step_number=step_number)
            except TypeError:
                return client.fetch_track(track_id=track_id)

        return self._run_with_timeout(
            _call,
            provider="song",
            identifier=track_id,
            step_number=step_number
        )

    def fetch_article(self, client: Any, article_id: str, step_number: Optional[int] = None) -> Dict[str, Any]:
        def _call():
            try:
                return client.fetch_article(article_id=article_id, step_number=step_number)
            except TypeError:
                return client.fetch_article(article_id=article_id)

        return self._run_with_timeout(
            _call,
            provider="knowledge",
            identifier=article_id,
            step_number=step_number
        )

    def _run_with_timeout(self, func, provider: str, identifier: str, step_number: Optional[int] = None) -> Dict[str, Any]:
        start = time.time()
        log_extra = {"event_tag": "Agent", "step": step_number}
        try:
            with ThreadPoolExecutor(max_workers=1) as ex:
                future = ex.submit(func)
                result = future.result(timeout=self.timeout)
        except FuturesTimeout:
            self.logger.warning(
                f"FETCH TIMEOUT | provider={provider} | id={identifier} | timeout={self.timeout}s",
                extra=log_extra,
            )
            raise TimeoutError(f"Fetch timeout for provider={provider}")
        except Exception as exc:
            self.logger.warning(
                f"FETCH ERROR | provider={provider} | id={identifier} | error={exc}",
                extra=log_extra,
            )
            raise

        self.logger.info(
            f"FETCH | provider={provider} | id={identifier} | ms={(time.time()-start)*1000:.1f}",
            extra=log_extra,
        )
        return result
